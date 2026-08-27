import csv
import json
from pathlib import Path

import pytest

from continuum_bench.compare import compare_suite
from continuum_bench.specification import release_identity


def _write(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.name == "summary.csv":
        (path.parent / "metadata.json").write_text(
            json.dumps(release_identity()),
            encoding="utf-8",
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_compare_scalability_checks_results_and_computes_speedup(tmp_path):
    mono = tmp_path / "mono" / "scalability"
    docker = tmp_path / "docker" / "scalability"
    common = {
        "reasoner": "rdfs",
        "repetition": 1,
        "synthetic_users": 10,
        "query_count": 1,
    }
    _write(
        mono / "summary.csv",
        [{**common, "input_triples": 100, "total_ms": 20}],
    )
    _write(
        docker / "summary.csv",
        [
            {
                **common,
                "total_wall_ms": 10,
                "node_reasoning_ms_sum": 30,
                "node_query_ms_sum": 5,
            }
        ],
    )
    detail = {
        "reasoner": "rdfs",
        "repetition": 1,
        "synthetic_users": 10,
        "query_id": "BASE-Q01",
        "result_count": 2,
        "ask_result": "",
    }
    _write(mono / "query-runs.csv", [detail])
    _write(
        docker / "query-runs.csv",
        [{**detail, "role": "cloud", "endpoint": "http://cloud"}],
    )

    comparison, validation = compare_suite(
        "scalability",
        tmp_path / "mono",
        tmp_path / "docker",
        tmp_path / "comparison",
    )

    with comparison.open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert float(row["speedup"]) == pytest.approx(2.0)
    assert float(row["parallel_efficiency"]) == pytest.approx(0.4)
    with validation.open(encoding="utf-8", newline="") as handle:
        validation_row = next(csv.DictReader(handle))
    assert validation_row["matches"] == "True"
    assert validation_row["validation_level"] == "cardinality_ask"


def test_compare_accepts_sharded_query_provenance(tmp_path):
    mono = tmp_path / "mono" / "scalability"
    sharded = tmp_path / "sharded" / "scalability"
    common = {
        "reasoner": "rdfs",
        "repetition": 1,
        "synthetic_users": 10,
        "query_count": 1,
    }
    _write(
        mono / "summary.csv",
        [{**common, "input_triples": 100, "total_ms": 20}],
    )
    _write(
        sharded / "summary.csv",
        [
            {
                **common,
                "total_wall_ms": 12,
                "node_reasoning_ms_sum": 25,
                "node_query_ms_sum": 8,
                "logical_input_triples": 100,
                "aggregate_fragment_triples": 350,
            }
        ],
    )
    detail = {
        "reasoner": "rdfs",
        "repetition": 1,
        "synthetic_users": 10,
        "query_id": "BASE-Q01",
        "result_count": 2,
        "ask_result": "",
        "result_digest": "same-bindings",
    }
    _write(mono / "query-runs.csv", [detail])
    _write(
        sharded / "query-runs.csv",
        [
            {
                **detail,
                "source_roles": "edge1|edge2|edge3",
                "source_count": 3,
            }
        ],
    )

    _, validation = compare_suite(
        "scalability",
        tmp_path / "mono",
        tmp_path / "sharded",
        tmp_path / "comparison",
    )

    with validation.open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["matches"] == "True"
    assert row["docker_role"] == ""
    assert row["docker_endpoint"] == ""
    assert row["distributed_source_roles"] == "edge1|edge2|edge3"
    assert row["distributed_source_count"] == "3"
    assert row["validation_level"] == "result_digest"


def test_compare_rejects_equal_cardinality_with_different_digests(tmp_path):
    mono = tmp_path / "mono" / "scalability"
    distributed = tmp_path / "distributed" / "scalability"
    common = {
        "reasoner": "rdfs",
        "repetition": 1,
        "synthetic_users": 10,
        "query_count": 1,
    }
    _write(
        mono / "summary.csv",
        [{**common, "input_triples": 100, "total_ms": 20}],
    )
    _write(
        distributed / "summary.csv",
        [
            {
                **common,
                "total_wall_ms": 10,
                "node_reasoning_ms_sum": 30,
                "node_query_ms_sum": 5,
            }
        ],
    )
    detail = {
        "reasoner": "rdfs",
        "repetition": 1,
        "synthetic_users": 10,
        "query_id": "BASE-Q01",
        "result_count": 2,
        "ask_result": "",
    }
    _write(
        mono / "query-runs.csv",
        [{**detail, "result_digest": "monolith-bindings"}],
    )
    _write(
        distributed / "query-runs.csv",
        [
            {
                **detail,
                "result_digest": "different-bindings",
                "source_roles": "edge1|edge2",
                "source_count": 2,
            }
        ],
    )

    with pytest.raises(
        AssertionError,
        match="distributed results differ from monolith",
    ):
        compare_suite(
            "scalability",
            tmp_path / "mono",
            tmp_path / "distributed",
            tmp_path / "comparison",
        )

    validation = (
        tmp_path
        / "comparison"
        / "scalability-result-validation.csv"
    )
    with validation.open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["validation_level"] == "result_digest"
    assert row["matches"] == "False"
