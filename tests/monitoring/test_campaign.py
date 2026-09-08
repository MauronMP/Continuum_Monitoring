"""Campaign contract tests use an in-memory infrastructure port, not remote hosts."""
from dataclasses import replace
import json
from threading import Lock
import pytest
from continuum_bench.monitoring.campaign_config import load_campaign, Axis
from continuum_bench.monitoring.campaign import execute_campaign, run_campaign
from continuum_bench.monitoring.campaign_runtime import CampaignRuntime
from continuum_bench.monitoring.workloads import build_workload

class MemoryInfrastructure:
    def __init__(self):
        self.runtimes = [CampaignRuntime(), CampaignRuntime()]
        self.locks = [Lock(), Lock()]
    def inventory(self):
        return [{'node_id': str(i)} for i in range(2)]
    def call(self, node, operation, payload, timeout):
        i = int(node['node_id'])
        with self.locks[i]:
            return getattr(self.runtimes[i], 'prepare' if operation == 'prepare' else 'execute')(payload)

class Sink:
    def __init__(self): self.rows = []
    def write(self, row): self.rows.append(row)

@pytest.fixture
def campaign(root):
    c = load_campaign(root/'configs/campaign-smoke.toml')
    return replace(c, reasoners=('rdfs',), axes=(Axis('physical_nodes',(1,2)),), warmup=0)

def test_equivalent_replicated_and_distributed_workloads(campaign):
    sink = Sink()
    assert execute_campaign(campaign, MemoryInfrastructure(), sink) == 0
    assert len(sink.rows) == 4
    assert all(r['result_validation_rate'] == 1 for r in sink.rows)
    assert all(r['completed_requests'] == 4 for r in sink.rows)
    assert all(r['cpu_ms'] >= 0 and r['throughput_rps'] > 0 for r in sink.rows)

@pytest.mark.parametrize('axis', ['iot_devices','users','policies','individuals','requirements','query_complexity'])
def test_workload_axes_change_real_graph_size(campaign, axis):
    small = replace(campaign.baseline, **{axis: 2})
    big = replace(campaign.baseline, **{axis: 4})
    assert len(build_workload(big,2026)) > len(build_workload(small,2026))
    assert set(build_workload(big,2026)) == set(build_workload(big,2026))

def test_timeouts_are_recorded_and_later_points_continue(campaign):
    class Broken(MemoryInfrastructure):
        def call(self, *args): raise TimeoutError('worker deadline')
    sink = Sink()
    assert execute_campaign(campaign, Broken(), sink) == 4
    assert {r['status'] for r in sink.rows} == {'timeout'}
    assert all(r['throughput_rps'] is None for r in sink.rows)

def test_structured_results_keep_configuration_and_do_not_overwrite(campaign,tmp_path):
    c = replace(campaign, axes=(Axis('concurrency',(2,)),), modes=('distributed',))
    first, failures = run_campaign(c, MemoryInfrastructure(), tmp_path)
    second, _ = run_campaign(c, MemoryInfrastructure(), tmp_path)
    assert first != second and failures == 0
    manifest = json.loads((first/'manifest.json').read_text())
    row = json.loads((first/'results.jsonl').read_text())
    assert manifest['configuration_id'] == c.fingerprint
    assert row['workload']['concurrency'] == 2
    assert row['status'] == 'completed'
    assert (first/'results.csv').is_file()

def test_unknown_or_decreasing_axes_fail_before_execution(root,tmp_path):
    source=(root/'configs/campaign-smoke.toml').read_text()
    p=tmp_path/'campaign.toml'
    p.write_text(source.replace('values = [1, 2, 5]','values = [2, 1]'))
    with pytest.raises(ValueError,match='increasing'):load_campaign(p)


def test_physical_lease_rejects_overlap_and_releases_after_failure(tmp_path):
    from continuum_bench.monitoring.lease import physical_lease
    with physical_lease(tmp_path):
        with pytest.raises(RuntimeError, match="Another physical campaign"):
            with physical_lease(tmp_path):
                pass
    with physical_lease(tmp_path):
        pass


def test_campaign_rejects_unexecuted_query_variants(root, tmp_path):
    source = (root / "configs/campaign-smoke.toml").read_text()
    path = tmp_path / "bad.toml"
    path.write_text(source.replace('query_count = 2', 'query_count = 100'))
    with pytest.raises(ValueError, match="cover every configured query"):
        load_campaign(path)
