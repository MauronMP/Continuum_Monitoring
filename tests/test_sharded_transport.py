from dataclasses import replace
from types import SimpleNamespace

from continuum_bench import sharded
from continuum_bench.distributed import Endpoint


def _response(query_ids, *, attempts=1):
    measurements = [
        {
            "query_id": query_id,
            "category": "observability",
            "tier": "extended",
            "duration_ms": 1.0,
            "result_count": 1,
            "ask_result": None,
            "result_digest": query_id,
            "result_keys": [query_id],
            "result_group_keys": [],
        }
        for query_id in query_ids
    ]
    return {
        "role": "edge3",
        "mode": "partitioned",
        "reasoner": "rdfs",
        "synthetic_users": 10,
        "query_count": len(query_ids),
        "query_wall_ms": float(len(query_ids)),
        "query_cpu_ms": float(len(query_ids)),
        "process_cpu_ms": float(len(query_ids)),
        "current_rss_kib": 100,
        "peak_rss_kib": 110,
        "disk_read_bytes": 2,
        "disk_write_bytes": 3,
        "request_bytes": 10,
        "response_bytes": 20,
        "measurements": measurements,
        "_coordinator_attempts": attempts,
    }


def test_partitioned_queries_are_bounded_and_aggregated(
    config,
    monkeypatch,
):
    transport = replace(
        config.distributed,
        request_timeout_seconds=30,
        request_retries=0,
        query_batch_size=2,
        worker_timeout_margin_seconds=1,
    )
    config = replace(config, distributed=transport)
    endpoint = Endpoint("http://edge3", "edge3")
    specs = [SimpleNamespace(id=f"Q{index:03d}") for index in range(5)]
    calls = []

    def fake_parallel(
        endpoints,
        path,
        payloads,
        *,
        phase,
        timeout,
        retries,
    ):
        calls.append((path, payloads, phase, timeout, retries))
        payload = payloads[endpoint.url]
        return 4.0, {
            endpoint.url: _response(payload["query_ids"]),
        }

    monkeypatch.setattr(sharded, "_parallel", fake_parallel)

    wall_ms, responses = sharded._query(
        config,
        [endpoint],
        {endpoint.url: specs},
    )

    assert wall_ms == 12.0
    assert [call[1][endpoint.url]["query_ids"] for call in calls] == [
        ["Q000", "Q001"],
        ["Q002", "Q003"],
        ["Q004"],
    ]
    assert all(
        call[1][endpoint.url]["phase_timeout_seconds"] == 29
        for call in calls
    )
    assert all(call[3:] == (30, 0) for call in calls)
    response = responses[endpoint.url]
    assert response["query_batch_count"] == 3
    assert response["query_count"] == 5
    assert response["request_bytes"] == 30
    assert response["response_bytes"] == 60
    assert [item["query_id"] for item in response["measurements"]] == [
        "Q000",
        "Q001",
        "Q002",
        "Q003",
        "Q004",
    ]


def test_partitioned_prepare_has_worker_deadline(config, monkeypatch):
    endpoint = Endpoint("http://edge3", "edge3")
    captured = {}

    def fake_parallel(endpoints, path, payloads, **options):
        captured.update(payloads[endpoint.url])
        return 0.0, {endpoint.url: {}}

    monkeypatch.setattr(sharded, "_parallel", fake_parallel)

    sharded._prepare(config, [endpoint], "rdfs", 10, 2026)

    assert captured["phase_timeout_seconds"] == (
        config.distributed.request_timeout_seconds
        - config.distributed.worker_timeout_margin_seconds
    )
