"""Balanced benchmarks for a configuration-driven physical continuum."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import platform
import statistics
from time import monotonic
from typing import Any

from .config import BenchmarkConfig
from .budget import error_text, failure_status, is_boundary_failure
from .distributed import (
    Endpoint,
    _censored_detail,
    _censored_summary,
    _detail_rows,
    _prepare,
    _query,
    _write_csv,
    discover,
)
from .queries import QuerySpec, by_categories, load_catalog
from .specification import release_identity
from .physical_cluster import load_physical_inventory


def inventory_endpoints(
    path: Path,
    topology_name: str = "physical",
) -> list[str]:
    """Load active HTTP endpoints from an elastic physical topology."""
    inventory = load_physical_inventory(path, topology_name=topology_name)
    return [node.endpoint for node in inventory.nodes]


def _calibrate(
    config: BenchmarkConfig,
    endpoints: list[Endpoint],
    specs: list[QuerySpec],
) -> tuple[
    float,
    dict[str, dict[str, dict[str, float]]],
    dict[str, dict[str, Any]],
]:
    """Run a bounded stratified sample and estimate the remaining costs."""
    by_category: dict[str, list[QuerySpec]] = {}
    for spec in specs:
        by_category.setdefault(spec.category, []).append(spec)
    sampled: list[QuerySpec] = []
    for category in config.category_order:
        candidates = by_category.get(category, [])
        if candidates and len(sampled) < config.limits.calibration_query_limit:
            sampled.append(candidates[0])
    for spec in specs:
        if (
            len(sampled) >= config.limits.calibration_query_limit
            or spec in sampled
        ):
            continue
        sampled.append(spec)
    assignment = {endpoint.url: sampled for endpoint in endpoints}
    wall_ms, responses = _query(
        config,
        endpoints,
        assignment,
        timeout_seconds=config.limits.phase_timeout_seconds,
        phase="calibration",
    )
    costs: dict[str, dict[str, dict[str, float]]] = {}
    for endpoint in endpoints:
        measurements = responses[endpoint.url]["measurements"]
        measured = {
            str(item["query_id"]): {
                "duration_ms": max(float(item["duration_ms"]), 0.001)
            }
            for item in measurements
        }
        category_medians = {
            category: statistics.median(
                measured[spec.id]["duration_ms"]
                for spec in sampled
                if spec.category == category and spec.id in measured
            )
            for category in by_category
            if any(
                spec.category == category and spec.id in measured
                for spec in sampled
            )
        }
        fallback = statistics.median(
            item["duration_ms"] for item in measured.values()
        )
        costs[endpoint.url] = {
            spec.id: measured.get(
                spec.id,
                {
                    "duration_ms": category_medians.get(
                        spec.category, fallback
                    )
                },
            )
            for spec in specs
        }
    return wall_ms, costs, responses


def balanced_assignment(
    specs: list[QuerySpec],
    endpoints: list[Endpoint],
    calibration: dict[str, dict[str, dict[str, float]]],
) -> tuple[dict[str, list[QuerySpec]], dict[str, float]]:
    """Heterogeneous LPT scheduling using per-query calibration costs.

    Queries with the largest best-node cost are assigned first to the node
    whose predicted finish time would be smallest. This accounts for both
    different host speeds and query-specific performance.
    """
    assigned = {endpoint.url: [] for endpoint in endpoints}
    predicted = {endpoint.url: 0.0 for endpoint in endpoints}
    ordered = sorted(
        specs,
        key=lambda spec: min(
            calibration[endpoint.url][spec.id]["duration_ms"]
            for endpoint in endpoints
        ),
        reverse=True,
    )
    for spec in ordered:
        endpoint = min(
            endpoints,
            key=lambda candidate: (
                predicted[candidate.url]
                + calibration[candidate.url][spec.id]["duration_ms"],
                predicted[candidate.url],
                candidate.role,
            ),
        )
        assigned[endpoint.url].append(spec)
        predicted[endpoint.url] += calibration[endpoint.url][spec.id][
            "duration_ms"
        ]
    return assigned, predicted


def _assignment_rows(
    suite: str,
    common: dict[str, Any],
    endpoints: list[Endpoint],
    assignment: dict[str, list[QuerySpec]],
    calibration: dict[str, dict[str, dict[str, float]]],
    predicted: dict[str, float],
) -> list[dict[str, Any]]:
    endpoint_by_url = {endpoint.url: endpoint for endpoint in endpoints}
    rows: list[dict[str, Any]] = []
    for url, specs in assignment.items():
        for spec in specs:
            rows.append(
                {
                    "suite": suite,
                    **common,
                    "endpoint": url,
                    "role": endpoint_by_url[url].role,
                    "tier_name": endpoint_by_url[url].tier,
                    "query_id": spec.id,
                    "category": spec.category,
                    "tier": spec.tier,
                    "status": "completed",
                    "censored": False,
                    "calibrated_query_ms": calibration[url][spec.id][
                        "duration_ms"
                    ],
                    "predicted_node_ms": predicted[url],
                }
            )
    return rows


def _node_rows(
    suite: str,
    common: dict[str, Any],
    endpoints: list[Endpoint],
    prepared: dict[str, dict[str, Any]],
    calibration_responses: dict[str, dict[str, Any]],
    query_responses: dict[str, dict[str, Any]],
    predicted: dict[str, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for endpoint in endpoints:
        measured = query_responses.get(endpoint.url)
        rows.append(
            {
                "suite": suite,
                **common,
                "endpoint": endpoint.url,
                "role": endpoint.role,
                "tier_name": endpoint.tier,
                "status": "completed",
                "censored": False,
                "reasoning_ms": prepared[endpoint.url]["reasoning_ms"],
                "generation_ms": prepared[endpoint.url]["generation_ms"],
                "prepare_transport_attempts": prepared[endpoint.url].get(
                    "_coordinator_attempts", 1
                ),
                "calibration_query_ms": calibration_responses[endpoint.url][
                    "query_cpu_ms"
                ],
                "calibration_transport_attempts": calibration_responses[
                    endpoint.url
                ].get("_coordinator_attempts", 1),
                "predicted_query_ms": predicted[endpoint.url],
                "measured_query_ms": (
                    measured["query_cpu_ms"] if measured else 0.0
                ),
                "query_count": measured["query_count"] if measured else 0,
                "query_transport_attempts": (
                    measured.get("_coordinator_attempts", 1)
                    if measured
                    else 0
                ),
            }
        )
    return rows


def _metadata(
    config: BenchmarkConfig,
    endpoints: list[Endpoint],
    suite: str,
    inventory: Path,
) -> dict[str, Any]:
    return {
        **release_identity(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "suite": suite,
        "mode": "physical-elastic-adaptive-lpt",
        "inventory": str(inventory.resolve()),
        "endpoints": [
            {
                "url": endpoint.url,
                "node_id": endpoint.role,
                "tier": endpoint.tier,
                "authority": endpoint.authority,
            }
            for endpoint in endpoints
        ],
        "reasoners": list(config.reasoners),
        "repetitions": config.repetitions,
        "seed": config.seed,
        "replica_count": len(endpoints),
        "node_count": len(endpoints),
        "balancing": (
            "one unmeasured stratified calibration sample per reasoner and "
            "dataset on every node, category-median estimation for queries "
            "outside the sample, reused across repetitions, followed by "
            "heterogeneous longest-processing-time greedy scheduling"
        ),
        "calibration_query_limit": config.limits.calibration_query_limit,
        "calibration_in_timed_total": False,
        "calibration_prepare_in_timed_total": False,
        "calibration_reused_across_repetitions": True,
        "transport": {
            "timeout_seconds": config.distributed.request_timeout_seconds,
            "retries": config.distributed.request_retries,
            "retry_delay_in_phase_wall_time": True,
            "retry_counts_in_summary_and_node_runs": True,
        },
        "execution_limits": {
            "phase_timeout_seconds": config.limits.phase_timeout_seconds,
            "point_timeout_seconds": config.limits.point_timeout_seconds,
            "stop_scaling_after_timeout": (
                config.limits.stop_scaling_after_timeout
            ),
            "timeout_semantics": "right-censored with monotone early stop",
        },
    }


def _summary(
    common: dict[str, Any],
    query_count: int,
    prepare_wall_ms: float,
    calibration_wall_ms: float,
    query_wall_ms: float,
    prepared: dict[str, dict[str, Any]],
    responses: dict[str, dict[str, Any]],
    predicted: dict[str, float],
    calibration_reused: bool,
) -> dict[str, Any]:
    node_query_ms = sum(
        float(response["query_cpu_ms"]) for response in responses.values()
    )
    return {
        **common,
        "status": "completed",
        "censored": False,
        "query_count": query_count,
        "node_count": len(prepared),
        "prepare_wall_ms": prepare_wall_ms,
        "calibration_wall_ms_excluded": calibration_wall_ms,
        "calibration_reused": calibration_reused,
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
        "node_query_ms_sum": node_query_ms,
        "max_predicted_node_ms": max(predicted.values()),
        "balance_efficiency": (
            node_query_ms / (len(prepared) * query_wall_ms)
            if query_wall_ms
            else 0.0
        ),
        "total_wall_ms": prepare_wall_ms + query_wall_ms,
        "input_triples_per_replica": next(iter(prepared.values()))[
            "input_triples"
        ],
        "output_triples_per_replica": next(iter(prepared.values()))[
            "output_triples"
        ],
    }


def _append_failure(
    details: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    common: dict[str, Any],
    node_count: int,
    query_count: int,
    status: str,
    phase: str,
    error: str,
    timeout_seconds: float,
    elapsed_seconds: float = 0.0,
) -> None:
    summaries.append(
        _censored_summary(
            common,
            node_count,
            query_count,
            status,
            phase,
            error,
            timeout_seconds,
            elapsed_seconds,
        )
    )
    detail = _censored_detail(
        common, status, phase, error, timeout_seconds
    )
    details.append(detail)
    assignments.append(detail)
    nodes.append(detail)


def run_physical_cumulative(
    config: BenchmarkConfig,
    inventory: Path,
    output_root: Path,
    topology_name: str = "physical",
) -> Path:
    declared = load_physical_inventory(
        inventory,
        topology_name=topology_name,
    )
    endpoint_urls = [node.endpoint for node in declared.nodes]
    endpoints = discover(
        endpoint_urls,
        declared.nodes,
        declared.topology.fingerprint if declared.topology is not None else None,
    )
    node_count = len(endpoints)
    endpoint_by_url = {endpoint.url: endpoint for endpoint in endpoints}
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    details: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    topology_stopped = False
    stop_reason = ""

    for reasoner in config.reasoners:
        if topology_stopped:
            for repetition in range(1, config.repetitions + 1):
                for stage, category in enumerate(
                    config.category_order, start=1
                ):
                    common = {
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "stage": stage,
                        "added_category": category,
                        "calibration_reused": False,
                    }
                    _append_failure(
                        details,
                        summaries,
                        assignments,
                        nodes,
                        common,
                        node_count,
                        len(by_categories(specs, set(config.category_order[:stage]))),
                        "skipped_after_timeout",
                        "early-stop",
                        stop_reason,
                        config.limits.point_timeout_seconds,
                    )
            continue
        print(
            f"[physical-cumulative] reasoner={reasoner} "
            f"phase=calibration-prepare nodes={node_count} status=running",
            flush=True,
        )
        phase_started = monotonic()
        phase = "calibration-prepare"
        try:
            _prepare(config, endpoints, reasoner, 0, config.seed)
            print(
                f"[physical-cumulative] reasoner={reasoner} "
                f"phase=calibration nodes={node_count} "
                f"queries={min(len(specs), config.limits.calibration_query_limit)} "
                "status=running",
                flush=True,
            )
            phase = "calibration"
            (
                calibration_ms,
                calibration,
                calibration_responses,
            ) = _calibrate(config, endpoints, specs)
        except Exception as error:
            if not is_boundary_failure(error):
                raise
            status = failure_status(error)
            stop_reason = error_text(error)
            for repetition in range(1, config.repetitions + 1):
                for stage, category in enumerate(
                    config.category_order, start=1
                ):
                    common = {
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "stage": stage,
                        "added_category": category,
                        "calibration_reused": False,
                    }
                    row_status = (
                        status
                        if repetition == 1 and stage == 1
                        else "skipped_after_timeout"
                    )
                    _append_failure(
                        details,
                        summaries,
                        assignments,
                        nodes,
                        common,
                        node_count,
                        len(by_categories(specs, set(config.category_order[:stage]))),
                        row_status,
                        phase,
                        stop_reason,
                        config.limits.phase_timeout_seconds,
                        monotonic() - phase_started
                        if row_status == status else 0.0,
                    )
            topology_stopped = config.limits.stop_scaling_after_timeout
            print(
                f"[physical-cumulative] reasoner={reasoner} phase={phase} "
                f"status={status} "
                f"limit_s={config.limits.phase_timeout_seconds:g}",
                flush=True,
            )
            continue
        for repetition in range(1, config.repetitions + 1):
            if topology_stopped:
                for stage, category in enumerate(
                    config.category_order, start=1
                ):
                    common = {
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "stage": stage,
                        "added_category": category,
                        "calibration_reused": True,
                    }
                    _append_failure(
                        details, summaries, assignments, nodes,
                        common, node_count,
                        len(by_categories(specs, set(config.category_order[:stage]))),
                        "skipped_after_timeout", "early-stop", stop_reason,
                        config.limits.point_timeout_seconds,
                    )
                continue
            print(
                f"[physical-cumulative] reasoner={reasoner} "
                f"repetition={repetition}/{config.repetitions} "
                f"nodes={node_count} phase=prepare status=running",
                flush=True,
            )
            point_started = monotonic()
            try:
                prepare_wall_ms, prepared = _prepare(
                    config, endpoints, reasoner, 0, config.seed
                )
            except Exception as error:
                if not is_boundary_failure(error):
                    raise
                status = failure_status(error)
                stop_reason = error_text(error)
                for stage, category in enumerate(
                    config.category_order, start=1
                ):
                    common = {
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "stage": stage,
                        "added_category": category,
                        "calibration_reused": True,
                    }
                    row_status = status if stage == 1 else "skipped_after_timeout"
                    _append_failure(
                        details, summaries, assignments, nodes,
                        common, node_count,
                        len(by_categories(specs, set(config.category_order[:stage]))),
                        row_status, "prepare", stop_reason,
                        config.limits.point_timeout_seconds,
                        monotonic() - point_started if stage == 1 else 0.0,
                    )
                topology_stopped = config.limits.stop_scaling_after_timeout
                continue
            recorded_calibration_ms = (
                calibration_ms if repetition == 1 else 0.0
            )
            active: set[str] = set()
            for stage, category in enumerate(config.category_order, start=1):
                active.add(category)
                active_specs = by_categories(specs, active)
                assignment, predicted = balanced_assignment(
                    active_specs, endpoints, calibration
                )
                loads = ",".join(
                    f"{endpoint.role}:{len(assignment[endpoint.url])}"
                    f"/{predicted[endpoint.url]:.1f}ms"
                    for endpoint in endpoints
                )
                print(
                    f"[physical-cumulative] reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    f"stage={stage}/{len(config.category_order)} "
                    f"category={category} queries={len(active_specs)} "
                    f"balance={loads} status=running",
                    flush=True,
                )
                common = {
                    "reasoner": reasoner,
                    "repetition": repetition,
                    "stage": stage,
                    "added_category": category,
                    "calibration_reused": True,
                }
                query_started = monotonic()
                try:
                    query_wall_ms, responses = _query(
                        config,
                        endpoints,
                        assignment,
                        timeout_seconds=max(
                            config.limits.point_timeout_seconds
                            - prepare_wall_ms / 1000,
                            0.001,
                        ),
                        phase="physical-balanced-queries",
                    )
                except Exception as error:
                    if not is_boundary_failure(error):
                        raise
                    status = failure_status(error)
                    stop_reason = error_text(error)
                    _append_failure(
                        details, summaries, assignments, nodes,
                        common, node_count, len(active_specs), status,
                        "queries", stop_reason,
                        config.limits.point_timeout_seconds,
                        prepare_wall_ms / 1000 + monotonic() - query_started,
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
                            "calibration_reused": True,
                        }
                        _append_failure(
                            details, summaries, assignments, nodes,
                            skipped_common, node_count,
                            len(
                                by_categories(
                                    specs,
                                    set(config.category_order[:skipped_stage]),
                                )
                            ),
                            "skipped_after_timeout", "early-stop", stop_reason,
                            config.limits.point_timeout_seconds,
                        )
                    topology_stopped = (
                        config.limits.stop_scaling_after_timeout
                    )
                    break
                details.extend(
                    _detail_rows(responses, endpoint_by_url, common)
                )
                assignments.extend(
                    _assignment_rows(
                        "cumulative",
                        common,
                        endpoints,
                        assignment,
                        calibration,
                        predicted,
                    )
                )
                nodes.extend(
                    _node_rows(
                        "cumulative",
                        common,
                        endpoints,
                        prepared,
                        calibration_responses,
                        responses,
                        predicted,
                    )
                )
                summary = _summary(
                    common,
                    len(active_specs),
                    prepare_wall_ms,
                    recorded_calibration_ms,
                    query_wall_ms,
                    prepared,
                    responses,
                    predicted,
                    True,
                )
                summaries.append(summary)
                print(
                    f"[physical-cumulative] reasoner={reasoner} "
                    f"stage={stage}/{len(config.category_order)} "
                    f"category={category} status=done "
                    f"wall_ms={summary['total_wall_ms']:.2f}",
                    flush=True,
                )

    output = output_root / "cumulative"
    _write_csv(output / "query-runs.csv", details)
    _write_csv(output / "summary.csv", summaries)
    _write_csv(output / "assignments.csv", assignments)
    _write_csv(output / "node-runs.csv", nodes)
    metadata = _metadata(config, endpoints, "cumulative", inventory)
    metadata["category_order"] = list(config.category_order)
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


def run_physical_scalability(
    config: BenchmarkConfig,
    inventory: Path,
    output_root: Path,
    topology_name: str = "physical",
) -> Path:
    declared = load_physical_inventory(
        inventory,
        topology_name=topology_name,
    )
    endpoint_urls = [node.endpoint for node in declared.nodes]
    endpoints = discover(
        endpoint_urls,
        declared.nodes,
        declared.topology.fingerprint if declared.topology is not None else None,
    )
    node_count = len(endpoints)
    endpoint_by_url = {endpoint.url: endpoint for endpoint in endpoints}
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    details: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    topology_stopped = False
    stop_reason = ""

    for block, users in enumerate(config.scale_users, start=1):
        for reasoner in config.reasoners:
            if topology_stopped:
                for repetition in range(1, config.repetitions + 1):
                    common = {
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "synthetic_users": users,
                        "synthetic_triples": "",
                        "calibration_reused": False,
                    }
                    summary = _censored_summary(
                        common,
                        node_count,
                        len(specs),
                        "skipped_after_timeout",
                        "early-stop",
                        stop_reason,
                        config.limits.point_timeout_seconds,
                        0.0,
                    )
                    detail = _censored_detail(
                        common,
                        "skipped_after_timeout",
                        "early-stop",
                        stop_reason,
                        config.limits.point_timeout_seconds,
                    )
                    summaries.append(summary)
                    details.append(detail)
                    assignments.append(detail)
                    nodes.append(detail)
                continue
            print(
                f"[physical-scalability] block={block}/"
                f"{len(config.scale_users)} users={users} "
                f"reasoner={reasoner} phase=calibration-prepare "
                f"nodes={node_count} status=running",
                flush=True,
            )
            phase_started = monotonic()
            phase = "calibration-prepare"
            try:
                _prepare(config, endpoints, reasoner, users, config.seed)
                print(
                    f"[physical-scalability] block={block}/"
                    f"{len(config.scale_users)} users={users} "
                    f"reasoner={reasoner} phase=calibration "
                    f"nodes={node_count} "
                    f"queries={min(len(specs), config.limits.calibration_query_limit)} "
                    "status=running",
                    flush=True,
                )
                phase = "calibration"
                (
                    calibration_ms,
                    calibration,
                    calibration_responses,
                ) = _calibrate(config, endpoints, specs)
            except Exception as error:
                if not is_boundary_failure(error):
                    raise
                status = failure_status(error)
                stop_reason = error_text(error)
                common = {
                    "reasoner": reasoner,
                    "repetition": 1,
                    "synthetic_users": users,
                    "synthetic_triples": "",
                    "calibration_reused": False,
                }
                summary = _censored_summary(
                    common,
                    node_count,
                    len(specs),
                    status,
                    phase,
                    stop_reason,
                    config.limits.phase_timeout_seconds,
                    monotonic() - phase_started,
                )
                detail = _censored_detail(
                    common,
                    status,
                    phase,
                    stop_reason,
                    config.limits.phase_timeout_seconds,
                )
                summaries.append(summary)
                details.append(detail)
                assignments.append(detail)
                nodes.append(detail)
                for skipped_repetition in range(2, config.repetitions + 1):
                    skipped_common = {
                        **common,
                        "repetition": skipped_repetition,
                    }
                    _append_failure(
                        details, summaries, assignments, nodes,
                        skipped_common, node_count, len(specs),
                        "skipped_after_timeout", "early-stop", stop_reason,
                        config.limits.point_timeout_seconds,
                    )
                topology_stopped = config.limits.stop_scaling_after_timeout
                print(
                    f"[physical-scalability] block={block} users={users} "
                    f"reasoner={reasoner} phase={phase} status={status} "
                    f"limit_s={config.limits.phase_timeout_seconds:g}; "
                    "remaining larger points will be skipped",
                    flush=True,
                )
                continue
            for repetition in range(1, config.repetitions + 1):
                if topology_stopped:
                    common = {
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "synthetic_users": users,
                        "synthetic_triples": "",
                        "calibration_reused": True,
                    }
                    _append_failure(
                        details, summaries, assignments, nodes,
                        common, node_count, len(specs),
                        "skipped_after_timeout", "early-stop", stop_reason,
                        config.limits.point_timeout_seconds,
                    )
                    continue
                print(
                    f"[physical-scalability] block={block}/"
                    f"{len(config.scale_users)} users={users} "
                    f"reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    f"nodes={node_count} phase=prepare status=running",
                    flush=True,
                )
                point_started = monotonic()
                phase = "prepare"
                try:
                    prepare_wall_ms, prepared = _prepare(
                        config, endpoints, reasoner, users, config.seed
                    )
                    recorded_calibration_ms = (
                        calibration_ms if repetition == 1 else 0.0
                    )
                    assignment, predicted = balanced_assignment(
                        specs, endpoints, calibration
                    )
                    loads = ",".join(
                        f"{endpoint.role}:{len(assignment[endpoint.url])}"
                        f"/{predicted[endpoint.url]:.1f}ms"
                        for endpoint in endpoints
                    )
                    print(
                        f"[physical-scalability] block={block}/"
                        f"{len(config.scale_users)} users={users} "
                        f"reasoner={reasoner} balance={loads} status=running",
                        flush=True,
                    )
                    phase = "queries"
                    query_wall_ms, responses = _query(
                        config,
                        endpoints,
                        assignment,
                        timeout_seconds=max(
                            config.limits.point_timeout_seconds
                            - (monotonic() - point_started),
                            0.001,
                        ),
                        phase="physical-balanced-queries",
                    )
                except Exception as error:
                    if not is_boundary_failure(error):
                        raise
                    status = failure_status(error)
                    stop_reason = error_text(error)
                    common = {
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "synthetic_users": users,
                        "synthetic_triples": "",
                        "calibration_reused": True,
                    }
                    summary = _censored_summary(
                        common,
                        node_count,
                        len(specs),
                        status,
                        phase,
                        stop_reason,
                        config.limits.point_timeout_seconds,
                        monotonic() - point_started,
                    )
                    detail = _censored_detail(
                        common,
                        status,
                        phase,
                        stop_reason,
                        config.limits.point_timeout_seconds,
                    )
                    summaries.append(summary)
                    details.append(detail)
                    assignments.append(detail)
                    nodes.append(detail)
                    topology_stopped = (
                        config.limits.stop_scaling_after_timeout
                    )
                    print(
                        f"[physical-scalability] block={block} users={users} "
                        f"reasoner={reasoner} phase={phase} status={status} "
                        f"limit_s={config.limits.point_timeout_seconds:g}",
                        flush=True,
                    )
                    continue
                common = {
                    "reasoner": reasoner,
                    "repetition": repetition,
                    "synthetic_users": users,
                    "synthetic_triples": next(iter(prepared.values()))[
                        "synthetic_triples"
                    ],
                    "calibration_reused": True,
                }
                details.extend(
                    _detail_rows(responses, endpoint_by_url, common)
                )
                assignments.extend(
                    _assignment_rows(
                        "scalability",
                        common,
                        endpoints,
                        assignment,
                        calibration,
                        predicted,
                    )
                )
                nodes.extend(
                    _node_rows(
                        "scalability",
                        common,
                        endpoints,
                        prepared,
                        calibration_responses,
                        responses,
                        predicted,
                    )
                )
                summary = _summary(
                    common,
                    len(specs),
                    prepare_wall_ms,
                    recorded_calibration_ms,
                    query_wall_ms,
                    prepared,
                    responses,
                    predicted,
                    True,
                )
                summary["node_generation_ms_sum"] = sum(
                    float(item["generation_ms"])
                    for item in prepared.values()
                )
                summaries.append(summary)
                print(
                    f"[physical-scalability] block={block}/"
                    f"{len(config.scale_users)} users={users} "
                    f"reasoner={reasoner} status=done "
                    f"queries={len(specs)} "
                    f"wall_ms={summary['total_wall_ms']:.2f}",
                    flush=True,
                )

    output = output_root / "scalability"
    _write_csv(output / "query-runs.csv", details)
    _write_csv(output / "summary.csv", summaries)
    _write_csv(output / "assignments.csv", assignments)
    _write_csv(output / "node-runs.csv", nodes)
    metadata = _metadata(config, endpoints, "scalability", inventory)
    metadata["scale_users"] = list(config.scale_users)
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output
