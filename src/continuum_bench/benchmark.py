from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import statistics
from time import monotonic, perf_counter_ns
from typing import Any

from rdflib import Graph

from .config import BenchmarkConfig
from .budget import PhaseBudgetTimeout, error_text, local_phase_timeout
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


def _censored_summary(
    common: dict[str, Any],
    query_count: int,
    phase: str,
    error: BaseException | str,
    timeout_seconds: float,
    elapsed_seconds: float,
) -> dict[str, Any]:
    message = error if isinstance(error, str) else error_text(error)
    lower_bound_ms = min(max(elapsed_seconds, 0.0), timeout_seconds) * 1000
    return {
        **common,
        "query_count": query_count,
        "input_triples": "",
        "output_triples": "",
        "inferred_triples": "",
        "generation_ms": "",
        "reasoning_ms": "",
        "query_ms": "",
        "total_ms": lower_bound_ms if phase != "early-stop" else "",
        "mean_query_ms": "",
        "p95_query_ms": "",
        "queries_per_second": "",
        "status": (
            "skipped_after_timeout" if phase == "early-stop" else "timeout"
        ),
        "censored": True,
        "censored_lower_bound_ms": lower_bound_ms,
        "failed_phase": phase,
        "timeout_seconds": timeout_seconds,
        "error": message,
    }


def _censored_detail(
    common: dict[str, Any],
    phase: str,
    error: BaseException | str,
    timeout_seconds: float,
) -> dict[str, Any]:
    return {
        **common,
        "query_id": "__phase__",
        "category": "",
        "tier": "",
        "duration_ms": "",
        "result_count": "",
        "ask_result": "",
        "result_digest": "",
        "status": (
            "skipped_after_timeout" if phase == "early-stop" else "timeout"
        ),
        "censored": True,
        "failed_phase": phase,
        "timeout_seconds": timeout_seconds,
        "error": error if isinstance(error, str) else error_text(error),
    }


def run_cumulative(config: BenchmarkConfig) -> Path:
    base_graph, specs = _load(config)
    detail_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    blocked: dict[str, str] = {}

    for reasoner in config.reasoners:
        for repetition in range(1, config.repetitions + 1):
            if reasoner in blocked:
                for stage, category in enumerate(
                    config.category_order, start=1
                ):
                    common = {
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "stage": stage,
                        "added_category": category,
                        "category_count": stage,
                    }
                    summary_rows.append(
                        _censored_summary(
                            common,
                            len(by_categories(specs, set(config.category_order[:stage]))),
                            "early-stop",
                            blocked[reasoner],
                            config.limits.point_timeout_seconds,
                            0.0,
                        )
                    )
                    detail_rows.append(
                        _censored_detail(
                            common,
                            "early-stop",
                            blocked[reasoner],
                            config.limits.point_timeout_seconds,
                        )
                    )
                continue
            print(
                "[cumulative] "
                f"reasoner={reasoner} "
                f"repetition={repetition}/{config.repetitions} "
                "phase=reasoning status=running",
                flush=True,
            )
            reasoning_started = monotonic()
            try:
                with local_phase_timeout(
                    min(
                        config.limits.phase_timeout_seconds,
                        config.limits.point_timeout_seconds,
                    )
                ):
                    reasoning = materialize(base_graph, reasoner)
            except PhaseBudgetTimeout as error:
                if config.limits.stop_scaling_after_timeout:
                    blocked[reasoner] = error_text(error)
                for stage, category in enumerate(
                    config.category_order, start=1
                ):
                    common = {
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "stage": stage,
                        "added_category": category,
                        "category_count": stage,
                    }
                    phase = "reasoning" if stage == 1 else "early-stop"
                    summary_rows.append(
                        _censored_summary(
                            common,
                            len(by_categories(specs, set(config.category_order[:stage]))),
                            phase,
                            error,
                            config.limits.point_timeout_seconds,
                            monotonic() - reasoning_started if stage == 1 else 0.0,
                        )
                    )
                    detail_rows.append(
                        _censored_detail(
                            common,
                            phase,
                            error,
                            config.limits.point_timeout_seconds,
                        )
                    )
                print(
                    f"[cumulative] reasoner={reasoner} phase=reasoning "
                    f"status=timeout limit_s={config.limits.phase_timeout_seconds:g}",
                    flush=True,
                )
                continue
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
                query_started = monotonic()
                query_budget = max(
                    config.limits.point_timeout_seconds
                    - reasoning.duration_ms / 1000,
                    0.001,
                )
                try:
                    with local_phase_timeout(
                        min(config.limits.phase_timeout_seconds, query_budget)
                    ):
                        measurements = [
                            execute_query(reasoning.graph, spec)
                            for spec in active_specs
                        ]
                except PhaseBudgetTimeout as error:
                    if config.limits.stop_scaling_after_timeout:
                        blocked[reasoner] = error_text(error)
                    common = {
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "stage": stage,
                        "added_category": category,
                        "category_count": stage,
                    }
                    summary_rows.append(
                        _censored_summary(
                            common,
                            len(active_specs),
                            "queries",
                            error,
                            config.limits.point_timeout_seconds,
                            reasoning.duration_ms / 1000
                            + monotonic()
                            - query_started,
                        )
                    )
                    detail_rows.append(
                        _censored_detail(
                            common,
                            "queries",
                            error,
                            config.limits.point_timeout_seconds,
                        )
                    )
                    for skipped_stage in range(
                        stage + 1, len(config.category_order) + 1
                    ):
                        skipped_common = {
                            "reasoner": reasoner,
                            "repetition": repetition,
                            "stage": skipped_stage,
                            "added_category": config.category_order[
                                skipped_stage - 1
                            ],
                            "category_count": skipped_stage,
                        }
                        summary_rows.append(
                            _censored_summary(
                                skipped_common,
                                len(
                                    by_categories(
                                        specs,
                                        set(config.category_order[:skipped_stage]),
                                    )
                                ),
                                "early-stop",
                                error,
                                config.limits.point_timeout_seconds,
                                0.0,
                            )
                        )
                        detail_rows.append(
                            _censored_detail(
                                skipped_common,
                                "early-stop",
                                error,
                                config.limits.point_timeout_seconds,
                            )
                        )
                    print(
                        f"[cumulative] reasoner={reasoner} stage={stage} "
                        "status=timeout; larger stages will be skipped",
                        flush=True,
                    )
                    break
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
                            "status": "completed",
                            "censored": False,
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
                        "status": "completed",
                        "censored": False,
                    }
                )

    output = config.resolve(config.output_dir) / "cumulative"
    _write_csv(output / "query-runs.csv", detail_rows)
    _write_csv(output / "summary.csv", summary_rows)
    metadata = _metadata(config, base_graph)
    metadata["category_order"] = list(config.category_order)
    metadata["final_query_count"] = len(specs)
    metadata["execution_limits"] = {
        "phase_timeout_seconds": config.limits.phase_timeout_seconds,
        "point_timeout_seconds": config.limits.point_timeout_seconds,
        "stop_scaling_after_timeout": config.limits.stop_scaling_after_timeout,
        "timeout_semantics": "right-censored; later stages skipped per reasoner",
    }
    _write_metadata(output / "metadata.json", metadata)
    return output


def run_scalability(config: BenchmarkConfig) -> Path:
    base_graph, specs = _load(config)
    detail_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    blocked: dict[str, str] = {}

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
                common = {
                    "reasoner": reasoner,
                    "repetition": repetition,
                    "synthetic_users": users,
                    "synthetic_triples": synthetic_triples,
                }
                if reasoner in blocked:
                    summary_rows.append(
                        _censored_summary(
                            common,
                            len(specs),
                            "early-stop",
                            blocked[reasoner],
                            config.limits.point_timeout_seconds,
                            0.0,
                        )
                    )
                    detail_rows.append(
                        _censored_detail(
                            common,
                            "early-stop",
                            blocked[reasoner],
                            config.limits.point_timeout_seconds,
                        )
                    )
                    continue
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
                point_started = monotonic()
                phase = "reasoning"
                try:
                    with local_phase_timeout(
                        min(
                            config.limits.phase_timeout_seconds,
                            config.limits.point_timeout_seconds,
                        )
                    ):
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
                    phase = "queries"
                    remaining = max(
                        config.limits.point_timeout_seconds
                        - (monotonic() - point_started),
                        0.001,
                    )
                    with local_phase_timeout(
                        min(config.limits.phase_timeout_seconds, remaining)
                    ):
                        measurements = [
                            execute_query(reasoning.graph, spec)
                            for spec in specs
                        ]
                except PhaseBudgetTimeout as error:
                    if config.limits.stop_scaling_after_timeout:
                        blocked[reasoner] = error_text(error)
                    summary_rows.append(
                        _censored_summary(
                            common,
                            len(specs),
                            phase,
                            error,
                            config.limits.point_timeout_seconds,
                            monotonic() - point_started,
                        )
                    )
                    detail_rows.append(
                        _censored_detail(
                            common,
                            phase,
                            error,
                            config.limits.point_timeout_seconds,
                        )
                    )
                    print(
                        f"[scalability] block={block} users={users} "
                        f"reasoner={reasoner} phase={phase} status=timeout "
                        f"limit_s={config.limits.point_timeout_seconds:g}; "
                        "larger blocks will be skipped for this reasoner",
                        flush=True,
                    )
                    continue
                for measurement in measurements:
                    detail_rows.append(
                        {
                            "reasoner": reasoner,
                            "repetition": repetition,
                            "synthetic_users": users,
                            "synthetic_triples": synthetic_triples,
                            "status": "completed",
                            "censored": False,
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
                        "status": "completed",
                        "censored": False,
                    }
                )

    output = config.resolve(config.output_dir) / "scalability"
    _write_csv(output / "query-runs.csv", detail_rows)
    _write_csv(output / "summary.csv", summary_rows)
    metadata = _metadata(config, base_graph)
    metadata["scale_users"] = list(config.scale_users)
    metadata["query_count_per_run"] = len(specs)
    metadata["execution_limits"] = {
        "phase_timeout_seconds": config.limits.phase_timeout_seconds,
        "point_timeout_seconds": config.limits.point_timeout_seconds,
        "stop_scaling_after_timeout": config.limits.stop_scaling_after_timeout,
        "timeout_semantics": "right-censored; later blocks skipped per reasoner",
    }
    _write_metadata(output / "metadata.json", metadata)
    return output
