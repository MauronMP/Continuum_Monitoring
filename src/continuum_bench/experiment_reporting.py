from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Iterable

import matplotlib.pyplot as plt


REASONER_LABELS = {
    "rdfs": "RDFS",
    "owlrl": "OWL RL",
    "rdfs_owlrl": "RDFS + OWL RL",
}


def _rows(root: Path, experiment: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for architecture in ("docker", "physical"):
        path = root / architecture / experiment / "summary.csv"
        if path.is_file():
            with path.open(encoding="utf-8", newline="") as handle:
                rows.extend(
                    {**row, "architecture": architecture}
                    for row in csv.DictReader(handle)
                    if row.get("status") == "completed"
                )
    return rows


def _save(figure: plt.Figure, base: Path) -> list[Path]:
    base.parent.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for suffix in (".png", ".pdf", ".svg"):
        path = base.with_suffix(suffix)
        figure.savefig(
            path,
            dpi=300 if suffix == ".png" else None,
            bbox_inches="tight",
        )
        outputs.append(path)
    plt.close(figure)
    return outputs


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
        for architecture in ("docker", "physical"):
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
                        label=f"{architecture}:{role}",
                    )
            axis.set_title(REASONER_LABELS.get(reasoner, reasoner))
            axis.set_xlabel(dimension.replace("_", " "))
            axis.grid(True, alpha=0.25)
        axes[0][0].set_ylabel("Reasoning time (s)")
        axes[0][-1].legend(frameon=False, fontsize=8)
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
        for architecture in ("docker", "physical"):
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


def plot_experiments(root: Path, selected: Iterable[str]) -> list[Path]:
    outputs: list[Path] = []
    selected_set = set(selected)
    if "scale-out" in selected_set:
        outputs.extend(plot_scale_out(root))
    if "reasoning-hardware" in selected_set:
        outputs.extend(plot_reasoning_hardware(root))
    if "distributed-ontology" in selected_set:
        outputs.extend(plot_distributed_ontology(root))
    return outputs


def plot_claim_analysis(root: Path) -> list[Path]:
    from .experiment_analysis import analyze_experiments

    analyze_experiments(root)
    return plot_experiments(root, ("scale-out", "reasoning-hardware", "distributed-ontology"))
