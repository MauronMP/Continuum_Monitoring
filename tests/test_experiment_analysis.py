import csv
import json

from continuum_bench.csv_utils import write_dict_rows
from continuum_bench.experiment_analysis import analyze_experiments


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _write(path, rows):
    write_dict_rows(path, rows, empty_message="test rows required")


def _scale_row(architecture, nodes, qps):
    return {
        "architecture": architecture,
        "reasoner": "rdfs",
        "node_count": nodes,
        "status": "completed",
        "queries_per_second": qps,
        "query_wall_ms": 1000 / qps,
        "query_latency_p95_ms": 100 / qps,
        "node_query_process_cpu_ms_sum": 10,
        "sum_current_rss_kib": 100 * nodes,
    }


def _distributed_row(architecture, total, cpu, rss):
    return {
        "architecture": architecture,
        "reasoner": "rdfs",
        "synthetic_users": 100,
        "status": "completed",
        "prepare_wall_ms": total * 0.8,
        "query_wall_ms": total * 0.2,
        "total_wall_ms": total,
        "total_process_cpu_ms": cpu,
        "max_sum_node_current_rss_kib": rss,
        "logical_input_triples": 10000,
        "aggregate_fragment_triples": 13000,
        "max_fragment_triples": 3500,
        "storage_replication_factor": 1.3,
        "prepare_request_bytes_sum": 1,
        "prepare_response_bytes_sum": 1,
        "query_request_bytes_sum": 1,
        "query_response_bytes_sum": 1,
        "result_validation_rate": 1.0,
        "oracle_status": (
            "self" if architecture == "monolith" else "completed"
        ),
    }


def test_analysis_emits_supported_matched_claim(tmp_path):
    for architecture in ("monolith", "docker", "physical"):
        _write_json(
            tmp_path / architecture / "scale-out" / "metadata.json",
            {"repetitions": 1, "query_rounds": 1},
        )
        _write_json(
            tmp_path
            / architecture
            / "distributed-ontology"
            / "metadata.json",
            {"repetitions": 1},
        )

    _write(
        tmp_path / "monolith" / "scale-out" / "summary.csv",
        [_scale_row("monolith", 1, 10)],
    )
    _write(
        tmp_path / "docker" / "scale-out" / "summary.csv",
        [
            _scale_row("docker", 1, 8),
            _scale_row("docker", 5, 32),
        ],
    )
    _write(
        tmp_path / "physical" / "scale-out" / "summary.csv",
        [
            _scale_row("physical", 1, 5),
            _scale_row("physical", 5, 15),
        ],
    )
    for architecture, nodes in (
        ("monolith", 1),
        ("docker", 1),
        ("docker", 5),
        ("physical", 1),
        ("physical", 5),
    ):
        _write(
            tmp_path / architecture / "scale-out" / "query-runs.csv",
            [
                {
                    "architecture": architecture,
                    "reasoner": "rdfs",
                    "node_count": nodes,
                    "query_id": "Q1",
                    "result_digest": "same",
                }
            ],
        )
    _write(
        tmp_path
        / "monolith"
        / "distributed-ontology"
        / "summary.csv",
        [_distributed_row("monolith", 100, 100, 100)],
    )
    _write(
        tmp_path / "docker" / "distributed-ontology" / "summary.csv",
        [_distributed_row("docker", 40, 80, 200)],
    )
    _write(
        tmp_path / "physical" / "distributed-ontology" / "summary.csv",
        [_distributed_row("physical", 60, 90, 250)],
    )

    paths = analyze_experiments(tmp_path)

    verdict_path = tmp_path / "analysis" / "claim-verdict.csv"
    verdicts = list(csv.DictReader(verdict_path.open()))
    assert {row["verdict"] for row in verdicts} == {"supported"}
    assert {row["semantic_equivalence"] for row in verdicts} == {"True"}
    assert verdict_path in paths
    assert (tmp_path / "analysis" / "REPORT.md").is_file()
