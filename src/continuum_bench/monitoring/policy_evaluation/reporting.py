"""PNG-only scientific figures for the four policy-monitoring experiments."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Callable
import csv
import json

from ...plot_environment import configure_matplotlib

configure_matplotlib()
import matplotlib.pyplot as plt
import numpy as np

from ..figure_style import save_png
from .runner import EXPERIMENTS, RESULT_FILES


COLORS = {
    "static": "#9aa9b8",
    "policy_driven": "#145da0",
    "normal": "#dcefd5",
    "overload": "#fff0bd",
    "failure": "#f7cccc",
    "recovery": "#d7eed7",
    "evaluation": "#ef7c24",
    "plan": "#5b8fc2",
    "reasoning": "#6b4fa1",
}


def _rows(root: Path, experiment: str) -> list[dict[str, str]]:
    path = root / experiment / RESULT_FILES[experiment]
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle) if row.get("status") == "completed"]


def _header(figure, number: int, title: str, subtitle: str) -> None:
    figure.patch.set_facecolor("white")
    figure.text(
        0.02,
        0.965,
        f"Fig. {number}. {title}",
        color="#222222",
        fontsize=12,
        fontweight="bold",
        ha="left",
        va="top",
    )
    figure.text(0.02, 0.905, subtitle, color="#3c4858", fontsize=9, ha="left", va="top")


def _style(axis) -> None:
    axis.grid(axis="y", alpha=0.22, linewidth=0.7)
    axis.spines[["top", "right"]].set_visible(False)


def _group(rows: list[dict[str, str]], keys: tuple[str, ...], value: str) -> dict[tuple[str, ...], tuple[float, float]]:
    grouped: dict[tuple[str, ...], list[float]] = defaultdict(list)
    for row in rows:
        raw = row.get(value, "")
        if raw != "":
            grouped[tuple(row[key] for key in keys)].append(float(raw))
    return {
        key: (mean(values), pstdev(values) if len(values) > 1 else 0.0)
        for key, values in grouped.items()
    }


def _repetition_means(rows, strategy: str, field: str) -> list[float]:
    """Use repetitions, not individual scenarios, as the uncertainty unit."""
    grouped = defaultdict(list)
    for row in rows:
        if row["strategy"] == strategy:
            grouped[row["repetition"]].append(float(row[field]))
    return [mean(values) for values in grouped.values()]


def _per_decision_cost(row, field: str) -> float:
    """Amortize the once-per-batch reasoning probe before stacking costs."""
    value = float(row[field])
    if field == "reasoning_ms":
        iterations = int(row["decision_iterations"])
        if iterations <= 0:
            raise ValueError("decision_iterations must be positive")
        return value / iterations
    return value


def plot_effectiveness(root: Path) -> list[Path]:
    rows = _rows(root, "effectiveness")
    if not rows:
        return []
    figure, axes = plt.subplots(1, 2, figsize=(12.4, 5.2))
    _header(
        figure,
        1,
        "Policy effectiveness in monitoring decisions",
        "Configured plan agreement, averaged across scenarios; bars show mean and population SD of repetition means.",
    )
    strategies = ("static", "policy_driven")
    labels = ("Coverage", "Precision", "Over-monitoring", "Under-monitoring")
    fields = ("coverage_recall", "precision", "over_monitoring", "under_monitoring")
    x = np.arange(len(fields))
    width = 0.34
    for offset, strategy in enumerate(strategies):
        means: list[float] = []
        errors: list[float] = []
        for field in fields:
            samples = [value * 100 for value in _repetition_means(rows, strategy, field)]
            means.append(mean(samples))
            errors.append(pstdev(samples) if len(samples) > 1 else 0.0)
        positions = x + (offset - 0.5) * width
        bars = axes[0].bar(
            positions,
            means,
            width,
            yerr=errors,
            capsize=3,
            label=strategy.replace("_", " ").title(),
            color=COLORS[strategy],
        )
        axes[0].bar_label(bars, fmt="%.1f", fontsize=8, padding=2)
    axes[0].set_xticks(x, labels, rotation=12, ha="right")
    axes[0].set_ylabel("Percentage (%)")
    axes[0].set_ylim(0, 108)
    axes[0].legend(frameon=False, ncol=2)
    axes[0].set_title("Functional quality")
    _style(axes[0])

    scenarios = list(dict.fromkeys(row["scenario_id"] for row in rows))
    policy_rows = [row for row in rows if row["strategy"] == "policy_driven"]
    matrix = np.array(
        [
            [
                mean(float(row[field]) * 100 for row in policy_rows if row["scenario_id"] == scenario)
                for field in ("coverage_recall", "precision")
            ]
            for scenario in scenarios
        ]
    )
    image = axes[1].imshow(matrix, vmin=0, vmax=100, cmap="Blues", aspect="auto")
    axes[1].set_xticks((0, 1), ("Coverage", "Precision"))
    axes[1].set_yticks(range(len(scenarios)), [item.replace("S", "S", 1).replace("-", " · ", 1) for item in scenarios])
    axes[1].set_title("Policy-driven agreement by scenario")
    for row_index in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            axes[1].text(column, row_index, f"{matrix[row_index, column]:.1f}%", ha="center", va="center", color="white" if matrix[row_index, column] > 55 else "#222")
    figure.colorbar(image, ax=axes[1], label="Configured-plan agreement (%)", fraction=0.046, pad=0.04)
    figure.subplots_adjust(top=0.82, bottom=0.16, left=0.07, right=0.96, wspace=0.28)
    return save_png(figure, root / "effectiveness" / "policy-effectiveness")


def plot_dynamic_adaptation(root: Path) -> list[Path]:
    rows = _rows(root, "dynamic-adaptation")
    if not rows:
        return []
    grouped = _group(rows, ("transition", "new_context"), "total_adaptation_latency_ms")
    transitions = sorted({int(row["transition"]) for row in rows})
    representative = {
        int(row["transition"]): row
        for row in rows
        if row["repetition"] == min(item["repetition"] for item in rows)
    }
    contexts = [representative[index]["new_context"] for index in transitions]
    times = [float(representative[index]["context_timestamp_seconds"]) for index in transitions]
    interval = times[1] - times[0] if len(times) > 1 else 1.0
    centers = [time_value + interval / 2 for time_value in times]
    figure, axes = plt.subplots(3, 1, figsize=(11.8, 8.0), sharex=True)
    _header(
        figure,
        2,
        "Dynamic adaptation to context changes",
        "Supplied normal → overload → failure → recovery contexts on a simulated timeline; no physical fault injection.",
    )
    for axis in axes:
        for time_value, context in zip(times, contexts):
            axis.axvspan(time_value, time_value + interval, color=COLORS[context], alpha=0.72, linewidth=0)
        _style(axis)
    total = [grouped[(str(index), contexts[index])][0] for index in transitions]
    total_sd = [grouped[(str(index), contexts[index])][1] for index in transitions]
    axes[0].errorbar(centers, total, yerr=total_sd, marker="o", linewidth=2, capsize=3, color="#145da0", label="Decision plus reasoning probe")
    axes[0].set_ylabel("Latency (ms)")
    axes[0].set_title("Controlled transition processing cost")
    axes[0].legend(frameon=False)

    active_policies = [float(representative[index]["active_policy_count"]) for index in transitions]
    active_metrics = [float(representative[index]["active_metric_count"]) for index in transitions]
    extended_times = times + [times[-1] + interval]
    axes[1].step(extended_times, active_policies + [active_policies[-1]], where="post", linewidth=2.2, color="#ef7c24", label="Active policies")
    axes[1].step(extended_times, active_metrics + [active_metrics[-1]], where="post", linewidth=2.2, color="#2b8c6b", label="Active metrics")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Resulting monitoring configuration")
    axes[1].legend(frameon=False, ncol=2)

    components = (
        ("reasoning_ms", "Separate reasoning probe", COLORS["reasoning"]),
        ("policy_evaluation_latency_ms", "Policy evaluation", COLORS["evaluation"]),
        ("monitoring_plan_generation_latency_ms", "Plan generation", COLORS["plan"]),
        ("detection_latency_ms", "Context read", "#7f8c8d"),
    )
    bottom = np.zeros(len(times))
    for field, label, color in components:
        values = np.array([mean(float(row[field]) for row in rows if int(row["transition"]) == index) for index in transitions])
        axes[2].bar(centers, values, width=interval * 0.56, bottom=bottom, label=label, color=color)
        bottom += values
    sampling = [float(json.loads(representative[index]["monitoring_plan"])["sampling_interval_seconds"]) for index in transitions]
    twin = axes[2].twinx()
    twin.plot(centers, sampling, color="#111111", marker="D", linestyle="--", label="Sampling interval")
    twin.set_ylabel("Sampling interval (s)")
    axes[2].set_ylim(0, max(float(bottom.max()), 1e-9) * 1.35)
    twin.set_ylim(0, max(max(sampling), 1e-9) * 1.35)
    twin.spines["top"].set_visible(False)
    axes[2].set_ylabel("Latency components (ms)")
    axes[2].set_xlabel(f"Simulated context timeline ({interval:g} s between transitions)")
    axes[2].set_title("Adaptation cost and sampling response")
    handles, labels = axes[2].get_legend_handles_labels()
    twin_handles, twin_labels = twin.get_legend_handles_labels()
    axes[2].legend(handles + twin_handles, labels + twin_labels, frameon=False, ncol=3, fontsize=8, loc="upper left")
    axes[2].set_xlim(times[0] - interval * 0.08, times[-1] + interval)
    axes[2].set_xticks(centers, [context.title() for context in contexts])
    figure.subplots_adjust(top=0.84, bottom=0.09, left=0.09, right=0.9, hspace=0.42)
    return save_png(figure, root / "dynamic-adaptation" / "dynamic-adaptation")


def plot_scalability(root: Path) -> list[Path]:
    rows = _rows(root, "scalability")
    if not rows:
        return []
    levels = sorted({(int(row["load_size"]), row["scenario_id"], int(row["resource_count"]), int(row["policy_count"]), int(row["event_count"])) for row in rows})
    indices = [item[0] for item in levels]
    labels = [f"{name}\nR={resources} P={policies}\nE={events}" for _, name, resources, policies, events in levels]
    figure, axes = plt.subplots(2, 2, figsize=(12.4, 8.0))
    _header(
        figure,
        3,
        "Scalability of the policy-driven monitoring architecture",
        "R, P and E denote continuum resources, evaluable policies and context events; uncertainty bars show population SD.",
    )

    def series(field: str) -> tuple[list[float], list[float]]:
        grouped = _group(rows, ("load_size",), field)
        return [grouped[(str(index),)][0] for index in indices], [grouped[(str(index),)][1] for index in indices]

    latency, latency_sd = series("decision_latency_mean_ms")
    p95, p95_sd = series("decision_latency_p95_ms")
    axes[0, 0].errorbar(indices, latency, yerr=latency_sd, marker="o", linewidth=2, capsize=3, label="Mean")
    axes[0, 0].errorbar(indices, p95, yerr=p95_sd, marker="s", linewidth=2, capsize=3, label="p95")
    axes[0, 0].set_ylabel("Decision latency (ms)")
    axes[0, 0].set_title("Decision latency")
    axes[0, 0].legend(frameon=False)

    decision_throughput, decision_throughput_sd = series("throughput_decisions_per_second")
    end_to_end, end_to_end_sd = series("end_to_end_throughput_events_per_second")
    axes[0, 1].errorbar(indices, decision_throughput, yerr=decision_throughput_sd, marker="o", linewidth=2, capsize=3, label="Decision stage")
    axes[0, 1].errorbar(indices, end_to_end, yerr=end_to_end_sd, marker="s", linewidth=2, capsize=3, label="End to end")
    axes[0, 1].set_ylabel("Events/s")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_title("Throughput")
    axes[0, 1].legend(frameon=False)

    cpu_mean, cpu_sd = series("cpu_mean_percent")
    cpu_max, cpu_max_sd = series("cpu_max_percent")
    axes[1, 0].errorbar(indices, cpu_mean, yerr=cpu_sd, marker="o", linewidth=2, capsize=3, label="Mean")
    axes[1, 0].errorbar(indices, cpu_max, yerr=cpu_max_sd, marker="s", linewidth=2, capsize=3, label="Maximum")
    axes[1, 0].set_ylabel("Process CPU (% of one core)")
    axes[1, 0].set_title("CPU cost")
    axes[1, 0].legend(frameon=False)

    ram_mean, ram_sd = series("ram_mean_mib")
    ram_max, ram_max_sd = series("ram_max_mib")
    axes[1, 1].errorbar(indices, ram_mean, yerr=ram_sd, marker="o", linewidth=2, capsize=3, label="Mean")
    axes[1, 1].errorbar(indices, ram_max, yerr=ram_max_sd, marker="s", linewidth=2, capsize=3, label="Maximum")
    axes[1, 1].set_ylabel("Resident memory (MiB)")
    axes[1, 1].set_title("Memory cost")
    axes[1, 1].legend(frameon=False)
    for axis in axes.flat:
        axis.set_xticks(indices, labels, fontsize=8)
        _style(axis)
    figure.subplots_adjust(top=0.84, bottom=0.14, left=0.08, right=0.97, hspace=0.48, wspace=0.28)
    return save_png(figure, root / "scalability" / "policy-scalability")


def plot_computational_cost(root: Path) -> list[Path]:
    rows = _rows(root, "computational-cost")
    if not rows:
        return []
    figure, axes = plt.subplots(2, 2, figsize=(12.4, 8.0))
    _header(
        figure,
        4,
        "Controlled monitoring plans and computational cost",
        "Static and policy-driven strategies execute the same scenarios and resources; network traffic is an explicit payload-size estimate.",
    )
    strategies = ("static", "policy_driven")
    names = ("Static", "Policy-driven")
    colors = [COLORS[item] for item in strategies]

    def values(field: str) -> tuple[list[float], list[float]]:
        grouped = _group(rows, ("strategy",), field)
        return [grouped[(strategy,)][0] for strategy in strategies], [grouped[(strategy,)][1] for strategy in strategies]

    cpu_samples = [
        np.array([float(row["cpu_time_per_decision_ms"]) for row in rows if row["strategy"] == strategy])
        for strategy in strategies
    ]
    cpu = [float(np.median(samples)) for samples in cpu_samples]
    cpu_error = np.vstack(
        (
            [center - float(np.percentile(samples, 25)) for center, samples in zip(cpu, cpu_samples)],
            [float(np.percentile(samples, 75)) - center for center, samples in zip(cpu, cpu_samples)],
        )
    )
    bars = axes[0, 0].bar(names, cpu, yerr=cpu_error, capsize=4, color=colors)
    axes[0, 0].bar_label(bars, fmt="%.4f", fontsize=8)
    axes[0, 0].set_ylim(bottom=0)
    axes[0, 0].set_ylabel("CPU time per decision (ms)")
    axes[0, 0].set_title("Median amortized CPU cost (IQR)")

    ram, ram_sd = values("ram_max_mib")
    bars = axes[0, 1].bar(names, ram, yerr=ram_sd, capsize=4, color=colors)
    axes[0, 1].bar_label(bars, fmt="%.1f", fontsize=8)
    axes[0, 1].set_ylabel("Resident memory (MiB)")
    axes[0, 1].set_title("Sampled peak memory (scenario/repetition SD)")

    observations, observations_sd = values("observations_generated")
    observation_error = np.vstack(
        (np.minimum(np.array(observations), np.array(observations_sd)), np.array(observations_sd))
    )
    bars = axes[1, 0].bar(names, observations, yerr=observation_error, capsize=4, color=colors)
    axes[1, 0].set_ylim(bottom=0)
    axes[1, 0].bar_label(bars, fmt="%.0f", fontsize=8)
    axes[1, 0].set_ylabel("Observations per scenario window")
    axes[1, 0].set_title("Estimated monitoring volume")

    policy_rows = [row for row in rows if row["strategy"] == "policy_driven"]
    breakdown_fields = (
        ("reasoning_ms", "Separate reasoning probe", COLORS["reasoning"]),
        ("policy_evaluation_ms", "Policy evaluation", COLORS["evaluation"]),
        ("monitoring_plan_generation_ms", "Plan generation", COLORS["plan"]),
    )
    scenarios = list(dict.fromkeys(row["scenario_id"] for row in policy_rows))
    bottom = np.zeros(len(scenarios))
    for field, label, color in breakdown_fields:
        component = np.array([mean(_per_decision_cost(row, field) for row in policy_rows if row["scenario_id"] == scenario) for scenario in scenarios])
        axes[1, 1].bar(range(len(scenarios)), component, bottom=bottom, label=label, color=color)
        bottom += component
    axes[1, 1].set_xticks(range(len(scenarios)), [scenario.split("-", 1)[1].title() for scenario in scenarios], rotation=12)
    axes[1, 1].set_ylabel("Amortized cost per decision (ms)")
    axes[1, 1].set_title("Decision cost plus amortized reasoning probe")
    axes[1, 1].legend(frameon=False, fontsize=8)
    for axis in axes.flat:
        _style(axis)
    figure.subplots_adjust(top=0.84, bottom=0.12, left=0.08, right=0.97, hspace=0.42, wspace=0.28)
    return save_png(figure, root / "computational-cost" / "computational-cost")


PLOTTERS: dict[str, Callable[[Path], list[Path]]] = {
    "effectiveness": plot_effectiveness,
    "dynamic-adaptation": plot_dynamic_adaptation,
    "scalability": plot_scalability,
    "computational-cost": plot_computational_cost,
}


def plot_policy_evaluation(root: Path, selected=EXPERIMENTS) -> list[Path]:
    outputs: list[Path] = []
    for name in selected:
        outputs.extend(PLOTTERS[name](root))
    return outputs
