"""Strong/weak scalability of reasoning over physical continuum nodes."""
from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import statistics
from time import monotonic, perf_counter_ns
from typing import Any
import uuid

import numpy as np

from ..csv_utils import write_dict_rows
from ..reasoners import reasoner_semantics
from ..specification import release_identity
from .budget import (
    error_text, execution_metadata, failure_status, is_boundary_failure,
    unlimited_execution,
)
from .config import BenchmarkConfig
from .distributed import Endpoint, _parallel, _request, discover
from .distributed_ontology import (
    _assignment as distributed_assignment,
    _merge_responses,
    _prepare as distributed_prepare,
    _query as distributed_query,
)
from .distributed_reasoning_config import DistributedReasoningConfig, REASONING_TASKS
from ..queries import QuerySpec, load_catalog


def _select_endpoints(endpoints: list[Endpoint], count: int) -> list[Endpoint]:
    if count > len(endpoints):
        raise ValueError(f"Requested {count} nodes but only {len(endpoints)} are available")
    cloud = next((item for item in endpoints if item.tier == "cloud"), endpoints[0])
    authorities = [item for item in endpoints if item.authority and item != cloud]
    others = [item for item in endpoints if item != cloud and item not in authorities]
    ordered = [cloud, *authorities[:1], *others, *authorities[1:]]
    selected = ordered[:count]
    if count == 1 and not selected[0].authority:
        item = selected[0]
        selected = [Endpoint(item.url, item.role, item.tier, True, item.categories)]
    return selected


def _payload(
    config: DistributedReasoningConfig, reasoner: str, target: int,
    validate_graph_digest: bool,
) -> dict[str, Any]:
    return {
        "reasoner": reasoner,
        "users": config.users,
        "seed": config.seed,
        "mode": "replicated",
        "target_triples": target,
        "rule_count": config.rule_count,
        "padding_mode": config.padding_mode,
        "validate_graph_digest": validate_graph_digest,
        "phase_timeout_seconds": (
            0 if unlimited_execution()
            else max(config.request_timeout_seconds - 5, 0.1)
        ),
    }


def _prepare(
    benchmark: BenchmarkConfig, experiment: DistributedReasoningConfig,
    endpoints: list[Endpoint], layout: str, reasoner: str, target: int,
    validate_graph_digest: bool,
) -> tuple[float, dict[str, dict[str, Any]]]:
    if layout == "distributed":
        return distributed_prepare(
            benchmark, endpoints, reasoner, experiment.users, experiment.seed,
            timeout_seconds=experiment.point_timeout_seconds,
            target_triples=target, padding_mode=experiment.padding_mode,
            validate_graph_digest=validate_graph_digest,
        )
    payload = _payload(experiment, reasoner, target, validate_graph_digest)
    return _parallel(
        endpoints, "/prepare", {item.url: dict(payload) for item in endpoints},
        phase="distributed-reasoning-replicated-prepare",
        timeout=experiment.request_timeout_seconds, retries=0,
    )


def _safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator > 0 else math.nan


def _measurement(
    common: dict[str, Any], prepare_wall_ms: float,
    prepared: dict[str, dict[str, Any]], layout: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    aggregation_started = perf_counter_ns()
    items = list(prepared.values())
    inputs = [int(item["input_triples"]) for item in items]
    outputs = [int(item["output_triples"]) for item in items]
    inferred = [int(item.get("inferred_triples", 0)) for item in items]
    reasoning = [float(item["reasoning_ms"]) for item in items]
    logical_input = max(int(item.get("logical_input_triples", item["input_triples"])) for item in items)
    logical_digests = {str(item.get("logical_input_graph_digest", "")) for item in items}
    if common.get("validation_sampled") and (len(logical_digests) != 1 or "" in logical_digests):
        raise ValueError("Workers did not report one common logical input graph digest")
    aggregate_input = sum(inputs)
    critical = max(reasoning)
    mean_reasoning = statistics.fmean(reasoning)
    partition_ms = max(float(item.get("partition_ms", 0)) for item in items)
    serialization_ms = max(float(item.get("serialization_ms", 0)) for item in items)
    transport_wall_ms = max(float(item.get("transport_wall_ms", prepare_wall_ms)) for item in items)
    coordinator_digest_ms = max(float(item.get("logical_graph_digest_ms", 0)) for item in items)
    worker_digest_ms = max(float(item.get("validation_digest_ms", 0)) for item in items)
    validation_overhead_ms = coordinator_digest_ms + worker_digest_ms
    benchmark_prepare_wall_ms = max(prepare_wall_ms - validation_overhead_ms, critical)
    fragments = np.asarray(inputs, dtype=float)
    closure = (
        max(outputs) if layout == "replicated"
        else logical_input + sum(inferred)
    )
    aggregation_ms = (perf_counter_ns() - aggregation_started) / 1_000_000
    benchmark_end_to_end_ms = benchmark_prepare_wall_ms + aggregation_ms
    coordination = max(benchmark_end_to_end_ms - critical, 0.0)
    row = {
        **common,
        "status": "completed", "censored": False, "error": "",
        "asserted_triples": logical_input,
        "inferred_triples": max(inferred) if layout == "replicated" else sum(inferred),
        "closure_triples": closure,
        "local_aggregate_inferred_triples": sum(inferred),
        "local_aggregate_closure_triples": sum(outputs),
        "closure_expansion_factor": _safe_ratio(closure, logical_input),
        "aggregate_input_triples": aggregate_input,
        "aggregate_output_triples": sum(outputs),
        "prepare_wall_ms": prepare_wall_ms,
        "benchmark_prepare_wall_ms": benchmark_prepare_wall_ms,
        "benchmark_end_to_end_ms": benchmark_end_to_end_ms,
        "reasoning_ms": critical,
        "e2e_ms": benchmark_end_to_end_ms,
        "validation_digest_overhead_ms": validation_overhead_ms,
        "reasoning_critical_path_ms": critical,
        "mean_node_reasoning_ms": mean_reasoning,
        "partition_ms": partition_ms,
        "serialization_ms": serialization_ms,
        "transport_wall_ms": transport_wall_ms,
        "aggregation_ms": aggregation_ms,
        "coordination_overhead_ms": coordination,
        "coordination_overhead_pct": 100 * _safe_ratio(coordination, benchmark_end_to_end_ms),
        "reasoning_throughput_triples_s": 1000 * _safe_ratio(logical_input, critical),
        "end_to_end_throughput_triples_s": 1000 * _safe_ratio(logical_input, benchmark_end_to_end_ms),
        "throughput": 1000 * _safe_ratio(logical_input, critical),
        "min_fragment_triples": int(fragments.min()),
        "mean_fragment_triples": float(fragments.mean()),
        "std_fragment_triples": float(fragments.std(ddof=0)),
        "max_fragment_triples": int(fragments.max()),
        "fragment_imbalance_ratio": _safe_ratio(float(fragments.max()), float(fragments.mean())),
        "straggler_ratio": _safe_ratio(critical, mean_reasoning),
        "process_cpu_ms": sum(float(item.get("process_cpu_ms", 0)) for item in items),
        "peak_rss_kib": max(int(item.get("peak_rss_kib", 0)) for item in items),
        "current_rss_kib_sum": sum(int(item.get("current_rss_kib", 0)) for item in items),
        "network_bytes": sum(int(item.get("request_bytes", 0)) + int(item.get("response_bytes", 0)) for item in items),
        "disk_io_bytes": sum(int(item.get("disk_read_bytes", 0)) + int(item.get("disk_write_bytes", 0)) for item in items),
        "storage_replication_factor": _safe_ratio(aggregate_input, logical_input),
        "logical_input_graph_digest": next(iter(logical_digests), ""),
        "closure_digest_scope": "single-full-graph" if layout == "replicated" else "per-fragment-only",
        "closure_graph_digests": ",".join(sorted(str(item.get("closure_graph_digest", "")) for item in items)),
    }
    node_rows = [
        {
            **common, "node_id": item.get("node_id", item.get("role", "")),
            "role": item.get("role", ""), "tier": item.get("tier_name", ""),
            "input_triples": int(item["input_triples"]),
            "inferred_triples": int(item.get("inferred_triples", 0)),
            "closure_triples": int(item["output_triples"]),
            "reasoning_ms": float(item["reasoning_ms"]),
            "throughput_tps": 1000 * _safe_ratio(int(item["input_triples"]), float(item["reasoning_ms"])),
            "process_cpu_ms": float(item.get("process_cpu_ms", 0)),
            "peak_rss_kib": int(item.get("peak_rss_kib", 0)),
            "current_rss_kib": int(item.get("current_rss_kib", 0)),
            "request_bytes": int(item.get("request_bytes", 0)),
            "response_bytes": int(item.get("response_bytes", 0)),
            "status": "completed",
        }
        for item in items
    ]
    return row, node_rows


def _derive_scaling(rows: list[dict[str, Any]]) -> None:
    baselines = {}
    for row in rows:
        if row["status"] != "completed" or row["node_count"] != 1:
            continue
        key = (row["scaling_mode"], row["reasoner"], row["reasoning_task"], row["layout"], row["repetition"],
               row["target_triples"] if row["scaling_mode"] == "strong" else row["triples_per_node"])
        baselines[key] = row["reasoning_critical_path_ms"]
    for row in rows:
        row.update(speedup="", parallel_efficiency="", weak_scaling_efficiency="", efficiency="")
        if row["status"] != "completed":
            continue
        key = (row["scaling_mode"], row["reasoner"], row["reasoning_task"], row["layout"], row["repetition"],
               row["target_triples"] if row["scaling_mode"] == "strong" else row["triples_per_node"])
        baseline = baselines.get(key)
        if not baseline:
            continue
        if row["scaling_mode"] == "strong":
            speedup = baseline / row["reasoning_critical_path_ms"]
            row["speedup"] = speedup
            row["parallel_efficiency"] = speedup / row["node_count"]
            row["efficiency"] = row["parallel_efficiency"]
        else:
            row["weak_scaling_efficiency"] = baseline / row["reasoning_critical_path_ms"]
            row["efficiency"] = row["weak_scaling_efficiency"]
    groups = defaultdict(list)
    for row in rows:
        if row["status"] == "completed":
            groups[(row["reasoner"], row["layout"], row["node_count"])].append(int(row["target_triples"]))
    for row in rows:
        values = groups.get((row["reasoner"], row["layout"], row["node_count"]), [])
        row["largest_successful_graph"] = max(values, default="")
    equivalence = defaultdict(set)
    for row in rows:
        if row["status"] == "completed":
            key = (row["scaling_mode"], row["target_triples"], row["node_count"], row["reasoner"], row["repetition"])
            equivalence[key].add(row.get("logical_input_graph_digest", ""))
    for row in rows:
        key = (row["scaling_mode"], row["target_triples"], row["node_count"], row["reasoner"], row["repetition"])
        digests = equivalence.get(key, set())
        row["input_graph_equivalent_across_layouts"] = (
            bool(row.get("validation_sampled"))
            and len(digests) == 1
            and "" not in digests
        )


def _derive_normalized_semantics(rows: list[dict[str, Any]]) -> None:
    """Use the equivalent full replica to de-duplicate fragment inference."""
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            row["scaling_mode"], row["target_triples"], row["node_count"],
            row["reasoner"], row["repetition"],
        )
        groups[key].append(row)
    for selected in groups.values():
        reference = next(
            (
                row for row in selected
                if row.get("layout") == "replicated"
                and row.get("status") == "completed"
            ),
            None,
        )
        for row in selected:
            if row.get("status") != "completed" or reference is None:
                row["normalized_inferred_triples"] = ""
                row["normalized_closure_triples"] = ""
                row["normalized_closure_source"] = "replicated_reference_unavailable"
                continue
            asserted = int(row["asserted_triples"])
            normalized_closure = int(reference["closure_triples"])
            row["normalized_closure_triples"] = normalized_closure
            row["normalized_inferred_triples"] = max(normalized_closure - asserted, 0)
            row["normalized_closure_source"] = "equivalent_replicated_full_graph"
            row["closure_expansion_factor"] = _safe_ratio(normalized_closure, asserted)
            row["local_closure_delta_vs_reference"] = (
                int(row["local_aggregate_closure_triples"]) - normalized_closure
            )


def _query_client(
    endpoints: list[Endpoint], specs: list[QuerySpec], layout: str,
    client_index: int, timeout: float,
) -> tuple[float, int, int, str]:
    started = monotonic()
    try:
        if layout == "replicated":
            endpoint = endpoints[client_index % len(endpoints)]
            response = _request(
                endpoint.url, "/queries",
                {"query_ids": [spec.id for spec in specs], "phase_timeout_seconds": (
                    0 if unlimited_execution() else max(timeout - 5, .1)
                )},
                timeout=timeout, retries=0,
            )
            processed = int(response.get("query_count", len(specs)))
            network = int(response.get("request_bytes", 0)) + int(response.get("response_bytes", 0))
        else:
            assignment = distributed_assignment(specs, endpoints)
            _, responses = _parallel(
                endpoints, "/queries",
                {url: {"query_ids": [spec.id for spec in selected],
                       "phase_timeout_seconds": (
                           0 if unlimited_execution() else max(timeout - 5, .1)
                       )}
                 for url, selected in assignment.items() if selected},
                phase="distributed-reasoning-query-scalability",
                timeout=timeout, retries=0,
            )
            processed = sum(int(item.get("query_count", 0)) for item in responses.values())
            network = sum(int(item.get("request_bytes", 0)) + int(item.get("response_bytes", 0)) for item in responses.values())
        return (monotonic() - started) * 1000, processed, network, ""
    except Exception as error:
        return (monotonic() - started) * 1000, 0, 0, error_text(error)


def _query_scalability(
    common: dict[str, Any], endpoints: list[Endpoint], specs: list[QuerySpec],
    layout: str, config: DistributedReasoningConfig,
) -> list[dict[str, Any]]:
    rows = []
    for concurrency in config.query_concurrency:
        latencies = []
        processed = network = errors = 0
        wall_started = monotonic()
        for round_index in range(1, config.query_rounds + 1):
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(_query_client, endpoints, specs, layout, index, config.request_timeout_seconds)
                           for index in range(concurrency)]
                for future in as_completed(futures):
                    latency, count, transferred, error = future.result()
                    if not error:
                        latencies.append(latency)
                    processed += count; network += transferred
                    errors += bool(error)
        wall_ms = (monotonic() - wall_started) * 1000
        attempts = concurrency * config.query_rounds
        rows.append({
            **common, "concurrency": concurrency, "query_rounds": config.query_rounds,
            "client_requests": attempts, "query_executions": processed,
            "query_wall_ms": wall_ms,
            "queries_per_second": 1000 * _safe_ratio(processed, wall_ms),
            "latency_p50_ms": float(np.percentile(latencies, 50)) if latencies else "",
            "latency_p95_ms": float(np.percentile(latencies, 95)) if latencies else "",
            "latency_p99_ms": float(np.percentile(latencies, 99)) if latencies else "",
            "error_count": errors, "error_rate": errors / attempts,
            "network_bytes": network,
            "status": "completed" if not errors else "partial_failure",
        })
    return rows


def _semantic_projection(
    benchmark: BenchmarkConfig,
    endpoints: list[Endpoint],
    specs: list[QuerySpec],
    layout: str,
    common: dict[str, Any],
    timeout_seconds: float,
) -> tuple[float, list[dict[str, Any]]]:
    """Return comparable query projections without including them in timings."""
    if layout == "distributed":
        wall_ms, responses = distributed_query(
            benchmark,
            endpoints,
            distributed_assignment(specs, endpoints),
            timeout_seconds=timeout_seconds,
        )
    else:
        endpoint = endpoints[0]
        started = monotonic()
        response = _request(
            endpoint.url,
            "/queries",
            {
                "query_ids": [spec.id for spec in specs],
                "include_result_keys": True,
                "phase_timeout_seconds": (
                    0 if unlimited_execution()
                    else max(timeout_seconds - 5, 0.1)
                ),
            },
            timeout=timeout_seconds,
            retries=0,
        )
        wall_ms = (monotonic() - started) * 1000
        responses = {endpoint.url: response}
    merged, _ = _merge_responses(specs, endpoints, responses, common)
    return wall_ms, merged


def _derive_semantic_validation(
    rows: list[dict[str, Any]],
    projections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compare one sampled repetition per point with its replicated reference."""
    by_run = {str(row["run_id"]): row for row in rows}
    grouped: dict[tuple[Any, ...], dict[str, list[dict[str, Any]]]] = defaultdict(dict)
    for projection in projections:
        key = (
            projection["scaling_mode"], projection["target_triples"],
            projection["node_count"], projection["reasoner"],
            projection["repetition"],
        )
        grouped[key].setdefault(str(projection["layout"]), []).append(projection)

    validation_rows: list[dict[str, Any]] = []
    for layouts in grouped.values():
        reference = {
            str(item["query_id"]): item
            for item in layouts.get("replicated", [])
        }
        for layout, selected in layouts.items():
            for item in selected:
                canonical = reference.get(str(item["query_id"]))
                valid = bool(canonical) and all((
                    int(item["result_count"]) == int(canonical["result_count"]),
                    item["ask_result"] == canonical["ask_result"],
                    item["result_digest"] == canonical["result_digest"],
                ))
                validation_rows.append({
                    "run_id": item["run_id"],
                    "scaling_mode": item["scaling_mode"],
                    "layout": layout,
                    "reasoner": item["reasoner"],
                    "reasoning_task": item["reasoning_task"],
                    "target_triples": item["target_triples"],
                    "node_count": item["node_count"],
                    "repetition": item["repetition"],
                    "query_id": item["query_id"],
                    "category": item["category"],
                    "execution_scope": item["execution_scope"],
                    "merge_strategy": item["merge_strategy"],
                    "observed_count": item["result_count"],
                    "replicated_count": canonical["result_count"] if canonical else "",
                    "observed_ask": item["ask_result"],
                    "replicated_ask": canonical["ask_result"] if canonical else "",
                    "observed_digest": item["result_digest"],
                    "replicated_digest": canonical["result_digest"] if canonical else "",
                    "valid": valid,
                    "status": "equivalent" if valid else (
                        "replicated_reference_unavailable" if canonical is None else "mismatch"
                    ),
                })

    by_validation_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in validation_rows:
        by_validation_run[str(item["run_id"])].append(item)
    for run_id, row in by_run.items():
        selected = by_validation_run.get(run_id, [])
        if selected:
            valid_count = sum(bool(item["valid"]) for item in selected)
            row["semantic_validation_queries"] = len(selected)
            row["semantic_validation_rate"] = valid_count / len(selected)
            row["semantic_equivalence_status"] = (
                "query_projection_equivalent"
                if valid_count == len(selected)
                else "query_projection_mismatch"
            )
        elif row.get("semantic_equivalence_status") == "validation_failed":
            row["semantic_validation_queries"] = 0
            row["semantic_validation_rate"] = ""
        elif int(row.get("repetition", 0)) == 1 and row.get("status") == "completed":
            row["semantic_validation_queries"] = 0
            row["semantic_validation_rate"] = ""
            row["semantic_equivalence_status"] = "validation_unavailable"
        else:
            row["semantic_validation_queries"] = 0
            row["semantic_validation_rate"] = ""
            row["semantic_equivalence_status"] = "not_sampled"
    return validation_rows


def _statistics(rows: list[dict[str, Any]], config: DistributedReasoningConfig) -> list[dict[str, Any]]:
    metrics = (
        "reasoning_critical_path_ms", "prepare_wall_ms", "reasoning_throughput_triples_s",
        "end_to_end_throughput_triples_s", "speedup", "parallel_efficiency",
        "weak_scaling_efficiency", "coordination_overhead_pct", "fragment_imbalance_ratio",
        "normalized_inferred_triples", "normalized_closure_triples",
        "process_cpu_ms", "peak_rss_kib", "network_bytes", "disk_io_bytes",
        "validation_digest_overhead_ms", "std_fragment_triples", "straggler_ratio",
    )
    groups = defaultdict(list)
    for row in rows:
        if row["status"] == "completed":
            groups[(row["scaling_mode"], row["layout"], row["reasoner"], row["reasoning_task"],
                    row["target_triples"], row["node_count"])].append(row)
    output = []
    alpha = (1 - config.confidence_level) / 2
    for key, selected in groups.items():
        for metric in metrics:
            values = np.asarray([float(row[metric]) for row in selected if row.get(metric) not in ("", None) and math.isfinite(float(row[metric]))])
            if not len(values):
                continue
            rng = np.random.default_rng(config.seed)
            bootstrap = np.asarray([np.median(rng.choice(values, len(values), replace=True)) for _ in range(config.bootstrap_samples)])
            output.append({
                "scaling_mode": key[0], "layout": key[1], "reasoner": key[2], "reasoning_task": key[3],
                "target_triples": key[4], "node_count": key[5], "metric": metric, "samples": len(values),
                "mean": float(values.mean()), "median": float(np.median(values)),
                "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
                "q1": float(np.percentile(values, 25)), "q3": float(np.percentile(values, 75)),
                "iqr": float(np.percentile(values, 75) - np.percentile(values, 25)),
                "ci95_low": float(np.quantile(bootstrap, alpha)),
                "ci95_high": float(np.quantile(bootstrap, 1 - alpha)),
            })
    return output


def _capacity(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = defaultdict(list)
    for row in rows:
        if row["scaling_mode"] == "strong":
            groups[(row["layout"], row["reasoner"], row["reasoning_task"], row["node_count"])].append(row)
    output = []
    for key, selected in sorted(groups.items()):
        successful = [int(row["target_triples"]) for row in selected if row["status"] == "completed"]
        censored = sorted({int(row["target_triples"]) for row in selected if row["status"] != "completed"})
        output.append({
            "layout": key[0], "reasoner": key[1], "reasoning_task": key[2], "node_count": key[3],
            "largest_successful_graph": max(successful, default=""),
            "smallest_censored_graph": min(censored, default=""),
            "capacity_observation": "right-censored" if censored else "within-tested-range",
        })
    return output


def run_distributed_reasoning_scalability(
    benchmark: BenchmarkConfig, experiment: DistributedReasoningConfig,
    target: str, output_root: Path, endpoint_urls: list[str] | None = None,
) -> Path:
    if target != "physical":
        raise ValueError("Distributed reasoning scalability requires physical workers")
    all_endpoints = discover(endpoint_urls or [])
    effective = replace(
        benchmark,
        distributed=replace(benchmark.distributed, request_timeout_seconds=experiment.request_timeout_seconds),
        limits=replace(benchmark.limits, phase_timeout_seconds=experiment.point_timeout_seconds,
                       point_timeout_seconds=experiment.point_timeout_seconds),
    )
    rows: list[dict[str, Any]] = []
    node_rows: list[dict[str, Any]] = []
    query_rows: list[dict[str, Any]] = []
    semantic_projections: list[dict[str, Any]] = []
    specs = load_catalog(benchmark.resolve(benchmark.query_catalog), benchmark.root)
    stopped: dict[tuple[str, str, str], str] = {}
    incompatible_profiles: dict[tuple[str, str], str] = {}
    points = []
    if experiment.strong_scaling:
        points.extend(("strong", triples, nodes, triples / nodes) for triples in experiment.target_triples for nodes in experiment.node_counts)
    if experiment.weak_scaling:
        points.extend(("weak", experiment.weak_triples_per_node * nodes, nodes, experiment.weak_triples_per_node) for nodes in experiment.node_counts)
    for scaling_mode, triples, node_count, triples_per_node in points:
        endpoints = _select_endpoints(all_endpoints, node_count)
        for layout in experiment.layouts:
            for reasoner in experiment.reasoners:
                semantics = reasoner_semantics(reasoner)
                for repetition in range(1, experiment.repetitions + 1):
                    run_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{experiment.seed}:{scaling_mode}:{triples}:{node_count}:{layout}:{reasoner}:{repetition}"))
                    common = {
                        "run_id": run_id, "architecture": target, "scaling_mode": scaling_mode,
                        "layout": layout, "reasoner": reasoner, **semantics,
                        "ontology_profile": "runtime-checked-rdf-owl-input",
                        "target_triples": triples, "node_count": node_count,
                        "triples_per_node": triples_per_node, "repetition": repetition,
                        "seed": experiment.seed, "endpoint_roles": ",".join(item.role for item in endpoints),
                        "validation_sampled": bool(experiment.semantic_validation and repetition == 1),
                    }
                    key = (scaling_mode, layout, reasoner)
                    profile_key = (layout, reasoner)
                    if profile_key in incompatible_profiles:
                        rows.append({
                            **common, "status": "skipped_profile_incompatible",
                            "censored": False, "profile_compatible": False,
                            "error": incompatible_profiles[profile_key],
                        })
                        continue
                    if experiment.stop_after_timeout and key in stopped:
                        rows.append({**common, "status": "skipped_after_timeout", "censored": True,
                                     "error": stopped[key], "timeout_seconds": experiment.point_timeout_seconds})
                        continue
                    started = monotonic()
                    try:
                        wall_ms, prepared = _prepare(
                            effective, experiment, endpoints, layout, reasoner,
                            triples, bool(experiment.semantic_validation and repetition == 1),
                        )
                        if (
                            not unlimited_execution()
                            and monotonic() - started > experiment.point_timeout_seconds
                        ):
                            raise TimeoutError("distributed reasoning point exceeded its configured budget")
                        row, nodes = _measurement(common, wall_ms, prepared, layout)
                        rows.append(row)
                        node_rows.extend(nodes)
                        if experiment.semantic_validation and repetition == 1:
                            try:
                                validation_wall_ms, projection = _semantic_projection(
                                    effective, endpoints, specs, layout, common,
                                    experiment.point_timeout_seconds,
                                )
                                row["semantic_validation_wall_ms"] = validation_wall_ms
                                semantic_projections.extend(projection)
                            except Exception as validation_error:
                                row["semantic_validation_wall_ms"] = ""
                                row["semantic_equivalence_status"] = "validation_failed"
                                row["semantic_validation_error"] = error_text(validation_error)
                        if (
                            experiment.query_concurrency
                            and repetition == 1
                            and scaling_mode == "strong"
                        ):
                            query_rows.extend(_query_scalability(common, endpoints, specs, layout, experiment))
                    except Exception as error:
                        status = failure_status(error)
                        message = error_text(error)
                        failed_common = dict(common)
                        profile_incompatible = (
                            "outside the required OWL profile" in message
                            or "Unsupported RDF-to-OWL mapping" in message
                        )
                        if profile_incompatible:
                            failed_common["profile_compatible"] = False
                        rows.append({**failed_common, "status": status, "censored": status == "timeout",
                                     "error": message, "timeout_seconds": experiment.point_timeout_seconds})
                        if experiment.stop_after_timeout and is_boundary_failure(error):
                            stopped[key] = message
                        if profile_incompatible:
                            incompatible_profiles[profile_key] = message
    _derive_scaling(rows)
    _derive_normalized_semantics(rows)
    validation_rows = _derive_semantic_validation(rows, semantic_projections)
    output = output_root / "distributed-reasoning-scalability"
    write_dict_rows(output / "distributed-reasoning-summary.csv", rows, empty_message="No distributed reasoning rows")
    write_dict_rows(output / "node-runs.csv", node_rows, empty_message="No distributed reasoning node rows")
    if query_rows:
        write_dict_rows(output / "query-scalability.csv", query_rows, empty_message="No query scalability rows")
    if validation_rows:
        write_dict_rows(output / "semantic-validation.csv", validation_rows, empty_message="No semantic validation rows")
    write_dict_rows(output / "distributed-reasoning-statistics.csv", _statistics(rows, experiment), empty_message="No distributed reasoning statistics")
    write_dict_rows(output / "capacity-summary.csv", _capacity(rows), empty_message="No capacity observations")
    metadata = {
        **release_identity(), "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment": "distributed-reasoning-scalability", "configuration": asdict(experiment),
        "execution_policy": execution_metadata(), "semantic_tasks": REASONING_TASKS,
        "timeout_is_right_censoring": True,
        "comparison_contract": "same target graph, seed, repetition, reasoner and selected endpoints across layouts",
        "semantic_validation_sampling": "first repetition of N for every matrix point",
        "semantic_equivalence_scope": "input graph digest plus query-result projection; distributed arbitrary OWL closure equivalence is not claimed",
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2, default=str) + "\n")
    with (output / "results.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps({"schema_version": "distributed-reasoning-v1", **row}, sort_keys=True, default=str) + "\n")
    return output
