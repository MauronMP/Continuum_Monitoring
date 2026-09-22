"""The all-tests workflow preserves workload selection and native coverage."""
from types import SimpleNamespace

from continuum_bench.monitoring import provenance, suite


def test_suite_uses_selected_configs_and_topology(root, tmp_path):
    plan = suite.suite_plan(root, root / 'configs/benchmark.toml', tmp_path,
        topology_file='configs/topologies/physical/topology.toml',
        load_config='configs/load-smoke.toml',
        experiment_config='configs/experiments-smoke.toml',
        campaign_config='configs/campaign-smoke.toml')
    steps = {step['name']: step for step in plan}
    for name in ('preflight', 'load'):
        command = steps[name]['command']
        assert command[command.index('--load-config') + 1] == 'configs/load-smoke.toml'
    for name in ('preflight', 'experiments'):
        command = steps[name]['command']
        assert command[command.index('--experiment-config') + 1] == 'configs/experiments-smoke.toml'
    for name in ('campaign-preflight', 'campaign'):
        command = steps[name]['command']
        assert command[command.index('--campaign-config') + 1] == 'configs/campaign-smoke.toml'
    for name, step in steps.items():
        if name not in {'software', 'documentation'}:
            assert '--topology-file' in step['command']
    assert '--validate-only' in steps['campaign-preflight']['command']
    assert list(steps).index('campaign-preflight') < list(steps).index('start-workers')


def test_suite_enables_native_tests_and_records_junit(root, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(provenance, 'snapshot', lambda *args: {})
    monkeypatch.setenv('CONTINUUM_TEST_NATIVE_OWL', '0')
    def run(command, **kwargs):
        calls.append((command, kwargs['env']))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(suite.subprocess, 'run', run)
    result = suite.run_suite(root, root/'configs/benchmark.toml', tmp_path,
                             families=['software'])
    assert calls[0][1]['CONTINUUM_TEST_NATIVE_OWL'] == '1'
    assert any(arg.endswith('/software-tests.xml') for arg in calls[0][0])
    assert [step['name'] for step in result['steps']] == ['software', 'documentation']
    assert all(step['status'] == 'completed' for step in result['steps'])
