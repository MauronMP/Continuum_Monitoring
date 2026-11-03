from dataclasses import replace

import pytest

from continuum_bench.continuous_monitoring import experiment as monitoring_experiment
from continuum_bench.continuous_monitoring.config import MonitoringTask, load_monitoring_config
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
    config = load_monitoring_config(root / "configs/monitoring.toml")
    assert config.benchmark.experiment["query_rounds"] == 18
    for level in ("low", "normal", "high", "critical"):
        tasks = config.resolve_tasks(level)
        assert tasks
        assert all(task.demand_level == level and task.interval_seconds > 0 for task in tasks)
    assert config.resolve_tasks("low")[0].interval_seconds > config.resolve_tasks("high")[0].interval_seconds


def test_fixed_rate_slots_do_not_drift_with_execution_duration():
    clock = FakeClock()
    scheduled = []

    def execute(_task, slot, _deadline):
        scheduled.append(slot)
        clock.sleep(3)
        return {"status": "completed"}

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
        return {"status": "completed"}

    run_scheduler(tasks, 11, 120, execute, clock=clock, sleeper=clock.sleep)
    assert order == ["a", "b", "z"]


def test_long_execution_records_missed_cycles_without_catch_up_burst():
    clock = FakeClock()
    executed = []

    def execute(_task, slot, _deadline):
        executed.append(slot)
        clock.sleep(12)
        return {"status": "completed"}

    result = run_scheduler((_task(interval=5),), 31, 30, execute, clock=clock, sleeper=clock.sleep)
    assert executed == [5, 20]
    assert [event["scheduled_at_monotonic"] for event in result["events"] if event["missed_cycle"]] == [10, 15, 25, 30]
    assert result["missed_cycles"] == 4
    assert result["scheduler_utilization"] == pytest.approx(23 / 31)


@pytest.mark.parametrize(
    ("outcome", "duration", "expected", "compliant"),
    [
        ("completed", 1, "completed_on_time", 1.0),
        ("completed", 7, "completed_late", 0.0),
        ("logical_timeout", 1, "logical_timeout", 0.0),
        ("semantic_failure", 1, "semantic_failure", 0.0),
    ],
)
def test_cycle_status_controls_policy_compliance(outcome, duration, expected, compliant):
    clock = FakeClock()

    def execute(_task, _slot, _deadline):
        clock.sleep(duration)
        return {"status": outcome}

    task = replace(_task(interval=5), deadline_seconds=5)
    result = run_scheduler((task,), 11, 120, execute, clock=clock, sleeper=clock.sleep)
    assert result["events"][0]["status"] == expected
    assert result["monitoring_compliance"] == compliant


def test_scheduler_metrics_use_controlled_clock():
    clock = FakeClock()

    def execute(_task, _slot, _deadline):
        clock.sleep(2)
        return {"status": "completed"}

    result = run_scheduler(
        (_task(interval=5), _task("task-b", interval=5)), 14.9, 120, execute, clock=clock, sleeper=clock.sleep
    )
    assert result["scheduler_busy_seconds"] == 8
    assert result["scheduler_idle_seconds"] == pytest.approx(6.9)
    assert result["scheduler_utilization"] == pytest.approx(8 / 14.9)
    assert result["max_pending_monitoring_tasks"] == 2
    assert max(event.get("schedule_lag_seconds", 0) for event in result["events"]) == 2


def test_multi_query_task_stops_and_is_non_compliant_when_required_query_times_out(root, monkeypatch):
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
    assert outcome["status"] == "logical_timeout"
    assert calls == ["Q1", "Q2"]
