"""Recovery decisions must retain identity, respect grants and expose failure."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from continuum_bench.config import load_config
from continuum_bench.monitoring.container_scale.config import load, logical_topology
from continuum_bench.monitoring.adaptive_monitoring.policy import load_policy, choose, evidence
from continuum_bench.monitoring.adaptive_monitoring.actuator import relocated_topology, RecoveryDeployment
from continuum_bench.monitoring.adaptive_monitoring.runner import supervise
from continuum_bench.monitoring.adaptive_monitoring.reporting import report


@pytest.fixture
def setup(root):
    config = load(root/'configs/container-scale.toml', root)
    benchmark = load_config(root/'configs/benchmark.toml')
    policy = load_policy(root/'configs/adaptive-monitoring.toml', benchmark)
    probes = [dict(host_id=n.node_id,ready=True,memory_available_mib=30000,cpu_count=8)
              for n in config.topology.active_nodes]
    observation = dict(preparations=3,preparation_failures=3,requests=0,request_failures=0,
        failure_fraction=None,source_counts={'edge2-c1':3},query_source_counts={},errors=[],semantic_statuses=[])
    return config,benchmark,policy,probes,observation


def test_hard_constraints_before_ranking(setup):
    config,_,policy,probes,observed = setup
    policy['authorization']['allowed_destinations'] = ['fog']
    decision = choose(policy,config,probes,observed,'distributed',1)
    assert decision['destination']=='fog'
    probes[1]['memory_available_mib']=0
    # Find by ID, never assume inventory ordering.
    for p in probes:
        if p['host_id']=='fog': p['memory_available_mib']=0
    assert choose(policy,config,probes,observed,'distributed',1)['action']=='abstain'


def test_trust_precedes_memory(setup):
    config,_,policy,probes,observed=setup
    policy['trust']['fog']=.95
    policy['trust']['cloud']=1
    next(p for p in probes if p['host_id']=='fog')['memory_available_mib']=100000
    assert choose(policy,config,probes,observed,'distributed',1)['destination']=='cloud'


def test_unknown_query_source_abstains(setup):
    config,_,policy,probes,observed=setup
    observed.update(preparation_failures=0,request_failures=30,requests=30,failure_fraction=1)
    assert choose(policy,config,probes,observed,'replicated',1)['action']=='abstain'
    observed['query_source_counts']={'edge2-c1':10}
    assert choose(policy,config,probes,observed,'replicated',1)['action']=='rebuild_replica_service'


def test_relocation_preserves_authorities_categories_and_identity(setup):
    config,_,_,_,_=setup
    original=logical_topology(config,1)
    relocated=relocated_topology(config,1,{'source':'edge2-c1','destination':'cloud'},8591)
    assert len(set(n.endpoint for n in relocated.nodes))==len(original.nodes)
    for before,after in zip(original.nodes,relocated.nodes):
        assert (before.node_id,before.tier,before.authority,before.categories)==(after.node_id,after.tier,after.authority,after.categories)
    assert relocated.node('edge2-c1').host==config.topology.node('cloud').host


def test_missing_evidence_does_not_trigger(setup,tmp_path):
    config,_,policy,probes,_=setup
    assert choose(policy,config,probes,evidence(tmp_path,'replicated'),'replicated',1)['action']=='abstain'


def test_policy_rejects_unknown_identifier(setup,tmp_path):
    config,benchmark,_,_,_=setup
    path=tmp_path/'policy.toml'
    path.write_text((benchmark.root/'configs/adaptive-monitoring.toml').read_text().replace('P-ADAPT-01','P-NONEXISTENT'))
    with pytest.raises(ValueError,match='policy bindings'):
        load_policy(path,benchmark)


def test_cleanup_attempts_every_host(setup,tmp_path,monkeypatch):
    config,_,_,_,_=setup
    a=RecoveryDeployment(config,tmp_path,logical_topology(config,1),tmp_path,'test')
    a.hosts=list(config.topology.active_nodes)
    called=[]
    def fail(node,*args):
        called.append(node.node_id)
        raise RuntimeError('injected')
    monkeypatch.setattr(a,'command',fail)
    assert len(a.close())==6
    assert len(called)==6


def test_plan_does_not_actuate(setup,tmp_path,monkeypatch):
    config,benchmark,policy,probes,observed=setup
    observed={**observed,'preparation_failures':0,'requests':45,'request_failures':6,'failure_fraction':6/45,'query_source_counts':{'edge2-c1':6}}
    campaign=tmp_path/'baseline';campaign.mkdir()
    (campaign/'configuration.json').write_text(json.dumps(config.raw))
    (campaign/'campaign.json').write_text(json.dumps({'steps':[dict(scenario='users-2000',containers_per_host=1,status='partial')]}))
    from continuum_bench.monitoring.adaptive_monitoring import runner
    monkeypatch.setattr(runner,'evidence',lambda *a:observed)
    monkeypatch.setattr(runner.deployment,'doctor',lambda *a:probes)
    monkeypatch.setattr(runner.deployment,'compose',lambda *a:pytest.fail('Plan mutated deployment'))
    output=supervise(config,benchmark,policy,tmp_path/'output',input_dir=campaign)
    assert all(r['status']=='planned' for r in json.loads((output/'decisions.json').read_text()))
    assert (output/'recovery-outcomes.png').exists()


def test_failed_expansion_never_stops_original_services(setup,tmp_path,monkeypatch):
    config,benchmark,policy,probes,observed=setup
    observed={**observed,'preparation_failures':0,'requests':45,'request_failures':6,'failure_fraction':6/45,'query_source_counts':{'edge2-c1':6}}
    campaign=tmp_path/'baseline';campaign.mkdir()
    (campaign/'configuration.json').write_text(json.dumps(config.raw))
    (campaign/'campaign.json').write_text(json.dumps({'steps':[dict(scenario='users-2000',containers_per_host=1,status='partial')]}))
    from continuum_bench.monitoring.adaptive_monitoring import runner
    monkeypatch.setattr(runner,'evidence',lambda *a:observed)
    monkeypatch.setattr(runner.deployment,'doctor',lambda *a:probes)
    monkeypatch.setattr(runner.deployment,'wait_ready',lambda *a,**kw:None)
    calls=[]
    def compose(config,root,node,*args):
        calls.append((node.node_id,args))
        return node.node_id+'-c1' if args[0]=='ps' and node.node_id=='cloud' else ''
    monkeypatch.setattr(runner.deployment,'compose',compose)
    cleaned=[]
    class BrokenDeployment:
        def __init__(self,*args,**kwargs):pass
        def start(self):raise RuntimeError('injected startup failure')
        def close(self):cleaned.append(True);return []
    monkeypatch.setattr(runner,'RecoveryDeployment',BrokenDeployment)
    output=supervise(config,benchmark,policy,tmp_path/'output',input_dir=campaign,execute=True)
    rows=json.loads((output/'decisions.json').read_text())
    assert all(r['status']=='failed' for r in rows)
    assert len(cleaned)==2
    starts=[(host,args) for host,args in calls if args[0]=='start']
    assert len(starts)==12
    assert all(args[0] not in ('stop','down','restart') for _,args in calls)


def test_replicated_query_failure_records_endpoint(monkeypatch):
    from continuum_bench.monitoring import distributed_reasoning_scalability as engine
    from continuum_bench.monitoring.distributed import Endpoint
    def fail(*args,**kwargs):raise TimeoutError('injected timeout')
    monkeypatch.setattr(engine,'_request',fail)
    result=engine._query_client([Endpoint('http://127.0.0.1:8491','edge2-c1',tier='edge')],[],'replicated',0,120)
    assert 'role=edge2-c1 endpoint=http://127.0.0.1:8491' in result[3]


def test_successful_recovery_preserves_experiment_budgets(setup,tmp_path,monkeypatch):
    from contextlib import nullcontext
    from continuum_bench.monitoring.adaptive_monitoring import runner,telemetry
    config,benchmark,policy,probes,observed=setup
    observed={**observed,'preparation_failures':0,'requests':45,'request_failures':6,'failure_fraction':6/45,'query_source_counts':{'edge2-c1':6}}
    campaign=tmp_path/'baseline';campaign.mkdir()
    (campaign/'configuration.json').write_text(json.dumps(config.raw))
    (campaign/'campaign.json').write_text(json.dumps({'steps':[dict(scenario='users-2000',containers_per_host=1,status='partial')]}))
    after={**observed,'preparation_failures':0,'requests':3,'request_failures':0,'failure_fraction':0}
    monkeypatch.setattr(runner,'evidence',lambda path,layout: observed if str(path).startswith(str(campaign)) else after)
    monkeypatch.setattr(runner.deployment,'doctor',lambda *a:probes)
    monkeypatch.setattr(runner.deployment,'compose',lambda *a:'')
    monkeypatch.setattr(runner.deployment,'wait_ready',lambda *a,**kw:None)
    monkeypatch.setattr(telemetry,'Sampler',lambda *a:nullcontext())
    class WorkingDeployment:
        def __init__(self,*args,**kwargs):pass
        def start(self):pass
        def close(self):return []
    monkeypatch.setattr(runner,'RecoveryDeployment',WorkingDeployment)
    experiments=[]
    def measured(benchmark,experiment,target,path,*args,**kwargs):
        experiments.append(experiment)
        result=path/'distributed-reasoning-scalability';result.mkdir(parents=True,exist_ok=True)
        import csv
        with (result/'replica-routing.csv').open('w') as handle:
            writer = csv.DictWriter(handle, fieldnames=['layout','worker','logical_owner','is_origin','status','process_cpu_ms','concurrency','reasoner'])
            writer.writeheader()
            for layout in ('distributed', 'replicated'):
                for endpoint in args[1].active_nodes:
                    owner = kwargs['replica_owners'].get(endpoint.node_id, endpoint.node_id)
                    writer.writerow(dict(layout=layout, worker=endpoint.node_id, logical_owner=owner,
                        is_origin=owner==endpoint.node_id, status='completed', process_cpu_ms=1, concurrency=1, reasoner='rdfs'))
        return result
    monkeypatch.setattr(runner,'run_distributed_reasoning_scalability',measured)
    output=supervise(config,benchmark,policy,tmp_path/'output',input_dir=campaign,execute=True)
    rows=json.loads((output/'decisions.json').read_text())
    assert all(r['status']=='execution_recovered' for r in rows)
    assert all(e.users==2000 and e.request_timeout_seconds==120 and e.point_timeout_seconds==600 for e in experiments)
    assert all(e.reasoners==('rdfs',) for e in experiments)


def test_cli_selects_all_user_levels_and_preserves_new_concurrency(setup,tmp_path,monkeypatch):
    from continuum_bench.cli import _parser
    from continuum_bench.monitoring.adaptive_monitoring import cli
    _,benchmark,_,_,_=setup
    args=_parser().parse_args(['--timeout-mode','bounded','adaptive-monitoring','run',
        '--users','1','50','100','500','1000','2000','--concurrency','1','2','4','8'])
    (tmp_path/'decisions.json').write_text('[]')
    captured={}
    def capture(config,benchmark,policy,output,**kwargs):
        captured.update(config=config,**kwargs)
        return tmp_path
    monkeypatch.setattr(cli,'supervise',capture)
    assert cli.dispatch(args,benchmark)==0
    selected=[s for s in captured['config'].raw['scenarios'] if s['name'] in captured['scenarios']]
    assert len(selected)==6
    assert all(s['concurrency']==[1,2,4,8] for s in selected)


def test_completed_label_without_evidence_is_not_reported_as_healthy(setup,tmp_path,monkeypatch):
    from continuum_bench.monitoring.adaptive_monitoring import runner
    config,benchmark,policy,_,_=setup
    campaign=tmp_path/'baseline';campaign.mkdir()
    (campaign/'configuration.json').write_text(json.dumps(config.raw))
    (campaign/'campaign.json').write_text(json.dumps({'steps':[dict(scenario='users-1',containers_per_host=1,status='completed')]}))
    monkeypatch.setattr(runner.deployment,'doctor',lambda *a:pytest.fail('Healthy case should not probe for recovery'))
    output=supervise(config,benchmark,policy,tmp_path/'output',input_dir=campaign,execute=True)
    assert {r['status'] for r in json.loads((output/'decisions.json').read_text())}=={'abstained'}


def test_high_concurrency_failure_is_not_diluted_by_healthy_requests(setup):
    from continuum_bench.monitoring.adaptive_monitoring.policy import trigger
    _,_,policy,_,observed=setup
    policy['supervisor'].update(minimum_failures=2,max_failure_fraction=.2)
    observed.update(preparation_failures=0,requests=102,request_failures=2,failure_fraction=2/102,
        query_strata=[dict(reasoner='rdfs',concurrency=1,requests=100,request_failures=0,failure_fraction=0,query_source_counts={}),
                      dict(reasoner='rdfs',concurrency=8,requests=2,request_failures=2,failure_fraction=1,query_source_counts={'edge1-c1':2})])
    assert trigger(policy,observed)['counts']=={'edge1-c1':2}


def test_cumulative_placement_retains_prior_move_and_checks_total_capacity(setup):
    config,_,policy,probes,observed=setup
    placements={n.node_id:n.node_id.rsplit('-c',1)[0] for n in logical_topology(config,1).nodes}
    placements['edge2-c1']='cloud'
    observed['source_counts']={'edge1-c1':3}
    policy['authorization']['allowed_destinations']=['cloud']
    cloud=next(p for p in probes if p['host_id']=='cloud')
    cloud['cpu_count']=2
    assert choose(policy,config,probes,observed,'distributed',1,placements=placements)['action']=='abstain'
    cloud['cpu_count']=8
    decision=choose(policy,config,probes,observed,'distributed',1,placements=placements)
    topo=relocated_topology(config,1,decision,8591,placements)
    assert topo.node('edge2-c1').host==topo.node('edge1-c1').host==config.topology.node('cloud').host
    assert len({n.endpoint for n in topo.nodes})==len(topo.nodes)
    assert choose(policy,config,probes,observed,'distributed',1,placements=placements,
                  tried={('edge1-c1','cloud')})['action']=='abstain'


def test_no_failures_in_one_layout_does_not_stop_healthy_services(setup,tmp_path,monkeypatch):
    from continuum_bench.monitoring.adaptive_monitoring import runner
    config,benchmark,policy,_,observed=setup
    observed={**observed,'preparation_failures':0,'requests':3,'request_failures':0,'failure_fraction':0}
    campaign=tmp_path/'baseline';campaign.mkdir()
    (campaign/'configuration.json').write_text(json.dumps(config.raw))
    (campaign/'campaign.json').write_text(json.dumps({'steps':[dict(scenario='users-1',containers_per_host=1,status='partial')]}))
    monkeypatch.setattr(runner,'evidence',lambda *a:observed)
    monkeypatch.setattr(runner.deployment,'compose',lambda *a:pytest.fail('Healthy layout stopped'))
    output=supervise(config,benchmark,policy,tmp_path/'output',input_dir=campaign,execute=True)
    assert all(r['status']=='not_needed' for r in json.loads((output/'decisions.json').read_text()))


def test_supervisor_keeps_earlier_replicas_between_attempts(setup,tmp_path,monkeypatch):
    from contextlib import nullcontext
    from continuum_bench.monitoring.adaptive_monitoring import runner,telemetry
    config,benchmark,policy,probes,observed=setup
    raw=deepcopy(config.raw);raw['experiment']['layouts']=['distributed'];raw['experiment']['warmup']=0
    config=replace(config,raw=raw)
    policy['supervisor']['max_attempts']=2
    observed={**observed,'preparation_failures':0,'requests':45,'request_failures':6,'failure_fraction':6/45,'query_source_counts':{'edge2-c1':6}}
    campaign=tmp_path/'baseline';campaign.mkdir()
    (campaign/'configuration.json').write_text(json.dumps(config.raw))
    (campaign/'campaign.json').write_text(json.dumps({'steps':[dict(scenario='users-2000',containers_per_host=1,status='partial')]}))
    observations=[observed,{**observed,'request_failures':3,'failure_fraction':3/45,'source_counts':{'edge1-c1':3}},
                  {**observed,'preparation_failures':0,'requests':3,'request_failures':0,'failure_fraction':0}]
    monkeypatch.setattr(runner,'evidence',lambda *a:observations.pop(0))
    monkeypatch.setattr(runner.deployment,'doctor',lambda *a:probes)
    monkeypatch.setattr(runner.deployment,'compose',lambda *a:'')
    monkeypatch.setattr(runner.deployment,'wait_ready',lambda *a,**kw:None)
    monkeypatch.setattr(telemetry,'Sampler',lambda *a:nullcontext())
    topologies=[]
    class Deployment:
        def __init__(self,c,r,t,*args,**kwargs):topologies.append(t)
        def start(self):pass
        def close(self):return []
    monkeypatch.setattr(runner,'RecoveryDeployment',Deployment)
    def measured(b,e,t,p,*a,**kw):
        result=p/'distributed-reasoning-scalability';result.mkdir(parents=True,exist_ok=True)
        import csv
        with (result/'replica-routing.csv').open('w') as handle:
            writer = csv.DictWriter(handle, fieldnames=['layout','worker','logical_owner','is_origin','status','process_cpu_ms','concurrency','reasoner'])
            writer.writeheader()
            for layout in ('distributed', 'replicated'):
                for endpoint in a[1].active_nodes:
                    owner = kw['replica_owners'].get(endpoint.node_id, endpoint.node_id)
                    writer.writerow(dict(layout=layout, worker=endpoint.node_id, logical_owner=owner,
                        is_origin=owner==endpoint.node_id, status='completed', process_cpu_ms=1, concurrency=1, reasoner='rdfs'))
        return result
    monkeypatch.setattr(runner,'run_distributed_reasoning_scalability',measured)
    output=supervise(config,benchmark,policy,tmp_path/'output',input_dir=campaign,execute=True)
    rows=json.loads((output/'decisions.json').read_text())
    assert [r['status'] for r in rows]==['not_recovered','execution_recovered']
    assert rows[1]['placements_before']==rows[0]['placements_after']
    assert topologies[0].node('edge2-c1').host==topologies[1].node('edge2-c1').host
