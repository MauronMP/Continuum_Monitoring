from __future__ import annotations

import csv
from pathlib import Path

import pytest
from rdflib.compare import to_isomorphic

from continuum_bench.monitoring.distributed_reasoning_config import (
    load_distributed_reasoning_config,
)
from continuum_bench.monitoring.distributed_reasoning_scalability import (
    _payload,
    _derive_scaling,
    _derive_semantic_validation,
    _derive_normalized_semantics,
    _capacity,
    _measurement,
    _statistics,
)
from continuum_bench.monitoring.budget import execution_policy
from continuum_bench.monitoring.experiment_reporting import (
    plot_distributed_reasoning_scalability,
)
from continuum_bench.monitoring.distributed_ontology import _full_source
from continuum_bench.partitioning import build_fragments
from continuum_bench.reasoners import PHYSICAL_REASONERS
from continuum_bench.topology import load_topology
from continuum_bench.cli import _family_timeout_updates, _parser


def test_unlimited_policy_disables_worker_alarm(root):
    config = load_distributed_reasoning_config(
        root / "tests/fixtures/distributed-reasoning.toml"
    )
    with execution_policy(unlimited=True):
        payload = _payload(config, "rdfs", 10000, True)
    assert payload["phase_timeout_seconds"] == 0


@pytest.mark.parametrize("name", [
    "configs/distributed-reasoning.toml",
    "tests/fixtures/distributed-reasoning.toml",
])
def test_active_distributed_reasoning_matrix_uses_five_backends(root, name):
    config = load_distributed_reasoning_config(root / name)
    assert config.reasoners == PHYSICAL_REASONERS
    assert config.tasks == (
        "rdfs_closure",
        "owl_dl_classification_realization",
    )


def test_all_experiments_requires_explicit_new_matrix_for_legacy_plans():
    parser = _parser()
    legacy = parser.parse_args(["experiment", "all", "physical"])
    current = parser.parse_args([
        "experiment", "all", "physical", "--distributed-reasoning-config",
        "configs/distributed-reasoning.toml",
    ])
    assert legacy.distributed_reasoning_config is None
    assert current.distributed_reasoning_config.endswith("distributed-reasoning.toml")


def test_independent_cli_timeouts_override_family_toml_values():
    args = _parser().parse_args([
        "--request-timeout-seconds", "180", "--point-timeout-seconds", "1800",
        "load", "physical",
    ])
    assert _family_timeout_updates(args, recovery=True) == {
        "request_timeout_seconds": 180,
        "point_timeout_seconds": 1800,
    }


def test_distributed_fragments_reach_an_exact_logical_target(config):
    topology = load_topology(
        config.root / "configs/topologies/physical/topology.toml", "physical"
    )
    baseline = build_fragments(config, 0, topology=topology)
    target = len(baseline.union()) + 23
    fragments = build_fragments(
        config, 0, topology=topology, target_triples=target,
        padding_mode="neutral",
    )
    assert len(fragments.union()) == target
    assert fragments.padding_triples == 23
    canonical = _full_source(config, 0, target_triples=target, padding_mode="neutral")
    assert to_isomorphic(fragments.union()) == to_isomorphic(canonical)
    sizes = [len(graph) for graph in fragments.graphs.values()]
    assert max(sizes) - min(sizes) < max(sizes)


def test_scaling_metrics_pair_each_repetition_with_one_node_baseline():
    common = dict(
        scaling_mode="strong", reasoner="rdfs", reasoning_task="rdfs_closure",
        layout="distributed", repetition=1, target_triples=1000,
        triples_per_node=1000,
    )
    rows = [
        {**common, "node_count": 1, "status": "completed", "reasoning_critical_path_ms": 100.0},
        {**common, "node_count": 2, "status": "completed", "reasoning_critical_path_ms": 60.0},
        {**common, "node_count": 4, "status": "timeout", "reasoning_critical_path_ms": ""},
    ]
    _derive_scaling(rows)
    assert rows[1]["speedup"] == pytest.approx(100 / 60)
    assert rows[1]["parallel_efficiency"] == pytest.approx(100 / 60 / 2)
    assert rows[2]["speedup"] == ""
    assert rows[2]["largest_successful_graph"] == ""


def test_capacity_treats_timeout_as_right_censoring():
    common = dict(
        scaling_mode="strong", layout="distributed", reasoner="rdfs",
        reasoning_task="rdfs_closure", node_count=2,
    )
    capacity = _capacity([
        {**common, "target_triples": 100_000, "status": "completed"},
        {**common, "target_triples": 250_000, "status": "timeout"},
    ])
    assert capacity == [{
        "layout": "distributed", "reasoner": "rdfs",
        "reasoning_task": "rdfs_closure", "node_count": 2,
        "largest_successful_graph": 100_000,
        "smallest_censored_graph": 250_000,
        "capacity_observation": "right-censored",
    }]


def test_measurement_records_overhead_balance_and_per_node_metrics():
    prepared = {
        "a": dict(node_id="cloud", role="cloud", tier_name="cloud", input_triples=60,
                  logical_input_triples=100, output_triples=75, inferred_triples=15,
                  reasoning_ms=20, process_cpu_ms=10, peak_rss_kib=100,
                  current_rss_kib=80, request_bytes=20, response_bytes=10,
                  disk_read_bytes=1, disk_write_bytes=2, partition_ms=5,
                  serialization_ms=3, transport_wall_ms=25,
                  logical_input_graph_digest="digest", closure_graph_digest="a"),
        "b": dict(node_id="edge", role="edge", tier_name="edge", input_triples=40,
                  logical_input_triples=100, output_triples=50, inferred_triples=10,
                  reasoning_ms=10, process_cpu_ms=8, peak_rss_kib=90,
                  current_rss_kib=70, request_bytes=15, response_bytes=5,
                  disk_read_bytes=3, disk_write_bytes=4, partition_ms=5,
                  serialization_ms=3, transport_wall_ms=25,
                  logical_input_graph_digest="digest", closure_graph_digest="b"),
    }
    row, nodes = _measurement({}, 40, prepared, "distributed")
    assert row["reasoning_critical_path_ms"] == 20
    assert row["coordination_overhead_ms"] == pytest.approx(20, abs=0.1)
    assert row["fragment_imbalance_ratio"] == pytest.approx(1.2)
    assert row["straggler_ratio"] == pytest.approx(4 / 3)
    assert row["reasoning_throughput_triples_s"] == 5000
    assert row["end_to_end_throughput_triples_s"] == pytest.approx(2500, rel=0.01)
    assert len(nodes) == 2


def test_semantic_validation_compares_sampled_layout_projections():
    rows = [
        {"run_id": "distributed", "repetition": 1, "status": "completed"},
        {"run_id": "replicated", "repetition": 1, "status": "completed"},
        {"run_id": "later", "repetition": 2, "status": "completed"},
    ]
    common = dict(
        scaling_mode="strong", target_triples=1000, node_count=2,
        reasoner="rdfs", reasoning_task="rdfs_closure", repetition=1,
        query_id="Q1", category="resource", execution_scope="all",
        merge_strategy="set_union", result_count=3, ask_result=None,
        result_digest="same",
    )
    validation = _derive_semantic_validation(rows, [
        {**common, "run_id": "distributed", "layout": "distributed"},
        {**common, "run_id": "replicated", "layout": "replicated"},
    ])
    assert len(validation) == 2
    assert all(item["valid"] for item in validation)
    assert rows[0]["semantic_equivalence_status"] == "query_projection_equivalent"
    assert rows[1]["semantic_validation_rate"] == 1
    assert rows[2]["semantic_equivalence_status"] == "not_sampled"


def test_normalized_inference_uses_equivalent_replicated_closure():
    common = dict(
        scaling_mode="strong", target_triples=1000, node_count=2,
        reasoner="rdfs", repetition=1, status="completed",
        asserted_triples=1000,
    )
    rows = [
        {**common, "layout": "distributed", "closure_triples": 1300,
         "local_aggregate_closure_triples": 1450},
        {**common, "layout": "replicated", "closure_triples": 1200,
         "local_aggregate_closure_triples": 2400},
    ]
    _derive_normalized_semantics(rows)
    assert rows[0]["normalized_inferred_triples"] == 200
    assert rows[0]["normalized_closure_triples"] == 1200
    assert rows[0]["closure_expansion_factor"] == pytest.approx(1.2)
    assert rows[0]["local_closure_delta_vs_reference"] == 250


def test_statistics_and_nine_scalability_figures(root, tmp_path):
    config = load_distributed_reasoning_config(
        root / "tests/fixtures/distributed-reasoning.toml"
    )
    directory = tmp_path / "distributed-reasoning-scalability"
    directory.mkdir()
    rows = []
    for layout in ("distributed", "replicated"):
        for nodes in (1, 2):
            for repetition in (1, 2):
                rows.append(dict(
                    status="completed", scaling_mode="strong", layout=layout,
                    reasoner="rdfs", reasoning_task="rdfs_closure",
                    target_triples="10000", node_count=str(nodes), repetition=str(repetition),
                    triples_per_node=str(10000/nodes), reasoning_critical_path_ms=str(100/nodes),
                    prepare_wall_ms=str(150/nodes), reasoning_throughput_triples_s=str(100000*nodes),
                    end_to_end_throughput_triples_s=str(66000*nodes), speedup=str(nodes),
                    parallel_efficiency="1", weak_scaling_efficiency="",
                    coordination_overhead_pct="33", fragment_imbalance_ratio="1.1",
                    closure_expansion_factor="1.2",
                ))
    weak = [{**row, "scaling_mode": "weak", "weak_scaling_efficiency": "0.9"} for row in rows]
    all_rows = rows + weak
    with (directory / "distributed-reasoning-summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=all_rows[0].keys())
        writer.writeheader(); writer.writerows(all_rows)
    statistics_rows = _statistics(rows, config)
    assert {item["metric"] for item in statistics_rows} >= {"speedup", "parallel_efficiency"}
    paths = plot_distributed_reasoning_scalability(tmp_path)
    assert len(paths) == 9
    assert all(path.suffix == ".png" and path.is_file() for path in paths)


def test_missing_replicated_projection_is_not_a_semantic_mismatch():
    rows = [{'run_id': 'distributed', 'repetition': 1, 'status': 'completed'}]
    projection = dict(run_id='distributed', scaling_mode='strong', target_triples=50000,
        node_count=6, reasoner='rdfs', reasoning_task='rdfs_closure', repetition=1,
        layout='distributed', query_id='Q1', category='resource', execution_scope='all',
        merge_strategy='set_union', result_count=3, ask_result=None, result_digest='abc')
    validation = _derive_semantic_validation(rows, [projection])
    assert validation[0]['status'] == 'replicated_reference_unavailable'
    assert rows[0]['semantic_equivalence_status'] == 'replicated_reference_unavailable'
    assert rows[0]['semantic_validation_rate'] == ''


def test_all_preparations_timing_out_still_finish_matrix_and_archive(root, config, tmp_path, monkeypatch):
    from dataclasses import replace
    import json
    from continuum_bench.monitoring import distributed_reasoning_scalability as module
    experiment = replace(load_distributed_reasoning_config(root / 'tests/fixtures/distributed-reasoning.toml'),
        repetitions=2, reasoners=('rdfs',), node_counts=(1,), target_triples=(0,),
        users=2000, strong_scaling=True, weak_scaling=False, stop_after_timeout=False,
        layouts=('distributed', 'replicated'))
    calls = []
    monkeypatch.setattr(module, 'discover', lambda *a, **k: [])
    monkeypatch.setattr(module, '_select_endpoints', lambda *a: [])
    def timeout(*args):
        calls.append(args)
        raise TimeoutError('controlled preparation timeout')
    monkeypatch.setattr(module, '_prepare', timeout)
    output = module.run_distributed_reasoning_scalability(config, experiment, 'physical', tmp_path)
    rows = list(csv.DictReader((output / 'distributed-reasoning-summary.csv').open()))
    assert len(calls) == len(rows) == 4
    assert all(r['status'] == 'timeout' for r in rows)
    assert (output / 'metadata.json').exists()
    assert len((output / 'results.jsonl').read_text().splitlines()) == 4
    assert not (output / 'node-runs.csv').exists()
    assert not (output / 'distributed-reasoning-statistics.csv').exists()
    assert json.loads((output / 'metadata.json').read_text())['configuration']['users'] == 2000
