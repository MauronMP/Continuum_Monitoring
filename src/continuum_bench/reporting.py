from __future__ import annotations

import csv
import json
import tomllib
from collections import Counter
from pathlib import Path
from statistics import median

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from matplotlib.ticker import NullFormatter

LAYOUTS = ("distributed", "replicated")
COLORS = {"distributed": "#2878B5", "replicated": "#E07A1F"}
MARKERS = {"distributed": "o", "replicated": "s"}
CATEGORY_COLOR_MAP = "tab20"
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


def _failure_cause(error: str, status: str | None = None) -> str:
    if status == "oom_killed":
        return "out_of_memory"
    if status in {"hard_timeout", "query_timeout"}:
        return "timeout"
    if status in {"payload_limit_exceeded", "semantic_mismatch", "incompatible_worker"}:
        return status
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


def _population_ticks(users: list[int]) -> list[int]:
    return users


def _population_label(value: int) -> str:
    if value >= 1_000 and value % 1_000 == 0:
        return f"{value // 1_000}k"
    return str(value)


def _configure_population_axis(ax, users: list[int], *, categorical: bool) -> None:
    ticks = _population_ticks(users)
    if categorical:
        positions = np.arange(len(users))
        ax.set_xticks(positions, [_population_label(user) for user in users])
    else:
        ax.set_xscale("log")
        ax.set_xticks(ticks, [_population_label(user) for user in ticks])
        ax.xaxis.set_minor_formatter(NullFormatter())
        if users:
            ax.set_xlim(max(0.8, users[0] * 0.75), users[-1] * 1.18)
    ax.tick_params(
        axis="x",
        labelsize=6.8 if categorical else 6.0,
        labelrotation=45 if categorical else 60,
    )
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")


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
    fig, ax = plt.subplots(figsize=(7.4, 4.15))
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
    _configure_population_axis(ax, users, categorical=True)
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
    fig, axes = plt.subplots(2, 1, figsize=(7.8, 5.4), sharex=True, constrained_layout=True)
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
    _configure_population_axis(axes[-1], users, categorical=True)
    axes[-1].set_xlabel("Users / monitored entities")
    fig.suptitle(title, fontsize=10, fontweight="normal")
    fig.colorbar(image, ax=axes, shrink=0.82, label=colorbar_label)
    fig.savefig(figures / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _query_metadata(run_dir: Path) -> tuple[dict[str, dict], dict]:
    snapshot = run_dir / "semantic-contract/queries/manifest.json"
    project = Path(__file__).resolve().parents[2] / "queries/manifest.json"
    source = snapshot if snapshot.is_file() else project
    if not source.is_file():
        return {}, {"source": None, "query_catalog_digest": None}
    manifest = json.loads(source.read_text())
    metadata = {str(item["id"]): item for item in manifest.get("queries", [])}
    return metadata, {
        "source": str(source),
        "query_catalog_digest": manifest.get("query_catalog_digest"),
    }


def _plot_query_categories(query_rows: list[dict], metadata: dict[str, dict], figures: Path) -> None:
    completed = [row for row in query_rows if row.get("status") == "completed" and _finite(row.get("duration_ms"))]
    grouped: dict[tuple[str, str], list[float]] = {}
    for row in completed:
        category = str(metadata.get(str(row.get("query_id")), {}).get("category", "uncategorized"))
        grouped.setdefault((category, str(row["layout"])), []).append(float(row["duration_ms"]))
    categories = sorted(
        {category for category, _layout in grouped},
        key=lambda category: max(
            (_percentile(grouped.get((category, layout), []), 95) or 0 for layout in LAYOUTS),
            default=0,
        ),
    )
    fig, ax = plt.subplots(figsize=(6.4, max(3.8, 0.35 * len(categories) + 1.3)))
    y = np.arange(len(categories))
    offsets = {"distributed": -0.16, "replicated": 0.16}
    for layout in LAYOUTS:
        p95 = [_percentile(grouped.get((category, layout), []), 95) or np.nan for category in categories]
        p50 = [_percentile(grouped.get((category, layout), []), 50) or np.nan for category in categories]
        ax.barh(
            y + offsets[layout], p95, height=0.28, color=COLORS[layout], alpha=0.78, label=f"{layout.capitalize()} p95"
        )
        ax.scatter(p50, y + offsets[layout], marker="|", s=80, linewidths=1.5, color="white", zorder=4)
    ax.set_yticks(y, [category.replace("_", " ") for category in categories])
    _finish(
        fig,
        ax,
        figures / "15_query_category_cost.png",
        "Logical query cost by category (bar: p95; white tick: p50)",
        "Latency (ms)",
        "Query category",
    )


def _plot_expensive_queries(query_rows: list[dict], metadata: dict[str, dict], figures: Path) -> None:
    grouped: dict[tuple[str, str], list[float]] = {}
    combined: dict[str, list[float]] = {}
    for row in query_rows:
        if row.get("status") != "completed" or not _finite(row.get("duration_ms")):
            continue
        query_id, layout = str(row.get("query_id")), str(row.get("layout"))
        value = float(row["duration_ms"])
        grouped.setdefault((query_id, layout), []).append(value)
        combined.setdefault(query_id, []).append(value)
    query_ids = sorted(combined, key=lambda query_id: _percentile(combined[query_id], 95) or 0, reverse=True)[:15]
    query_ids.reverse()
    fig, ax = plt.subplots(figsize=(6.5, 5.0))
    y = np.arange(len(query_ids))
    offsets = {"distributed": -0.12, "replicated": 0.12}
    for layout in LAYOUTS:
        values = [_percentile(grouped.get((query_id, layout), []), 95) or np.nan for query_id in query_ids]
        ax.scatter(
            values, y + offsets[layout], s=28, marker=MARKERS[layout], color=COLORS[layout], label=layout.capitalize()
        )
    ax.set_xscale("log")
    labels = [
        f"{query_id} · {str(metadata.get(query_id, {}).get('category', 'uncategorized')).replace('_', ' ')}"
        for query_id in query_ids
    ]
    ax.set_yticks(y, labels)
    _finish(
        fig,
        ax,
        figures / "16_most_expensive_queries.png",
        "Most expensive logical queries across the campaign",
        "p95 latency (ms)",
        "Logical query and category",
    )


def _plot_transfer_throughput(rows: list[dict], figures: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.7, 3.8))
    for layout in LAYOUTS:
        points = sorted(
            [
                row
                for row in rows
                if row["layout"] == layout
                and _finite(row.get("transfer_bytes_median"))
                and _finite(row.get("catalog_throughput_per_second"))
            ],
            key=lambda row: int(row["users"]),
        )
        if not points:
            continue
        x = [float(row["transfer_bytes_median"]) / 1024**2 for row in points]
        y = [float(row["catalog_throughput_per_second"]) for row in points]
        ax.plot(x, y, marker=MARKERS[layout], color=COLORS[layout], linewidth=1.4, label=layout.capitalize())
        labelled_users = {1, 500, 2000, 7000, max(int(row["users"]) for row in points)}
        if layout == "replicated":
            labelled_users.add(4000)
        for px, py, row in zip(x, y, points, strict=True):
            if int(row["users"]) not in labelled_users:
                continue
            user = int(row["users"])
            vertical_offset = 5 if user in {1, 500, 7000} else -10
            ax.annotate(
                str(row["users"]),
                (px, py),
                xytext=(4, vertical_offset),
                textcoords="offset points",
                fontsize=6.4,
                color=COLORS[layout],
            )
    ax.text(0.02, 0.03, "Point labels: users", transform=ax.transAxes, fontsize=7, color="#555")
    _finish(
        fig,
        ax,
        figures / "17_transfer_throughput_tradeoff.png",
        "Transferred knowledge versus logical throughput",
        "RDF payload per repetition (MiB)",
        "Logical queries/s",
    )


def _plot_layout_ratios(rows: list[dict], figures: Path) -> None:
    users = _users(rows)
    positions = np.arange(len(users))
    by_key = {(str(row["layout"]), int(row["users"])): row for row in rows}
    metrics = (
        ("preparation_seconds_median", "Preparation time"),
        ("query_latency_p95_ms", "Query p95 latency"),
        ("transfer_bytes_median", "Transferred payload"),
        ("cpu_seconds_median", "CPU time"),
    )
    fig, axes = plt.subplots(2, 2, figsize=(8.4, 5.8), sharex=True, sharey=True, constrained_layout=True)
    for ax, (field, title) in zip(axes.flat, metrics, strict=True):
        values = []
        for user in users:
            distributed = by_key.get(("distributed", user), {}).get(field)
            replicated = by_key.get(("replicated", user), {}).get(field)
            values.append(
                100.0 * (1.0 - float(distributed) / float(replicated))
                if _finite(distributed) and _finite(replicated) and float(replicated)
                else np.nan
            )
        values_array = np.asarray(values, dtype=float)
        ax.fill_between(
            positions,
            0,
            values_array,
            where=values_array >= 0,
            color="#3A923A",
            alpha=0.18,
            interpolate=True,
        )
        ax.fill_between(
            positions,
            0,
            values_array,
            where=values_array < 0,
            color="#C74343",
            alpha=0.18,
            interpolate=True,
        )
        point_colors = ["#277A36" if value >= 0 else "#B12D2D" for value in values_array]
        ax.plot(positions, values_array, color="#4B4B4B", linewidth=1.2, zorder=2)
        ax.scatter(positions, values_array, c=point_colors, s=24, zorder=3)
        ax.axhline(0.0, color="#555", linewidth=0.9, linestyle="--")
        ax.set_title(title, fontsize=9, fontweight="normal")
        ax.set_ylim(-110, 110)
        ax.grid(alpha=0.22)
        _configure_population_axis(ax, users, categorical=True)
    for ax in axes[-1]:
        ax.set_xlabel("Users / monitored entities")
    for ax in axes[:, 0]:
        ax.set_ylabel("Distributed cost reduction (%)")
    fig.suptitle(
        "Distributed cost relative to replication (positive values are reductions)",
        fontsize=10,
        fontweight="normal",
    )
    fig.savefig(figures / "18_distributed_cost_reduction.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_node_cpu_time(node_rows: list[dict], figures: Path, users: list[int], hosts: list[str]) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(8.4, 6.0), sharex=True)
    palette = plt.get_cmap(CATEGORY_COLOR_MAP)(np.linspace(0.05, 0.95, max(len(hosts), 1)))
    positions = np.arange(len(users))
    width = 0.36
    node_values: dict[tuple[str, str], np.ndarray] = {}
    for layout in LAYOUTS:
        by_key = {(str(row["host"]), int(row["users"])): row for row in node_rows if row["layout"] == layout}
        for host in hosts:
            node_values[(layout, host)] = np.asarray(
                [
                    float(by_key[(host, user)]["cpu_seconds_median"])
                    if (host, user) in by_key and _finite(by_key[(host, user)].get("cpu_seconds_median"))
                    else 0.0
                    for user in users
                ]
            )
    for layout, offset, hatch in (("distributed", -width / 2, ""), ("replicated", width / 2, "///")):
        absolute_bottom = np.zeros(len(users))
        totals = sum((node_values[(layout, host)] for host in hosts), start=np.zeros(len(users)))
        share_bottom = np.zeros(len(users))
        for host, color in zip(hosts, palette, strict=True):
            values = node_values[(layout, host)]
            shares = np.divide(values * 100, totals, out=np.zeros_like(values), where=totals > 0)
            axes[0].bar(
                positions + offset,
                values,
                width,
                bottom=absolute_bottom,
                color=color,
                edgecolor="white",
                linewidth=0.35,
                hatch=hatch,
            )
            axes[1].bar(
                positions + offset,
                shares,
                width,
                bottom=share_bottom,
                color=color,
                edgecolor="white",
                linewidth=0.35,
                hatch=hatch,
            )
            absolute_bottom += values
            share_bottom += shares
    axes[0].set_title("Absolute compute effort", fontsize=9, fontweight="normal")
    axes[0].set_ylabel("CPU time (s)")
    axes[1].set_title("Node share of measured compute", fontsize=9, fontweight="normal")
    axes[1].set_ylabel("CPU time share (%)")
    axes[1].set_ylim(0, 100)
    for ax in axes:
        ax.grid(axis="y", alpha=0.22)
    host_handles = [Patch(facecolor=color, label=host) for host, color in zip(hosts, palette, strict=True)]
    layout_handles = [
        Patch(facecolor="white", edgecolor="#555", label="Distributed"),
        Patch(facecolor="white", edgecolor="#555", hatch="///", label="Replicated"),
    ]
    fig.legend(handles=host_handles, loc="upper center", bbox_to_anchor=(0.5, 0.94), ncol=6, frameon=False, fontsize=7)
    fig.legend(
        handles=layout_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.895),
        ncol=2,
        frameon=False,
        fontsize=7,
    )
    _configure_population_axis(axes[-1], users, categorical=True)
    axes[-1].set_xlabel("Users / monitored entities")
    fig.suptitle("Measured compute contribution by continuum node", fontsize=10, fontweight="normal")
    fig.tight_layout(rect=(0, 0, 1, 0.89))
    fig.savefig(figures / "19_node_cpu_time_contribution.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_phase_metric(
    phase_rows: list[dict], figures: Path, filename: str, field: str, title: str, ylabel: str, scale: float = 1.0
) -> None:
    if not phase_rows:
        return
    users = sorted({int(row["users"]) for row in phase_rows})
    positions = np.arange(len(users))
    fig, axes = plt.subplots(2, 1, figsize=(7.8, 5.6), sharex=True, constrained_layout=True)
    styles = {"preparation": "-", "queries": "--"}
    for ax, layout in zip(axes, LAYOUTS, strict=True):
        by_key = {(int(row["users"]), str(row["phase"])): row for row in phase_rows if row["layout"] == layout}
        for phase in ("preparation", "queries"):
            values = [
                float(by_key[(user, phase)][field]) / scale
                if (user, phase) in by_key and _finite(by_key[(user, phase)].get(field))
                else np.nan
                for user in users
            ]
            if np.isfinite(values).any():
                ax.plot(positions, values, styles[phase], marker="o", linewidth=1.4, label=phase.capitalize())
        ax.set_title(layout.capitalize(), fontsize=9, fontweight="normal")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.22)
        handles, _ = ax.get_legend_handles_labels()
        if handles:
            ax.legend(frameon=False, fontsize=7)
    _configure_population_axis(axes[-1], users, categorical=True)
    axes[-1].set_xlabel("Users / monitored entities")
    fig.suptitle(title, fontsize=10, fontweight="normal")
    fig.savefig(figures / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _first_incomplete_position(rows: list[dict], users: list[int], layout: str) -> int | None:
    by_user = {int(row["users"]): row for row in rows if row["layout"] == layout}
    return next(
        (
            index
            for index, user in enumerate(users)
            if user in by_user
            and int(by_user[user].get("completed_repetitions", 0)) < int(by_user[user].get("repetitions", 0))
        ),
        None,
    )


def _shade_replication_failure_region(ax, rows: list[dict], users: list[int], *, label: bool = False) -> None:
    first = _first_incomplete_position(rows, users, "replicated")
    if first is None:
        return
    ax.axvspan(
        first - 0.45,
        len(users) - 0.55,
        color="#B22222",
        alpha=0.07,
        linewidth=0,
        label="Replicated OOM region" if label else None,
    )


def _plot_scalability_evidence_overview(rows: list[dict], figures: Path, memory_limit_mib: float | None) -> None:
    users = _users(rows)
    positions = np.arange(len(users))
    by_key = {(str(row["layout"]), int(row["users"])): row for row in rows}
    metrics = (
        ("ready_seconds_median", "Semantic readiness", "Median time (s)", 1.0),
        ("query_latency_p95_ms", "Logical query tail latency", "p95 latency (ms)", 1.0),
        ("catalog_throughput_per_second", "Logical throughput", "Queries/s", 1.0),
        ("memory_peak_bytes", "Peak container memory", "Peak memory (MiB)", 1024**2),
    )
    fig, axes = plt.subplots(2, 2, figsize=(8.4, 5.9), sharex=True, constrained_layout=True)
    for panel, (ax, (field, title, ylabel, scale)) in enumerate(zip(axes.flat, metrics, strict=True)):
        for layout in LAYOUTS:
            values = [
                float(by_key[(layout, user)][field]) / scale
                if (layout, user) in by_key and _finite(by_key[(layout, user)].get(field))
                else np.nan
                for user in users
            ]
            ax.plot(
                positions,
                values,
                color=COLORS[layout],
                marker=MARKERS[layout],
                markersize=4.2,
                linewidth=1.5,
                label=layout.capitalize(),
            )
            _mark_incomplete(
                ax,
                positions,
                [row for row in rows if row["layout"] == layout],
                users,
                add_label=False,
            )
        _shade_replication_failure_region(ax, rows, users, label=panel == 0)
        if field == "ready_seconds_median":
            ax.axhline(120, color="#666", linestyle="--", linewidth=0.9, label="120 s operational target")
        if field == "memory_peak_bytes" and memory_limit_mib:
            ax.axhline(
                memory_limit_mib,
                color="#7F1D1D",
                linestyle="--",
                linewidth=0.9,
                label=f"{memory_limit_mib:g} MiB limit",
            )
        ax.set_title(title, fontsize=9, fontweight="normal")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.22)
        _configure_population_axis(ax, users, categorical=True)
    for ax in axes[-1]:
        ax.set_xlabel("Users / monitored entities")
    handles, labels = [], []
    for ax in axes.flat:
        for handle, label in zip(*ax.get_legend_handles_labels(), strict=True):
            if label not in labels:
                handles.append(handle)
                labels.append(label)
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.075), ncol=3, frameon=False, fontsize=7.2)
    fig.suptitle("Scalability evidence: distributed versus replicated", fontsize=10, fontweight="normal", y=1.145)
    fig.savefig(figures / "22_scalability_evidence_overview.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_normalized_cost_growth(rows: list[dict], figures: Path) -> None:
    users = _users(rows)
    positions = np.arange(len(users))
    by_key = {(str(row["layout"]), int(row["users"])): row for row in rows}
    metrics = (
        ("ready_seconds_median", "Readiness"),
        ("query_latency_p95_ms", "Query p95"),
        ("transfer_bytes_median", "Transferred RDF"),
        ("cpu_seconds_median", "CPU time"),
    )
    reference = next(
        (
            user
            for user in users
            if all(
                _finite(by_key.get((layout, user), {}).get(field)) for layout in LAYOUTS for field, _title in metrics
            )
        ),
        None,
    )
    fig, axes = plt.subplots(2, 2, figsize=(8.4, 5.9), sharex=True, constrained_layout=True)
    if reference is None:
        for ax in axes.flat:
            ax.axis("off")
        axes.flat[0].text(0.5, 0.5, "No paired completed baseline", ha="center", va="center")
    else:
        for panel, (ax, (field, title)) in enumerate(zip(axes.flat, metrics, strict=True)):
            for layout in LAYOUTS:
                baseline = float(by_key[(layout, reference)][field])
                values = [
                    float(by_key[(layout, user)][field]) / baseline
                    if (layout, user) in by_key and _finite(by_key[(layout, user)].get(field))
                    else np.nan
                    for user in users
                ]
                ax.plot(
                    positions,
                    values,
                    color=COLORS[layout],
                    marker=MARKERS[layout],
                    markersize=4.2,
                    linewidth=1.5,
                    label=layout.capitalize(),
                )
            _shade_replication_failure_region(ax, rows, users, label=panel == 0)
            ax.axhline(1.0, color="#666", linestyle="--", linewidth=0.8)
            ax.set_yscale("log")
            ax.set_title(title, fontsize=9, fontweight="normal")
            ax.set_ylabel(f"Growth from {reference} users (×)")
            ax.grid(alpha=0.22, which="both")
            _configure_population_axis(ax, users, categorical=True)
        for ax in axes[-1]:
            ax.set_xlabel("Users / monitored entities")
        handles, labels = axes.flat[0].get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            loc="upper center",
            bbox_to_anchor=(0.5, 1.065),
            ncol=3,
            frameon=False,
            fontsize=7.2,
        )
    fig.suptitle("Normalized cost growth on completed repetitions", fontsize=10, fontweight="normal", y=1.125)
    fig.savefig(figures / "23_normalized_scaling_growth.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_capacity_frontier(rows: list[dict], figures: Path, memory_limit_mib: float | None) -> None:
    users = _users(rows)
    positions = np.arange(len(users))
    by_key = {(str(row["layout"]), int(row["users"])): row for row in rows}
    fig, axes = plt.subplots(2, 1, figsize=(8.0, 5.6), constrained_layout=True)
    for layout in LAYOUTS:
        memory = [
            float(by_key[(layout, user)]["memory_peak_bytes"]) / 1024**2
            if (layout, user) in by_key and _finite(by_key[(layout, user)].get("memory_peak_bytes"))
            else np.nan
            for user in users
        ]
        axes[0].plot(
            positions,
            memory,
            color=COLORS[layout],
            marker=MARKERS[layout],
            linewidth=1.5,
            label=f"{layout.capitalize()} measured peak",
        )
    failed_positions = [
        index
        for index, user in enumerate(users)
        if ("replicated", user) in by_key
        and int(by_key[("replicated", user)].get("completed_repetitions", 0))
        < int(by_key[("replicated", user)].get("repetitions", 0))
    ]
    if failed_positions and memory_limit_mib:
        axes[0].scatter(
            failed_positions,
            [memory_limit_mib] * len(failed_positions),
            marker="x",
            s=45,
            linewidths=1.6,
            color="#B22222",
            label="Replicated OOM (no completed measurement)",
            zorder=5,
        )
    if memory_limit_mib:
        axes[0].axhline(memory_limit_mib, color="#7F1D1D", linestyle="--", linewidth=0.9)
    _shade_replication_failure_region(axes[0], rows, users)
    axes[0].set_title("Memory pressure and observed OOM boundary", fontsize=9, fontweight="normal")
    axes[0].set_ylabel("Peak memory (MiB)")
    axes[0].grid(alpha=0.22)
    axes[0].legend(frameon=False, fontsize=7.0, ncol=2)
    _configure_population_axis(axes[0], users, categorical=True)

    maximum_completed = {}
    first_failed = {}
    for layout in LAYOUTS:
        layout_rows = sorted((row for row in rows if row["layout"] == layout), key=lambda row: int(row["users"]))
        complete = [
            int(row["users"])
            for row in layout_rows
            if int(row.get("completed_repetitions", 0)) == int(row.get("repetitions", 0))
        ]
        failed = [
            int(row["users"])
            for row in layout_rows
            if int(row.get("completed_repetitions", 0)) < int(row.get("repetitions", 0))
        ]
        maximum_completed[layout] = max(complete, default=0)
        first_failed[layout] = min(failed, default=None)
    y = np.arange(len(LAYOUTS))
    bars = axes[1].barh(y, [maximum_completed[layout] for layout in LAYOUTS], color=[COLORS[x] for x in LAYOUTS])
    axes[1].set_yticks(y, [layout.capitalize() for layout in LAYOUTS])
    axes[1].set_xlabel("Largest population with 3/3 measured repetitions")
    axes[1].set_title("Empirical completion frontier within the tested range", fontsize=9, fontweight="normal")
    axes[1].grid(axis="x", alpha=0.22)
    for bar, layout in zip(bars, LAYOUTS, strict=True):
        value = maximum_completed[layout]
        suffix = " (test limit)" if first_failed[layout] is None else f"; first OOM at {first_failed[layout]:,}"
        axes[1].text(
            value,
            bar.get_y() + bar.get_height() / 2,
            f" {value:,}{suffix}",
            va="center",
            fontsize=7.4,
        )
    axes[1].set_xlim(0, max(maximum_completed.values(), default=1) * 1.32)
    fig.suptitle("Capacity frontier under identical container limits", fontsize=10, fontweight="normal")
    fig.savefig(figures / "24_capacity_frontier_and_memory.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_paired_layout_advantage(rows: list[dict], figures: Path) -> None:
    by_key = {(str(row["layout"]), int(row["users"])): row for row in rows}
    comparable = sorted(
        user
        for user in _users(rows)
        if all(
            (layout, user) in by_key
            and int(by_key[(layout, user)].get("completed_repetitions", 0))
            == int(by_key[(layout, user)].get("repetitions", 0))
            for layout in LAYOUTS
        )
    )
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    if not comparable:
        ax.axis("off")
        ax.text(0.5, 0.5, "No paired completed population", ha="center", va="center")
    else:
        user = comparable[-1]
        distributed = by_key[("distributed", user)]
        replicated = by_key[("replicated", user)]
        metrics = (
            ("preparation_seconds_median", "Preparation time"),
            ("query_latency_p95_ms", "Query p95 latency"),
            ("transfer_bytes_median", "Transferred RDF"),
            ("cpu_seconds_median", "CPU time"),
            ("memory_peak_bytes", "Peak memory"),
        )
        reductions = [100.0 * (1.0 - float(distributed[field]) / float(replicated[field])) for field, _label in metrics]
        labels = [label for _field, label in metrics]
        y = np.arange(len(metrics))
        colors = ["#2E7D32" if value >= 0 else "#B22222" for value in reductions]
        bars = ax.barh(y, reductions, color=colors, alpha=0.88)
        ax.set_yticks(y, labels)
        ax.invert_yaxis()
        ax.axvline(0, color="#555", linewidth=0.8)
        ax.set_xlabel("Distributed cost reduction relative to replication (%)")
        ax.set_title(
            f"Paired advantage at {user:,} users (highest population completed by both layouts)",
            fontsize=10,
            fontweight="normal",
        )
        ax.grid(axis="x", alpha=0.22)
        for bar, value in zip(bars, reductions, strict=True):
            ax.text(
                value + (1.2 if value >= 0 else -1.2),
                bar.get_y() + bar.get_height() / 2,
                f"{value:.1f}%",
                va="center",
                ha="left" if value >= 0 else "right",
                fontsize=8,
            )
        lower = min(-5.0, min(reductions) - 8)
        upper = max(10.0, max(reductions) + 12)
        ax.set_xlim(lower, upper)
    fig.tight_layout()
    fig.savefig(figures / "25_paired_layout_advantage.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def report(run_dir: Path) -> Path:
    summary, figures = run_dir / "summary", run_dir / "figures"
    summary.mkdir(exist_ok=True)
    figures.mkdir(exist_ok=True)
    for old in figures.glob("*.png"):
        old.unlink()

    grouped: dict[tuple[int, str], list[dict]] = {}
    query_rows, physical_query_rows, catalog_rows, resource_rows, preparation_rows, failures = [], [], [], [], [], []
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
                    "parse_and_digest_seconds": prepared.get("parse_and_digest_seconds"),
                    "store_load_seconds": prepared.get("store_load_seconds"),
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
        ppath = result_path.with_name("physical_queries.json")
        if ppath.is_file():
            physical_query_rows.extend(json.loads(ppath.read_text()))
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

    rows, node_rows, phase_rows = [], [], []
    for (users, layout), reps in sorted(grouped.items()):
        complete = [result for result in reps if result["status"].startswith("completed")]
        complete_ids = {int(result["repetition"]) for result in complete}
        prepares = [float(result["preparation_seconds"]) for result in complete]
        ready = [float(result["ready_seconds"]) for result in complete if result.get("ready_seconds") is not None]
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
        physical_queries = [
            float(row.get("request_duration_ms", row["duration_ms"]))
            for row in physical_query_rows
            if row.get("layout") == layout
            and row.get("users") == users
            and int(row.get("repetition", 0)) in complete_ids
            and row["status"] == "completed"
        ]
        fanouts = [
            int(row.get("fanout_size", len(row.get("participants", []))))
            for row in query_rows
            if row["layout"] == layout
            and row.get("users") == users
            and int(row.get("repetition", 0)) in complete_ids
            and row["status"] == "completed"
        ]
        logical_timeouts = sum(
            row["layout"] == layout and row.get("users") == users and row.get("status") == "query_timeout"
            for row in query_rows
        )
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
            _failure_cause(str(result.get("error", "")), str(result.get("status", "")))
            for result in reps
            if result["status"] in FAILURE_STATUSES
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
                "ready_seconds_median": median(ready) if ready else None,
                "ready_seconds_min": min(ready) if ready else None,
                "ready_seconds_max": max(ready) if ready else None,
                "partition_seconds_median": median(partitions) if partitions else None,
                "serialize_seconds_median": median(serializes) if serializes else None,
                "transfer_seconds_median": median(transfers) if transfers else None,
                "remote_load_seconds_median": median(remote_loads) if remote_loads else None,
                "reasoning_seconds_median": median(reasoning) if reasoning else None,
                "transfer_bytes_median": median(payload) if payload else None,
                "query_latency_p50_ms": _percentile(queries, 50),
                "query_latency_p95_ms": _percentile(queries, 95),
                "query_latency_p99_ms": _percentile(queries, 99),
                "physical_query_latency_p50_ms": _percentile(physical_queries, 50),
                "physical_query_latency_p95_ms": _percentile(physical_queries, 95),
                "fanout_size_median": median(fanouts) if fanouts else None,
                "logical_query_timeouts": logical_timeouts,
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
            host_cpu_seconds = []
            for repetition in complete_ids:
                values = [
                    float(row["cpu_usage_seconds"])
                    for row in samples
                    if int(row["repetition"]) == repetition and row.get("cpu_usage_seconds") is not None
                ]
                if values:
                    host_cpu_seconds.append(max(values) - min(values))
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
                    "cpu_seconds_median": median(host_cpu_seconds) if host_cpu_seconds else None,
                }
            )
        for phase in ("preparation", "queries"):
            samples = [row for row in resources if row.get("phase") == phase]
            phase_cpu = [float(row["cpu_percent"]) for row in samples]
            phase_memory = [float(row["memory_bytes"]) for row in samples if row.get("memory_bytes") is not None]
            cpu_seconds_by_rep: list[float] = []
            for repetition in complete_ids:
                total = 0.0
                found = False
                for host in {str(row["host"]) for row in samples}:
                    values = [
                        float(row["cpu_usage_seconds"])
                        for row in samples
                        if int(row["repetition"]) == repetition
                        and row["host"] == host
                        and row.get("cpu_usage_seconds") is not None
                    ]
                    if values:
                        total += max(values) - min(values)
                        found = True
                if found:
                    cpu_seconds_by_rep.append(total)
            if phase_cpu or phase_memory:
                phase_rows.append(
                    {
                        "users": users,
                        "layout": layout,
                        "phase": phase,
                        "samples": len(samples),
                        "cpu_mean_percent": float(np.mean(phase_cpu)) if phase_cpu else None,
                        "cpu_p95_percent": _percentile(phase_cpu, 95),
                        "cpu_peak_percent": max(phase_cpu) if phase_cpu else None,
                        "cpu_seconds_median": median(cpu_seconds_by_rep) if cpu_seconds_by_rep else None,
                        "memory_mean_bytes": float(np.mean(phase_memory)) if phase_memory else None,
                        "memory_p95_bytes": _percentile(phase_memory, 95),
                        "memory_peak_bytes": max(phase_memory) if phase_memory else None,
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
        ("physical_queries.csv", physical_query_rows),
        ("resources.csv", resource_rows),
        ("node_resources.csv", node_rows),
        ("phase_resources.csv", phase_rows),
        ("failures.csv", failures),
    ):
        _write_csv(summary / name, data)
    cause_rows = [
        {"cause": cause, "count": count}
        for cause, count in sorted(
            Counter(_failure_cause(str(row.get("error", "")), str(row.get("status", ""))) for row in failures).items()
        )
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
        "ready_seconds_median",
        "End-to-end time until all workers are semantically ready",
        "Median seconds",
    )

    users = _users(rows)
    category_positions = np.arange(len(users))
    width = 0.36
    phases = (
        ("partition_seconds_median", "Partition", "#4C78A8"),
        ("serialize_seconds_median", "Serialize", "#F58518"),
        ("transfer_seconds_median", "Transfer", "#54A24B"),
        ("remote_load_seconds_median", "Remote load", "#E45756"),
    )
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
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
                category_positions + offset,
                values,
                width,
                bottom=bottom,
                color=color,
                edgecolor="white",
                hatch=hatch,
                label=label if layout == "distributed" else None,
            )
            bottom += np.nan_to_num(values)
        _mark_incomplete(ax, category_positions + offset, layout_rows, users, add_label=layout == "distributed")
    _configure_population_axis(ax, users, categorical=True)
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
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
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
                    category_positions,
                    values,
                    linestyle=style,
                    marker=MARKERS[layout],
                    color=COLORS[layout],
                    linewidth=1.5,
                    label=f"{layout.capitalize()} {label}",
                )
        _mark_incomplete(ax, category_positions, layout_rows, users, add_label=layout == "distributed")
    _configure_population_axis(ax, users, categorical=True)
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
        fig, axes = plt.subplots(2, 1, figsize=(7.8, 5.6), sharex=True, constrained_layout=True)
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
                    ax.plot(category_positions, values, marker="o", linewidth=1.4, label=label)
            _mark_incomplete(ax, category_positions, layout_rows, users, add_label=True)
            _configure_population_axis(ax, users, categorical=True)
            ax.set_ylabel(unit)
            ax.set_title(layout.capitalize(), fontsize=9, fontweight="normal")
            ax.grid(alpha=0.22)
            handles, _ = ax.get_legend_handles_labels()
            if handles:
                ax.legend(frameon=False, fontsize=7, ncol=4)
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
    fig, ax = plt.subplots(figsize=(8.0, 2.8))
    image = ax.imshow(matrix, vmin=0, vmax=1, cmap="RdYlGn", aspect="auto")
    _configure_population_axis(ax, users, categorical=True)
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

    fig, ax = plt.subplots(figsize=(8.0, 4.1))
    for layout, offset in (("distributed", -width / 2), ("replicated", width / 2)):
        layout_rows = {int(row["users"]): row for row in rows if row["layout"] == layout}
        completed = [int(layout_rows.get(user, {}).get("completed_repetitions", 0)) for user in users]
        failed = [int(layout_rows.get(user, {}).get("failures", 0)) for user in users]
        ax.bar(
            category_positions + offset,
            completed,
            width,
            color=COLORS[layout],
            label=f"{layout.capitalize()} completed",
        )
        ax.bar(
            category_positions + offset,
            failed,
            width,
            bottom=completed,
            facecolor="white",
            edgecolor=COLORS[layout],
            hatch="xx",
            label=f"{layout.capitalize()} failed",
        )
    _configure_population_axis(ax, users, categorical=True)
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
    query_metadata, metadata_provenance = _query_metadata(run_dir)
    _plot_query_categories(query_rows, query_metadata, figures)
    _plot_expensive_queries(query_rows, query_metadata, figures)
    _plot_transfer_throughput(rows, figures)
    _plot_layout_ratios(rows, figures)
    _plot_node_cpu_time(node_rows, figures, users, all_hosts)
    _plot_phase_metric(
        phase_rows,
        figures,
        "20_cpu_by_phase.png",
        "cpu_p95_percent",
        "Container CPU p95 by measured phase",
        "CPU p95 (%)",
    )
    _plot_phase_metric(
        phase_rows,
        figures,
        "21_memory_by_phase.png",
        "memory_peak_bytes",
        "Peak container memory by measured phase",
        "Peak memory (MiB)",
        1024**2,
    )
    configuration_path = run_dir / "configuration.toml"
    memory_limit_mib = None
    if configuration_path.is_file():
        configuration = tomllib.loads(configuration_path.read_text(encoding="utf-8"))
        memory_limit_mib = float(configuration.get("deployment", {}).get("memory_mib_per_container", 0)) or None
    _plot_scalability_evidence_overview(rows, figures, memory_limit_mib)
    _plot_normalized_cost_growth(rows, figures)
    _plot_capacity_frontier(rows, figures, memory_limit_mib)
    _plot_paired_layout_advantage(rows, figures)

    campaign_manifest_path = run_dir / "manifest.json"
    campaign_manifest = json.loads(campaign_manifest_path.read_text()) if campaign_manifest_path.is_file() else {}
    campaign_digest = campaign_manifest.get("query_catalog_digest")
    figure_files = sorted(path.name for path in figures.glob("*.png"))
    (figures / "manifest.json").write_text(
        json.dumps(
            {
                "figure_count": len(figure_files),
                "figures": figure_files,
                "query_metadata_source": metadata_provenance["source"],
                "query_metadata_digest": metadata_provenance["query_catalog_digest"],
                "campaign_query_catalog_digest": campaign_digest,
                "query_metadata_matches_campaign": bool(campaign_digest)
                and campaign_digest == metadata_provenance["query_catalog_digest"],
            },
            indent=2,
        )
        + "\n"
    )
    (summary / "summary.json").write_text(json.dumps(rows, indent=2) + "\n")
    return summary
