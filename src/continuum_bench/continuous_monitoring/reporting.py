from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

import matplotlib.pyplot as plt
import numpy as np


def _percentile(values: list[float], value: int):
    return float(np.percentile(values, value)) if values else None


def _difference(active: dict, idle: dict | None, field: str):
    if not idle or active.get(field) is None or idle.get(field) is None:
        return None
    return active[field] - idle[field]


def _write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _resource_metrics(samples: list[dict], duration: float) -> tuple[dict, list[dict]]:
    hours = duration / 3600
    host_rows = []
    for host in sorted({str(row["host"]) for row in samples if "host" in row}):
        rows = [row for row in samples if row.get("host") == host and "cpu_percent" in row]
        cpu = [float(row["cpu_percent"]) for row in rows]
        memory = [float(row["memory_bytes"]) for row in rows if row.get("memory_bytes") is not None]
        counters = {}
        for key in ("cpu_usage_seconds", "network_rx_bytes", "network_tx_bytes"):
            values = [float(row[key]) for row in rows if row.get(key) is not None]
            counters[key] = max(values) - min(values) if values else 0.0
        host_rows.append(
            {
                "host": host,
                "cpu_mean": float(np.mean(cpu)) if cpu else None,
                "cpu_p95": _percentile(cpu, 95),
                "cpu_peak": max(cpu) if cpu else None,
                "cpu_seconds": counters["cpu_usage_seconds"],
                "cpu_seconds_per_hour": counters["cpu_usage_seconds"] / hours,
                "memory_mean": float(np.mean(memory)) if memory else None,
                "memory_p95": _percentile(memory, 95),
                "memory_peak": max(memory) if memory else None,
                "network_rx_mib_per_hour": counters["network_rx_bytes"] / 1024**2 / hours,
                "network_tx_mib_per_hour": counters["network_tx_bytes"] / 1024**2 / hours,
                "pids_peak": max((int(row.get("pids", 0)) for row in rows), default=0),
            }
        )
    cpu = [float(row["cpu_percent"]) for row in samples if "cpu_percent" in row]
    memory = [float(row["memory_bytes"]) for row in samples if row.get("memory_bytes") is not None]
    return (
        {
            "cpu_mean": float(np.mean(cpu)) if cpu else None,
            "cpu_p95": _percentile(cpu, 95),
            "cpu_peak": max(cpu) if cpu else None,
            "cpu_seconds_per_hour": sum(row["cpu_seconds_per_hour"] for row in host_rows),
            "memory_mean": float(np.mean(memory)) if memory else None,
            "memory_p95": _percentile(memory, 95),
            "memory_peak": max(memory) if memory else None,
            "network_rx_mib_per_hour": sum(row["network_rx_mib_per_hour"] for row in host_rows),
            "network_tx_mib_per_hour": sum(row["network_tx_mib_per_hour"] for row in host_rows),
        },
        host_rows,
    )


def _plot(summary: list[dict], figures: Path, field: str, filename: str, title: str, ylabel: str) -> None:
    keys = []
    for row in summary:
        key = (row["scenario"], row["layout"])
        if key not in keys:
            keys.append(key)
    levels = []
    for row in summary:
        if row["demand_level"] not in levels:
            levels.append(row["demand_level"])
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    x = np.arange(len(levels))
    for scenario, layout in keys:
        by_level = {
            row["demand_level"]: row for row in summary if row["scenario"] == scenario and row["layout"] == layout
        }
        values = [by_level.get(level, {}).get(field, np.nan) for level in levels]
        ax.plot(x, values, marker="o", label=f"{scenario} · {layout}")
    ax.set_xticks(x, levels)
    ax.set_title(title, fontweight="normal")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25)
    if keys:
        ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(figures / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_multi(
    summary: list[dict], figures: Path, fields: tuple[tuple[str, str], ...], filename: str, title: str, ylabel: str
) -> None:
    keys = list(dict.fromkeys((row["scenario"], row["layout"]) for row in summary))
    levels = list(dict.fromkeys(row["demand_level"] for row in summary))
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    x = np.arange(len(levels))
    styles = ("-", "--", ":")
    for scenario, layout in keys:
        by_level = {
            row["demand_level"]: row for row in summary if row["scenario"] == scenario and row["layout"] == layout
        }
        for index, (field, label) in enumerate(fields):
            values = [by_level.get(level, {}).get(field, np.nan) for level in levels]
            ax.plot(x, values, marker="o", linestyle=styles[index], label=f"{scenario} · {layout} · {label}")
    ax.set_xticks(x, levels)
    ax.set_title(title, fontweight="normal")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25)
    if keys:
        ax.legend(frameon=False, fontsize=6.5)
    fig.tight_layout()
    fig.savefig(figures / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)


def report(run_dir: Path) -> Path:
    summary_dir = run_dir / "summary"
    figures = run_dir / "figures"
    summary_dir.mkdir(exist_ok=True)
    figures.mkdir(exist_ok=True)
    for path in figures.glob("*.png"):
        path.unlink()
    repetitions, host_rows, task_rows = [], [], []
    for result_path in run_dir.glob("users-*/*/*/rep-*/result.json"):
        result = json.loads(result_path.read_text())
        if result.get("status") != "completed":
            continue
        samples_path = result_path.with_name("resource_samples.jsonl")
        samples = [json.loads(line) for line in samples_path.read_text().splitlines()] if samples_path.is_file() else []
        resources, hosts = _resource_metrics(samples, float(result["measurement_seconds"]))
        events_path = result_path.with_name("scheduler_events.jsonl")
        events = [json.loads(line) for line in events_path.read_text().splitlines()] if events_path.is_file() else []
        executed = [event for event in events if not event.get("missed_cycle")]
        lags = [float(event["schedule_lag_seconds"]) for event in executed]
        logical_path = result_path.with_name("logical_queries.jsonl")
        logical = [json.loads(line) for line in logical_path.read_text().splitlines()] if logical_path.is_file() else []
        latencies = [float(row["logical_duration_ms"]) for row in logical if row.get("status") == "completed"]
        hours = float(result["measurement_seconds"]) / 3600
        row = (
            result
            | resources
            | {
                "monitoring_compliance_percent": (
                    float(result["monitoring_compliance"]) * 100
                    if result.get("monitoring_compliance") is not None
                    else None
                ),
                "schedule_lag_p50": _percentile(lags, 50),
                "schedule_lag_p95": _percentile(lags, 95),
                "schedule_lag_max": max(lags) if lags else None,
                "logical_latency_p50": _percentile(latencies, 50),
                "logical_latency_p95": _percentile(latencies, 95),
                "logical_latency_p99": _percentile(latencies, 99),
                "logical_cycles_per_hour": int(result["scheduled_cycles"]) / hours,
                "logical_queries_per_hour": int(result["logical_queries"]) / hours,
                "physical_requests_per_hour": int(result["physical_requests"]) / hours,
            }
        )
        repetitions.append(row)
        context = {key: result[key] for key in ("scenario", "layout", "demand_level", "repetition")}
        host_rows.extend(context | host for host in hosts)
        by_task: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for event in events:
            by_task[(event["task_id"], event["policy_id"])].append(event)
        for (task_id, policy_id), task_events in by_task.items():
            on_time = sum(event["status"] == "completed_on_time" for event in task_events)
            task_rows.append(
                context
                | {
                    "task_id": task_id,
                    "policy_id": policy_id,
                    "scheduled_cycles": len(task_events),
                    "completed_on_time": on_time,
                    "monitoring_compliance_percent": 100 * on_time / len(task_events),
                }
            )
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in repetitions:
        grouped[(row["scenario"], row["layout"], row["demand_level"])].append(row)
    summary = []
    numeric = (
        "monitoring_compliance_percent",
        "scheduled_cycles",
        "completed_on_time",
        "completed_late",
        "missed_cycles",
        "logical_timeouts",
        "semantic_failures",
        "physical_failures",
        "scheduler_busy_seconds",
        "scheduler_idle_seconds",
        "scheduler_utilization",
        "max_pending_monitoring_tasks",
        "schedule_lag_p50",
        "schedule_lag_p95",
        "schedule_lag_max",
        "logical_latency_p50",
        "logical_latency_p95",
        "logical_latency_p99",
        "cpu_mean",
        "cpu_p95",
        "cpu_peak",
        "cpu_seconds_per_hour",
        "memory_mean",
        "memory_p95",
        "memory_peak",
        "network_rx_mib_per_hour",
        "network_tx_mib_per_hour",
        "logical_cycles_per_hour",
        "logical_queries_per_hour",
        "physical_requests_per_hour",
    )
    for key, rows in grouped.items():
        item = {"scenario": key[0], "layout": key[1], "demand_level": key[2], "repetitions": len(rows)}
        for field in numeric:
            values = [float(row[field]) for row in rows if row.get(field) is not None]
            item[field] = median(values) if values else None
        scheduled_total = sum(int(row["scheduled_cycles"]) for row in rows)
        item["monitoring_compliance_percent"] = (
            100 * sum(int(row["completed_on_time"]) for row in rows) / scheduled_total if scheduled_total else None
        )
        summary.append(item)
    idle_active = []
    for row in summary:
        idle = next(
            (
                candidate
                for candidate in summary
                if candidate["scenario"] == row["scenario"]
                and candidate["layout"] == row["layout"]
                and candidate["demand_level"] == "idle"
            ),
            None,
        )

        idle_active.append(
            row
            | {
                "incremental_cpu_seconds_per_hour": _difference(row, idle, "cpu_seconds_per_hour"),
                "descriptive_memory_mean_difference": _difference(row, idle, "memory_mean"),
                "incremental_network_rx_mib_per_hour": _difference(row, idle, "network_rx_mib_per_hour"),
                "incremental_network_tx_mib_per_hour": _difference(row, idle, "network_tx_mib_per_hour"),
            }
        )
    _write_csv(summary_dir / "repetitions.csv", repetitions)
    _write_csv(summary_dir / "summary.csv", summary)
    _write_csv(summary_dir / "host_summary.csv", host_rows)
    _write_csv(summary_dir / "task_policy_summary.csv", task_rows)
    _write_csv(summary_dir / "idle_vs_active.csv", idle_active)
    plots = (
        ("cpu_seconds_per_hour", "01_cpu_seconds_per_hour.png", "Recurring CPU cost", "CPU-seconds/hour"),
        ("monitoring_compliance_percent", "04_compliance.png", "Policy monitoring compliance", "%"),
        ("scheduler_utilization", "06_scheduler_utilization.png", "Scheduler utilization", "Ratio"),
    )
    for field, filename, title, ylabel in plots:
        _plot(summary, figures, field, filename, title, ylabel)
    _plot_multi(
        summary,
        figures,
        (("memory_mean", "mean"), ("memory_p95", "p95")),
        "02_memory_by_demand.png",
        "Container memory by demand level",
        "Bytes",
    )
    _plot_multi(
        summary,
        figures,
        (("network_rx_mib_per_hour", "RX"), ("network_tx_mib_per_hour", "TX")),
        "03_network_by_demand.png",
        "Network traffic by demand level",
        "MiB/hour",
    )
    _plot_multi(
        summary,
        figures,
        (("schedule_lag_p50", "p50"), ("schedule_lag_p95", "p95")),
        "05_schedule_lag.png",
        "Schedule lag by demand level",
        "Seconds",
    )
    _plot_multi(
        summary,
        figures,
        (
            ("logical_latency_p50", "p50"),
            ("logical_latency_p95", "p95"),
            ("logical_latency_p99", "p99"),
        ),
        "07_logical_latency.png",
        "Logical query latency by demand level",
        "Milliseconds",
    )
    (summary_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (figures / "manifest.json").write_text(
        json.dumps({"figure_count": 7, "figures": sorted(path.name for path in figures.glob("*.png"))}, indent=2) + "\n"
    )
    return summary_dir
