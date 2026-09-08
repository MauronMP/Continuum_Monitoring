from __future__ import annotations

import csv
from pathlib import Path
import statistics
from typing import Any

from ..csv_utils import write_dict_rows
from ..queries import load_catalog
from ..config import BenchmarkConfig
from .sparql import characterize_query


def analyze_category_costs(
    config: BenchmarkConfig,
    events_path: Path,
    output_dir: Path,
) -> list[Path]:
    """Aggregate request-level observations by category, policy and query."""

    specs = {
        spec.id: spec
        for spec in load_catalog(config.resolve(config.query_catalog), config.root)
    }
    features = {
        query_id: characterize_query(spec)
        for query_id, spec in specs.items()
    }
    with events_path.open(encoding="utf-8", newline="") as handle:
        events = list(csv.DictReader(handle))
    enriched = []
    for row in events:
        query_id = row.get("query_id", "")
        spec = specs.get(query_id)
        if spec is None:
            continue
        enriched.append(
            {
                **row,
                "category": spec.category,
                "policies": spec.policies,
                "structural_complexity": features[
                    query_id
                ].structural_complexity,
            }
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    category_path = output_dir / "category-cost-summary.csv"
    policy_path = output_dir / "policy-cost-summary.csv"
    query_path = output_dir / "query-cost-summary.csv"
    write_dict_rows(
        category_path,
        _aggregate(enriched, "category"),
        empty_message="No category cost rows",
    )
    write_dict_rows(
        policy_path,
        _aggregate_by_policy(enriched),
        empty_message="No policy cost rows",
    )
    write_dict_rows(
        query_path,
        _aggregate(enriched, "query_id"),
        empty_message="No query cost rows",
    )
    return [category_path, policy_path, query_path]


def _aggregate(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    keys = sorted({row[field] for row in rows})
    total_equivalents = sum(
        float(row.get("attribution_fraction", 1.0)) for row in rows
    )
    return [
        _summary(
            key,
            [row for row in rows if row[field] == key],
            field,
            total_equivalents,
        )
        for key in keys
    ]


def _aggregate_by_policy(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    policy_rows = []
    for row in rows:
        policies = row["policies"] or ("",)
        attribution_fraction = 1.0 / len(policies)
        for policy in policies:
            policy_rows.append(
                {
                    **row,
                    "policy_id": policy,
                    "attribution_fraction": attribution_fraction,
                }
            )
    return _aggregate(policy_rows, "policy_id")


def _summary(
    key: str,
    rows: list[dict[str, Any]],
    field: str,
    total_requests: float,
) -> dict[str, Any]:
    completed = [
        row for row in rows
        if str(row.get("processed", "")).lower() in {"true", "1"}
        or row.get("lost_reason", "") == ""
    ]
    latencies = _numbers(completed, "latency_ms")
    engine = _numbers(completed, "engine_duration_ms")
    additive_resource_fields = (
        "reasoning_ms",
        "process_cpu_ms",
        "disk_read_bytes",
        "disk_write_bytes",
        "network_rx_bytes",
        "network_tx_bytes",
        "request_bytes",
        "response_bytes",
    )
    stock_resource_fields = ("current_rss_kib", "peak_rss_kib")
    resource_fields = (*additive_resource_fields, *stock_resource_fields)
    complexity = [float(row["structural_complexity"]) for row in rows]
    attributed_requests = sum(
        float(row.get("attribution_fraction", 1.0)) for row in rows
    )
    attributed_completed = sum(
        float(row.get("attribution_fraction", 1.0)) for row in completed
    )
    return {
        field: key,
        "requests": len(rows),
        "attributed_request_equivalents": attributed_requests,
        "popularity_share": (
            attributed_requests / total_requests if total_requests else 0.0
        ),
        "completed_requests": len(completed),
        "error_or_loss_requests": len(rows) - len(completed),
        "attributed_completed_equivalents": attributed_completed,
        "attributed_error_or_loss_equivalents": (
            attributed_requests - attributed_completed
        ),
        "completion_rate": (
            attributed_completed / attributed_requests
            if attributed_requests
            else 0.0
        ),
        "latency_p50_ms": _percentile(latencies, 50),
        "latency_p90_ms": _percentile(latencies, 90),
        "latency_p95_ms": _percentile(latencies, 95),
        "latency_p99_ms": _percentile(latencies, 99),
        "mean_query_execution_ms": statistics.mean(engine) if engine else "",
        "mean_structural_complexity": statistics.mean(complexity)
        if complexity
        else "",
        "total_impact_latency_ms": sum(
            float(row.get("latency_ms", 0) or 0)
            * float(row.get("attribution_fraction", 1.0))
            for row in completed
        ),
        **{
            f"mean_{name}": (
                _weighted_mean(completed, name) if values else ""
            )
            for name in resource_fields
            for values in [_numbers(completed, name)]
        },
        **{
            f"max_{name}": max(values) if values else ""
            for name in stock_resource_fields
            for values in [_numbers(completed, name)]
        },
        **{
            f"total_{name}": (
                sum(
                    float(row.get(name, 0) or 0)
                    * float(row.get("attribution_fraction", 1.0))
                    for row in completed
                )
                if values
                else ""
            )
            for name in additive_resource_fields
            for values in [_numbers(completed, name)]
        },
    }


def _numbers(rows: list[dict[str, Any]], field: str) -> list[float]:
    values = []
    for row in rows:
        value = row.get(field, "")
        if value not in {"", None}:
            values.append(float(value))
    return values


def _weighted_mean(rows: list[dict[str, Any]], field: str) -> float | str:
    weighted = [
        (
            float(row[field]),
            float(row.get("attribution_fraction", 1.0)),
        )
        for row in rows
        if row.get(field, "") not in {"", None}
    ]
    total_weight = sum(weight for _, weight in weighted)
    if not weighted or total_weight == 0:
        return ""
    return sum(value * weight for value, weight in weighted) / total_weight


def _percentile(values: list[float], percentile: int) -> float | str:
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=100, method="inclusive")[percentile - 1]
