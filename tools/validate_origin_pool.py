#!/usr/bin/env python3
"""Bounded physical validation: retain six origins and add one Edge-2 copy on Fog."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime,timezone
import json
from pathlib import Path
import uuid
import argparse

from continuum_bench.config import load_config
from continuum_bench.monitoring.lease import physical_lease
from continuum_bench.monitoring.container_scale.config import load,logical_topology
from continuum_bench.monitoring.container_scale import deployment
from continuum_bench.monitoring.container_scale.runner import workload,read_rows
from continuum_bench.monitoring.adaptive_monitoring.actuator import RecoveryDeployment
from continuum_bench.monitoring.adaptive_monitoring.pools import expanded_topology
from continuum_bench.monitoring.adaptive_monitoring.telemetry import Sampler
from continuum_bench.monitoring.distributed_reasoning_scalability import run_distributed_reasoning_scalability


def main():
    root=Path(__file__).resolve().parents[1]
    config=load(root/'configs/container-scale.toml',root);benchmark=load_config(root/'configs/benchmark.toml')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exclude-host", action="append", default=[], help="Explicitly exclude an unavailable host from this mechanism check")
    args=parser.parse_args()
    original=logical_topology(config,max(config.deployment["containers_per_host"]))
    if set(args.exclude_host)-{n.node_id for n in config.topology.active_nodes}:
        parser.error("Unknown excluded host")
    if {"edge2", "fog"} & set(args.exclude_host):
        parser.error("Edge 2 and Fog are required for this validation")
    config=replace(config,topology=replace(config.topology,nodes=tuple(n for n in config.topology.nodes if n.node_id not in args.exclude_host)))
    raw=deepcopy(config.raw);raw['experiment'].update(repetitions=1,warmup=0,semantic_validation=True,layouts=['distributed','replicated'])
    config=replace(config,raw=raw)
    scenario=dict(name='origin-pool-validation',family='users',users=1,target_triples=0,query_rounds=1,concurrency=[1,2,4])
    token=uuid.uuid4().hex[:12]
    output=root/'outputs/validation'/('origin-pool-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    output.mkdir(parents=True)
    replicas=[dict(id='edge2-c1-r1',owner='edge2-c1',host='fog')];owners={r['id']:r['owner'] for r in replicas}
    topology=expanded_topology(config,1,replicas,8591)
    actuator=RecoveryDeployment(config,root,topology,output/'deployment',token,replica_owners=owners)
    def snapshot():
        values={}
        for host in config.topology.active_nodes:
            identity=host.node_id+'-c1';container=deployment.compose(config,root,host,'ps','-q',identity).strip()
            if not container:raise RuntimeError(f'Origin {identity} is not running')
            state=json.loads(deployment.execute(config,host,['docker','inspect','--format','{{json .State}}',container]))
            values[identity]=dict(id=container,pid=state['Pid'],started_at=state['StartedAt'])
        return values
    with physical_lease(root):
        print("[origin-pool-validation] Checking selected original workers", flush=True)
        deployment.wait_ready(config,original)
        if not all(p['ready'] for p in deployment.doctor(config,2,host_ids=['fog'])):raise RuntimeError('Fog capacity validation failed')
        before=snapshot();(output/'origins-before.json').write_text(json.dumps(before,indent=2))
        try:
            print("[origin-pool-validation] Adding Edge 2 replica on Fog", flush=True)
            actuator.start()
            print("[origin-pool-validation] Measuring both layouts at concurrency 1, 2 and 4", flush=True)
            with Sampler(actuator,output/'service-samples.jsonl',10):
                result=run_distributed_reasoning_scalability(benchmark,workload(config,scenario,len(config.topology.active_nodes)),'physical',output/'measured',
                    topology.endpoints(),topology,query_each_repetition=True,replica_owners=owners,origin_topology=original)
            routing=read_rows(result/'replica-routing.csv')
            selected=[r for r in routing if r['layout']=='distributed' and r['logical_owner']=='edge2-c1' and r['status']=='completed']
            counts={worker:sum(r['worker']==worker for r in selected) for worker in ['edge2-c1','edge2-c1-r1']}
            assert all(counts.values()),counts
            assert all(float(r['process_cpu_ms'])>0 for r in selected)
            summaries=read_rows(result/'distributed-reasoning-summary.csv')
            assert len(summaries)==2 and all(r['status']=='completed' for r in summaries),summaries
            queries=read_rows(result/'query-scalability.csv')
            assert queries and all(int(r['error_count'])==0 for r in queries),queries
            semantics=read_rows(result/'semantic-validation.csv')
            assert semantics and all(r['status']=='equivalent' for r in semantics),semantics
            expected_origins={n.node_id+'-c1' for n in config.topology.active_nodes}
            working_origins={r['worker'] for r in routing if r['layout']=='distributed' and r['status']=='completed' and float(r.get('process_cpu_ms') or 0)>0}
            assert expected_origins <= working_origins, (expected_origins-working_origins)
        finally:
            print("[origin-pool-validation] Removing extra replica and checking original processes", flush=True)
            errors=actuator.close();(output/'cleanup.json').write_text(json.dumps(errors))
            after=snapshot();(output/'origins-after.json').write_text(json.dumps(after,indent=2))
            if errors:raise RuntimeError(f'Extra-container cleanup failed: {errors}')
            assert before==after,'An origin container was restarted or replaced'
        samples=[json.loads(line) for line in (output/'service-samples.jsonl').read_text().splitlines() if line.strip()]
        observed_hosts={r['host'] for r in samples if not r.get('error') and r.get('resources')}
        assert {n.node_id for n in config.topology.active_nodes} <= observed_hosts, observed_hosts
        (output/'validation.json').write_text(json.dumps(dict(status='passed',originals_unchanged=True,origin_count=len(config.topology.active_nodes), excluded_hosts=args.exclude_host,
            extra_copies=1,destination='fog',successful_distributed_requests=counts,
            semantic_comparisons=len(semantics),working_origins=sorted(expected_origins),telemetry_hosts=sorted(observed_hosts),
            scope='One-user mechanism validation, not a scalability result'),indent=2))
    from continuum_bench.monitoring.adaptive_monitoring.pool_reporting import report_pools
    (output/'figures').mkdir(exist_ok=True)
    (output/'analysis').mkdir(exist_ok=True)
    report_pools(output,[dict(scenario=f'Mechanism validation (1 user, {len(config.topology.active_nodes)} origins)',
        layout='distributed',attempt=1,replica_owners=owners,results=str(result.relative_to(output)))])
    print('Validation:',output)

if __name__=='__main__':main()
