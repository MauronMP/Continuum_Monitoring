"""Publication figures for the independent semantic-product matrix."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
import statistics
from typing import Iterable

from ..plot_environment import configure_matplotlib

configure_matplotlib()
import matplotlib.pyplot as plt


ENGINE_ORDER = ("rdflib", "jena", "rdf4j", "oxigraph")
ENGINE_LABELS = {
    "rdflib": "RDFLib (RDFS)",
    "jena": "Apache Jena (RDFS)",
    "rdf4j": "Eclipse RDF4J (RDFS)",
    "oxigraph": "Oxigraph (no inference)",
}
ENGINE_COLORS = {
    "rdflib": "#0072B2",
    "jena": "#D55E00",
    "rdf4j": "#009E73",
    "oxigraph": "#CC79A7",
}
ENGINE_MARKERS = {
    "rdflib": "o",
    "jena": "s",
    "rdf4j": "^",
    "oxigraph": "D",
}


def _read(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required engine summary not found: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Engine summary is empty: {path}")
    present = {row.get("engine", "") for row in rows}
    missing = set(ENGINE_ORDER) - present
    if missing:
        raise ValueError(
            f"Engine summary {path} is missing products: {sorted(missing)}"
        )
    return rows


def _median_points(
    rows: list[dict[str, str]],
    x_field: str,
    y_field: str,
) -> dict[str, tuple[list[float], list[float]]]:
    grouped: dict[tuple[str, float], list[float]] = defaultdict(list)
    for row in rows:
        if row.get("status", "completed") != "completed":
            continue
        if row.get(x_field, "") == "" or row.get(y_field, "") == "":
            continue
        grouped[(row["engine"], float(row[x_field]))].append(
            float(row[y_field])
        )
    output = {}
    for engine in ENGINE_ORDER:
        points = sorted(
            (
                x,
                statistics.median(values),
            )
            for (name, x), values in grouped.items()
            if name == engine
        )
        output[engine] = (
            [point[0] for point in points],
            [point[1] for point in points],
        )
    return output


def _plot_lines(
    axis,
    rows: list[dict[str, str]],
    x_field: str,
    y_field: str,
    *,
    title: str,
    x_label: str,
    y_label: str,
    log_y: bool = False,
) -> None:
    for engine, (x_values, y_values) in _median_points(
        rows, x_field, y_field
    ).items():
        axis.plot(
            x_values,
            y_values,
            label=ENGINE_LABELS[engine],
            color=ENGINE_COLORS[engine],
            marker=ENGINE_MARKERS[engine],
            linewidth=1.8,
            markersize=5,
        )
    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    if log_y:
        axis.set_yscale("log")
    axis.grid(True, alpha=0.25)


def _plot_coverage(axis, rows: list[dict[str, str]]) -> None:
    complete = []
    censored = []
    for engine in ENGINE_ORDER:
        samples = [row for row in rows if row.get("engine") == engine]
        completed = sum(
            row.get("status", "completed") == "completed" for row in samples
        )
        complete.append(100 * completed / len(samples) if samples else 0.0)
        censored.append(100 - complete[-1])
    positions = list(range(len(ENGINE_ORDER)))
    axis.bar(positions, complete, color="#56B4E9", label="Completed")
    axis.bar(
        positions,
        censored,
        bottom=complete,
        color="#E69F00",
        hatch="//",
        label="Censored/failed",
    )
    axis.set_xticks(
        positions,
        [ENGINE_LABELS[engine].split(" (")[0] for engine in ENGINE_ORDER],
        rotation=20,
        ha="right",
    )
    axis.set_ylim(0, 100)
    axis.set_ylabel("Observation coverage (%)")
    axis.set_title("Completion coverage")
    axis.grid(True, axis="y", alpha=0.25)
    axis.legend(frameon=False, fontsize=8)


def _save(fig, base):
    from .figure_style import save_png
    return save_png(fig, base)


def _plot_suite(root: Path, suite: str) -> list[Path]:
    rows = _read(root / suite / "summary.csv")
    if suite == "cumulative":
        x_field = "stage"
        x_label = "Accumulated category stage"
    elif suite == "scalability":
        x_field = "synthetic_users"
        x_label = "Synthetic users"
    else:
        raise ValueError(f"Unknown engine suite {suite!r}")

    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.4))
    _plot_lines(
        axes[0, 0],
        rows,
        x_field,
        "engine_total_ms",
        title="End-to-end semantic processing",
        x_label=x_label,
        y_label="Median time (ms, log scale)",
        log_y=True,
    )
    _plot_lines(
        axes[0, 1],
        rows,
        x_field,
        "query_ms",
        title="SPARQL battery execution",
        x_label=x_label,
        y_label="Median query wall time (ms, log scale)",
        log_y=True,
    )
    _plot_lines(
        axes[1, 0],
        rows,
        x_field,
        "reasoning_ms",
        title="RDFS materialisation cost",
        x_label=x_label,
        y_label="Median reasoning time (ms)",
    )
    _plot_coverage(axes[1, 1], rows)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, 1.02),
    )
    fig.suptitle(
        "Independent semantic products — "
        + ("cumulative categories" if suite == "cumulative" else "scalability"),
        y=1.07,
        fontsize=13,
    )
    fig.tight_layout()
    return _save(fig, root / "figures" / f"engines-{suite}")


def plot_engine_benchmarks(
    root: Path,
    suites: Iterable[str] = ("cumulative", "scalability"),
) -> list[Path]:
    """Create paper-ready figures and require all four named products."""

    outputs = []
    for suite in suites:
        outputs.extend(_plot_suite(root, suite))
    return outputs
