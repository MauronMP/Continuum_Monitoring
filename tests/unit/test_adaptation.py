import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from continuum_bench.adaptation.config import TriggerThresholds, load_adaptation_config
from continuum_bench.adaptation.deployment import deploy_read_only_replica
from continuum_bench.adaptation.experiment import require_same_workload
from continuum_bench.adaptation.logic import ReplicaRouter, analyze_trigger, evaluate_trigger, plan_adaptation
from continuum_bench.adaptation.reporting import report
from continuum_bench.topology import Host


def _config(root):
    return load_adaptation_config(root / "configs/adaptation.toml")


def _event(index: int, *, compliant: bool, latency_ms: float, outcome: str = "observation_available") -> dict:
    started = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=index)
    return {
        "task_id": "operational-node-state",
        "scheduled_at_utc": started.isoformat(),
        "actual_start_utc": started.isoformat(),
        "actual_end_utc": (started + timedelta(milliseconds=latency_ms)).isoformat(),
        "actual_start_monotonic": float(index),
        "actual_end_monotonic": float(index) + latency_ms / 1000,
        "execution_status": "completed",
        "monitoring_compliant": compliant,
        "observation_outcome": outcome,
    }


def test_trigger_not_satisfied_produces_no_adaptation(root):
    config = replace(
        _config(root),
        thresholds=TriggerThresholds(90, 40, 0.2, 1000, 0.8, 1),
        consecutive_trigger_cycles=2,
    )
    scheduler = {
        "events": [_event(1, compliant=True, latency_ms=10), _event(2, compliant=True, latency_ms=10)],
        "monitoring_compliance": 1.0,
        "logical_timeouts": 0,
    }
    trigger = evaluate_trigger(config, scheduler, [])
    assert trigger["triggered"] is False
    analysis = analyze_trigger(trigger, "2026-01-01T00:00:00+00:00")
    assert analysis["conclusion"] == "no_adaptation_required"
    assert analysis["mode"] == "simulated_rule_based"
    plan = plan_adaptation(config, analysis, [], "2026-01-01T00:00:00+00:00")
    assert plan["status"] == "no_action"
    assert plan["action"] is None


def test_persistent_measured_degradation_generates_capacity_analysis(root):
    config = replace(
        _config(root),
        thresholds=TriggerThresholds(90, 40, 0.2, 100, 0.95, 1),
        consecutive_trigger_cycles=3,
    )
    scheduler = {
        "events": [_event(index, compliant=False, latency_ms=200) for index in range(1, 4)],
        "monitoring_compliance": 0.0,
        "logical_timeouts": 0,
    }
    trigger = evaluate_trigger(config, scheduler, [])
    assert trigger["triggered"] is True
    assert trigger["maximum_consecutive_degraded_cycles"] == 3
    analysis = analyze_trigger(trigger, "2026-01-01T00:00:00+00:00")
    assert analysis["conclusion"] == "additional_capacity_required"


def test_cpu_trigger_selects_the_most_pressured_configured_edge(root):
    config = replace(
        _config(root),
        thresholds=TriggerThresholds(90, 40, 0.2, 10000, 0.5, 1),
        consecutive_trigger_cycles=2,
    )
    scheduler = {
        "events": [_event(10, compliant=True, latency_ms=10), _event(20, compliant=True, latency_ms=10)],
        "monitoring_compliance": 1.0,
        "logical_timeouts": 0,
    }
    base = datetime(2026, 1, 1, tzinfo=UTC)
    resources = []
    for second in range(1, 21):
        resources.extend(
            [
                {
                    "host": "edge1",
                    "timestamp": (base + timedelta(seconds=second)).isoformat(),
                    "cpu_percent": 95.0,
                },
                {
                    "host": "edge2",
                    "timestamp": (base + timedelta(seconds=second)).isoformat(),
                    "cpu_percent": 100.0,
                },
            ]
        )
    trigger = evaluate_trigger(config, scheduler, resources)
    assert trigger["triggered"] is True
    assert trigger["trigger_resource_host"] == "edge2"
    assert trigger["metrics"]["resource_sample_count"] == 20
    assert trigger["maximum_consecutive_degraded_cycles"] == 2


def test_sustained_cpu_sample_series_triggers_despite_short_cycle_troughs(root):
    config = replace(
        _config(root),
        thresholds=TriggerThresholds(90, 40, 0.2, 10000, 0.5, 1),
        consecutive_trigger_cycles=3,
        trigger_resource_hosts=("edge1",),
    )
    scheduler = {
        "events": [_event(index * 10, compliant=True, latency_ms=10) for index in range(1, 7)],
        "monitoring_compliance": 1.0,
        "logical_timeouts": 0,
    }
    base = datetime(2026, 1, 1, tzinfo=UTC)
    cpu = [100.0, 100.0, 10.0, 100.0, 100.0, 10.0] * 10
    resources = [
        {
            "host": "edge1",
            "timestamp": (base + timedelta(seconds=index + 1)).isoformat(),
            "cpu_percent": value,
        }
        for index, value in enumerate(cpu)
    ]
    trigger = evaluate_trigger(config, scheduler, resources)
    assert trigger["triggered"] is True
    assert trigger["sustained_resource_samples"] is True
    assert trigger["persistence_basis"] == "resource_sample_series"


def test_plan_filters_capacity_and_governance_and_selects_eligible_preference(root):
    config = replace(_config(root), excluded_targets=("edge3",))
    analysis = {"conclusion": "additional_capacity_required"}
    candidates = [
        {
            "id": "edge2",
            "tier": "edge",
            "connected": True,
            "worker_ready": True,
            "worker_idle": True,
            "available_memory_mib": 8000,
            "cpu_count": 4,
            "load_1m": 1.0,
            "replica_port_available": True,
        },
        {
            "id": "edge3",
            "tier": "edge",
            "connected": True,
            "worker_ready": True,
            "worker_idle": True,
            "available_memory_mib": 8000,
            "cpu_count": 4,
            "load_1m": 1.0,
            "replica_port_available": True,
        },
        {
            "id": "fog",
            "tier": "fog",
            "connected": True,
            "worker_ready": True,
            "worker_idle": True,
            "available_memory_mib": 100,
            "cpu_count": 4,
            "load_1m": 1.0,
            "replica_port_available": True,
        },
    ]
    plan = plan_adaptation(config, analysis, candidates, "2026-01-01T00:00:00+00:00")
    assert plan["status"] == "planned"
    assert plan["target"] == "edge2"
    assert plan["selected_target"] == "edge2"
    assert "governance_constraint" in plan["rejected_candidates"]["edge3"]
    assert "insufficient_residual_memory" in plan["rejected_candidates"]["fog"]


def test_plan_fails_when_no_candidate_is_eligible(root):
    config = replace(_config(root), fallback_to_ranked_candidate=False)
    candidate = {
        "id": "edge2",
        "tier": "edge",
        "connected": False,
        "worker_ready": False,
        "worker_idle": False,
        "available_memory_mib": 0,
        "cpu_count": 4,
        "load_1m": 1.0,
        "replica_port_available": False,
    }
    plan = plan_adaptation(
        config,
        {"conclusion": "additional_capacity_required"},
        [candidate],
        "2026-01-01T00:00:00+00:00",
    )
    assert plan["status"] == "planning_failed"
    assert plan["target"] is None
    assert plan["selected_target"] is None


def test_replica_routing_alternates_without_adding_a_partition_participant():
    source = Host("edge1", "edge", "a", "127.0.0.1", 8001)
    peer = Host("edge2", "edge", "b", "127.0.0.1", 8002)
    replica = Host("edge1-replica-on-edge2", "edge", "a", "127.0.0.1", 9001)
    router = ReplicaRouter((source, peer), "edge1", replica)
    query = {"execution_scope": "authorities"}
    first = router.select(query, 1, 0, "distributed")
    second = router.select(query, 1, 0, "distributed")
    assert [host.id for host in first] == ["edge1", "edge2"]
    assert [host.id for host in second] == ["edge1-replica-on-edge2", "edge2"]
    assert len(first) == len(second) == 2


def test_execute_requires_an_explicit_completed_plan(root, tmp_path):
    config = _config(root)
    with pytest.raises(ValueError, match="requires a completed"):
        deploy_read_only_replica(config, None, tmp_path, {"status": "no_action"})


def test_before_and_after_must_use_the_same_workload():
    workload = {"scenario": "users-10000", "tasks": ["operational-node-state"]}
    require_same_workload(workload, dict(workload))
    with pytest.raises(RuntimeError, match="not identical"):
        require_same_workload(workload, workload | {"scenario": "users-20000"})


def test_adaptation_configuration_uses_existing_policies_queries_and_scenario(root):
    config = _config(root)
    manifest = json.loads((root / "queries/manifest.json").read_text())
    query_ids = {query["id"] for query in manifest["queries"]}
    assert config.trigger_policy == "P-ADAPT-03"
    assert set(config.trigger_query_ids) <= query_ids
    assert set(config.candidate_query_ids) <= query_ids
    assert config.adaptation_context_query_id in query_ids
    assert config.scenario in {scenario.name for scenario in config.benchmark.scenarios}


def test_adaptation_report_preserves_measured_deltas_without_claiming_improvement(tmp_path):
    run_dir = tmp_path / "adaptation-run"
    before = run_dir / "before"
    after = run_dir / "after"
    execute = run_dir / "execute"
    for directory in (before, after, execute):
        directory.mkdir(parents=True)
    metrics = {
        "logical_latency_p50_ms": 10.0,
        "logical_latency_p95_ms": 20.0,
        "logical_latency_p99_ms": 30.0,
        "logical_timeouts": 0,
        "monitoring_compliance": 1.0,
        "schedule_lag_p50_seconds": 0.1,
        "schedule_lag_p95_seconds": 0.2,
        "schedule_lag_p99_seconds": 0.3,
        "cpu_mean_percent": 10.0,
        "cpu_peak_percent": 20.0,
        "memory_mean_bytes": 100.0,
        "memory_peak_bytes": 200.0,
        "network_rx_bytes": 10,
        "network_tx_bytes": 20,
        "physical_query_executions": 2,
    }
    (before / "result.json").write_text(json.dumps({"metrics": metrics}))
    (after / "result.json").write_text(
        json.dumps({"metrics": metrics | {"logical_latency_p95_ms": 25.0}, "same_workload_verified": True})
    )
    logical = json.dumps({"query_id": "Q", "status": "completed", "result_digest": "same"}) + "\n"
    (before / "logical_queries.jsonl").write_text(logical)
    (after / "logical_queries.jsonl").write_text(logical)
    (execute / "result.json").write_text(json.dumps({"replica_ready_seconds": 2.0}))
    (run_dir / "manifest.json").write_text(json.dumps({"status": "verified"}))
    output = report(run_dir)
    summary = json.loads((output / "summary.json").read_text())
    assert summary["all_common_query_digests_equivalent"] is True
    latency = next(item for item in summary["metrics"] if item["metric"] == "logical_latency_p95_ms")
    assert latency["delta"] == 5.0
    assert "does not imply performance improvement" in summary["interpretation"]


def test_adaptation_report_accepts_a_valid_no_action_outcome(tmp_path):
    run_dir = tmp_path / "adaptation-no-action"
    (run_dir / "before").mkdir(parents=True)
    (run_dir / "execute").mkdir()
    baseline = {
        "logical_latency_p95_ms": 20.0,
        "monitoring_compliance": 1.0,
        "per_host": {"edge1": {"cpu_peak_percent": 75.0}},
    }
    (run_dir / "before/result.json").write_text(json.dumps({"metrics": baseline}))
    (run_dir / "before/logical_queries.jsonl").write_text("")
    (run_dir / "execute/result.json").write_text(
        json.dumps({"status": "skipped_no_action", "infrastructure_changed": False})
    )
    (run_dir / "manifest.json").write_text(json.dumps({"status": "verified_no_action"}))

    output = report(run_dir)
    summary = json.loads((output / "summary.json").read_text())
    latency = next(item for item in summary["metrics"] if item["metric"] == "logical_latency_p95_ms")
    assert summary["adaptation_outcome"] == "no_action"
    assert summary["same_workload_verified"] is None
    assert summary["all_common_query_digests_equivalent"] is None
    assert latency == {"metric": "logical_latency_p95_ms", "before": 20.0, "after": None, "delta": None}
    assert "No replica was deployed" in (output / "report.md").read_text()


def test_adaptation_report_rejects_duplicate_container_resource_aliases(tmp_path):
    run_dir = tmp_path / "adaptation-collision"
    for directory in (run_dir / "before", run_dir / "after", run_dir / "execute"):
        directory.mkdir(parents=True)
    metrics = {
        "cpu_mean_percent": 10.0,
        "cpu_peak_percent": 20.0,
        "memory_mean_bytes": 100.0,
        "memory_peak_bytes": 200.0,
        "network_rx_bytes": 10,
        "network_tx_bytes": 20,
        "per_host": {
            "mist": {"cpu_mean_percent": 10.0},
            "edge3-replica-on-mist": {"cpu_mean_percent": 10.0},
        },
    }
    (run_dir / "before" / "result.json").write_text(json.dumps({"metrics": metrics}))
    (run_dir / "after" / "result.json").write_text(json.dumps({"metrics": metrics, "same_workload_verified": True}))
    logical = json.dumps({"query_id": "Q", "status": "completed", "result_digest": "same"}) + "\n"
    for phase in ("before", "after"):
        (run_dir / phase / "logical_queries.jsonl").write_text(logical)
    (run_dir / "before" / "resource_samples.jsonl").write_text(
        json.dumps({"host": "mist", "container_id": "base"}) + "\n"
    )
    (run_dir / "after" / "resource_samples.jsonl").write_text(
        json.dumps({"host": "mist", "container_id": "duplicate"})
        + "\n"
        + json.dumps({"host": "edge3-replica-on-mist", "container_id": "duplicate"})
        + "\n"
    )
    (run_dir / "execute" / "result.json").write_text(
        json.dumps({"status": "replica_ready", "replica": {"id": "edge3-replica-on-mist"}})
    )
    (run_dir / "manifest.json").write_text(json.dumps({"status": "verified"}))

    summary = json.loads((report(run_dir) / "summary.json").read_text())
    assert summary["resource_telemetry_audit"]["after"]["valid"] is False
    assert summary["resource_telemetry_audit"]["after"]["invalid_logical_hosts"] == ["mist"]
    cpu = next(row for row in summary["metrics"] if row["metric"] == "cpu_mean_percent")
    assert cpu["after"] is None
    assert not any(row["host"] == "mist" and row["after"] is not None for row in summary["node_metrics"])
