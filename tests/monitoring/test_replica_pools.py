"""Scale-out must preserve origins, semantic ownership and exactly-once routing."""
from dataclasses import replace
from types import SimpleNamespace
from pathlib import Path
import pytest

from continuum_bench.monitoring.distributed import Endpoint
from continuum_bench.monitoring.adaptive_monitoring.pools import ReplicaRouter, expanded_topology
from continuum_bench.monitoring.adaptive_monitoring.policy import load_policy, choose_expansion
from continuum_bench.monitoring.container_scale.config import load, logical_topology
from continuum_bench.config import load_config
from continuum_bench.monitoring import distributed_reasoning_scalability as engine


def test_distributed_routing_uses_origin_and_copy_without_double_count(monkeypatch):
    primary=Endpoint('http://edge:1','edge2-c1',tier='edge');copy=Endpoint('http://fog:2','edge2-c1-r1',tier='edge')
    router=ReplicaRouter([primary,copy],{copy.role:primary.role});sent=[]
    monkeypatch.setattr(engine,'distributed_assignment',lambda specs,endpoints:{primary.url:specs})
    def request(url,path,payload,**kw):
        sent.append(url);return dict(query_count=len(payload['query_ids']),request_bytes=1,response_bytes=1)
    monkeypatch.setattr(engine,'_request',request)
    specs=[SimpleNamespace(id='Q1')]
    results=[engine._query_client([primary],specs,'distributed',i,120,router,{}) for i in range(4)]
    assert sent==[primary.url,copy.url,primary.url,copy.url]
    assert sum(r[1] for r in results)==4
    assert sum(r['is_origin'] for r in router.records)==2
    assert all(r['status']=='completed' for r in router.records)


def test_pool_cannot_promote_replica_to_a_new_authority():
    a=Endpoint('http://a:1','edge-c1');b=Endpoint('http://b:1','edge-c1-r1')
    with pytest.raises(ValueError):ReplicaRouter([a,b],{b.role:'missing'})
    with pytest.raises(ValueError):ReplicaRouter([a,b],{a.role:b.role,b.role:a.role})


def test_expansion_keeps_every_original_host_and_scope(root):
    config=load(root/'configs/container-scale.toml',root)
    original=logical_topology(config,1)
    topo=expanded_topology(config,1,[dict(id='edge2-c1-r1',owner='edge2-c1',host='fog')],8591)
    assert len(topo.active_nodes)==7
    for n in original.active_nodes:
        retained=topo.node(n.node_id)
        assert (retained.host,retained.tier,retained.authority,retained.categories)==(n.host,n.tier,n.authority,n.categories)
    assert topo.node('edge2-c1-r1').host==config.topology.node('fog').host
    assert len({n.endpoint for n in topo.active_nodes})==7


def test_policy_prefers_available_noncloud_and_rejects_preparation_replication(root):
    config=load(root/'configs/container-scale.toml',root);b=load_config(root/'configs/benchmark.toml')
    p=load_policy(root/'configs/adaptive-monitoring.toml',b)
    probes=[dict(host_id=n.node_id,ready=True,memory_available_mib=30000,cpu_count=8) for n in config.topology.active_nodes]
    o=dict(preparation_failures=0,requests=8,request_failures=4,failure_fraction=.5,query_source_counts={'edge2-c1':4},source_counts={})
    action=choose_expansion(p,config,probes,o,'distributed',1)
    assert action['origin_retained'] and action['destination'] not in ('cloud','edge2')
    o.update(preparation_failures=1,source_counts={'edge2-c1':1})
    assert choose_expansion(p,config,probes,o,'distributed',1)['action']=='abstain'


def test_replica_prepare_checks_original_fragment_identity(root,tmp_path):
    from continuum_bench.node import NodeRuntime
    from continuum_bench.partitioning import build_fragments,serialize_fragment
    from continuum_bench.topology import render_flat_topology
    config=load(root/'configs/container-scale.toml',root);benchmark=load_config(root/'configs/benchmark.toml')
    original=logical_topology(config,1)
    topo=expanded_topology(config,1,[dict(id='edge2-c1-r1',owner='edge2-c1',host='fog')],8591)
    path=render_flat_topology(topo,tmp_path/'topology.toml')
    runtime=NodeRuntime(root,'edge2-c1-r1',tier='edge',topology_name='container-scale',topology_file=path,replica_of='edge2-c1')
    fragments=build_fragments(benchmark,1,2026,topology=original,validate_graph_digest=False)
    payload=serialize_fragment(fragments,'edge2-c1',users=1,seed=2026)
    result=runtime.prepare('rdfs',1,2026,mode='distributed',fragment=payload,validate_graph_digest=False)
    assert result['node_id']=='edge2-c1-r1' and result['fragment_sha256']==payload['sha256']
    wrong=serialize_fragment(fragments,'edge1-c1',users=1,seed=2026)
    with pytest.raises(ValueError,match='another node'):
        runtime.prepare('rdfs',1,2026,mode='distributed',fragment=wrong,validate_graph_digest=False)


def test_pool_figures_preserve_each_attempt(tmp_path):
    import csv
    from continuum_bench.monitoring.adaptive_monitoring.pool_reporting import report_pools

    (tmp_path / 'figures').mkdir()
    (tmp_path / 'analysis').mkdir()
    decisions = []
    for attempt in (1, 2):
        result = tmp_path / f'users-1-distributed-1-{attempt}' / 'measured' / 'distributed-reasoning-scalability'
        result.mkdir(parents=True)
        with (result / 'replica-routing.csv').open('w') as handle:
            writer = csv.DictWriter(handle, fieldnames=['layout', 'logical_owner', 'is_origin', 'status', 'process_cpu_ms'])
            writer.writeheader()
            writer.writerows([
                dict(layout='distributed', logical_owner='edge2-c1', is_origin=str(origin), status='completed', process_cpu_ms=12)
                for origin in (True, False)
            ])
        decisions.append(dict(scenario='users-1', layout='distributed', attempt=attempt,
            replica_owners={'edge2-c1-r1': 'edge2-c1'}, results=str(result.relative_to(tmp_path))))
    report_pools(tmp_path, decisions)
    assert len(list((tmp_path / 'figures').glob('*-origin-work.png'))) == 2
    with (tmp_path / 'analysis/replica-workshare.csv').open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    assert {row['attempt'] for row in rows} == {'1', '2'}


@pytest.mark.parametrize("concurrency", [1, 2, 4])
def test_replicated_schedule_covers_all_origins_and_copies(monkeypatch, concurrency):
    origins = [Endpoint(f'http://node{i}:1', f'node{i}', tier='edge') for i in range(6)]
    copies = [Endpoint(f'http://copy{i}:1', f'copy{i}', tier='edge') for i in range(2)]
    router = ReplicaRouter(origins + copies, {c.role: origins[0].role for c in copies})
    sent = []
    def request(url, path, payload, **kwargs):
        sent.append(url)
        return dict(query_count=1, process_cpu_ms=1)
    monkeypatch.setattr(engine, '_request', request)
    for index in range(18 * concurrency):
        result = engine._query_client(origins, [SimpleNamespace(id='Q1')], 'replicated',
                                      index, 120, router, {'layout': 'replicated', 'concurrency': str(concurrency)})
        assert not result[-1]
    assert set(sent) == {e.url for e in origins + copies}
    assert len(sent) == 18 * concurrency
    from continuum_bench.monitoring.adaptive_monitoring.pools import routing_coverage
    assert routing_coverage(router.records, 'replicated', [e.role for e in origins + copies])['complete']


def test_coverage_rejects_starvation_and_no_progress():
    from continuum_bench.monitoring.adaptive_monitoring.pools import routing_coverage, progress_assessment
    records = [dict(layout='replicated', worker='origin', concurrency='1')]
    assert not routing_coverage(records, 'replicated', ['origin', 'copy'])['complete']
    before = dict(requests=21, request_failures=21, preparation_failures=0)
    assert progress_assessment(before, before) == (False, False)
    assert progress_assessment(before, dict(before, request_failures=10)) == (True, False)
    assert progress_assessment(before, dict(before, preparation_failures=1)) == (False, True)


@pytest.mark.parametrize("adaptive", [False, True])
def test_engine_advances_indices_between_rounds(monkeypatch, adaptive):
    indices = []
    def client(endpoints, specs, layout, index, timeout, **kwargs):
        indices.append(index)
        return 1, 1, 1, ''
    monkeypatch.setattr(engine, '_query_client', client)
    config = SimpleNamespace(query_concurrency=(1, 2, 4), query_rounds=18,
                             request_timeout_seconds=120)
    engine._query_scalability({}, [], [], 'replicated', config,
                              router=object() if adaptive else None)
    assert sorted(indices) == sorted(list(range(18)) + list(range(36)) + list(range(72)))
