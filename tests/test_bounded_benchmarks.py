import csv
from dataclasses import replace

from rdflib import Graph

from continuum_bench import distributed, engines, physical, sharded
from continuum_bench.budget import (
    PhaseBudgetTimeout,
    failure_status,
    is_boundary_failure,
)
from continuum_bench.distributed import Endpoint
from continuum_bench.queries import QuerySpec, load_catalog


def test_nested_broken_pipe_is_a_transport_observation():
    try:
        try:
            raise BrokenPipeError("peer closed while uploading")
        except BrokenPipeError as error:
            raise RuntimeError("engine request failed") from error
    except RuntimeError as error:
        assert is_boundary_failure(error)
        assert failure_status(error) == "transport_error"


def test_engine_scalability_censors_failure_and_skips_larger_block(
    config,
    tmp_path,
    monkeypatch,
):
    limits = replace(
        config.limits,
        phase_timeout_seconds=0.1,
        point_timeout_seconds=0.2,
    )
    bounded = replace(
        config,
        scale_users=(0, 1),
        repetitions=1,
        limits=limits,
    )
    query_path = tmp_path / "query.rq"
    query_path.write_text("ASK { ?s ?p ?o }", encoding="utf-8")
    spec = QuerySpec(
        order=1,
        id="TEST-Q01",
        tier="core",
        category="topology",
        kind="ask",
        expectation="none",
        path=query_path,
        title="bounded request",
    )
    endpoint = engines.EngineEndpoint(
        "http://jena",
        "jena",
        "test",
        "rdfs",
    )
    monkeypatch.setattr(engines, "discover", lambda urls: [endpoint])
    monkeypatch.setattr(engines, "_load", lambda config: (Graph(), [spec]))

    def broken_request(url, path, payload=None, timeout=60):
        raise BrokenPipeError("container closed the upload")

    monkeypatch.setattr(engines, "_request", broken_request)

    output = engines.run_engine_scalability(
        bounded,
        [endpoint.url],
        tmp_path / "results",
    )

    with (output / "summary.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["status"] for row in rows] == [
        "transport_error",
        "skipped_after_timeout",
    ]
    assert all(row["censored"] == "True" for row in rows)


def test_physical_calibration_is_sampled_and_estimates_every_query(
    config,
    monkeypatch,
):
    limits = replace(config.limits, calibration_query_limit=3)
    bounded = replace(config, limits=limits)
    specs = load_catalog(config.resolve(config.query_catalog), config.root)[:12]
    endpoint = Endpoint("http://edge", "edge1")
    captured = {}

    def fake_query(config, endpoints, assignment, **options):
        captured["ids"] = [spec.id for spec in assignment[endpoint.url]]
        measurements = [
            {"query_id": query_id, "duration_ms": float(index + 1)}
            for index, query_id in enumerate(captured["ids"])
        ]
        return 4.0, {
            endpoint.url: {
                "query_cpu_ms": sum(
                    item["duration_ms"] for item in measurements
                ),
                "measurements": measurements,
            }
        }

    monkeypatch.setattr(physical, "_query", fake_query)

    _, costs, _ = physical._calibrate(bounded, [endpoint], specs)

    assert len(captured["ids"]) == 3
    assert set(costs[endpoint.url]) == {spec.id for spec in specs}
    assert all(
        item["duration_ms"] > 0 for item in costs[endpoint.url].values()
    )


def test_replicated_queries_use_batches_and_worker_deadlines(
    config,
    monkeypatch,
):
    transport = replace(
        config.distributed,
        request_timeout_seconds=10,
        query_batch_size=2,
        worker_timeout_margin_seconds=1,
    )
    limits = replace(config.limits, point_timeout_seconds=20)
    bounded = replace(config, distributed=transport, limits=limits)
    endpoint = Endpoint("http://edge", "edge1")
    specs = [type("Spec", (), {"id": f"Q{index}"})() for index in range(5)]
    calls = []

    def fake_parallel(endpoints, path, payloads, **options):
        payload = payloads[endpoint.url]
        calls.append((payload, options))
        measurements = [
            {"query_id": query_id, "duration_ms": 1.0}
            for query_id in payload["query_ids"]
        ]
        return 2.0, {
            endpoint.url: {
                "role": "edge1",
                "mode": "replicated",
                "reasoner": "rdfs",
                "synthetic_users": 1,
                "query_count": len(measurements),
                "query_wall_ms": len(measurements),
                "query_cpu_ms": len(measurements),
                "measurements": measurements,
            }
        }

    monkeypatch.setattr(distributed, "_parallel", fake_parallel)

    _, responses = distributed._query(
        bounded,
        [endpoint],
        {endpoint.url: specs},
    )

    assert [call[0]["query_ids"] for call in calls] == [
        ["Q0", "Q1"],
        ["Q2", "Q3"],
        ["Q4"],
    ]
    assert all(
        0 < call[0]["phase_timeout_seconds"] <= 9 for call in calls
    )
    assert responses[endpoint.url]["query_count"] == 5
    assert responses[endpoint.url]["query_batch_count"] == 3


def test_sharded_scalability_persists_timeout_instead_of_aborting(
    config,
    tmp_path,
    monkeypatch,
):
    bounded = replace(
        config,
        reasoners=("rdfs",),
        scale_users=(10, 100),
        repetitions=1,
    )
    endpoint = Endpoint("http://edge", "edge1")
    specs = load_catalog(config.resolve(config.query_catalog), config.root)[:1]
    monkeypatch.setattr(sharded, "discover", lambda *args: [endpoint])
    monkeypatch.setattr(sharded, "load_catalog", lambda *args: specs)

    def timeout(*args, **kwargs):
        raise PhaseBudgetTimeout("prepare exceeded the point budget")

    monkeypatch.setattr(sharded, "_prepare", timeout)

    output = sharded.run_sharded_scalability(
        bounded,
        [endpoint.url],
        tmp_path,
        target="docker",
        validate_results=False,
    )

    with (output / "summary.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["status"] for row in rows] == [
        "timeout",
        "skipped_after_timeout",
    ]
    assert (output / "query-runs.csv").is_file()
    assert (output / "node-query-runs.csv").is_file()
