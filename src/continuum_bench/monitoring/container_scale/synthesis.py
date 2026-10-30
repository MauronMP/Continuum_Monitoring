"""Campaign-level comparisons with censoring and missing-reference safeguards."""
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import statistics

from .runner import read_rows

METRICS = (
    ('benchmark_end_to_end_ms', 1000, 'Preparation wall time (s)'),
    ('reasoning_ms', 1000, 'Reasoning critical path (s)'),
    ('process_cpu_ms', 1000, 'Aggregate participant CPU (s)'),
    ('current_rss_kib_sum', 1024, 'Aggregate process RSS (MiB)'),
    ('aggregate_input_triples', 1000, 'Stored input copies (thousand triples)'),
    ('network_bytes', 1048576, 'Preparation payload (MiB)'),
)
COLORS = {'distributed': '#0072B2', 'replicated': '#D55E00'}


def values(rows, metric, divisor=1):
    return [float(r[metric]) / divisor for r in rows
            if r.get('status') == 'completed' and r.get(metric) not in (None, '')
            and math.isfinite(float(r[metric]))]


def semantic_state(rows):
    """A missing reference is not a measured mismatch; support historical CSVs."""
    statuses = {r.get('status') for r in rows}
    if 'mismatch' in statuses:
        return 'mismatch'
    if 'replicated_reference_unavailable' in statuses:
        return 'reference unavailable'
    if statuses == {'equivalent'}:
        return 'equivalent'
    return 'not validated'


def write_table(path, rows):
    if rows:
        with path.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def synthesis(directory: Path, figures: Path):
    import matplotlib.pyplot as plt
    import numpy as np

    config = json.loads((directory / 'configuration.json').read_text())
    scenarios = {s['name']: s for s in config['scenarios']}
    groups = defaultdict(list)
    for path in sorted(directory.glob('placement-*/*/measured/distributed-reasoning-scalability')):
        scenario, placement = path.parents[1].name, path.parents[2].name
        validation = read_rows(path / 'semantic-validation.csv')
        for row in read_rows(path / 'distributed-reasoning-summary.csv'):
            state = semantic_state([v for v in validation if v['layout'] == row['layout']
                                    and v['reasoner'] == row['reasoner']])
            groups[(placement, row['reasoner'])].append({**row, 'scenario': scenario,
                                                       'validation_state': state})
    # Failed acquisition can leave no measurement CSV. Preserve attempted levels.
    campaign_path = directory / 'campaign.json'
    campaign = json.loads(campaign_path.read_text()) if campaign_path.exists() else {}
    missing = []
    for step in campaign.get('steps', []):
        placement = f"placement-{step['containers_per_host']}"
        for reasoner in config.get('experiment', {}).get('reasoners', []):
            if any(r['scenario'] == step['scenario'] for r in groups[(placement, reasoner)]):
                continue
            missing.append(dict(placement=placement, scenario=step['scenario'], reasoner=reasoner,
                                status=step['status'], error=step.get('error', 'No measured CSV')))
            for layout in config['experiment']['layouts']:
                groups[(placement, reasoner)].append(dict(scenario=step['scenario'], layout=layout,
                    reasoner=reasoner, status='not_recorded', validation_state='not validated',
                    missing_measurement=True))
    manifest, table, contrasts = [], [], []

    def save(fig, name):
        fig.savefig(figures / name, dpi=300, bbox_inches='tight', pad_inches=.12)
        plt.close(fig)
        manifest.append(name)

    for (placement, reasoner), rows in groups.items():
        names = [n for n in scenarios if any(r['scenario'] == n for r in rows)]
        layouts = [l for l in COLORS if any(r['layout'] == l for r in rows)]
        prefix = f'global-{placement}-{reasoner}'
        def select(name, layout):
            return [r for r in rows if r['scenario'] == name and r['layout'] == layout]
        def samples(name, layout, metric, divisor=1):
            return values(select(name, layout), metric, divisor)
        for name in names:
            for layout in layouts:
                selected = select(name, layout)
                for metric, divisor, label in METRICS:
                    data = values(selected, metric, divisor)
                    table.append(dict(placement=placement, reasoner=reasoner, scenario=name,
                        layout=layout, metric=metric, display_unit=label, attempted=sum(not r.get("missing_measurement") for r in selected),
                        completed=sum(r['status']=='completed' for r in selected),
                        timeouts=sum(r['status']=='timeout' for r in selected),
                        validation=selected[0]['validation_state'] if selected else 'not validated',
                        median=statistics.median(data) if data else '',
                        minimum=min(data) if data else '', maximum=max(data) if data else ''))

        # Availability and validity must be read before completed-only costs.
        fig, ax = plt.subplots(figsize=(max(8, len(names)*1.35), 3), layout='constrained')
        matrix = np.array([[sum(r['status']=='completed' for r in select(n,l))/len(select(n,l))
                            if select(n,l) else np.nan for n in names] for l in layouts])
        ax.imshow(matrix, cmap='YlGnBu', vmin=0, vmax=1, aspect='auto')
        for i,l in enumerate(layouts):
            for j,n in enumerate(names):
                rr=select(n,l); completed=sum(r['status']=='completed' for r in rr)
                state=rr[0]['validation_state'] if rr else 'not validated'
                state=state.replace('reference unavailable', 'reference\nunavailable')
                cell = ('No measurements\nScenario failed' if any(r.get('missing_measurement') for r in rr) else f'{completed}/{len(rr)} completed\n{sum(r["status"]=="timeout" for r in rr)} timeouts\n{state}')
                ax.text(j,i,cell,
                        ha='center', va='center', fontsize=8, color='white' if matrix[i,j]>.65 else 'black')
        ax.set_xticks(range(len(names)), names, rotation=20, ha='right')
        ax.set_yticks(range(len(layouts)), layouts)
        ax.set_title(f'{placement} / {reasoner}: completion and sampled query equivalence\nMissing replicated reference is not evidence of a semantic mismatch')
        save(fig, prefix+'-completion.png')

        fig, axes = plt.subplots(2,3,figsize=(12,7),layout='constrained')
        for ax,(metric,divisor,label) in zip(axes.flat,METRICS):
            for index,layout in enumerate(layouts):
                for j,name in enumerate(names):
                    data=samples(name,layout,metric,divisor); x=j+(index-.5)*.24
                    if data:
                        median=statistics.median(data)
                        ax.errorbar(x,median,yerr=[[median-min(data)],[max(data)-median]],fmt='o',capsize=3,color=COLORS[layout],label=layout if j==0 else None)
                        ax.scatter(np.linspace(x-.045,x+.045,len(data)),data,s=12,alpha=.5,color=COLORS[layout])
                    else:
                        ax.text(x,.025,'NA',transform=ax.get_xaxis_transform(),ha='center',color=COLORS[layout],fontsize=7)
            ax.set_xticks(range(len(names)), names, rotation=35,ha='right')
            ax.set_ylabel(label); ax.grid(axis='y',alpha=.25)
            ax.set_xlim(-.5,len(names)-.5)
            ax.set_ylim(bottom=0)
        if axes.flat[0].get_legend_handles_labels()[0]: axes.flat[0].legend()
        fig.suptitle(f'{placement} / {reasoner}: total costs across the continuum\nDots: repetitions; large marker: median; whiskers: observed min–max (not confidence intervals). NA: no completed measurement.',fontsize=11)
        save(fig,prefix+'-costs.png')

        # Only compare complete, equivalent cohorts. No timeout imputation.
        eligible=[]
        for name in names:
            pair=[select(name,l) for l in COLORS]
            if all(rr and all(r['status']=='completed' for r in rr) and rr[0]['validation_state']=='equivalent' for rr in pair):
                eligible.append(name)
        if eligible:
            ratios=np.full((len(METRICS),len(eligible)),np.nan)
            for i,(metric,divisor,label) in enumerate(METRICS):
                for j,name in enumerate(eligible):
                    d=samples(name,'distributed',metric); r=samples(name,'replicated',metric)
                    if d and r and statistics.median(r)>0:
                        ratio=statistics.median(d)/statistics.median(r);ratios[i,j]=ratio
                        contrasts.append(dict(placement=placement,reasoner=reasoner,scenario=name,metric=metric,
                            distributed_over_replicated=ratio,reduction_percent=100*(1-ratio),
                            comparison='ratio of medians; complete cohorts; sampled query equivalence'))
            fig,ax=plt.subplots(figsize=(max(6,len(eligible)*1.8),5),layout='constrained')
            im=ax.imshow(np.clip(np.log2(np.maximum(ratios,1e-9)),-2,2),cmap='RdBu_r',vmin=-2,vmax=2,aspect='auto')
            for i in range(len(METRICS)):
                for j in range(len(eligible)):
                    v=ratios[i,j]
                    ax.text(j,i,f'{v:.2f}×' if math.isfinite(v) else 'NA',ha='center',va='center',color='white' if v>2 or v<.5 else 'black')
            ax.set_xticks(range(len(eligible)),eligible);ax.set_yticks(range(len(METRICS)),[m[2] for m in METRICS])
            ax.set_title(f'{placement} / {reasoner}: distributed cost ÷ replicated cost\nBelow 1: lower distributed cost. Above 1: higher distributed cost.\nOnly complete cohorts with available sampled equivalence checks.')
            cb=fig.colorbar(im,ax=ax,ticks=[-2,-1,0,1,2]);cb.ax.set_yticklabels(['≤0.25×','0.5×','1×','2×','≥4×'])
            save(fig,prefix+'-tradeoffs.png')

        for family in ('users','data'):
            subset=[n for n in names if scenarios[n]['family']==family]
            if not subset: continue
            xvals={n: scenarios[n]['users'] if family=='users' else scenarios[n]['target_triples'] for n in subset}
            subset.sort(key=lambda n:xvals[n])
            fig,axes=plt.subplots(2,3,figsize=(10,6.7),layout='constrained')
            for ax,(metric,divisor,label) in zip(axes.flat,METRICS):
                for layout in layouts:
                    medians=[]
                    for name in subset:
                        data=samples(name,layout,metric,divisor); x=xvals[name]
                        medians.append(statistics.median(data) if data else float('nan'))
                        if data:
                            ax.vlines(x,min(data),max(data),color=COLORS[layout]);ax.scatter([x]*len(data),data,s=12,color=COLORS[layout],alpha=.5)
                        else:
                            ax.text(x,.025,f'{layout}: NA',transform=ax.get_xaxis_transform(),ha='center',fontsize=7,color=COLORS[layout])
                    ax.plot([xvals[n] for n in subset],medians,'o-',color=COLORS[layout],label=layout)
                low, high = min(xvals[n] for n in subset), max(xvals[n] for n in subset)
                margin = max((high-low)*.15, abs(low)*.05, 1)
                ax.set_xlim(low-margin, high+margin)
                if family == 'users' and low > 0 and high / low >= 100:
                    ax.set_xscale('log')
                    ax.set_xlim(low / 1.5, high * 1.5)
                    ax.set_xticks([xvals[n] for n in subset], [str(xvals[n]) for n in subset])
                    ax.tick_params(axis='x', labelrotation=30)
                ax.set_xlabel('Synthetic users' if family=='users' else 'Target logical triples (neutral padding)')
                ax.set_ylabel(label);ax.grid(alpha=.25);ax.set_ylim(bottom=0)
            if axes.flat[0].get_legend_handles_labels()[0]: axes.flat[0].legend()
            fig.suptitle(f'{placement} / {reasoner}: {family} load sensitivity on fixed physical hosts\nMedians and observed ranges; missing costs remain NA. Lines connect measured levels only.',fontsize=11)
            save(fig,prefix+f'-{family}.png')

        # Preparation partition is additive by definition, not a network profiler.
        fig,ax=plt.subplots(figsize=(10,4),layout='constrained')
        labels=[];x=0
        for name in names:
            for layout in layouts:
                selected=select(name,layout)
                critical=values(selected,'reasoning_ms',1000)
                residual=values(selected,'coordination_overhead_ms',1000)
                labels.append(f'{name}\n{layout[:4]}')
                if critical and residual:
                    ax.bar(x,statistics.mean(critical),color='#009E73',label='Reasoning critical path' if x==0 else None)
                    ax.bar(x,statistics.mean(residual),bottom=statistics.mean(critical),color='#CC79A7',label='Remaining preparation wall time' if x==0 else None)
                else: ax.text(x,0,'NA',ha='center',va='bottom',fontsize=7)
                x+=1
        ax.set_xticks(range(x),labels,rotation=40,ha='right');ax.set_ylabel('Mean preparation time (s)')
        if ax.get_legend_handles_labels()[0]: ax.legend()
        ax.set_title(f'{placement} / {reasoner}: where preparation time is spent\nResidual includes serialization, transport, parsing and coordination; it is not pure network latency.')
        save(fig,prefix+'-preparation.png')

    analysis=directory/'analysis';analysis.mkdir(exist_ok=True)
    write_table(analysis/'global-costs.csv',table)
    write_table(analysis/'missing-measurements.csv',missing)
    write_table(analysis/'layout-contrasts.csv',contrasts)
    (analysis/'README.md').write_text('''# Campaign interpretation

Start with `../figures/global-*-completion.png`, then `global-*-costs.png` and
`global-*-tradeoffs.png`. Load-specific figures compare users and neutral data
padding. Individual host and request-concurrency figures remain in `figures/`.
CSV tables contain the exact plotted statistics and cost ratios.

- Missing or timed-out results are not zero and are not imputed as deadline values.
- Cost ratios require complete cohorts and available sampled query equivalence.
- Error bars are observed min–max ranges, not confidence intervals. Three
  repetitions do not support strong inferential claims.
- Layouts run sequentially, not in randomized order. Process RSS may retain
  allocator state from earlier scenarios and is not host/cgroup memory.
- Preparation is asymmetric: distributed sends fragments; replicated generates
  its graph locally. Payload bytes are serialized messages, not VPN traffic.
  Completion under these budgets does not isolate reasoning capacity alone.
- Semantic checks cover the first repetition and the configured query catalog.
  An unavailable replicated reference cannot establish correctness or mismatch.
- Neutral padding tests data volume, not richer policies or ontology complexity.
- One participant-count level cannot demonstrate strong/weak scaling efficiency.
  Two user or data levels show sensitivity, not an asymptotic scaling law.
- Historical raw results are unchanged. Read semantic-validation.csv to distinguish
  a missing reference from historical summary labels saying mismatch.
''')
    manifest.extend(infrastructure_figures(directory, figures))
    manifest.extend(concurrency_matrix(directory, figures))
    return manifest


def infrastructure_figures(directory, figures):
    """Compare per-host CPU across workloads and request scaling with uncertainty."""
    import matplotlib.pyplot as plt
    import numpy as np
    manifests=[]
    configuration=json.loads((directory/'configuration.json').read_text())
    scenarios={s['name']:s for s in configuration['scenarios']}
    for placement in sorted(directory.glob('placement-*')):
        paths={p.parents[1].name:p for p in placement.glob('*/measured/distributed-reasoning-scalability')}
        campaign_path = directory / 'campaign.json'
        if campaign_path.exists():
            for step in json.loads(campaign_path.read_text()).get('steps', []):
                if placement.name == f"placement-{step['containers_per_host']}":
                    paths.setdefault(step['scenario'], placement / step['scenario'] / 'measured/distributed-reasoning-scalability')
        names=[n for n in scenarios if n in paths]
        node_rows={n:read_rows(paths[n]/'node-runs.csv') for n in names}
        observed={r['node_id'].rsplit('-c',1)[0] for rr in node_rows.values() for r in rr}
        hosts=[h for h in ['cloud','fog','mist','edge1','edge2','edge3'] if h in observed]
        hosts+=sorted(observed-set(hosts))
        reasoners=sorted({r['reasoner'] for rr in node_rows.values() for r in rr})
        for reasoner in reasoners:
            arrays=[]
            for layout in COLORS:
                matrix=np.full((len(hosts),len(names)),np.nan)
                for j,name in enumerate(names):
                    per_run=defaultdict(float)
                    for r in node_rows[name]:
                        if r['reasoner']==reasoner and r['layout']==layout and r.get('status','completed')=='completed':
                            per_run[(r['node_id'].rsplit('-c',1)[0],r['run_id'])]+=float(r['process_cpu_ms'])/1000
                    for i,host in enumerate(hosts):
                        data=[v for (h,_),v in per_run.items() if h==host]
                        if data:matrix[i,j]=statistics.median(data)
                arrays.append(matrix)
            if not hosts:continue
            maximum=max((float(np.nanmax(a)) for a in arrays if np.isfinite(a).any()),default=1)
            fig,axes=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
            cmap=plt.get_cmap('YlGnBu').with_extremes(bad='#eeeeee')
            for ax,layout,matrix in zip(axes,COLORS,arrays):
                im=ax.imshow(matrix,cmap=cmap,vmin=0,vmax=maximum,aspect='auto')
                for i in range(len(hosts)):
                    for j in range(len(names)):
                        v=matrix[i,j];ax.text(j,i,f'{v:.1f}' if math.isfinite(v) else 'NA',ha='center',va='center',fontsize=7,color='white' if v>maximum*.6 else 'black')
                ax.set_xticks(range(len(names)),names,rotation=40,ha='right');ax.set_yticks(range(len(hosts)),hosts);ax.set_title(layout)
            fig.colorbar(im,ax=axes,label='Median summed participant CPU time per host (s)',shrink=.8)
            fig.suptitle(f'{placement.name} / {reasoner}: cost distribution across physical hosts\nShared color scale; NA = no completed node measurement, not zero cost.',fontsize=11)
            name=f'global-{placement.name}-{reasoner}-host-cpu.png';fig.savefig(figures/name,dpi=300,bbox_inches='tight');plt.close(fig);manifests.append(name)
            for scenario,path in paths.items():
                if not any(level > 1 for level in scenarios[scenario].get('concurrency', [1])):continue
                rows=[r for r in read_rows(path/'client-throughput.csv') if r['reasoner']==reasoner]
                if not rows:continue
                fig,axes=plt.subplots(1,3,figsize=(10,3.6),layout='constrained')
                for ax,(metric,divisor,label) in zip(axes,[('latency_p95_ms',1000,'Within-run request p95 (s)'),('client_requests_per_second',1,'Completed catalog requests/s'),('error_rate',1,'Request error fraction')]):
                    for layout in COLORS:
                        rr=[r for r in rows if r['layout']==layout];levels=sorted({int(r['concurrency']) for r in rr})
                        medians=[]
                        for level in levels:
                            data=[float(r[metric])/divisor for r in rr if int(r['concurrency'])==level and r.get(metric) not in ('',None)]
                            medians.append(statistics.median(data) if data else np.nan)
                            if data:ax.vlines(level,min(data),max(data),color=COLORS[layout]);ax.scatter([level]*len(data),data,s=15,color=COLORS[layout],alpha=.5)
                        ax.plot(levels,medians,'o-',label=layout,color=COLORS[layout])
                    ax.set_xlabel('Concurrent full-catalog requests');ax.set_ylabel(label);ax.set_ylim(bottom=0);ax.grid(alpha=.25)
                if all(float(r['error_rate']) == 0 for r in rows):
                    counts = [f"{layout}: 0 / {sum(int(r['client_requests']) for r in rows if r['layout'] == layout)} requests failed" for layout in COLORS]
                    axes[2].text(.5, .55, '\n'.join(counts), transform=axes[2].transAxes, ha='center', va='center', fontsize=8)
                axes[0].legend();fig.suptitle(f'{placement.name} / {reasoner}: request-load scalability\nMedians and observed ranges across repetitions; p95 excludes failed requests.',fontsize=11)
                name=f'global-{placement.name}-{reasoner}-{scenario}-concurrency.png';fig.savefig(figures/name,dpi=300,bbox_inches='tight');plt.close(fig);manifests.append(name)
    return manifests


def concurrency_matrix(directory, figures):
    """Render every attempted user/concurrency level, including absent measurements."""
    import matplotlib.pyplot as plt
    import numpy as np
    config=json.loads((directory/'configuration.json').read_text())
    campaign_path=directory/'campaign.json'
    if not campaign_path.exists(): return []
    steps=json.loads(campaign_path.read_text()).get('steps',[])
    scenarios={s['name']:s for s in config['scenarios']}
    manifest=[]
    for count in sorted({s['containers_per_host'] for s in steps}):
        names=[s['scenario'] for s in steps if s['containers_per_host']==count and scenarios[s['scenario']]['family']=='users']
        names.sort(key=lambda n:scenarios[n]['users'])
        if not names:continue
        levels=sorted({c for n in names for c in scenarios[n]['concurrency']})
        for reasoner in config['experiment']['reasoners']:
            rows={n:read_rows(directory/f'placement-{count}'/n/'measured/distributed-reasoning-scalability/client-throughput.csv') for n in names}
            fig,axes=plt.subplots(2,3,figsize=(11,7),layout='constrained')
            for j,(metric,divisor,label) in enumerate([('latency_p95_ms',1000,'Within-run p95 latency (s)'),('client_requests_per_second',1,'Completed catalog requests/s'),('error_rate',1,'Request error fraction')]):
                arrays=[]
                for layout in COLORS:
                    matrix=np.full((len(names),len(levels)),np.nan)
                    for i,n in enumerate(names):
                        for k,c in enumerate(levels):
                            rr=[r for r in rows[n] if r['layout']==layout and r['reasoner']==reasoner and int(r['concurrency'])==c and r.get(metric) not in ('',None)]
                            if rr: matrix[i,k]=statistics.median(float(r[metric])/divisor for r in rr)
                    arrays.append(matrix)
                maximum=1 if metric=='error_rate' else max([float(np.nanmax(a)) for a in arrays if np.isfinite(a).any()]+[.001])
                for i,(layout,matrix) in enumerate(zip(COLORS,arrays)):
                    ax=axes[i,j]; im=ax.imshow(matrix,vmin=0,vmax=maximum,cmap=plt.get_cmap('YlOrRd').with_extremes(bad='#eeeeee'),aspect='auto')
                    for a in range(len(names)):
                        for b in range(len(levels)):
                            value=matrix[a,b];ax.text(b,a,f'{value:.2f}' if math.isfinite(value) else 'NA',ha='center',va='center',fontsize=8,color='white' if value>maximum*.65 else 'black')
                    ax.set_xticks(range(len(levels)),levels);ax.set_yticks(range(len(names)),[scenarios[n]['users'] for n in names])
                    ax.set_xlabel('Concurrent catalog requests');ax.set_ylabel(f'{layout}: synthetic users');ax.set_title(label)
                fig.colorbar(im,ax=axes[:,j],shrink=.65)
            fig.suptitle(f'placement-{count} / {reasoner}: users × request concurrency\nMedians across recorded repetitions; p95 excludes failed requests. Grey NA = no measurement, not zero.',fontsize=11)
            name=f'global-placement-{count}-{reasoner}-users-concurrency.png'
            fig.savefig(figures/name,dpi=300,bbox_inches='tight');plt.close(fig);manifest.append(name)
    return manifest
