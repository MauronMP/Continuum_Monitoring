import csv
import json
from dataclasses import replace

import pytest

from continuum_bench.continuous_monitoring import experiment as monitoring_experiment
from continuum_bench.continuous_monitoring.config import MonitoringTask, known_policy_ids, load_monitoring_config
from continuum_bench.continuous_monitoring.reporting import _resource_metrics, report
from continuum_bench.continuous_monitoring.scheduler import run_scheduler
from continuum_bench.topology import Host, Topology


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def _task(task_id="task-a", priority=0, interval=10, deadline=None):
    return MonitoringTask(task_id, "P-TEST", ("Q1",), priority, "normal", interval, deadline)


def test_monitoring_configuration_resolves_policy_demand_schedules(root):
    with pytest.warns(UserWarning, match="policy-audit"):
        config = load_monitoring_config(root / "configs/monitoring.toml")
    assert config.benchmark.experiment["query_rounds"] == 18
    for level in ("low", "normal", "high", "critical"):
        tasks = config.resolve_tasks(level)
        assert tasks
        assert all(task.demand_level == level and task.interval_seconds > 0 for task in tasks)
    assert config.resolve_tasks("low")[0].interval_seconds > config.resolve_tasks("high")[0].interval_seconds
    assert config.minimum_recommended_cycles_per_task == 3
    assert config.validation_warnings


def test_policy_validation_uses_declared_identifiers_not_substrings(root):
    identifiers = known_policy_ids(root / "ontology")
    assert "P-OPS-02" in identifiers
    assert "OPS-02" not in identifiers


def test_infrastructure_memory_sums_workers_at_each_sample():
    samples = [
        {"host": "a", "timestamp": "1", "cpu_percent": 1, "memory_bytes": 100},
        {"host": "b", "timestamp": "1", "cpu_percent": 1, "memory_bytes": 300},
        {"host": "a", "timestamp": "2", "cpu_percent": 1, "memory_bytes": 200},
        {"host": "b", "timestamp": "2", "cpu_percent": 1, "memory_bytes": 400},
    ]
    metrics, hosts = _resource_metrics(samples, 60)
    assert metrics["worker_memory_mean"] == 250
    assert metrics["infrastructure_memory_mean"] == 500
    assert metrics["infrastructure_memory_peak"] == 600
    assert len(hosts) == 2


def test_fixed_rate_slots_do_not_drift_with_execution_duration():
    clock = FakeClock()
    scheduled = []

    def execute(_task, slot, _deadline):
        scheduled.append(slot)
        clock.sleep(3)
        return {"execution_status": "completed", "observation_outcome": "condition_detected"}

    result = run_scheduler((_task(),), 41, 120, execute, clock=clock, sleeper=clock.sleep)
    assert scheduled == [10, 20, 30, 40]
    assert result["scheduled_cycles"] == 4


def test_priority_deadline_and_task_id_provide_deterministic_tie_breaking():
    clock = FakeClock()
    order = []
    tasks = (
        _task("z", priority=1, deadline=8),
        _task("b", priority=2, deadline=9),
        _task("a", priority=2, deadline=9),
    )

    def execute(task, _slot, _deadline):
        order.append(task.task_id)
        return {"execution_status": "completed", "observation_outcome": "condition_not_detected"}

    run_scheduler(tasks, 11, 120, execute, clock=clock, sleeper=clock.sleep)
    assert order == ["a", "b", "z"]


def test_long_execution_records_missed_cycles_without_catch_up_burst():
    clock = FakeClock()
    executed = []

    def execute(_task, slot, _deadline):
        executed.append(slot)
        clock.sleep(12)
        return {"execution_status": "completed", "observation_outcome": "condition_detected"}

    result = run_scheduler((_task(interval=5),), 31, 30, execute, clock=clock, sleeper=clock.sleep)
    assert executed == [5, 20]
    assert [event["scheduled_at_monotonic"] for event in result["events"] if event["missed_cycle"]] == [10, 15, 25, 30]
    assert result["missed_cycles"] == 4
    assert result["scheduler_utilization"] == pytest.approx(24 / 32)


@pytest.mark.parametrize(
    ("outcome", "duration", "expected", "compliant"),
    [
        ("completed", 1, "completed_on_time", 1.0),
        ("completed", 7, "completed_late", 0.0),
        ("logical_timeout", 1, "completed_on_time", 0.0),
        ("semantic_failure", 1, "completed_on_time", 0.0),
    ],
)
def test_cycle_status_controls_policy_compliance(outcome, duration, expected, compliant):
    clock = FakeClock()

    def execute(_task, _slot, _deadline):
        clock.sleep(duration)
        return {"execution_status": outcome, "observation_outcome": "condition_detected"}

    task = replace(_task(interval=5), deadline_seconds=5)
    result = run_scheduler((task,), 11, 120, execute, clock=clock, sleeper=clock.sleep)
    assert result["events"][0]["execution_status"] == outcome
    assert result["events"][0]["schedule_status"] == expected
    assert result["monitoring_compliance"] == compliant


def test_detected_condition_is_a_compliant_observation_not_a_semantic_failure():
    clock = FakeClock()

    def execute(_task, _slot, _deadline):
        return {"execution_status": "completed", "observation_outcome": "condition_detected"}

    result = run_scheduler((_task(interval=5),), 6, 10, execute, clock=clock, sleeper=clock.sleep)
    event = result["events"][0]
    assert event["execution_status"] == "completed"
    assert event["schedule_status"] == "completed_on_time"
    assert event["observation_outcome"] == "condition_detected"
    assert event["monitoring_compliant"] is True
    assert result["semantic_failures"] == 0
    assert event["scheduled_offset_seconds"] == 5
    assert event["scheduled_at_utc"].endswith("+00:00")


@pytest.mark.parametrize(
    ("kind", "expectation", "result_count", "expected"),
    [
        ("violation", "zero_rows", 0, "condition_not_detected"),
        ("violation", "zero_rows", 2, "condition_detected"),
        ("report", "non_empty", 2, "observation_available"),
        ("inventory", "non_empty", 2, "observation_available"),
        ("ask", "true", 1, "expected_boolean_observed"),
        ("ask", "false", 1, "unexpected_boolean_observed"),
    ],
)
def test_observation_outcome_follows_query_contract(kind, expectation, result_count, expected):
    query = {"kind": kind, "expectation": expectation, "merge_strategy": "boolean_or" if kind == "ask" else "single"}
    logical = {"status": "completed", "result_count": result_count}
    assert monitoring_experiment._query_observation_outcome(query, logical) == expected


def test_scheduler_metrics_use_controlled_clock():
    clock = FakeClock()

    def execute(_task, _slot, _deadline):
        clock.sleep(2)
        return {"execution_status": "completed", "observation_outcome": "condition_not_detected"}

    result = run_scheduler(
        (_task(interval=5), _task("task-b", interval=5)), 14.9, 120, execute, clock=clock, sleeper=clock.sleep
    )
    assert result["scheduler_busy_seconds"] == 8
    assert result["scheduler_idle_seconds"] == pytest.approx(6.9)
    assert result["scheduler_utilization"] == pytest.approx(8 / 14.9)
    assert result["max_pending_monitoring_tasks"] == 2
    assert max(event.get("schedule_lag_seconds", 0) for event in result["events"]) == 2


def test_multi_query_task_stops_and_is_non_compliant_when_required_query_times_out(root, monkeypatch):
    with pytest.warns(UserWarning):
        config = load_monitoring_config(root / "configs/monitoring.toml")
    topology = Topology("test", (Host("edge", "edge", "a", "127.0.0.1", 8391),))
    queries = {
        query_id: {
            "id": query_id,
            "order": index,
            "query": "ASK { ?s ?p ?o }",
            "execution_scope": "all",
            "merge_strategy": "boolean_or",
            "kind": "ask",
            "expectation": "non_empty",
        }
        for index, query_id in enumerate(("Q1", "Q2", "Q3"), 1)
    }
    calls = []

    def logical_query(_hosts, query, *_args, **_kwargs):
        calls.append(query["id"])
        status = "query_timeout" if query["id"] == "Q2" else "completed"
        return (
            {"status": status, "result_count": 1, "logical_duration_ms": 1},
            [{"host": "edge", "status": status}],
        )

    monkeypatch.setattr(monitoring_experiment, "execute_logical_query", logical_query)
    execute, _logical, _physical = monitoring_experiment._task_executor(config, topology, queries, "distributed")
    task = MonitoringTask("multi", "P1", ("Q1", "Q2", "Q3"), 1, "normal", 10, 10)
    outcome = execute(task, 10, 10)
    assert outcome["execution_status"] == "logical_timeout"
    assert outcome["observation_outcome"] == "not_observed"
    assert outcome["recovery_count"] == 0
    assert calls == ["Q1", "Q2"]


def test_timeout_recovery_restarts_reprepares_and_verifies_non_idle_worker(root, monkeypatch):
    with pytest.warns(UserWarning):
        config = load_monitoring_config(root / "configs/monitoring.toml")
    topology = Topology("test", (Host("edge", "edge", "a", "127.0.0.1", 8391),))
    ready_calls = []

    def ready(*_args, **_kwargs):
        ready_calls.append(1)
        if len(ready_calls) == 1:
            raise TimeoutError("still busy")
        return {"status": "ready", "idle": True}

    monkeypatch.setattr(monitoring_experiment, "wait_ready", ready)
    monkeypatch.setattr(
        monitoring_experiment,
        "restart_workers",
        lambda *_args: [{"host": "edge", "required": True, "recovered": True, "restarted": True}],
    )
    monkeypatch.setattr(
        monitoring_experiment,
        "_prepare_workers",
        lambda *_args: [{"host": "edge", "status": "prepared"}],
    )
    evidence = monitoring_experiment._recover_after_timeout(
        config,
        topology,
        {"edge"},
        {"edge": b"<urn:s> <urn:p> <urn:o> .\n"},
        {"edge": {"dataset_digest": "dataset", "closure_digest": "closure"}},
        {},
    )
    assert evidence["recovery_count"] == 1
    assert evidence["worker_restart_count"] == 1
    assert evidence["recovery_succeeded"] is True
    assert evidence["recovery_preparation_evidence"][0]["status"] == "prepared"


def test_timeout_recovery_reports_failure_when_reprepare_fails(root, monkeypatch):
    with pytest.warns(UserWarning):
        config = load_monitoring_config(root / "configs/monitoring.toml")
    topology = Topology("test", (Host("edge", "edge", "a", "127.0.0.1", 8391),))
    monkeypatch.setattr(
        monitoring_experiment,
        "wait_ready",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError("worker remained busy")),
    )
    monkeypatch.setattr(
        monitoring_experiment,
        "restart_workers",
        lambda *_args: [{"host": "edge", "required": True, "recovered": True, "restarted": True}],
    )
    monkeypatch.setattr(
        monitoring_experiment,
        "_prepare_workers",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("reprepare failed")),
    )
    evidence = monitoring_experiment._recover_after_timeout(
        config,
        topology,
        {"edge"},
        {"edge": b"<urn:s> <urn:p> <urn:o> .\n"},
        {"edge": {"dataset_digest": "dataset", "closure_digest": "closure"}},
        {},
    )
    assert evidence["recovery_succeeded"] is False
    assert evidence["recovery_count"] == evidence["worker_restart_count"] == 1
    assert evidence["recovery_error"] == "reprepare failed"


def test_recovery_failure_halts_scheduler_and_marks_partial_result(tmp_path):
    clock = FakeClock()

    def execute(task, _slot, _deadline):
        clock.sleep(1)
        return {
            "execution_status": "logical_timeout",
            "observation_outcome": "not_observed",
            "recovery_count": 1,
            "recovery_seconds": 1.0,
            "worker_restart_count": 1,
            "recovery_succeeded": False,
            "failure_reason": "timeout_recovery_failed",
            "failed_task": task.task_id,
            "failed_query": "Q1",
            "failed_hosts": ["edge"],
        }

    scheduler = run_scheduler((_task(interval=5),), 30, 10, execute, clock=clock, sleeper=clock.sleep)
    events = scheduler.pop("events")
    result = {"measurement_requested_seconds": 30}
    completed = monitoring_experiment._finalize_measurement_result(result, scheduler, 1, 1)
    evidence = tmp_path / "scheduler_events.jsonl"
    evidence.write_text("".join(json.dumps(event) + "\n" for event in events))
    assert completed is False
    assert result["status"] == "recovery_failed"
    assert result["measurement_actual_seconds"] < result["measurement_requested_seconds"]
    assert result["failed_task"] == "task-a"
    assert result["failed_query"] == "Q1"
    assert result["failed_hosts"] == ["edge"]
    assert result["recovery_count"] == result["worker_restart_count"] == 1
    assert evidence.read_text()


def test_partial_reporting_uses_actual_duration_and_excludes_partial_from_summary(tmp_path):
    run_dir = tmp_path / "monitoring"

    def repetition(rep, status, requested, actual):
        path = run_dir / f"users-1/distributed/normal/rep-{rep:02}"
        path.mkdir(parents=True)
        result = {
            "scenario": "users-1",
            "layout": "distributed",
            "demand_level": "normal",
            "repetition": rep,
            "status": status,
            "scheduler_halted": status != "completed",
            "measurement_requested_seconds": requested,
            "measurement_actual_seconds": actual,
            "scheduled_cycles": 10,
            "monitoring_compliant_cycles": 8,
            "monitoring_compliance": 0.8,
            "completed_on_time": 8,
            "completed_late": 0,
            "missed_cycles": 2,
            "logical_timeouts": int(status != "completed"),
            "semantic_failures": 0,
            "physical_failures": 0,
            "recovery_count": int(status != "completed"),
            "recovery_seconds": 1,
            "worker_restart_count": int(status != "completed"),
            "scheduler_busy_seconds": 10,
            "scheduler_idle_seconds": actual - 10,
            "scheduler_utilization": 10 / actual,
            "max_pending_monitoring_tasks": 1,
            "logical_queries": 8,
            "physical_requests": 16,
            "failure_reason": "timeout_recovery_failed" if status != "completed" else None,
        }
        (path / "result.json").write_text(json.dumps(result))
        event = {
            "task_id": "task",
            "policy_id": "P-TEST",
            "missed_cycle": False,
            "schedule_lag_seconds": 0,
            "monitoring_compliant": True,
            "observation_outcome": "observation_available",
        }
        (path / "scheduler_events.jsonl").write_text(json.dumps(event) + "\n")
        (path / "logical_queries.jsonl").write_text(
            json.dumps({"status": "completed", "logical_duration_ms": 2}) + "\n"
        )
        samples = (
            {
                "host": "edge",
                "timestamp": "1",
                "cpu_percent": 1,
                "cpu_usage_seconds": 0,
                "memory_bytes": 100,
                "network_rx_bytes": 0,
                "network_tx_bytes": 0,
                "pids": 1,
            },
            {
                "host": "edge",
                "timestamp": "2",
                "cpu_percent": 2,
                "cpu_usage_seconds": 10,
                "memory_bytes": 110,
                "network_rx_bytes": 1024**2,
                "network_tx_bytes": 2 * 1024**2,
                "pids": 1,
            },
        )
        (path / "resource_samples.jsonl").write_text("".join(json.dumps(row) + "\n" for row in samples))

    repetition(1, "completed", 300, 300)
    repetition(2, "recovery_failed", 300, 80)
    summary_dir = report(run_dir)
    with (summary_dir / "partial_repetitions.csv").open() as handle:
        partial = next(csv.DictReader(handle))
    with (summary_dir / "summary.csv").open() as handle:
        summary = next(csv.DictReader(handle))
    assert float(partial["normalization_duration_seconds"]) == 80
    assert float(partial["cpu_seconds_per_hour"]) == 450
    assert float(partial["network_rx_mib_per_hour"]) == 45
    assert float(partial["logical_queries_per_hour"]) == 360
    assert float(summary["cpu_seconds_per_hour"]) == 120
    assert int(float(summary["repetitions"])) == 1
