from __future__ import annotations

from types import SimpleNamespace
from threading import RLock
from time import sleep

import pytest
from rdflib import Graph, URIRef

from continuum_bench import node
from continuum_bench.queries import QueryMeasurement
from continuum_bench.sharded import _summary


def _runtime() -> node.NodeRuntime:
    runtime = node.NodeRuntime.__new__(node.NodeRuntime)
    runtime.role = "edge1"
    runtime.config = object()
    runtime.base_graph = Graph()
    runtime.base_graph.add(
        (URIRef("urn:test:s"), URIRef("urn:test:p"), URIRef("urn:test:o"))
    )
    runtime.catalog = {"Q1": object()}
    runtime.graph = None
    runtime.reasoner = None
    runtime.users = None
    runtime.mode = "replicated"
    runtime.lock = RLock()
    return runtime


def test_worker_reports_cpu_and_peak_rss_for_prepare_and_queries(monkeypatch):
    runtime = _runtime()

    def fake_materialize(graph, reasoner):
        return SimpleNamespace(
            graph=graph,
            duration_ms=0.25,
            input_triples=len(graph),
            output_triples=len(graph),
            inferred_triples=0,
        )

    monkeypatch.setattr(node, "materialize", fake_materialize)
    monkeypatch.setattr(
        node,
        "execute_query",
        lambda graph, spec: QueryMeasurement(
            query_id="Q1",
            category="topology",
            tier="core",
            duration_ms=0.1,
            result_count=1,
            ask_result=None,
        ),
    )

    prepared = runtime.prepare("rdfs", users=0, seed=2026)
    queried = runtime.execute(["Q1"])

    for result in (prepared, queried):
        assert result["process_cpu_ms"] >= 0
        assert result["current_rss_kib"] > 0
        assert result["peak_rss_kib"] > 0


def test_partitioned_prepare_reports_placement_profile(monkeypatch):
    runtime = _runtime()
    source = Graph()
    source.add(
        (URIRef("urn:test:s"), URIRef("urn:test:p"), URIRef("urn:test:o"))
    )
    fragments = SimpleNamespace(
        synthetic_triples=0,
        substrate_triples=5,
        substrate_triples_by_role={"edge1": 3},
        placement_profiles={"edge1": "edge"},
        reference_triples=1,
        sensitive_resources=frozenset(),
    )
    monkeypatch.setattr(
        node,
        "build_role_graph",
        lambda config, role, users, seed: (source, fragments),
    )
    monkeypatch.setattr(
        node,
        "privacy_violations",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(
        node,
        "materialize",
        lambda graph, reasoner: SimpleNamespace(
            graph=graph,
            duration_ms=0.25,
            input_triples=len(graph),
            output_triples=len(graph),
            inferred_triples=0,
        ),
    )

    result = runtime.prepare("rdfs", users=0, seed=2026, mode="partitioned")

    assert result["profile"] == "edge"
    assert result["local_substrate_triples"] == 3


def test_transport_metrics_report_exact_encoded_body_size():
    payload, encoded = node._with_transport_metrics({"status": "ok"}, 123)

    assert payload["request_bytes"] == 123
    assert payload["response_bytes"] == len(encoded)


def test_worker_phase_timeout_interrupts_and_restores_signal_handler():
    with pytest.raises(node.WorkerPhaseTimeout):
        with node._worker_timeout(0.01):
            sleep(0.05)

    with node._worker_timeout(0):
        pass


def test_sharded_summary_aggregates_worker_telemetry():
    prepared = {
        "cloud": {
            "input_triples": 60,
            "logical_input_triples": 100,
            "generation_ms": 2,
            "reasoning_ms": 3,
            "process_cpu_ms": 4,
            "peak_rss_kib": 1000,
            "request_bytes": 10,
            "response_bytes": 20,
        },
        "edge1": {
            "input_triples": 50,
            "logical_input_triples": 100,
            "generation_ms": 1,
            "reasoning_ms": 2,
            "process_cpu_ms": 3,
            "peak_rss_kib": 1500,
            "request_bytes": 11,
            "response_bytes": 21,
        },
    }
    responses = {
        "cloud": {
            "query_cpu_ms": 5,
            "process_cpu_ms": 6,
            "peak_rss_kib": 1200,
            "request_bytes": 12,
            "response_bytes": 22,
        },
        "edge1": {
            "query_cpu_ms": 7,
            "process_cpu_ms": 8,
            "peak_rss_kib": 1600,
            "request_bytes": 13,
            "response_bytes": 23,
        },
    }

    result = _summary({}, 2, 10.0, 20.0, prepared, responses)

    assert result["node_prepare_process_cpu_ms_sum"] == 7
    assert result["node_query_process_cpu_ms_sum"] == 14
    assert result["max_node_peak_rss_kib"] == 1600
    assert result["prepare_request_bytes_sum"] == 21
    assert result["query_response_bytes_sum"] == 45
