"""Evidence that original authorities and extra copies both execute work."""
from collections import defaultdict
import json

import matplotlib.pyplot as plt
import numpy as np

from .comparison import read_csv,write_csv,save_figure


def report_pools(directory,decisions):
    figures=directory/'figures';manifest_path=figures/'manifest.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    table=[]
    for decision in decisions:
        if not decision.get('replica_owners') or not decision.get('results'):continue
        result=directory/decision['results'];raw=read_csv(result/'replica-routing.csv')
        if not raw:continue
        for layout in sorted({r['layout'] for r in raw}):
            groups=defaultdict(lambda:dict(completed=0,failed=0,cpu_ms=0.0))
            for r in raw:
                if r['layout']!=layout:continue
                origin=r['is_origin'].lower()=='true';item=groups[r['logical_owner'],origin]
                item['completed' if r['status']=='completed' else 'failed']+=1
                item['cpu_ms']+=float(r['process_cpu_ms'] or 0)
            owners=sorted({owner for owner,_ in groups} | (set(decision.get('placements_after', {})) - set(decision['replica_owners'])));xs=np.arange(len(owners))
            fig,axes=plt.subplots(1,3,figsize=(14,4),layout='constrained')
            for ax,field,label,scale in zip(axes,('completed','failed','cpu_ms'),('Completed worker requests','Failed worker requests','Measured successful-request CPU (s)'),(1,1,.001)):
                bottom=np.zeros(len(owners))
                for origin,color,name in [(True,'#009E73','Original host'),(False,'#0072B2','Additional copies')]:
                    values=np.array([groups[o,origin][field]*scale for o in owners]);ax.bar(xs,values,bottom=bottom,label=name,color=color);bottom+=values
                ax.set(ylabel=label,xticks=xs,xticklabels=owners,ylim=(0,max(1,float(bottom.max())*1.15)));ax.tick_params(axis='x',rotation=30);ax.grid(axis='y',alpha=.2)
                if not bottom.any():
                    empty_label = {'failed': 'No failed worker requests', 'completed': 'No completed worker requests', 'cpu_ms': 'Successful-request CPU unavailable'}[field]
                    ax.text(.5,.5,empty_label,ha='center',va='center',transform=ax.transAxes,color='#555555')
            axes[0].legend(fontsize=8)
            fig.suptitle(f"{decision['scenario']} / {layout} / attempt {decision['attempt']}: retained-origin work\nOne copy per authority per request; failed-request CPU is unavailable, not zero.",fontsize=10)
            name=f"{result.parent.parent.name}-{layout}-origin-work.png";save_figure(fig,figures,name,manifest)
            for (owner,origin),values in sorted(groups.items()):
                table.append(dict(scenario=decision['scenario'],trigger_layout=decision['layout'],measured_layout=layout,
                    attempt=decision['attempt'],owner=owner,is_origin=origin,**values))
    write_csv(directory/'analysis/replica-workshare.csv',table)
    manifest_path.write_text(json.dumps(list(dict.fromkeys(manifest)),indent=2)+'\n')
