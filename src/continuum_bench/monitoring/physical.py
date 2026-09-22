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
from .resource_summary import native_resources
from ..reasoners import reasoner_provenance
from .budget import (error_text, is_timeout_failure, TimeoutSkipState, skip_metadata,
                     PhaseBudgetTimeout, unlimited_execution)
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
from ..queries import QuerySpec, by_categories, load_catalog
from ..specification import release_identity
from .budget import execution_metadata
from ..physical_cluster import load_physical_inventory
from ..topology import Topology


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
                "prepare_process_cpu_ms": prepared[endpoint.url].get("process_cpu_ms"),
                "query_process_cpu_ms": measured.get("process_cpu_ms") if measured else None,
                "current_rss_kib": (measured or prepared[endpoint.url]).get("current_rss_kib"),
                "peak_rss_kib": (measured or prepared[endpoint.url]).get("peak_rss_kib"),
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
    inventory: Path | Topology,
) -> dict[str, Any]:
    architecture = (
        inventory.kind if isinstance(inventory, Topology) else "physical"
    )
    return {
        **release_identity(),
        "execution_policy": execution_metadata(),
        "reasoner_backends": {name: reasoner_provenance(name) for name in config.reasoners},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "suite": suite,
        "mode": f"{architecture}-elastic-adaptive-lpt",
        "architecture": architecture,
        "inventory": (
            str(inventory.resolve())
            if isinstance(inventory, Path)
            else str(inventory.source_path or inventory.name)
        ),
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
            **skip_metadata(config.limits),
            "phase_timeout_seconds": config.limits.phase_timeout_seconds,
            "point_timeout_seconds": config.limits.point_timeout_seconds,
            "stop_scaling_after_timeout": (
                config.limits.stop_scaling_after_timeout
            ),
            "timeout_semantics": "right-censored with configurable timeout skip scopes",
        },
    }


def _resource_summary(prepared, responses):
    """Collect observed replica resources; missing telemetry is never zero."""
    phases=[*prepared.values(),*responses.values()]
    def total(field):
        values=[item.get(field) for item in phases]
        return sum(float(v) for v in values) if values and all(v is not None for v in values) else None
    peaks=[float(item['peak_rss_kib']) for item in phases if item.get('peak_rss_kib') is not None]
    current={url:item.get('current_rss_kib') for url,item in prepared.items()}
    before=sum(float(v) for v in current.values()) if current and all(v is not None for v in current.values()) else None
    current.update({url:item.get('current_rss_kib') for url,item in responses.items()})
    after=sum(float(v) for v in current.values()) if current and all(v is not None for v in current.values()) else None
    return {'total_process_cpu_ms':total('process_cpu_ms'),
            'max_node_peak_rss_kib':max(peaks) if len(peaks)==len(phases) and peaks else None,
            'max_sum_node_current_rss_kib':max(before,after) if before is not None and after is not None else None,
            'disk_read_bytes':total('disk_read_bytes'),'disk_write_bytes':total('disk_write_bytes'),
            'request_bytes':total('request_bytes'),'response_bytes':total('response_bytes')}


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
        **native_resources(prepared),
        **_resource_summary(prepared, responses),
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
    inventory: Path | Topology,
    output_root: Path,
    topology_name: str = "physical",
) -> Path:
    return _run_physical(config, inventory, output_root, topology_name, "cumulative")


def run_physical_scalability(
    config: BenchmarkConfig,
    inventory: Path | Topology,
    output_root: Path,
    topology_name: str = "physical",
) -> Path:
    return _run_physical(config, inventory, output_root, topology_name, "scalability")


def _run_physical(config, *args, **kwargs):
    from .budget import execution_policy
    with execution_policy(unlimited_execution() or config.limits.timeout_mode == "unlimited"):
        return _run_physical_impl(config, *args, **kwargs)


def _run_physical_impl(config, inventory, output_root, topology_name, suite):
    declared = (
        load_physical_inventory(inventory, topology_name=topology_name)
        if isinstance(inventory, Path)
        else None
    )
    topology = inventory if isinstance(inventory, Topology) else declared.topology
    target = topology.kind if topology is not None else "physical"
    declared_nodes = topology.active_nodes if topology is not None else declared.nodes
    endpoint_urls = [node.endpoint for node in declared_nodes]
    endpoints = discover(
        endpoint_urls,
        declared_nodes,
        topology.fingerprint if topology is not None else None,
    )
    node_count = len(endpoints)
    endpoint_by_url = {endpoint.url: endpoint for endpoint in endpoints}
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    details: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    skips = TimeoutSkipState(config.limits)
    cumulative = suite == "cumulative"
    for users in ((0,) if cumulative else config.scale_users):
        for reasoner in config.reasoners:
            calibration_data = None
            calibration_repetition = None
            for repetition in range(1, config.repetitions + 1):
                prepared_data = None
                stages = enumerate(config.category_order, 1) if cumulative else [(0, None)]
                for stage, category in stages:
                    active_specs = (
                        by_categories(specs, set(config.category_order[:stage]))
                        if cumulative else specs
                    )
                    common = {"reasoner": reasoner, "repetition": repetition,
                              "calibration_reused": calibration_data is not None}
                    if cumulative:
                        common.update(stage=stage, added_category=category)
                    else:
                        common.update(synthetic_users=users, synthetic_triples="")
                    stop_reason = skips.skipped(reasoner, users, repetition, stage)
                    if stop_reason is not None:
                        _append_failure(
                            details, summaries, assignments, nodes, common,
                            node_count, len(active_specs), "skipped_after_timeout",
                            "early-stop", stop_reason, config.limits.point_timeout_seconds,
                        )
                        print(f"[{target}-{suite}] reasoner={reasoner} users={users} "
                              f"repetition={repetition} stage={stage} status=skipped_after_timeout", flush=True)
                        continue
                    phase = "calibration-prepare"
                    started = monotonic()
                    timeout_seconds = config.limits.phase_timeout_seconds
                    print(f"[{target}-{suite}] reasoner={reasoner} users={users} "
                          f"repetition={repetition} stage={stage} status=running", flush=True)
                    try:
                        if calibration_data is None:
                            _prepare(config, endpoints, reasoner, users, config.seed)
                            phase = "calibration"
                            calibration_data = _calibrate(config, endpoints, specs)
                            calibration_repetition = repetition
                        calibration_ms, calibration, calibration_responses = calibration_data
                        phase = "prepare"
                        started = monotonic()
                        timeout_seconds = config.limits.point_timeout_seconds
                        if prepared_data is None:
                            prepared_data = _prepare(config, endpoints, reasoner, users, config.seed)
                        prepare_wall_ms, prepared = prepared_data
                        assignment, predicted = balanced_assignment(active_specs, endpoints, calibration)
                        phase = "queries"
                        query_started = monotonic()
                        # Preparation is shared by cumulative stages; charge it to each point.
                        budget = timeout_seconds - prepare_wall_ms / 1000
                        if budget <= 0 and not unlimited_execution():
                            raise PhaseBudgetTimeout("preparation exhausted the point budget")
                        query_wall_ms, responses = _query(
                            config, endpoints, assignment, timeout_seconds=max(budget, 0.001),
                            phase="physical-balanced-queries",
                        )
                    except Exception as error:
                        if not is_timeout_failure(error):
                            raise
                        skips.timeout(reasoner, users, repetition, stage, error)
                        elapsed = monotonic() - started
                        if phase == "queries":
                            elapsed = prepare_wall_ms / 1000 + monotonic() - query_started
                        _append_failure(
                            details, summaries, assignments, nodes, common,
                            node_count, len(active_specs), "timeout", phase,
                            error_text(error), timeout_seconds, elapsed,
                        )
                        print(f"[{target}-{suite}] reasoner={reasoner} phase={phase} status=timeout", flush=True)
                        continue
                    skips.completed(reasoner)
                    if not cumulative:
                        common["synthetic_triples"] = next(iter(prepared.values()))["synthetic_triples"]
                    common["calibration_reused"] = True
                    details.extend(_detail_rows(responses, endpoint_by_url, common))
                    assignments.extend(_assignment_rows(suite, common, endpoints, assignment, calibration, predicted))
                    nodes.extend(_node_rows(suite, common, endpoints, prepared, calibration_responses, responses, predicted))
                    summary = _summary(
                        common, len(active_specs), prepare_wall_ms,
                        calibration_ms if repetition == calibration_repetition else 0.0,
                        query_wall_ms, prepared, responses, predicted, True,
                    )
                    if not cumulative:
                        summary["node_generation_ms_sum"] = sum(float(item["generation_ms"]) for item in prepared.values())
                    summaries.append(summary)
                    print(f"[{target}-{suite}] reasoner={reasoner} stage={stage} status=done "
                          f"wall_ms={summary['total_wall_ms']:.2f}", flush=True)
    output = output_root / suite
    _write_csv(output / "query-runs.csv", details)
    _write_csv(output / "summary.csv", summaries)
    _write_csv(output / "assignments.csv", assignments)
    _write_csv(output / "node-runs.csv", nodes)
    metadata = _metadata(config, endpoints, suite, inventory)
    metadata["category_order" if cumulative else "scale_users"] = list(config.category_order if cumulative else config.scale_users)
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    completed = sum(row.get("status") == "completed" for row in summaries)
    censored = sum(row.get("status") == "timeout" for row in summaries)
    skipped = sum(row.get("status") == "skipped_after_timeout" for row in summaries)
    print(f"[{target}-{suite}] status=completed completed_points={completed} "
          f"timeout_points={censored} skipped_points={skipped} output={output}", flush=True)
    return output
