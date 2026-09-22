"""Sequential, recorded execution of every physical acceptance family."""
from datetime import datetime, timezone
import json
import os
import csv
from pathlib import Path
import subprocess
import sys
import uuid
from collections import Counter
from .report_profiles import outcome


def suite_plan(root, config, destination, *, patient=False, unlimited=False,
               timeout_seconds=None, repetitions=None, families=None,
               timeout_mode=None, request_timeout_seconds=None,
               phase_timeout_seconds=None, point_timeout_seconds=None,
               skip_after_timeouts=None, skip_repetitions=None,
               skip_larger_points=None, skip_cumulative_stages=None,
               keep_going=False, topology_file=None,
               load_config='configs/load-benchmark.toml',
               experiment_config='configs/experiments.toml',
               campaign_config='configs/campaign.toml'):
    budget=timeout_seconds if timeout_seconds is not None else (3600 if patient else None)
    prefix=[sys.executable,'-m','continuum_bench','--config',str(config)]
    if topology_file is not None:prefix+=['--topology-file',str(topology_file)]
    if budget is not None:prefix+=['--timeout-seconds',str(budget)]
    if unlimited:prefix+=['--unlimited']
    if patient or unlimited or keep_going:prefix+=['--keep-going']
    if repetitions is not None:prefix+=['--repetitions',str(repetitions)]
    for name, value in (
        ('timeout-mode', timeout_mode),
        ('request-timeout-seconds', request_timeout_seconds),
        ('phase-timeout-seconds', phase_timeout_seconds),
        ('point-timeout-seconds', point_timeout_seconds),
        ('skip-after-timeouts', skip_after_timeouts),
    ):
        if value is not None:
            prefix += ['--'+name, str(value)]
    for name, value in (
        ('skip-repetitions', skip_repetitions),
        ('skip-larger-points', skip_larger_points),
        ('skip-cumulative-stages', skip_cumulative_stages),
    ):
        if value is not None:
            prefix.append('--'+('' if value else 'no-')+name)
    families=families or ['software','validation','monitoring','load','experiments','campaign','report']
    steps=[]
    def add(name,args):steps.append({'name':name,'command':prefix+args})
    if 'software' in families:
        steps.append({'name':'software','command':[sys.executable,'-m','pytest','-o','addopts=','-q','-ra',
                      '--junitxml='+str(destination/'software-tests.xml')],
                      'environment':{'CONTINUUM_TEST_NATIVE_OWL':'1'}})
        steps.append({'name':'documentation','command':[sys.executable,str(root/'tools/check_documentation.py')]})
    if 'validation' in families:
        add('validate',['validate']);add('preflight',['preflight','--load-config',str(load_config),'--experiment-config',str(experiment_config)]);add('owl-validation',['owl-validate','--require-all','--output',str(destination/'validation/owl-reasoners.json')])
    if 'campaign' in families:
        add('campaign-preflight',['campaign','--campaign-config',str(campaign_config),'--validate-only'])
    if set(families) & {'monitoring','load','experiments','campaign'}:
        add('start-workers',['physical','start'])
    if 'monitoring' in families:
        for layout in ('distributed','replicated'):add('monitoring-'+layout,['physical','all','--layout',layout,'--output-dir',str(destination/'monitoring')])
    if 'load' in families:add('load',['load','physical','--load-config',str(load_config),'--output-dir',str(destination/'load')])
    if 'experiments' in families:add('experiments',['experiment','all','physical','--experiment-config',str(experiment_config),'--output-dir',str(destination/'experiments')])
    if 'campaign' in families:add('campaign',['campaign','--campaign-config',str(campaign_config),'--output-dir',str(destination/'campaign')])
    if 'report' in families:add('report',['report','--input-dir',str(destination),'--output-dir',str(destination/'report')])
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
            environment = {**os.environ, **step.get('environment', {})}
            result=subprocess.run(step['command'],cwd=root,env=environment,stdout=log,stderr=subprocess.STDOUT,check=False)
        step['returncode']=result.returncode
        step['finished_at']=datetime.now(timezone.utc).isoformat()
        roots={'monitoring-distributed':directory/'monitoring/distributed','monitoring-replicated':directory/'monitoring/replicated',
               'load':directory/'load','experiments':directory/'experiments'}
        step['status']='completed' if result.returncode==0 else 'failed'
        if step['name'] in roots:
            records=[]
            for summary in roots[step['name']].rglob('summary.csv'):
                with summary.open(newline='') as handle: records.extend(csv.DictReader(handle))
            step['recorded_points']=len(records)
            step['incomplete_points']=sum(r.get('status')!='completed' for r in records)
            counts=Counter(outcome(row) for row in records)
            step['outcomes']={status:counts[status] for status in ('completed','timeout','skipped','failed')}
            if result.returncode != 0 or counts['failed']:
                step['status']='failed'
            elif not records:
                step['status']='missing_evidence'
            elif counts['timeout']:
                step['status']='timeout'
            elif counts['skipped']:
                step['status']='skipped'

        path.write_text(json.dumps(manifest,indent=2)+'\n')
        print(f"[suite] {step['name']} {step['status']}; log={step['name']}.log",flush=True)
    return manifest
