"""Publication-oriented comparison report for continuum deployments."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import tempfile
from typing import Any, Iterable
import webbrowser

_MPL_CONFIG = Path(tempfile.gettempdir()) / "continuum-matplotlib"
_MPL_CONFIG.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CONFIG))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .compare import compare_all
from .csv_utils import write_dict_rows
from .result_contract import require_release_metadata


REASONER_LABELS = {
    "rdfs": "RDFS",
    "owlrl": "OWL RL",
    "rdfs_owlrl": "RDFS + OWL RL",
}
REASONER_MARKERS = {
    "rdfs": "o",
    "owlrl": "s",
    "rdfs_owlrl": "^",
}
ROLES = ("cloud", "fog", "edge1", "edge2", "edge3")
ENGINE_LABELS = {
    "jena": "Apache Jena (RDFS)",
    "rdf4j": "Eclipse RDF4J (RDFS)",
    "rdflib": "RDFLib/OWL-RL (RDFS)",
    "oxigraph": "Oxigraph (sin inferencia)",
}
ENGINE_MARKERS = {
    "jena": "o",
    "rdf4j": "s",
    "rdflib": "^",
    "oxigraph": "D",
}
ARCHITECTURE_LABELS = {
    "monolith": "Monolito",
    "docker": "Docker (5 nodos)",
    "physical": "Continuum físico (5 nodos)",
    "docker_sharded": "Docker particionado (5 nodos)",
    "physical_sharded": "Continuum físico particionado (5 nodos)",
}


def _read(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required benchmark CSV not found: {path}")
    if path.name == "summary.csv":
        require_release_metadata(path.parent)
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Benchmark CSV is empty: {path}")
    return rows


def _write(path: Path, rows: list[dict[str, Any]]) -> Path:
    write_dict_rows(
        path,
        rows,
        empty_message=f"Cannot write an empty report CSV: {path}",
    )
    return path


def _median(values: Iterable[float]) -> float:
    return statistics.median(list(values))


def _optional_median(
    rows: list[dict[str, str]],
    field: str,
) -> float | str:
    values = [
        float(row[field])
        for row in rows
        if row.get(field, "") not in {"", None}
    ]
    return statistics.median(values) if values else ""


def _samples(
    rows: list[dict[str, str]],
    x_field: str,
    y_field: str,
) -> dict[str, list[tuple[float, float, float, float]]]:
    grouped: dict[tuple[str, float], list[float]] = defaultdict(list)
    for row in rows:
        grouped[(row["reasoner"], float(row[x_field]))].append(
            float(row[y_field])
        )
    output: dict[str, list[tuple[float, float, float, float]]] = defaultdict(
        list
    )
    for (reasoner, x_value), values in grouped.items():
        output[reasoner].append(
            (
                x_value,
                statistics.median(values),
                min(values),
                max(values),
            )
        )
    for values in output.values():
        values.sort()
    return output


def _named_samples(
    rows: list[dict[str, str]],
    name_field: str,
    x_field: str,
    y_field: str,
) -> dict[str, list[tuple[float, float, float, float]]]:
    grouped: dict[tuple[str, float], list[float]] = defaultdict(list)
    for row in rows:
        grouped[(row[name_field], float(row[x_field]))].append(
            float(row[y_field])
        )
    output: dict[str, list[tuple[float, float, float, float]]] = defaultdict(
        list
    )
    for (name, x_value), values in grouped.items():
        output[name].append(
            (x_value, statistics.median(values), min(values), max(values))
        )
    for values in output.values():
        values.sort()
    return output


def _named_error_line(
    axis,
    samples: dict[str, list[tuple[float, float, float, float]]],
    labels: dict[str, str],
    markers: dict[str, str],
) -> None:
    for name, points in sorted(samples.items()):
        x = np.array([point[0] for point in points])
        median = np.array([point[1] for point in points])
        low = median - np.array([point[2] for point in points])
        high = np.array([point[3] for point in points]) - median
        axis.errorbar(
            x,
            median,
            yerr=np.vstack([low, high]),
            marker=markers[name],
            capsize=2.5,
            linewidth=1.5,
            label=labels[name],
        )


def _error_line(
    axis,
    samples: dict[str, list[tuple[float, float, float, float]]],
) -> None:
    for reasoner, points in sorted(samples.items()):
        x = np.array([point[0] for point in points])
        median = np.array([point[1] for point in points])
        low = median - np.array([point[2] for point in points])
        high = np.array([point[3] for point in points]) - median
        axis.errorbar(
            x,
            median,
            yerr=np.vstack([low, high]),
            marker=REASONER_MARKERS[reasoner],
            capsize=2.5,
            linewidth=1.5,
            label=REASONER_LABELS[reasoner],
        )


def _save(fig, stem: Path) -> list[Path]:
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


def _final_rows(
    rows: list[dict[str, str]],
    x_field: str,
) -> list[dict[str, str]]:
    maximum = max(float(row[x_field]) for row in rows)
    return [row for row in rows if float(row[x_field]) == maximum]


def _reasoner_medians(
    rows: list[dict[str, str]],
    fields: tuple[str, ...],
) -> dict[str, list[float]]:
    output: dict[str, list[float]] = {}
    for reasoner in REASONER_LABELS:
        selected = [row for row in rows if row["reasoner"] == reasoner]
        output[reasoner] = [
            _median(float(row[field]) for row in selected)
            for field in fields
        ]
    return output


def _stacked_components(
    axis,
    rows: list[dict[str, str]],
    fields: tuple[str, str],
    labels: tuple[str, str],
) -> None:
    medians = _reasoner_medians(rows, fields)
    x = np.arange(len(medians))
    first = np.array([medians[key][0] for key in medians])
    second = np.array([medians[key][1] for key in medians])
    axis.bar(x, first, label=labels[0])
    axis.bar(x, second, bottom=first, label=labels[1])
    axis.set_xticks(
        x,
        [REASONER_LABELS[key] for key in medians],
        rotation=15,
    )
    axis.legend(frameon=False)


def _style(axis, xlabel: str, ylabel: str) -> None:
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.grid(True, axis="y", alpha=0.25)


def _user_axis(axis, rows: list[dict[str, str]]) -> None:
    values = sorted({float(row["synthetic_users"]) for row in rows})
    axis.set_xscale("log")
    axis.set_xticks(values)
    axis.set_xticklabels(
        [
            str(int(value)) if value.is_integer() else str(value)
            for value in values
        ]
    )


def plot_monolith(
    monolith_root: Path,
    figure_root: Path,
) -> list[Path]:
    cumulative = _read(monolith_root / "cumulative" / "summary.csv")
    scalability = _read(monolith_root / "scalability" / "summary.csv")
    outputs: list[Path] = []

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.2))
    _error_line(
        axes[0, 0],
        _samples(cumulative, "stage", "total_ms"),
    )
    _style(axes[0, 0], "Cumulative category stage", "Total time (ms)")
    axes[0, 0].legend(frameon=False)

    final = _final_rows(cumulative, "stage")
    _stacked_components(
        axes[0, 1],
        final,
        ("reasoning_ms", "query_ms"),
        ("Reasoning", "SPARQL"),
    )
    _style(axes[0, 1], "Reasoning profile", "Median time (ms)")

    _error_line(
        axes[1, 0],
        _samples(cumulative, "stage", "p95_query_ms"),
    )
    _style(axes[1, 0], "Cumulative category stage", "SPARQL p95 (ms)")

    expansion = _reasoner_medians(
        final,
        ("input_triples", "output_triples"),
    )
    names = list(expansion)
    ratios = [
        expansion[name][1] / expansion[name][0]
        for name in names
    ]
    axes[1, 1].bar(
        np.arange(len(names)),
        ratios,
    )
    axes[1, 1].set_xticks(
        np.arange(len(names)),
        [REASONER_LABELS[name] for name in names],
        rotation=15,
    )
    _style(axes[1, 1], "Reasoning profile", "Materialization expansion")
    fig.tight_layout()
    outputs.extend(_save(fig, figure_root / "monolith-cumulative"))

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.2))
    _error_line(
        axes[0, 0],
        _samples(scalability, "synthetic_users", "total_ms"),
    )
    _user_axis(axes[0, 0], scalability)
    axes[0, 0].set_yscale("log")
    _style(axes[0, 0], "Synthetic users (log)", "Total time, ms (log)")
    axes[0, 0].legend(frameon=False)

    _error_line(
        axes[0, 1],
        _samples(
            scalability,
            "synthetic_users",
            "queries_per_second",
        ),
    )
    _user_axis(axes[0, 1], scalability)
    _style(axes[0, 1], "Synthetic users (log)", "Queries per second")

    final = _final_rows(scalability, "synthetic_users")
    _stacked_components(
        axes[1, 0],
        final,
        ("reasoning_ms", "query_ms"),
        ("Reasoning", "SPARQL"),
    )
    _style(axes[1, 0], "Reasoning profile", "Median time (ms)")

    _error_line(
        axes[1, 1],
        _samples(scalability, "synthetic_users", "inferred_triples"),
    )
    _user_axis(axes[1, 1], scalability)
    _style(axes[1, 1], "Synthetic users (log)", "Inferred triples")
    fig.tight_layout()
    outputs.extend(_save(fig, figure_root / "monolith-scalability"))
    return outputs


def _engine_summary_rows(
    engine_root: Path,
    architecture: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for suite, x_field in (
        ("cumulative", "stage"),
        ("scalability", "synthetic_users"),
    ):
        rows = _read(engine_root / suite / "summary.csv")
        final = _final_rows(rows, x_field)
        for engine in ENGINE_LABELS:
            selected = [row for row in final if row["engine"] == engine]
            if not selected:
                continue
            output.append(
                {
                    "architecture": architecture,
                    "suite": suite,
                    "engine": engine,
                    "label": ENGINE_LABELS[engine],
                    "inference_profile": selected[0]["inference_profile"],
                    "load_point": max(
                        float(row[x_field]) for row in selected
                    ),
                    "samples": len(selected),
                    "engine_total_ms_median": _median(
                        float(row["engine_total_ms"]) for row in selected
                    ),
                    "prepare_ms_median": _median(
                        float(row["prepare_ms"]) for row in selected
                    ),
                    "query_ms_median": _median(
                        float(row["query_ms"]) for row in selected
                    ),
                    "mean_query_ms_median": _median(
                        float(row["mean_query_ms"]) for row in selected
                    ),
                    "inferred_triples_median": _median(
                        float(row["inferred_triples"]) for row in selected
                    ),
                }
            )
    return output


def _engine_final_bars(
    axis,
    rows: list[dict[str, str]],
    fields: tuple[str, str],
    labels: tuple[str, str],
) -> None:
    engines = [engine for engine in ENGINE_LABELS if any(
        row["engine"] == engine for row in rows
    )]
    first = np.array(
        [
            _median(
                float(row[fields[0]])
                for row in rows
                if row["engine"] == engine
            )
            for engine in engines
        ]
    )
    second = np.array(
        [
            _median(
                float(row[fields[1]])
                for row in rows
                if row["engine"] == engine
            )
            for engine in engines
        ]
    )
    x = np.arange(len(engines))
    axis.bar(x, first, label=labels[0])
    axis.bar(x, second, bottom=first, label=labels[1])
    axis.set_xticks(
        x,
        [ENGINE_LABELS[engine].split(" (")[0] for engine in engines],
        rotation=15,
    )
    axis.legend(frameon=False)


def plot_product_engines(
    engine_root: Path,
    figure_root: Path,
    stem_prefix: str,
) -> list[Path]:
    """Plot all independent products, explicitly labelling inference scope."""
    outputs: list[Path] = []
    for suite, x_field, x_label in (
        ("cumulative", "stage", "Etapa acumulativa"),
        ("scalability", "synthetic_users", "Usuarios sintéticos"),
    ):
        rows = _read(engine_root / suite / "summary.csv")
        present = {row["engine"] for row in rows}
        missing = set(ENGINE_LABELS) - present
        if missing:
            raise ValueError(
                f"Missing product engines in {engine_root / suite}: "
                f"{sorted(missing)}"
            )
        final = _final_rows(rows, x_field)
        fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.5))
        _named_error_line(
            axes[0, 0],
            _named_samples(rows, "engine", x_field, "engine_total_ms"),
            ENGINE_LABELS,
            ENGINE_MARKERS,
        )
        _style(axes[0, 0], x_label, "Tiempo total del motor (ms)")
        axes[0, 0].legend(frameon=False, fontsize=8)

        _engine_final_bars(
            axes[0, 1],
            final,
            ("prepare_ms", "query_ms"),
            ("Carga + inferencia", "SPARQL"),
        )
        _style(axes[0, 1], "Producto", "Mediana en carga máxima (ms)")

        _named_error_line(
            axes[1, 0],
            _named_samples(rows, "engine", x_field, "mean_query_ms"),
            ENGINE_LABELS,
            ENGINE_MARKERS,
        )
        _style(axes[1, 0], x_label, "Latencia SPARQL media (ms)")

        engines = list(ENGINE_LABELS)
        inferred = [
            _median(
                float(row["inferred_triples"])
                for row in final
                if row["engine"] == engine
            )
            for engine in engines
        ]
        axes[1, 1].bar(np.arange(len(engines)), inferred)
        axes[1, 1].set_xticks(
            np.arange(len(engines)),
            [ENGINE_LABELS[engine].split(" (")[0] for engine in engines],
            rotation=15,
        )
        _style(
            axes[1, 1],
            "Producto",
            "Triples materializados en carga máxima",
        )
        axes[1, 1].text(
            0.99,
            0.97,
            "Oxigraph: control SPARQL sin inferencia",
            ha="right",
            va="top",
            transform=axes[1, 1].transAxes,
            fontsize=8,
        )
        if suite == "scalability":
            _user_axis(axes[0, 0], rows)
            _user_axis(axes[1, 0], rows)
        fig.tight_layout()
        outputs.extend(
            _save(fig, figure_root / f"{stem_prefix}-products-{suite}")
        )
    return outputs


def _node_cost_rows(
    suite: str,
    rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    run_field = "stage" if suite == "cumulative" else "synthetic_users"
    grouped: dict[
        tuple[str, str, str, str],
        list[dict[str, str]],
    ] = defaultdict(list)
    for row in rows:
        key = (
            row["reasoner"],
            row["repetition"],
            row[run_field],
            row["role"],
        )
        grouped[key].append(row)
    output = []
    for (reasoner, repetition, run_value, role), samples in grouped.items():
        output.append(
            {
                "suite": suite,
                "reasoner": reasoner,
                "repetition": repetition,
                "stage_or_users": run_value,
                "role": role,
                "query_count": len(samples),
                "query_cpu_ms": sum(
                    float(row["duration_ms"]) for row in samples
                ),
                "mean_query_ms": statistics.fmean(
                    float(row["duration_ms"]) for row in samples
                ),
                "p95_query_ms": float(
                    np.percentile(
                        [float(row["duration_ms"]) for row in samples],
                        95,
                    )
                ),
            }
        )
    return sorted(
        output,
        key=lambda row: (
            row["suite"],
            row["reasoner"],
            int(row["repetition"]),
            float(row["stage_or_users"]),
            row["role"],
        ),
    )


def _node_medians(
    rows: list[dict[str, Any]],
    reasoner: str,
    run_value: float,
    field: str,
) -> list[float]:
    values: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if (
            row["reasoner"] == reasoner
            and float(row["stage_or_users"]) == run_value
        ):
            values[str(row["role"])].append(float(row[field]))
    return [
        statistics.median(values[role]) if values[role] else 0.0
        for role in ROLES
    ]


def _grouped_node_bars(
    axis,
    rows: list[dict[str, Any]],
    run_value: float,
    field: str,
    ylabel: str,
    node_label: str = "Node",
) -> None:
    x = np.arange(len(ROLES))
    width = 0.24
    for index, reasoner in enumerate(REASONER_LABELS):
        axis.bar(
            x + (index - 1) * width,
            _node_medians(rows, reasoner, run_value, field),
            width,
            label=REASONER_LABELS[reasoner],
        )
    axis.set_xticks(x, ROLES)
    _style(axis, node_label, ylabel)
    axis.legend(frameon=False)


def _work_ratio_rows(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    output = []
    for row in rows:
        clone = dict(row)
        total_work = (
            float(row["node_reasoning_ms_sum"])
            + float(row["node_query_ms_sum"])
        )
        clone["aggregate_work_per_wall"] = (
            str(total_work / float(row["total_wall_ms"]))
            if float(row["total_wall_ms"])
            else "0"
        )
        clone["queries_per_second"] = str(
            float(row["query_count"])
            / (float(row["query_wall_ms"]) / 1000)
            if float(row["query_wall_ms"])
            else 0.0
        )
        output.append(clone)
    return output


def _distributed_detail_path(root: Path, suite: str) -> Path:
    """Return per-node detail for replicated or sharded distributed runs."""
    sharded = root / suite / "node-query-runs.csv"
    if sharded.is_file():
        return sharded
    return root / suite / "query-runs.csv"


def plot_docker(
    docker_root: Path,
    figure_root: Path,
    data_root: Path,
    *,
    stem_prefix: str = "docker",
    architecture_label: str = "Docker",
) -> tuple[list[Path], list[Path]]:
    cumulative = _read(docker_root / "cumulative" / "summary.csv")
    scalability = _read(docker_root / "scalability" / "summary.csv")
    cumulative_detail = _read(
        _distributed_detail_path(docker_root, "cumulative")
    )
    scalability_detail = _read(
        _distributed_detail_path(docker_root, "scalability")
    )
    node_costs = _node_cost_rows(
        "cumulative",
        cumulative_detail,
    ) + _node_cost_rows(
        "scalability",
        scalability_detail,
    )
    data_paths = [
        _write(data_root / f"{stem_prefix}-node-costs.csv", node_costs)
    ]
    outputs: list[Path] = []
    cumulative_work = _work_ratio_rows(cumulative)
    scalability_work = _work_ratio_rows(scalability)

    fig, axes = plt.subplots(2, 2, figsize=(10.8, 7.2))
    _error_line(
        axes[0, 0],
        _samples(cumulative, "stage", "total_wall_ms"),
    )
    _style(axes[0, 0], "Cumulative category stage", "Wall time (ms)")
    axes[0, 0].legend(frameon=False)

    final = _final_rows(cumulative, "stage")
    _stacked_components(
        axes[0, 1],
        final,
        ("prepare_wall_ms", "query_wall_ms"),
        ("Prepare wall", "SPARQL wall"),
    )
    _style(axes[0, 1], "Reasoning profile", "Median wall time (ms)")

    final_stage = max(float(row["stage"]) for row in cumulative)
    cumulative_costs = [
        row for row in node_costs if row["suite"] == "cumulative"
    ]
    _grouped_node_bars(
        axes[1, 0],
        cumulative_costs,
        final_stage,
        "query_cpu_ms",
        "Median node SPARQL CPU proxy (ms)",
        f"{architecture_label} node",
    )

    _error_line(
        axes[1, 1],
        _samples(
            cumulative_work,
            "stage",
            "aggregate_work_per_wall",
        ),
    )
    _style(
        axes[1, 1],
        "Cumulative category stage",
        "Aggregate node work / wall time",
    )
    fig.tight_layout()
    outputs.extend(
        _save(fig, figure_root / f"{stem_prefix}-cumulative")
    )

    fig, axes = plt.subplots(2, 2, figsize=(10.8, 7.2))
    _error_line(
        axes[0, 0],
        _samples(scalability, "synthetic_users", "total_wall_ms"),
    )
    _user_axis(axes[0, 0], scalability)
    axes[0, 0].set_yscale("log")
    _style(axes[0, 0], "Synthetic users (log)", "Wall time, ms (log)")
    axes[0, 0].legend(frameon=False)

    _error_line(
        axes[0, 1],
        _samples(
            scalability_work,
            "synthetic_users",
            "queries_per_second",
        ),
    )
    _user_axis(axes[0, 1], scalability)
    _style(axes[0, 1], "Synthetic users (log)", "Queries per second")

    max_users = max(float(row["synthetic_users"]) for row in scalability)
    scalability_costs = [
        row for row in node_costs if row["suite"] == "scalability"
    ]
    _grouped_node_bars(
        axes[1, 0],
        scalability_costs,
        max_users,
        "query_cpu_ms",
        "Median node SPARQL CPU proxy (ms)",
        f"{architecture_label} node",
    )

    _error_line(
        axes[1, 1],
        _samples(
            scalability_work,
            "synthetic_users",
            "aggregate_work_per_wall",
        ),
    )
    _user_axis(axes[1, 1], scalability)
    _style(
        axes[1, 1],
        "Synthetic users (log)",
        "Aggregate node work / wall time",
    )
    fig.tight_layout()
    outputs.extend(
        _save(fig, figure_root / f"{stem_prefix}-scalability")
    )
    return outputs, data_paths


def _deployment_bars(
    axis,
    rows: list[dict[str, str]],
) -> None:
    medians = _reasoner_medians(
        rows,
        ("monolith_total_ms", "docker_wall_ms"),
    )
    x = np.arange(len(medians))
    width = 0.36
    axis.bar(
        x - width / 2,
        [medians[key][0] for key in medians],
        width,
        label="Monolith",
    )
    axis.bar(
        x + width / 2,
        [medians[key][1] for key in medians],
        width,
        label="Docker (5 nodes)",
    )
    axis.set_xticks(
        x,
        [REASONER_LABELS[key] for key in medians],
        rotation=15,
    )
    axis.legend(frameon=False)


def plot_deployment_comparison(
    comparison_root: Path,
    figure_root: Path,
) -> list[Path]:
    outputs: list[Path] = []
    for suite, x_field, x_label in (
        ("cumulative", "stage", "Cumulative category stage"),
        ("scalability", "synthetic_users", "Synthetic users"),
    ):
        rows = _read(comparison_root / f"{suite}.csv")
        final = _final_rows(rows, x_field)
        fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.2))

        _error_line(
            axes[0, 0],
            _samples(rows, x_field, "speedup"),
        )
        axes[0, 0].axhline(
            1.0,
            color="black",
            linestyle="--",
            linewidth=1,
        )
        _style(axes[0, 0], x_label, "Speedup (monolith / Docker)")
        axes[0, 0].legend(frameon=False)

        _deployment_bars(axes[0, 1], final)
        _style(
            axes[0, 1],
            "Reasoning profile",
            "Median total time (ms)",
        )

        _error_line(
            axes[1, 0],
            _samples(rows, x_field, "parallel_efficiency"),
        )
        _style(axes[1, 0], x_label, "Parallel efficiency (speedup / 5)")

        _error_line(
            axes[1, 1],
            _samples(rows, x_field, "docker_change_percent"),
        )
        axes[1, 1].axhline(
            0.0,
            color="black",
            linestyle="--",
            linewidth=1,
        )
        _style(
            axes[1, 1],
            x_label,
            "Docker time change (%)",
        )
        if suite == "scalability":
            _user_axis(axes[0, 0], rows)
            _user_axis(axes[1, 0], rows)
            _user_axis(axes[1, 1], rows)
        fig.tight_layout()
        outputs.extend(
            _save(fig, figure_root / f"deployment-{suite}")
        )
    return outputs


def _architecture_points(
    monolith_root: Path,
    docker_root: Path,
    physical_root: Path,
    suite: str,
) -> list[dict[str, Any]]:
    x_field = "stage" if suite == "cumulative" else "synthetic_users"
    sources = (
        ("monolith", monolith_root, "total_ms"),
        ("docker", docker_root, "total_wall_ms"),
        ("physical", physical_root, "total_wall_ms"),
    )
    output: list[dict[str, Any]] = []
    for architecture, root, value_field in sources:
        rows = _read(root / suite / "summary.csv")
        grouped: dict[tuple[str, float], list[float]] = defaultdict(list)
        for row in rows:
            grouped[(row["reasoner"], float(row[x_field]))].append(
                float(row[value_field])
            )
        for (reasoner, load), values in sorted(grouped.items()):
            output.append(
                {
                    "suite": suite,
                    "architecture": architecture,
                    "reasoner": reasoner,
                    x_field: load,
                    "samples": len(values),
                    "median_ms": statistics.median(values),
                    "min_ms": min(values),
                    "max_ms": max(values),
                }
            )
    return output


def plot_three_architectures(
    monolith_root: Path,
    docker_root: Path,
    physical_root: Path,
    figure_root: Path,
    data_root: Path,
) -> tuple[list[Path], list[Path]]:
    figures: list[Path] = []
    tables: list[Path] = []
    architecture_markers = {
        "monolith": "o",
        "docker": "s",
        "physical": "^",
    }
    architectures = tuple(architecture_markers)
    for suite, x_field, x_label in (
        ("cumulative", "stage", "Etapa acumulativa"),
        ("scalability", "synthetic_users", "Usuarios sintéticos"),
    ):
        points = _architecture_points(
            monolith_root,
            docker_root,
            physical_root,
            suite,
        )
        tables.append(
            _write(data_root / f"three-way-{suite}.csv", points)
        )
        fig, axes = plt.subplots(2, 2, figsize=(11.0, 7.4))
        for axis, reasoner in zip(
            (axes[0, 0], axes[0, 1], axes[1, 0]),
            REASONER_LABELS,
            strict=True,
        ):
            selected = [
                row for row in points if row["reasoner"] == reasoner
            ]
            for architecture in architectures:
                rows = sorted(
                    (
                        row
                        for row in selected
                        if row["architecture"] == architecture
                    ),
                    key=lambda row: float(row[x_field]),
                )
                x = np.array([float(row[x_field]) for row in rows])
                median = np.array([float(row["median_ms"]) for row in rows])
                low = median - np.array(
                    [float(row["min_ms"]) for row in rows]
                )
                high = np.array(
                    [float(row["max_ms"]) for row in rows]
                ) - median
                axis.errorbar(
                    x,
                    median,
                    yerr=np.vstack([low, high]),
                    marker=architecture_markers[architecture],
                    capsize=2.5,
                    linewidth=1.5,
                    label=ARCHITECTURE_LABELS[architecture],
                )
            if suite == "scalability":
                _user_axis(axis, [
                    {"synthetic_users": str(row[x_field])}
                    for row in selected
                ])
                axis.set_yscale("log")
            _style(
                axis,
                x_label,
                f"{REASONER_LABELS[reasoner]} — tiempo total (ms)",
            )
            axis.legend(frameon=False, fontsize=8)

        final_load = max(float(row[x_field]) for row in points)
        final = [
            row for row in points if float(row[x_field]) == final_load
        ]
        x = np.arange(len(REASONER_LABELS))
        width = 0.24
        for index, architecture in enumerate(architectures):
            values = [
                next(
                    float(row["median_ms"])
                    for row in final
                    if row["architecture"] == architecture
                    and row["reasoner"] == reasoner
                )
                for reasoner in REASONER_LABELS
            ]
            axes[1, 1].bar(
                x + (index - 1) * width,
                values,
                width,
                label=ARCHITECTURE_LABELS[architecture],
            )
        axes[1, 1].set_xticks(
            x,
            [REASONER_LABELS[value] for value in REASONER_LABELS],
            rotation=15,
        )
        _style(
            axes[1, 1],
            "Perfil de inferencia",
            f"Mediana en carga máxima ({final_load:g}) (ms)",
        )
        axes[1, 1].legend(frameon=False, fontsize=8)
        fig.tight_layout()
        figures.extend(
            _save(fig, figure_root / f"architecture-{suite}")
        )
    return figures, tables


def _article_architecture_rows(
    monolith_root: Path,
    docker_root: Path,
    physical_root: Path,
    suite: str,
) -> list[dict[str, Any]]:
    x_field = "stage" if suite == "cumulative" else "synthetic_users"
    sources = (
        ("monolith", monolith_root),
        ("docker", docker_root),
        ("physical", physical_root),
    )
    rows_by_architecture = {
        architecture: _read(root / suite / "summary.csv")
        for architecture, root in sources
    }
    final_load = max(
        float(row[x_field])
        for rows in rows_by_architecture.values()
        for row in rows
    )
    output: list[dict[str, Any]] = []
    for architecture, rows in rows_by_architecture.items():
        selected = [
            row for row in rows if float(row[x_field]) == final_load
        ]
        for reasoner in REASONER_LABELS:
            samples = [
                row for row in selected if row["reasoner"] == reasoner
            ]
            if architecture == "monolith":
                totals = [float(row["total_ms"]) for row in samples]
                prepare = [
                    float(row.get("generation_ms", 0.0) or 0.0)
                    + float(row["reasoning_ms"])
                    for row in samples
                ]
                query = [float(row["query_ms"]) for row in samples]
            else:
                totals = [float(row["total_wall_ms"]) for row in samples]
                prepare = [
                    float(row["prepare_wall_ms"]) for row in samples
                ]
                query = [float(row["query_wall_ms"]) for row in samples]
            throughput = [
                float(row["query_count"]) / (query_ms / 1000)
                if query_ms
                else 0.0
                for row, query_ms in zip(samples, query, strict=True)
            ]
            total_median = statistics.median(totals)
            prepare_median = statistics.median(prepare)
            query_median = statistics.median(query)
            output.append(
                {
                    "suite": suite,
                    "load_point": final_load,
                    "architecture": architecture,
                    "reasoner": reasoner,
                    "samples": len(samples),
                    "total_ms_median": total_median,
                    "total_ms_min": min(totals),
                    "total_ms_max": max(totals),
                    "variation_span_percent": (
                        (max(totals) - min(totals)) / total_median * 100
                        if total_median
                        else 0.0
                    ),
                    "prepare_ms_median": prepare_median,
                    "query_ms_median": query_median,
                    "prepare_share_percent": (
                        prepare_median / total_median * 100
                        if total_median
                        else 0.0
                    ),
                    "query_throughput_median": statistics.median(throughput),
                }
            )
    monolith = {
        row["reasoner"]: float(row["total_ms_median"])
        for row in output
        if row["architecture"] == "monolith"
    }
    for row in output:
        baseline = monolith[str(row["reasoner"])]
        total = float(row["total_ms_median"])
        row["speedup_vs_monolith"] = baseline / total if total else 0.0
        row["slowdown_vs_monolith"] = total / baseline if baseline else 0.0
    return output


def plot_article_architecture_summary(
    monolith_root: Path,
    docker_root: Path,
    physical_root: Path,
    figure_root: Path,
    data_root: Path,
) -> tuple[list[Path], list[Path]]:
    """Create compact paper-oriented performance, speedup and cost figures."""
    figures: list[Path] = []
    tables: list[Path] = []
    architectures = ("monolith", "docker", "physical")
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"][:3]
    x = np.arange(len(REASONER_LABELS))
    width = 0.24
    reasoner_ticks = [
        REASONER_LABELS[reasoner] for reasoner in REASONER_LABELS
    ]

    for suite in ("cumulative", "scalability"):
        rows = _article_architecture_rows(
            monolith_root,
            docker_root,
            physical_root,
            suite,
        )
        tables.append(
            _write(data_root / f"article-{suite}-summary.csv", rows)
        )
        fig, axes = plt.subplots(2, 2, figsize=(11.0, 7.4))
        metrics = (
            ("total_ms_median", "Tiempo total mediano (s)"),
            ("speedup_vs_monolith", "Aceleración frente al monolito"),
            ("prepare_share_percent", "Preparación sobre tiempo total (%)"),
            ("query_throughput_median", "Rendimiento SPARQL (consultas/s)"),
        )
        for axis, (metric, ylabel) in zip(
            axes.flat,
            metrics,
            strict=True,
        ):
            for index, architecture in enumerate(architectures):
                selected = {
                    str(row["reasoner"]): row
                    for row in rows
                    if row["architecture"] == architecture
                }
                values = np.array(
                    [
                        float(selected[reasoner][metric])
                        for reasoner in REASONER_LABELS
                    ]
                )
                if metric == "total_ms_median":
                    values = values / 1000
                    low = values - np.array(
                        [
                            float(selected[reasoner]["total_ms_min"]) / 1000
                            for reasoner in REASONER_LABELS
                        ]
                    )
                    high = np.array(
                        [
                            float(selected[reasoner]["total_ms_max"]) / 1000
                            for reasoner in REASONER_LABELS
                        ]
                    ) - values
                    yerr = np.vstack([low, high])
                else:
                    yerr = None
                axis.bar(
                    x + (index - 1) * width,
                    values,
                    width,
                    yerr=yerr,
                    capsize=2.5 if yerr is not None else 0,
                    color=colors[index],
                    label=ARCHITECTURE_LABELS[architecture],
                )
            axis.set_xticks(x, reasoner_ticks, rotation=12)
            _style(axis, "Perfil de inferencia", ylabel)
        axes[0, 1].axhline(
            1.0,
            color="black",
            linestyle="--",
            linewidth=1,
        )
        axes[0, 0].legend(frameon=False, fontsize=8)
        fig.tight_layout()
        figures.extend(
            _save(fig, figure_root / f"article-{suite}-summary")
        )
    return figures, tables


def _multi_architecture_points(
    architecture_roots: dict[str, Path],
    suite: str,
) -> list[dict[str, Any]]:
    x_field = "stage" if suite == "cumulative" else "synthetic_users"
    output: list[dict[str, Any]] = []
    for architecture, root in architecture_roots.items():
        value_field = (
            "total_ms" if architecture == "monolith" else "total_wall_ms"
        )
        rows = _read(root / suite / "summary.csv")
        grouped: dict[tuple[str, float], list[float]] = defaultdict(list)
        for row in rows:
            grouped[(row["reasoner"], float(row[x_field]))].append(
                float(row[value_field])
            )
        for (reasoner, load), values in sorted(grouped.items()):
            output.append(
                {
                    "suite": suite,
                    "architecture": architecture,
                    "reasoner": reasoner,
                    x_field: load,
                    "samples": len(values),
                    "median_ms": statistics.median(values),
                    "min_ms": min(values),
                    "max_ms": max(values),
                }
            )
    return output


def plot_multi_architectures(
    architecture_roots: dict[str, Path],
    figure_root: Path,
    data_root: Path,
) -> tuple[list[Path], list[Path]]:
    """Compare replicated and sharded layouts without replacing legacy plots."""
    figures: list[Path] = []
    tables: list[Path] = []
    markers = {
        "monolith": "o",
        "docker": "s",
        "physical": "^",
        "docker_sharded": "D",
        "physical_sharded": "P",
    }
    architectures = list(architecture_roots)
    for suite, x_field, x_label in (
        ("cumulative", "stage", "Etapa acumulativa"),
        ("scalability", "synthetic_users", "Usuarios sintéticos"),
    ):
        points = _multi_architecture_points(architecture_roots, suite)
        tables.append(
            _write(data_root / f"multi-architecture-{suite}.csv", points)
        )
        fig, axes = plt.subplots(2, 2, figsize=(12.2, 7.8))
        for axis, reasoner in zip(
            (axes[0, 0], axes[0, 1], axes[1, 0]),
            REASONER_LABELS,
            strict=True,
        ):
            selected = [
                row for row in points if row["reasoner"] == reasoner
            ]
            for architecture in architectures:
                rows = sorted(
                    (
                        row
                        for row in selected
                        if row["architecture"] == architecture
                    ),
                    key=lambda row: float(row[x_field]),
                )
                if not rows:
                    continue
                x = np.array([float(row[x_field]) for row in rows])
                median = np.array([float(row["median_ms"]) for row in rows])
                low = median - np.array(
                    [float(row["min_ms"]) for row in rows]
                )
                high = np.array(
                    [float(row["max_ms"]) for row in rows]
                ) - median
                axis.errorbar(
                    x,
                    median,
                    yerr=np.vstack([low, high]),
                    marker=markers[architecture],
                    capsize=2.5,
                    linewidth=1.5,
                    label=ARCHITECTURE_LABELS[architecture],
                )
            if suite == "scalability":
                _user_axis(
                    axis,
                    [
                        {"synthetic_users": str(row[x_field])}
                        for row in selected
                    ],
                )
                axis.set_yscale("log")
            _style(
                axis,
                x_label,
                f"{REASONER_LABELS[reasoner]} — tiempo total (ms)",
            )
            axis.legend(frameon=False, fontsize=7)

        final_load = max(float(row[x_field]) for row in points)
        final = [
            row for row in points if float(row[x_field]) == final_load
        ]
        x = np.arange(len(REASONER_LABELS))
        width = 0.8 / len(architectures)
        center = (len(architectures) - 1) / 2
        for index, architecture in enumerate(architectures):
            values = []
            for reasoner in REASONER_LABELS:
                samples = [
                    float(row["median_ms"])
                    for row in final
                    if row["architecture"] == architecture
                    and row["reasoner"] == reasoner
                ]
                values.append(samples[0] if samples else np.nan)
            axes[1, 1].bar(
                x + (index - center) * width,
                values,
                width,
                label=ARCHITECTURE_LABELS[architecture],
            )
        axes[1, 1].set_xticks(
            x,
            [REASONER_LABELS[value] for value in REASONER_LABELS],
            rotation=15,
        )
        _style(
            axes[1, 1],
            "Perfil de inferencia",
            f"Mediana en carga máxima ({final_load:g}) (ms)",
        )
        axes[1, 1].legend(frameon=False, fontsize=7)
        fig.tight_layout()
        figures.extend(
            _save(fig, figure_root / f"architecture-all-{suite}")
        )
    return figures, tables


def _monolith_summary_rows(
    monolith_root: Path,
) -> list[dict[str, Any]]:
    output = []
    for suite, x_field in (
        ("cumulative", "stage"),
        ("scalability", "synthetic_users"),
    ):
        rows = _read(monolith_root / suite / "summary.csv")
        final = _final_rows(rows, x_field)
        for reasoner in REASONER_LABELS:
            selected = [
                row for row in final if row["reasoner"] == reasoner
            ]
            query_ms = _median(float(row["query_ms"]) for row in selected)
            query_count = _median(
                float(row["query_count"]) for row in selected
            )
            output.append(
                {
                    "architecture": "monolith",
                    "suite": suite,
                    "reasoner": reasoner,
                    "load_point": max(
                        float(row[x_field]) for row in selected
                    ),
                    "samples": len(selected),
                    "total_ms_median": _median(
                        float(row["total_ms"]) for row in selected
                    ),
                    "reasoning_ms_median": _median(
                        float(row["reasoning_ms"]) for row in selected
                    ),
                    "query_ms_median": query_ms,
                    "queries_per_second": (
                        query_count / (query_ms / 1000)
                        if query_ms
                        else 0.0
                    ),
                    "p95_query_ms_median": _median(
                        float(row["p95_query_ms"]) for row in selected
                    ),
                    "input_triples": _median(
                        float(row["input_triples"]) for row in selected
                    ),
                    "output_triples": _median(
                        float(row["output_triples"]) for row in selected
                    ),
                    "inferred_triples": _median(
                        float(row["inferred_triples"]) for row in selected
                    ),
                }
            )
    return output


def _docker_summary_rows(
    docker_root: Path,
    *,
    architecture: str = "docker-five-node",
) -> list[dict[str, Any]]:
    output = []
    for suite, x_field in (
        ("cumulative", "stage"),
        ("scalability", "synthetic_users"),
    ):
        rows = _read(docker_root / suite / "summary.csv")
        final = _final_rows(rows, x_field)
        for reasoner in REASONER_LABELS:
            selected = [
                row for row in final if row["reasoner"] == reasoner
            ]
            query_wall = _median(
                float(row["query_wall_ms"]) for row in selected
            )
            query_count = _median(
                float(row["query_count"]) for row in selected
            )
            is_sharded = any(
                row.get("logical_input_triples", "") for row in selected
            )
            input_per_replica = _optional_median(
                selected, "input_triples_per_replica"
            )
            output_per_replica = _optional_median(
                selected, "output_triples_per_replica"
            )
            logical_input = _optional_median(
                selected, "logical_input_triples"
            )
            aggregate_fragments = _optional_median(
                selected, "aggregate_fragment_triples"
            )
            max_fragment = _optional_median(
                selected, "max_fragment_triples"
            )
            storage_factor = _optional_median(
                selected, "storage_replication_factor"
            )
            if not is_sharded and input_per_replica != "":
                logical_input = input_per_replica
                aggregate_fragments = float(input_per_replica) * 5
                max_fragment = input_per_replica
                storage_factor = 5.0
            output.append(
                {
                    "architecture": architecture,
                    "data_layout": (
                        "authority-sharded" if is_sharded else "replicated"
                    ),
                    "suite": suite,
                    "reasoner": reasoner,
                    "load_point": max(
                        float(row[x_field]) for row in selected
                    ),
                    "samples": len(selected),
                    "total_wall_ms_median": _median(
                        float(row["total_wall_ms"]) for row in selected
                    ),
                    "prepare_wall_ms_median": _median(
                        float(row["prepare_wall_ms"]) for row in selected
                    ),
                    "query_wall_ms_median": query_wall,
                    "queries_per_second": (
                        query_count / (query_wall / 1000)
                        if query_wall
                        else 0.0
                    ),
                    "node_reasoning_ms_sum_median": _median(
                        float(row["node_reasoning_ms_sum"])
                        for row in selected
                    ),
                    "node_query_ms_sum_median": _median(
                        float(row["node_query_ms_sum"])
                        for row in selected
                    ),
                    "input_triples_per_replica": input_per_replica,
                    "output_triples_per_replica": output_per_replica,
                    "logical_input_triples": logical_input,
                    "aggregate_fragment_triples": aggregate_fragments,
                    "max_fragment_triples": max_fragment,
                    "storage_replication_factor": storage_factor,
                    "replicas": 5,
                }
            )
    return output


def _deployment_summary_rows(
    comparison_root: Path,
) -> list[dict[str, Any]]:
    output = []
    for suite, x_field in (
        ("cumulative", "stage"),
        ("scalability", "synthetic_users"),
    ):
        rows = _read(comparison_root / f"{suite}.csv")
        final = _final_rows(rows, x_field)
        for reasoner in REASONER_LABELS:
            selected = [
                row for row in final if row["reasoner"] == reasoner
            ]
            speedup = _median(
                float(row["speedup"]) for row in selected
            )
            output.append(
                {
                    "suite": suite,
                    "reasoner": reasoner,
                    "load_point": max(
                        float(row[x_field]) for row in selected
                    ),
                    "samples": len(selected),
                    "monolith_total_ms_median": _median(
                        float(row["monolith_total_ms"])
                        for row in selected
                    ),
                    "docker_wall_ms_median": _median(
                        float(row["docker_wall_ms"])
                        for row in selected
                    ),
                    "speedup_median": speedup,
                    "parallel_efficiency_median": _median(
                        float(row["parallel_efficiency"])
                        for row in selected
                    ),
                    "docker_change_percent_median": _median(
                        float(row["docker_change_percent"])
                        for row in selected
                    ),
                    "faster_architecture": (
                        "docker-five-node"
                        if speedup > 1
                        else "monolith"
                    ),
                }
            )
    return output


def _complete_result_root(root: Path | None) -> bool:
    return bool(
        root
        and (root / "cumulative" / "summary.csv").is_file()
        and (root / "scalability" / "summary.csv").is_file()
    )


def generate_report(
    monolith_root: Path,
    docker_root: Path,
    output_root: Path,
    physical_root: Path | None = None,
    docker_sharded_root: Path | None = None,
    physical_sharded_root: Path | None = None,
) -> list[Path]:
    monolith_root = monolith_root.resolve()
    docker_root = docker_root.resolve()
    physical_root = physical_root.resolve() if physical_root else None
    docker_sharded_root = (
        docker_sharded_root.resolve() if docker_sharded_root else None
    )
    physical_sharded_root = (
        physical_sharded_root.resolve() if physical_sharded_root else None
    )
    output_root = output_root.resolve()
    figure_root = output_root / "figures"
    data_root = output_root / "data"
    output_root.mkdir(parents=True, exist_ok=True)

    comparison_paths = compare_all(
        monolith_root,
        docker_root,
        data_root,
    )
    outputs = list(comparison_paths)
    outputs.append(
        _write(
            data_root / "monolith-reasoner-summary.csv",
            _monolith_summary_rows(monolith_root),
        )
    )
    outputs.append(
        _write(
            data_root / "docker-reasoner-summary.csv",
            _docker_summary_rows(docker_root),
        )
    )
    product_rows = _engine_summary_rows(
        monolith_root / "engines",
        "monolith-product-stack",
    )
    product_rows.extend(
        _engine_summary_rows(
            docker_root / "engines",
            "docker-invoked-product-stack",
        )
    )
    outputs.append(
        _write(data_root / "product-engine-summary.csv", product_rows)
    )
    outputs.append(
        _write(
            data_root / "deployment-summary.csv",
            _deployment_summary_rows(data_root),
        )
    )
    outputs.extend(plot_monolith(monolith_root, figure_root))
    outputs.extend(
        plot_product_engines(
            monolith_root / "engines",
            figure_root,
            "monolith",
        )
    )
    outputs.extend(
        plot_product_engines(
            docker_root / "engines",
            figure_root,
            "docker",
        )
    )
    docker_figures, docker_data = plot_docker(
        docker_root,
        figure_root,
        data_root,
    )
    outputs.extend(docker_data)
    outputs.extend(docker_figures)
    outputs.extend(
        plot_deployment_comparison(data_root, figure_root)
    )
    architecture_roots = {
        "monolith": monolith_root,
        "docker": docker_root,
    }
    physical_included = _complete_result_root(physical_root)
    if physical_included:
        assert physical_root is not None
        architecture_roots["physical"] = physical_root
        physical_comparison = data_root / "physical-comparison"
        outputs.extend(
            compare_all(
                monolith_root,
                physical_root,
                physical_comparison,
            )
        )
        outputs.append(
            _write(
                data_root / "physical-reasoner-summary.csv",
                _docker_summary_rows(
                    physical_root,
                    architecture="physical-five-node",
                ),
            )
        )
        physical_figures, physical_data = plot_docker(
            physical_root,
            figure_root,
            data_root,
            stem_prefix="physical",
            architecture_label="Physical",
        )
        outputs.extend(physical_data)
        outputs.extend(physical_figures)
        three_figures, three_tables = plot_three_architectures(
            monolith_root,
            docker_root,
            physical_root,
            figure_root,
            data_root,
        )
        outputs.extend(three_tables)
        outputs.extend(three_figures)
        article_figures, article_tables = (
            plot_article_architecture_summary(
                monolith_root,
                docker_root,
                physical_root,
                figure_root,
                data_root,
            )
        )
        outputs.extend(article_tables)
        outputs.extend(article_figures)

    sharded_included: dict[str, bool] = {}
    for (
        architecture_key,
        sharded_root,
        stem_prefix,
        architecture_name,
    ) in (
        (
            "docker_sharded",
            docker_sharded_root,
            "docker-sharded",
            "Docker sharded",
        ),
        (
            "physical_sharded",
            physical_sharded_root,
            "physical-sharded",
            "Physical sharded",
        ),
    ):
        included = _complete_result_root(sharded_root)
        sharded_included[architecture_key] = included
        if not included:
            continue
        assert sharded_root is not None
        architecture_roots[architecture_key] = sharded_root
        comparison_root = data_root / f"{stem_prefix}-comparison"
        outputs.extend(
            compare_all(
                monolith_root,
                sharded_root,
                comparison_root,
            )
        )
        outputs.append(
            _write(
                data_root / f"{stem_prefix}-reasoner-summary.csv",
                _docker_summary_rows(
                    sharded_root,
                    architecture=f"{stem_prefix}-five-node",
                ),
            )
        )
        sharded_figures, sharded_data = plot_docker(
            sharded_root,
            figure_root,
            data_root,
            stem_prefix=stem_prefix,
            architecture_label=architecture_name,
        )
        outputs.extend(sharded_data)
        outputs.extend(sharded_figures)

    if any(sharded_included.values()):
        multi_figures, multi_tables = plot_multi_architectures(
            architecture_roots,
            figure_root,
            data_root,
        )
        outputs.extend(multi_tables)
        outputs.extend(multi_figures)

    metadata_path = output_root / "report-metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "monolith_root": str(monolith_root),
                "docker_root": str(docker_root),
                "physical_root": (
                    str(physical_root) if physical_root else None
                ),
                "physical_included": physical_included,
                "docker_sharded_root": (
                    str(docker_sharded_root) if docker_sharded_root else None
                ),
                "physical_sharded_root": (
                    str(physical_sharded_root)
                    if physical_sharded_root
                    else None
                ),
                "sharded_included": sharded_included,
                "architectures": list(architecture_roots),
                "node_count": 5,
                "reasoners": list(REASONER_LABELS),
                "product_engines": list(ENGINE_LABELS),
                "statistics": "median with min-max repetition range",
                "node_cost_definition": (
                    "sum of per-query durations; CPU-time proxy, not money, "
                    "energy or host CPU utilization"
                ),
                "figures": [str(path) for path in outputs if path.suffix != ".csv"],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    outputs.append(metadata_path)
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate monolith, five-node Docker and deployment comparison "
            "figures from benchmark CSV files, optionally including a "
            "five-host physical continuum and authority-sharded layouts."
        )
    )
    parser.add_argument("--monolith-dir", default="outputs")
    parser.add_argument("--docker-dir", default="outputs/docker/replicated")
    parser.add_argument("--physical-dir", default="outputs/physical/replicated")
    parser.add_argument(
        "--docker-sharded-dir",
        help=(
            "Optional authority-sharded Docker result root "
            "(default: outputs/docker/sharded)"
        ),
        default="outputs/docker/sharded",
    )
    parser.add_argument(
        "--physical-sharded-dir",
        help=(
            "Optional authority-sharded physical result root "
            "(default: outputs/physical/sharded)"
        ),
        default="outputs/physical/sharded",
    )
    parser.add_argument("--output-dir", default="outputs/analysis")
    parser.add_argument(
        "--show",
        action="store_true",
        help="Open generated PNG figures in the system viewer",
    )
    args = parser.parse_args(argv)
    outputs = generate_report(
        Path(args.monolith_dir),
        Path(args.docker_dir),
        Path(args.output_dir),
        Path(args.physical_dir),
        (
            Path(args.docker_sharded_dir)
            if args.docker_sharded_dir
            else None
        ),
        (
            Path(args.physical_sharded_dir)
            if args.physical_sharded_dir
            else None
        ),
    )
    if args.show:
        for path in outputs:
            if path.suffix == ".png":
                webbrowser.open(path.as_uri())
    print(
        json.dumps(
            {"comparative_report": [str(path) for path in outputs]},
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
