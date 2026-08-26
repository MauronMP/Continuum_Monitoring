from continuum_bench.engines import _record_measurements
from continuum_bench.queries import QuerySpec


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
