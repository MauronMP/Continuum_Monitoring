"""Per-host resource sensitivity and observed infrastructure health, without interpolation."""
from collections import defaultdict
import json
import math
import statistics

from .runner import read_rows


METRICS = (
    ('process_cpu_ms', 1000, 'Participant CPU time (s)', 'cpu'),
    ('current_rss_kib', 1024, 'Participant process RSS (MiB)', 'memory'),
    ('reasoning_ms', 1000, 'Host reasoning critical path (s)', 'reasoning'),
    ('input_triples', 1000, 'Input copies (thousand triples)', 'knowledge'),
)


def aggregate_nodes(rows, metric, divisor):
    """Sum additive participant resources per host/run; take max for wall time."""
    grouped = defaultdict(list)
    for row in rows:
        if row.get('status') != 'completed' or row.get(metric) in ('', None):
            continue
        value = float(row[metric]) / divisor
        if math.isfinite(value):
            key = (row['node_id'].rsplit('-c', 1)[0], row['layout'], row['reasoner'], row['run_id'])
            grouped[key].append(value)
    return {key: max(values) if metric == 'reasoning_ms' else sum(values)
            for key, values in grouped.items()}


def resource_figures(directory, figures):
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from .synthesis import COLORS, write_table

    campaign_path = directory / 'campaign.json'
    if not campaign_path.exists():
        return []
    campaign = json.loads(campaign_path.read_text())
    config = json.loads((directory / 'configuration.json').read_text())
    scenarios = {s['name']: s for s in config['scenarios']}
    manifest, exported, health_rows = [], [], []
    for count in sorted({s['containers_per_host'] for s in campaign['steps']}):
        placement = directory / f'placement-{count}'
        steps = [s for s in campaign['steps'] if s['containers_per_host'] == count]
        names = [s['scenario'] for s in steps]
        topology_path = placement / 'placement.json'
        if not topology_path.exists():
            continue
        topology = json.loads(topology_path.read_text())
        hosts = [node['id'] for node in topology['physical_hosts']]
        users = sorted([n for n in names if scenarios[n]['family'] == 'users'],
                       key=lambda n: scenarios[n]['users'])
        source = {n: read_rows(placement / n / 'measured/distributed-reasoning-scalability/node-runs.csv') for n in users}
        for reasoner in config['experiment']['reasoners']:
            for metric, divisor, label, suffix in METRICS:
                if not users:
                    continue
                aggregates = {n: aggregate_nodes(source[n], metric, divisor) for n in users}
                upper = max(
                    (value for data in aggregates.values() for key, value in data.items()
                     if key[2] == reasoner), default=1,
                )
                fig, axes = plt.subplots(math.ceil(len(hosts)/3), 3, figsize=(12, 7),
                                         layout='constrained', squeeze=False, sharey=True)
                levels = [scenarios[n]['users'] for n in users]
                for ax, host in zip(axes.flat, hosts):
                    for layout, color in COLORS.items():
                        medians = []
                        for name, level in zip(users, levels):
                            data = [v for (h, l, r, _), v in aggregates[name].items()
                                    if (h, l, r) == (host, layout, reasoner)]
                            medians.append(statistics.median(data) if data else float('nan'))
                            exported.append(dict(placement=placement.name, scenario=name,
                                host=host, layout=layout, reasoner=reasoner, metric=metric,
                                samples=len(data), median=statistics.median(data) if data else '',
                                minimum=min(data) if data else '', maximum=max(data) if data else '',
                                display_unit=label))
                            if data:
                                ax.vlines(level, min(data), max(data), color=color)
                                ax.scatter([level]*len(data), data, s=12, color=color, alpha=.45)
                        ax.plot(levels, medians, 'o-', color=color, label=layout)
                    for name, level in zip(users, levels):
                        if not any(key[0] == host and key[2] == reasoner for key in aggregates[name]):
                            ax.text(level, .03, 'NA', transform=ax.get_xaxis_transform(), ha='center', fontsize=7)
                    if min(levels) > 0:
                        ax.set_xscale('log')
                        ax.set_xlim(min(levels)/1.5, max(levels)*1.5)
                    ax.set_xticks(levels, [str(v) for v in levels], rotation=35)
                    ax.set_xlabel('Synthetic users'); ax.set_ylabel(label)
                    ax.set_title(host); ax.set_ylim(0, max(upper * 1.12, .01)); ax.grid(alpha=.2)
                for ax in list(axes.flat)[len(hosts):]:
                    ax.set_visible(False)
                axes.flat[0].legend()
                fig.suptitle(f'{placement.name} / {reasoner}: {label} by physical host\nShared vertical scale; medians and observed ranges. NA = no completed measurement.', fontsize=11)
                filename = f'global-{placement.name}-{reasoner}-nodes-{suffix}.png'
                fig.savefig(figures/filename, dpi=300, bbox_inches='tight'); plt.close(fig)
                manifest.append(filename)

        # Recorded end-of-scenario snapshots, not a fabricated continuous trace.
        matrix = np.full((len(hosts), len(names)), np.nan)
        for j, name in enumerate(names):
            path = placement/name/'after.json'
            snapshots = json.loads(path.read_text()) if path.exists() else []
            for i, host in enumerate(hosts):
                record = next((r for r in snapshots if r['physical_host'] == host), {})
                containers = record.get('containers', [])
                states = [c.get('State', {}) for c in containers]
                health = [s.get('Health', {}).get('Status', 'unknown') for s in states]
                value = 2 if any(not s.get('Running') for s in states) else (
                    1 if 'unhealthy' in health else 0 if states and all(h == 'healthy' for h in health) else np.nan)
                matrix[i,j] = value
                health_rows.append(dict(placement=placement.name, scenario=name, host=host,
                    snapshot_status={0:'healthy',1:'unhealthy',2:'stopped'}.get(value,'unavailable'),
                    oom_killed=sum(bool(s.get('OOMKilled')) for s in states),
                    restarts=sum(c.get('RestartCount',0) for c in containers),
                    probe_failures_in_retained_window=sum(x.get('ExitCode',0)!=0 for s in states for x in s.get('Health',{}).get('Log',[]))))
        cmap = ListedColormap(['#009E73','#E69F00','#D55E00']).with_extremes(bad='#dddddd')
        fig, ax = plt.subplots(figsize=(10,4.7), layout='constrained')
        ax.imshow(matrix, cmap=cmap, norm=BoundaryNorm([-.5,.5,1.5,2.5],3), aspect='auto')
        for i in range(len(hosts)):
            for j in range(len(names)):
                label = {0:'Healthy',1:'Unhealthy',2:'Stopped'}.get(matrix[i,j], 'Unknown')
                ax.text(j,i,label,ha='center',va='center',fontsize=8)
        ax.set_xticks(range(len(names)), names, rotation=30, ha='right'); ax.set_yticks(range(len(hosts)), hosts)
        ax.set_title(f'{placement.name}: infrastructure health after each scenario\nDocker snapshots: unresponsive health probe does not prove OOM or node failure.')
        filename=f'global-{placement.name}-infrastructure-health.png'
        fig.savefig(figures/filename,dpi=300,bbox_inches='tight');plt.close(fig);manifest.append(filename)
    analysis=directory/'analysis';analysis.mkdir(exist_ok=True)
    write_table(analysis/'node-resources.csv', exported)
    write_table(analysis/'infrastructure-health.csv', health_rows)
    return manifest
