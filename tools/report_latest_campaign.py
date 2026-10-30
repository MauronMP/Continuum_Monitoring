#!/usr/bin/env python3
"""Portable, read-only evidence analysis; write derived PNGs and CSVs into a campaign."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def stamp(value):
    return datetime.fromisoformat(value).timestamp() if value else None


def rows(path):
    return list(csv.DictReader(path.open())) if path.exists() else []


def objects(value):
    if not value.strip(): return []
    try:
        data=json.loads(value);return data if isinstance(data,list) else [data]
    except json.JSONDecodeError:
        return [json.loads(line) for line in value.splitlines() if line.strip()]


def memory(value):
    m=re.match(r'([\d.]+)\s*(\w+)',value.split('/')[0])
    factors={'B':1/1048576,'KiB':1/1024,'MiB':1,'GiB':1024,'kB':1000/1048576,'MB':1000000/1048576,'GB':1000000000/1048576}
    return float(m[1])*factors.get(m[2],float('nan')) if m else float('nan')


def write(path,data):
    if data:
        with path.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)


def report(root):
    root=Path(root).resolve();out=root/'review';out.mkdir(exist_ok=True)
    decisions=json.loads((root/'decisions.json').read_text())
    groups=defaultdict(list)
    for d in decisions:groups[d['scenario'],d['layout'],d.get('containers_per_host',1)].append(d)
    manifest=[];attempts=[];samples=[];summary=[]
    def save(fig,name):
        fig.savefig(out/name,dpi=240,bbox_inches='tight');plt.close(fig);manifest.append(name)
    for (scenario,layout,count),ds in sorted(groups.items(),key=lambda kv:(int(kv[0][0].split('-')[-1]),kv[0][1])):
        ds=sorted(ds,key=lambda d:d['attempt']);last=ds[-1];before=ds[0]['before'];after=last.get('after',{})
        summary.append(dict(scenario=scenario,layout=layout,containers_per_host=count,status=last['status'],
            attempts=sum(d['attempt']>0 for d in ds),before_prepared=before['preparations']-before['preparation_failures'],
            before_preparations=before['preparations'],before_completed=before['requests']-before['request_failures'],before_requests=before['requests'],
            after_prepared=after.get('preparations',0)-after.get('preparation_failures',0),after_preparations=after.get('preparations',0),
            after_completed=after.get('requests',0)-after.get('request_failures',0),after_requests=after.get('requests',0),
            total_minutes=sum(d.get('elapsed_seconds',0) for d in ds)/60,
            physical_hosts=len(set(last.get('placements_after',{}).values())) or '',cloud_services=Counter(last.get('placements_after',{}).values()).get('cloud','')))
        active=[d for d in ds if d.get('started_at')]
        if not active:continue
        origin=stamp(active[0]['started_at']);local=[]
        for d in active:
            folder=root/f"{scenario}-{layout}-{count}-{d['attempt']}";start=stamp(d['started_at']);end=stamp(d.get('finished_at'))
            setup=d.get('deployment_seconds');warm=None;measured=None;remainder=None
            wm=folder/'warmup/distributed-reasoning-scalability/metadata.json'
            mm=folder/'measured/distributed-reasoning-scalability/metadata.json'
            we=stamp(json.loads(wm.read_text()).get('generated_at')) if wm.exists() else None
            me=stamp(json.loads(mm.read_text()).get('generated_at')) if mm.exists() else None
            if setup is not None and we is not None:
                warm=max(0,we-start-setup)
                if me is not None:measured=max(0,me-we);remainder=max(0,end-me) if end else None
            a=d.get('after',{});decision=d.get('decision',{})
            item=dict(scenario=scenario,layout=layout,containers_per_host=count,attempt=d['attempt'],status=d['status'],
                start_utc=d['started_at'],end_utc=d.get('finished_at',''),source=decision.get('source',''),destination=decision.get('destination',''),
                trigger=decision.get('cause',decision.get('reason','')),trigger_strata=json.dumps(decision.get('trigger_strata',[])),
                setup_seconds=setup,warmup_interval_seconds=warm,measured_interval_seconds=measured,cleanup_interval_seconds=remainder,
                total_seconds=d.get('elapsed_seconds'),completed=a.get('requests',0)-a.get('request_failures',0),requests=a.get('requests',0),
                prepared=a.get('preparations',0)-a.get('preparation_failures',0),preparations=a.get('preparations',0),
                placements=json.dumps(d.get('placements_after',{})),error=d.get('error',''))
            attempts.append(item);local.append(item)
            tf=folder/'service-samples.jsonl'
            if tf.exists():
                for line in tf.open():
                    s=json.loads(line);rr=objects(s.get('resources',''))
                    cpu=[float(r['CPUPerc'].strip('%')) for r in rr if re.fullmatch(r'[\d.]+%',r.get('CPUPerc',''))]
                    ram=[memory(r.get('MemUsage','')) for r in rr];ram=[v for v in ram if np.isfinite(v)]
                    samples.append(dict(scenario=scenario,layout=layout,containers_per_host=count,attempt=d['attempt'],host=s['host'],
                        time_utc=s['time'],minutes=(stamp(s['time'])-origin)/60,cpu_percent=sum(cpu) if cpu else float('nan'),
                        memory_mib=sum(ram) if ram else float('nan'),containers=len(rr),error=s.get('error','')))
        fig,axes=plt.subplots(3,1,figsize=(10,9),layout='constrained')
        xs=np.arange(len(local));labels=[f"A{r['attempt']}\n{r['source']} → {r['destination']}" for r in local]
        for offset,num,den,label,color in [(-.18,'prepared','preparations','Preparation','#009E73'),(.18,'completed','requests','Catalog requests','#0072B2')]:
            for i,r in enumerate(local):
                value=100*r[num]/r[den] if r[den] else np.nan
                axes[0].bar(i+offset,value,width=.34,color=color,label=label if i==0 else None)
                axes[0].text(i+offset,(value if np.isfinite(value) else 0)+3,f"{r[num]}/{r[den]}" if r[den] else 'NA',ha='center',fontsize=8)
        axes[0].set(xlim=(-.6,len(local)-.4),ylim=(0,125),ylabel='Completed (%)',xticks=xs,xticklabels=labels);axes[0].legend(loc='upper right',fontsize=8)
        bottom=np.zeros(len(local))
        for key,label,color in [('setup_seconds','Setup (recorded)','#999999'),('warmup_interval_seconds','Warm-up interval*','#E69F00'),('measured_interval_seconds','Measured interval*','#0072B2'),('cleanup_interval_seconds','Post-report / cleanup*','#009E73')]:
            values=np.array([(r[key] or 0)/60 for r in local]);axes[1].bar(xs,values,bottom=bottom,color=color,label=label);bottom+=values
        for i,r in enumerate(local):
            if r['setup_seconds'] is None:axes[1].bar(i,r['total_seconds']/60,color='#CC79A7',hatch='//');axes[1].text(i,r['total_seconds']/60,'Failed setup',ha='center',fontsize=8)
        axes[1].set(ylabel='Minutes',xticks=xs,xticklabels=[f'A{r["attempt"]}' for r in local]);axes[1].legend(ncol=2,fontsize=8)
        own=[s for s in samples if (s['scenario'],s['layout'],s['containers_per_host'])==(scenario,layout,count)]
        for host in sorted({s['host'] for s in own}):
            peaks=[max((s['memory_mib'] for s in own if s['host']==host and s['attempt']==r['attempt'] and np.isfinite(s['memory_mib'])),default=np.nan) for r in local]
            axes[2].plot(xs,peaks,'o-',label=host)
        axes[2].set(ylabel='Sampled peak Docker RAM (MiB)',xticks=xs,xticklabels=[f'A{r["attempt"]}' for r in local]);
        if own: axes[2].legend(ncol=3,fontsize=8)
        else:
            axes[2].text(.5,.5,'No resource samples: deployment did not become ready',transform=axes[2].transAxes,ha='center')
            axes[2].set_yticks([])
        for ax in axes:ax.grid(axis='y',alpha=.2)
        fig.suptitle(f'{scenario} / {layout} / placement {count}: adaptation trajectory\n*Intervals reconstructed from report timestamps; include reporting/waits. NA is not success.',fontsize=10)
        save(fig,f'{scenario}-{layout}-{count}-trajectory.png')
        if own:
            fig,axes=plt.subplots(2,1,figsize=(12,6),sharex=True,layout='constrained')
            for host in sorted({s['host'] for s in own}):
                ss=[s for s in own if s['host']==host]
                # Separate attempts to avoid interpolating across stopped containers.
                for attempt in sorted({s['attempt'] for s in ss}):
                    segment=sorted([s for s in ss if s['attempt']==attempt],key=lambda s:s['minutes'])
                    for ax,key in zip(axes,['cpu_percent','memory_mib']):ax.plot([s['minutes'] for s in segment],[s[key] for s in segment],label=host if attempt==min(s['attempt'] for s in ss) else None,linewidth=.8,color=f'C{sorted({s["host"] for s in own}).index(host)}')
            for i,d in enumerate(active):
                x=(stamp(d['started_at'])-origin)/60
                for ax in axes:ax.axvline(x,color='black',alpha=.3,linestyle='--')
                axes[0].text(x,1.01,f'A{d["attempt"]}',transform=axes[0].get_xaxis_transform(),fontsize=8)
            axes[0].set(ylabel='Sum of container CPU (%)');axes[0].legend(ncol=6,fontsize=8,loc='upper right')
            axes[1].set(ylabel='Docker RAM (MiB)',xlabel='Minutes since first adaptation decision')
            fig.suptitle(f'{scenario} / {layout}: observed infrastructure response\nDashed lines: attempt starts; 100% CPU = one core. Gaps are not zero usage.',fontsize=10)
            save(fig,f'{scenario}-{layout}-{count}-resources.png')
    if attempts:
        hosts=sorted({h for r in attempts for h in json.loads(r['placements']).values()})
        matrix=np.array([[Counter(json.loads(r['placements']).values()).get(h,0) for h in hosts] for r in attempts])
        fig,ax=plt.subplots(figsize=(9,max(6,len(attempts)*.24)),layout='constrained')
        im=ax.imshow(matrix,aspect='auto',vmin=0,vmax=max(6,matrix.max()),cmap='Blues')
        for i in range(len(attempts)):
            for j in range(len(hosts)):ax.text(j,i,str(matrix[i,j]),ha='center',va='center',fontsize=7,color='white' if matrix[i,j]>3 else 'black')
        ax.set(xticks=range(len(hosts)),xticklabels=hosts,yticks=range(len(attempts)),yticklabels=[f"{r['scenario']} / {r['layout']} / A{r['attempt']}" for r in attempts],title='Planned container placement per attempt (not an uptime measurement)')
        ax.tick_params(axis='y',labelsize=7);fig.colorbar(im,ax=ax,label='Logical services assigned');save(fig,'placement-evolution.png')
        trigger_rows=[]
        for key,ds in sorted(groups.items()):
            first=ds[0];obs=first['before']
            for g in obs.get('query_strata',[]):trigger_rows.append(dict(scenario=key[0],layout=key[1],reasoner=g['reasoner'],concurrency=g['concurrency'],requests=g['requests'],failures=g['request_failures'],failure_fraction=g['failure_fraction']))
        write(out/'baseline-trigger-strata.csv',trigger_rows)
        labels=sorted({(r['scenario'],r['layout'],r['reasoner']) for r in trigger_rows},key=lambda k:(int(k[0].split('-')[-1]),k[1],k[2]))
        cs=sorted({r['concurrency'] for r in trigger_rows})
        if labels and cs:
            matrix=np.full((len(labels),len(cs)),np.nan)
            for r in trigger_rows:matrix[labels.index((r['scenario'],r['layout'],r['reasoner'])),cs.index(r['concurrency'])]=100*r['failure_fraction']
            fig,ax=plt.subplots(figsize=(9,max(5,len(labels)*.42)),layout='constrained');cmap=plt.get_cmap('YlOrRd').copy();cmap.set_bad('#eeeeee')
            im=ax.imshow(matrix,aspect='auto',vmin=0,vmax=100,cmap=cmap)
            for i in range(len(labels)):
                for j in range(len(cs)):
                    value=matrix[i,j];ax.text(j,i,'NA' if np.isnan(value) else f'{value:.1f}%',ha='center',va='center',color='white' if value>60 else 'black')
            ax.set(xticks=range(len(cs)),xticklabels=cs,yticks=range(len(labels)),yticklabels=[' / '.join(k) for k in labels],xlabel='Concurrent catalog requests',title='Baseline request failures that can trigger adaptation\nArchived threshold: any failure. Preparation failures are separate; see outcome table.')
            fig.colorbar(im,ax=ax,label='Failed requests (%)');save(fig,'baseline-triggers.png')
    write(out/'scenario-outcomes.csv',summary);write(out/'attempt-phases.csv',attempts);write(out/'resource-samples.csv',samples)
    if attempts:
        fig,ax=plt.subplots(figsize=(13,max(5,len(attempts)*.22)),layout='constrained')
        origin=min(stamp(r['start_utc']) for r in attempts)
        for i,r in enumerate(attempts):
            ax.barh(i,r['total_seconds']/3600,left=(stamp(r['start_utc'])-origin)/3600,color='#009E73' if r['status']=='execution_recovered' else '#D55E00')
        ax.set(yticks=range(len(attempts)),yticklabels=[f"{r['scenario']} / {r['layout']} / A{r['attempt']}" for r in attempts],xlabel='Hours since first adaptation decision',title='Actual adaptation schedule: green = recovered; orange = unresolved / failed');ax.tick_params(axis='y',labelsize=7);ax.grid(axis='x',alpha=.2)
        save(fig,'campaign-timeline.png')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'{len(manifest)} figures; {len(attempts)} attempts; {len(samples)} resource samples')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('campaign',type=Path);args=parser.parse_args();report(args.campaign)
