import pytest

from continuum_bench import engines
from continuum_bench.engines import _expectation_ok, _record_measurements
from continuum_bench.queries import QuerySpec
from continuum_bench.reasoners import REASONING_CONTRACT


def test_engine_measurements_normalize_optional_result_digest(tmp_path):
    spec = QuerySpec(
        order=1,
        id="TEST-Q01",
        tier="core",
        category="topology",
        kind="select",
        expectation="non_empty",
        path=tmp_path / "query.rq",
        title="Contract test",
    )
    common = {
        "engine": "jena",
        "inference_profile": "rdfs",
        "repetition": 1,
    }

    java_row = _record_measurements(
        [
            {
                "query_id": spec.id,
                "category": spec.category,
                "tier": spec.tier,
                "duration_ms": 1.0,
                "result_count": 1,
                "ask_result": None,
            }
        ],
        [spec],
        common,
    )[0]
    python_row = _record_measurements(
        [
            {
                "query_id": spec.id,
                "category": spec.category,
                "tier": spec.tier,
                "duration_ms": 1.0,
                "result_count": 1,
                "ask_result": None,
                "result_digest": "digest-from-engine",
            }
        ],
        [spec],
        {**common, "engine": "rdflib"},
    )[0]

    assert java_row["result_digest"] == ""
    assert python_row["result_digest"] == "digest-from-engine"
    assert java_row.keys() == python_row.keys()


def test_engine_expectation_validates_false_ask(tmp_path):
    spec = QuerySpec(
        order=1,
        id="TEST-Q02",
        tier="core",
        category="validation",
        kind="ask",
        expectation="false",
        path=tmp_path / "query.rq",
        title="Negative ASK contract",
    )

    assert _expectation_ok(
        spec,
        {"result_count": 0, "ask_result": False},
    )
    assert not _expectation_ok(
        spec,
        {"result_count": 1, "ask_result": True},
    )


def test_engine_discovery_requires_the_v3_service_protocol(monkeypatch):
    names = {
        "http://rdflib": ("rdflib", "rdfs"),
        "http://jena": ("jena", "rdfs"),
        "http://rdf4j": ("rdf4j", "rdfs"),
        "http://oxigraph": ("oxigraph", "none"),
    }

    def health(url, path):
        name, inference = names[url]
        return {
            "status": "ok",
            "service": "continuum-semantic-engine",
            "protocol_version": "2",
            "engine": name,
            "version": "test",
            "inference_profile": inference,
            "reasoning_contract": REASONING_CONTRACT,
        }

    monkeypatch.setattr(engines, "_request", health)

    found = engines.discover(list(names))

    assert {item.engine for item in found} == set(names[url][0] for url in names)


def test_engine_discovery_rejects_a_legacy_service(monkeypatch):
    monkeypatch.setattr(
        engines,
        "_request",
        lambda *args: {
            "status": "ok",
            "engine": "jena",
            "version": "legacy",
            "inference_profile": "rdfs",
        },
    )

    with pytest.raises(RuntimeError, match="expected service"):
        engines.discover(["http://jena"])


def test_engine_discovery_rejects_rdflib_without_datatype_correction(monkeypatch):
    monkeypatch.setattr(
        engines,
        "_request",
        lambda *args: {
            "status": "ok",
            "service": "continuum-semantic-engine",
            "protocol_version": "2",
            "engine": "rdflib",
            "version": "old-image",
            "inference_profile": "rdfs",
        },
    )

    with pytest.raises(RuntimeError, match="reasoning_contract"):
        engines.discover(["http://rdflib"])


def test_expectation_failure_identifies_stage_and_observed_count():
    with pytest.raises(AssertionError, match="stage=13, repetition=1, count=3"):
        engines._validate_expectations([
            {
                "engine": "rdflib",
                "query_id": "EXT-Q68",
                "stage": 13,
                "repetition": 1,
                "result_count": 3,
                "expectation": "zero_rows",
                "expectation_ok": False,
            }
        ])
