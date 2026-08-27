"""Three non-confounded experiments for continuum ontology evaluation.

The module deliberately separates replicated query scale-out, isolated
hardware reasoning, and authority-partitioned ontology execution.  A result
from one family must not be used as a measurement of another family.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import struct
from time import perf_counter_ns
from typing import Any

import numpy as np

from .config import BenchmarkConfig
from .csv_utils import write_dict_rows
from .distributed import Endpoint, _parallel, _request, discover
from .experiment_config import ExperimentConfig, ReasoningProfile
from .load_benchmark import _local_timeout
from .node import NodeRuntime
from .queries import QuerySpec, execute_query_detailed, load_catalog
from .specification import release_identity
from .sharded import (
    _assignment as sharded_assignment,
    _baseline_counts,
    _merge_responses,
    _summary as sharded_summary,
    _validation_rows,
)


EXPERIMENTS = (
    "scale-out",
    "reasoning-hardware",
    "distributed-ontology",
)


def _write(path: Path, rows: list[dict[str, Any]]) -> None:
    write_dict_rows(path, rows, empty_message=f"No rows for {path}")


def _metadata(
    target: str,
    experiment: str,
    config: BenchmarkConfig,
    workload: ExperimentConfig,
    endpoints: list[Endpoint],
) -> dict[str, Any]:
    endpoint_hardware = []
    for endpoint in endpoints:
        if endpoint.url.startswith("local://"):
            endpoint_hardware.append(
                {
                    "url": endpoint.url,
                    "role": endpoint.role,
                    "python_version": platform.python_version(),
                    "platform": platform.platform(),
                    "machine": platform.machine(),
                    "cpu_count": os.cpu_count() or 0,
                    "pointer_bits": struct.calcsize("P") * 8,
                    "total_memory_kib": 0,
                }
            )
            continue
        try:
            health = _request(
                endpoint.url,
                "/health",
                timeout=5.0,
                retries=0,
            )
        except Exception as error:
            endpoint_hardware.append(
                {
                    "url": endpoint.url,
                    "role": endpoint.role,
                    "metadata_error": f"{type(error).__name__}: {error}",
                }
            )
            continue
        endpoint_hardware.append(
            {
                key: health.get(key, "")
                for key in (
                    "role",
                    "python_version",
                    "platform",
                    "machine",
                    "cpu_count",
                    "pointer_bits",
                    "total_memory_kib",
                )
            }
            | {"url": endpoint.url}
        )
    return {
        **release_identity(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment": experiment,
        "architecture": target,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "reasoners": list(config.reasoners),
        "repetitions": workload.repetitions,
        "request_timeout_seconds": workload.request_timeout_seconds,
        "seed": workload.seed,
        "endpoints": [
            {"url": endpoint.url, "role": endpoint.role}
            for endpoint in endpoints
        ],
        "endpoint_hardware": endpoint_hardware,
    }


def _save_metadata(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _target_runtime(
    config: BenchmarkConfig,
    target: str,
    endpoint_urls: list[str] | None,
) -> tuple[NodeRuntime | None, list[Endpoint]]:
    if target == "monolith":
        return NodeRuntime(config.root, "cloud"), [
            Endpoint("local://cloud", "cloud")
        ]
    if target not in {"docker", "physical"}:
        raise ValueError(f"Unknown experiment target {target!r}")
    return None, discover(endpoint_urls or [])


def _phase_payload(
    workload: ExperimentConfig,
    *,
    reasoner: str,
    users: int,
    mode: str,
    target_triples: int = 0,
    rule_count: int = 0,
    padding_mode: str = "neutral",
) -> dict[str, Any]:
    return {
        "reasoner": reasoner,
        "users": users,
        "seed": workload.seed,
        "mode": mode,
        "target_triples": target_triples,
        "rule_count": rule_count,
        "padding_mode": padding_mode,
        "phase_timeout_seconds": max(
            workload.request_timeout_seconds - 1.0,
            0.1,
        ),
    }


def _prepare_one(
    runtime: NodeRuntime | None,
    endpoint: Endpoint,
    payload: dict[str, Any],
    timeout: float,
) -> tuple[float, dict[str, Any]]:
    started = perf_counter_ns()
    if runtime is not None:
        with _local_timeout(timeout):
            result = runtime.prepare(**payload)
    else:
        result = _request(
            endpoint.url,
            "/prepare",
            payload,
            timeout=timeout,
            retries=0,
        )
    return (perf_counter_ns() - started) / 1_000_000, result


def _execute_one(
    runtime: NodeRuntime | None,
    endpoint: Endpoint,
    query_ids: list[str],
    timeout: float,
    *,
    include_result_keys: bool = False,
) -> tuple[float, dict[str, Any]]:
    started = perf_counter_ns()
    if runtime is not None:
        with _local_timeout(timeout):
            result = runtime.execute(
                query_ids,
                include_result_keys=include_result_keys,
            )
    else:
        result = _request(
            endpoint.url,
            "/queries",
            {
                "query_ids": query_ids,
                "include_result_keys": include_result_keys,
                "phase_timeout_seconds": max(timeout - 1.0, 0.1),
            },
            timeout=timeout,
            retries=0,
        )
    return (perf_counter_ns() - started) / 1_000_000, result


def _replicated_prepare(
    runtime: NodeRuntime | None,
    endpoints: list[Endpoint],
    payload: dict[str, Any],
    timeout: float,
) -> tuple[float, dict[str, dict[str, Any]]]:
    if runtime is not None:
        wall, result = _prepare_one(runtime, endpoints[0], payload, timeout)
        return wall, {endpoints[0].url: result}
    return _parallel(
        endpoints,
        "/prepare",
        {endpoint.url: payload for endpoint in endpoints},
        phase="experiment-replicated-prepare",
        timeout=timeout,
        retries=0,
    )


def _execute_query_assignment(
    runtime: NodeRuntime | None,
    endpoints: list[Endpoint],
    assignment: dict[str, list[str]],
    timeout: float,
    *,
    include_result_keys: bool = False,
) -> tuple[float, dict[str, dict[str, Any]]]:
    if runtime is not None:
        wall, result = _execute_one(
            runtime,
            endpoints[0],
            assignment[endpoints[0].url],
            timeout,
            include_result_keys=include_result_keys,
        )
        return wall, {endpoints[0].url: result}
    payloads = {
        endpoint.url: {
            "query_ids": assignment[endpoint.url],
            "include_result_keys": include_result_keys,
            "phase_timeout_seconds": max(timeout - 1.0, 0.1),
        }
        for endpoint in endpoints
        if assignment[endpoint.url]
    }
    return _parallel(
        endpoints,
        "/queries",
        payloads,
        phase="experiment-balanced-queries",
        timeout=timeout,
        retries=0,
    )


def _calibrate_query_costs(
    runtime: NodeRuntime | None,
    endpoints: list[Endpoint],
    specs: list[QuerySpec],
    timeout: float,
    rounds: int,
) -> tuple[dict[str, dict[str, float]], bool]:
    """Learn per-node query costs outside measured rounds.

    Every replica executes every query, so calibration also proves that all
    active replicas expose the same result digest before load is distributed.
    """

    query_ids = [spec.id for spec in specs]
    samples: dict[tuple[str, str], list[float]] = defaultdict(list)
    digests: dict[str, set[str]] = defaultdict(set)
    for _ in range(max(rounds, 1)):
        assignment = {endpoint.url: query_ids for endpoint in endpoints}
        _, responses = _execute_query_assignment(
            runtime,
            endpoints,
            assignment,
            timeout,
        )
        for url, response in responses.items():
            for measurement in response["measurements"]:
                query_id = str(measurement["query_id"])
                samples[(url, query_id)].append(
                    float(measurement["duration_ms"])
                )
                digests[query_id].add(str(measurement["result_digest"]))
    costs = {
        endpoint.url: {
            spec.id: float(np.median(samples[(endpoint.url, spec.id)]))
            for spec in specs
        }
        for endpoint in endpoints
    }
    consistent = all(len(digests[spec.id]) == 1 for spec in specs)
    return costs, consistent


def _optimized_assignment(
    specs: list[QuerySpec],
    endpoints: list[Endpoint],
    costs: dict[str, dict[str, float]],
    *,
    rotation: int = 0,
) -> tuple[dict[str, list[str]], dict[str, float]]:
    """Greedy unrelated-machine scheduling using measured query costs."""

    rotated = specs[rotation % len(specs) :] + specs[: rotation % len(specs)]
    ordered = sorted(
        rotated,
        key=lambda spec: max(
            costs[endpoint.url][spec.id] for endpoint in endpoints
        ),
        reverse=True,
    )
    assignment = {endpoint.url: [] for endpoint in endpoints}
    predicted = {endpoint.url: 0.0 for endpoint in endpoints}
    for spec in ordered:
        selected = min(
            endpoints,
            key=lambda endpoint: (
                predicted[endpoint.url] + costs[endpoint.url][spec.id],
                predicted[endpoint.url],
                endpoint.role,
            ),
        )
        assignment[selected.url].append(spec.id)
        predicted[selected.url] += costs[selected.url][spec.id]
    return assignment, predicted


def _measurement_rows(
    responses: dict[str, dict[str, Any]],
    endpoints: list[Endpoint],
    common: dict[str, Any],
) -> list[dict[str, Any]]:
    roles = {endpoint.url: endpoint.role for endpoint in endpoints}
    return [
        {
            **common,
            "endpoint": url,
            "role": roles[url],
            **measurement,
        }
        for url, response in responses.items()
        for measurement in response["measurements"]
    ]


def run_scale_out(
    config: BenchmarkConfig,
    workload: ExperimentConfig,
    target: str,
    output_root: Path,
    endpoint_urls: list[str] | None = None,
) -> Path:
    """Measure query scale-out after an explicitly excluded prepare phase."""

    runtime, all_endpoints = _target_runtime(config, target, endpoint_urls)
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    summary_rows: list[dict[str, Any]] = []
    query_rows: list[dict[str, Any]] = []
    node_counts = (
        (1,) if target == "monolith" else workload.scale_out_node_counts
    )
    timeout = workload.request_timeout_seconds
    for node_count in node_counts:
        endpoints = all_endpoints[:node_count]
        for reasoner in config.reasoners:
            for repetition in range(1, workload.repetitions + 1):
                label = (
                    f"[experiment-scale-out] architecture={target} "
                    f"nodes={node_count} reasoner={reasoner} "
                    f"repetition={repetition}/{workload.repetitions}"
                )
                print(f"{label} phase=prepare status=running", flush=True)
                payload = _phase_payload(
                    workload,
                    reasoner=reasoner,
                    users=workload.scale_out_users,
                    mode="replicated",
                    target_triples=workload.scale_out_target_triples,
                    rule_count=workload.scale_out_rule_count,
                    padding_mode=workload.scale_out_padding_mode,
                )
                try:
                    prepare_wall_ms, prepared = _replicated_prepare(
                        runtime, endpoints, payload, timeout
                    )
                except Exception as error:
                    summary_rows.append(
                        {
                            "architecture": target,
                            "node_count": node_count,
                            "reasoner": reasoner,
                            "repetition": repetition,
                            "query_round": 0,
                            "status": "prepare_failed",
                            "error": f"{type(error).__name__}: {error}",
                        }
                    )
                    print(
                        f"{label} phase=prepare status=failed error={error}",
                        flush=True,
                    )
                    continue
                warmup_failed = ""
                calibration_consistent = False
                query_costs: dict[str, dict[str, float]] = {}
                print(
                    f"{label} phase=calibration rounds="
                    f"{max(workload.warmup_query_rounds, 1)} "
                    "strategy=adaptive-lpt status=running",
                    flush=True,
                )
                try:
                    query_costs, calibration_consistent = (
                        _calibrate_query_costs(
                            runtime,
                            endpoints,
                            specs,
                            timeout,
                            workload.warmup_query_rounds,
                        )
                    )
                except Exception as error:
                    warmup_failed = f"{type(error).__name__}: {error}"
                if warmup_failed:
                    summary_rows.append(
                        {
                            "architecture": target,
                            "node_count": node_count,
                            "reasoner": reasoner,
                            "repetition": repetition,
                            "query_round": 0,
                            "status": "warmup_failed",
                            "error": warmup_failed,
                            "prepare_wall_ms_excluded": prepare_wall_ms,
                        }
                    )
                    print(
                        f"{label} phase=warmup status=failed "
                        f"error={warmup_failed}",
                        flush=True,
                    )
                    continue
                known_digests: dict[str, str] = {}
                for query_round in range(1, workload.query_rounds + 1):
                    print(
                        f"{label} phase=query round={query_round}/"
                        f"{workload.query_rounds} status=running",
                        flush=True,
                    )
                    try:
                        assignment, predicted_load = _optimized_assignment(
                            specs,
                            endpoints,
                            query_costs,
                            rotation=query_round - 1,
                        )
                        query_wall_ms, responses = _execute_query_assignment(
                            runtime,
                            endpoints,
                            assignment,
                            timeout,
                        )
                    except Exception as error:
                        summary_rows.append(
                            {
                                "architecture": target,
                                "node_count": node_count,
                                "reasoner": reasoner,
                                "repetition": repetition,
                                "query_round": query_round,
                                "status": "query_failed",
                                "error": f"{type(error).__name__}: {error}",
                                "prepare_wall_ms_excluded": prepare_wall_ms,
                            }
                        )
                        continue
                    common = {
                        "architecture": target,
                        "node_count": node_count,
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "query_round": query_round,
                    }
                    measurements = _measurement_rows(
                        responses, endpoints, common
                    )
                    query_rows.extend(measurements)
                    consistent = calibration_consistent
                    for item in measurements:
                        previous = known_digests.setdefault(
                            item["query_id"], item["result_digest"]
                        )
                        consistent &= previous == item["result_digest"]
                    durations = [
                        float(item["duration_ms"]) for item in measurements
                    ]
                    summary_rows.append(
                        {
                            **common,
                            "status": "completed",
                            "error": "",
                            "synthetic_users": workload.scale_out_users,
                            "target_triples_per_replica": (
                                workload.scale_out_target_triples
                            ),
                            "rule_count": workload.scale_out_rule_count,
                            "query_count": len(measurements),
                            "query_wall_ms": query_wall_ms,
                            "queries_per_second": (
                                len(measurements) / (query_wall_ms / 1000)
                                if query_wall_ms else 0.0
                            ),
                            "query_latency_p50_ms": float(
                                np.percentile(durations, 50)
                            ),
                            "query_latency_p95_ms": float(
                                np.percentile(durations, 95)
                            ),
                            "query_latency_p99_ms": float(
                                np.percentile(durations, 99)
                            ),
                            "result_digest_consistent": consistent,
                            "assignment_strategy": (
                                "calibrated-longest-processing-time"
                            ),
                            "assignment_counts": ",".join(
                                f"{endpoint.role}:"
                                f"{len(assignment[endpoint.url])}"
                                for endpoint in endpoints
                            ),
                            "predicted_max_node_query_ms": max(
                                predicted_load.values()
                            ),
                            "prepare_wall_ms_excluded": prepare_wall_ms,
                            "max_node_reasoning_ms_excluded": max(
                                float(item["reasoning_ms"])
                                for item in prepared.values()
                            ),
                            "logical_input_triples": max(
                                int(item["input_triples"])
                                for item in prepared.values()
                            ),
                            "aggregate_replica_triples": sum(
                                int(item["input_triples"])
                                for item in prepared.values()
                            ),
                            "storage_replication_factor": node_count,
                            "node_query_cpu_ms_sum": sum(
                                float(item["query_cpu_ms"])
                                for item in responses.values()
                            ),
                            "node_query_process_cpu_ms_sum": sum(
                                float(item.get("process_cpu_ms", 0.0))
                                for item in responses.values()
                            ),
                            "max_peak_rss_kib": max(
                                int(item.get("peak_rss_kib", 0))
                                for item in responses.values()
                            ),
                            "sum_current_rss_kib": sum(
                                int(item.get("current_rss_kib", 0))
                                for item in responses.values()
                            ),
                            "query_request_bytes_sum": sum(
                                int(item.get("request_bytes", 0))
                                for item in responses.values()
                            ),
                            "query_response_bytes_sum": sum(
                                int(item.get("response_bytes", 0))
                                for item in responses.values()
                            ),
                        }
                    )
                    print(
                        f"{label} phase=query round={query_round} status=done "
                        f"wall_ms={query_wall_ms:.2f}",
                        flush=True,
                    )
    output = output_root / target / "scale-out"
    _write(output / "summary.csv", summary_rows)
    if query_rows:
        _write(output / "query-runs.csv", query_rows)
    metadata = _metadata(
        target, "scale-out", config, workload, all_endpoints
    )
    metadata.update(
        {
            "prepare_excluded_from_primary_timing": True,
            "layout": "full-replica-per-active-node",
            "query_distribution": (
                "per-node calibrated longest-processing-time scheduling"
            ),
            "node_counts": list(node_counts),
            "query_rounds": workload.query_rounds,
            "warmup_query_rounds": workload.warmup_query_rounds,
        }
    )
    _save_metadata(output / "metadata.json", metadata)
    return output


def _profile_value(profile: ReasoningProfile) -> int:
    return {
        "target_triples": profile.target_triples,
        "rule_count": profile.rule_count,
        "users": profile.users,
    }[profile.dimension]


def run_reasoning_hardware(
    config: BenchmarkConfig,
    workload: ExperimentConfig,
    target: str,
    output_root: Path,
    endpoint_urls: list[str] | None = None,
) -> Path:
    """Measure each hardware endpoint independently, never as a cluster."""

    runtime, endpoints = _target_runtime(config, target, endpoint_urls)
    rows: list[dict[str, Any]] = []
    timeout = workload.request_timeout_seconds
    for endpoint in endpoints:
        for profile in workload.reasoning_profiles:
            for reasoner in config.reasoners:
                for repetition in range(1, workload.repetitions + 1):
                    label = (
                        "[experiment-reasoning-hardware] "
                        f"architecture={target} role={endpoint.role} "
                        f"profile={profile.name} reasoner={reasoner} "
                        f"repetition={repetition}/{workload.repetitions}"
                    )
                    print(f"{label} status=running", flush=True)
                    payload = _phase_payload(
                        workload,
                        reasoner=reasoner,
                        users=profile.users,
                        mode="replicated",
                        target_triples=profile.target_triples,
                        rule_count=profile.rule_count,
                        padding_mode=profile.padding_mode,
                    )
                    common = {
                        "architecture": target,
                        "endpoint": endpoint.url,
                        "role": endpoint.role,
                        "profile": profile.name,
                        "dimension": profile.dimension,
                        "dimension_value": _profile_value(profile),
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "synthetic_users": profile.users,
                        "target_triples": profile.target_triples,
                        "rule_count": profile.rule_count,
                        "padding_mode": profile.padding_mode,
                    }
                    try:
                        wall_ms, result = _prepare_one(
                            runtime, endpoint, payload, timeout
                        )
                    except Exception as error:
                        rows.append(
                            {
                                **common,
                                "status": "timeout"
                                if "timeout" in str(error).lower()
                                else "failed",
                                "error": f"{type(error).__name__}: {error}",
                                "prepare_wall_ms": "",
                                "timeout_seconds": timeout,
                            }
                        )
                        print(
                            f"{label} status=failed error={error}",
                            flush=True,
                        )
                        continue
                    rows.append(
                        {
                            **common,
                            "status": "completed",
                            "error": "",
                            "prepare_wall_ms": wall_ms,
                            "generation_ms": result["generation_ms"],
                            "reasoning_ms": result["reasoning_ms"],
                            "input_triples": result["input_triples"],
                            "output_triples": result["output_triples"],
                            "inferred_triples": result["inferred_triples"],
                            "closure_expansion_factor": (
                                int(result["output_triples"])
                                / int(result["input_triples"])
                            ),
                            "process_cpu_ms": result["process_cpu_ms"],
                            "current_rss_kib": result["current_rss_kib"],
                            "peak_rss_kib": result["peak_rss_kib"],
                            "disk_read_bytes": result["disk_read_bytes"],
                            "disk_write_bytes": result["disk_write_bytes"],
                            "timeout_seconds": timeout,
                        }
                    )
                    print(
                        f"{label} status=done reasoning_ms="
                        f"{float(result['reasoning_ms']):.2f}",
                        flush=True,
                    )
    output = output_root / target / "reasoning-hardware"
    _write(output / "summary.csv", rows)
    metadata = _metadata(
        target, "reasoning-hardware", config, workload, endpoints
    )
    metadata.update(
        {
            "execution": "one-endpoint-at-a-time",
            "cluster_aggregation": False,
            "timeout_is_right_censoring": True,
            "profiles": [
                {
                    "name": item.name,
                    "dimension": item.dimension,
                    "users": item.users,
                    "target_triples": item.target_triples,
                    "rule_count": item.rule_count,
                    "padding_mode": item.padding_mode,
                }
                for item in workload.reasoning_profiles
            ],
        }
    )
    _save_metadata(output / "metadata.json", metadata)
    return output


def _monolith_distributed_point(
    runtime: NodeRuntime,
    endpoint: Endpoint,
    specs: list[QuerySpec],
    workload: ExperimentConfig,
    reasoner: str,
    users: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = _phase_payload(
        workload,
        reasoner=reasoner,
        users=users,
        mode="replicated",
        padding_mode="neutral",
    )
    prepare_wall_ms, prepared = _prepare_one(
        runtime, endpoint, payload, workload.request_timeout_seconds
    )
    query_wall_ms, response = _execute_one(
        runtime,
        endpoint,
        [spec.id for spec in specs],
        workload.request_timeout_seconds,
        include_result_keys=True,
    )
    measurements = response["measurements"]
    summary = {
        "status": "completed",
        "prepare_wall_ms": prepare_wall_ms,
        "max_node_reasoning_ms": prepared["reasoning_ms"],
        "node_reasoning_ms_sum": prepared["reasoning_ms"],
        "query_wall_ms": query_wall_ms,
        "total_wall_ms": prepare_wall_ms + query_wall_ms,
        "query_count": len(measurements),
        "source_query_executions": len(measurements),
        "federation_fanout_factor": 1.0,
        "logical_input_triples": prepared["input_triples"],
        "aggregate_fragment_triples": prepared["input_triples"],
        "aggregate_output_triples": prepared["output_triples"],
        "aggregate_inferred_triples": prepared["inferred_triples"],
        "max_fragment_triples": prepared["input_triples"],
        "max_fragment_fraction": 1.0,
        "storage_replication_factor": 1.0,
        "max_node_peak_rss_kib": max(
            int(prepared.get("peak_rss_kib", 0)),
            int(response.get("peak_rss_kib", 0)),
        ),
        "sum_node_prepare_current_rss_kib": int(
            prepared.get("current_rss_kib", 0)
        ),
        "sum_node_query_current_rss_kib": int(
            response.get("current_rss_kib", 0)
        ),
        "max_sum_node_current_rss_kib": max(
            int(prepared.get("current_rss_kib", 0)),
            int(response.get("current_rss_kib", 0)),
        ),
        "node_prepare_process_cpu_ms_sum": float(
            prepared.get("process_cpu_ms", 0.0)
        ),
        "node_query_process_cpu_ms_sum": float(
            response.get("process_cpu_ms", 0.0)
        ),
        "total_process_cpu_ms": (
            float(prepared.get("process_cpu_ms", 0.0))
            + float(response.get("process_cpu_ms", 0.0))
        ),
        "prepare_request_bytes_sum": 0,
        "prepare_response_bytes_sum": 0,
        "query_request_bytes_sum": 0,
        "query_response_bytes_sum": 0,
        "result_validation_rate": 1.0,
        "oracle_status": "self",
        "oracle_error": "",
    }
    return summary, measurements


def run_distributed_ontology(
    config: BenchmarkConfig,
    workload: ExperimentConfig,
    target: str,
    output_root: Path,
    endpoint_urls: list[str] | None = None,
) -> Path:
    """Compare one logical graph with authority-partitioned five-node graphs."""

    runtime, endpoints = _target_runtime(config, target, endpoint_urls)
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    summary_rows: list[dict[str, Any]] = []
    query_rows: list[dict[str, Any]] = []
    validation_rows: list[dict[str, Any]] = []
    timeout = workload.request_timeout_seconds
    for users in workload.distributed_users:
        for reasoner in config.reasoners:
            pending_validation: list[
                tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]
            ] = []
            for repetition in range(1, workload.repetitions + 1):
                label = (
                    "[experiment-distributed-ontology] "
                    f"architecture={target} users={users} "
                    f"reasoner={reasoner} "
                    f"repetition={repetition}/{workload.repetitions}"
                )
                print(f"{label} phase=prepare status=running", flush=True)
                common = {
                    "architecture": target,
                    "synthetic_users": users,
                    "reasoner": reasoner,
                    "repetition": repetition,
                    "node_count": 1 if target == "monolith" else len(endpoints),
                }
                try:
                    if runtime is not None:
                        summary, measurements = _monolith_distributed_point(
                            runtime,
                            endpoints[0],
                            specs,
                            workload,
                            reasoner,
                            users,
                        )
                        summary_rows.append({**common, **summary, "error": ""})
                        query_rows.extend(
                            {
                                **common,
                                "endpoint": endpoints[0].url,
                                "role": "cloud",
                                "execution_scope": "monolith",
                                **measurement,
                            }
                            for measurement in measurements
                        )
                    else:
                        payload = _phase_payload(
                            workload,
                            reasoner=reasoner,
                            users=users,
                            mode="partitioned",
                        )
                        prepare_wall_ms, prepared = _parallel(
                            endpoints,
                            "/prepare",
                            {
                                endpoint.url: payload
                                for endpoint in endpoints
                            },
                            phase="experiment-partitioned-prepare",
                            timeout=timeout,
                            retries=0,
                        )
                        assignment = sharded_assignment(specs, endpoints)
                        query_wall_ms, responses = _parallel(
                            endpoints,
                            "/queries",
                            {
                                url: {
                                    "query_ids": [
                                        spec.id for spec in assigned
                                    ],
                                    "include_result_keys": True,
                                    "phase_timeout_seconds": max(
                                        timeout - 1.0, 0.1
                                    ),
                                }
                                for url, assigned in assignment.items()
                                if assigned
                            },
                            phase="experiment-federated-queries",
                            timeout=timeout,
                            retries=0,
                        )
                        merged, raw = _merge_responses(
                            specs, endpoints, responses, common
                        )
                        query_rows.extend(
                            {**common, **item} for item in raw
                        )
                        summary = sharded_summary(
                            common,
                            len(specs),
                            prepare_wall_ms,
                            query_wall_ms,
                            prepared,
                            responses,
                        )
                        summary_row = {
                            **summary,
                            "status": "completed",
                            "error": "",
                            "result_validation_rate": "",
                            "oracle_status": "pending",
                            "oracle_error": "",
                        }
                        summary_rows.append(summary_row)
                        pending_validation.append(
                            (common, merged, summary_row)
                        )
                except Exception as error:
                    summary_rows.append(
                        {
                            **common,
                            "status": "timeout"
                            if "timeout" in str(error).lower()
                            else "failed",
                            "error": f"{type(error).__name__}: {error}",
                            "timeout_seconds": timeout,
                        }
                    )
                    print(f"{label} status=failed error={error}", flush=True)
                    continue
                print(f"{label} status=done", flush=True)
            if target != "monolith" and pending_validation:
                print(
                    "[experiment-distributed-ontology] "
                    f"architecture={target} users={users} "
                    f"reasoner={reasoner} phase=monolith-oracle "
                    "status=running timing=excluded",
                    flush=True,
                )
                try:
                    with _local_timeout(timeout):
                        baseline = _baseline_counts(
                            config, specs, reasoner, users
                        )
                except Exception as error:
                    baseline_error = f"{type(error).__name__}: {error}"
                    for _, _, summary_row in pending_validation:
                        summary_row["oracle_status"] = "failed"
                        summary_row["oracle_error"] = baseline_error
                    print(
                        "[experiment-distributed-ontology] "
                        f"architecture={target} users={users} "
                        f"reasoner={reasoner} phase=monolith-oracle "
                        f"status=failed error={baseline_error}; "
                        "measurements remain explicitly unvalidated",
                        flush=True,
                    )
                    continue
                for common, merged, summary_row in pending_validation:
                    validation = _validation_rows(merged, baseline)
                    validation_rows.extend(
                        {**common, **item} for item in validation
                    )
                    valid_count = sum(
                        bool(item["valid"]) for item in validation
                    )
                    rate = valid_count / len(validation)
                    summary_row["result_validation_rate"] = rate
                    summary_row["oracle_status"] = "completed"
                    if rate != 1.0:
                        summary_row["status"] = "invalid_results"
                        summary_row["error"] = (
                            f"{len(validation) - valid_count}/"
                            f"{len(validation)} query results differ from "
                            "the monolithic oracle"
                        )
                print(
                    "[experiment-distributed-ontology] "
                    f"architecture={target} users={users} "
                    f"reasoner={reasoner} phase=monolith-oracle "
                    "status=done",
                    flush=True,
                )
    output = output_root / target / "distributed-ontology"
    _write(output / "summary.csv", summary_rows)
    if query_rows:
        _write(output / "query-runs.csv", query_rows)
    if validation_rows:
        _write(output / "result-validation.csv", validation_rows)
    metadata = _metadata(
        target, "distributed-ontology", config, workload, endpoints
    )
    metadata.update(
        {
            "layout": (
                "monolithic-oracle"
                if target == "monolith"
                else "authority-and-privacy-partitioned"
            ),
            "logical_dataset_is_equal_across_architectures": True,
            "distributed_reasoning": (
                "local materialisation per fragment plus federated query merge"
            ),
            "validation": (
                "exact order-independent result bag against monolithic oracle"
            ),
            "ontology_placement_manifest": str(
                config.root / "configs/ontology-placement.toml"
            ),
            "users": list(workload.distributed_users),
        }
    )
    _save_metadata(output / "metadata.json", metadata)
    return output


def run_experiment(
    name: str,
    config: BenchmarkConfig,
    workload: ExperimentConfig,
    target: str,
    output_root: Path,
    endpoint_urls: list[str] | None = None,
) -> Path:
    runners = {
        "scale-out": run_scale_out,
        "reasoning-hardware": run_reasoning_hardware,
        "distributed-ontology": run_distributed_ontology,
    }
    try:
        runner = runners[name]
    except KeyError as error:
        raise ValueError(f"Unknown experiment {name!r}") from error
    return runner(config, workload, target, output_root, endpoint_urls)
