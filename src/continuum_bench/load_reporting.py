"""Publication plots for the multidimensional event-load experiment."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
import statistics
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, NullFormatter
import numpy as np

from .csv_utils import write_dict_rows
from .reporting import REASONER_LABELS


DIMENSION_X = {
    "events_per_second": ("events_per_second", "Eventos ofrecidos/s"),
    "users": ("synthetic_users", "Usuarios sintéticos"),
    "target_triples": ("target_triples", "Triples objetivo/nodo"),
    "rule_count": ("rule_count", "Reglas sintéticas"),
    "node_count": ("node_count", "Nodos activos"),
}
LOAD_ARCHITECTURE_LABELS = {
    "monolith": "Monolito (1 nodo)",
    "docker": "Docker local",
    "physical": "Continuum físico",
}


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _float(row: dict[str, str], field: str) -> float | None:
    value = row.get(field, "")
    if value in {"", None}:
        return None
    return float(value)


def _aggregate(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    fields = (
        "latency_p50_ms",
        "latency_p95_ms",
        "latency_p99_ms",
        "events_processed_per_second",
        "events_lost",
        "event_loss_percent",
        "inference_wall_ms",
        "pipeline_wall_ms",
        "alert_precision",
        "alert_accuracy",
        "alert_recall",
        "alert_f1",
        "cpu_percent_per_node_one_core",
        "process_cpu_time_ms",
        "max_current_rss_kib",
        "max_peak_rss_kib",
        "disk_read_bytes",
        "disk_write_bytes",
        "disk_io_bytes",
        "network_body_bytes",
        "recovery_wall_ms",
        "input_triples_per_node",
    )
    grouped: dict[tuple[str, str, str, str], list[dict[str, str]]] = (
        defaultdict(list)
    )
    for row in rows:
        grouped[
            (
                row["architecture"],
                row["profile"],
                row["dimension"],
                row["reasoner"],
            )
        ].append(row)
    output: list[dict[str, Any]] = []
    for key, samples in grouped.items():
        architecture, profile, dimension, reasoner = key
        completed = [
            row for row in samples if row["status"] == "completed"
        ]
        timeout_count = sum(
            "timeout" in row["status"] for row in samples
        )
        item: dict[str, Any] = {
            "architecture": architecture,
            "profile": profile,
            "profile_index": int(samples[0].get("profile_index", 0)),
            "dimension": dimension,
            "reasoner": reasoner,
            "samples": len(samples),
            "completed_samples": len(completed),
            "noncompleted_samples": len(samples) - len(completed),
            "completion_rate_percent": len(completed) / len(samples) * 100,
            "noncompletion_rate_percent_median": (
                (len(samples) - len(completed)) / len(samples) * 100
            ),
            "timeout_samples": timeout_count,
            "timeout_rate_percent_median": timeout_count / len(samples) * 100,
            "failed_samples": sum(
                "failed" in row["status"] for row in samples
            ),
            "comparison_eligible": len(completed) == len(samples),
            "events_per_second": float(samples[0]["events_per_second"]),
            "events_per_second_median": float(
                samples[0]["events_per_second"]
            ),
            "synthetic_users": int(samples[0]["synthetic_users"]),
            "synthetic_users_median": int(samples[0]["synthetic_users"]),
            "target_triples": int(samples[0]["target_triples"]),
            "target_triples_median": int(samples[0]["target_triples"]),
            "rule_count": int(samples[0]["rule_count"]),
            "rule_count_median": int(samples[0]["rule_count"]),
            "node_count": int(samples[0]["node_count"]),
            "node_count_median": int(samples[0]["node_count"]),
        }
        for field in fields:
            source = (
                samples
                if field in {"events_lost", "event_loss_percent"}
                else completed
            )
            values = [
                value
                for row in source
                for value in [_float(row, field)]
                if value is not None
            ]
            item[f"{field}_median"] = (
                statistics.median(values) if values else ""
            )
            item[f"{field}_min"] = min(values) if values else ""
            item[f"{field}_max"] = max(values) if values else ""
        for source, derived, divisor in (
            ("latency_p50_ms", "latency_p50_seconds", 1000),
            ("latency_p95_ms", "latency_p95_seconds", 1000),
            ("latency_p99_ms", "latency_p99_seconds", 1000),
            ("inference_wall_ms", "inference_wall_seconds", 1000),
            ("pipeline_wall_ms", "pipeline_wall_seconds", 1000),
            ("recovery_wall_ms", "recovery_wall_seconds", 1000),
            ("max_current_rss_kib", "max_current_rss_mib", 1024),
            ("disk_io_bytes", "disk_io_mib", 1024 * 1024),
            ("network_body_bytes", "network_body_mib", 1024 * 1024),
        ):
            for suffix in ("median", "min", "max"):
                raw_value = item[f"{source}_{suffix}"]
                item[f"{derived}_{suffix}"] = (
                    float(raw_value) / divisor
                    if raw_value != ""
                    else ""
                )
        output.append(item)
    return sorted(
        output,
        key=lambda row: (
            row["dimension"],
            row["architecture"],
            row["reasoner"],
            row["profile"],
        ),
    )


def _save(fig, path: Path) -> list[Path]:
    path.parent.mkdir(parents=True, exist_ok=True)
    outputs = []
    for suffix in (".png", ".pdf", ".svg"):
        output = path.with_suffix(suffix)
        fig.savefig(
            output,
            dpi=300 if suffix == ".png" else None,
            bbox_inches="tight",
        )
        outputs.append(output)
    plt.close(fig)
    return outputs


def _architecture_ratios(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compare Docker/physical rows with the matching one-node baseline."""

    monolith = [
        row for row in rows if row["architecture"] == "monolith"
    ]
    output: list[dict[str, Any]] = []

    def value(row: dict[str, Any], field: str) -> float | None:
        raw = row.get(f"{field}_median", "")
        return None if raw == "" else float(raw)

    for row in rows:
        if row["architecture"] not in {"docker", "physical"}:
            continue
        candidates = [
            baseline
            for baseline in monolith
            if baseline["reasoner"] == row["reasoner"]
            and baseline["dimension"] == row["dimension"]
            and (
                row["dimension"] == "node_count"
                or baseline["profile"] == row["profile"]
            )
        ]
        if not candidates:
            continue
        baseline = min(
            candidates,
            key=lambda item: float(item["node_count_median"]),
        )
        if (
            not row["comparison_eligible"]
            or not baseline["comparison_eligible"]
        ):
            continue
        x_field, _ = DIMENSION_X[row["dimension"]]
        item = {
            "architecture": row["architecture"],
            "profile": row["profile"],
            "dimension": row["dimension"],
            "reasoner": row["reasoner"],
            "independent_value": row[f"{x_field}_median"],
            "node_count": row["node_count_median"],
            "baseline_profile": baseline["profile"],
        }
        ratio_fields = (
            ("latency_p95_ms", "latency_speedup"),
            ("events_processed_per_second", "throughput_gain"),
            ("inference_wall_ms", "inference_speedup"),
            ("recovery_wall_ms", "recovery_speedup"),
        )
        for field, result_field in ratio_fields:
            base_value = value(baseline, field)
            distributed_value = value(row, field)
            if (
                base_value is None
                or distributed_value is None
                or base_value <= 0
                or distributed_value <= 0
            ):
                item[result_field] = ""
            elif result_field == "throughput_gain":
                item[result_field] = distributed_value / base_value
            else:
                item[result_field] = base_value / distributed_value
        gain = item["throughput_gain"]
        nodes = float(item["node_count"])
        item["scale_out_efficiency_percent"] = (
            float(gain) / nodes * 100 if gain != "" and nodes else ""
        )
        base_loss = value(baseline, "event_loss_percent")
        distributed_loss = value(row, "event_loss_percent")
        item["loss_delta_percentage_points"] = (
            distributed_loss - base_loss
            if base_loss is not None and distributed_loss is not None
            else ""
        )
        output.append(item)
    return output


def _plot_ratio_comparison(
    rows: list[dict[str, Any]],
    output_root: Path,
    colors: dict[str, Any],
    markers: dict[str, str],
) -> list[Path]:
    outputs: list[Path] = []
    styles = {"rdfs": "-", "owlrl": "--", "rdfs_owlrl": ":"}
    metrics = (
        ("latency_speedup", "Speedup de latencia p95 (×)"),
        ("throughput_gain", "Ganancia de throughput (×)"),
        ("inference_speedup", "Speedup de inferencia (×)"),
        ("recovery_speedup", "Speedup de recuperación (×)"),
        ("scale_out_efficiency_percent", "Eficiencia scale-out (%)"),
        (
            "loss_delta_percentage_points",
            "Diferencia de pérdida (p.p.)",
        ),
    )
    for dimension, (_, xlabel) in DIMENSION_X.items():
        selected_dimension = [
            row for row in rows if row["dimension"] == dimension
        ]
        if not selected_dimension:
            continue
        figure, axes = plt.subplots(2, 3, figsize=(13.0, 7.6))
        for axis, (field, ylabel) in zip(
            axes.flat,
            metrics,
            strict=True,
        ):
            for architecture in ("docker", "physical"):
                for reasoner in REASONER_LABELS:
                    selected = [
                        row
                        for row in selected_dimension
                        if row["architecture"] == architecture
                        and row["reasoner"] == reasoner
                        and row[field] != ""
                    ]
                    selected.sort(
                        key=lambda row: float(row["independent_value"])
                    )
                    if not selected:
                        continue
                    axis.plot(
                        [
                            float(row["independent_value"])
                            for row in selected
                        ],
                        [float(row[field]) for row in selected],
                        color=colors[architecture],
                        marker=markers[reasoner],
                        linestyle=styles[reasoner],
                        linewidth=1.4,
                        label=(
                            f"{LOAD_ARCHITECTURE_LABELS[architecture]} · "
                            f"{REASONER_LABELS[reasoner]}"
                        ),
                    )
            reference = {
                "loss_delta_percentage_points": 0,
                "scale_out_efficiency_percent": 100,
            }.get(field, 1)
            axis.axhline(
                reference,
                color="black",
                linewidth=0.7,
                alpha=0.5,
            )
            _style(axis, xlabel, ylabel)
        _factorized_legend(figure, colors, markers)
        if dimension in {
            "events_per_second",
            "users",
            "target_triples",
        }:
            for axis in axes.flat:
                axis.set_xscale("log")
        ratio_axis_rows = [
            {
                "dimension": dimension,
                f"{DIMENSION_X[dimension][0]}_median": row[
                    "independent_value"
                ],
            }
            for row in selected_dimension
        ]
        _format_dimension_x(axes, dimension, ratio_axis_rows)
        figure.tight_layout(rect=(0, 0, 1, 0.91))
        outputs.extend(
            _save(
                figure,
                output_root
                / "figures"
                / f"load-{dimension}-architecture-ratios",
            )
        )
    return outputs


def _style(axis, xlabel: str, ylabel: str) -> None:
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.grid(True, alpha=0.25)


def _factorized_legend(
    figure,
    colors: dict[str, Any],
    markers: dict[str, str],
    *,
    partial: bool = False,
) -> None:
    styles = {"rdfs": "-", "owlrl": "--", "rdfs_owlrl": ":"}
    handles = [
        Line2D(
            [],
            [],
            color=colors[architecture],
            linewidth=2,
            label=LOAD_ARCHITECTURE_LABELS[architecture],
        )
        for architecture in ("monolith", "docker", "physical")
    ]
    handles.extend(
        Line2D(
            [],
            [],
            color="0.3",
            marker=markers[reasoner],
            linestyle=styles[reasoner],
            label=REASONER_LABELS[reasoner],
        )
        for reasoner in REASONER_LABELS
    )
    if partial:
        handles.append(
            Line2D(
                [],
                [],
                color="0.35",
                marker="o",
                markerfacecolor="none",
                linestyle="none",
                label="Parcial (<3/3 rep.)",
            )
        )
    figure.legend(
        handles=handles,
        loc="upper center",
        ncol=len(handles),
        fontsize=7,
        frameon=False,
    )


def _format_dimension_x(
    axes,
    dimension: str,
    rows: list[dict[str, Any]],
) -> None:
    x_field, _ = DIMENSION_X[dimension]
    values = sorted(
        {
            float(row[f"{x_field}_median"])
            for row in rows
            if row["dimension"] == dimension
            and row.get(f"{x_field}_median", "") != ""
        }
    )

    def compact(value: float) -> str:
        if value >= 1000:
            scaled = value / 1000
            return (
                f"{scaled:.0f}k"
                if scaled.is_integer()
                else f"{scaled:g}k"
            )
        return f"{value:g}"

    for axis in np.asarray(axes).flat:
        axis.xaxis.set_major_locator(FixedLocator(values))
        axis.xaxis.set_minor_formatter(NullFormatter())
        axis.set_xticklabels(
            [compact(value) for value in values],
            rotation=25 if len(values) >= 5 else 0,
            ha="right" if len(values) >= 5 else "center",
        )


def _series(
    rows: list[dict[str, Any]],
    dimension: str,
    x_field: str,
) -> list[tuple[str, str, list[dict[str, Any]]]]:
    output = []
    for architecture in ("monolith", "docker", "physical"):
        for reasoner in REASONER_LABELS:
            selected = [
                row
                for row in rows
                if row["dimension"] == dimension
                and row["architecture"] == architecture
                and row["reasoner"] == reasoner
                and row[f"{x_field}_median"] != ""
            ]
            selected.sort(key=lambda row: float(row[f"{x_field}_median"]))
            if selected:
                output.append((architecture, reasoner, selected))
    return output


def _plot_lines(
    axis,
    series,
    x_field: str,
    y_field: str,
    colors: dict[str, Any],
    markers: dict[str, str],
    *,
    latency_band: bool = False,
    show_repetition_range: bool = True,
) -> None:
    styles = {"rdfs": "-", "owlrl": "--", "rdfs_owlrl": ":"}
    for architecture, reasoner, selected in series:
        selected = [
            row
            for row in selected
            if row.get(f"{y_field}_median", "") != ""
        ]
        if not selected:
            continue
        x = np.array(
            [float(row[f"{x_field}_median"]) for row in selected]
        )
        y = np.array(
            [float(row[f"{y_field}_median"]) for row in selected]
        )
        label = (
            f"{LOAD_ARCHITECTURE_LABELS[architecture]} · "
            f"{REASONER_LABELS[reasoner]}"
        )
        axis.plot(
            x,
            y,
            color=colors[architecture],
            marker=markers[reasoner],
            linestyle=styles[reasoner],
            linewidth=1.4,
            label=label,
        )
        if show_repetition_range:
            minimum = np.array(
                [float(row[f"{y_field}_min"]) for row in selected]
            )
            maximum = np.array(
                [float(row[f"{y_field}_max"]) for row in selected]
            )
            axis.errorbar(
                x,
                y,
                yerr=np.vstack((y - minimum, maximum - y)),
                color=colors[architecture],
                linestyle="none",
                linewidth=0.7,
                capsize=2,
                alpha=0.35,
            )
        partial = [
            row
            for row in selected
            if int(row["completed_samples"]) < int(row["samples"])
        ]
        if partial and y_field not in {
            "event_loss_percent",
            "noncompletion_rate_percent",
            "timeout_rate_percent",
        }:
            axis.scatter(
                [
                    float(row[f"{x_field}_median"])
                    for row in partial
                ],
                [float(row[f"{y_field}_median"]) for row in partial],
                marker=markers[reasoner],
                facecolors=[axis.get_facecolor()],
                edgecolors=colors[architecture],
                linewidths=1.4,
                s=62,
                zorder=5,
            )
        if latency_band:
            low = np.array(
                [
                    float(row["latency_p50_seconds_median"])
                    for row in selected
                ]
            )
            high = np.array(
                [
                    float(row["latency_p99_seconds_median"])
                    for row in selected
                ]
            )
            axis.fill_between(
                x,
                low,
                high,
                color=colors[architecture],
                alpha=0.08,
            )


def _data_quality_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "architecture": row["architecture"],
            "dimension": row["dimension"],
            "profile": row["profile"],
            "reasoner": row["reasoner"],
            "samples": row["samples"],
            "completed_samples": row["completed_samples"],
            "timeout_samples": row["timeout_samples"],
            "failed_samples": row["failed_samples"],
            "completion_rate_percent": row["completion_rate_percent"],
            "comparison_eligible": row["comparison_eligible"],
        }
        for row in rows
    ]


def _plot_data_coverage(
    rows: list[dict[str, Any]],
    output_root: Path,
) -> list[Path]:
    profiles = sorted(
        {
            (row["dimension"], row["profile"])
            for row in rows
        },
        key=lambda value: min(
            int(candidate["profile_index"])
            for candidate in rows
            if candidate["dimension"] == value[0]
            and candidate["profile"] == value[1]
        ),
    )
    row_keys = [
        (architecture, reasoner)
        for architecture in ("monolith", "docker", "physical")
        for reasoner in REASONER_LABELS
    ]
    lookup = {
        (
            row["architecture"],
            row["reasoner"],
            row["dimension"],
            row["profile"],
        ): row
        for row in rows
    }
    matrix = np.full((len(row_keys), len(profiles)), np.nan)
    annotations = np.full(
        (len(row_keys), len(profiles)),
        "",
        dtype=object,
    )
    for row_index, (architecture, reasoner) in enumerate(row_keys):
        for column_index, (dimension, profile) in enumerate(profiles):
            item = lookup.get(
                (architecture, reasoner, dimension, profile)
            )
            if item is None:
                continue
            matrix[row_index, column_index] = (
                float(item["completion_rate_percent"]) / 100
            )
            annotations[row_index, column_index] = (
                f"{item['completed_samples']}/{item['samples']}"
            )

    figure, axis = plt.subplots(
        figsize=(max(12.5, len(profiles) * 0.62), 5.4)
    )
    image = axis.imshow(
        matrix,
        cmap="RdYlGn",
        vmin=0,
        vmax=1,
        aspect="auto",
    )
    axis.set_xticks(range(len(profiles)))
    axis.set_xticklabels(
        [profile for _, profile in profiles],
        rotation=45,
        ha="right",
    )
    axis.set_yticks(range(len(row_keys)))
    axis.set_yticklabels(
        [
            f"{LOAD_ARCHITECTURE_LABELS[architecture]} · "
            f"{REASONER_LABELS[reasoner]}"
            for architecture, reasoner in row_keys
        ]
    )
    for row_index in range(len(row_keys)):
        for column_index in range(len(profiles)):
            if annotations[row_index, column_index]:
                fraction = matrix[row_index, column_index]
                axis.text(
                    column_index,
                    row_index,
                    annotations[row_index, column_index],
                    ha="center",
                    va="center",
                    fontsize=6,
                    color=(
                        "white"
                        if fraction <= 0.2 or fraction >= 0.8
                        else "black"
                    ),
                )
    colorbar = figure.colorbar(image, ax=axis, pad=0.01)
    colorbar.set_label("Fracción de repeticiones completadas")
    axis.set_xlabel("Perfil experimental")
    axis.set_ylabel("Arquitectura y razonador")
    figure.tight_layout()
    return _save(
        figure,
        output_root / "figures" / "load-data-coverage",
    )


def _reference_summary(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for architecture in ("monolith", "docker", "physical"):
        for reasoner in REASONER_LABELS:
            selected = [
                row
                for row in rows
                if row["architecture"] == architecture
                and row["reasoner"] == reasoner
                and row["dimension"] == "events_per_second"
                and row["comparison_eligible"]
            ]
            if not selected:
                continue
            baseline = next(
                (
                    row
                    for row in selected
                    if row["profile"] == "eps-200"
                ),
                None,
            )
            overload = next(
                (
                    row
                    for row in selected
                    if row["profile"] == "eps-2500"
                ),
                None,
            )
            if baseline is None or overload is None:
                continue
            loss_free = [
                row
                for row in selected
                if float(row["event_loss_percent_median"]) <= 1
            ]
            output.append(
                {
                    "architecture": architecture,
                    "reasoner": reasoner,
                    "max_tested_loss_free_eps": max(
                        float(row["events_per_second_median"])
                        for row in loss_free
                    ),
                    "peak_processed_eps": max(
                        float(
                            row[
                                "events_processed_per_second_median"
                            ]
                        )
                        for row in selected
                    ),
                    "latency_p95_at_200_seconds": baseline[
                        "latency_p95_seconds_median"
                    ],
                    "loss_at_2500_percent": overload[
                        "event_loss_percent_median"
                    ],
                    "cpu_at_200_percent_per_node": baseline[
                        "cpu_percent_per_node_one_core_median"
                    ],
                    "rss_at_200_mib": baseline[
                        "max_current_rss_mib_median"
                    ],
                    "inference_at_200_seconds": baseline[
                        "inference_wall_seconds_median"
                    ],
                    "recovery_at_200_seconds": baseline[
                        "recovery_wall_seconds_median"
                    ],
                }
            )
    return output


def _plot_reference_overview(
    rows: list[dict[str, Any]],
    output_root: Path,
    colors: dict[str, Any],
) -> list[Path]:
    metrics = (
        ("latency_p95_at_200_seconds", "Latencia p95 a 200 eventos/s (s)"),
        ("peak_processed_eps", "Pico de eventos procesados/s"),
        ("loss_at_2500_percent", "Pérdida a 2.500 eventos/s (%)"),
        ("rss_at_200_mib", "RSS a 200 eventos/s (MiB)"),
    )
    figure, axes = plt.subplots(2, 2, figsize=(10.8, 7.2))
    reasoners = list(REASONER_LABELS)
    positions = np.arange(len(reasoners))
    width = 0.24
    for axis, (field, ylabel) in zip(
        axes.flat,
        metrics,
        strict=True,
    ):
        for architecture_index, architecture in enumerate(
            ("monolith", "docker", "physical")
        ):
            selected = {
                row["reasoner"]: row
                for row in rows
                if row["architecture"] == architecture
            }
            values = [
                float(selected[reasoner][field])
                for reasoner in reasoners
            ]
            offset = (architecture_index - 1) * width
            bars = axis.bar(
                positions + offset,
                values,
                width,
                color=colors[architecture],
                label=LOAD_ARCHITECTURE_LABELS[architecture],
            )
            axis.bar_label(bars, fmt="%.1f", fontsize=6, padding=2)
        axis.set_xticks(positions)
        axis.set_xticklabels(
            [REASONER_LABELS[value] for value in reasoners]
        )
        axis.set_ylabel(ylabel)
        axis.grid(True, axis="y", alpha=0.25)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    figure.legend(
        handles,
        labels,
        loc="upper center",
        ncol=3,
        frameon=False,
    )
    figure.tight_layout(rect=(0, 0, 1, 0.94))
    return _save(
        figure,
        output_root / "figures" / "load-reference-overview",
    )


def plot_load_comparison(
    result_root: Path,
    output_root: Path | None = None,
) -> list[Path]:
    result_root = result_root.resolve()
    output_root = (output_root or result_root / "analysis").resolve()
    figure_root = output_root / "figures"
    if figure_root.is_dir():
        for old_figure in figure_root.glob("load-*"):
            if old_figure.is_file():
                old_figure.unlink()
    for old_table in (
        output_root / "data" / "load-architecture-ratios.csv",
        output_root / "data" / "load-data-quality.csv",
        output_root / "data" / "load-reference-summary.csv",
    ):
        old_table.unlink(missing_ok=True)
    rows: list[dict[str, str]] = []
    for architecture in ("monolith", "docker", "physical"):
        path = result_root / architecture / "summary.csv"
        if path.is_file():
            rows.extend(_read(path))
    if not rows:
        raise FileNotFoundError(
            f"No load summary files found below {result_root}"
        )
    aggregate = _aggregate(rows)
    data_path = output_root / "data" / "load-comparison-summary.csv"
    write_dict_rows(
        data_path,
        aggregate,
        empty_message="No load comparison rows",
    )
    outputs: list[Path] = [data_path]
    colors_raw = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    colors = {
        "monolith": colors_raw[0],
        "docker": colors_raw[1],
        "physical": colors_raw[2],
    }
    markers = {"rdfs": "o", "owlrl": "s", "rdfs_owlrl": "^"}
    quality = _data_quality_rows(aggregate)
    quality_path = output_root / "data" / "load-data-quality.csv"
    write_dict_rows(
        quality_path,
        quality,
        empty_message="No load quality rows",
    )
    outputs.append(quality_path)
    outputs.extend(_plot_data_coverage(aggregate, output_root))

    reference = _reference_summary(aggregate)
    if reference:
        reference_path = (
            output_root / "data" / "load-reference-summary.csv"
        )
        write_dict_rows(
            reference_path,
            reference,
            empty_message="No reference summary rows",
        )
        outputs.append(reference_path)
        outputs.extend(
            _plot_reference_overview(
                reference,
                output_root,
                colors,
            )
        )

    ratios = _architecture_ratios(aggregate)
    if ratios:
        ratio_path = (
            output_root / "data" / "load-architecture-ratios.csv"
        )
        write_dict_rows(
            ratio_path,
            ratios,
            empty_message="No load architecture ratios",
        )
        outputs.append(ratio_path)

    for dimension, (x_field, xlabel) in DIMENSION_X.items():
        series = _series(aggregate, dimension, x_field)
        if not series:
            continue
        performance, axes = plt.subplots(2, 3, figsize=(13.0, 7.6))
        performance_metrics = (
            (
                "latency_p95_seconds",
                "Latencia p95 (s); banda p50–p99",
                True,
            ),
            (
                "events_processed_per_second",
                "Eventos procesados/s",
                False,
            ),
            ("event_loss_percent", "Eventos perdidos (%)", False),
            (
                "inference_wall_seconds",
                "Inferencia crítica (s)",
                False,
            ),
            (
                "pipeline_wall_seconds",
                "Pipeline completo (s)",
                False,
            ),
            (
                "noncompletion_rate_percent",
                "Corridas no completadas (%)",
                False,
            ),
        )
        for axis, (field, ylabel, band) in zip(
            axes.flat,
            performance_metrics,
            strict=True,
        ):
            _plot_lines(
                axis,
                series,
                x_field,
                field,
                colors,
                markers,
                latency_band=band,
                show_repetition_range=(
                    not band
                    and field != "noncompletion_rate_percent"
                ),
            )
            _style(axis, xlabel, ylabel)
            if field in {
                "latency_p95_seconds",
                "inference_wall_seconds",
                "pipeline_wall_seconds",
            }:
                axis.set_yscale("log")
            if field in {
                "event_loss_percent",
                "noncompletion_rate_percent",
            }:
                axis.set_ylim(-2, 105)
        has_partial = any(
            row["dimension"] == dimension
            and 0 < int(row["completed_samples"]) < int(row["samples"])
            for row in aggregate
        )
        _factorized_legend(
            performance,
            colors,
            markers,
            partial=has_partial,
        )
        if dimension in {
            "events_per_second",
            "users",
            "target_triples",
        }:
            for axis in axes.flat:
                axis.set_xscale("log")
        _format_dimension_x(axes, dimension, aggregate)
        performance.tight_layout(rect=(0, 0, 1, 0.89))
        outputs.extend(
            _save(
                performance,
                output_root / "figures" / f"load-{dimension}-performance",
            )
        )

        resources, axes = plt.subplots(2, 3, figsize=(13.0, 7.6))
        resource_metrics = (
            ("alert_accuracy", "Exactitud de alertas"),
            (
                "cpu_percent_per_node_one_core",
                "CPU media/nodo (% de un núcleo)",
            ),
            ("max_current_rss_mib", "RSS observada máxima (MiB)"),
            ("disk_io_mib", "E/S de disco (MiB)"),
            ("network_body_mib", "Red HTTP útil (MiB)"),
            (
                "recovery_wall_seconds",
                "Recuperación de estado (s)",
            ),
        )
        for axis, (field, ylabel) in zip(
            axes.flat,
            resource_metrics,
            strict=True,
        ):
            _plot_lines(
                axis,
                series,
                x_field,
                field,
                colors,
                markers,
            )
            _style(axis, xlabel, ylabel)
            if field == "alert_accuracy":
                axis.set_ylim(0.98, 1.002)
            if field == "cpu_percent_per_node_one_core":
                axis.set_ylim(0, 105)
            if field == "recovery_wall_seconds":
                axis.set_yscale("log")
        _factorized_legend(
            resources,
            colors,
            markers,
            partial=has_partial,
        )
        if dimension in {
            "events_per_second",
            "users",
            "target_triples",
        }:
            for axis in axes.flat:
                axis.set_xscale("log")
        _format_dimension_x(axes, dimension, aggregate)
        resources.tight_layout(rect=(0, 0, 1, 0.89))
        outputs.extend(
            _save(
                resources,
                output_root / "figures" / f"load-{dimension}-resources",
            )
        )
    if ratios:
        outputs.extend(
            _plot_ratio_comparison(
                ratios,
                output_root,
                colors,
                markers,
            )
        )
    return outputs
