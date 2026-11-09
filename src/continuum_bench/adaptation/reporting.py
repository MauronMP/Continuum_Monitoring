from __future__ import annotations

import copy
import csv
import json
from datetime import UTC, datetime
from math import ceil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

METRICS = (
    "logical_latency_p50_ms",
    "logical_latency_p95_ms",
    "logical_latency_p99_ms",
    "logical_timeouts",
    "monitoring_compliance",
    "schedule_lag_p50_seconds",
    "schedule_lag_p95_seconds",
    "schedule_lag_p99_seconds",
    "cpu_mean_percent",
    "cpu_peak_percent",
    "memory_mean_bytes",
    "memory_peak_bytes",
    "network_rx_bytes",
    "network_tx_bytes",
    "physical_query_executions",
    "application_queries",
    "application_completed_queries",
    "application_timeouts",
    "application_duration_seconds",
    "application_throughput_qps",
    "application_latency_p50_ms",
    "application_latency_p95_ms",
    "application_latency_p99_ms",
    "monitoring_queries",
    "monitoring_latency_p95_ms",
)

RESOURCE_METRICS = (
    "cpu_mean_percent",
    "cpu_peak_percent",
    "memory_mean_bytes",
    "memory_peak_bytes",
    "network_rx_bytes",
    "network_tx_bytes",
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text())


def _jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _digests(path: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("status") == "completed" and row.get("result_digest"):
            result.setdefault(str(row["query_id"]), set()).add(str(row["result_digest"]))
    return result


def _resource_identity_collisions(path: Path) -> dict[str, list[str]]:
    if not path.is_file():
        return {}
    identities: dict[str, set[str]] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        container_id, host = row.get("container_id"), row.get("host")
        if container_id and host:
            identities.setdefault(str(container_id), set()).add(str(host))
    return {container_id: sorted(hosts) for container_id, hosts in identities.items() if len(hosts) > 1}


def _audited_resource_metrics(run_dir: Path, phase: str, metrics: dict, replica_id: str | None) -> tuple[dict, dict]:
    audited = copy.deepcopy(metrics)
    collisions = _resource_identity_collisions(run_dir / phase / "resource_samples.jsonl")
    invalid_hosts: set[str] = set()
    for hosts in collisions.values():
        if replica_id in hosts:
            invalid_hosts.update(host for host in hosts if host != replica_id)
        else:
            invalid_hosts.update(hosts)
    if invalid_hosts:
        for host in invalid_hosts:
            audited.get("per_host", {}).pop(host, None)
        # The missing container cannot be reconstructed from historical evidence,
        # so infrastructure-wide resource aggregates must remain unavailable.
        for metric in RESOURCE_METRICS:
            audited[metric] = None
    audit = {
        "valid": not collisions,
        "duplicate_container_ids": collisions,
        "invalid_logical_hosts": sorted(invalid_hosts),
        "aggregate_resource_metrics_available": not collisions,
    }
    return audited, audit


def _display(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _row_normalized(values: list[list[float | None]]) -> np.ndarray:
    raw = np.array([[np.nan if value is None else float(value) for value in row] for row in values], dtype=float)
    normalized = np.full_like(raw, np.nan)
    for index, row in enumerate(raw):
        valid = row[np.isfinite(row)]
        if not valid.size:
            continue
        minimum, maximum = float(valid.min()), float(valid.max())
        normalized[index] = 0.5 if maximum == minimum else (row - minimum) / (maximum - minimum)
    return normalized


def _annotated_matrix(
    path: Path,
    values: list[list[float | None]],
    row_labels: list[str],
    column_labels: list[str],
    title: str,
    *,
    formats: list[str] | None = None,
) -> None:
    if not values or not column_labels:
        return
    raw = np.array([[np.nan if value is None else float(value) for value in row] for row in values], dtype=float)
    normalized = _row_normalized(values)
    masked = np.ma.masked_invalid(normalized)
    width = min(7.2, max(4.8, 1.0 + 0.85 * len(column_labels)))
    height = max(2.6, 1.1 + 0.5 * len(row_labels))
    fig, axis = plt.subplots(figsize=(width, height), constrained_layout=True)
    axis.imshow(
        masked,
        cmap=plt.get_cmap("Blues").with_extremes(bad="#eeeeee"),
        vmin=0,
        vmax=1,
        aspect="auto",
    )
    tick_step = max(1, ceil(len(column_labels) / 10))
    tick_positions = list(range(0, len(column_labels), tick_step))
    if tick_positions[-1] != len(column_labels) - 1:
        tick_positions.append(len(column_labels) - 1)
    axis.set_xticks(tick_positions, labels=[column_labels[index] for index in tick_positions])
    axis.set_yticks(range(len(row_labels)), labels=row_labels)
    axis.set_title(title, fontsize=10, fontweight="normal")
    axis.tick_params(axis="x", labelrotation=25, labelsize=8)
    axis.tick_params(axis="y", labelsize=8)
    if raw.size <= 80:
        for row_index in range(raw.shape[0]):
            for column_index in range(raw.shape[1]):
                value = raw[row_index, column_index]
                label = (
                    "N/A" if not np.isfinite(value) else format(value, (formats or [".2f"] * len(values))[row_index])
                )
                shade = normalized[row_index, column_index]
                color = "white" if np.isfinite(shade) and shade > 0.62 else "#17202a"
                axis.text(column_index, row_index, label, ha="center", va="center", fontsize=7.5, color=color)
    else:
        axis.set_xlabel("Monitoring cycle (colour normalized within each metric)", fontsize=8)
    for spine in axis.spines.values():
        spine.set_visible(False)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _figures(run_dir: Path, output: Path, before_metrics: dict, after_metrics: dict | None) -> list[str]:
    figures = output / "figures"
    figures.mkdir(exist_ok=True)
    created: list[str] = []
    trigger_path = run_dir / "trigger.json"
    if trigger_path.is_file():
        observations = _json(trigger_path).get("observations", [])
        if observations:
            columns = [str(index + 1) for index in range(len(observations))]
            values = [
                [item.get("cpu_mean_percent") for item in observations],
                [item.get("cpu_p95_percent") for item in observations],
                [100 * float(item.get("cpu_saturation_fraction") or 0) for item in observations],
                [item.get("logical_latency_ms") for item in observations],
                [float(bool(item.get("condition_holds"))) for item in observations],
            ]
            name = "01_trigger_evidence_matrix.png"
            _annotated_matrix(
                figures / name,
                values,
                ["CPU mean (%)", "CPU p95 (%)", "Saturated samples (%)", "Monitor latency (ms)", "Trigger condition"],
                columns,
                "Policy trigger evidence by monitoring cycle",
                formats=[".1f", ".1f", ".0f", ".1f", ".0f"],
            )
            created.append(f"figures/{name}")
    before_nodes = before_metrics.get("per_host", {})
    after_nodes = (after_metrics or {}).get("per_host", {})
    hosts = sorted(set(before_nodes) | set(after_nodes))
    if hosts:
        for name, metrics, labels, title, formats in (
            (
                "02_node_cpu_before_after.png",
                ("cpu_mean_percent", "cpu_p95_percent"),
                ("Before mean", "Before p95", "After mean", "After p95"),
                "Worker/container CPU under the identical scalability workload (%)",
                [".1f"] * len(hosts),
            ),
            (
                "03_node_memory_before_after.png",
                ("memory_mean_bytes", "memory_peak_bytes"),
                ("Before mean", "Before peak", "After mean", "After peak"),
                "Worker/container memory under the identical scalability workload (MiB)",
                [".1f"] * len(hosts),
            ),
        ):
            values = []
            for host in hosts:
                before = before_nodes.get(host, {})
                after = after_nodes.get(host, {})
                row = [before.get(metrics[0]), before.get(metrics[1]), after.get(metrics[0]), after.get(metrics[1])]
                if "memory" in name:
                    row = [value / (1024**2) if isinstance(value, (int, float)) else None for value in row]
                values.append(row)
            _annotated_matrix(figures / name, values, hosts, list(labels), title, formats=formats)
            created.append(f"figures/{name}")
    workload_metrics = (
        ("application_latency_p50_ms", "Latency p50 (ms)", ".1f"),
        ("application_latency_p95_ms", "Latency p95 (ms)", ".1f"),
        ("application_latency_p99_ms", "Latency p99 (ms)", ".1f"),
        ("application_completed_queries", "Completed queries", ".0f"),
        ("application_timeouts", "Timeouts", ".0f"),
        ("application_throughput_qps", "Throughput (queries/s)", ".3f"),
    )
    name = "04_application_before_after.png"
    _annotated_matrix(
        figures / name,
        [[before_metrics.get(key), (after_metrics or {}).get(key)] for key, _, _ in workload_metrics],
        [label for _, label, _ in workload_metrics],
        ["Before", "After"],
        "Scalability workload before and after adaptation",
        formats=[fmt for _, _, fmt in workload_metrics],
    )
    created.append(f"figures/{name}")

    before_physical = _jsonl(run_dir / "before/application_physical_queries.jsonl")
    after_physical = _jsonl(run_dir / "after/application_physical_queries.jsonl")
    if before_physical and after_physical:
        before_counts: dict[str, int] = {}
        after_counts: dict[str, int] = {}
        for row in before_physical:
            host = str(row.get("host", "unknown"))
            before_counts[host] = before_counts.get(host, 0) + 1
        for row in after_physical:
            host = str(row.get("host", "unknown"))
            after_counts[host] = after_counts.get(host, 0) + 1
        hosts = sorted(
            set(before_counts) | set(after_counts),
            key=lambda host: (host.startswith("edge3-replica"), host),
        )
        positions = np.arange(len(hosts))
        height = 0.36
        fig, axis = plt.subplots(figsize=(7.2, max(3.2, 0.52 * len(hosts) + 1.4)), constrained_layout=True)
        before_bars = axis.barh(
            positions - height / 2,
            [before_counts.get(host, 0) for host in hosts],
            height,
            label="Before",
            color="#7f8c8d",
        )
        after_bars = axis.barh(
            positions + height / 2,
            [after_counts.get(host, 0) for host in hosts],
            height,
            label="After",
            color="#2878b5",
        )
        axis.bar_label(before_bars, padding=3, fontsize=8)
        axis.bar_label(after_bars, padding=3, fontsize=8)
        axis.set_yticks(positions, hosts)
        axis.set_xlabel("Physical application-query executions")
        axis.set_title("Measured request redistribution after adaptation", fontsize=10, fontweight="normal")
        axis.legend(frameon=False, ncol=2)
        axis.grid(axis="x", alpha=0.25)
        axis.spines[["top", "right"]].set_visible(False)
        name = "05_request_redistribution.png"
        fig.savefig(figures / name, dpi=300, bbox_inches="tight")
        plt.close(fig)
        created.append(f"figures/{name}")

    execution_path = run_dir / "execute/result.json"
    if execution_path.is_file():
        execution = _json(execution_path)
        phases = [
            ("Container start", float(execution.get("container_start_seconds") or 0)),
            ("Fragment transfer", float(execution.get("transfer_seconds") or 0)),
            ("RDFS reasoning", float(execution.get("reasoning_seconds") or 0)),
            ("Store load", float(execution.get("store_load_seconds") or 0)),
        ]
        ready = float(execution.get("replica_ready_seconds") or 0)
        accounted = sum(value for _, value in phases)
        if ready > accounted:
            phases.append(("Coordination", ready - accounted))
        colors = ["#4c78a8", "#72b7b2", "#f58518", "#54a24b", "#b279a2"]
        fig, axis = plt.subplots(figsize=(7.2, 2.8), constrained_layout=True)
        left = 0.0
        for (label, duration), color in zip(phases, colors, strict=False):
            axis.barh([0], [duration], left=left, color=color, label=f"{label} ({duration:.1f} s)")
            if duration >= 3:
                axis.text(left + duration / 2, 0, f"{duration:.1f}", ha="center", va="center", fontsize=8)
            left += duration
        axis.axvline(ready, color="#222222", linestyle="--", linewidth=1.2)
        axis.text(ready, 0.62, f"Replica ready: {ready:.1f} s", ha="right", va="bottom", fontsize=8)
        axis.set_yticks([])
        axis.set_xlabel("Elapsed deployment time (s)")
        axis.set_title("Measured replica deployment critical path", fontsize=10, fontweight="normal")
        axis.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.28), fontsize=8)
        axis.spines[["top", "right", "left"]].set_visible(False)
        axis.grid(axis="x", alpha=0.25)
        name = "06_replica_deployment_timeline.png"
        fig.savefig(figures / name, dpi=300, bbox_inches="tight")
        plt.close(fig)
        created.append(f"figures/{name}")

    before_load_path = run_dir / "before/application_load.json"
    after_load_path = run_dir / "after/application_load.json"
    if before_load_path.is_file() and after_load_path.is_file():
        before_rounds = _json(before_load_path).get("rounds", [])
        after_rounds = _json(after_load_path).get("rounds", [])
        if before_rounds and after_rounds:
            before_by_round = {int(row["round"]): float(row["duration_seconds"]) for row in before_rounds}
            after_by_round = {int(row["round"]): float(row["duration_seconds"]) for row in after_rounds}
            rounds = sorted(set(before_by_round) & set(after_by_round))
            fig, axis = plt.subplots(figsize=(7.2, 3.5), constrained_layout=True)
            axis.plot(
                rounds,
                [before_by_round[item] for item in rounds],
                marker="o",
                linewidth=1.5,
                markersize=4,
                color="#7f8c8d",
                label="Before",
            )
            axis.plot(
                rounds,
                [after_by_round[item] for item in rounds],
                marker="s",
                linewidth=1.5,
                markersize=4,
                color="#2878b5",
                label="After",
            )
            axis.set_xticks(rounds)
            axis.set_xlabel("Catalog round (113 logical queries)")
            axis.set_ylabel("Round duration (s)")
            axis.set_title(
                "Round-level workload stability before and after adaptation", fontsize=10, fontweight="normal"
            )
            axis.legend(frameon=False, ncol=2)
            axis.grid(alpha=0.25)
            axis.spines[["top", "right"]].set_visible(False)
            name = "07_round_duration_before_after.png"
            fig.savefig(figures / name, dpi=300, bbox_inches="tight")
            plt.close(fig)
            created.append(f"figures/{name}")

    if trigger_path.is_file():
        trigger = _json(trigger_path)
        host_metrics = trigger.get("per_host_resource_metrics", {})
        thresholds = trigger.get("experimental_thresholds", {})
        if host_metrics:
            hosts = sorted(host_metrics)
            panels = (
                ("cpu_mean_percent", "CPU mean (%)", float(thresholds.get("cpu_mean_percent", 0))),
                ("cpu_p95_percent", "CPU p95 (%)", float(thresholds.get("cpu_p95_percent", 0))),
                (
                    "cpu_saturation_fraction",
                    "Saturated samples (%)",
                    100 * float(thresholds.get("cpu_saturation_fraction", 0)),
                ),
            )
            fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.1), constrained_layout=True)
            selected = str(trigger.get("trigger_resource_host"))
            for axis, (field, label, threshold) in zip(axes, panels, strict=True):
                values = [
                    float(host_metrics[host].get(field) or 0) * (100 if field.endswith("fraction") else 1)
                    for host in hosts
                ]
                colors = ["#d95f02" if host == selected else "#4c78a8" for host in hosts]
                bars = axis.bar(hosts, values, color=colors)
                axis.axhline(threshold, color="#8b1a1a", linestyle="--", linewidth=1.2, label="Threshold")
                axis.bar_label(bars, fmt="%.1f", padding=2, fontsize=7)
                axis.set_title(label, fontsize=9, fontweight="normal")
                axis.tick_params(axis="x", labelrotation=25, labelsize=8)
                axis.grid(axis="y", alpha=0.2)
                axis.spines[["top", "right"]].set_visible(False)
            axes[0].set_ylabel("Observed value")
            fig.legend(
                handles=[
                    Patch(facecolor="#d95f02", label=f"Selected source ({selected})"),
                    Patch(facecolor="#4c78a8", label="Other candidate"),
                    Line2D([0], [0], color="#8b1a1a", linestyle="--", linewidth=1.2, label="Policy threshold"),
                ],
                loc="outside lower center",
                frameon=False,
                ncol=3,
                fontsize=7,
            )
            fig.suptitle(
                f"Policy trigger evidence: {selected} selected as replica source",
                fontsize=10,
                fontweight="normal",
            )
            name = "08_policy_trigger_source_selection.png"
            fig.savefig(figures / name, dpi=300, bbox_inches="tight")
            plt.close(fig)
            created.append(f"figures/{name}")

    execution_data = _json(execution_path) if execution_path.is_file() else {}
    source = str(execution_data.get("replica_source") or "edge3")
    replica = str(execution_data.get("replica", {}).get("id") or f"{source}-replica")
    replica_physical_host = str(execution_data.get("replica", {}).get("physical_host") or "target")
    before_source = before_nodes.get(source, {})
    after_source = after_nodes.get(source, {})
    after_replica = after_nodes.get(replica, {})
    before_samples = [
        row
        for row in _jsonl(run_dir / "before/resource_samples.jsonl")
        if row.get("host") == source and isinstance(row.get("cpu_percent"), (int, float))
    ]
    after_samples = [
        row
        for row in _jsonl(run_dir / "after/resource_samples.jsonl")
        if row.get("host") in {source, replica} and isinstance(row.get("cpu_percent"), (int, float))
    ]
    before_query_rows = _jsonl(run_dir / "before/application_physical_queries.jsonl")
    after_query_rows = _jsonl(run_dir / "after/application_physical_queries.jsonl")
    if before_source and after_source and after_replica and before_samples and after_samples:
        saturation_threshold = 90.0
        if trigger_path.is_file():
            saturation_threshold = float(
                _json(trigger_path).get("experimental_thresholds", {}).get("cpu_p95_percent", 90.0)
            )

        def query_count(rows: list[dict], host: str) -> int:
            return sum(row.get("host") == host for row in rows)

        def saturation_fraction(rows: list[dict], host: str) -> float:
            values = [float(row["cpu_percent"]) for row in rows if row.get("host") == host]
            return 100 * sum(value >= saturation_threshold for value in values) / len(values) if values else 0.0

        source_label = source.capitalize()
        target_label = replica_physical_host.capitalize()
        labels = [f"{source_label}\nbefore", f"{source_label}\nafter", f"Replica on {target_label}\nafter"]
        edge_color = "#d95f02"
        replica_color = "#4c78a8"
        colors = [edge_color, edge_color, replica_color]
        query_values = [
            query_count(before_query_rows, source),
            query_count(after_query_rows, source),
            query_count(after_query_rows, replica),
        ]
        cpu_values = [
            float(before_source["cpu_mean_percent"]),
            float(after_source["cpu_mean_percent"]),
            float(after_replica["cpu_mean_percent"]),
        ]
        saturation_values = [
            saturation_fraction(before_samples, source),
            saturation_fraction(after_samples, source),
            saturation_fraction(after_samples, replica),
        ]
        memory_values = [
            float(before_source["memory_mean_bytes"]) / (1024**2),
            float(after_source["memory_mean_bytes"]) / (1024**2),
            float(after_replica["memory_mean_bytes"]) / (1024**2),
        ]
        panels = (
            (query_values, "Application-query executions", "Queries", ".0f"),
            (cpu_values, "Mean CPU utilization", "CPU (%)", ".1f"),
            (saturation_values, f"Samples at or above {saturation_threshold:.0f}% CPU", "Samples (%)", ".1f"),
            (memory_values, "Mean resident memory", "Memory (MiB)", ".1f"),
        )
        fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.0), constrained_layout=True)
        for axis, (values, title, ylabel, value_format) in zip(axes.flat, panels, strict=True):
            bars = axis.bar(labels, values, color=colors, width=0.65)
            axis.bar_label(bars, fmt=f"%{value_format}", padding=3, fontsize=8)
            axis.set_title(title, fontsize=9, fontweight="normal")
            axis.set_ylabel(ylabel, fontsize=8)
            axis.tick_params(axis="x", labelsize=8)
            axis.tick_params(axis="y", labelsize=8)
            axis.grid(axis="y", alpha=0.22)
            axis.spines[["top", "right"]].set_visible(False)
            axis.margins(y=0.15)
        fig.suptitle(
            f"Measured {source_label} relief and replica resource cost",
            fontsize=10,
            fontweight="normal",
        )
        fig.legend(
            handles=[
                Patch(facecolor=edge_color, label=f"Original {source_label} worker"),
                Patch(facecolor=replica_color, label=f"Read-only replica on {target_label}"),
            ],
            loc="outside lower center",
            frameon=False,
            ncol=2,
            fontsize=8,
        )
        name = "09_edge3_relief_and_replica_cost.png"
        fig.savefig(figures / name, dpi=300, bbox_inches="tight")
        plt.close(fig)
        created.append(f"figures/{name}")

        def rolling_cpu(rows: list[dict], host: str, window: int = 9) -> tuple[np.ndarray, np.ndarray]:
            values = np.array(
                [float(row["cpu_percent"]) for row in rows if row.get("host") == host],
                dtype=float,
            )
            if not values.size:
                return np.array([]), np.array([])
            size = min(window, values.size)
            smoothed = np.convolve(values, np.ones(size) / size, mode="same")
            progress = np.linspace(0, 100, values.size)
            return progress, smoothed

        fig, axis = plt.subplots(figsize=(7.2, 3.8), constrained_layout=True)
        for rows, host, label, color, style in (
            (before_samples, source, f"{source_label} before", "#7f2704", "-"),
            (after_samples, source, f"{source_label} after", edge_color, "-"),
            (after_samples, replica, f"Replica on {target_label} after", replica_color, "-"),
        ):
            progress, cpu = rolling_cpu(rows, host)
            axis.plot(progress, cpu, label=label, color=color, linestyle=style, linewidth=1.7)
        axis.axhline(
            saturation_threshold,
            color="#8b1a1a",
            linestyle="--",
            linewidth=1.1,
            label="Saturation threshold",
        )
        axis.set_xlabel("Workload progress (%)")
        axis.set_ylabel("Rolling mean CPU (%)")
        axis.set_title(
            f"CPU demand transferred from {source_label} to the {target_label} replica",
            fontsize=10,
            fontweight="normal",
        )
        axis.set_xlim(0, 100)
        axis.set_ylim(bottom=0)
        axis.grid(alpha=0.22)
        axis.spines[["top", "right"]].set_visible(False)
        handles, legend_labels = axis.get_legend_handles_labels()
        fig.legend(
            handles,
            legend_labels,
            loc="outside lower center",
            frameon=False,
            fontsize=8,
            ncol=2,
        )
        name = "10_edge3_cpu_profile_before_after.png"
        fig.savefig(figures / name, dpi=300, bbox_inches="tight")
        plt.close(fig)
        created.append(f"figures/{name}")
    return created


def report(run_dir: Path) -> Path:
    before = _json(run_dir / "before/result.json")
    execution = _json(run_dir / "execute/result.json")
    no_action = execution.get("status") == "skipped_no_action"
    after = None if no_action else _json(run_dir / "after/result.json")
    replica_id = execution.get("replica", {}).get("id")
    before_metrics, before_resource_audit = _audited_resource_metrics(run_dir, "before", before["metrics"], replica_id)
    after_metrics, after_resource_audit = (
        (
            {},
            {
                "valid": True,
                "duplicate_container_ids": {},
                "invalid_logical_hosts": [],
                "aggregate_resource_metrics_available": True,
            },
        )
        if after is None
        else _audited_resource_metrics(run_dir, "after", after["metrics"], replica_id)
    )
    comparisons = []
    for metric in METRICS:
        baseline = before_metrics.get(metric)
        adapted = after_metrics.get(metric) if after is not None else None
        delta = adapted - baseline if isinstance(baseline, (int, float)) and isinstance(adapted, (int, float)) else None
        comparisons.append({"metric": metric, "before": baseline, "after": adapted, "delta": delta})
    node_comparisons = []
    before_nodes = before_metrics.get("per_host", {})
    after_nodes = after_metrics.get("per_host", {}) if after is not None else {}
    for host in sorted(set(before_nodes) | set(after_nodes)):
        for metric in (
            "cpu_mean_percent",
            "cpu_p95_percent",
            "cpu_peak_percent",
            "memory_mean_bytes",
            "memory_peak_bytes",
            "network_rx_bytes",
            "network_tx_bytes",
        ):
            baseline = before_nodes.get(host, {}).get(metric)
            adapted = after_nodes.get(host, {}).get(metric)
            delta = (
                adapted - baseline if isinstance(baseline, (int, float)) and isinstance(adapted, (int, float)) else None
            )
            node_comparisons.append(
                {"host": host, "metric": metric, "before": baseline, "after": adapted, "delta": delta}
            )
    before_digests = _digests(run_dir / "before/logical_queries.jsonl")
    after_digests = {} if no_action else _digests(run_dir / "after/logical_queries.jsonl")
    common = sorted(set(before_digests) & set(after_digests))
    semantic_equivalence = {query_id: before_digests[query_id] == after_digests[query_id] for query_id in common}
    resource_effect: dict[str, float | int | str] = {}
    source = str(execution.get("replica_source") or "")
    replica = str(execution.get("replica", {}).get("id") or "")
    source_before = before_nodes.get(source, {})
    source_after = after_nodes.get(source, {})
    replica_after = after_nodes.get(replica, {})
    if source_before and source_after and replica_after:
        before_cpu = float(source_before["cpu_mean_percent"])
        after_cpu = float(source_after["cpu_mean_percent"])
        before_memory = float(source_before["memory_mean_bytes"])
        combined_after_memory = float(source_after["memory_mean_bytes"]) + float(replica_after["memory_mean_bytes"])
        before_queries = _jsonl(run_dir / "before/application_physical_queries.jsonl")
        after_queries = _jsonl(run_dir / "after/application_physical_queries.jsonl")
        source_before_queries = sum(row.get("host") == source for row in before_queries)
        source_after_queries = sum(row.get("host") == source for row in after_queries)
        replica_after_queries = sum(row.get("host") == replica for row in after_queries)
        resource_effect = {
            "source": source,
            "replica": replica,
            "source_query_executions_before": source_before_queries,
            "source_query_executions_after": source_after_queries,
            "replica_query_executions_after": replica_after_queries,
            "source_cpu_mean_before_percent": before_cpu,
            "source_cpu_mean_after_percent": after_cpu,
            "source_cpu_mean_reduction_percent": 100 * (before_cpu - after_cpu) / before_cpu,
            "source_memory_mean_before_mib": before_memory / (1024**2),
            "source_memory_mean_after_mib": float(source_after["memory_mean_bytes"]) / (1024**2),
            "replica_memory_mean_after_mib": float(replica_after["memory_mean_bytes"]) / (1024**2),
            "combined_memory_increase_percent": 100 * (combined_after_memory - before_memory) / before_memory,
        }
    output = run_dir / "comparison"
    output.mkdir(exist_ok=True)
    figures = _figures(run_dir, output, before_metrics, after_metrics if after is not None else None)
    summary = {
        "stage_semantics": {
            "monitor": "measured",
            "analyze": "simulated_rule_based",
            "plan": "simulated_rule_based",
            "execute": "scripted_manual",
            "verification": "measured",
        },
        "adaptation_outcome": "no_action" if no_action else "executed_and_verified",
        "same_workload_verified": None if after is None else bool(after.get("same_workload_verified")),
        "same_application_sequence_verified": (
            None if after is None else bool(after.get("same_application_sequence_verified"))
        ),
        "metrics": comparisons,
        "node_metrics": node_comparisons,
        "figures": figures,
        "adaptation_execution": {
            "container_start_seconds": execution.get("container_start_seconds"),
            "transfer_seconds": execution.get("transfer_seconds"),
            "reasoning_seconds": execution.get("reasoning_seconds"),
            "store_load_seconds": execution.get("store_load_seconds"),
            "replica_ready_seconds": execution.get("replica_ready_seconds"),
        },
        "adaptation_resource_effect": resource_effect,
        "resource_telemetry_audit": {
            "before": before_resource_audit,
            "after": after_resource_audit,
        },
        "semantic_result_digest_equivalence": semantic_equivalence,
        "all_common_query_digests_equivalent": (
            None if no_action else bool(common) and all(semantic_equivalence.values())
        ),
        "interpretation": (
            "The measured trigger did not persist for the configured consecutive cycles. No infrastructure change "
            "or before/after comparison was performed."
            if no_action
            else "Observed deltas are measurements; replica readiness does not imply performance improvement."
        ),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (output / "metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("metric", "before", "after", "delta"))
        writer.writeheader()
        writer.writerows(comparisons)
    with (output / "node-metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("host", "metric", "before", "after", "delta"))
        writer.writeheader()
        writer.writerows(node_comparisons)
    title = "# Adaptation decision report" if no_action else "# Adaptation before/after report"
    lines = [title, ""]
    if no_action:
        lines += [
            "The measured trigger did not persist for the configured consecutive cycles. Analyze and Plan selected `no_action`.",
            "Execute and Verification were recorded as skipped, and the physical infrastructure was not changed.",
            "",
            "The table preserves baseline measurements only. Empty After and Delta cells are intentional.",
            "",
        ]
    else:
        lines += [
            "Monitor and verification are measured. Analyze and Plan are deterministic simulations. Execute is scripted and manually invoked.",
            "",
        ]
        if not after_resource_audit["valid"]:
            lines += [
                (
                    "Resource telemetry warning: one physical container was sampled under multiple logical worker IDs. "
                    "Affected aliases and infrastructure-wide CPU, memory, and network aggregates are reported as unavailable; "
                    "query, timeout, throughput, latency, and semantic evidence remain valid."
                ),
                "",
            ]
    lines += ["| Metric | Before | After | Delta |", "|---|---:|---:|---:|"]
    lines.extend(
        f"| {row['metric']} | {_display(row['before'])} | {_display(row['after'])} | {_display(row['delta'])} |"
        for row in comparisons
    )
    if no_action:
        lines += ["", "No replica was deployed because the adaptation condition was not sustained."]
    else:
        lines += [
            "",
            f"Replica ready time: {execution.get('replica_ready_seconds')} seconds.",
            "",
            "A successfully deployed replica is an execution outcome. Performance improvement must be inferred only from the measured deltas above.",
        ]
        if resource_effect:
            lines += [
                "",
                "## Measured source relief and replica cost",
                "",
                (
                    f"The source worker `{source}` reduced its mean CPU utilization from "
                    f"{resource_effect['source_cpu_mean_before_percent']:.1f}% to "
                    f"{resource_effect['source_cpu_mean_after_percent']:.1f}% "
                    f"({resource_effect['source_cpu_mean_reduction_percent']:.1f}% relative reduction)."
                ),
                (
                    f"Its application-query executions fell from "
                    f"{resource_effect['source_query_executions_before']} to "
                    f"{resource_effect['source_query_executions_after']}; the replica processed "
                    f"{resource_effect['replica_query_executions_after']} executions."
                ),
                (
                    "The source memory footprint remained nearly constant because it retained its ontology fragment. "
                    f"The additional replica increased the combined source-plus-replica memory footprint by "
                    f"{resource_effect['combined_memory_increase_percent']:.1f}%."
                ),
            ]
    (output / "report.md").write_text("\n".join(lines) + "\n")
    manifest_path = run_dir / "manifest.json"
    manifest = _json(manifest_path)
    manifest.update(status="reported_no_action" if no_action else "reported", finished_at=datetime.now(UTC).isoformat())
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return output
