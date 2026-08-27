import pytest
from urllib.error import URLError

from continuum_bench import distributed
from continuum_bench.distributed import Endpoint, _assignment
from continuum_bench.protocol import worker_health_error
from continuum_bench.queries import load_catalog
from continuum_bench.reasoners import REASONING_CONTRACT


def test_docker_role_assignment_routes_every_query_once(config):
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    endpoints = [
        Endpoint("http://cloud", "cloud"),
        Endpoint("http://fog", "fog"),
        Endpoint("http://edge1", "edge1"),
        Endpoint("http://edge2", "edge2"),
        Endpoint("http://edge3", "edge3"),
    ]
    assigned = _assignment(specs, endpoints)
    flattened = [
        spec.id for endpoint_specs in assigned.values() for spec in endpoint_specs
    ]
    assert len(flattened) == 115
    assert len(set(flattened)) == 115
    assert assigned["http://cloud"]
    assert assigned["http://fog"]
    assert all(assigned[f"http://edge{index}"] for index in (1, 2, 3))


def test_discover_rejects_an_unrelated_health_service(monkeypatch):
    monkeypatch.setattr(
        distributed,
        "_request",
        lambda *args, **kwargs: {
            "status": "ok",
            "protocol_version": "5",
            "node_role": "fog",
            "build_id": "continuum-v5-contract",
        },
    )

    with pytest.raises(
        RuntimeError,
        match="Incompatible continuum worker.*service",
    ):
        distributed.discover(["http://192.168.1.137:8080"])


def test_request_retries_a_transient_disconnect(monkeypatch):
    attempts = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        @staticmethod
        def read():
            return b'{"status": "ok"}'

    def fake_urlopen(request, timeout):
        attempts.append((request.full_url, timeout))
        if len(attempts) == 1:
            raise URLError("temporary Wi-Fi reset")
        return Response()

    monkeypatch.setattr(distributed, "urlopen", fake_urlopen)
    monkeypatch.setattr(distributed, "sleep", lambda value: None)

    result = distributed._request(
        "http://edge2",
        "/health",
        timeout=9.0,
        retries=1,
    )

    assert result == {"status": "ok", "_coordinator_attempts": 2}
    assert attempts == [
        ("http://edge2/health", 9.0),
        ("http://edge2/health", 9.0),
    ]


def test_worker_health_rejects_an_old_ontology_release():
    health = {
        "status": "ok",
        "service": "continuum-benchmark-node",
        "protocol_version": "5",
        "ontology_version": "2.3.0",
        "query_count": 69,
        "role": "fog",
    }

    assert "ontology_version" in worker_health_error(health)

    health.update(ontology_version="3.0.0", query_count=115)
    assert "reasoning_contract" in worker_health_error(health)
    health["reasoning_contract"] = REASONING_CONTRACT
    assert worker_health_error(health, expected_role="fog") is None
