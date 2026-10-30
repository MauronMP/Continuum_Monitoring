"""Paired service outcomes: same workload, explicit missing trials and intervention cost."""
from collections import defaultdict
import json
import math

import matplotlib.pyplot as plt
import numpy as np

from .comparison import read_csv, write_csv, save_figure


def metrics(path, layout, reasoner, concurrency=None):
    preparations = [r for r in read_csv(path/'distributed-reasoning-summary.csv')
                    if r['layout'] == layout and r['reasoner'] == reasoner]
    queries = [r for r in read_csv(path/'query-scalability.csv')
               if r['layout'] == layout and r['reasoner'] == reasoner
               and (concurrency is None or int(r['concurrency']) == concurrency)]
    total = sum(int(r['client_requests']) for r in queries)
    failed = sum(int(r['error_count']) for r in queries)
    return dict(preparations=len(preparations), prepared=sum(r['status']=='completed' for r in preparations),
                requests=total, completed=total-failed,
                completion_percent=100*(total-failed)/total if total else math.nan)


def paired_figures(directory, baseline, decisions, figures):
    """Only the intervention's target layout is a matched adaptive trial."""
    config = json.loads((directory/'configuration.json').read_text())
    scenarios = {s['name']:s for s in config.get('scenarios', [])}
    grouped = defaultdict(list)
    for d in decisions:
        if scenarios.get(d['scenario'], {}).get('family') == 'users':
            grouped[d.get('containers_per_host', 1), d['scenario'], d['layout']].append(d)
    manifest, table, trajectories = [], [], []
    for count in sorted({key[0] for key in grouped}):
        names = sorted({k[1] for k in grouped if k[0] == count}, key=lambda n:scenarios[n]['users'])
        users = [scenarios[n]['users'] for n in names]
        for reasoner in config.get('experiment', {}).get('reasoners', []):
            tag = f'paired-placement-{count}-{reasoner}'
            fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout='constrained', sharex=True)
            for li, layout in enumerate(('distributed', 'replicated')):
                for i, name in enumerate(names):
                    actions = sorted(grouped.get((count,name,layout), []), key=lambda d:d['attempt'])
                    before = baseline/f'placement-{count}'/name/'measured/distributed-reasoning-scalability'
                    # Never select the best outcome post hoc; use the final measured attempt.
                    measured = [d for d in actions if d.get('results')]
                    final = measured[-1] if measured else None
                    status = actions[-1]['status'] if actions else 'not_selected'
                    for phase, path, offset, color in [('Docker only',before,-.18,'#777777'),
                            ('Adaptive measured',directory/final['results'] if final else None,.18,'#0072B2')]:
                        m = metrics(path,layout,reasoner) if path else None
                        if m:
                            table.append(dict(containers_per_host=count,scenario=name,users=users[i],layout=layout,
                                reasoner=reasoner,phase=phase,final_status=status,**m))
                        for j, (num,den) in enumerate((('prepared','preparations'),('completed','requests'))):
                            ax = axes[li,j]
                            if m and m[den]:
                                value = 100*m[num]/m[den]
                                ax.bar(i+offset,value,width=.34,color=color)
                                ax.text(i+offset,value+2,f'{m[num]}/{m[den]}',ha='center',fontsize=8,rotation=90)
                            else:
                                label = 'no requests' if m and m['preparations'] else 'no trial'
                                ax.text(i+offset,3,label,ha='center',fontsize=7,rotation=90,color='#555555')
                    for d in measured:
                        m = metrics(directory/d['results'],layout,reasoner)
                        trajectories.append(dict(containers_per_host=count,scenario=name,users=users[i],layout=layout,
                            reasoner=reasoner,attempt=d['attempt'],status=d['status'],
                            deployment_seconds=d.get('deployment_seconds',math.nan),
                            attempt_seconds=d.get('elapsed_seconds',math.nan),
                            source=d.get('decision',{}).get('source',''),destination=d.get('decision',{}).get('destination',''),**m))
                for j, label in enumerate(('Preparations completed (%)','Catalog requests completed (%)')):
                    axes[li,j].set(title=f'{layout.capitalize()} — {label}',ylim=(0,132),yticks=[0,25,50,75,100],
                        xticks=range(len(users)),xticklabels=users,xlabel='Synthetic users')
                    axes[li,j].grid(axis='y',alpha=.2)
                    axes[li,j].tick_params(labelbottom=True)
            from matplotlib.patches import Patch
            axes[0,0].legend(handles=[Patch(color='#777777',label='Docker only'),Patch(color='#0072B2',label='Final measured adaptive attempt')],loc='upper left',fontsize=8)
            fig.suptitle(f'{reasoner.upper()}: workload-matched availability\nNo trial ≠ unchanged performance. Counts retain failed requests; no requests ≠ 0% completion.',fontsize=11)
            save_figure(fig,figures,tag+'-availability.png',manifest)

            concurrencies = sorted({int(r['concurrency']) for name in names for r in read_csv(
                baseline/f'placement-{count}'/name/'measured/distributed-reasoning-scalability/query-scalability.csv') if r['reasoner']==reasoner})
            if concurrencies:
                fig,axes = plt.subplots(2,3,figsize=(13, max(6,len(names)*.7+2)),layout='constrained')
                for li,layout in enumerate(('distributed','replicated')):
                    arrays = [np.full((len(names),len(concurrencies)),np.nan) for _ in range(3)]
                    for i,name in enumerate(names):
                        actions = sorted(grouped.get((count,name,layout),[]),key=lambda d:d['attempt'])
                        measured=[d for d in actions if d.get('results')]
                        paths=[baseline/f'placement-{count}'/name/'measured/distributed-reasoning-scalability',
                               directory/measured[-1]['results'] if measured else None]
                        for j,c in enumerate(concurrencies):
                            for phase,path in enumerate(paths):
                                if path: arrays[phase][i,j]=metrics(path,layout,reasoner,c)['completion_percent']
                    arrays[2]=arrays[1]-arrays[0]
                    for col,(array,title) in enumerate(zip(arrays,('Docker only','Final adaptive trial','Change (percentage points)'))):
                        ax=axes[li,col]; cmap=plt.get_cmap('RdYlGn' if col==2 else 'viridis').copy();cmap.set_bad('#eeeeee')
                        im=ax.imshow(array,vmin=-100 if col==2 else 0,vmax=100,cmap=cmap,aspect='auto')
                        for i in range(len(names)):
                            for j in range(len(concurrencies)):
                                v=array[i,j];ax.text(j,i,'NA' if np.isnan(v) else f'{v:.0f}',ha='center',va='center',fontsize=9,color='black' if np.isnan(v) or v>55 else 'white')
                        ax.set(title=f'{layout.capitalize()} / {title}',xticks=range(len(concurrencies)),xticklabels=concurrencies,
                            yticks=range(len(users)),yticklabels=users,xlabel='Concurrent catalog requests',ylabel='Synthetic users')
                        fig.colorbar(im,ax=ax,shrink=.7)
                fig.suptitle('Request completion (%) and paired change\nNA: no paired request evidence. Prepared-but-failing and unprepared workloads remain distinct.',fontsize=11)
                save_figure(fig,figures,tag+'-concurrency-benefit.png',manifest)

            trial = [r for r in trajectories if r['containers_per_host']==count and r['reasoner']==reasoner]
            if trial:
                fig,axes=plt.subplots(1,2,figsize=(12,max(4,len(trial)*.42+1)),layout='constrained')
                labels=[f"{r['users']} users / {r['layout']} / attempt {r['attempt']}" for r in trial]
                axes[0].barh(range(len(trial)),[r['completion_percent'] for r in trial],color='#0072B2')
                axes[0].set(xlim=(0,105),xlabel='Completed catalog requests (%)',yticks=range(len(trial)),yticklabels=labels)
                axes[1].barh(np.arange(len(trial))-.18,[r['deployment_seconds']/60 for r in trial],height=.34,label='Deployment',color='#E69F00')
                axes[1].barh(np.arange(len(trial))+.18,[r['attempt_seconds']/60 for r in trial],height=.34,label='Whole attempt',color='#777777')
                axes[1].set(xlabel='Minutes (not service recovery time)',yticks=range(len(trial)),yticklabels=labels);axes[1].legend()
                for i,r in enumerate(trial):
                    axes[0].text(2,i,f"{r['completed']}/{r['requests']} · {r['source']} → {r['destination']}",va='center',fontsize=8)
                fig.suptitle('Measured intervention effectiveness and overhead\nEvery attempt is retained, including unsuccessful interventions.',fontsize=11)
                save_figure(fig,figures,tag+'-intervention-cost.png',manifest)
    write_csv(directory/'analysis/paired-service-outcomes.csv',table)
    write_csv(directory/'analysis/intervention-trajectory.csv',trajectories)
    return manifest
