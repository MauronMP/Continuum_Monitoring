"""PNG diagnostics with explicit placement labels and visible failed-point counts."""

from collections import defaultdict
import json
from pathlib import Path
import statistics

from .runner import read_rows


def placement_order(result_path, observed, key):
    """Keep continuum tier order rather than sorting physical host names alphabetically."""
    manifest = result_path.parents[2] / "placement.json"
    recorded = (
        json.loads(manifest.read_text()).get(key, []) if manifest.exists() else []
    )
    ordered = [node["id"] for node in recorded if node["id"] in observed]
    return ordered + sorted(set(observed) - set(ordered))


def report(directory: Path):
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams.update(
        {"font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8, "legend.fontsize": 7}
    )
    import matplotlib.pyplot as plt

    figures = directory / "figures"
    figures.mkdir(exist_ok=True)
    manifest = early_failure_figures(directory, figures)
    for path in sorted(
        directory.glob("placement-*/*/measured/distributed-reasoning-scalability")
    ):
        scenario = path.parents[1].name
        placement = path.parents[2].name
        rows = read_rows(path / "distributed-reasoning-summary.csv")
        nodes = read_rows(path / "node-runs.csv")
        if not rows:
            continue
        label = f"{placement} / {scenario}"
        failed = sum(r["status"] != "completed" for r in rows)
        groups = defaultdict(list)
        for r in rows:
            if r["status"] == "completed":
                groups[(r["layout"], r["reasoner"])].append(r)
        if groups:
            fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.4), layout="constrained")
            for ax, metric, title in zip(
                axes,
                ["benchmark_end_to_end_ms", "reasoning_ms", "current_rss_kib_sum"],
                [
                    "Preparation incl. coordination (ms)",
                    "Reasoning critical path (ms)",
                    "Sum of process RSS (MiB)",
                ],
            ):
                for i, (key, items) in enumerate(sorted(groups.items())):
                    values = [
                        float(r[metric]) / (1024 if "rss" in metric else 1)
                        for r in items
                    ]
                    ax.scatter([i] * len(values), values, s=25, alpha=0.65)
                    ax.plot(
                        [i - 0.2, i + 0.2],
                        [statistics.median(values)] * 2,
                        color="black",
                        linewidth=2,
                    )
                ax.set_xticks(
                    range(len(groups)),
                    [" / ".join(k) for k in sorted(groups)],
                    rotation=25,
                    ha="right",
                )
                ax.set_ylabel(title)
                ax.grid(axis="y", alpha=0.25)
            fig.suptitle(
                f"{label} — completed repetitions; {failed}/{len(rows)} non-completed\nPoints: repetitions; black line: median. Participants share physical resources.",
                fontsize=10,
            )
            name = f"{placement}-{scenario}-costs.png"
            fig.savefig(figures / name, dpi=300, bbox_inches="tight", pad_inches=0.1)
            plt.close(fig)
            manifest.append(name)
        if nodes:
            fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.5), layout="constrained")
            ids = placement_order(path, {r["node_id"] for r in nodes}, "participants")
            combinations = sorted({(r["layout"], r["reasoner"]) for r in nodes})
            for ax, metric, title in zip(
                axes,
                ["reasoning_ms", "current_rss_kib"],
                ["Reasoning time (ms)", "Process RSS (MiB)"],
            ):
                for index, key in enumerate(combinations):
                    ys = []
                    for identity in ids:
                        values = [
                            float(r[metric]) / (1024 if "rss" in metric else 1)
                            for r in nodes
                            if r["node_id"] == identity
                            and (r["layout"], r["reasoner"]) == key
                        ]
                        ys.append(statistics.median(values) if values else float("nan"))
                    positions = [
                        i
                        + (index - (len(combinations) - 1) / 2)
                        * min(0.18, 0.7 / len(combinations))
                        for i in range(len(ids))
                    ]
                    ax.plot(
                        positions,
                        ys,
                        marker="o",
                        linestyle="none",
                        label=" / ".join(key),
                    )
                ax.set_xticks(range(len(ids)), ids, rotation=35, ha="right")
                ax.set_ylabel(title)
                ax.grid(axis="y", alpha=0.25)
                ax.legend(fontsize=8)
            fig.suptitle(
                f"{label}\nLogical participants grouped by physical host",
                fontsize=9,
            )
            name = f"{placement}-{scenario}-participants.png"
            fig.savefig(figures / name, dpi=300, bbox_inches="tight", pad_inches=0.1)
            plt.close(fig)
            manifest.append(name)
        fig, ax = plt.subplots(figsize=(7, 4), layout="constrained")
        statuses = sorted({r["status"] for r in rows})
        ax.bar(statuses, [sum(r["status"] == s for r in rows) for s in statuses])
        ax.set_ylabel("Measured executions")
        ax.set_title(f"{label}: completion and failures")
        name = f"{placement}-{scenario}-status.png"
        fig.savefig(figures / name, dpi=300, bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)
        manifest.append(name)
    manifest.extend(campaign_figures(directory, figures))
    from .synthesis import synthesis
    manifest.extend(synthesis(directory, figures))
    from .resources import resource_figures
    manifest.extend(resource_figures(directory, figures))
    from .diagnostics import diagnostic_figures
    manifest.extend(diagnostic_figures(directory, figures))
    (figures / "manifest.json").write_text(
        json.dumps(
            {
                "figures": manifest,
                "limitations": [
                    "Completed-only cost plots must be read alongside status plots.",
                    "Process RSS is not whole-host memory or cgroup memory.",
                    "No interpolation or invented values for missing executions.",
                ],
            },
            indent=2,
        )
        + "\n"
    )
    return figures


def early_failure_figures(directory: Path, figures: Path) -> list[str]:
    """Render honest diagnostics when deployment ends before measured evidence exists."""
    import matplotlib.pyplot as plt
    import numpy as np

    campaign_path = directory / "campaign.json"
    configuration_path = directory / "configuration.json"
    if not campaign_path.exists() or not configuration_path.exists():
        return []
    campaign = json.loads(campaign_path.read_text())
    if campaign.get("steps") or campaign.get("status") not in ("failed", "interrupted"):
        return []

    error = str(campaign.get("error", "Campaign ended before the first scenario"))
    stages = ["Configuration", "Placement", "Deployment", "Warm-up", "Measured run"]
    states = ["completed", "completed", "failed", "not started", "not started"]
    colors = ["#009E73", "#009E73", "#D55E00", "#BDBDBD", "#BDBDBD"]
    fig, ax = plt.subplots(figsize=(7.2, 2.7), layout="constrained")
    positions = np.arange(len(stages))
    ax.barh([0] * len(stages), [0.82] * len(stages), left=positions,
            color=colors, edgecolor="#555555", height=0.46)
    for index, (stage, state) in enumerate(zip(stages, states)):
        ax.text(index + 0.41, 0, f"{stage}\n{state}", ha="center", va="center",
                color="white" if state != "not started" else "#333333", fontsize=8)
        if index < len(stages) - 1:
            ax.annotate("", xy=(index + 0.98, 0), xytext=(index + 0.84, 0),
                        arrowprops=dict(arrowstyle="->", color="#444444"))
    ax.set(xlim=(-0.05, len(stages)), ylim=(-0.7, 0.85))
    ax.axis("off")
    ax.set_title("Campaign stopped before experimental execution", fontsize=11)
    ax.text(0, -0.52, error, ha="left", va="center", fontsize=8, color="#7A1F00",
            wrap=True, transform=ax.transData)
    name = "campaign-early-failure-stage.png"
    fig.savefig(figures / name, dpi=300, bbox_inches="tight", pad_inches=.12)
    plt.close(fig)

    configuration = json.loads(configuration_path.read_text())
    scenarios = [item["name"] for item in configuration.get("scenarios", [])]
    layouts = configuration.get("experiment", {}).get("layouts", [])
    matrix = np.zeros((len(layouts), len(scenarios)))
    fig, ax = plt.subplots(figsize=(7.2, max(2.4, .55 * len(layouts) + 1.5)),
                           layout="constrained")
    ax.imshow(matrix, vmin=0, vmax=1, cmap="Greys", aspect="auto")
    ax.set_xticks(range(len(scenarios)), scenarios, rotation=35, ha="right")
    ax.set_yticks(range(len(layouts)), layouts)
    ax.set_xlabel("Configured scenario")
    ax.set_ylabel("Layout")
    for row in range(len(layouts)):
        for column in range(len(scenarios)):
            ax.text(column, row, "not run", ha="center", va="center", fontsize=7,
                    color="#555555")
    ax.set_title("Measured evidence coverage: 0 scenarios executed\n"
                 "Deployment failure is not a zero-performance measurement", fontsize=10)
    name2 = "campaign-measurement-coverage.png"
    fig.savefig(figures / name2, dpi=300, bbox_inches="tight", pad_inches=.12)
    plt.close(fig)
    return [name, name2]


def campaign_figures(directory, figures):
    """Compare load points; retain raw request counts as a common throughput unit."""
    import matplotlib.pyplot as plt

    configuration = json.loads((directory / "configuration.json").read_text())
    scenarios = {s["name"]: s for s in configuration["scenarios"]}
    gathered = []
    manifest = []
    for path in sorted(
        directory.glob("placement-*/*/measured/distributed-reasoning-scalability")
    ):
        scenario = path.parents[1].name
        placement = path.parents[2].name
        for row in read_rows(path / "distributed-reasoning-summary.csv"):
            gathered.append(
                {
                    **row,
                    "scenario": scenario,
                    "placement": placement,
                    "family": scenarios[scenario]["family"],
                    "users": scenarios[scenario]["users"],
                }
            )
        query_rows = read_rows(path / "client-throughput.csv")
        if query_rows:
            fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.4), layout="constrained")
            combos = sorted({(r["layout"], r["reasoner"]) for r in query_rows})
            for ax, key, title in zip(
                axes,
                ["latency_p95_ms", "client_requests_per_second", "error_rate"],
                [
                    "Request p95 latency (ms)",
                    "Completed catalog requests/s",
                    "Request error fraction",
                ],
            ):
                for combo in combos:
                    selected = [
                        r
                        for r in query_rows
                        if (r["layout"], r["reasoner"]) == combo
                        and r.get(key) not in (None, "")
                    ]
                    levels = sorted({int(r["concurrency"]) for r in selected})
                    values = [
                        statistics.median(
                            float(r[key])
                            for r in selected
                            if int(r["concurrency"]) == c
                        )
                        for c in levels
                    ]
                    ax.plot(levels, values, marker="o", label=" / ".join(combo))
                ax.set_xlabel("Concurrent catalog requests")
                ax.set_ylabel(title)
                ax.grid(alpha=0.25)
            axes[0].legend(fontsize=8)
            fig.suptitle(
                f"{placement} / {scenario}\np95 excludes failed requests; errors shown separately",
                fontsize=10,
            )
            name = f"{placement}-{scenario}-requests.png"
            fig.savefig(figures / name, dpi=300, bbox_inches="tight", pad_inches=0.1)
            plt.close(fig)
            manifest.append(name)
        nodes = read_rows(path / "node-runs.csv")
        if nodes:
            by_run = defaultdict(lambda: defaultdict(float))
            for r in nodes:
                host = r["node_id"].rsplit("-c", 1)[0]
                group = (host, r["layout"], r["reasoner"], r["run_id"])
                by_run[group]["rss"] += float(r["current_rss_kib"]) / 1024
                by_run[group]["cpu"] += float(r["process_cpu_ms"])
            hosts = placement_order(path, {g[0] for g in by_run}, "physical_hosts")
            combos = sorted({(g[1], g[2]) for g in by_run})
            fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.5), layout="constrained")
            for ax, key, title in zip(
                axes,
                ["rss", "cpu"],
                [
                    "Sum of participant process RSS (MiB)",
                    "Sum of participant CPU time (ms)",
                ],
            ):
                for index, combo in enumerate(combos):
                    values = []
                    for h in hosts:
                        samples = [
                            v[key]
                            for g, v in by_run.items()
                            if g[0] == h and (g[1], g[2]) == combo
                        ]
                        values.append(
                            statistics.median(samples) if samples else float("nan")
                        )
                    positions = [
                        i
                        + (index - (len(combos) - 1) / 2) * min(0.18, 0.7 / len(combos))
                        for i in range(len(hosts))
                    ]
                    ax.plot(
                        positions,
                        values,
                        marker="o",
                        linestyle="none",
                        label=" / ".join(combo),
                    )
                ax.set_xticks(range(len(hosts)), hosts)
                ax.set_ylabel(title)
                ax.tick_params(axis="x", rotation=25)
                ax.grid(alpha=0.25)
            axes[0].legend(fontsize=8)
            fig.suptitle(
                f"{placement} / {scenario}\nPhysical hosts: completed preparations only",
                fontsize=10,
            )
            name = f"{placement}-{scenario}-hosts.png"
            fig.savefig(figures / name, dpi=300, bbox_inches="tight", pad_inches=0.1)
            plt.close(fig)
            manifest.append(name)
    # Requests vary concurrency, not graph size; use the dedicated request plot.
    (figures / "requests-scaling.png").unlink(missing_ok=True)
    for family in sorted({r["family"] for r in gathered} - {"requests"}):
        selected = [
            r for r in gathered if r["family"] == family and r["status"] == "completed"
        ]
        if not selected:
            continue
        fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.5), layout="constrained")
        placement_axis = family in ("strong", "weak")
        combos = sorted(
            {
                (r["layout"], r["reasoner"], "" if placement_axis else r["placement"])
                for r in selected
            }
        )
        for ax, metric, title in zip(
            axes,
            ["benchmark_end_to_end_ms", "current_rss_kib_sum"],
            ["Preparation time (ms)", "Sum of process RSS (MiB)"],
        ):
            for combo in combos:
                points = [
                    r
                    for r in selected
                    if (
                        r["layout"],
                        r["reasoner"],
                        "" if placement_axis else r["placement"],
                    )
                    == combo
                ]
                xkey = (
                    "node_count"
                    if placement_axis
                    else ("users" if family == "users" else "asserted_triples")
                )
                levels = sorted({int(r[xkey]) for r in points})
                ys = [
                    statistics.median(
                        float(r[metric]) / (1024 if "rss" in metric else 1)
                        for r in points
                        if int(r[xkey]) == x
                    )
                    for x in levels
                ]
                ax.plot(levels, ys, marker="o", label=" / ".join(combo))
            if family == "users":
                user_levels = sorted({int(r["users"]) for r in selected})
                campaign_file = directory / "campaign.json"
                if campaign_file.exists():
                    steps = json.loads(campaign_file.read_text()).get("steps", [])
                    user_levels = sorted(set(user_levels) | {
                        scenarios[s["scenario"]]["users"] for s in steps
                        if scenarios[s["scenario"]]["family"] == "users"
                    })
                observed = {int(r["users"]) for r in selected}
                for level in set(user_levels) - observed:
                    ax.text(level, .03, "NA", transform=ax.get_xaxis_transform(), ha="center")
                if user_levels[0] > 0 and user_levels[-1] / user_levels[0] >= 100:
                    ax.set_xscale("log")
                    ax.set_xlim(user_levels[0] / 1.5, user_levels[-1] * 1.5)
                    ax.set_xticks(user_levels, [str(level) for level in user_levels])
                    ax.tick_params(axis="x", labelrotation=30)
            ax.set_xlabel(
                "Logical participants (fixed physical hosts)"
                if placement_axis
                else (
                    "Synthetic users"
                    if family == "users"
                    else "Actual logical input triples"
                )
            )
            ax.set_ylabel(title)
            ax.grid(alpha=0.25)
        axes[0].legend(fontsize=7)
        family_label = family
        if placement_axis and len({r["node_count"] for r in selected}) == 1:
            family_label = f"{family}: single placement, no scaling estimate"
        fig.suptitle(
            f"{family_label}: medians of completed preparations\nConsult status figures for censoring",
            fontsize=10,
        )
        name = f"{family}-scaling.png"
        fig.savefig(figures / name, dpi=300, bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)
        manifest.append(name)
    return manifest
