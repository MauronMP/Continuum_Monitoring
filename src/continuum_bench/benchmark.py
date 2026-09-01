from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import statistics
from time import perf_counter_ns
from typing import Any

from rdflib import Graph

from .config import BenchmarkConfig
from .csv_utils import write_dict_rows
from .ontology import graph_digest, load_graph
from .queries import QuerySpec, by_categories, execute_query, load_catalog
from .reasoners import materialize
from .specification import release_identity
from .synthetic import add_synthetic_data
from .topology import Topology, load_topology


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_dict_rows(
        path,
        rows,
        empty_message=f"Cannot write empty benchmark CSV: {path}",
    )


def _percentile95(values: list[float]) -> float:
    if len(values) < 2:
        return values[0]
    return statistics.quantiles(values, n=20, method="inclusive")[18]


def _monolith_topology(config: BenchmarkConfig) -> Topology:
    return load_topology(config.resolve(config.topology_file), "monolith")


def _metadata(config: BenchmarkConfig, graph: Graph) -> dict[str, Any]:
    topology = _monolith_topology(config)
    return {
        **release_identity(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "graph_sha256": graph_digest(graph),
        "base_triples": len(graph),
        "reasoners": list(config.reasoners),
        "repetitions": config.repetitions,
        "seed": config.seed,
        "architecture": "monolith",
        "topology": topology.public(),
    }


def _write_metadata(path: Path, metadata: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _load(config: BenchmarkConfig) -> tuple[Graph, list[QuerySpec]]:
    # Fail before a potentially long run if the monolithic architecture
    # configuration is invalid.  Its fingerprint is persisted in metadata.
    _monolith_topology(config)
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    specs = load_catalog(
        config.resolve(config.query_catalog),
        config.root,
    )
    configured = set(config.category_order)
    catalogued = {spec.category for spec in specs}
    if configured != catalogued:
        raise ValueError(
            f"Category mismatch: config-only={configured - catalogued}, "
            f"catalog-only={catalogued - configured}"
        )
    return graph, specs


def run_cumulative(config: BenchmarkConfig) -> Path:
    base_graph, specs = _load(config)
    detail_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    for reasoner in config.reasoners:
        for repetition in range(1, config.repetitions + 1):
            print(
                "[cumulative] "
                f"reasoner={reasoner} "
                f"repetition={repetition}/{config.repetitions} "
                "phase=reasoning status=running",
                flush=True,
            )
            reasoning = materialize(base_graph, reasoner)
            print(
                "[cumulative] "
                f"reasoner={reasoner} "
                f"repetition={repetition}/{config.repetitions} "
                f"phase=reasoning status=done "
                f"duration_ms={reasoning.duration_ms:.2f} "
                f"triples={reasoning.input_triples}->{reasoning.output_triples}",
                flush=True,
            )
            active_categories: set[str] = set()
            for stage, category in enumerate(config.category_order, start=1):
                active_categories.add(category)
                active_specs = by_categories(specs, active_categories)
                print(
                    "[cumulative] "
                    f"reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    f"stage={stage}/{len(config.category_order)} "
                    f"category={category} "
                    f"cumulative_queries={len(active_specs)} "
                    "status=running",
                    flush=True,
                )
                measurements = [
                    execute_query(reasoning.graph, spec) for spec in active_specs
                ]
                for measurement in measurements:
                    detail_rows.append(
                        {
                            "reasoner": reasoner,
                            "repetition": repetition,
                            "stage": stage,
                            "added_category": category,
                            "cumulative_categories": "|".join(
                                config.category_order[:stage]
                            ),
                            **asdict(measurement),
                        }
                    )
                query_times = [item.duration_ms for item in measurements]
                query_ms = sum(query_times)
                print(
                    "[cumulative] "
                    f"reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    f"stage={stage}/{len(config.category_order)} "
                    f"category={category} "
                    f"cumulative_queries={len(active_specs)} "
                    f"status=done query_ms={query_ms:.2f}",
                    flush=True,
                )
                summary_rows.append(
                    {
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "stage": stage,
                        "added_category": category,
                        "category_count": stage,
                        "query_count": len(active_specs),
                        "input_triples": reasoning.input_triples,
                        "output_triples": reasoning.output_triples,
                        "inferred_triples": reasoning.inferred_triples,
                        "reasoning_ms": reasoning.duration_ms,
                        "query_ms": query_ms,
                        "total_ms": reasoning.duration_ms + query_ms,
                        "mean_query_ms": statistics.fmean(query_times),
                        "p95_query_ms": _percentile95(query_times),
                    }
                )

    output = config.resolve(config.output_dir) / "cumulative"
    _write_csv(output / "query-runs.csv", detail_rows)
    _write_csv(output / "summary.csv", summary_rows)
    metadata = _metadata(config, base_graph)
    metadata["category_order"] = list(config.category_order)
    metadata["final_query_count"] = len(specs)
    _write_metadata(output / "metadata.json", metadata)
    return output


def run_scalability(config: BenchmarkConfig) -> Path:
    base_graph, specs = _load(config)
    detail_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    for block, users in enumerate(config.scale_users, start=1):
        print(
            "[scalability] "
            f"block={block}/{len(config.scale_users)} "
            f"users={users} phase=generation status=running",
            flush=True,
        )
        source = Graph()
        for prefix, namespace in base_graph.namespaces():
            source.bind(prefix, namespace)
        for triple in base_graph:
            source.add(triple)
        started = perf_counter_ns()
        synthetic_triples = add_synthetic_data(source, users, config.seed)
        generation_ms = (perf_counter_ns() - started) / 1_000_000
        print(
            "[scalability] "
            f"block={block}/{len(config.scale_users)} "
            f"users={users} phase=generation status=done "
            f"synthetic_triples={synthetic_triples} "
            f"duration_ms={generation_ms:.2f}",
            flush=True,
        )

        for reasoner in config.reasoners:
            for repetition in range(1, config.repetitions + 1):
                print(
                    "[scalability] "
                    f"block={block}/{len(config.scale_users)} "
                    f"users={users} "
                    f"reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    f"queries={len(specs)} "
                    "phase=reasoning status=running",
                    flush=True,
                )
                reasoning = materialize(source, reasoner)
                print(
                    "[scalability] "
                    f"block={block}/{len(config.scale_users)} "
                    f"users={users} "
                    f"reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    "phase=queries status=running",
                    flush=True,
                )
                measurements = [
                    execute_query(reasoning.graph, spec) for spec in specs
                ]
                for measurement in measurements:
                    detail_rows.append(
                        {
                            "reasoner": reasoner,
                            "repetition": repetition,
                            "synthetic_users": users,
                            "synthetic_triples": synthetic_triples,
                            **asdict(measurement),
                        }
                    )
                query_times = [item.duration_ms for item in measurements]
                query_ms = sum(query_times)
                total_ms = generation_ms + reasoning.duration_ms + query_ms
                print(
                    "[scalability] "
                    f"block={block}/{len(config.scale_users)} "
                    f"users={users} "
                    f"reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    f"queries={len(specs)} status=done "
                    f"reasoning_ms={reasoning.duration_ms:.2f} "
                    f"query_ms={query_ms:.2f} total_ms={total_ms:.2f}",
                    flush=True,
                )
                summary_rows.append(
                    {
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "synthetic_users": users,
                        "synthetic_triples": synthetic_triples,
                        "query_count": len(specs),
                        "input_triples": reasoning.input_triples,
                        "output_triples": reasoning.output_triples,
                        "inferred_triples": reasoning.inferred_triples,
                        "generation_ms": generation_ms,
                        "reasoning_ms": reasoning.duration_ms,
                        "query_ms": query_ms,
                        "total_ms": total_ms,
                        "queries_per_second": (
                            len(specs) / (query_ms / 1000) if query_ms else 0
                        ),
                        "mean_query_ms": statistics.fmean(query_times),
                        "p95_query_ms": _percentile95(query_times),
                    }
                )

    output = config.resolve(config.output_dir) / "scalability"
    _write_csv(output / "query-runs.csv", detail_rows)
    _write_csv(output / "summary.csv", summary_rows)
    metadata = _metadata(config, base_graph)
    metadata["scale_users"] = list(config.scale_users)
    metadata["query_count_per_run"] = len(specs)
    _write_metadata(output / "metadata.json", metadata)
    return output
