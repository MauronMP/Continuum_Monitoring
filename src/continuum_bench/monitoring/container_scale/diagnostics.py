"""Failure provenance: distinguish transport errors, budgets and missing phases."""
from collections import Counter
import json
import re

from .runner import read_rows


def error_kind(message):
    text = message.lower()
    if 'connectionreseterror' in text or 'connection reset' in text:
        return 'Connection reset'
    if '408' in text or 'worker phase exceeded' in text:
        return 'Worker deadline'
    if 'timeout' in text or 'timed out' in text:
        return 'Request timeout'
    return 'Other / unavailable'


def diagnostic_figures(directory, figures):
    import matplotlib.pyplot as plt
    import numpy as np
    from .synthesis import write_table
    campaign_path = directory / 'campaign.json'
    if not campaign_path.exists():
        return []
    campaign = json.loads(campaign_path.read_text())
    manifest, error_rows, phase_rows = [], [], []
    for count in sorted({s['containers_per_host'] for s in campaign['steps']}):
        steps = [s for s in campaign['steps'] if s['containers_per_host'] == count]
        names = [s['scenario'] for s in steps]
        causes = Counter()
        for step in steps:
            base = directory / f'placement-{count}' / step['scenario']
            for phase in ('warmup', 'measured'):
                path = base / phase / 'distributed-reasoning-scalability'
                runs = read_rows(path/'distributed-reasoning-summary.csv')
                queries = read_rows(path/'query-scalability.csv')
                phase_rows.append(dict(placement=count, scenario=step['scenario'], phase=phase,
                    completed_preparations=sum(r['status']=='completed' for r in runs),
                    failed_preparations=sum(r['status']!='completed' for r in runs),
                    query_attempts=sum(int(r['client_requests']) for r in queries),
                    query_errors=sum(int(r['error_count']) for r in queries),
                    scenario_status=step['status'], scenario_error=step.get('error','')))
                if phase != 'measured':
                    continue
                for row in queries:
                    messages = json.loads(row.get('error_details') or '[]')
                    messages += ['Details not recorded'] * max(0, int(row['error_count'])-len(messages))
                    for message in messages:
                        kind = error_kind(message)
                        causes[(step['scenario'],kind)] += 1
                        match = re.search(r'role=([^ ]+)', message)
                        error_rows.append(dict(placement=count, scenario=step['scenario'],
                            layout=row['layout'], reasoner=row['reasoner'], repetition=row['repetition'],
                            concurrency=row['concurrency'], error_kind=kind,
                            first_reported_worker=match.group(1) if match else '', detail=message))
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout='constrained')
        kinds = ['Connection reset','Worker deadline','Request timeout','Other / unavailable']
        bottoms = np.zeros(len(names))
        for kind, color in zip(kinds, ['#CC79A7','#D55E00','#E69F00','#999999']):
            values = [causes[(name,kind)] for name in names]
            axes[0].bar(range(len(names)),values,bottom=bottoms,label=kind,color=color)
            bottoms += values
        for i, n in enumerate(names):
            total = sum(r['query_attempts'] for r in phase_rows if r['placement']==count and r['scenario']==n and r['phase']=='measured')
            axes[0].text(i,bottoms[i]+.15,f'{int(bottoms[i])}/{total}' if total else 'NA',ha='center',fontsize=8)
        axes[0].set_ylim(0,max(max(bottoms,default=0)*1.25,1))
        axes[0].set_ylabel('Failed measured catalog requests');axes[0].legend(fontsize=7)
        axes[0].set_title('Query errors by recorded cause\nLabels: failed / attempted requests')
        cells=[]
        for phase in ('warmup','measured'):
            cells.append([next(r for r in phase_rows if r['placement']==count and r['scenario']==name and r['phase']==phase) for name in names])
        matrix=np.array([[r['completed_preparations']/(r['completed_preparations']+r['failed_preparations']) if r['completed_preparations']+r['failed_preparations'] else np.nan for r in group] for group in cells])
        axes[1].imshow(matrix,vmin=0,vmax=1,cmap=plt.get_cmap('YlGnBu').with_extremes(bad='#dddddd'),aspect='auto')
        for i, group in enumerate(cells):
            for j,r in enumerate(group):
                total=r['completed_preparations']+r['failed_preparations']
                axes[1].text(j,i,f"{r['completed_preparations']}/{total}" if total else 'No data',ha='center',va='center',color='white' if matrix[i,j]>.6 else 'black')
        axes[1].set_yticks([0,1],['Warm-up','Measured'])
        axes[1].set_title('Preparation evidence by phase\nCompleted / recorded; warm-up is not a measurement')
        for ax in axes:
            ax.set_xticks(range(len(names)),names,rotation=35,ha='right')
        fig.suptitle(f'placement-{count}: failure diagnosis (all recorded layouts/reasoners)\nCounts describe recorded failures; no cause or result is inferred for missing data.',fontsize=11)
        name=f'global-placement-{count}-failure-diagnosis.png'
        fig.savefig(figures/name,dpi=300,bbox_inches='tight');plt.close(fig);manifest.append(name)
    analysis=directory/'analysis';analysis.mkdir(exist_ok=True)
    write_table(analysis/'query-errors.csv',error_rows)
    write_table(analysis/'phase-evidence.csv',phase_rows)
    return manifest
