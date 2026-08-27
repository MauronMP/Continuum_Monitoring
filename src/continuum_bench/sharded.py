"""Privacy-aware benchmark coordinator for Docker and physical continuum nodes."""

from __future__ import annotations

from dataclasses import asdict
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
from time import perf_counter_ns
from typing import Any

from rdflib import Graph

from .config import BenchmarkConfig
from .distributed import (
    DISTRIBUTED_REQUEST_RETRIES,
    DISTRIBUTED_REQUEST_TIMEOUT_SECONDS,
    Endpoint,
    _parallel,
    _write_csv,
    discover,
)
from .ontology import load_graph
from .queries import (
    QuerySpec,
    by_categories,
    execute_query_detailed,
    load_catalog,
    result_digest,
)
from .reasoners import materialize
from .specification import release_identity
from .synthetic import add_synthetic_data


def _sources(
    spec: QuerySpec,
    endpoints: list[Endpoint],
) -> list[Endpoint]:
    cloud = [item for item in endpoints if item.role == "cloud"]
    fog = [item for item in endpoints if item.role == "fog"]
    edges = sorted(
        (item for item in endpoints if item.role.startswith("edge")),
        key=lambda item: item.role,
    )
    if spec.execution_scope == "cloud":
        return cloud
    if spec.execution_scope == "fog":
        return fog
    if spec.execution_scope == "edges":
        return edges
    if spec.execution_scope in {"edge1", "edge2", "edge3"}:
        return [
            item for item in edges if item.role == spec.execution_scope
        ]
    if spec.execution_scope == "cloud_edges":
        return cloud + edges
    raise ValueError(
        f"{spec.id}: unsupported execution scope {spec.execution_scope!r}"
    )


def _assignment(
    specs: list[QuerySpec],
    endpoints: list[Endpoint],
) -> dict[str, list[QuerySpec]]:
    assigned = {endpoint.url: [] for endpoint in endpoints}
    for spec in specs:
        for endpoint in _sources(spec, endpoints):
            assigned[endpoint.url].append(spec)
    return assigned


def _prepare(
    endpoints: list[Endpoint],
    reasoner: str,
    users: int,
    seed: int,
) -> tuple[float, dict[str, dict[str, Any]]]:
    return _parallel(
        endpoints,
        "/prepare",
        {
            endpoint.url: {
                "reasoner": reasoner,
                "users": users,
                "seed": seed,
                "mode": "partitioned",
            }
            for endpoint in endpoints
        },
        phase="partitioned-prepare",
    )


def _query(
    endpoints: list[Endpoint],
    assignment: dict[str, list[QuerySpec]],
) -> tuple[float, dict[str, dict[str, Any]]]:
    return _parallel(
        endpoints,
        "/queries",
        {
            url: {
                "query_ids": [spec.id for spec in specs],
                "include_result_keys": True,
            }
            for url, specs in assignment.items()
            if specs
        },
        phase="partitioned-queries",
    )


def _merge_responses(
    specs: list[QuerySpec],
    endpoints: list[Endpoint],
    responses: dict[str, dict[str, Any]],
    common: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    endpoint_by_url = {item.url: item for item in endpoints}
    raw_by_query: dict[str, list[dict[str, Any]]] = {
        spec.id: [] for spec in specs
    }
    node_rows: list[dict[str, Any]] = []
    for url, response in responses.items():
        role = endpoint_by_url[url].role
        for measurement in response["measurements"]:
            node_rows.append(
                {
                    **common,
                    "endpoint": url,
                    "role": role,
                    **measurement,
                }
            )
            raw_by_query[measurement["query_id"]].append(
                {"role": role, **measurement}
            )

    merged: list[dict[str, Any]] = []
    for spec in specs:
        parts = raw_by_query[spec.id]
        if not parts:
            raise RuntimeError(f"No source returned {spec.id}")
        if spec.merge_strategy == "boolean_or":
            ask_result = any(bool(part["ask_result"]) for part in parts)
            result_count = int(ask_result)
            merged_keys: list[str] = []
        elif spec.merge_strategy == "set_union":
            ask_result = None
            counters = [
                Counter(part.get("result_keys", [])) for part in parts
            ]
            merged_counter = Counter(
                {
                    key: max(counter[key] for counter in counters)
                    for key in {
                        key for counter in counters for key in counter
                    }
                }
            )
            merged_keys = list(merged_counter.elements())
            result_count = len(merged_keys)
        elif spec.merge_strategy == "group_union":
            raise ValueError(
                f"{spec.id}: group_union cannot preserve aggregate values; "
                "route aggregate queries to one authoritative source or "
                "declare an algebraic partial aggregate"
            )
        elif spec.merge_strategy == "single":
            if len(parts) != 1:
                raise RuntimeError(
                    f"{spec.id}: single merge received {len(parts)} sources"
                )
            ask_result = parts[0]["ask_result"]
            result_count = int(parts[0]["result_count"])
            merged_keys = list(parts[0].get("result_keys", []))
        else:
            raise ValueError(
                f"{spec.id}: unknown merge strategy {spec.merge_strategy}"
            )
        merged.append(
            {
                **common,
                "query_id": spec.id,
                "category": spec.category,
                "tier": spec.tier,
                "execution_scope": spec.execution_scope,
                "authority": spec.authority,
                "privacy_class": spec.privacy_class,
                "merge_strategy": spec.merge_strategy,
                "source_roles": "|".join(
                    sorted(str(part["role"]) for part in parts)
                ),
                "source_count": len(parts),
                "duration_ms": max(
                    float(part["duration_ms"]) for part in parts
                ),
                "node_duration_ms_sum": sum(
                    float(part["duration_ms"]) for part in parts
                ),
                "result_count": result_count,
                "ask_result": ask_result,
                "result_digest": result_digest(merged_keys, ask_result),
            }
        )
    return merged, node_rows


def _full_source(config: BenchmarkConfig, users: int) -> Graph:
    graph = load_graph(
        config.resolve(path) for path in config.ontology_files
    )
    add_synthetic_data(graph, users, config.seed)
    return graph


def _baseline_counts(
    config: BenchmarkConfig,
    specs: list[QuerySpec],
    reasoner: str,
    users: int,
) -> dict[str, tuple[int, bool | None, str]]:
    reasoning = materialize(_full_source(config, users), reasoner)
    return {
        spec.id: (
            execution.measurement.result_count,
            execution.measurement.ask_result,
            result_digest(
                execution.result_keys,
                execution.measurement.ask_result,
            ),
        )
        for spec in specs
        for execution in [execute_query_detailed(reasoning.graph, spec)]
    }


def _validation_rows(
    merged: list[dict[str, Any]],
    baseline: dict[str, tuple[int, bool | None, str]],
) -> list[dict[str, Any]]:
    rows = []
    for item in merged:
        expected_count, expected_ask, expected_digest = baseline[
            item["query_id"]
        ]
        valid = (
            int(item["result_count"]) == expected_count
            and item["ask_result"] == expected_ask
            and item["result_digest"] == expected_digest
        )
        rows.append(
            {
                "reasoner": item["reasoner"],
                "synthetic_users": item.get("synthetic_users", 0),
                "query_id": item["query_id"],
                "execution_scope": item["execution_scope"],
                "distributed_count": item["result_count"],
                "monolith_count": expected_count,
                "distributed_ask": item["ask_result"],
                "monolith_ask": expected_ask,
                "distributed_digest": item["result_digest"],
                "monolith_digest": expected_digest,
                "valid": valid,
            }
        )
    return rows


def _summary(
    common: dict[str, Any],
    query_count: int,
    prepare_wall_ms: float,
    query_wall_ms: float,
    prepared: dict[str, dict[str, Any]],
    responses: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    aggregate_input = sum(
        int(item["input_triples"]) for item in prepared.values()
    )
    logical_input = max(
        int(item["logical_input_triples"])
        for item in prepared.values()
    )
    prepare_peak_rss = [
        int(item.get("peak_rss_kib", 0)) for item in prepared.values()
    ]
    query_peak_rss = [
        int(item.get("peak_rss_kib", 0)) for item in responses.values()
    ]
    prepare_current_rss = [
        int(item.get("current_rss_kib", 0)) for item in prepared.values()
    ]
    query_current_rss = [
        int(item.get("current_rss_kib", 0)) for item in responses.values()
    ]
    return {
        **common,
        "query_count": query_count,
        "source_query_executions": sum(
            int(item.get("query_count", 0)) for item in responses.values()
        ),
        "federation_fanout_factor": (
            sum(
                int(item.get("query_count", 0))
                for item in responses.values()
            )
            / query_count
            if query_count
            else 0.0
        ),
        "prepare_wall_ms": prepare_wall_ms,
        "node_generation_ms_sum": sum(
            float(item["generation_ms"]) for item in prepared.values()
        ),
        "node_reasoning_ms_sum": sum(
            float(item["reasoning_ms"]) for item in prepared.values()
        ),
        "max_node_reasoning_ms": max(
            float(item["reasoning_ms"]) for item in prepared.values()
        ),
        "query_wall_ms": query_wall_ms,
        "prepare_transport_retry_count": sum(
            max(int(item.get("_coordinator_attempts", 1)) - 1, 0)
            for item in prepared.values()
        ),
        "query_transport_retry_count": sum(
            max(int(item.get("_coordinator_attempts", 1)) - 1, 0)
            for item in responses.values()
        ),
        "node_query_ms_sum": sum(
            float(item["query_cpu_ms"]) for item in responses.values()
        ),
        "node_prepare_process_cpu_ms_sum": sum(
            float(item.get("process_cpu_ms", 0.0))
            for item in prepared.values()
        ),
        "node_query_process_cpu_ms_sum": sum(
            float(item.get("process_cpu_ms", 0.0))
            for item in responses.values()
        ),
        "total_process_cpu_ms": sum(
            float(item.get("process_cpu_ms", 0.0))
            for item in (*prepared.values(), *responses.values())
        ),
        "max_node_prepare_peak_rss_kib": max(prepare_peak_rss, default=0),
        "max_node_query_peak_rss_kib": max(query_peak_rss, default=0),
        "max_node_peak_rss_kib": max(
            (*prepare_peak_rss, *query_peak_rss),
            default=0,
        ),
        "sum_node_prepare_current_rss_kib": sum(prepare_current_rss),
        "sum_node_query_current_rss_kib": sum(query_current_rss),
        "max_sum_node_current_rss_kib": max(
            sum(prepare_current_rss),
            sum(query_current_rss),
        ),
        "prepare_request_bytes_sum": sum(
            int(item.get("request_bytes", 0)) for item in prepared.values()
        ),
        "prepare_response_bytes_sum": sum(
            int(item.get("response_bytes", 0)) for item in prepared.values()
        ),
        "query_request_bytes_sum": sum(
            int(item.get("request_bytes", 0)) for item in responses.values()
        ),
        "query_response_bytes_sum": sum(
            int(item.get("response_bytes", 0)) for item in responses.values()
        ),
        "total_wall_ms": prepare_wall_ms + query_wall_ms,
        "logical_input_triples": logical_input,
        "aggregate_fragment_triples": aggregate_input,
        "aggregate_output_triples": sum(
            int(item.get("output_triples", item["input_triples"]))
            for item in prepared.values()
        ),
        "aggregate_inferred_triples": sum(
            int(item.get("inferred_triples", 0))
            for item in prepared.values()
        ),
        "max_fragment_triples": max(
            int(item["input_triples"]) for item in prepared.values()
        ),
        "max_fragment_fraction": (
            max(int(item["input_triples"]) for item in prepared.values())
            / logical_input
            if logical_input
            else 0.0
        ),
        "storage_replication_factor": (
            aggregate_input / logical_input if logical_input else 0.0
        ),
    }


def _metadata(
    config: BenchmarkConfig,
    endpoints: list[Endpoint],
    target: str,
    suite: str,
    validate_results: bool,
) -> dict[str, Any]:
    return {
        **release_identity(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "suite": suite,
        "mode": f"{target}-five-node-authority-sharded",
        "endpoints": [
            {"url": item.url, "role": item.role} for item in endpoints
        ],
        "reasoners": list(config.reasoners),
        "repetitions": config.repetitions,
        "seed": config.seed,
        "result_validation": validate_results,
        "result_validation_level": (
            "exact-order-independent-canonical-result-set; numeric lexical "
            "forms and duplicate solution rows are normalized"
        ),
        "timing_excludes_monolith_validation": True,
        "ontology_placement_manifest": str(
            (config.root / "configs/ontology-placement.toml").resolve()
        ),
        "telemetry": {
            "process_cpu_ms": "per-process CPU time consumed during phase",
            "peak_rss_kib": (
                "process lifetime high-water RSS; not incremental phase memory"
            ),
            "request_response_bytes": (
                "HTTP JSON body bytes; excludes transport headers"
            ),
        },
        "worker_telemetry": {
            "process_cpu_ms": "per request process CPU time",
            "peak_rss_kib": "process high-water resident set size",
            "transport_bytes": "exact JSON HTTP request/response body sizes",
        },
        "transport": {
            "timeout_seconds": DISTRIBUTED_REQUEST_TIMEOUT_SECONDS,
            "retries": DISTRIBUTED_REQUEST_RETRIES,
            "retry_delay_in_phase_wall_time": True,
            "retry_counts_in_summary": True,
        },
        "routing": (
            "query source selection from queries/execution-plan.toml, "
            "parallel owner execution, deterministic set/ASK merge"
        ),
    }


def run_sharded_cumulative(
    config: BenchmarkConfig,
    endpoint_urls: list[str],
    output_root: Path,
    *,
    target: str,
    validate_results: bool = True,
) -> Path:
    endpoints = discover(endpoint_urls)
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    details: list[dict[str, Any]] = []
    node_details: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    validations: list[dict[str, Any]] = []
    baseline_cache: dict[
        str, dict[str, tuple[int, bool | None, str]]
    ] = {}

    for reasoner in config.reasoners:
        if validate_results:
            print(
                f"[{target}-sharded-cumulative] reasoner={reasoner} "
                "phase=monolith-validation status=running",
                flush=True,
            )
            baseline_cache[reasoner] = _baseline_counts(
                config, specs, reasoner, 0
            )
        for repetition in range(1, config.repetitions + 1):
            print(
                f"[{target}-sharded-cumulative] reasoner={reasoner} "
                f"repetition={repetition}/{config.repetitions} "
                "nodes=5 phase=partitioned-prepare status=running",
                flush=True,
            )
            prepare_wall_ms, prepared = _prepare(
                endpoints, reasoner, 0, config.seed
            )
            active: set[str] = set()
            for stage, category in enumerate(config.category_order, start=1):
                active.add(category)
                active_specs = by_categories(specs, active)
                assignment = _assignment(active_specs, endpoints)
                loads = ",".join(
                    f"{endpoint.role}:{len(assignment[endpoint.url])}"
                    for endpoint in endpoints
                )
                print(
                    f"[{target}-sharded-cumulative] reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    f"stage={stage}/{len(config.category_order)} "
                    f"category={category} queries={len(active_specs)} "
                    f"sources={loads} status=running",
                    flush=True,
                )
                query_wall_ms, responses = _query(endpoints, assignment)
                common = {
                    "reasoner": reasoner,
                    "repetition": repetition,
                    "stage": stage,
                    "added_category": category,
                }
                merged, raw = _merge_responses(
                    active_specs, endpoints, responses, common
                )
                details.extend(merged)
                node_details.extend(raw)
                summaries.append(
                    _summary(
                        common,
                        len(active_specs),
                        prepare_wall_ms,
                        query_wall_ms,
                        prepared,
                        responses,
                    )
                )
                if validate_results:
                    validations.extend(
                        _validation_rows(merged, baseline_cache[reasoner])
                    )
                print(
                    f"[{target}-sharded-cumulative] reasoner={reasoner} "
                    f"stage={stage}/{len(config.category_order)} "
                    f"category={category} status=done "
                    f"wall_ms={prepare_wall_ms + query_wall_ms:.2f}",
                    flush=True,
                )

    output = output_root / "cumulative"
    _write_csv(output / "query-runs.csv", details)
    _write_csv(output / "node-query-runs.csv", node_details)
    _write_csv(output / "summary.csv", summaries)
    if validations:
        _write_csv(output / "result-validation.csv", validations)
        invalid = [item for item in validations if not item["valid"]]
        if invalid:
            sample = ", ".join(
                f"{item['reasoner']}:{item['query_id']}"
                for item in invalid[:8]
            )
            raise RuntimeError(
                f"Distributed result validation failed ({len(invalid)} rows): "
                f"{sample}"
            )
    metadata = _metadata(
        config, endpoints, target, "cumulative", validate_results
    )
    metadata["category_order"] = list(config.category_order)
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


def run_sharded_scalability(
    config: BenchmarkConfig,
    endpoint_urls: list[str],
    output_root: Path,
    *,
    target: str,
    validate_results: bool = True,
) -> Path:
    endpoints = discover(endpoint_urls)
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    details: list[dict[str, Any]] = []
    node_details: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    validations: list[dict[str, Any]] = []

    for block, users in enumerate(config.scale_users, start=1):
        for reasoner in config.reasoners:
            baseline = None
            if validate_results:
                print(
                    f"[{target}-sharded-scalability] "
                    f"block={block}/{len(config.scale_users)} users={users} "
                    f"reasoner={reasoner} phase=monolith-validation "
                    "status=running",
                    flush=True,
                )
                baseline = _baseline_counts(config, specs, reasoner, users)
            for repetition in range(1, config.repetitions + 1):
                print(
                    f"[{target}-sharded-scalability] "
                    f"block={block}/{len(config.scale_users)} users={users} "
                    f"reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    "nodes=5 phase=partitioned-prepare status=running",
                    flush=True,
                )
                prepare_wall_ms, prepared = _prepare(
                    endpoints, reasoner, users, config.seed
                )
                assignment = _assignment(specs, endpoints)
                query_wall_ms, responses = _query(endpoints, assignment)
                common = {
                    "reasoner": reasoner,
                    "repetition": repetition,
                    "synthetic_users": users,
                    "synthetic_triples": next(iter(prepared.values()))[
                        "synthetic_triples"
                    ],
                }
                merged, raw = _merge_responses(
                    specs, endpoints, responses, common
                )
                details.extend(merged)
                node_details.extend(raw)
                summaries.append(
                    _summary(
                        common,
                        len(specs),
                        prepare_wall_ms,
                        query_wall_ms,
                        prepared,
                        responses,
                    )
                )
                if baseline is not None:
                    validations.extend(_validation_rows(merged, baseline))
                print(
                    f"[{target}-sharded-scalability] "
                    f"block={block}/{len(config.scale_users)} users={users} "
                    f"reasoner={reasoner} status=done "
                    f"wall_ms={prepare_wall_ms + query_wall_ms:.2f}",
                    flush=True,
                )

    output = output_root / "scalability"
    _write_csv(output / "query-runs.csv", details)
    _write_csv(output / "node-query-runs.csv", node_details)
    _write_csv(output / "summary.csv", summaries)
    if validations:
        _write_csv(output / "result-validation.csv", validations)
        invalid = [item for item in validations if not item["valid"]]
        if invalid:
            sample = ", ".join(
                f"{item['reasoner']}:{item['query_id']}"
                for item in invalid[:8]
            )
            raise RuntimeError(
                f"Distributed result validation failed ({len(invalid)} rows): "
                f"{sample}"
            )
    metadata = _metadata(
        config, endpoints, target, "scalability", validate_results
    )
    metadata["scale_users"] = list(config.scale_users)
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


def export_fragments(
    config: BenchmarkConfig,
    users: int,
    output_dir: Path,
) -> list[Path]:
    from .partitioning import build_fragments, write_fragments

    started = perf_counter_ns()
    fragments = build_fragments(config, users)
    paths = write_fragments(fragments, output_dir)
    manifest = {
        **release_identity(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "synthetic_users": users,
        "logical_triples": len(fragments.union()),
        "logical_substrate_triples": fragments.substrate_triples,
        "sensitive_resources": len(fragments.sensitive_resources),
        "fragments": {
            role: {
                "path": str((output_dir / f"{role}.ttl").resolve()),
                "triples": len(graph),
                "substrate_triples": (
                    fragments.substrate_triples_by_role[role]
                ),
                "profile": fragments.placement_profiles[role],
            }
            for role, graph in fragments.graphs.items()
        },
        "generation_ms": (perf_counter_ns() - started) / 1_000_000,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return [*paths, manifest_path]
