from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from time import monotonic, sleep

import pytest

from continuum_bench.distributed import Endpoint
from continuum_bench.load_benchmark import (
    _is_timeout,
    _run_event_stream,
    _workload_specs,
)
from continuum_bench.load_config import (
    LoadBenchmarkConfig,
    LoadProfile,
    load_load_config,
    select_load_profiles,
)
from continuum_bench.load_reporting import (
    _aggregate,
)
from continuum_bench.queries import QuerySpec


def _config(tmp_path: Path) -> LoadBenchmarkConfig:
    return LoadBenchmarkConfig(
        path=tmp_path / "load.toml",
        profiles=(),
        repetitions=1,
        batch_size=4,
        queue_capacity_events=20,
        request_timeout_seconds=1,
        point_timeout_seconds=2,
        recovery_timeout_seconds=1,
        seed=2026,
    )


def _spec(query_id: str, expectation: str) -> QuerySpec:
    return QuerySpec(
        order=1,
        id=query_id,
        tier="core",
        category="policy_governance",
        kind="ASK" if expectation == "true" else "SELECT",
        expectation=expectation,
        path=Path(f"{query_id}.rq"),
        title="Synthetic alert query",
    )


def test_full_load_config_covers_all_independent_variables_and_high_scale(
    config,
):
    workload = load_load_config(config.root / "configs/load-benchmark.toml")

    assert {profile.dimension for profile in workload.profiles} == {
        "events_per_second",
        "users",
        "target_triples",
        "rule_count",
        "node_count",
    }
    assert max(profile.events_per_second for profile in workload.profiles) >= 2500
    assert max(profile.users for profile in workload.profiles) >= 10000
    assert max(profile.target_triples for profile in workload.profiles) >= 500000
    assert max(profile.rule_count for profile in workload.profiles) >= 250
    assert max(profile.node_count for profile in workload.profiles) == 5

    selected = select_load_profiles(
        workload,
        dimensions=["events_per_second"],
        names=["eps-2500"],
    )
    assert [profile.name for profile in selected.profiles] == ["eps-2500"]


def test_load_workload_covers_every_query_category(config):
    specs = _workload_specs(config)

    assert len(specs) == 115
    assert {spec.category for spec in specs} == set(config.category_order)
    assert {spec.category for spec in specs[: len(config.category_order)]} == (
        set(config.category_order)
    )


def test_event_stream_measures_latency_throughput_loss_and_alert_accuracy(
    tmp_path,
):
    profile = LoadProfile(
        name="unit",
        dimension="events_per_second",
        events_per_second=40,
        duration_seconds=0.1,
        users=0,
        target_triples=0,
        rule_count=0,
        node_count=1,
    )
    specs = [_spec("POS", "true"), _spec("NEG", "zero_rows")]

    def invoke(endpoint, query_ids, timeout):
        sleep(0.001)
        return {
            "measurements": [
                {
                    "duration_ms": 0.1,
                    "result_count": 1 if query_id == "POS" else 0,
                    "ask_result": query_id == "POS" if query_id == "POS" else None,
                }
                for query_id in query_ids
            ],
            "process_cpu_ms": 0.2,
            "current_rss_kib": 80,
            "peak_rss_kib": 100,
            "request_bytes": 20,
            "response_bytes": 40,
        }

    summary, rows, node_metrics = _run_event_stream(
        profile,
        _config(tmp_path),
        specs,
        [Endpoint("http://worker:8391", "cloud")],
        invoke,
        {"architecture": "physical"},
    )

    assert summary["events_offered"] == 4
    assert summary["events_processed"] == 4
    assert summary["events_lost"] == 0
    assert summary["latency_p50_ms"] >= 0
    assert summary["latency_p50_ms"] <= summary["latency_p95_ms"]
    assert summary["latency_p95_ms"] <= summary["latency_p99_ms"]
    assert summary["events_processed_per_second"] > 0
    assert summary["alert_precision"] == 1
    assert summary["alert_accuracy"] == 1
    assert summary["alerts_evaluated"] == 4
    assert len(rows) == 4
    assert sum(row["process_cpu_ms"] for row in rows) == pytest.approx(
        node_metrics["cloud"]["process_cpu_ms"]
    )
    assert all(row["current_rss_kib"] == 80 for row in rows)
    assert all(
        row["resource_attribution"]
        == "batch-duration-proportional;rss-observed"
        for row in rows
    )
    assert node_metrics["cloud"]["events"] == 4


def test_event_stream_records_queue_loss(tmp_path):
    profile = LoadProfile(
        name="loss",
        dimension="events_per_second",
        events_per_second=1000,
        duration_seconds=0.01,
        users=0,
        target_triples=0,
        rule_count=0,
        node_count=1,
    )
    workload = replace(
        _config(tmp_path),
        batch_size=1,
        queue_capacity_events=1,
    )
    specs = [_spec("POS", "true"), _spec("NEG", "zero_rows")]

    def slow_invoke(endpoint, query_ids, timeout):
        sleep(0.03)
        return {
            "measurements": [
                {
                    "duration_ms": 30,
                    "result_count": 1,
                    "ask_result": True,
                }
                for _ in query_ids
            ]
        }

    summary, rows, _ = _run_event_stream(
        profile,
        workload,
        specs,
        [Endpoint("http://worker:8391", "cloud")],
        slow_invoke,
        {},
    )

    assert summary["events_lost"] > 0
    assert any(row["lost_reason"] == "queue_capacity" for row in rows)


def test_point_timeout_returns_without_waiting_for_running_worker(tmp_path):
    profile = LoadProfile(
        name="deadline",
        dimension="events_per_second",
        events_per_second=10,
        duration_seconds=0.1,
        users=0,
        target_triples=0,
        rule_count=0,
        node_count=1,
    )
    workload = replace(
        _config(tmp_path),
        batch_size=1,
        point_timeout_seconds=0.05,
    )

    def blocked_worker(endpoint, query_ids, timeout):
        sleep(0.5)
        return {"measurements": []}

    started = monotonic()
    summary, rows, _ = _run_event_stream(
        profile,
        workload,
        [_spec("POS", "true")],
        [Endpoint("http://worker:8391", "cloud")],
        blocked_worker,
        {},
    )

    assert monotonic() - started < 0.25
    assert summary["events_lost"] == 1
    assert rows[0]["lost_reason"] == "point_timeout_in_flight"


@pytest.mark.parametrize(
    "message",
    [
        "TimeoutError: phase timeout",
        "URLError: operation timed out",
        "HTTP Error 408: Request Timeout",
    ],
)
def test_timeout_detection_accepts_common_spellings(message):
    assert _is_timeout(message)


def test_load_reporting_computes_timeout_rate_for_physical_rows():
    base = {
        "profile": "eps-50",
        "dimension": "events_per_second",
        "reasoner": "rdfs",
        "events_per_second": "50",
        "synthetic_users": "500",
        "target_triples": "25000",
        "rule_count": "25",
        "latency_p50_ms": "5",
        "latency_p95_ms": "10",
        "latency_p99_ms": "15",
        "events_processed_per_second": "40",
        "event_loss_percent": "0",
        "inference_wall_ms": "100",
        "pipeline_wall_ms": "1000",
        "recovery_wall_ms": "100",
        "node_count": "1",
        "status": "completed",
    }
    physical = {
        **base,
        "architecture": "physical",
        "latency_p95_ms": "5",
        "events_processed_per_second": "100",
        "inference_wall_ms": "50",
        "recovery_wall_ms": "50",
        "node_count": "5",
        "status": "completed",
    }
    aggregate = _aggregate([physical])
    physical_row = next(
        row for row in aggregate if row["architecture"] == "physical"
    )

    assert physical_row["timeout_rate_percent_median"] == 0
    assert physical_row["target_triples_median"] == 25000

    timeout_aggregate = _aggregate(
        [
            {
                **physical,
                "profile": "eps-timeout",
                "status": "workload_timeout",
            }
        ]
    )
    assert timeout_aggregate[0]["timeout_rate_percent_median"] == 100
    assert timeout_aggregate[0]["comparison_eligible"] is False


def test_unlimited_stream_drains_slow_requests_after_point_budget(tmp_path):
    from continuum_bench.monitoring.budget import execution_policy
    profile = LoadProfile(name='slow', dimension='events_per_second',
                          events_per_second=10, duration_seconds=0.1, users=0,
                          target_triples=0, rule_count=0, node_count=1)
    workload = replace(_config(tmp_path), batch_size=1, point_timeout_seconds=0.001)
    def invoke(endpoint, query_ids, timeout):
        sleep(0.05)
        return {'measurements': [{'duration_ms':50, 'result_count':1, 'ask_result':True}]}
    with execution_policy(True):
        summary, rows, _ = _run_event_stream(profile, workload, [_spec('POS', 'true')],
            [Endpoint('http://worker:8391', 'cloud')], invoke, {}, point_timeout_seconds=-1)
    assert summary['events_processed'] == 1
    assert summary['events_lost'] == 0
    assert summary['timed_out'] is False
    assert len(rows) == 1
