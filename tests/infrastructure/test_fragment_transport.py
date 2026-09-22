"""Workers ingest transported placement, never canonical private source data."""
from threading import RLock

import pytest
from rdflib.compare import isomorphic

from continuum_bench import node, partitioning
from continuum_bench.partitioning import (
    build_fragments, deserialize_fragment, serialize_fragment,
)


@pytest.fixture(scope="module")
def fragments(config):
    return build_fragments(config, 5)


def test_transport_roundtrip_preserves_each_assignment(fragments):
    for role, expected in fragments.graphs.items():
        payload = serialize_fragment(fragments, role, users=5, seed=2026)
        graph, descriptor = deserialize_fragment(payload, role, users=5, seed=2026)
        assert isomorphic(graph, expected)
        assert set(descriptor.graphs) == {role}
        assert descriptor.reference_triples == fragments.reference_triples
        assert len(graph) < len(fragments.union())


@pytest.mark.parametrize("field,value", [
    ("node_id", "edge2"), ("users", 99), ("seed", 99),
    ("contract", "unknown"), ("data", ""), ("profile", "tampered"),
    ("sha256", "bad"), ("format", "xml"),
])
def test_transport_rejects_mismatch(fragments, field, value):
    payload = serialize_fragment(fragments, "edge1", users=5, seed=2026)
    payload[field] = value
    with pytest.raises(ValueError):
        deserialize_fragment(payload, "edge1", users=5, seed=2026)


@pytest.mark.parametrize("role", ["cloud", "fog", "edge1"])
def test_worker_materializes_and_recovers_only_transport(fragments, monkeypatch, role):
    payload = serialize_fragment(fragments, role, users=5, seed=2026)
    runtime = node.NodeRuntime.__new__(node.NodeRuntime)
    runtime.role = role
    runtime.base_graph = None
    runtime.lock = RLock()

    def forbidden(*args, **kwargs):
        pytest.fail("Worker accessed canonical data or generated unassigned data")

    for name in ("load_graph", "add_synthetic_data", "add_synthetic_rules",
                 "pad_to_target_triples"):
        monkeypatch.setattr(node, name, forbidden)
    for name in ("build_role_graph", "build_fragments", "load_substrate",
                 "load_reference_abox", "iter_synthetic_triples"):
        monkeypatch.setattr(partitioning, name, forbidden)
    original = node.materialize
    materialized = []

    def local_only(graph, reasoner):
        assert isomorphic(graph, fragments.graphs[role])
        materialized.append(len(graph))
        return original(graph, reasoner)

    monkeypatch.setattr(node, "materialize", local_only)
    result = runtime.prepare("rdfs", 5, 2026, mode="distributed", fragment=payload)
    assert result["fragment_sha256"] == payload["sha256"]
    assert result["reasoning_scope"] == "local-fragment-closure"
    assert runtime.base_graph is None
    recovered = runtime.recover()
    assert recovered["input_triples"] == payload["triples"]
    assert len(materialized) == 2


@pytest.mark.parametrize("mode", ["distributed", "partitioned"])
def test_worker_rejects_missing_fragment_without_local_fallback(mode):
    runtime = node.NodeRuntime.__new__(node.NodeRuntime)
    runtime.role = "edge1"
    runtime.lock = RLock()
    with pytest.raises(ValueError, match="requires a serialized fragment"):
        runtime.prepare("rdfs", 5, 2026, mode=mode)


def test_http_prepare_decodes_only_assigned_fragment(fragments, monkeypatch):
    from io import BytesIO
    import json
    from types import SimpleNamespace

    payload = serialize_fragment(fragments, "edge1", users=5, seed=2026)
    body = json.dumps({
        "reasoner": "rdfs", "users": 5, "seed": 2026,
        "mode": "distributed", "fragment": payload,
    }).encode()
    runtime = node.NodeRuntime.__new__(node.NodeRuntime)
    runtime.role = "edge1"
    runtime.lock = RLock()
    handler = node.Handler.__new__(node.Handler)
    handler.path = "/prepare"
    handler.headers = {"Content-Length": str(len(body))}
    handler.rfile = BytesIO(body)
    handler.server = SimpleNamespace(runtime=runtime)
    responses = []
    handler._json = lambda status, result, **kwargs: responses.append((status, result))

    def materialize(graph, reasoner):
        assert isomorphic(graph, fragments.graphs["edge1"])
        return SimpleNamespace(graph=graph, duration_ms=0, input_triples=len(graph),
                               output_triples=len(graph), inferred_triples=0)

    monkeypatch.setattr(node, "materialize", materialize)
    node.Handler.do_POST(handler)
    assert responses[0][0] == 200
    assert responses[0][1]["fragment_sha256"] == payload["sha256"]
    assert responses[0][1]["request_bytes"] == len(body)


def test_transport_checks_triple_count_after_hash_validation(fragments):
    payload = serialize_fragment(fragments, "edge1", users=5, seed=2026)
    payload["triples"] += 1
    payload["sha256"] = partitioning._fragment_hash(payload)
    with pytest.raises(ValueError, match="triple count mismatch"):
        deserialize_fragment(payload, "edge1", users=5, seed=2026)


def test_coordinator_transports_fragments_and_times_placement(config, monkeypatch):
    from types import SimpleNamespace
    from continuum_bench.monitoring import distributed_ontology as distributed
    from continuum_bench.distributed import Endpoint

    endpoints = [Endpoint("http://" + role, role) for role in
                 ("cloud", "fog", "edge1", "edge2", "edge3")]
    clock = [100.0]
    builds = []
    original_build = partitioning.build_fragments

    def build(*args, **kwargs):
        result = original_build(*args, **kwargs)
        builds.append(result)
        clock[0] += 2.0
        return result

    monkeypatch.setattr(partitioning, "build_fragments", build)
    monkeypatch.setattr(distributed, "monotonic", lambda: clock[0])
    monkeypatch.setattr("continuum_bench.monitoring.budget.monotonic", lambda: clock[0])
    monkeypatch.setattr(node, "materialize", lambda graph, reasoner: SimpleNamespace(
        graph=graph, duration_ms=0, input_triples=len(graph),
        output_triples=len(graph), inferred_triples=0,
    ))

    def parallel(active, path, payloads, **kwargs):
        assert len(builds) == 1
        assert path == "/prepare"
        assert kwargs["timeout"] == min(
            min(config.limits.point_timeout_seconds, config.limits.phase_timeout_seconds) - 2,
            config.distributed.request_timeout_seconds,
        )
        results = {}
        for endpoint in active:
            runtime = node.NodeRuntime.__new__(node.NodeRuntime)
            runtime.role = endpoint.role
            runtime.lock = RLock()
            payload = payloads[endpoint.url]
            assert payload["mode"] == "distributed"
            results[endpoint.url] = runtime.prepare(**payload)
            assert isomorphic(runtime.graph, builds[0].graphs[endpoint.role])
        clock[0] += 3.0
        return 3000.0, results

    monkeypatch.setattr(distributed, "_parallel", parallel)
    wall_ms, prepared = distributed._prepare(config, endpoints, "rdfs", 5, 2026)
    assert wall_ms == 5000.0
    assert len(builds) == 1
    assert all(result["coordinator_placement_ms"] == 2000 for result in prepared.values())
    assert all(result["placement_validation"] == "observed-worker-fragment-match"
               for result in prepared.values())


def test_coordinator_rejects_unconfirmed_worker_placement(config, monkeypatch):
    from continuum_bench.monitoring import distributed_ontology as distributed
    from continuum_bench.distributed import Endpoint

    endpoints = [Endpoint("http://cloud", "cloud"), Endpoint("http://edge1", "edge1")]
    monkeypatch.setattr(distributed, "_parallel", lambda *args, **kwargs:
                        (1.0, {endpoint.url: {} for endpoint in endpoints}))
    with pytest.raises(ValueError, match="did not confirm"):
        distributed._prepare(config, endpoints, "rdfs", 0, 2026)


def test_placement_exhaustion_prevents_transport(config, monkeypatch):
    from continuum_bench.monitoring import distributed_ontology as distributed
    from continuum_bench.monitoring.budget import PhaseBudgetTimeout
    from continuum_bench.distributed import Endpoint

    clock = [100.0]
    original_build = partitioning.build_fragments

    def build(*args, **kwargs):
        result = original_build(*args, **kwargs)
        clock[0] += config.limits.point_timeout_seconds + 1
        return result

    monkeypatch.setattr(distributed, "monotonic", lambda: clock[0])
    monkeypatch.setattr("continuum_bench.monitoring.budget.monotonic", lambda: clock[0])
    monkeypatch.setattr(partitioning, "build_fragments", build)
    monkeypatch.setattr(distributed, "_parallel", lambda *args, **kwargs:
                        pytest.fail("No transport after placement exhausts budget"))
    endpoints = [Endpoint("http://cloud", "cloud"), Endpoint("http://edge1", "edge1")]
    with pytest.raises(PhaseBudgetTimeout):
        distributed._prepare(config, endpoints, "rdfs", 0, 2026)
