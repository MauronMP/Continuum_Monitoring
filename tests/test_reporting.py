import csv
import json

from continuum_bench.reporting import (
    ENGINE_LABELS,
    _distributed_detail_path,
    _docker_summary_rows,
    _engine_summary_rows,
    _final_rows,
    _node_cost_rows,
    plot_three_architectures,
)
from continuum_bench.specification import release_identity


def _release(directory):
    (directory / "metadata.json").write_text(
        json.dumps(release_identity()),
        encoding="utf-8",
    )


def test_node_costs_are_aggregated_per_role_and_run():
    rows = [
        {
            "reasoner": "rdfs",
            "repetition": "1",
            "synthetic_users": "10",
            "role": "cloud",
            "duration_ms": "2.0",
        },
        {
            "reasoner": "rdfs",
            "repetition": "1",
            "synthetic_users": "10",
            "role": "cloud",
            "duration_ms": "4.0",
        },
        {
            "reasoner": "rdfs",
            "repetition": "1",
            "synthetic_users": "10",
            "role": "fog",
            "duration_ms": "1.0",
        },
    ]

    costs = _node_cost_rows("scalability", rows)
    cloud = next(row for row in costs if row["role"] == "cloud")

    assert cloud["query_count"] == 2
    assert cloud["query_cpu_ms"] == 6.0
    assert cloud["mean_query_ms"] == 3.0


def test_final_rows_select_the_largest_load_point():
    rows = [
        {"synthetic_users": "10", "reasoner": "rdfs"},
        {"synthetic_users": "500", "reasoner": "rdfs"},
        {"synthetic_users": "500", "reasoner": "owlrl"},
    ]

    final = _final_rows(rows, "synthetic_users")

    assert len(final) == 2
    assert {row["reasoner"] for row in final} == {"rdfs", "owlrl"}


def test_product_summary_includes_all_semantic_engines(tmp_path):
    fields = [
        "engine",
        "inference_profile",
        "stage",
        "synthetic_users",
        "engine_total_ms",
        "prepare_ms",
        "query_ms",
        "mean_query_ms",
        "inferred_triples",
    ]
    for suite in ("cumulative", "scalability"):
        directory = tmp_path / suite
        directory.mkdir()
        _release(directory)
        with (directory / "summary.csv").open(
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for engine in ENGINE_LABELS:
                writer.writerow(
                    {
                        "engine": engine,
                        "inference_profile": (
                            "none" if engine == "oxigraph" else "rdfs"
                        ),
                        "stage": 16,
                        "synthetic_users": 500,
                        "engine_total_ms": 10,
                        "prepare_ms": 2,
                        "query_ms": 8,
                        "mean_query_ms": 1,
                        "inferred_triples": (
                            0 if engine == "oxigraph" else 10
                        ),
                    }
                )
    rows = _engine_summary_rows(
        tmp_path,
        "test",
    )

    assert {row["engine"] for row in rows} == set(ENGINE_LABELS)


def test_distributed_summary_accepts_sharded_storage_metrics(tmp_path):
    fields = [
        "reasoner",
        "stage",
        "synthetic_users",
        "query_count",
        "total_wall_ms",
        "prepare_wall_ms",
        "query_wall_ms",
        "node_reasoning_ms_sum",
        "node_query_ms_sum",
        "logical_input_triples",
        "aggregate_fragment_triples",
        "max_fragment_triples",
        "storage_replication_factor",
    ]
    for suite in ("cumulative", "scalability"):
        directory = tmp_path / suite
        directory.mkdir()
        _release(directory)
        with (directory / "summary.csv").open(
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for reasoner in ("rdfs", "owlrl", "rdfs_owlrl"):
                writer.writerow(
                    {
                        "reasoner": reasoner,
                        "stage": 16,
                        "synthetic_users": 500,
                        "query_count": 115,
                        "total_wall_ms": 20,
                        "prepare_wall_ms": 12,
                        "query_wall_ms": 8,
                        "node_reasoning_ms_sum": 40,
                        "node_query_ms_sum": 10,
                        "logical_input_triples": 100,
                        "aggregate_fragment_triples": 350,
                        "max_fragment_triples": 90,
                        "storage_replication_factor": 3.5,
                    }
                )

    rows = _docker_summary_rows(
        tmp_path,
        architecture="docker-sharded-five-node",
    )

    assert len(rows) == 6
    assert {row["data_layout"] for row in rows} == {"authority-sharded"}
    assert {row["logical_input_triples"] for row in rows} == {100.0}
    assert {row["aggregate_fragment_triples"] for row in rows} == {350.0}
    assert {row["input_triples_per_replica"] for row in rows} == {""}


def test_sharded_node_detail_file_is_preferred(tmp_path):
    suite = tmp_path / "scalability"
    suite.mkdir()
    (suite / "query-runs.csv").write_text("merged\n", encoding="utf-8")
    node_detail = suite / "node-query-runs.csv"
    node_detail.write_text("per-node\n", encoding="utf-8")

    assert _distributed_detail_path(tmp_path, "scalability") == node_detail


def test_three_architecture_plot_ignores_unrequested_layout_labels(tmp_path):
    roots = {
        "monolith": tmp_path / "monolith",
        "docker": tmp_path / "docker",
        "physical": tmp_path / "physical",
    }
    reasoners = ("rdfs", "owlrl", "rdfs_owlrl")
    for architecture, root in roots.items():
        for suite, x_field, x_value in (
            ("cumulative", "stage", 16),
            ("scalability", "synthetic_users", 500),
        ):
            directory = root / suite
            directory.mkdir(parents=True)
            _release(directory)
            value_field = (
                "total_ms"
                if architecture == "monolith"
                else "total_wall_ms"
            )
            with (directory / "summary.csv").open(
                "w",
                encoding="utf-8",
                newline="",
            ) as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["reasoner", x_field, value_field],
                )
                writer.writeheader()
                for index, reasoner in enumerate(reasoners, start=1):
                    writer.writerow(
                        {
                            "reasoner": reasoner,
                            x_field: x_value,
                            value_field: 10 * index,
                        }
                    )

    figures, tables = plot_three_architectures(
        roots["monolith"],
        roots["docker"],
        roots["physical"],
        tmp_path / "figures",
        tmp_path / "data",
    )

    assert len(figures) == 6
    assert len(tables) == 2
