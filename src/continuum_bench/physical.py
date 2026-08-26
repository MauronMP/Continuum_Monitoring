"""Balanced benchmarks for one cloud host and four physical Raspberry Pi nodes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import platform
import tomllib
from typing import Any

from .config import BenchmarkConfig
from .distributed import (
    DISTRIBUTED_REQUEST_RETRIES,
    DISTRIBUTED_REQUEST_TIMEOUT_SECONDS,
    Endpoint,
    _detail_rows,
    _parallel,
    _prepare,
    _query,
    _write_csv,
    discover,
)
from .queries import QuerySpec, by_categories, load_catalog


def inventory_endpoints(path: Path) -> list[str]:
    """Load and validate the five HTTP endpoints from a physical inventory."""
    with path.open("rb") as handle:
        document = tomllib.load(handle)
    nodes = document.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError(f"Inventory must contain [[nodes]] entries: {path}")
    roles: set[str] = set()
    endpoints: list[str] = []
    for node in nodes:
        role = str(node.get("role", "")).strip()
        endpoint = str(node.get("endpoint", "")).strip().rstrip("/")
        if not role or not endpoint:
            raise ValueError("Every physical node requires role and endpoint")
        if role in roles:
            raise ValueError(f"Duplicate physical role: {role}")
        roles.add(role)
        endpoints.append(endpoint)
    expected = {"cloud", "fog", "edge1", "edge2", "edge3"}
    if roles != expected:
        raise ValueError(
            f"Physical inventory roles must be {sorted(expected)}, "
            f"got {sorted(roles)}"
        )
    return endpoints


def _calibrate(
    endpoints: list[Endpoint],
    specs: list[QuerySpec],
) -> tuple[
    float,
    dict[str, dict[str, dict[str, float]]],
    dict[str, dict[str, Any]],
]:
    """Measure every query on every node outside the timed experiment."""
    payload = {"query_ids": [spec.id for spec in specs]}
    wall_ms, responses = _parallel(
        endpoints,
        "/queries",
        {endpoint.url: payload for endpoint in endpoints},
        phase="calibration",
    )
    costs: dict[str, dict[str, dict[str, float]]] = {}
    for endpoint in endpoints:
        measurements = responses[endpoint.url]["measurements"]
        costs[endpoint.url] = {
            str(item["query_id"]): {
                "duration_ms": max(float(item["duration_ms"]), 0.001)
            }
            for item in measurements
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
                    "query_id": spec.id,
                    "category": spec.category,
                    "tier": spec.tier,
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
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "suite": suite,
        "mode": "physical-five-node-adaptive-lpt",
        "inventory": str(inventory.resolve()),
        "endpoints": [
            {"url": endpoint.url, "role": endpoint.role}
            for endpoint in endpoints
        ],
        "reasoners": list(config.reasoners),
        "repetitions": config.repetitions,
        "seed": config.seed,
        "replica_count": len(endpoints),
        "balancing": (
            "one unmeasured per-query calibration per reasoner and dataset "
            "on every node, reused across repetitions, followed by "
            "heterogeneous longest-processing-time greedy scheduling"
        ),
        "calibration_in_timed_total": False,
        "calibration_prepare_in_timed_total": False,
        "calibration_reused_across_repetitions": True,
        "transport": {
            "timeout_seconds": DISTRIBUTED_REQUEST_TIMEOUT_SECONDS,
            "retries": DISTRIBUTED_REQUEST_RETRIES,
            "retry_delay_in_phase_wall_time": True,
            "retry_counts_in_summary_and_node_runs": True,
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
        "query_count": query_count,
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


def run_physical_cumulative(
    config: BenchmarkConfig,
    inventory: Path,
    output_root: Path,
) -> Path:
    endpoints = discover(inventory_endpoints(inventory))
    endpoint_by_url = {endpoint.url: endpoint for endpoint in endpoints}
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    details: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []

    for reasoner in config.reasoners:
        print(
            f"[physical-cumulative] reasoner={reasoner} "
            "phase=calibration-prepare nodes=5 status=running",
            flush=True,
        )
        _prepare(endpoints, reasoner, 0, config.seed)
        print(
            f"[physical-cumulative] reasoner={reasoner} "
            f"phase=calibration nodes=5 queries={len(specs)} status=running",
            flush=True,
        )
        (
            calibration_ms,
            calibration,
            calibration_responses,
        ) = _calibrate(endpoints, specs)
        for repetition in range(1, config.repetitions + 1):
            print(
                f"[physical-cumulative] reasoner={reasoner} "
                f"repetition={repetition}/{config.repetitions} "
                "nodes=5 phase=prepare status=running",
                flush=True,
            )
            prepare_wall_ms, prepared = _prepare(
                endpoints, reasoner, 0, config.seed
            )
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
                query_wall_ms, responses = _query(endpoints, assignment)
                common = {
                    "reasoner": reasoner,
                    "repetition": repetition,
                    "stage": stage,
                    "added_category": category,
                    "calibration_reused": True,
                }
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
) -> Path:
    endpoints = discover(inventory_endpoints(inventory))
    endpoint_by_url = {endpoint.url: endpoint for endpoint in endpoints}
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    details: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []

    for block, users in enumerate(config.scale_users, start=1):
        for reasoner in config.reasoners:
            print(
                f"[physical-scalability] block={block}/"
                f"{len(config.scale_users)} users={users} "
                f"reasoner={reasoner} phase=calibration-prepare "
                "nodes=5 status=running",
                flush=True,
            )
            _prepare(endpoints, reasoner, users, config.seed)
            print(
                f"[physical-scalability] block={block}/"
                f"{len(config.scale_users)} users={users} "
                f"reasoner={reasoner} phase=calibration "
                f"nodes=5 queries={len(specs)} status=running",
                flush=True,
            )
            (
                calibration_ms,
                calibration,
                calibration_responses,
            ) = _calibrate(endpoints, specs)
            for repetition in range(1, config.repetitions + 1):
                print(
                    f"[physical-scalability] block={block}/"
                    f"{len(config.scale_users)} users={users} "
                    f"reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    "nodes=5 phase=prepare status=running",
                    flush=True,
                )
                prepare_wall_ms, prepared = _prepare(
                    endpoints, reasoner, users, config.seed
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
                query_wall_ms, responses = _query(endpoints, assignment)
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
