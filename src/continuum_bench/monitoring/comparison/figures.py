"""Journal-sized PNG figures, point-level provenance and explicit missing data."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ...csv_utils import write_dict_rows
from ..figure_style import save_png
from .statistics import estimate

COLORS = {"static": "#666666", "procedural": "#D55E00", "semantic": "#0072B2"}
LABELS = {"static": "Static", "procedural": "Procedural", "semantic": "Semantic (RDFS)"}
MARKERS = {"static": "s", "procedural": "^", "semantic": "o"}
CONTEXTS = ("normal", "overload", "failure", "recovery")
TITLES = {"effectiveness": "Monitoring-plan quality", "adaptation": "Response to supplied contexts",
          "scalability": "Logical workload scalability", "cumulative": "Accumulated decision work"}
CAPTIONS = {
    "effectiveness": "Coverage and excess are computed on resource–metric pairs. Exact-plan agreement additionally requires the configured actions and sampling interval. Contexts are supplied labels and the oracle is configured, not clinical ground truth. Latency is the decision call only.",
    "adaptation": "Contexts follow normal → overload → failure → recovery in replay. Each plotted observation first aggregates repeated events within one process repetition. Activated-policy counts describe the mechanisms selected; static has no adaptive policies and is not penalized for that metadata. Sampling intervals are returned plans, not applied sampling changes. No physical detection or recovery delay is measured.",
    "scalability": "Resources and policy copies increase jointly; the horizontal axis is logical workload size, not the physical node count. Preparation includes materialization and query preparation for the semantic strategy. Loop throughput excludes setup, warm-up and oracle scoring. RSS is the maximum sampled across setup and decision phases, not an exact allocation peak.",
    "cumulative": "Each size is an independent run with one prepared model and sequential context events. Accumulated time sums decision calls. Amortized throughput includes adapter preparation and the timed decision loop. CPU per event divides measured decision-phase process CPU time by event count. The ontology does not grow between events.",
}


def _metrics(experiment):
    if experiment == "effectiveness":
        return [("coverage", "Coverage (%) ↑"), ("over_monitoring", "Excess monitoring (%) ↓"),
                ("plan_correct", "Exact-plan agreement (%) ↑"), ("decision_ms", "Mean decision latency (ms) ↓")]
    if experiment == "adaptation":
        return [("decision_ms", "Mean decision latency (ms) ↓"), ("active_policy_count", "Activated policies (count)"),
                ("plan_correct", "Exact-plan agreement (%) ↑"), ("interval", "Planned sampling interval (s)")]
    if experiment == "scalability":
        return [("decision_mean_ms", "Mean decision latency (ms) ↓"), ("setup_ms", "Preparation time (ms) ↓"),
                ("throughput_decisions_per_second", "Decision-loop throughput (s⁻¹) ↑"),
                ("peak_sampled_rss_mib", "Peak sampled process RSS (MiB) ↓")]
    return [("cumulative_decision_ms", "Accumulated decision time (ms) ↓"),
            ("setup_amortized_throughput", "Throughput incl. preparation (s⁻¹) ↑"),
            ("cpu_per_event_ms", "Process CPU per event (ms) ↓"),
            ("plan_correct", "Exact-plan agreement (%) ↑")]


def _event_value(record, context, metric):
    events = [e for e in record["events"] if e["context"] == context]
    if not events:
        return None
    if metric == "interval":
        return float(np.mean([e["actual"]["sampling_interval_seconds"] for e in events]))
    factor = 100 if metric in ("coverage", "over_monitoring", "plan_correct") else 1
    return factor * float(np.mean([e[metric] for e in events]))


def point_table(records, rows):
    """Every point contains per-repetition values, denominators and CI provenance."""
    by_id = {r["job_id"]: r for r in records}
    output = []
    for experiment, node in sorted({(r["experiment"], r["node"]) for r in rows}):
        subset = [r for r in rows if (r["experiment"], r["node"]) == (experiment, node)]
        context_plot = experiment in ("effectiveness", "adaptation")
        xs = list(CONTEXTS) if context_plot else sorted({r["size"] for r in subset})
        for metric, label in _metrics(experiment):
            for strategy in COLORS:
                for x in xs:
                    candidates = [r for r in subset if r["strategy"] == strategy and (context_plot or r["size"] == x)]
                    values, ids = [], []
                    for row in candidates:
                        if row["status"] != "completed":
                            continue
                        if context_plot:
                            value = _event_value(by_id[row["job_id"]], x, metric)
                        elif metric == "cpu_per_event_ms":
                            value = row["cpu_time_ms"] / row["event_count"]
                        else:
                            value = row[metric] * (100 if metric == "plan_correct" else 1)
                        if value is not None:
                            values.append(value)
                            ids.append(row["job_id"])
                    key = (experiment, node, metric, strategy, x)
                    point = estimate(values, key)
                    reference = candidates[0] if candidates else next((r for r in subset if not context_plot and r["size"] == x), None)
                    output.append({"experiment": experiment, "node": node, "metric": metric,
                                   "strategy": strategy, "x": x, **point,
                                   "recorded_jobs": len(candidates), "unsuccessful_jobs": sum(r["status"] != "completed" for r in candidates),
                                   "resource_count": reference["resource_count"] if reference else None,
                                   "policy_count": reference["policy_count"] if reference else None,
                                   "event_count": reference["event_count"] if reference else None,
                                   "values": json.dumps(values), "job_ids": json.dumps(ids)})
    return output


def _draw(axis, points, metric, xs, context_plot):
    """NaNs break curves at failed/missing sizes instead of connecting survivors."""
    all_values = [p["mean"] for p in points if p["mean"] is not None]
    if not all_values:
        axis.text(.5, .5, "No completed measurements", transform=axis.transAxes, ha="center")
        axis.set_xticks([])
        axis.set_yticks([])
        return
    xmetric = "resource_count" if points[0]["experiment"] == "scalability" else "event_count"
    positions = np.arange(len(xs), dtype=float) if context_plot else np.array([next(p[xmetric] for p in points if p["x"] == x and p[xmetric] is not None) for x in xs], dtype=float)
    for index, strategy in enumerate(COLORS):
        ordered = [next(p for p in points if p["strategy"] == strategy and p["x"] == x) for x in xs]
        yy = np.array([p["mean"] if p["mean"] is not None else np.nan for p in ordered])
        xx = positions + ((index-1)*.16 if context_plot else 0)
        # Point offsets distinguish identical strategies without changing values.
        axis.plot(xx, yy, color=COLORS[strategy], marker=MARKERS[strategy],
                  markersize=6.5 if strategy == "semantic" else 4.5, linewidth=1, linestyle="none" if context_plot else ("--" if strategy == "semantic" else "-"),
                  markerfacecolor="white" if strategy == "semantic" else COLORS[strategy], label=LABELS[strategy])
        for position, point in zip(xx, ordered):
            if point["low"] is not None:
                center = point["mean"]
                axis.errorbar(position, center, yerr=[[max(0,center-point["low"])], [max(0,point["high"]-center)]],
                              fmt="none", color=COLORS[strategy], capsize=2, linewidth=.8)
    axis.set_xticks(positions)
    if context_plot:
        axis.set_xlim(-.5, len(xs)-.5)
    else:
        if max(positions) / min(positions) >= 4:
            axis.set_xscale("log", base=2)
        axis.set_xlim(min(positions)*.8, max(positions)*1.2)
    axis.grid(axis="y", color="#d8d8d8", linewidth=.5)
    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)
    if metric in ("coverage", "over_monitoring", "plan_correct"):
        axis.set_ylim(-5, 105)
        axis.set_yticks([0, 25, 50, 75, 100])
    elif metric == "active_policy_count":
        from matplotlib.ticker import MaxNLocator
        axis.set_ylim(-.1, max(all_values)*1.1 + .1)
        axis.yaxis.set_major_locator(MaxNLocator(integer=True))
    elif metric in ("peak_sampled_rss_mib", "interval"):
        upper = max(p["high"] if p["high"] is not None else p["mean"] for p in points if p["mean"] is not None)
        axis.set_ylim(0, upper*1.12 if upper > 0 else 1)
    elif min(all_values) > 0 and max(all_values)/min(all_values) >= 20:
        axis.set_yscale("log")
        axis.set_ylabel("log scale", fontsize=7, color="#555555")
    else:
        axis.set_ylim(bottom=0)
        axis.ticklabel_format(axis="y", style="plain", useOffset=False)


def figures(directory: Path, records, rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    points = point_table(records, rows)
    write_dict_rows(directory / "figure-data.csv", points, empty_message="No figure data")
    paths, captions = [], ["# Figure captions and interpretation", "",
                           "Figures use separate physical hosts; no host is treated as an independent repetition of another.", ""]
    style = {"font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
             "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 8}
    with plt.rc_context(style):
        for experiment, node in sorted({(r["experiment"], r["node"]) for r in rows}):
            subset = [p for p in points if (p["experiment"], p["node"]) == (experiment, node)]
            data = [r for r in rows if (r["experiment"], r["node"]) == (experiment, node)]
            metrics = _metrics(experiment)
            context_plot = experiment in ("effectiveness", "adaptation")
            xs = list(CONTEXTS) if context_plot else sorted({r["size"] for r in data})
            fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.4))
            for i, (axis, (metric, ylabel)) in enumerate(zip(axes.flat, metrics)):
                panel = [p for p in subset if p["metric"] == metric]
                _draw(axis, panel, metric, xs, context_plot)
                axis.set_title(f"({chr(97+i)}) {ylabel}", loc="left", pad=8)
                if metric == "interval":
                    done_records = [r for r in records if r["experiment"] == experiment and r["node"] == node and r["status"] == "completed"]
                    expected = [next((e["expected"]["sampling_interval_seconds"] for r in done_records for e in r["events"] if e["context"] == context), np.nan) for context in CONTEXTS]
                    expected_line, = axis.plot(range(len(xs)), expected, color="black", linestyle=":", linewidth=.8, label="Expected interval")
                    if any(np.isfinite(expected)):
                        axis.legend(handles=[expected_line], loc="best", fontsize=6, frameon=False)
                if context_plot:
                    axis.set_xticks(range(len(xs)), [x.title() for x in xs])
                    axis.set_xlabel("Supplied context")
                else:
                    labels = []
                    for x in xs:
                        row = next(r for r in data if r["size"] == x)
                        labels.append(f"{row['resource_count']} / {row['policy_count']}" if experiment == "scalability" else str(row["event_count"]))
                    position_key = "resource_count" if experiment == "scalability" else "event_count"
                    positions = [next(r[position_key] for r in data if r["size"] == x) for x in xs]
                    axis.set_xticks(positions, labels)
                    axis.minorticks_off()
                    axis.set_xlabel(("Logical resources / policy copies" if experiment == "scalability" else "Replayed events") + (" (log)" if axis.get_xscale() == "log" else ""))
            ns = [p["n"] for p in subset if p["recorded_jobs"]]
            nlabel = str(min(ns)) if min(ns) == max(ns) else f"{min(ns)}–{max(ns)}"
            warning = "Exploratory: fewer than 5 repetitions at some points; no CI there." if min(ns) < 5 else "Whiskers: 95% bootstrap CI across process repetitions."
            failed = sum(r["status"] != "completed" for r in data)
            fig.suptitle(f"{TITLES[experiment]} | {node}", fontsize=10, y=.99)
            handles = [Line2D([], [], color=COLORS[s], marker=MARKERS[s], linestyle="none", label=LABELS[s],
                              markerfacecolor="white" if s == "semantic" else COLORS[s]) for s in COLORS if any(r["strategy"]==s for r in data)]
            fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.5,.955), ncol=3, frameon=False)
            fig.text(.5, .04, f"Mean across process repetitions; n per point = {nlabel}. Unsuccessful jobs: {failed}/{len(data)}.", ha="center", fontsize=7)
            fig.text(.5, .016, warning, ha="center", fontsize=7)
            fig.tight_layout(rect=(0,.075,1,.89), h_pad=1.5, w_pad=2)
            path = save_png(fig, directory / experiment / "figures" / node)[0]
            paths.append(path)
            captions += [f"## {path.relative_to(directory)}", "", CAPTIONS[experiment], "",
                         f"Means aggregate process repetitions (n={nlabel} per point). {warning} "
                         "Missing points are not imputed, and curves do not bridge them. Sample sizes and contributing job IDs are in figure-data.csv. "
                         "Workload axes preserve numeric spacing and use a logarithmic x scale when the range spans a factor of four or more. Context markers are horizontally offset for visibility. Lines show measured points only; they are not fitted complexity models.", ""]
        # Outcome coverage remains visible even when every performance job fails.
        labels = sorted({(r["experiment"], r["node"]) for r in rows})
        fig, axis = plt.subplots(figsize=(7.2, max(3, .2*len(labels)+1.3)))
        statuses = ("completed", "timeout", "failed", "unavailable", "invalid")
        bottom = np.zeros(len(labels))
        palette = ("#009E73", "#E69F00", "#D55E00", "#999999", "#CC79A7")
        for status, color in zip(statuses, palette):
            values = [sum((r["experiment"],r["node"])==key and r["status"]==status for r in rows) for key in labels]
            if any(values):
                axis.barh(range(len(labels)), values, left=bottom, color=color, label=status.title())
            bottom += values
        axis.set_yticks(range(len(labels)), [f"{e} / {n}" for e,n in labels])
        axis.set_xlabel("Recorded jobs (all strategies and sizes)")
        axis.set_title("Execution outcome coverage")
        axis.legend(loc="upper center", bbox_to_anchor=(.5,1.13), ncol=5, frameon=False)
        axis.spines[["top","right"]].set_visible(False)
        fig.tight_layout()
        paths += save_png(fig, directory / "figures" / "outcomes")
    captions += ["## figures/outcomes.png", "", "Recorded jobs by execution status. Jobs not yet attempted in an interrupted campaign are not included; consult report.json for planned and missing jobs. Completed execution does not imply agreement with the oracle.", ""]
    (directory / "figure-captions.md").write_text("\n".join(captions))
    return paths


def paired_cost_figure(directory, paired):
    """Show semantic overhead against equivalent procedural policies by host."""
    import matplotlib.pyplot as plt
    available = [r for r in paired if r["experiment"] == "scalability" and r["baseline"] == "procedural"]
    if not available:
        (directory / "figures/paired-cost.png").unlink(missing_ok=True)
        return []
    # Use the same workload size across hosts; never mix each host's largest survivor.
    size = max(r["size"] for r in available)
    selected = [r for r in available if r["size"] == size]
    nodes = sorted({r["node"] for r in selected})
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.3))
    for axis, metric, title in zip(axes, ("decision_mean_ms", "peak_sampled_rss_mib"),
                                   ("(a) Additional decision time (ms)", "(b) Additional peak sampled RSS (MiB)")):
        for i, node in enumerate(nodes):
            row = next(r for r in selected if r["node"] == node and r["metric"] == metric)
            value = row["semantic_minus_baseline"]
            axis.plot(value, i, "o", color=COLORS["semantic"], markerfacecolor="white", markersize=5)
            if row["bootstrap_low_95"] is not None:
                axis.errorbar(value, i, xerr=[[max(0,value-row["bootstrap_low_95"])], [max(0,row["bootstrap_high_95"]-value)]],
                              fmt="none", capsize=3, color=COLORS["semantic"])
        axis.axvline(0, color="#777777", linewidth=.7, linestyle="--")
        axis.set_yticks(range(len(nodes)), [f"{node} (n={next(r['paired_repetitions'] for r in selected if r['node']==node)})" for node in nodes], fontsize=8)
        axis.set_ylim(-.5, len(nodes)-.5)
        axis.set_xlabel("Semantic minus procedural", fontsize=8)
        axis.set_title(title, fontsize=9, loc="left")
        axis.tick_params(labelsize=8)
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="x", alpha=.2)
    fig.suptitle(f"Paired mechanism overhead | workload multiplier {size}", fontsize=10)
    label = "95% bootstrap CI only for n ≥ 5; smaller samples are exploratory."
    fig.text(.5, .02, label, ha="center", fontsize=7)
    fig.tight_layout(rect=(0,.07,1,.94))
    paths = save_png(fig, directory / "figures/paired-cost")
    with (directory / "figure-captions.md").open("a") as handle:
        handle.write("\n## figures/paired-cost.png\n\nPaired semantic-minus-procedural cost differences at the largest workload multiplier with matched observations. The multiplier is identical across included hosts. Hosts without matched completed runs at that size are absent; consult outcomes.csv. Positive values denote additional cost, not improved performance. Trace and workload hashes must match within each pair. The sample size is paired process repetitions, not events. " + label + "\n")
    return paths


def infrastructure_figures(directory, records, rows):
    """Compare all recorded hosts without pooling hosts or inventing fleet totals."""
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    points = point_table(records, rows)
    order = {name: i for i, name in enumerate(('cloud', 'fog', 'mist', 'edge1', 'edge2', 'edge3'))}
    nodes = sorted({r['node'] for r in rows}, key=lambda n: (order.get(n, 99), n))
    paths = []
    for experiment in sorted({r['experiment'] for r in rows}):
        metrics = _metrics(experiment)
        context = experiment in ('effectiveness', 'adaptation')
        subset = [p for p in points if p['experiment'] == experiment]
        xs = list(CONTEXTS) if context else sorted({p['x'] for p in subset})
        fig, axes = plt.subplots(len(metrics), len(nodes), squeeze=False,
                                 figsize=(max(7.2, 2.65 * len(nodes)), 9.6))
        for i, (metric, label) in enumerate(metrics):
            metric_points = [p for p in subset if p['metric'] == metric]
            means = [p['mean'] for p in metric_points if p['mean'] is not None]
            log = bool(means) and min(means) > 0 and max(means) / min(means) >= 20 and metric not in ('coverage', 'over_monitoring', 'plan_correct', 'interval', 'peak_sampled_rss_mib', 'active_policy_count')
            for j, node in enumerate(nodes):
                axis = axes[i, j]
                panel = [p for p in metric_points if p['node'] == node]
                if panel:
                    node_xs = list(CONTEXTS) if context else sorted({p['x'] for p in panel})
                    _draw(axis, panel, metric, node_xs, context)
                    ns = [p['n'] for p in panel if p['recorded_jobs']]
                    n_label = str(min(ns)) if min(ns) == max(ns) else f'{min(ns)}–{max(ns)}'
                    axis.set_title(f'{node} | n={n_label}', fontsize=9)
                    axis.set_yscale('log' if log else 'linear')
                    if context:
                        axis.set_xticks(range(len(xs)), ['Normal', 'Overload', 'Failure', 'Recovery'], rotation=30)
                    else:
                        key = 'resource_count' if experiment == 'scalability' else 'event_count'
                        ticks = [next(p[key] for p in panel if p['x'] == x) for x in node_xs]
                        axis.set_xticks(ticks, [str(t) for t in ticks])
                        axis.minorticks_off()
                    axis.set_xlabel('Supplied context' if context else ('Logical resources' if experiment == 'scalability' else 'Replayed events'), fontsize=8)
                else:
                    axis.text(.5, .5, 'No recorded jobs', ha='center', transform=axis.transAxes)
                from textwrap import fill
                axis.set_ylabel(fill(label + (' [log]' if log else ''), 32) if j == 0 else '', fontsize=8)
                axis.tick_params(labelsize=7)
            # Identical vertical scales across hosts within each metric row.
            if means:
                lows = [p['low'] if p['low'] is not None else p['mean'] for p in metric_points if p['mean'] is not None]
                highs = [p['high'] if p['high'] is not None else p['mean'] for p in metric_points if p['mean'] is not None]
                limits = (-5, 105) if metric in ('coverage', 'over_monitoring', 'plan_correct') else ((max(min(lows)*.75, min(means)*.1), max(highs)*1.3) if log else (0, max(max(highs)*1.15, .1)))
                for axis in axes[i]:
                    axis.set_ylim(*limits)
        handles = [Line2D([], [], color=COLORS[s], marker=MARKERS[s], label=LABELS[s],
                          markerfacecolor='white' if s == 'semantic' else COLORS[s]) for s in COLORS]
        fig.suptitle(f'{TITLES[experiment]} | all participating physical nodes', fontsize=13, y=.995)
        fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5, .97), ncol=3, frameon=False)
        fig.text(.5, .027, 'Same y scale within each row. Means and 95% bootstrap CI across process repetitions (CI only when n ≥ 5).', ha='center', fontsize=8)
        fig.text(.5, .010, 'Independent host replays; not simultaneous infrastructure totals. Missing measurements are not zero. Only recorded nodes are shown.', ha='center', fontsize=8)
        fig.tight_layout(rect=(0, .055, 1, .94), h_pad=2, w_pad=1.3)
        path = save_png(fig, directory / experiment / 'figures' / 'all-nodes')[0]
        paths.append(path)
        with (directory / 'figure-captions.md').open('a') as handle:
            handle.write(f'\n## {path.relative_to(directory)}\n\n{CAPTIONS[experiment]} All recorded hosts are compared using common metric scales. Hosts are not pooled as repetitions and their RSS, throughput and latencies are not summed into a simultaneous infrastructure measurement. Point values, confidence intervals and job provenance are in figure-data.csv. Nodes excluded from acquisition cannot be reconstructed by reporting.\n')
    return paths


def cross_node_summary(directory, rows):
    """Compact four-test comparison at a common recorded size across hosts."""
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    order = {n: i for i, n in enumerate(('cloud', 'fog', 'mist', 'edge1', 'edge2', 'edge3'))}
    nodes = sorted({r['node'] for r in rows}, key=lambda n: (order.get(n, 99), n))
    panels = [('effectiveness', 'plan_correct', 'Exact-plan agreement (%)', 100),
              ('adaptation', 'decision_mean_ms', 'Context-response decision latency (ms)', 1),
              ('scalability', 'decision_mean_ms', 'Decision latency at largest workload (ms)', 1),
              ('cumulative', 'cumulative_decision_ms', 'Accumulated decision time at longest trace (ms)', 1)]
    fig, axes = plt.subplots(2, 2, figsize=(9, 6.6))
    export = []
    for axis, (experiment, metric, title, factor) in zip(axes.flat, panels):
        candidates = [r for r in rows if r['experiment'] == experiment]
        if not candidates:
            axis.set_title(title)
            continue
        size = max(r['size'] for r in candidates)
        values_on_axis = []
        for j, strategy in enumerate(COLORS):
            for i, node in enumerate(nodes):
                matched = [r for r in candidates if r['size'] == size and r['node'] == node and r['strategy'] == strategy]
                completed = [r for r in matched if r['status'] == 'completed']
                values = [r[metric] * factor for r in completed]
                stat = estimate(values, ('overview', experiment, node, strategy, size))
                export.append(dict(experiment=experiment, metric=metric, node=node, strategy=strategy,
                                   size=size, **stat, recorded_jobs=len(matched),
                                   values=json.dumps(values), job_ids=json.dumps([r['job_id'] for r in completed])))
                if stat['mean'] is None:
                    continue
                values_on_axis.append(stat['mean'])
                x = i + (j - 1) * .18
                axis.plot(x, stat['mean'], marker=MARKERS[strategy], color=COLORS[strategy],
                          markerfacecolor='white' if strategy == 'semantic' else COLORS[strategy], markersize=5)
                if stat['low'] is not None:
                    axis.errorbar(x, stat['mean'], yerr=[[max(0, stat['mean']-stat['low'])], [max(0, stat['high']-stat['mean'])]],
                                  fmt='none', color=COLORS[strategy], capsize=2)
        if metric == 'plan_correct':
            axis.set_ylim(-5, 105)
        elif values_on_axis and min(values_on_axis) > 0 and max(values_on_axis)/min(values_on_axis) >= 20:
            axis.set_yscale('log')
        else:
            axis.set_ylim(bottom=0)
        axis.set_title(title, fontsize=9)
        resource = next((r for r in candidates if r['size'] == size), None)
        detail = f"{resource['resource_count']} logical resources; {resource['policy_count']} policy copies; {resource['event_count']} events/job"
        axis.set_xlabel(detail, fontsize=7)
        axis.set_xticks(range(len(nodes)), nodes)
        axis.tick_params(labelsize=8)
        axis.grid(axis='y', alpha=.25)
        axis.spines[['top', 'right']].set_visible(False)
    fig.suptitle('Policy evaluation across all participating hosts', fontsize=12)
    handles = [Line2D([], [], color=COLORS[s], marker=MARKERS[s], linestyle='none', label=LABELS[s]) for s in COLORS]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5, .95), ncol=3, frameon=False)
    fig.text(.5, .02, 'Independent host replays; mean and 95% bootstrap CI (n ≥ 5). Missing results are not zero.', ha='center', fontsize=8)
    fig.tight_layout(rect=(0, .05, 1, .89), h_pad=2)
    write_dict_rows(directory / 'cross-node-summary-data.csv', export, empty_message='No cross-node summary data')
    paths = save_png(fig, directory / 'figures/cross-node-summary')
    with (directory / 'figure-captions.md').open('a') as f:
        f.write('\n## figures/cross-node-summary.png\n\nOne selected metric per experiment across every recorded host. Each panel uses the same largest recorded workload size for all hosts, including missing/failed observations in the selection; it does not choose a different successful size per host. Context-response latency is the mean decision call across the replay, not failure detection or service recovery. Detailed metric-by-host panels remain in each experiment’s figures/all-nodes.png. Source repetitions and job IDs are recorded in cross-node-summary-data.csv.\n')
    return paths
