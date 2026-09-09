from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Iterable

from ..plot_environment import configure_matplotlib

configure_matplotlib()
import matplotlib.pyplot as plt

from ..csv_utils import write_dict_rows


REASONER_LABELS = {
    "rdfs": "RDFS",
    "owlrl": "OWL RL",
    "rdfs_owlrl": "RDFS + OWL RL",
}
ARCHITECTURES = ("physical",)


def _rows(root: Path, experiment: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for architecture in ARCHITECTURES:
        path = root / architecture / experiment / "summary.csv"
        if path.is_file():
            with path.open(encoding="utf-8", newline="") as handle:
                rows.extend(
                    {**row, "architecture": architecture}
                    for row in csv.DictReader(handle)
                    if row.get("status") == "completed"
                )
    return rows


def _quality_rows(
    root: Path,
    experiments: Iterable[str],
) -> list[dict[str, str | int | float]]:
    groups: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for architecture in ARCHITECTURES:
        for experiment in experiments:
            path = root / architecture / experiment / "summary.csv"
            if not path.is_file():
                continue
            with path.open(encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    reasoner = row.get("reasoner", "unknown")
                    groups[(architecture, experiment, reasoner)].append(
                        row.get("status", "unknown")
                    )
    output: list[dict[str, str | int | float]] = []
    for (architecture, experiment, reasoner), statuses in sorted(
        groups.items()
    ):
        completed = sum(status == "completed" for status in statuses)
        timeout = sum("timeout" in status and not status.startswith("skipped") for status in statuses)
        skipped = sum(status.startswith("skipped") for status in statuses)
        failed = len(statuses) - completed - timeout - skipped
        output.append(
            {
                "architecture": architecture,
                "experiment": experiment,
                "reasoner": reasoner,
                "samples": len(statuses),
                "completed_samples": completed,
                "timeout_samples": timeout,
                "skipped_samples": skipped,
                "skipped_rate_percent": skipped / len(statuses) * 100,
                "failed_or_other_samples": failed,
                "completion_rate_percent": completed / len(statuses) * 100,
                "timeout_rate_percent": timeout / len(statuses) * 100,
                "failed_or_other_rate_percent": failed / len(statuses) * 100,
            }
        )
    return output


def _save(figure, base):
    from .figure_style import save_png
    return save_png(figure, base)


def _median_groups(
    rows: Iterable[dict[str, str]],
    keys: tuple[str, ...],
    value: str,
) -> dict[tuple[str, ...], float]:
    groups: dict[tuple[str, ...], list[float]] = defaultdict(list)
    for row in rows:
        raw = row.get(value, "")
        if raw != "":
            groups[tuple(row[key] for key in keys)].append(float(raw))
    return {key: median(samples) for key, samples in groups.items()}


def plot_scale_out(root: Path) -> list[Path]:
    rows = _rows(root, "scale-out")
    if not rows:
        return []
    reasoners = sorted({row["reasoner"] for row in rows})
    figure, axes = plt.subplots(
        1,
        len(reasoners),
        figsize=(5.0 * len(reasoners), 4.0),
        squeeze=False,
        sharey=True,
    )
    values = _median_groups(
        rows, ("architecture", "reasoner", "node_count"), "queries_per_second"
    )
    for column, reasoner in enumerate(reasoners):
        axis = axes[0][column]
        for architecture in ARCHITECTURES:
            points = sorted(
                (int(nodes), value)
                for (item_architecture, item_reasoner, nodes), value in values.items()
                if item_architecture == architecture and item_reasoner == reasoner
            )
            if points:
                axis.plot(
                    [item[0] for item in points],
                    [item[1] for item in points],
                    marker="o", linewidth=2, label=architecture,
                )
        axis.set_title(REASONER_LABELS.get(reasoner, reasoner))
        axis.set_xlabel("Active nodes")
        axis.set_xticks(sorted({int(row["node_count"]) for row in rows}))
        if len({row["node_count"] for row in rows}) == 1:
            axis.text(.5,.05,"Only one node count completed",transform=axis.transAxes,ha="center",fontsize=8)
        axis.grid(True, alpha=0.25)
    axes[0][0].set_ylabel("Processed queries/s")
    axes[0][-1].legend(frameon=False)
    figure.suptitle("Query scale-out by architecture", fontweight="bold")
    return _save(figure, root / "figures" / "architecture-scale-out")


def plot_reasoning_hardware(root: Path) -> list[Path]:
    rows = _rows(root, "reasoning-hardware")
    if not rows:
        return []
    outputs: list[Path] = []
    for dimension in ("target_triples", "rule_count", "users"):
        selected = [row for row in rows if row.get("dimension") == dimension]
        if not selected:
            continue
        reasoners = sorted({row["reasoner"] for row in selected})
        figure, axes = plt.subplots(
            1,
            len(reasoners),
            figsize=(5.0 * len(reasoners), 4.0),
            squeeze=False,
            sharey=True,
        )
        values = _median_groups(
            selected,
            ("architecture", "reasoner", "role", "dimension_value"),
            "reasoning_ms",
        )
        node_keys=sorted({(row["architecture"],row["role"]) for row in selected})
        node_colors={key:plt.get_cmap("tab10")(i) for i,key in enumerate(node_keys)}
        for column, reasoner in enumerate(reasoners):
            axis = axes[0][column]
            for architecture, role in sorted(
                {(row["architecture"], row["role"]) for row in selected}
            ):
                points = sorted(
                    (int(value), sample / 1000)
                    for (item_architecture, item_reasoner, item_role, value), sample
                    in values.items()
                    if item_architecture == architecture
                    and item_reasoner == reasoner and item_role == role
                )
                if points:
                    axis.plot(
                        [item[0] for item in points],
                        [item[1] for item in points],
                        marker="o",
                        linewidth=2,
                        label=f"{role}",
                        color=node_colors[(architecture,role)],
                    )
            axis.set_title(REASONER_LABELS.get(reasoner, reasoner))
            axis.set_xlabel(dimension.replace("_", " "))
            axis.grid(True, alpha=0.25)
        axes[0][0].set_ylabel("Reasoning time (s)")
        handles={}
        for axis in axes[0]:
            artists,labels=axis.get_legend_handles_labels()
            handles.update(zip(labels,artists))
        figure.legend(handles.values(),handles.keys(),loc="lower center",ncol=5,frameon=False,fontsize=9)
        figure.subplots_adjust(bottom=.22)
        figure.suptitle(f"Reasoning cost by architecture and node: {dimension}", fontweight="bold")
        outputs.extend(_save(figure, root / "figures" / f"architecture-hardware-{dimension}"))
    return outputs


def plot_distributed_ontology(root: Path) -> list[Path]:
    rows = _rows(root, "distributed-ontology")
    if not rows:
        return []
    reasoners = sorted({row["reasoner"] for row in rows})
    figure, axes = plt.subplots(
        1,
        len(reasoners),
        figsize=(5.0 * len(reasoners), 4.0),
        squeeze=False,
        sharey=True,
    )
    values = _median_groups(
        rows,
        ("architecture", "reasoner", "synthetic_users"),
        "total_wall_ms",
    )
    for column, reasoner in enumerate(reasoners):
        axis = axes[0][column]
        for architecture in ARCHITECTURES:
            points = sorted(
                (int(users), value / 1000)
                for (item_architecture, item_reasoner, users), value in values.items()
                if item_architecture == architecture and item_reasoner == reasoner
            )
            if points:
                axis.plot(
                    [item[0] for item in points],
                    [item[1] for item in points],
                    marker="o", linewidth=2, label=architecture,
                )
        axis.set_title(REASONER_LABELS.get(reasoner, reasoner))
        axis.set_xlabel("Synthetic users")
        axis.grid(True, alpha=0.25)
    axes[0][0].set_ylabel("Total wall time (s)")
    axes[0][-1].legend(frameon=False)
    figure.suptitle("Distributed ontology by architecture", fontweight="bold")
    return _save(figure, root / "figures" / "architecture-distributed-ontology")


def plot_experiment_coverage(
    root: Path,
    experiments: Iterable[str],
) -> list[Path]:
    """Plot completed, timeout and other outcomes without hiding censoring."""

    rows = _quality_rows(root, experiments)
    if not rows:
        return []
    table = root / "analysis" / "experiment-data-quality.csv"
    write_dict_rows(table, rows, empty_message="No experiment quality rows")
    labels = [
        f"{row['architecture']} · {row['experiment']} · "
        f"{REASONER_LABELS.get(str(row['reasoner']), row['reasoner'])}"
        for row in rows
    ]
    completed = [float(row["completion_rate_percent"]) for row in rows]
    timeout = [float(row["timeout_rate_percent"]) for row in rows]
    failed = [float(row["failed_or_other_rate_percent"]) for row in rows]
    skipped = [float(row["skipped_rate_percent"]) for row in rows]
    positions = list(range(len(rows)))
    figure, axis = plt.subplots(
        figsize=(10.5, max(3.2, 0.34 * len(rows) + 1.5))
    )
    axis.barh(positions, completed, color="#2E8B57", label="Completed")
    axis.barh(
        positions,
        timeout,
        left=completed,
        color="#E69F00",
        label="Timeout/censored",
    )
    failed_left = [
        completed_value + timeout_value
        for completed_value, timeout_value in zip(
            completed, timeout, strict=True
        )
    ]
    axis.barh(positions, skipped, left=failed_left, color="#999999", label="Skipped (not executed)")
    failed_left = [a+b for a,b in zip(failed_left, skipped)]
    axis.barh(
        positions,
        failed,
        left=failed_left,
        color="#D55E00",
        label="Failed/other",
    )
    for position, row in zip(positions, rows, strict=True):
        axis.text(
            101,
            position,
            f"n={row['samples']}",
            va="center",
            fontsize=7,
        )
    axis.set_yticks(positions)
    axis.set_yticklabels(labels, fontsize=7)
    axis.set_xlim(0, 108)
    axis.set_xlabel("Observed outcomes (%)")
    axis.grid(True, axis="x", alpha=0.25)
    axis.legend(
        frameon=False,
        ncol=4,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.01),
    )
    figure.tight_layout()
    return [table, *_save(figure, root / "figures" / "experiment-data-coverage")]


def plot_experiments(root: Path, selected: Iterable[str]) -> list[Path]:
    outputs: list[Path] = []
    selected_set = set(selected)
    if "scale-out" in selected_set:
        outputs.extend(plot_scale_out(root))
    if "reasoning-hardware" in selected_set:
        outputs.extend(plot_reasoning_hardware(root))
    if "distributed-ontology" in selected_set:
        outputs.extend(plot_distributed_ontology(root))
    outputs.extend(plot_experiment_coverage(root, selected_set))
    return outputs


def plot_claim_analysis(root: Path) -> list[Path]:
    from .experiment_analysis import analyze_experiments

    analyze_experiments(root)
    return plot_experiments(root, ("scale-out", "reasoning-hardware", "distributed-ontology"))
