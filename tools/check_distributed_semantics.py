#!/usr/bin/env python3
"""Compare local fragment closure/query merge with a canonical native reference.

This is a semantic diagnostic on the coordinator, not a physical benchmark.
Result differences remain failures; no inference or privacy gate is bypassed.
"""
from dataclasses import asdict
from collections import Counter
from pathlib import Path
import argparse
import json
import math
from continuum_bench.config import load_config
from continuum_bench.topology import load_topology
from continuum_bench.partitioning import build_fragments
from continuum_bench.monitoring.distributed import Endpoint
from continuum_bench.monitoring.distributed_ontology import _full_source, _sources, _merge_responses, _validation_rows
from continuum_bench.reasoners import materialize
from continuum_bench.queries import load_catalog, execute_query_detailed, result_digest
from continuum_bench.specification import release_identity

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--users',type=int,default=100)
    parser.add_argument('--reasoner',choices=['rdfs','hermit','openllet','jfact','konclude'],default='konclude')
    parser.add_argument('--topology-file',type=Path,default=ROOT/'configs/topologies/physical/topology.toml')
    parser.add_argument('--timeout-seconds',type=float,default=120)
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/audit/distributed-semantics.json')
    args=parser.parse_args()
    if args.users<0 or not math.isfinite(args.timeout_seconds) or args.timeout_seconds<=0:
        parser.error('users must be nonnegative and timeout must be positive')
    from continuum_bench.monitoring.budget import local_phase_timeout
    config=load_config(ROOT/'configs/benchmark.toml')
    topology=load_topology(args.topology_file,'physical')
    endpoints=[Endpoint(n.endpoint,n.node_id,n.tier,n.authority,n.categories) for n in topology.active_nodes]
    fragments=build_fragments(config,args.users,config.seed,topology=topology)
    specs=load_catalog(config.resolve(config.query_catalog),config.root)
    with local_phase_timeout(args.timeout_seconds):
        canonical=materialize(_full_source(config,args.users),args.reasoner).graph
    graphs={}
    for role,graph in fragments.graphs.items():
        with local_phase_timeout(args.timeout_seconds):
            graphs[role]=materialize(graph,args.reasoner).graph
        print(f'[semantic-check] node={role} status=materialized',flush=True)
    responses={e.url:{'measurements':[]} for e in endpoints}
    baseline={}
    expected_keys={}
    with local_phase_timeout(args.timeout_seconds):
        for spec in specs:
            result=execute_query_detailed(canonical,spec)
            expected_keys[spec.id]=Counter(result.result_keys)
            baseline[spec.id]=(result.measurement.result_count,result.measurement.ask_result,
                               result_digest(result.result_keys,result.measurement.ask_result))
            for endpoint in _sources(spec,endpoints):
                result=execute_query_detailed(graphs[endpoint.role],spec)
                responses[endpoint.url]['measurements'].append({**asdict(result.measurement),'result_keys':result.result_keys})
    merged,_=_merge_responses(specs,endpoints,responses,{'reasoner':args.reasoner,'synthetic_users':args.users})
    rows=_validation_rows(merged,baseline)
    for spec, row in zip(specs, rows):
        if not row['valid']:
            actual=Counter()
            for endpoint in _sources(spec,endpoints):
                part=next(m for m in responses[endpoint.url]['measurements'] if m['query_id']==spec.id)
                actual |= Counter(part['result_keys'])
            row['missing_bindings']=list((expected_keys[spec.id]-actual).elements())[:30]
            row['extra_bindings']=list((actual-expected_keys[spec.id]).elements())[:30]
    report={**release_identity(),'execution':'local-semantic-diagnostic-not-physical-measurement',
            'topology':topology.public(),'users':args.users,'reasoner':args.reasoner,
            'all_matched':all(r['valid'] for r in rows),'queries':rows}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(f"[semantic-check] matched={sum(r['valid'] for r in rows)}/{len(rows)} output={args.output}")
    return int(not report['all_matched'])

if __name__=='__main__':
    raise SystemExit(main())
