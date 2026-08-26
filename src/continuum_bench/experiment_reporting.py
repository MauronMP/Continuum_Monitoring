from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Iterable

import matplotlib.pyplot as plt


ARCHITECTURE_LABELS = {
    "monolith": "Monolito",
    "docker": "Docker Compose",
    "physical": "Continuum físico",
}
REASONER_LABELS = {
    "rdfs": "RDFS",
    "owlrl": "OWL RL",
    "rdfs_owlrl": "RDFS + OWL RL",
}
COLORS = {
    "monolith": "#1f77b4",
    "docker": "#ff7f0e",
    "physical": "#2ca02c",
    "physical-cloud": "#9467bd",
    "physical-raspberry": "#2ca02c",
}


def _rows(root: Path, experiment: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for architecture in ("monolith", "docker", "physical"):
        path = root / architecture / experiment / "summary.csv"
        if path.is_file():
            with path.open(encoding="utf-8", newline="") as handle:
                rows.extend(csv.DictReader(handle))
    return [row for row in rows if row.get("status") == "completed"]


def _csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _save(figure: plt.Figure, base: Path) -> list[Path]:
    base.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for suffix in (".png", ".pdf", ".svg"):
        path = base.with_suffix(suffix)
        figure.savefig(
            path,
            dpi=300 if suffix == ".png" else None,
            bbox_inches="tight",
        )
        paths.append(path)
    plt.close(figure)
    return paths


def _median_groups(
    rows: Iterable[dict[str, str]],
    keys: tuple[str, ...],
    value: str,
) -> dict[tuple[str, ...], float]:
    groups: dict[tuple[str, ...], list[float]] = defaultdict(list)
    for row in rows:
        if row.get(value, "") != "":
            groups[tuple(row[key] for key in keys)].append(float(row[value]))
    return {key: median(values) for key, values in groups.items()}


def plot_scale_out(root: Path) -> list[Path]:
    rows = _rows(root, "scale-out")
    if not rows:
        return []
    reasoners = sorted({row["reasoner"] for row in rows})
    figure, axes = plt.subplots(
        1,
        len(reasoners),
        figsize=(5.2 * len(reasoners), 4.2),
        squeeze=False,
        sharey=True,
    )
    values = _median_groups(
        rows,
        ("reasoner", "architecture", "node_count"),
        "queries_per_second",
    )
    for column, reasoner in enumerate(reasoners):
        axis = axes[0][column]
        for architecture in ("monolith", "docker", "physical"):
            points = sorted(
                (
                    int(nodes),
                    value,
                )
                for (item_reasoner, item_architecture, nodes), value
                in values.items()
                if item_reasoner == reasoner
                and item_architecture == architecture
            )
            if points:
                axis.plot(
                    [item[0] for item in points],
                    [item[1] for item in points],
                    marker="o",
                    linewidth=2,
                    label=ARCHITECTURE_LABELS[architecture],
                    color=COLORS[architecture],
                )
        axis.set_title(REASONER_LABELS.get(reasoner, reasoner))
        axis.set_xlabel("Nodos activos")
        axis.grid(True, alpha=0.25)
    axes[0][0].set_ylabel("Consultas procesadas/s")
    axes[0][-1].legend(frameon=False)
    figure.suptitle(
        "Scale-out de consultas (preparación excluida)",
        fontweight="bold",
    )
    return _save(figure, root / "figures" / "experiment-scale-out")


def _hardware_group(row: dict[str, str]) -> str:
    architecture = row["architecture"]
    if architecture != "physical":
        return architecture
    return "physical-cloud" if row["role"] == "cloud" else "physical-raspberry"


def plot_reasoning_hardware(root: Path) -> list[Path]:
    rows = _rows(root, "reasoning-hardware")
    if not rows:
        return []
    output: list[Path] = []
    labels = {
        "monolith": "PC monolítico",
        "docker": "Contenedor Docker (mediana)",
        "physical-cloud": "Cloud físico (PC)",
        "physical-raspberry": "Raspberry Pi (mediana)",
    }
    for dimension in ("target_triples", "rule_count", "users"):
        selected = [row for row in rows if row["dimension"] == dimension]
        if not selected:
            continue
        reasoners = sorted({row["reasoner"] for row in selected})
        figure, axes = plt.subplots(
            1,
            len(reasoners),
            figsize=(5.2 * len(reasoners), 4.2),
            squeeze=False,
            sharey=True,
        )
        groups: dict[tuple[str, str, int], list[float]] = defaultdict(list)
        for row in selected:
            groups[
                (
                    row["reasoner"],
                    _hardware_group(row),
                    int(row["dimension_value"]),
                )
            ].append(float(row["reasoning_ms"]) / 1000)
        for column, reasoner in enumerate(reasoners):
            axis = axes[0][column]
            for group in labels:
                points = sorted(
                    (value, median(samples))
                    for (item_reasoner, item_group, value), samples
                    in groups.items()
                    if item_reasoner == reasoner and item_group == group
                )
                if points:
                    axis.plot(
                        [item[0] for item in points],
                        [item[1] for item in points],
                        marker="o",
                        linewidth=2,
                        label=labels[group],
                        color=COLORS[group],
                    )
            axis.set_title(REASONER_LABELS.get(reasoner, reasoner))
            axis.set_xlabel(
                {
                    "target_triples": "Triples afirmados",
                    "rule_count": "Reglas sintéticas",
                    "users": "Usuarios sintéticos",
                }[dimension]
            )
            axis.grid(True, alpha=0.25)
        axes[0][0].set_ylabel("Tiempo de razonamiento (s)")
        axes[0][-1].legend(frameon=False, fontsize=8)
        figure.suptitle(
            f"Escalabilidad del razonamiento por hardware: {dimension}",
            fontweight="bold",
        )
        output.extend(
            _save(
                figure,
                root / "figures" / f"experiment-hardware-{dimension}",
            )
        )
    return output


def plot_distributed_ontology(root: Path) -> list[Path]:
    rows = _rows(root, "distributed-ontology")
    if not rows:
        return []
    reasoners = sorted({row["reasoner"] for row in rows})
    figure, axes = plt.subplots(
        len(reasoners),
        2,
        figsize=(11, 3.7 * len(reasoners)),
        squeeze=False,
    )
    for row_index, reasoner in enumerate(reasoners):
        for column, (field, ylabel) in enumerate(
            (
                ("prepare_wall_ms", "Preparación e inferencia (s)"),
                ("query_wall_ms", "Consultas federadas (s)"),
            )
        ):
            axis = axes[row_index][column]
            groups = _median_groups(
                [
                    row
                    for row in rows
                    if row["reasoner"] == reasoner
                ],
                ("architecture", "synthetic_users"),
                field,
            )
            for architecture in ("monolith", "docker", "physical"):
                points = sorted(
                    (int(users), value / 1000)
                    for (item_architecture, users), value in groups.items()
                    if item_architecture == architecture
                )
                if points:
                    axis.plot(
                        [item[0] for item in points],
                        [item[1] for item in points],
                        marker="o",
                        linewidth=2,
                        label=ARCHITECTURE_LABELS[architecture],
                        color=COLORS[architecture],
                    )
            axis.set_title(
                f"{REASONER_LABELS.get(reasoner, reasoner)} · {ylabel}"
            )
            axis.set_xlabel("Usuarios sintéticos del dataset lógico")
            axis.set_ylabel(ylabel)
            axis.grid(True, alpha=0.25)
    axes[0][-1].legend(frameon=False)
    figure.suptitle(
        "Ontología distribuida: mismo dataset lógico",
        fontweight="bold",
    )
    return _save(
        figure,
        root / "figures" / "experiment-distributed-ontology",
    )


def plot_experiments(
    root: Path,
    experiments: tuple[str, ...] = (
        "scale-out",
        "reasoning-hardware",
        "distributed-ontology",
    ),
) -> list[Path]:
    paths: list[Path] = []
    if "scale-out" in experiments:
        paths.extend(plot_scale_out(root))
    if "reasoning-hardware" in experiments:
        paths.extend(plot_reasoning_hardware(root))
    if "distributed-ontology" in experiments:
        paths.extend(plot_distributed_ontology(root))
    return paths


def plot_claim_analysis(root: Path) -> list[Path]:
    scale_rows = _csv(root / "analysis" / "scale-out-comparison.csv")
    distributed_rows = _csv(
        root / "analysis" / "distributed-comparison.csv"
    )
    output: list[Path] = []
    if scale_rows:
        reasoners = sorted({row["reasoner"] for row in scale_rows})
        figure, axes = plt.subplots(
            1,
            len(reasoners),
            figsize=(5.2 * len(reasoners), 4.2),
            squeeze=False,
            sharey=True,
        )
        for column, reasoner in enumerate(reasoners):
            axis = axes[0][column]
            for architecture in ("docker", "physical"):
                points = sorted(
                    (
                        int(row["node_count"]),
                        float(row["throughput_speedup_vs_own_1_node"]),
                    )
                    for row in scale_rows
                    if row["reasoner"] == reasoner
                    and row["architecture"] == architecture
                    and row.get("fully_complete") == "True"
                    and row.get("semantic_equivalent_to_monolith") == "True"
                    and row.get("throughput_speedup_vs_own_1_node", "")
                    != ""
                )
                if points:
                    axis.plot(
                        [point[0] for point in points],
                        [point[1] for point in points],
                        marker="o",
                        linewidth=2,
                        label=ARCHITECTURE_LABELS[architecture],
                        color=COLORS[architecture],
                    )
            axis.axhline(1.0, color="#555555", linestyle="--", linewidth=1)
            axis.set_title(REASONER_LABELS.get(reasoner, reasoner))
            axis.set_xlabel("Nodos activos")
            axis.grid(True, alpha=0.25)
        axes[0][0].set_ylabel("Speedup throughput vs 1 nodo")
        axes[0][-1].legend(frameon=False)
        figure.suptitle(
            "Eficacia del scale-out de consultas",
            fontweight="bold",
        )
        output.extend(
            _save(figure, root / "figures" / "experiment-scale-out-speedup")
        )
    if distributed_rows:
        reasoners = sorted({row["reasoner"] for row in distributed_rows})
        figure, axes = plt.subplots(
            1,
            len(reasoners),
            figsize=(5.2 * len(reasoners), 4.2),
            squeeze=False,
            sharey=True,
        )
        for column, reasoner in enumerate(reasoners):
            axis = axes[0][column]
            for architecture in ("docker", "physical"):
                points = []
                censored = []
                for row in distributed_rows:
                    if (
                        row["reasoner"] != reasoner
                        or row["architecture"] != architecture
                        or row.get("distributed_fully_complete") != "True"
                        or row.get("distributed_semantic_valid") != "True"
                    ):
                        continue
                    exact = row.get("total_speedup_vs_monolith", "")
                    lower = row.get("total_speedup_lower_bound", "")
                    if exact != "":
                        points.append(
                            (int(row["synthetic_users"]), float(exact))
                        )
                    elif lower != "":
                        censored.append(
                            (int(row["synthetic_users"]), float(lower))
                        )
                points.sort()
                censored.sort()
                if points:
                    axis.plot(
                        [point[0] for point in points],
                        [point[1] for point in points],
                        marker="o",
                        linewidth=2,
                        label=ARCHITECTURE_LABELS[architecture],
                        color=COLORS[architecture],
                    )
                if censored:
                    axis.scatter(
                        [point[0] for point in censored],
                        [point[1] for point in censored],
                        marker="^",
                        s=65,
                        facecolors="none",
                        edgecolors=COLORS[architecture],
                        label=f"{ARCHITECTURE_LABELS[architecture]} (límite)",
                    )
            axis.axhline(1.0, color="#555555", linestyle="--", linewidth=1)
            axis.set_title(REASONER_LABELS.get(reasoner, reasoner))
            axis.set_xlabel("Usuarios del dataset lógico")
            axis.grid(True, alpha=0.25)
        axes[0][0].set_ylabel("Speedup tiempo total vs monolito")
        axes[0][-1].legend(frameon=False, fontsize=8)
        figure.suptitle(
            "Punto de equilibrio de la ontología distribuida",
            fontweight="bold",
        )
        output.extend(
            _save(
                figure,
                root / "figures" / "experiment-distributed-speedup",
            )
        )
    return output
