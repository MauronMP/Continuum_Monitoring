from __future__ import annotations

import csv
from collections import defaultdict
import os
from pathlib import Path
import statistics
import tempfile

_MPL_CONFIG = Path(tempfile.gettempdir()) / "continuum-matplotlib"
_MPL_CONFIG.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CONFIG))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _median_groups(
    rows: list[dict[str, str]],
    x_field: str,
    y_field: str,
) -> dict[str, list[tuple[float, float]]]:
    values: dict[tuple[str, float], list[float]] = defaultdict(list)
    for row in rows:
        values[(row["reasoner"], float(row[x_field]))].append(float(row[y_field]))
    grouped: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for (reasoner, x_value), samples in values.items():
        grouped[reasoner].append((x_value, statistics.median(samples)))
    for points in grouped.values():
        points.sort()
    return grouped


def _line_plot(
    groups: dict[str, list[tuple[float, float]]],
    output: Path,
    title: str,
    xlabel: str,
    ylabel: str,
    tick_labels: dict[float, str] | None = None,
) -> None:
    fig, axis = plt.subplots(figsize=(9, 5.5))
    for reasoner, points in sorted(groups.items()):
        axis.plot(
            [point[0] for point in points],
            [point[1] for point in points],
            marker="o",
            linewidth=2,
            label=reasoner,
        )
    axis.set_title(title)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    if tick_labels:
        positions = sorted(tick_labels)
        axis.set_xticks(positions, [tick_labels[position] for position in positions])
        axis.tick_params(axis="x", labelrotation=25)
    axis.grid(True, alpha=0.25)
    axis.legend(title="Reasoner")
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_cumulative(directory: Path) -> list[Path]:
    rows = _read(directory / "summary.csv")
    tick_labels = {
        float(row["stage"]): row["added_category"]
        for row in rows
    }
    outputs = [
        directory / "cumulative-total-time.png",
        directory / "cumulative-p95-query-time.png",
    ]
    _line_plot(
        _median_groups(rows, "stage", "total_ms"),
        outputs[0],
        "Cumulative benchmark: reasoning + accumulated queries",
        "Cumulative category stage",
        "Median total time (ms)",
        tick_labels,
    )
    _line_plot(
        _median_groups(rows, "stage", "p95_query_ms"),
        outputs[1],
        "Cumulative benchmark: SPARQL p95",
        "Cumulative category stage",
        "Median p95 query time (ms)",
        tick_labels,
    )
    return outputs


def plot_scalability(directory: Path) -> list[Path]:
    rows = _read(directory / "summary.csv")
    outputs = [
        directory / "scalability-total-time.png",
        directory / "scalability-query-throughput.png",
    ]
    _line_plot(
        _median_groups(rows, "synthetic_users", "total_ms"),
        outputs[0],
        "Scalability benchmark: total execution time",
        "Synthetic users",
        "Median total time (ms)",
    )
    _line_plot(
        _median_groups(rows, "synthetic_users", "queries_per_second"),
        outputs[1],
        "Scalability benchmark: SPARQL throughput",
        "Synthetic users",
        "Median queries/s",
    )
    return outputs


def _save_publication(fig, stem: Path) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    outputs = [
        stem.with_suffix(".png"),
        stem.with_suffix(".pdf"),
        stem.with_suffix(".svg"),
    ]
    fig.savefig(outputs[0], dpi=300, bbox_inches="tight")
    fig.savefig(outputs[1], bbox_inches="tight")
    fig.savefig(outputs[2], bbox_inches="tight")
    plt.close(fig)
    return outputs


def _summary_samples(
    rows: list[dict[str, str]],
    x_field: str,
    y_field: str,
) -> dict[str, list[tuple[float, float, float, float]]]:
    values: dict[tuple[str, float], list[float]] = defaultdict(list)
    for row in rows:
        values[(row["reasoner"], float(row[x_field]))].append(
            float(row[y_field])
        )
    grouped: dict[str, list[tuple[float, float, float, float]]] = defaultdict(list)
    for (reasoner, x_value), samples in values.items():
        grouped[reasoner].append(
            (
                x_value,
                statistics.median(samples),
                min(samples),
                max(samples),
            )
        )
    for points in grouped.values():
        points.sort()
    return grouped


def plot_publication(output_root: Path) -> list[Path]:
    """Create vector and 300-DPI figures with repetition ranges."""
    publication = output_root / "publication"
    cumulative_rows = _read(output_root / "cumulative" / "summary.csv")
    scalability_rows = _read(output_root / "scalability" / "summary.csv")
    outputs: list[Path] = []

    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
        }
    )

    fig, axis = plt.subplots(figsize=(7.2, 4.2))
    category_labels = {
        float(row["stage"]): row["added_category"]
        for row in cumulative_rows
    }
    for reasoner, points in sorted(
        _summary_samples(cumulative_rows, "stage", "total_ms").items()
    ):
        x = np.array([point[0] for point in points])
        median = np.array([point[1] for point in points])
        low = median - np.array([point[2] for point in points])
        high = np.array([point[3] for point in points]) - median
        axis.errorbar(
            x,
            median,
            yerr=np.vstack([low, high]),
            marker="o",
            capsize=2.5,
            linewidth=1.5,
            label=reasoner,
        )
    ticks = sorted(category_labels)
    axis.set_xticks(ticks, [category_labels[tick] for tick in ticks])
    axis.tick_params(axis="x", rotation=35)
    axis.set_xlabel("Cumulative query category")
    axis.set_ylabel("Wall-clock time (ms)")
    axis.grid(True, axis="y", alpha=0.25)
    axis.legend(title="Reasoning profile", frameon=False)
    fig.tight_layout()
    outputs.extend(
        _save_publication(fig, publication / "cumulative-total-range")
    )

    reasoners = sorted({row["reasoner"] for row in scalability_rows})
    users = sorted({int(row["synthetic_users"]) for row in scalability_rows})
    fig, axes = plt.subplots(
        1,
        len(reasoners),
        figsize=(10.5, 3.5),
        sharey=True,
    )
    for axis, reasoner in zip(axes, reasoners):
        subset = [
            row for row in scalability_rows if row["reasoner"] == reasoner
        ]
        x = np.arange(len(users))
        generation = [
            statistics.median(
                float(row["generation_ms"])
                for row in subset
                if int(row["synthetic_users"]) == value
            )
            for value in users
        ]
        reasoning = [
            statistics.median(
                float(row["reasoning_ms"])
                for row in subset
                if int(row["synthetic_users"]) == value
            )
            for value in users
        ]
        queries = [
            statistics.median(
                float(row["query_ms"])
                for row in subset
                if int(row["synthetic_users"]) == value
            )
            for value in users
        ]
        axis.bar(x, generation, label="Generation")
        axis.bar(x, reasoning, bottom=generation, label="Reasoning")
        axis.bar(
            x,
            queries,
            bottom=np.array(generation) + np.array(reasoning),
            label="SPARQL",
        )
        axis.set_title(reasoner)
        axis.set_xticks(x, [str(value) for value in users])
        axis.set_xlabel("Synthetic users")
        axis.grid(True, axis="y", alpha=0.2)
    axes[0].set_ylabel("Median time (ms)")
    axes[-1].legend(frameon=False, loc="upper left")
    fig.tight_layout()
    outputs.extend(
        _save_publication(fig, publication / "scalability-breakdown")
    )

    fig, axis = plt.subplots(figsize=(6.2, 4.0))
    for reasoner, points in sorted(
        _summary_samples(
            scalability_rows,
            "input_triples",
            "total_ms",
        ).items()
    ):
        x = np.array([point[0] for point in points])
        median = np.array([point[1] for point in points])
        low = median - np.array([point[2] for point in points])
        high = np.array([point[3] for point in points]) - median
        axis.errorbar(
            x,
            median,
            yerr=np.vstack([low, high]),
            marker="o",
            capsize=2.5,
            linewidth=1.5,
            label=reasoner,
        )
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("Input triples (log scale)")
    axis.set_ylabel("Wall-clock time in ms (log scale)")
    axis.grid(True, which="both", alpha=0.25)
    axis.legend(title="Reasoning profile", frameon=False)
    fig.tight_layout()
    outputs.extend(
        _save_publication(fig, publication / "scalability-loglog")
    )
    return outputs


def plot_comparison(
    comparison_root: Path,
    suites: tuple[str, ...] = ("cumulative", "scalability"),
) -> list[Path]:
    outputs: list[Path] = []
    publication = comparison_root / "figures"
    for suite, x_field, x_label in (
        ("cumulative", "stage", "Cumulative category stage"),
        ("scalability", "synthetic_users", "Synthetic users"),
    ):
        if suite not in suites:
            continue
        rows = _read(comparison_root / f"{suite}.csv")
        fig, axis = plt.subplots(figsize=(6.4, 4.0))
        for reasoner, points in sorted(
            _summary_samples(rows, x_field, "speedup").items()
        ):
            x = np.array([point[0] for point in points])
            median = np.array([point[1] for point in points])
            low = median - np.array([point[2] for point in points])
            high = np.array([point[3] for point in points]) - median
            axis.errorbar(
                x,
                median,
                yerr=np.vstack([low, high]),
                marker="o",
                capsize=2.5,
                linewidth=1.5,
                label=reasoner,
            )
        axis.axhline(1.0, color="black", linestyle="--", linewidth=1)
        axis.set_xlabel(x_label)
        axis.set_ylabel("Speedup (monolith / Docker wall time)")
        axis.grid(True, axis="y", alpha=0.25)
        axis.legend(title="Reasoning profile", frameon=False)
        fig.tight_layout()
        outputs.extend(
            _save_publication(fig, publication / f"{suite}-speedup")
        )
    return outputs


def _engine_samples(
    rows: list[dict[str, str]],
    x_field: str,
    y_field: str,
) -> dict[str, list[tuple[float, float, float, float]]]:
    values: dict[tuple[str, float], list[float]] = defaultdict(list)
    for row in rows:
        values[(row["engine"], float(row[x_field]))].append(
            float(row[y_field])
        )
    grouped: dict[str, list[tuple[float, float, float, float]]] = defaultdict(
        list
    )
    for (engine, x_value), samples in values.items():
        grouped[engine].append(
            (
                x_value,
                statistics.median(samples),
                min(samples),
                max(samples),
            )
        )
    for points in grouped.values():
        points.sort()
    return grouped


def plot_engine_benchmark(
    output_root: Path,
    suites: tuple[str, ...] = ("cumulative", "scalability"),
) -> list[Path]:
    """Publication figures comparing independent engine implementations."""
    publication = output_root / "figures"
    outputs: list[Path] = []
    labels = {
        "jena": "Apache Jena (RDFS)",
        "rdf4j": "Eclipse RDF4J (RDFS)",
        "rdflib": "RDFLib/OWL-RL (RDFS)",
        "oxigraph": "Oxigraph (no inference)",
    }
    markers = {
        "jena": "o",
        "rdf4j": "s",
        "rdflib": "^",
        "oxigraph": "D",
    }

    if "cumulative" in suites:
        cumulative = _read(output_root / "cumulative" / "summary.csv")
        fig, axis = plt.subplots(figsize=(9.2, 4.8))
        for engine, points in sorted(
            _engine_samples(cumulative, "stage", "engine_total_ms").items()
        ):
            x = np.array([point[0] for point in points])
            median = np.array([point[1] for point in points])
            axis.errorbar(
                x,
                median,
                yerr=np.vstack(
                    [
                        median - np.array([point[2] for point in points]),
                        np.array([point[3] for point in points]) - median,
                    ]
                ),
                marker=markers[engine],
                capsize=2.5,
                linewidth=1.5,
                label=labels[engine],
            )
        category_labels = {
            float(row["stage"]): row["added_category"].replace("_", "\n")
            for row in cumulative
        }
        positions = sorted(category_labels)
        axis.set_xticks(
            positions,
            [category_labels[position] for position in positions],
        )
        axis.tick_params(axis="x", labelsize=7)
        axis.set_xlabel("Cumulative category stage")
        axis.set_ylabel("Prepare + SPARQL wall time (ms)")
        axis.grid(True, axis="y", alpha=0.25)
        axis.legend(title="Engine", frameon=False)
        fig.tight_layout()
        outputs.extend(
            _save_publication(fig, publication / "engines-cumulative")
        )

    if "scalability" in suites:
        scalability = _read(output_root / "scalability" / "summary.csv")
        fig, axis = plt.subplots(figsize=(7.8, 4.2))
        for engine, points in sorted(
            _engine_samples(
                scalability,
                "synthetic_users",
                "engine_total_ms",
            ).items()
        ):
            x = np.array([point[0] for point in points])
            median = np.array([point[1] for point in points])
            axis.errorbar(
                x,
                median,
                yerr=np.vstack(
                    [
                        median - np.array([point[2] for point in points]),
                        np.array([point[3] for point in points]) - median,
                    ]
                ),
                marker=markers[engine],
                capsize=2.5,
                linewidth=1.5,
                label=labels[engine],
            )
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlabel("Synthetic users (log scale)")
        axis.set_ylabel("Prepare + SPARQL wall time in ms (log scale)")
        axis.grid(True, which="both", alpha=0.25)
        axis.legend(
            title="Engine / entailment",
            frameon=False,
            loc="center left",
            bbox_to_anchor=(1.01, 0.5),
        )
        fig.tight_layout()
        outputs.extend(
            _save_publication(fig, publication / "engines-scalability")
        )
    return outputs
