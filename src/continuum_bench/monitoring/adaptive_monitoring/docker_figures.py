"""Reuse Docker scalability metrics and host aggregation for adaptive comparisons."""
from collections import defaultdict
import json
import math
import statistics
import tomllib

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np

from ..container_scale.synthesis import METRICS, COLORS, values
from ..container_scale.resources import METRICS as NODE_METRICS, aggregate_nodes
from .comparison import read_csv, write_csv, save_figure


def remap_nodes(rows, logical_to_physical):
    """The existing aggregator groups node-ID prefixes; supply physical identity."""
    return [{**r, 'node_id':logical_to_physical.get(r['node_id'],r['node_id'].rsplit('-c',1)[0])+'-c1'} for r in rows]


def docker_figures(directory, baseline, decisions, figures):
    config=json.loads((directory/'configuration.json').read_text())
    campaign=json.loads((baseline/'campaign.json').read_text())
    scenarios={s['name']:s for s in config['scenarios']}
    manifest=[];costs=[];hosts_table=[];coverage=[];matrices=[]
    recovery={}; mappings={}
    for decision in decisions:
        if not decision.get('results'):
            continue
        result=directory/decision['results']; attempt=result.parent.parent
        count=decision.get('containers_per_host',int(attempt.name.rsplit('-',2)[1]))
        cohort=f"{decision['layout']}-attempt-{decision['attempt']}"
        recovery[count,cohort,decision['scenario']]=result
        topology=attempt/'deployment/topology.toml'
        placement=baseline/f'placement-{count}/placement.json'
        if topology.exists() and placement.exists():
            host_ids={n['host']:n['id'] for n in json.loads(placement.read_text())['physical_hosts']}
            nodes=tomllib.loads(topology.read_text())['topologies']['container-scale']['nodes']
            mappings[count,cohort,decision['scenario']]={n['id']:host_ids[n['host']] for n in nodes}
    counts=sorted({s['containers_per_host'] for s in campaign['steps']})
    for count in counts:
        user_names=sorted({s['scenario'] for s in campaign['steps'] if s['containers_per_host']==count and scenarios[s['scenario']]['family']=='users'},key=lambda n:scenarios[n]['users'])
        if not user_names:continue
        users=[scenarios[n]['users'] for n in user_names]
        for name in user_names:
            for layout in ('distributed','replicated'):
                matching=[d for d in decisions if d['scenario']==name and d['layout']==layout and d.get('containers_per_host',count)==count]
                coverage.append(dict(placement=count,scenario=name,users=scenarios[name]['users'],layout=layout,
                    status=matching[-1]['status'] if matching else 'not_selected_or_not_recorded'))
        fig,ax=plt.subplots(figsize=(max(9,len(users)*1.6),3),layout='constrained')
        shades={'execution_recovered':'#d9efdf','not_recovered':'#ffe0b2','abstained':'#e5d8ef','not_needed':'#d7eaf7'}
        for i,layout in enumerate(('distributed','replicated')):
            for j,name in enumerate(user_names):
                state=next(r['status'] for r in coverage if r['placement']==count and r['scenario']==name and r['layout']==layout)
                from matplotlib.patches import Rectangle
                ax.add_patch(Rectangle((j-.5,i-.5),1,1,facecolor=shades.get(state,'#eeeeee'),edgecolor='white'))
                ax.text(j,i,state.replace('_','\n'),ha='center',va='center',fontsize=8)
        ax.set(xlim=(-.5,len(users)-.5),ylim=(1.5,-.5),xticks=range(len(users)),yticks=[0,1],yticklabels=['Distributed trigger','Replicated trigger'])
        ax.set_xticklabels(users);ax.set_xlabel('Synthetic users')
        ax.set_title(f'Placement {count}: supervisor action coverage\nUnselected levels are not adaptive measurements; not needed is not a recovery.')
        save_figure(fig,figures,f'docker-placement-{count}-adaptive-coverage.png',manifest)
        cohorts=sorted({cohort for placement,cohort,name in recovery if placement==count})
        for cohort in cohorts:
            for reasoner in config['experiment']['reasoners']:
                data={};node_rows={};query_rows={}
                for phase in ('Baseline','Adaptive trial'):
                    for name in user_names:
                        path=(baseline/f'placement-{count}'/name/'measured/distributed-reasoning-scalability') if phase=='Baseline' else recovery.get((count,cohort,name))
                        for target,filename in ((data,'distributed-reasoning-summary.csv'),(node_rows,'node-runs.csv'),(query_rows,'query-scalability.csv')):
                            target[phase,name]=[r for r in read_csv(path/filename) if r['reasoner']==reasoner] if path else []
                prefix=f'docker-placement-{count}-{cohort}-{reasoner}'
                fig,axes=plt.subplots(2,3,figsize=(13,7),layout='constrained')
                for ax,(metric,divisor,label) in zip(axes.flat,METRICS):
                    for layout,color in COLORS.items():
                        for phase,style,marker in (('Baseline','--','o'),('Adaptive trial','-','s')):
                            means=[];low=[];high=[]
                            for name in user_names:
                                selected=[r for r in data[phase,name] if r['layout']==layout]
                                samples=values(selected,metric,divisor)
                                mid=statistics.median(samples) if samples else math.nan
                                means.append(mid);low.append(mid-min(samples) if samples else math.nan);high.append(max(samples)-mid if samples else math.nan)
                                costs.append(dict(placement=count,cohort=cohort,reasoner=reasoner,scenario=name,users=scenarios[name]['users'],phase=phase,layout=layout,metric=metric,unit=label,samples=len(samples),median=mid,minimum=min(samples) if samples else math.nan,maximum=max(samples) if samples else math.nan))
                            ax.errorbar(users,means,yerr=[low,high],color=color,linestyle=style,marker=marker,capsize=2,label=f'{phase} / {layout}')
                    ax.set(xscale='log',xlim=(min(users)/1.4,max(users)*1.4),xlabel='Synthetic users',ylabel=label,ylim=(0,None))
                    ax.set_xticks(users,[str(u) for u in users]);ax.tick_params(axis='x',labelrotation=30);ax.grid(alpha=.2)
                axes[0,0].legend(fontsize=7)
                fig.suptitle(f'{prefix}: same six metrics as Docker scalability\nCompleted preparations only; medians and observed ranges. Gaps mean unavailable, not zero. Read coverage and completion first.',fontsize=10)
                save_figure(fig,figures,prefix+'-users-costs.png',manifest)
                levels=sorted({int(r['concurrency']) for rows in query_rows.values() for r in rows})
                if levels:
                    fig,axes=plt.subplots(4,3,figsize=(13,max(8,len(users)*1.4)),layout='constrained')
                    arrays=[]
                    for layout in COLORS:
                        for phase in ('Baseline','Adaptive trial'):
                            grids=[np.full((len(users),len(levels)),np.nan) for _ in range(3)]
                            for i,name in enumerate(user_names):
                                for j,level in enumerate(levels):
                                    rr=[r for r in query_rows[phase,name] if r['layout']==layout and int(r['concurrency'])==level]
                                    n=sum(int(r['client_requests']) for r in rr);fail=sum(int(r['error_count']) for r in rr)
                                    lat=[float(r['latency_p95_ms'])/1000 for r in rr if int(r['client_requests'])>int(r['error_count']) and math.isfinite(float(r['latency_p95_ms']))]
                                    thr=[(int(r['client_requests'])-int(r['error_count']))*1000/float(r['query_wall_ms']) for r in rr if float(r['query_wall_ms'])>0]
                                    vals=[statistics.median(lat) if lat else math.nan,statistics.median(thr) if thr else math.nan,fail/n if n else math.nan]
                                    for grid,v in zip(grids,vals):grid[i,j]=v
                                    matrices.append(dict(placement=count,cohort=cohort,reasoner=reasoner,users=users[i],phase=phase,layout=layout,concurrency=level,requests=n,failures=fail,p95_successful_seconds=vals[0],completed_requests_s=vals[1],error_fraction=vals[2]))
                            arrays.append((layout,phase,grids))
                    for col,title in enumerate(('Within-run p95 (s)','Completed catalog requests / s','Request error fraction')):
                        finite=[v for _,_,grids in arrays for v in grids[col].flat if math.isfinite(v)]
                        norm=Normalize(0,1 if col==2 else max(finite,default=1) or 1)
                        for row,(layout,phase,grids) in enumerate(arrays):
                            ax=axes[row,col];grid=grids[col]
                            im=ax.imshow(grid,aspect='auto',norm=norm,cmap=plt.get_cmap('YlOrRd').with_extremes(bad='#dddddd'))
                            for i in range(len(users)):
                                for j in range(len(levels)):
                                    value=grid[i,j];label=f'{value:.2f}' if math.isfinite(value) else 'NA'
                                    ax.text(j,i,label,ha='center',va='center',fontsize=7,color='white' if math.isfinite(value) and norm(value)>.65 else 'black')
                            ax.set(title=f'{phase} / {layout}\n{title}',xticks=range(len(levels)),yticks=range(len(users)),ylabel='Users')
                            ax.set_xticklabels(levels);ax.set_yticklabels(users);ax.set_xlabel('Concurrent catalog requests')
                        fig.colorbar(im,ax=list(axes[:,col]),shrink=.6)
                    fig.suptitle(prefix+' — Docker users × concurrency comparison\nCommon color scales; NA is unmeasured/invalid. Latency excludes failures; zero throughput is retained for attempted all-failed requests.',fontsize=10)
                    save_figure(fig,figures,prefix+'-users-concurrency.png',manifest)
                placement=baseline/f'placement-{count}/placement.json'
                host_ids=[n['id'] for n in json.loads(placement.read_text())['physical_hosts']] if placement.exists() else []
                if not host_ids:continue
                for metric,divisor,label,suffix in NODE_METRICS:
                    fig,axes=plt.subplots(math.ceil(len(host_ids)/3),3,figsize=(13,6),layout='constrained',squeeze=False,sharey=True)
                    upper = 0.0
                    for ax,host in zip(axes.flat,host_ids):
                        for layout,color in COLORS.items():
                            for phase,style,marker in (('Baseline','--','o'),('Adaptive trial','-','s')):
                                mids=[];lo=[];hi=[]
                                for name in user_names:
                                    mapping=mappings.get((count,cohort,name),{}) if phase=='Adaptive trial' else {}
                                    rows=remap_nodes(node_rows[phase,name],mapping) if phase=='Baseline' or mapping else []
                                    aggregates=aggregate_nodes(rows,metric,divisor)
                                    selected=[v for (h,l,r,run),v in aggregates.items() if h==host and l==layout and r==reasoner]
                                    upper = max(upper, max(selected, default=0))
                                    mid=statistics.median(selected) if selected else math.nan
                                    mids.append(mid);lo.append(mid-min(selected) if selected else math.nan);hi.append(max(selected)-mid if selected else math.nan)
                                    hosts_table.append(dict(placement=count,cohort=cohort,reasoner=reasoner,host=host,users=scenarios[name]['users'],phase=phase,layout=layout,metric=metric,samples=len(selected),median=mid))
                                ax.errorbar(users,mids,yerr=[lo,hi],color=color,linestyle=style,marker=marker,capsize=2,label=f'{phase} / {layout}')
                        ax.set(title=host,xscale='log',xlim=(min(users)/1.4,max(users)*1.4),ylim=(0,None),xlabel='Synthetic users',ylabel=label)
                        ax.set_xticks(users,[str(u) for u in users]);ax.tick_params(axis='x',labelrotation=30);ax.grid(alpha=.2)
                    for ax in list(axes.flat)[len(host_ids):]:ax.set_visible(False)
                    axes.flat[0].set_ylim(0,max(1,upper*1.08))
                    axes.flat[0].legend(fontsize=6,loc='upper left')
                    fig.suptitle(prefix+f' — {label}\nActual physical placement, shared scales. Missing/unoccupied recovery hosts have no point. Completed preparations only.',fontsize=10)
                    save_figure(fig,figures,prefix+f'-nodes-{suffix}.png',manifest)
    analysis=directory/'analysis'
    write_csv(analysis/'docker-cost-comparison.csv',costs)
    write_csv(analysis/'docker-node-comparison.csv',hosts_table)
    write_csv(analysis/'docker-concurrency-comparison.csv',matrices)
    write_csv(analysis/'adaptive-coverage.csv',coverage)
    return manifest
