"""Matched physical comparisons; no inferred node timing or causal policy claims."""
from collections import defaultdict
import statistics

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import LogLocator, NullFormatter, ScalarFormatter
import numpy as np

from .publication import COLORS, LABELS, number, outcome, write_csv

LAYOUTS = {'sharded': 'Shared / authority-partitioned', 'replicated': 'Replicated'}


def summarize(rows, keys, metric):
    groups = defaultdict(list)
    for row in rows:
        value = number(row, metric)
        if value is not None and value >= 0:
            groups[tuple(row.get(k, 'unknown') for k in keys)].append(value)
    return [{**dict(zip(keys, key)), 'n': len(values), 'median': statistics.median(values),
             'p95': float(np.percentile(values, 95)), 'total': sum(values)}
            for key, values in sorted(groups.items())]


def matched_users(datasets):
    sets = [{number(r, 'synthetic_users') for r in rows if outcome(r) == 'completed'}
            for rows in datasets]
    common = set.intersection(*sets) if sets else set()
    return min(common - {None}) if common - {None} else None


def generate_comparisons(report):
    summaries = {}
    for suite in ('scalability', 'cumulative'):
        for layout in LAYOUTS:
            summaries[layout, suite] = report.read(report.inputs / f'physical/{layout}/{suite}/summary.csv')
    # Match the population across both methods and all three observed reasoners.
    population = matched_users([[r for r in summaries[layout, 'scalability'] if r.get('reasoner') == reasoner]
                                for layout in LAYOUTS for reasoner in COLORS])
    if population is None:
        report.findings.append('Comparative node/query panels: no population completed across both layouts and all three reasoners.')
    else:
        report.findings.append(f"Matched node/category/query comparisons use synthetic_users={population:g}, completed parent runs in both layouts and all three reasoners; worker timings include routing and fan-out.")
        node_rows = []
        for layout in LAYOUTS:
            filename = 'node-query-runs.csv' if layout == 'sharded' else 'query-runs.csv'
            raw = report.read(report.inputs / f'physical/{layout}/scalability/{filename}')
            valid = {(r['reasoner'], r['repetition']) for r in summaries[layout, 'scalability']
                     if outcome(r) == 'completed' and number(r, 'synthetic_users') == population}
            for row in raw:
                if (outcome(row) == 'completed' and number(row, 'synthetic_users') == population
                        and (row.get('reasoner'), row.get('repetition')) in valid):
                    role = row.get('role', 'unknown')
                    node_rows.append({**row, 'layout': layout, 'layer': 'Edge' if role.startswith('edge') else role.title()})
        category_colors = {cat: plt.get_cmap('tab20')(i) for i, cat in enumerate(sorted({r['category'] for r in node_rows}))}
        tables = summarize(node_rows, ['layout', 'reasoner', 'role', 'layer', 'category'], 'duration_ms')
        write_csv(report.output / 'node-category-observations.csv', tables)
        write_csv(report.output / 'node-query-observations.csv', summarize(node_rows, ['layout', 'reasoner', 'role', 'query_id', 'category'], 'duration_ms'))
        for layout in LAYOUTS:
            for reasoner in COLORS:
                selected = [r for r in tables if r['layout'] == layout and r['reasoner'] == reasoner]
                if not selected:
                    continue
                categories = sorted({r['category'] for r in selected})
                roles = sorted({r['role'] for r in selected})
                matrix = np.full((len(categories), len(roles)), np.nan)
                for row in selected:
                    matrix[categories.index(row['category']), roles.index(row['role'])] = row['median']
                fig, ax = plt.subplots(figsize=(10, 8))
                positive = matrix[np.isfinite(matrix) & (matrix > 0)]
                if not len(positive):
                    plt.close(fig)
                    continue
                mesh = ax.imshow(np.ma.masked_invalid(matrix), aspect='auto', cmap='YlOrRd',
                                 norm=LogNorm(vmin=max(positive.min(), .001), vmax=max(positive.max(), positive.min()*1.01)))
                ax.set_xticks(range(len(roles)), roles)
                ax.set_yticks(range(len(categories)), categories)
                for y in range(len(categories)):
                    for x in range(len(roles)):
                        value = matrix[y, x]
                        ax.text(x, y, f'{value:.1f}' if np.isfinite(value) else 'N/A', ha='center', va='center', fontsize=8,
                                color='white' if np.isfinite(value) and value > np.sqrt(positive.min()*positive.max()) else 'black')
                fig.colorbar(mesh, ax=ax, label='Median worker query execution (ms; log colour scale)')
                report.save(fig, f'node-category-{layout}-{reasoner}', f'{LAYOUTS[layout]}; users={population:g}. N/A means no assigned observation. Category query mixes differ by node; not hardware speedup.')
        category_work = defaultdict(float)
        for row in node_rows:
            value = number(row, 'duration_ms')
            if value is not None:
                category_work[row['layout'], row['reasoner'], row['category'], row['repetition']] += value
        work_rows = [{'layout': a, 'reasoner': b, 'category': c, 'repetition': d, 'query_ms': v}
                     for (a,b,c,d),v in category_work.items()]
        write_csv(report.output / 'category-method-work.csv', work_rows)
        categories = sorted({r['category'] for r in work_rows})
        if categories:
            fig, axes = plt.subplots(1, 3, figsize=(18, 8), sharey=True)
            for ax, reasoner in zip(axes, COLORS):
                for i, layout in enumerate(LAYOUTS):
                    vals = [[r['query_ms'] for r in work_rows if r['layout']==layout and r['reasoner']==reasoner and r['category']==cat] for cat in categories]
                    ax.barh(np.arange(len(categories))+(i-.5)*.35, [statistics.median(v) if v else np.nan for v in vals], .35, label=LAYOUTS[layout])
                ax.set_title(LABELS[reasoner]); ax.set_xscale('log'); ax.set_xlabel('Total worker query time per repetition (ms)'); ax.grid(axis='x',alpha=.2); ax.legend(fontsize=8)
            axes[0].set_yticks(range(len(categories)), categories)
            report.save(fig, 'category-evaluation-methods', f'Users={population:g}; medians over repetitions. Includes actual partition fan-out. Missing bars mean no observation, not zero cost.')
        # Comparable query IDs with node execution timing: not federated end-to-end latency.
        query_stats = summarize(node_rows, ['layout', 'reasoner', 'query_id', 'category'], 'duration_ms')
        write_csv(report.output / 'query-ranking.csv', query_stats)
        for layout in LAYOUTS:
            selected = [r for r in query_stats if r['layout'] == layout]
            ranking = sorted({r['query_id'] for r in selected}, key=lambda q: max(r['median'] for r in selected if r['query_id'] == q), reverse=True)[:20]
            if not ranking:
                continue
            fig, axes = plt.subplots(1, 3, figsize=(17, 9), sharey=True, sharex=True)
            for ax, reasoner in zip(axes, COLORS):
                for row in selected:
                    if row['reasoner'] == reasoner and row['query_id'] in ranking:
                        y = ranking.index(row['query_id'])
                        ax.plot([row['median'], row['p95']], [y, y], color=category_colors[row['category']], alpha=.5)
                        ax.scatter(row['median'], y, color=category_colors[row['category']], s=45)
                ax.set_title(LABELS[reasoner]); ax.set_xscale('log'); ax.set_xlabel('Worker query execution (ms)'); ax.grid(alpha=.2)
                ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5), numticks=10)); ax.xaxis.set_major_formatter(ScalarFormatter()); ax.xaxis.set_minor_formatter(NullFormatter())
            axes[0].set_yticks(range(len(ranking)), ranking); axes[0].invert_yaxis()
            cats = sorted({r['category'] for r in selected if r['query_id'] in ranking})
            axes[-1].legend(handles=[Line2D([], [], marker='o', linestyle='', color=category_colors[c], label=c) for c in cats], loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=8)
            report.save(fig, f'expensive-queries-{layout}', f'Users={population:g}; top 20 by maximum median across reasoners. Dot=median; line extends to p95. Node executions pooled; see CSV sample counts.')
        per_node = summarize(node_rows, ['layout','reasoner','role','query_id','category'], 'duration_ms')
        for layout in LAYOUTS:
            selected = [r for r in per_node if r['layout']==layout]
            if not selected: continue
            queries = sorted({r['query_id'] for r in selected}, key=lambda q: max(r['median'] for r in selected if r['query_id']==q), reverse=True)[:15]
            roles = sorted({r['role'] for r in selected})
            positive = [r['median'] for r in selected if r['query_id'] in queries and r['median']>0]
            if not positive: continue
            norm = LogNorm(vmin=min(positive), vmax=max(max(positive),min(positive)*1.01))
            fig, axes = plt.subplots(1, 3, figsize=(16, 8), sharey=True)
            for ax, reasoner in zip(axes, COLORS):
                matrix = np.full((len(queries),len(roles)),np.nan)
                for row in selected:
                    if row['reasoner']==reasoner and row['query_id'] in queries:
                        matrix[queries.index(row['query_id']),roles.index(row['role'])]=row['median']
                ax.imshow(np.ma.masked_invalid(matrix),aspect='auto',norm=norm,cmap='YlOrRd')
                for y in range(len(queries)):
                    for x in range(len(roles)):
                        value=matrix[y,x]
                        ax.text(x,y,f'{value:.1f}' if np.isfinite(value) else '—',ha='center',va='center',fontsize=7,
                                color='white' if np.isfinite(value) and value>np.sqrt(min(positive)*max(positive)) else 'black')
                ax.set_title(LABELS[reasoner]);ax.set_xticks(range(len(roles)),roles,rotation=45)
            axes[0].set_yticks(range(len(queries)),queries)
            fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap='YlOrRd'), ax=axes[-1], label='Median worker query execution (ms)')
            report.save(fig,f'node-expensive-queries-{layout}',f'Users={population:g}; median worker query ms printed in cells. Common logarithmic colour scale across panels; dash=no assigned observation. Top 15 by maximum median.')
        catalog = {r['id']:r for r in report.read(report.root/'queries/catalog.csv')}
        policy_work = defaultdict(float)
        for row in node_rows:
            ids = [v.strip() for v in catalog.get(row['query_id'],{}).get('policies','').split(',') if v.strip()]
            value = number(row,'duration_ms')
            if ids and value is not None:
                for policy in ids:
                    policy_work[row['layout'],row['reasoner'],row['role'],row['layer'],row['repetition'],policy] += value/len(ids)
        write_csv(report.output/'node-policy-attribution.csv',
                  [{'layout':a,'reasoner':b,'role':c,'layer':d,'repetition':e,'policy':f,'attributed_query_ms':v}
                   for (a,b,c,d,e,f),v in policy_work.items()])
        # Layer work, grouped per repetition before summarizing; no division of federated timing among nodes.
        layer_totals = defaultdict(float)
        for row in node_rows:
            value = number(row, 'duration_ms')
            if value is not None:
                layer_totals[row['layout'], row['reasoner'], row['layer'], row['repetition']] += value
        layer_rows = [{'layout': a, 'reasoner': b, 'layer': c, 'repetition': d, 'query_ms': v} for (a,b,c,d),v in layer_totals.items()]
        write_csv(report.output / 'layer-query-work.csv', layer_rows)
        fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
        for ax, layout in zip(axes, LAYOUTS):
            for i, reasoner in enumerate(COLORS):
                vals = [[r['query_ms']/1000 for r in layer_rows if r['layout']==layout and r['reasoner']==reasoner and r['layer']==layer] for layer in ('Edge','Fog','Cloud')]
                ax.bar(np.arange(3)+(i-1)*.23, [statistics.median(v) if v else np.nan for v in vals], .23, label=LABELS[reasoner], color=COLORS[reasoner])
            ax.set_xticks(range(3), ['Edge','Fog','Cloud']); ax.set_title(LAYOUTS[layout]); ax.legend(); ax.grid(axis='y', alpha=.2)
        axes[0].set_ylabel('Median total worker query time per repetition (s)')
        report.save(fig, 'continuum-layer-query-work', f'Users={population:g}. Edge sums its physical nodes. Work depends on routing, fan-out and query mix; not elapsed time or a hardware-only comparison.')
    # Equivalent logical workload curves, retaining censoring in the companion coverage report.
    curve_table = []
    for suite in ('scalability', 'cumulative'):
        xkey = 'synthetic_users' if suite == 'scalability' else 'stage'
        for reasoner in COLORS:
            fig, axes = plt.subplots(1, 3, figsize=(16, 5))
            plotted = False
            for ax, metric, label in zip(axes, ['total_wall_ms','max_node_reasoning_ms','query_wall_ms'], ['Total wall time (s)','Critical reasoning time (s)','Query wall time (s)']):
                for layout, marker in zip(LAYOUTS, ['o','s']):
                    rows = [r for r in summaries[layout,suite] if outcome(r)=='completed' and r['reasoner']==reasoner]
                    points = summarize(rows, [xkey], metric)
                    points.sort(key=lambda p: float(p[xkey]))
                    if not points: continue
                    plotted = True
                    curve_table.extend({'suite':suite,'reasoner':reasoner,'layout':layout,'metric':metric,**p} for p in points)
                    ax.errorbar([float(p[xkey]) for p in points], [p['median']/1000 for p in points],
                                yerr=[[ (p['median']-min(number(r,metric) for r in rows if r[xkey]==p[xkey] and number(r,metric) is not None))/1000 for p in points],
                                      [(max(number(r,metric) for r in rows if r[xkey]==p[xkey] and number(r,metric) is not None)-p['median'])/1000 for p in points]],
                                marker=marker, capsize=3, label=LAYOUTS[layout])
                ax.set_xlabel(xkey.replace('_',' ').title()); ax.set_ylabel(label); ax.grid(alpha=.2)
                if ax.has_data(): ax.legend(fontsize=8)
            if plotted:
                report.save(fig, f'placement-{suite}-{reasoner}', 'Same configured logical progression; completed rows only. Median and min–max; missing later points are not zero. Shared means authority-partitioned, not shared-memory.')
            else: plt.close(fig)
    write_csv(report.output / 'placement-comparison.csv', curve_table)
    report.findings.append('Policy associations and cumulative category additions are observational. No matched policies-disabled intervention exists here; category costs and cumulative changes do not establish causal policy overhead. Policy weights in cost tables are attribution fractions, not measured decision importance.')
