#!/usr/bin/env python3
"""Offline semantic verification; no network and no physical performance claim."""
from pathlib import Path
import argparse,json,sys
from dataclasses import asdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from continuum_bench.config import load_config
from continuum_bench.partitioning import build_fragments, serialize_fragment, deserialize_fragment
from continuum_bench.reasoners import materialize
from continuum_bench.queries import load_catalog,execute_query_detailed
from continuum_bench.topology import load_topology
from continuum_bench.monitoring.distributed_ontology import _assignment,_merge_responses,_baseline_counts,_validation_rows

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='configs/smoke-scalability.toml')
    parser.add_argument('--users',type=int,default=1)
    parser.add_argument('--output',default='outputs/validation/readiness/distributed-reasoning.json')
    args=parser.parse_args();config=load_config(args.config)
    topology=load_topology(config.resolve(config.topology_file),'physical')
    from continuum_bench.monitoring.distributed import Endpoint
    endpoints=[Endpoint(n.endpoint,n.node_id,tier=n.tier,authority=n.authority,categories=n.categories) for n in topology.active_nodes]
    specs=load_catalog(config.resolve(config.query_catalog),config.root)
    assignment=_assignment(specs,endpoints)
    fragments=build_fragments(config,args.users,config.seed,topology=topology)
    report={'mode':'offline-semantic-check','remote_contacted':False,'users':args.users,'reasoners':[]}
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    for reasoner in config.reasoners:
        print(f'[offline] {reasoner} canonical and {len(endpoints)} local fragments',flush=True)
        baseline=_baseline_counts(config,specs,reasoner,args.users)
        responses={}
        for endpoint in endpoints:
            payload=serialize_fragment(fragments,endpoint.role,users=args.users,seed=config.seed)
            source,_=deserialize_fragment(payload,endpoint.role,users=args.users,seed=config.seed)
            graph=materialize(source,reasoner).graph
            measurements=[]
            for spec in assignment[endpoint.url]:
                execution=execute_query_detailed(graph,spec)
                measurements.append({**asdict(execution.measurement),'result_keys':execution.result_keys})
            responses[endpoint.url]={'measurements':measurements}
        merged,_=_merge_responses(specs,endpoints,responses,{'reasoner':reasoner})
        validation=_validation_rows(merged,baseline)
        invalid=[r for r in validation if not r['valid']]
        report['reasoners'].append({'reasoner':reasoner,'checks':len(validation),'mismatches':invalid})
        output.write_text(json.dumps(report,indent=2)+'\n')
        print(f'[offline] {reasoner} checks={len(validation)} mismatches={len(invalid)}',flush=True)
    return int(any(r['mismatches'] for r in report['reasoners']))
if __name__=='__main__':raise SystemExit(main())
