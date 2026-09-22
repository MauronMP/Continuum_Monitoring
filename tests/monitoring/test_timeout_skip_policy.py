"""Independent timeout skip scopes, shared by both physical coordinators."""
import csv
import re
from dataclasses import replace
from urllib.error import HTTPError, URLError

import pytest

from continuum_bench.monitoring import physical, distributed_ontology as distributed
from continuum_bench.monitoring.budget import (
    TimeoutSkipState, execution_policy, is_timeout_failure,
)
from continuum_bench.monitoring.config import load_config
from continuum_bench.monitoring.distributed import Endpoint
from continuum_bench.topology import load_topology


@pytest.mark.parametrize("field,value", [
    ("consecutive_timeout_threshold", 0),
    ("consecutive_timeout_threshold", 1.5),
    ("consecutive_timeout_threshold", True),
    ("skip_repetitions_after_timeout", "false"),
    ("skip_larger_sizes_after_timeout", 1),
    ("skip_cumulative_stages_after_timeout", None),
    ("timeout_mode", "sometimes"),
])
def test_policy_validation(config, field, value):
    with pytest.raises(ValueError, match=field):
        replace(config.limits, **{field: value})


def test_toml_loads_policy(config, tmp_path):
    source = (config.root / "configs/smoke-cumulative.toml").read_text()
    source = re.sub(
        r"(?m)^(?:skip_repetitions_after_timeout|skip_larger_sizes_after_timeout|"
        r"skip_cumulative_stages_after_timeout|consecutive_timeout_threshold|timeout_mode)\s*=.*\n",
        "", source,
    )
    # Add new keys directly below the limits header without changing source config.
    source = source.replace('[limits]', '''[limits]
skip_repetitions_after_timeout = false
skip_larger_sizes_after_timeout = true
skip_cumulative_stages_after_timeout = false
consecutive_timeout_threshold = 3
timeout_mode = "unlimited"
''')
    path = tmp_path / 'config.toml'
    path.write_text(source)
    limits = load_config(path).limits
    assert limits.skip_repetitions_after_timeout is False
    assert limits.skip_larger_sizes_after_timeout is True
    assert limits.skip_cumulative_stages_after_timeout is False
    assert limits.consecutive_timeout_threshold == 3
    assert limits.timeout_mode == 'unlimited'


def test_typed_timeout_classification_does_not_hide_errors():
    assert is_timeout_failure(TimeoutError())
    assert is_timeout_failure(URLError(TimeoutError()))
    assert is_timeout_failure(HTTPError('url', 408, 'timeout', {}, None))
    assert not is_timeout_failure(HTTPError('url', 500, 'timeout in invalid configuration', {}, None))
    assert not is_timeout_failure(ConnectionError('timed out'))
    assert not is_timeout_failure(ValueError('invalid timeout'))
    try:
        raise TimeoutError()
    except TimeoutError:
        try:
            raise ValueError('cleanup failed')
        except ValueError as error:
            assert not is_timeout_failure(error)
    try:
        raise RuntimeError('worker failed') from TimeoutError()
    except RuntimeError as error:
        assert is_timeout_failure(error)


def test_streak_reset_reasoner_isolation_and_latched_scopes(config):
    state = TimeoutSkipState(replace(config.limits, consecutive_timeout_threshold=2))
    state.timeout('rdfs', 5, 1, 1, TimeoutError('first'))
    assert state.skipped('rdfs', 5, 2, 1) is None
    state.completed('rdfs')
    state.timeout('rdfs', 5, 2, 1, TimeoutError('second'))
    assert state.skipped('rdfs', 10, 1, 1) is None
    state.timeout('rdfs', 5, 2, 2, TimeoutError('third'))
    assert state.skipped('rdfs', 5, 2, 3)
    assert state.skipped('rdfs', 5, 3, 1)
    assert state.skipped('rdfs', 10, 1, 1)
    assert state.skipped('owlrl', 10, 1, 1) is None
    state.completed('rdfs')
    assert state.skipped('rdfs', 10, 1, 1)
    with execution_policy(True):
        assert state.skipped('rdfs', 10, 1, 1) is None


@pytest.fixture(params=[physical, distributed], ids=['balanced', 'partitioned'])
def coordinator(request, config, tmp_path, monkeypatch):
    module = request.param
    selected = replace(config, reasoners=('rdfs',), scale_users=(5, 25), repetitions=3,
                       category_order=config.category_order[:3])
    endpoint = Endpoint('http://worker', 'cloud', tier='cloud', authority=True,
                        categories=selected.category_order)
    monkeypatch.setattr(module, 'discover', lambda *a, **k: [endpoint])
    topology = load_topology(config.root / 'configs/topologies/physical/topology.toml', 'physical')

    def run(suite, limits=None):
        cfg = replace(selected, limits=limits or selected.limits)
        if module is physical:
            runner = getattr(module, 'run_physical_' + suite)
            output = runner(cfg, topology, tmp_path)
        else:
            runner = getattr(module, 'run_distributed_' + suite)
            output = runner(cfg, [endpoint.url], tmp_path, target='physical', validate_results=False)
        with (output / 'summary.csv').open() as handle:
            return list(csv.DictReader(handle))
    return module, selected, run


@pytest.mark.parametrize('repetitions,sizes,expected_calls', [
    (True, True, 1), (True, False, 2), (False, True, 3), (False, False, 6),
])
def test_scalability_setup_skip_scopes(coordinator, monkeypatch, repetitions, sizes, expected_calls):
    module, config, run = coordinator
    calls = []
    def timeout(*args, **kwargs):
        calls.append(1)
        raise TimeoutError('setup deadline')
    monkeypatch.setattr(module, '_prepare', timeout)
    limits = replace(config.limits, skip_repetitions_after_timeout=repetitions,
                     skip_larger_sizes_after_timeout=sizes)
    rows = run('scalability', limits)
    assert len(calls) == expected_calls
    assert len(rows) == 6
    assert sum(row['status'] == 'timeout' for row in rows) == expected_calls


@pytest.mark.parametrize('repetitions,stages,expected_calls', [
    (True, True, 1), (True, False, 3), (False, True, 3), (False, False, 9),
])
def test_cumulative_setup_skip_scopes(coordinator, monkeypatch, repetitions, stages, expected_calls):
    module, config, run = coordinator
    calls = []
    def timeout(*args, **kwargs):
        calls.append(1)
        raise TimeoutError('setup deadline')
    monkeypatch.setattr(module, '_prepare', timeout)
    limits = replace(config.limits, skip_repetitions_after_timeout=repetitions,
                     skip_cumulative_stages_after_timeout=stages)
    rows = run('cumulative', limits)
    assert len(calls) == expected_calls
    assert len(rows) == 9
    assert sum(row['status'] == 'timeout' for row in rows) == expected_calls


@pytest.mark.parametrize('suite', ['cumulative', 'scalability'])
def test_threshold_counts_actual_attempts(coordinator, monkeypatch, suite):
    module, config, run = coordinator
    def timeout(*args, **kwargs):
        raise TimeoutError('deadline')
    monkeypatch.setattr(module, '_prepare', timeout)
    rows = run(suite, replace(config.limits, consecutive_timeout_threshold=2))
    assert [row['status'] for row in rows[:2]] == ['timeout', 'timeout']
    assert all(row['status'] == 'skipped_after_timeout' for row in rows[2:])


@pytest.mark.parametrize('suite', ['cumulative', 'scalability'])
@pytest.mark.parametrize('error', [ValueError('bad timeout setting'), ConnectionError('lost worker'),
                                  HTTPError('url', 500, 'worker crashed', {}, None)])
def test_real_errors_propagate(coordinator, monkeypatch, suite, error):
    module, config, run = coordinator
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(module, '_prepare', fail)
    with pytest.raises(type(error)):
        run(suite)


@pytest.mark.parametrize('suite,count', [('cumulative', 9), ('scalability', 6)])
def test_unlimited_does_not_skip_external_timeouts(coordinator, monkeypatch, suite, count):
    module, config, run = coordinator
    def timeout(*args, **kwargs):
        raise TimeoutError('external deadline')
    monkeypatch.setattr(module, '_prepare', timeout)
    with execution_policy(True):
        rows = run(suite)
    assert len(rows) == count
    assert all(row['status'] == 'timeout' for row in rows)


@pytest.fixture
def query_coordinator(coordinator, monkeypatch):
    module, config, run = coordinator
    url = 'http://worker'
    prepared = {url: {
        'synthetic_triples': 10, 'input_triples': 20, 'output_triples': 20,
        'logical_input_triples': 20, 'reasoning_ms': 1, 'generation_ms': 1,
    }}
    monkeypatch.setattr(module, '_prepare', lambda *a, **k: (2.0, prepared))
    if module is physical:
        def calibrate(config, endpoints, specs):
            return 1.0, {url: {spec.id: {'duration_ms': 1.0} for spec in specs}}, {url: {'query_cpu_ms': 1}}
        monkeypatch.setattr(module, '_calibrate', calibrate)
    else:
        monkeypatch.setattr(module, '_assignment', lambda specs, endpoints: {url: specs})
    calls = []

    def install(outcomes):
        outcomes = iter(outcomes)
        def query(config, endpoints, assignment, **kwargs):
            calls.append(kwargs)
            outcome = next(outcomes, 'ok')
            if isinstance(outcome, Exception):
                raise outcome
            specs = assignment[url]
            return 1.0, {url: {
                'query_count': len(specs), 'query_cpu_ms': 1.0,
                'measurements': [dict(
                    query_id=spec.id, duration_ms=1.0, result_count=0,
                    ask_result=False if spec.merge_strategy == 'boolean_or' else None,
                    result_keys=[], result_digest='', category=spec.category, tier=spec.tier,
                ) for spec in specs],
            }}
        monkeypatch.setattr(module, '_query', query)
    return module, config, run, calls, install


@pytest.mark.parametrize('suite', ['cumulative', 'scalability'])
def test_query_success_resets_timeout_streak(query_coordinator, suite):
    module, config, run, calls, install = query_coordinator
    install([TimeoutError('one'), 'ok', TimeoutError('two'), TimeoutError('three')])
    rows = run(suite, replace(config.limits, consecutive_timeout_threshold=2))
    assert [row['status'] for row in rows[:4]] == ['timeout', 'completed', 'timeout', 'timeout']
    assert all(row['status'] == 'skipped_after_timeout' for row in rows[4:])
    assert len(calls) == 4


@pytest.mark.parametrize('repetitions,stages,count', [
    (True, True, 1), (True, False, 3), (False, True, 3), (False, False, 9),
])
def test_query_cumulative_skip_scopes(query_coordinator, repetitions, stages, count):
    module, config, run, calls, install = query_coordinator
    install([TimeoutError('query deadline')] * 9)
    rows = run('cumulative', replace(config.limits,
        skip_repetitions_after_timeout=repetitions,
        skip_cumulative_stages_after_timeout=stages))
    assert len(calls) == count
    assert len(rows) == 9


@pytest.mark.parametrize('repetitions,sizes,count', [
    (True, True, 1), (True, False, 2), (False, True, 3), (False, False, 6),
])
def test_query_scalability_skip_scopes(query_coordinator, repetitions, sizes, count):
    module, config, run, calls, install = query_coordinator
    install([TimeoutError('query deadline')] * 6)
    rows = run('scalability', replace(config.limits,
        skip_repetitions_after_timeout=repetitions,
        skip_larger_sizes_after_timeout=sizes))
    assert len(calls) == count
    assert len(rows) == 6


@pytest.mark.parametrize('suite', ['cumulative', 'scalability'])
def test_keep_going_recovers_and_propagates_subsequent_errors(query_coordinator, suite):
    module, config, run, calls, install = query_coordinator
    limits = replace(config.limits, stop_scaling_after_timeout=False,
                     skip_repetitions_after_timeout=False,
                     skip_larger_sizes_after_timeout=False,
                     skip_cumulative_stages_after_timeout=False)
    install([TimeoutError('deadline'), 'ok', ValueError('invalid query')])
    with pytest.raises(ValueError, match='invalid query'):
        run(suite, limits)
    assert len(calls) == 3


@pytest.mark.parametrize('suite', ['cumulative', 'scalability'])
def test_all_points_completed_without_timeouts(query_coordinator, suite):
    module, config, run, calls, install = query_coordinator
    install([])
    rows = run(suite)
    assert len(rows) == (9 if suite == 'cumulative' else 6)
    assert all(row['status'] == 'completed' for row in rows)
    assert all(float(row['total_wall_ms']) == 3 for row in rows)


def test_legacy_flag_fallback_and_explicit_overrides(config):
    limits = replace(config.limits, stop_scaling_after_timeout=False,
                     skip_repetitions_after_timeout=None,
                     skip_larger_sizes_after_timeout=None)
    state = TimeoutSkipState(limits)
    state.timeout('rdfs', 5, 1, 1, TimeoutError())
    assert state.skipped('rdfs', 5, 2, 1) is None
    assert state.skipped('rdfs', 25, 1, 1) is None
    assert state.skipped('rdfs', 5, 1, 2)
    state = TimeoutSkipState(replace(limits, skip_larger_sizes_after_timeout=True))
    state.timeout('rdfs', 5, 1, 1, TimeoutError())
    assert state.skipped('rdfs', 25, 1, 1)


@pytest.mark.parametrize('suite', ['cumulative', 'scalability'])
def test_setup_recovery_when_skips_disabled(query_coordinator, monkeypatch, suite):
    module, config, run, calls, install = query_coordinator
    install([])
    prepare = module._prepare
    attempts = []
    def flaky_prepare(*args, **kwargs):
        attempts.append(1)
        if len(attempts) == 1:
            raise TimeoutError('setup deadline')
        return prepare(*args, **kwargs)
    monkeypatch.setattr(module, '_prepare', flaky_prepare)
    rows = run(suite, replace(config.limits, skip_repetitions_after_timeout=False,
                             skip_larger_sizes_after_timeout=False,
                             skip_cumulative_stages_after_timeout=False))
    assert rows[0]['status'] == 'timeout'
    assert all(row['status'] == 'completed' for row in rows[1:])


@pytest.mark.parametrize('suite', ['cumulative', 'scalability'])
def test_calibration_retry_and_reuse(query_coordinator, monkeypatch, suite):
    module, config, run, calls, install = query_coordinator
    if module is not physical:
        pytest.skip('partitioned coordinator does not calibrate')
    install([])
    calibrate = module._calibrate
    attempts = []
    def flaky_calibration(*args, **kwargs):
        attempts.append(1)
        if len(attempts) == 1:
            raise TimeoutError('calibration deadline')
        return calibrate(*args, **kwargs)
    monkeypatch.setattr(module, '_calibrate', flaky_calibration)
    rows = run(suite, replace(config.limits, skip_repetitions_after_timeout=False,
                             skip_larger_sizes_after_timeout=False,
                             skip_cumulative_stages_after_timeout=False))
    assert rows[0]['status'] == 'timeout'
    assert rows[0]['failed_phase'] == 'calibration'
    assert all(row['status'] == 'completed' for row in rows[1:])
    assert len(attempts) == (2 if suite == 'cumulative' else 3)


@pytest.mark.parametrize('module,function', [(physical, '_run_physical'), (distributed, '_run_distributed')])
def test_direct_api_honours_config_unlimited_and_restores_policy(config, monkeypatch, module, function):
    from continuum_bench.monitoring.budget import unlimited_execution
    unlimited = replace(config, limits=replace(config.limits, timeout_mode='unlimited'))
    monkeypatch.setattr(module, function + '_impl', lambda config, *a, **k: unlimited_execution())
    with execution_policy(False):
        assert getattr(module, function)(unlimited) is True
        assert unlimited_execution() is False
