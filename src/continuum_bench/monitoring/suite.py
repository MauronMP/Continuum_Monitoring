"""Sequential, recorded execution of every physical acceptance family."""
from datetime import datetime, timezone
import json
import csv
from pathlib import Path
import subprocess
import sys
import uuid


def suite_plan(root, config, destination, *, patient=False, unlimited=False, timeout_seconds=None, repetitions=None, families=None):
    budget=timeout_seconds or (3600 if patient else None)
    prefix=[sys.executable,'-m','continuum_bench','--config',str(config)]
    if budget:prefix+=['--timeout-seconds',str(budget)]
    if unlimited:prefix+=['--unlimited']
    if patient or unlimited:prefix+=['--keep-going']
    if repetitions:prefix+=['--repetitions',str(repetitions)]
    families=families or ['software','validation','monitoring','load','experiments','campaign','report']
    steps=[]
    def add(name,args):steps.append({'name':name,'command':prefix+args})
    if 'software' in families:steps.append({'name':'software','command':[sys.executable,'-m','pytest','-q']})
    if 'validation' in families:
        add('validate',['validate']);add('preflight',['preflight']);add('owl-validation',['owl-validate','--require-all'])
    if set(families) & {'monitoring','load','experiments','campaign'}:
        add('start-workers',['physical','start'])
    if 'monitoring' in families:
        for layout in ('sharded','replicated'):add('monitoring-'+layout,['physical','all','--layout',layout,'--output-dir',str(destination/'physical')])
    if 'load' in families:add('load',['load','physical','--output-dir',str(destination/'load')])
    if 'experiments' in families:add('experiments',['experiment','all','physical','--output-dir',str(destination/'experiments')])
    if 'campaign' in families:add('campaign',['campaign','--campaign-config','configs/campaign.toml','--output-dir',str(destination/'campaigns')])
    if 'report' in families:add('report',['report','--input-dir',str(destination),'--output-dir',str(destination/'paper')])
    return steps


def run_suite(root,config,output,**options):
    dry_run=options.pop('dry_run',False)
    directory=output/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    directory.mkdir(parents=True)
    plan=suite_plan(root,config,directory,**options)
    manifest={'options':options,'steps':plan,'output':str(directory),'dry_run':dry_run}
    path=directory/'suite.json'
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    if dry_run:return manifest
    from .provenance import snapshot
    manifest["provenance"]=snapshot(root,directory)
    path.write_text(json.dumps(manifest,indent=2)+"\n")
    for step in plan:
        print(f"[suite] {step['name']} starting; evidence={directory}",flush=True)
        step['started_at']=datetime.now(timezone.utc).isoformat()
        with (directory/(step['name']+'.log')).open('w') as log:
            result=subprocess.run(step['command'],cwd=root,stdout=log,stderr=subprocess.STDOUT,check=False)
        step['returncode']=result.returncode
        step['finished_at']=datetime.now(timezone.utc).isoformat()
        roots={'monitoring-sharded':directory/'physical/sharded','monitoring-replicated':directory/'physical/replicated',
               'load':directory/'load/physical','experiments':directory/'experiments/physical'}
        if step['name'] in roots:
            records=[]
            for summary in roots[step['name']].rglob('summary.csv'):
                with summary.open(newline='') as handle: records.extend(csv.DictReader(handle))
            step['recorded_points']=len(records)
            step['incomplete_points']=sum(r.get('status')!='completed' for r in records)
            if not records or step['incomplete_points']: step['returncode']=1
        step['status']='completed' if step['returncode']==0 else 'failed' 
        path.write_text(json.dumps(manifest,indent=2)+'\n')
        print(f"[suite] {step['name']} {step['status']}; log={step['name']}.log",flush=True)
    return manifest
