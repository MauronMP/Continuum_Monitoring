from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from statistics import median

import matplotlib.pyplot as plt
import numpy as np

LAYOUTS = ("distributed", "replicated")
COLORS = {"distributed": "#2878B5", "replicated": "#E07A1F"}
MARKERS = {"distributed": "o", "replicated": "s"}
FAILURE_STATUSES = {
    "failed",
    "hard_timeout",
    "query_timeout",
    "oom_killed",
    "payload_limit_exceeded",
    "incompatible_worker",
    "semantic_mismatch",
}


def _percentile(values: list[float], q: float) -> float | None:
    return float(np.percentile(values, q)) if values else None


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and np.isfinite(float(value))


def _failure_cause(error: str) -> str:
    message = error.lower()
    if "payload_limit_exceeded" in message:
        return "payload_limit_exceeded"
    if "http 413" in message or "length limit exceeded" in message:
        return "http_body_limit"
    if "broken pipe" in message:
        return "upload_broken_pipe"
    if "timed out" in message:
        return "timeout"
    if "semantic_mismatch" in message or "http 422" in message:
        return "semantic_mismatch"
    if "oom" in message:
        return "out_of_memory"
    return "other"


def _write_csv(path: Path, data: list[dict]) -> None:
    keys = sorted({key for row in data for key in row})
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)


def _users(rows: list[dict]) -> list[int]:
    return sorted({int(row["users"]) for row in rows})


def _mark_incomplete(ax, positions, rows: list[dict], users: list[int], *, add_label: bool) -> None:
    by_user = {int(row["users"]): row for row in rows}
    label_used = False
    for position, user in zip(positions, users, strict=True):
        row = by_user.get(user)
        if row and int(row["completed_repetitions"]) < int(row["repetitions"]):
            ax.scatter(
                position,
                0.035,
                transform=ax.get_xaxis_transform(),
                marker="x",
                s=42,
                linewidths=1.5,
                color="#B22222",
                zorder=6,
                label="Incomplete scenario" if add_label and not label_used else None,
            )
            label_used = True


def _finish(fig, ax, path: Path, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title, fontsize=10, fontweight="normal")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.22)
    handles, _ = ax.get_legend_handles_labels()
    if handles:
        ax.legend(frameon=False, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_series(rows, figures, filename, field, title, ylabel, *, scale=1.0) -> None:
    users = _users(rows)
    positions = np.arange(len(users))
    fig, ax = plt.subplots(figsize=(5.2, 3.45))
    any_value = False
    for layout in LAYOUTS:
        layout_rows = [row for row in rows if row["layout"] == layout]
        by_user = {int(row["users"]): row for row in layout_rows}
        values = [
            float(by_user[user][field]) / scale if user in by_user and _finite(by_user[user].get(field)) else np.nan
            for user in users
        ]
        if np.isfinite(values).any():
            any_value = True
            ax.plot(
                positions,
                values,
                marker=MARKERS[layout],
                color=COLORS[layout],
                linewidth=1.8,
                label=layout.capitalize(),
            )
        _mark_incomplete(ax, positions, layout_rows, users, add_label=layout == LAYOUTS[0])
    if not any_value:
        ax.text(0.5, 0.52, "No completed measurements", transform=ax.transAxes, ha="center", color="#666")
    ax.set_xticks(positions, [str(user) for user in users])
    _finish(fig, ax, figures / filename, title, "Users / monitored entities", ylabel)


def _resource_heatmap(node_rows, figures, filename, field, title, colorbar_label, scale, users, hosts) -> None:
    if not users or not hosts:
        fig, ax = plt.subplots(figsize=(6.0, 2.7))
        ax.axis("off")
        ax.text(0.5, 0.5, "No per-node measurements", ha="center", va="center")
        fig.savefig(figures / filename, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return
    finite_values = [float(row[field]) / scale for row in node_rows if _finite(row.get(field))]
    vmax = max(finite_values) if finite_values else 1
    fig, axes = plt.subplots(2, 1, figsize=(6.3, 4.9), sharex=True, constrained_layout=True)
    image = None
    for ax, layout in zip(axes, LAYOUTS, strict=True):
        by_key = {(str(row["host"]), int(row["users"])): row for row in node_rows if row["layout"] == layout}
        matrix = np.full((len(hosts), len(users)), np.nan)
        for row_index, host in enumerate(hosts):
            for column, user in enumerate(users):
                row = by_key.get((host, user))
                if row and _finite(row.get(field)):
                    matrix[row_index, column] = float(row[field]) / scale
        image = ax.imshow(np.ma.masked_invalid(matrix), aspect="auto", cmap="viridis", vmin=0, vmax=vmax)
        ax.set_yticks(range(len(hosts)))
        ax.set_yticklabels(hosts)
        ax.set_title(layout.capitalize(), fontsize=9, fontweight="normal")
        for row_index in range(len(hosts)):
            for column in range(len(users)):
                value = matrix[row_index, column]
                text = "—" if not np.isfinite(value) else f"{value:.1f}"
                color = "white" if np.isfinite(value) and value / vmax > 0.52 else "black"
                ax.text(column, row_index, text, ha="center", va="center", fontsize=6.7, color=color)
    axes[-1].set_xticks(range(len(users)), [str(user) for user in users])
    axes[-1].set_xlabel("Users / monitored entities")
    fig.suptitle(title, fontsize=10, fontweight="normal")
    fig.colorbar(image, ax=axes, shrink=0.82, label=colorbar_label)
    fig.savefig(figures / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)


def report(run_dir: Path) -> Path:
    summary, figures = run_dir / "summary", run_dir / "figures"
    summary.mkdir(exist_ok=True)
    figures.mkdir(exist_ok=True)
    for old in figures.glob("*.png"):
        old.unlink()

    grouped: dict[tuple[int, str], list[dict]] = {}
    query_rows, catalog_rows, resource_rows, preparation_rows, failures = [], [], [], [], []
    for result_path in run_dir.glob("scenarios/*/*/rep-*/result.json"):
        result = json.loads(result_path.read_text())
        grouped.setdefault((result["users"], result["layout"]), []).append(result)
        if result["status"] in FAILURE_STATUSES:
            failures.append(result)
        for prepared in result.get("preparation", []):
            reasoning = prepared.get("reasoning", {})
            preparation_rows.append(
                {
                    "scenario": result["scenario"],
                    "users": result["users"],
                    "layout": result["layout"],
                    "repetition": result["repetition"],
                    "host": prepared.get("host"),
                    "status": result["status"],
                    "partition_seconds": result.get("partition_seconds"),
                    "serialize_seconds": result.get("serialize_seconds"),
                    "transfer_seconds": prepared.get("transfer_seconds"),
                    "remote_load_seconds": prepared.get("remote_load_seconds"),
                    "reasoning_seconds": reasoning.get("reasoning_seconds"),
                    "transfer_and_remote_seconds": prepared.get("transfer_and_remote_seconds"),
                    "payload_bytes": prepared.get("payload_bytes"),
                    "triples_before_reasoning": reasoning.get("triples_before_reasoning"),
                    "triples_after_reasoning": reasoning.get("triples_after_reasoning"),
                    "dataset_digest": prepared.get("dataset_digest"),
                    "closure_digest": prepared.get("closure_digest"),
                }
            )
        qpath = result_path.with_name("logical_queries.json")
        if qpath.is_file():
            repetition_queries = json.loads(qpath.read_text())
            query_rows.extend(repetition_queries)
            failures.extend(
                {"failure_scope": "logical_query", **row}
                for row in repetition_queries
                if row.get("status") != "completed"
            )
        cpath = result_path.with_name("catalog_rounds.json")
        if cpath.is_file():
            rounds = json.loads(cpath.read_text())
            for row in rounds:
                row.update(users=result["users"], layout=result["layout"], repetition=result["repetition"])
            catalog_rows.extend(rounds)
        rpath = result_path.with_name("resources.jsonl")
        if rpath.is_file():
            for line in rpath.read_text().splitlines():
                row = json.loads(line)
                row.update(
                    users=result["users"],
                    layout=result["layout"],
                    repetition=result["repetition"],
                    result_status=result["status"],
                )
                resource_rows.append(row)
    failures.extend(json.loads(path.read_text()) for path in run_dir.glob("**/failure.json"))

    rows, node_rows = [], []
    for (users, layout), reps in sorted(grouped.items()):
        complete = [result for result in reps if result["status"].startswith("completed")]
        complete_ids = {int(result["repetition"]) for result in complete}
        prepares = [float(result["preparation_seconds"]) for result in complete]
        partitions = [float(result.get("partition_seconds", 0)) for result in complete]
        serializes = [float(result.get("serialize_seconds", 0)) for result in complete]
        transfers = [
            max((float(item.get("transfer_seconds", 0)) for item in result.get("preparation", [])), default=0)
            for result in complete
        ]
        remote_loads = [
            max((float(item.get("remote_load_seconds", 0)) for item in result.get("preparation", [])), default=0)
            for result in complete
        ]
        reasoning = [
            max(
                (
                    float(item.get("reasoning", {}).get("reasoning_seconds", 0))
                    for item in result.get("preparation", [])
                ),
                default=0,
            )
            for result in complete
        ]
        payload = [
            sum(int(item.get("payload_bytes", 0)) for item in result.get("preparation", [])) for result in complete
        ]
        reasoned = (
            median(
                [
                    sum(
                        int(item.get("reasoning", {}).get("triples_after_reasoning", 0))
                        for item in result.get("preparation", [])
                    )
                    for result in complete
                ]
            )
            if complete
            else None
        )
        queries = [
            float(row["duration_ms"])
            for row in query_rows
            if row["layout"] == layout
            and row.get("users") == users
            and int(row.get("repetition", 0)) in complete_ids
            and row["status"] == "completed"
        ]
        catalogs = [
            row
            for row in catalog_rows
            if row["layout"] == layout and row["users"] == users and int(row["repetition"]) in complete_ids
        ]
        catalog_by_rep: dict[int, list[dict]] = {}
        for item in catalogs:
            catalog_by_rep.setdefault(int(item["repetition"]), []).append(item)
        catalog_throughputs, catalog_durations = [], []
        for rounds in catalog_by_rep.values():
            duration = sum(float(item["duration_seconds"]) for item in rounds)
            if duration > 0:
                catalog_throughputs.append(sum(int(item["logical_queries"]) for item in rounds) / duration)
            catalog_durations.extend(float(item["duration_seconds"]) for item in rounds)
        resources = [
            row
            for row in resource_rows
            if row["users"] == users
            and row["layout"] == layout
            and int(row["repetition"]) in complete_ids
            and "cpu_percent" in row
        ]
        cpu = [float(row["cpu_percent"]) for row in resources]
        memory = [float(row["memory_bytes"]) for row in resources if row.get("memory_bytes") is not None]
        counter_totals = {"cpu_usage_seconds": [], "network_rx_bytes": [], "network_tx_bytes": []}
        by_rep_host: dict[tuple[int, str], list[dict]] = {}
        for sample in resources:
            by_rep_host.setdefault((int(sample["repetition"]), str(sample["host"])), []).append(sample)
        per_rep: dict[int, dict[str, float]] = {}
        for (repetition, _host), samples in by_rep_host.items():
            totals = per_rep.setdefault(repetition, {key: 0.0 for key in counter_totals})
            for key in counter_totals:
                values = [float(sample[key]) for sample in samples if sample.get(key) is not None]
                if values:
                    totals[key] += max(values) - min(values)
        for totals in per_rep.values():
            for key, value in totals.items():
                counter_totals[key].append(value)
        causes = Counter(
            _failure_cause(str(result.get("error", ""))) for result in reps if result["status"] in FAILURE_STATUSES
        )
        rows.append(
            {
                "users": users,
                "layout": layout,
                "repetitions": len(reps),
                "completed_repetitions": len(complete),
                "dataset_generation_seconds": median(
                    [result["dataset"]["dataset_generation_seconds"] for result in reps]
                ),
                "dataset_bytes": median([result["dataset"]["dataset_bytes"] for result in reps]),
                "dataset_digest": reps[0]["dataset"]["dataset_digest"],
                "actual_input_triples": median([result["dataset"]["actual_input_triples"] for result in reps]),
                "actual_reasoned_triples": reasoned,
                "preparation_seconds_median": median(prepares) if prepares else None,
                "preparation_seconds_min": min(prepares) if prepares else None,
                "preparation_seconds_max": max(prepares) if prepares else None,
                "partition_seconds_median": median(partitions) if partitions else None,
                "serialize_seconds_median": median(serializes) if serializes else None,
                "transfer_seconds_median": median(transfers) if transfers else None,
                "remote_load_seconds_median": median(remote_loads) if remote_loads else None,
                "reasoning_seconds_median": median(reasoning) if reasoning else None,
                "transfer_bytes_median": median(payload) if payload else None,
                "query_latency_p50_ms": _percentile(queries, 50),
                "query_latency_p95_ms": _percentile(queries, 95),
                "query_latency_p99_ms": _percentile(queries, 99),
                "catalog_round_seconds_median": median(catalog_durations) if catalog_durations else None,
                "catalog_throughput_per_second": median(catalog_throughputs) if catalog_throughputs else None,
                "cpu_mean_percent": float(np.mean(cpu)) if cpu else None,
                "cpu_p95_percent": _percentile(cpu, 95),
                "cpu_peak_percent": max(cpu) if cpu else None,
                "cpu_seconds_median": median(counter_totals["cpu_usage_seconds"])
                if counter_totals["cpu_usage_seconds"]
                else None,
                "memory_mean_bytes": float(np.mean(memory)) if memory else None,
                "memory_p95_bytes": _percentile(memory, 95),
                "memory_peak_bytes": max(memory) if memory else None,
                "network_rx_bytes_median": median(counter_totals["network_rx_bytes"])
                if counter_totals["network_rx_bytes"]
                else None,
                "network_tx_bytes_median": median(counter_totals["network_tx_bytes"])
                if counter_totals["network_tx_bytes"]
                else None,
                "failures": len(reps) - len(complete),
                "failure_causes": ";".join(f"{key}:{value}" for key, value in sorted(causes.items())),
            }
        )
        for host in sorted({str(row["host"]) for row in resources}):
            samples = [row for row in resources if row["host"] == host]
            host_cpu = [float(row["cpu_percent"]) for row in samples]
            host_memory = [float(row["memory_bytes"]) for row in samples if row.get("memory_bytes") is not None]
            node_rows.append(
                {
                    "users": users,
                    "layout": layout,
                    "host": host,
                    "cpu_mean_percent": float(np.mean(host_cpu)) if host_cpu else None,
                    "cpu_p95_percent": _percentile(host_cpu, 95),
                    "cpu_peak_percent": max(host_cpu) if host_cpu else None,
                    "memory_mean_bytes": float(np.mean(host_memory)) if host_memory else None,
                    "memory_p95_bytes": _percentile(host_memory, 95),
                    "memory_peak_bytes": max(host_memory) if host_memory else None,
                }
            )

    fields = list(rows[0]) if rows else ["users", "layout"]
    with (summary / "scalability.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    for name, data in (
        ("preparation.csv", preparation_rows),
        ("queries.csv", query_rows),
        ("resources.csv", resource_rows),
        ("node_resources.csv", node_rows),
        ("failures.csv", failures),
    ):
        _write_csv(summary / name, data)
    cause_rows = [
        {"cause": cause, "count": count}
        for cause, count in sorted(Counter(_failure_cause(str(row.get("error", ""))) for row in failures).items())
    ]
    _write_csv(summary / "failure_causes.csv", cause_rows)

    _plot_series(
        rows,
        figures,
        "01_users_vs_input_triples.png",
        "actual_input_triples",
        "ABox growth from monitored population",
        "Input RDF triples",
    )
    _plot_series(
        rows,
        figures,
        "02_users_vs_reasoned_triples.png",
        "actual_reasoned_triples",
        "RDFS materialized graph size",
        "Reasoned RDF triples (sum across workers)",
    )
    _plot_series(
        rows,
        figures,
        "03_preparation_total.png",
        "preparation_seconds_median",
        "End-to-end preparation",
        "Median seconds",
    )

    users = _users(rows)
    positions = np.arange(len(users))
    width = 0.36
    phases = (
        ("partition_seconds_median", "Partition", "#4C78A8"),
        ("serialize_seconds_median", "Serialize", "#F58518"),
        ("transfer_seconds_median", "Transfer", "#54A24B"),
        ("remote_load_seconds_median", "Remote load", "#E45756"),
    )
    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    for layout, offset, hatch in (("distributed", -width / 2, ""), ("replicated", width / 2, "//")):
        layout_rows = [row for row in rows if row["layout"] == layout]
        by_user = {int(row["users"]): row for row in layout_rows}
        bottom = np.zeros(len(users))
        for field, label, color in phases:
            values = np.array(
                [
                    float(by_user[user][field]) if user in by_user and _finite(by_user[user].get(field)) else np.nan
                    for user in users
                ]
            )
            ax.bar(
                positions + offset,
                values,
                width,
                bottom=bottom,
                color=color,
                edgecolor="white",
                hatch=hatch,
                label=label if layout == "distributed" else None,
            )
            bottom += np.nan_to_num(values)
        _mark_incomplete(ax, positions + offset, layout_rows, users, add_label=layout == "distributed")
    ax.set_xticks(positions, [str(user) for user in users])
    _finish(
        fig,
        ax,
        figures / "04_preparation_breakdown.png",
        "Preparation phases (reasoning excluded)",
        "Users / monitored entities",
        "Median seconds",
    )

    _plot_series(
        rows,
        figures,
        "05_reasoning_time.png",
        "reasoning_seconds_median",
        "RDFS materialization cost",
        "Median seconds",
    )
    fig, ax = plt.subplots(figsize=(6.0, 3.7))
    for layout in LAYOUTS:
        layout_rows = [row for row in rows if row["layout"] == layout]
        by_user = {int(row["users"]): row for row in layout_rows}
        for metric, label, style in (
            ("query_latency_p50_ms", "p50", "-"),
            ("query_latency_p95_ms", "p95", "--"),
            ("query_latency_p99_ms", "p99", ":"),
        ):
            values = [
                float(by_user[user][metric]) if user in by_user and _finite(by_user[user].get(metric)) else np.nan
                for user in users
            ]
            if np.isfinite(values).any():
                ax.plot(
                    positions,
                    values,
                    linestyle=style,
                    marker=MARKERS[layout],
                    color=COLORS[layout],
                    linewidth=1.5,
                    label=f"{layout.capitalize()} {label}",
                )
        _mark_incomplete(ax, positions, layout_rows, users, add_label=layout == "distributed")
    ax.set_xticks(positions, [str(user) for user in users])
    _finish(
        fig,
        ax,
        figures / "06_query_latency_p50_p95_p99.png",
        "Logical SPARQL latency distribution",
        "Users / monitored entities",
        "Latency (ms)",
    )
    _plot_series(
        rows,
        figures,
        "07_catalog_throughput.png",
        "catalog_throughput_per_second",
        "Logical query throughput",
        "Logical queries/s",
    )

    for number, prefix, fields, title, unit, scale in (
        (
            "08",
            "cpu",
            (("cpu_mean_percent", "mean"), ("cpu_p95_percent", "p95"), ("cpu_peak_percent", "peak")),
            "Container CPU on completed repetitions",
            "CPU (%)",
            1.0,
        ),
        (
            "09",
            "memory",
            (("memory_mean_bytes", "mean"), ("memory_p95_bytes", "p95"), ("memory_peak_bytes", "peak")),
            "Container memory on completed repetitions",
            "Memory (MiB)",
            1024**2,
        ),
    ):
        fig, axes = plt.subplots(2, 1, figsize=(5.7, 5.0), sharex=True, constrained_layout=True)
        for ax, layout in zip(axes, LAYOUTS, strict=True):
            layout_rows = [row for row in rows if row["layout"] == layout]
            by_user = {int(row["users"]): row for row in layout_rows}
            for field, label in fields:
                values = [
                    float(by_user[user][field]) / scale
                    if user in by_user and _finite(by_user[user].get(field))
                    else np.nan
                    for user in users
                ]
                if np.isfinite(values).any():
                    ax.plot(positions, values, marker="o", linewidth=1.4, label=label)
            _mark_incomplete(ax, positions, layout_rows, users, add_label=True)
            ax.set_ylabel(unit)
            ax.set_title(layout.capitalize(), fontsize=9, fontweight="normal")
            ax.grid(alpha=0.22)
            handles, _ = ax.get_legend_handles_labels()
            if handles:
                ax.legend(frameon=False, fontsize=7, ncol=4)
        axes[-1].set_xticks(positions, [str(user) for user in users])
        axes[-1].set_xlabel("Users / monitored entities")
        fig.suptitle(title, fontsize=10, fontweight="normal")
        fig.savefig(figures / f"{number}_{prefix}_mean_p95_peak.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

    _plot_series(
        rows,
        figures,
        "10_transfer_bytes.png",
        "transfer_bytes_median",
        "RDF payload transferred",
        "MiB per repetition",
        scale=1024**2,
    )

    matrix = np.zeros((len(LAYOUTS), len(users)))
    annotations = [["" for _ in users] for _ in LAYOUTS]
    by_key = {(row["layout"], int(row["users"])): row for row in rows}
    for row_index, layout in enumerate(LAYOUTS):
        for column, user in enumerate(users):
            row = by_key.get((layout, user), {})
            total = int(row.get("repetitions", 0))
            completed = int(row.get("completed_repetitions", 0))
            matrix[row_index, column] = completed / total if total else 0
            annotations[row_index][column] = f"{completed}/{total}" if total else "—"
    fig, ax = plt.subplots(figsize=(6.0, 2.25))
    image = ax.imshow(matrix, vmin=0, vmax=1, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(len(users)), [str(user) for user in users])
    ax.set_yticks(range(len(LAYOUTS)), [x.capitalize() for x in LAYOUTS])
    for row_index in range(len(LAYOUTS)):
        for column in range(len(users)):
            ax.text(column, row_index, annotations[row_index][column], ha="center", va="center", fontsize=8)
    ax.set_title("Measured repetition completion frontier", fontsize=10, fontweight="normal")
    ax.set_xlabel("Users / monitored entities")
    fig.colorbar(image, ax=ax, label="Completion ratio", shrink=0.8)
    fig.tight_layout()
    fig.savefig(figures / "11_timeout_failure_frontier.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.0, 3.45))
    for layout, offset in (("distributed", -width / 2), ("replicated", width / 2)):
        layout_rows = {int(row["users"]): row for row in rows if row["layout"] == layout}
        completed = [int(layout_rows.get(user, {}).get("completed_repetitions", 0)) for user in users]
        failed = [int(layout_rows.get(user, {}).get("failures", 0)) for user in users]
        ax.bar(positions + offset, completed, width, color=COLORS[layout], label=f"{layout.capitalize()} completed")
        ax.bar(
            positions + offset,
            failed,
            width,
            bottom=completed,
            facecolor="white",
            edgecolor=COLORS[layout],
            hatch="xx",
            label=f"{layout.capitalize()} failed",
        )
    ax.set_xticks(positions, [str(user) for user in users])
    ax.set_ylim(0, 3.4)
    ax.set_yticks(range(4))
    _finish(
        fig,
        ax,
        figures / "12_distributed_vs_replicated.png",
        "Completion evidence by layout and population",
        "Users / monitored entities",
        "Measured repetitions",
    )
    topology_path = run_dir / "topology.json"
    all_hosts = (
        sorted(host["id"] for host in json.loads(topology_path.read_text())["hosts"])
        if topology_path.is_file()
        else sorted({str(row["host"]) for row in node_rows})
    )
    _resource_heatmap(
        node_rows,
        figures,
        "13_node_cpu_p95.png",
        "cpu_p95_percent",
        "Per-node CPU p95 on completed repetitions",
        "CPU p95 (%)",
        1.0,
        users,
        all_hosts,
    )
    _resource_heatmap(
        node_rows,
        figures,
        "14_node_memory_peak.png",
        "memory_peak_bytes",
        "Per-node peak memory on completed repetitions",
        "Peak memory (MiB)",
        1024**2,
        users,
        all_hosts,
    )
    (summary / "summary.json").write_text(json.dumps(rows, indent=2) + "\n")
    return summary
