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
    hours = duration / 3600 if duration > 0 else None
    host_rows = []
    for host in sorted({str(row["host"]) for row in samples if "host" in row}):
        rows = [row for row in samples if row.get("host") == host and "cpu_percent" in row]
        cpu = [float(row["cpu_percent"]) for row in rows]
        memory = [float(row["memory_bytes"]) for row in rows if row.get("memory_bytes") is not None]
        counters: dict[str, float | None] = {}
        for key in ("cpu_usage_seconds", "network_rx_bytes", "network_tx_bytes"):
            values = [float(row[key]) for row in rows if row.get(key) is not None]
            counters[key] = max(values) - min(values) if len(values) >= 2 else None
        cpu_seconds = counters["cpu_usage_seconds"]
        network_rx = counters["network_rx_bytes"]
        network_tx = counters["network_tx_bytes"]
        host_rows.append(
            {
                "host": host,
                "cpu_mean": float(np.mean(cpu)) if cpu else None,
                "cpu_p95": _percentile(cpu, 95),
                "cpu_peak": max(cpu) if cpu else None,
                "cpu_seconds": cpu_seconds,
                "cpu_seconds_per_hour": cpu_seconds / hours if hours and cpu_seconds is not None else None,
                "memory_mean": float(np.mean(memory)) if memory else None,
                "memory_p95": _percentile(memory, 95),
                "memory_peak": max(memory) if memory else None,
                "network_rx_mib_per_hour": network_rx / 1024**2 / hours if hours and network_rx is not None else None,
                "network_tx_mib_per_hour": network_tx / 1024**2 / hours if hours and network_tx is not None else None,
                "pids_peak": max((int(row.get("pids", 0)) for row in rows), default=0),
            }
        )
    cpu = [float(row["cpu_percent"]) for row in samples if "cpu_percent" in row]
    worker_memory = [float(row["memory_bytes"]) for row in samples if row.get("memory_bytes") is not None]
    hosts = sorted({str(row["host"]) for row in samples if "host" in row})
    series = {
        host: sorted((row for row in samples if row.get("host") == host), key=lambda row: row.get("timestamp", ""))
        for host in hosts
    }
    infrastructure_memory = []
    for index in range(min((len(rows) for rows in series.values()), default=0)):
        values = [series[host][index].get("memory_bytes") for host in hosts]
        if all(value is not None for value in values):
            infrastructure_memory.append(sum(float(value) for value in values))

    def observed_sum(field: str) -> float | None:
        values = [float(row[field]) for row in host_rows if row.get(field) is not None]
        return sum(values) if values else None

    return (
        {
            "cpu_mean": float(np.mean(cpu)) if cpu else None,
            "cpu_p95": _percentile(cpu, 95),
            "cpu_peak": max(cpu) if cpu else None,
            "cpu_seconds_per_hour": observed_sum("cpu_seconds_per_hour"),
            "worker_memory_mean": float(np.mean(worker_memory)) if worker_memory else None,
            "worker_memory_p95": _percentile(worker_memory, 95),
            "worker_memory_peak": max(worker_memory) if worker_memory else None,
            "infrastructure_memory_mean": (float(np.mean(infrastructure_memory)) if infrastructure_memory else None),
            "infrastructure_memory_p95": _percentile(infrastructure_memory, 95),
            "infrastructure_memory_peak": max(infrastructure_memory) if infrastructure_memory else None,
            "network_rx_mib_per_hour": observed_sum("network_rx_mib_per_hour"),
            "network_tx_mib_per_hour": observed_sum("network_tx_mib_per_hour"),
            "resource_hosts_total": len(hosts),
            "cpu_telemetry_hosts": sum(row.get("cpu_seconds_per_hour") is not None for row in host_rows),
            "memory_telemetry_hosts": sum(row.get("memory_peak") is not None for row in host_rows),
            "network_telemetry_hosts": sum(
                row.get("network_rx_mib_per_hour") is not None and row.get("network_tx_mib_per_hour") is not None
                for row in host_rows
            ),
        },
        host_rows,
    )


DEMAND_ORDER = ("idle", "low", "normal", "high", "critical")


def _ordered_levels(rows: list[dict]) -> list[str]:
    present = {str(row["demand_level"]) for row in rows}
    return [level for level in DEMAND_ORDER if level in present] + sorted(present - set(DEMAND_ORDER))


def _median_or_nan(values: list[float]) -> float:
    return float(median(values)) if values else float("nan")


def _format_cell(value: float, specification: str) -> str:
    if not np.isfinite(value):
        return "N/A"
    return format(value, specification)


def _matrix_plot(
    values: np.ndarray,
    row_labels: list[str],
    column_labels: list[str],
    figures: Path,
    filename: str,
    title: str,
    *,
    formats: list[str] | None = None,
    row_normalized: bool = False,
    color_label: str = "Value",
    cmap: str = "YlGnBu",
) -> None:
    raw = np.asarray(values, dtype=float)
    display = raw.copy()
    if row_normalized:
        for index, row in enumerate(raw):
            finite = row[np.isfinite(row)]
            if finite.size:
                minimum, maximum = float(np.min(finite)), float(np.max(finite))
                display[index] = (row - minimum) / (maximum - minimum) if maximum > minimum else 0.5
        color_label = "Relative magnitude within each metric"
    masked = np.ma.masked_invalid(display)
    palette = plt.get_cmap(cmap).with_extremes(bad="#e6e6e6")
    height = max(3.3, 0.48 * len(row_labels) + 1.7)
    width = max(6.2, 1.2 * len(column_labels) + 2.8)
    fig, ax = plt.subplots(figsize=(width, height))
    image = ax.imshow(masked, aspect="auto", cmap=palette, interpolation="nearest")
    ax.set_xticks(np.arange(len(column_labels)), [label.title() for label in column_labels])
    ax.set_yticks(np.arange(len(row_labels)), row_labels)
    ax.set_title(title, fontweight="normal", pad=12)
    ax.tick_params(axis="both", length=0)
    ax.set_xticks(np.arange(-0.5, len(column_labels), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(row_labels), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.5)
    ax.tick_params(which="minor", bottom=False, left=False)
    formats = formats or [".2f"] * len(row_labels)
    threshold = np.nanmedian(display) if np.isfinite(display).any() else 0.5
    for row_index in range(raw.shape[0]):
        for column_index in range(raw.shape[1]):
            value = raw[row_index, column_index]
            shown = display[row_index, column_index]
            color = "white" if np.isfinite(shown) and shown > threshold else "#17202a"
            ax.text(
                column_index,
                row_index,
                _format_cell(value, formats[row_index]),
                ha="center",
                va="center",
                fontsize=8,
                color=color,
            )
    colorbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.03)
    colorbar.set_label(color_label, fontsize=8)
    if row_normalized:
        colorbar.set_ticks((0, 0.5, 1))
        colorbar.set_ticklabels(("row min", "mid", "row max"))
    fig.tight_layout()
    fig.savefig(figures / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _summary_matrix(
    summary: list[dict],
    fields: tuple[tuple[str, str, str], ...],
    levels: list[str],
) -> tuple[np.ndarray, list[str], list[str]]:
    by_level = {str(row["demand_level"]): row for row in summary}
    values = np.asarray(
        [[by_level.get(level, {}).get(field, np.nan) for level in levels] for field, _, _ in fields], dtype=float
    )
    return values, [label for _, label, _ in fields], [specification for _, _, specification in fields]


def _host_matrix(
    host_rows: list[dict], field: str, levels: list[str], divisor: float = 1.0
) -> tuple[np.ndarray, list[str]]:
    hosts = sorted({str(row["host"]) for row in host_rows})
    values = []
    for host in hosts:
        host_values = []
        for level in levels:
            candidates = [row for row in host_rows if row["host"] == host and row["demand_level"] == level]
            samples = [float(row[field]) / divisor for row in candidates if row.get(field) is not None]
            host_values.append(_median_or_nan(samples) if len(samples) == len(candidates) else float("nan"))
        values.append(host_values)
    return np.asarray(values), hosts


def _task_matrix(task_rows: list[dict], levels: list[str]) -> tuple[np.ndarray, list[str]]:
    tasks = sorted({(str(row["task_id"]), str(row["policy_id"])) for row in task_rows})
    values = []
    for task_id, policy_id in tasks:
        row_values = []
        for level in levels:
            samples = [
                float(row["scheduled_cycles"])
                for row in task_rows
                if row["task_id"] == task_id
                and row["policy_id"] == policy_id
                and row["demand_level"] == level
                and row.get("scheduled_cycles") is not None
            ]
            row_values.append(_median_or_nan(samples))
        values.append(row_values)
    return np.asarray(values), [f"{task_id}\n({policy_id})" for task_id, policy_id in tasks]


def report(run_dir: Path) -> Path:
    summary_dir = run_dir / "summary"
    figures = run_dir / "figures"
    summary_dir.mkdir(exist_ok=True)
    figures.mkdir(exist_ok=True)
    for path in figures.glob("*.png"):
        path.unlink()
    repetitions, completed_repetitions, partial_repetitions = [], [], []
    host_rows, task_rows, failure_rows = [], [], []
    for result_path in run_dir.glob("users-*/*/*/rep-*/result.json"):
        result = json.loads(result_path.read_text())
        is_complete = result.get("status") == "completed" and not result.get("scheduler_halted", False)
        actual_value = result.get("measurement_actual_seconds")
        if actual_value is None:
            actual_value = result.get("measurement_seconds", 0.0) if result.get("status") == "completed" else 0.0
        actual_duration = float(actual_value)
        requested_duration = float(result.get("measurement_requested_seconds", result.get("measurement_seconds", 0.0)))
        completeness = "complete" if is_complete else "partial"
        if not is_complete:
            failure_rows.append(
                {
                    "scenario": result.get("scenario"),
                    "layout": result.get("layout"),
                    "demand_level": result.get("demand_level"),
                    "repetition": result.get("repetition"),
                    "status": result.get("status"),
                    "failure_reason": result.get("failure_reason") or result.get("error"),
                    "failed_task": result.get("failed_task"),
                    "failed_query": result.get("failed_query"),
                    "failed_hosts": json.dumps(result.get("failed_hosts")),
                    "measurement_requested_seconds": requested_duration,
                    "measurement_actual_seconds": actual_duration,
                    "recovery_count": result.get("recovery_count"),
                    "recovery_seconds": result.get("recovery_seconds"),
                    "worker_restart_count": result.get("worker_restart_count"),
                    "result_path": str(result_path.relative_to(run_dir)),
                }
            )
        if actual_duration <= 0 or "scheduled_cycles" not in result:
            continue
        samples_path = result_path.with_name("resource_samples.jsonl")
        samples = [json.loads(line) for line in samples_path.read_text().splitlines()] if samples_path.is_file() else []
        resources, hosts = _resource_metrics(samples, actual_duration)
        events_path = result_path.with_name("scheduler_events.jsonl")
        events = [json.loads(line) for line in events_path.read_text().splitlines()] if events_path.is_file() else []
        executed = [event for event in events if not event.get("missed_cycle")]
        lags = [float(event["schedule_lag_seconds"]) for event in executed]
        logical_path = result_path.with_name("logical_queries.jsonl")
        logical = [json.loads(line) for line in logical_path.read_text().splitlines()] if logical_path.is_file() else []
        latencies = [float(row["logical_duration_ms"]) for row in logical if row.get("status") == "completed"]
        hours = actual_duration / 3600
        row = (
            result
            | resources
            | {
                "monitoring_compliance_percent": (
                    float(result["monitoring_compliance"]) * 100
                    if result.get("monitoring_compliance") is not None
                    else None
                ),
                "measurement_completeness": completeness,
                "normalization_duration_seconds": actual_duration,
                "schedule_lag_p50": _percentile(lags, 50),
                "schedule_lag_p95": _percentile(lags, 95),
                "schedule_lag_max": max(lags) if lags else None,
                "logical_latency_p50": _percentile(latencies, 50),
                "logical_latency_p95": _percentile(latencies, 95),
                "logical_latency_p99": _percentile(latencies, 99),
                "logical_cycles_per_hour": len(executed) / hours,
                "logical_queries_per_hour": int(result["logical_queries"]) / hours,
                "physical_requests_per_hour": int(result["physical_requests"]) / hours,
            }
        )
        repetitions.append(row)
        (completed_repetitions if is_complete else partial_repetitions).append(row)
        context = {key: result[key] for key in ("scenario", "layout", "demand_level", "repetition")} | {
            "measurement_completeness": completeness
        }
        host_rows.extend(context | host for host in hosts)
        by_task: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for event in events:
            by_task[(event["task_id"], event["policy_id"])].append(event)
        for (task_id, policy_id), task_events in by_task.items():
            on_time = sum(bool(event.get("monitoring_compliant")) for event in task_events)
            task_rows.append(
                context
                | {
                    "task_id": task_id,
                    "policy_id": policy_id,
                    "scheduled_cycles": len(task_events),
                    "monitoring_compliant_cycles": on_time,
                    "monitoring_compliance_percent": 100 * on_time / len(task_events),
                    "conditions_detected": sum(
                        event.get("observation_outcome") == "condition_detected" for event in task_events
                    ),
                    "conditions_not_detected": sum(
                        event.get("observation_outcome") == "condition_not_detected" for event in task_events
                    ),
                    "observations_available": sum(
                        event.get("observation_outcome") == "observation_available" for event in task_events
                    ),
                    "expected_boolean_observations": sum(
                        event.get("observation_outcome") == "expected_boolean_observed" for event in task_events
                    ),
                    "unexpected_boolean_observations": sum(
                        event.get("observation_outcome") == "unexpected_boolean_observed" for event in task_events
                    ),
                }
            )
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in completed_repetitions:
        grouped[(row["scenario"], row["layout"], row["demand_level"])].append(row)
    summary = []
    numeric = (
        "measurement_requested_seconds",
        "measurement_actual_seconds",
        "normalization_duration_seconds",
        "monitoring_compliance_percent",
        "scheduled_cycles",
        "completed_on_time",
        "completed_late",
        "missed_cycles",
        "monitoring_compliant_cycles",
        "logical_timeouts",
        "semantic_failures",
        "physical_failures",
        "recovery_count",
        "recovery_seconds",
        "worker_restart_count",
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
        "worker_memory_mean",
        "worker_memory_p95",
        "worker_memory_peak",
        "infrastructure_memory_mean",
        "infrastructure_memory_p95",
        "infrastructure_memory_peak",
        "network_rx_mib_per_hour",
        "network_tx_mib_per_hour",
        "resource_hosts_total",
        "cpu_telemetry_hosts",
        "memory_telemetry_hosts",
        "network_telemetry_hosts",
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
            100 * sum(int(row["monitoring_compliant_cycles"]) for row in rows) / scheduled_total
            if scheduled_total
            else None
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
                "descriptive_infrastructure_memory_mean_difference": _difference(
                    row, idle, "infrastructure_memory_mean"
                ),
                "incremental_network_rx_mib_per_hour": _difference(row, idle, "network_rx_mib_per_hour"),
                "incremental_network_tx_mib_per_hour": _difference(row, idle, "network_tx_mib_per_hour"),
            }
        )
    _write_csv(summary_dir / "repetitions.csv", repetitions)
    _write_csv(summary_dir / "completed_repetitions.csv", completed_repetitions)
    _write_csv(summary_dir / "partial_repetitions.csv", partial_repetitions)
    _write_csv(summary_dir / "failures.csv", failure_rows)
    _write_csv(summary_dir / "summary.csv", summary)
    _write_csv(summary_dir / "host_summary.csv", host_rows)
    _write_csv(summary_dir / "task_policy_summary.csv", task_rows)
    _write_csv(summary_dir / "idle_vs_active.csv", idle_active)
    levels = _ordered_levels(summary)
    resource_fields = (
        ("cpu_seconds_per_hour", "Observed CPU (s/h)", ".1f"),
        ("worker_memory_peak", "Worker peak memory (MiB)", ".1f"),
        ("network_rx_mib_per_hour", "Observed network RX (MiB/h)", ".2f"),
        ("network_tx_mib_per_hour", "Observed network TX (MiB/h)", ".2f"),
        ("cpu_telemetry_hosts", "Nodes with CPU telemetry", ".0f"),
        ("memory_telemetry_hosts", "Nodes with memory telemetry", ".0f"),
    )
    resource_values, resource_labels, resource_formats = _summary_matrix(summary, resource_fields, levels)
    resource_values[1] /= 1024**2
    _matrix_plot(
        resource_values,
        resource_labels,
        levels,
        figures,
        "01_resource_overhead_matrix.png",
        "Monitoring resource overhead by demand level",
        formats=resource_formats,
        row_normalized=True,
    )

    workload_fields = (
        ("logical_cycles_per_hour", "Monitoring cycles/h", ".0f"),
        ("logical_queries_per_hour", "Logical queries/h", ".0f"),
        ("physical_requests_per_hour", "Physical requests/h", ".0f"),
        ("max_pending_monitoring_tasks", "Maximum pending tasks", ".0f"),
    )
    workload_values, workload_labels, workload_formats = _summary_matrix(summary, workload_fields, levels)
    _matrix_plot(
        workload_values,
        workload_labels,
        levels,
        figures,
        "02_workload_intensity_matrix.png",
        "Executed monitoring workload",
        formats=workload_formats,
        row_normalized=True,
    )

    cpu_values, hosts = _host_matrix(host_rows, "cpu_seconds_per_hour", levels)
    _matrix_plot(
        cpu_values,
        hosts,
        levels,
        figures,
        "03_host_cpu_matrix.png",
        "Recurring CPU cost by physical node",
        formats=[".1f"] * len(hosts),
        color_label="CPU-seconds/hour",
    )

    memory_values, hosts = _host_matrix(host_rows, "memory_peak", levels, 1024**2)
    _matrix_plot(
        memory_values,
        hosts,
        levels,
        figures,
        "04_host_memory_matrix.png",
        "Peak worker memory by physical node",
        formats=[".1f"] * len(hosts),
        color_label="MiB",
        cmap="PuBuGn",
    )

    network_rx, hosts = _host_matrix(host_rows, "network_rx_mib_per_hour", levels)
    network_tx, _ = _host_matrix(host_rows, "network_tx_mib_per_hour", levels)
    network_values = np.vstack((network_rx, network_tx))
    network_labels = [f"{host} RX" for host in hosts] + [f"{host} TX" for host in hosts]
    _matrix_plot(
        network_values,
        network_labels,
        levels,
        figures,
        "05_host_network_matrix.png",
        "Monitoring network traffic by physical node",
        formats=[".2f"] * len(network_labels),
        color_label="MiB/hour",
        cmap="YlOrRd",
    )

    quality_levels = [level for level in levels if level != "idle"]
    quality_fields = (
        ("monitoring_compliance_percent", "Compliant cycles (%)", ".1f"),
        ("scheduler_utilization", "Scheduler utilization (%)", ".2f"),
        ("schedule_lag_p95", "Schedule lag p95 (s)", ".2f"),
        ("logical_latency_p50", "Logical latency p50 (ms)", ".1f"),
        ("logical_latency_p95", "Logical latency p95 (ms)", ".1f"),
        ("logical_latency_p99", "Logical latency p99 (ms)", ".1f"),
    )
    quality_values, quality_labels, quality_formats = _summary_matrix(summary, quality_fields, quality_levels)
    quality_values[1] *= 100
    _matrix_plot(
        quality_values,
        quality_labels,
        quality_levels,
        figures,
        "06_temporal_quality_matrix.png",
        "Temporal quality and monitoring compliance",
        formats=quality_formats,
        row_normalized=True,
        cmap="BuPu",
    )

    task_values, task_labels = _task_matrix(task_rows, quality_levels)
    _matrix_plot(
        task_values,
        task_labels,
        quality_levels,
        figures,
        "07_policy_task_cycles_matrix.png",
        "Executed cycles by monitoring task and policy",
        formats=[".0f"] * len(task_labels),
        color_label="Median cycles per repetition",
        cmap="YlGn",
    )
    (summary_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (figures / "manifest.json").write_text(
        json.dumps({"figure_count": 7, "figures": sorted(path.name for path in figures.glob("*.png"))}, indent=2) + "\n"
    )
    return summary_dir
