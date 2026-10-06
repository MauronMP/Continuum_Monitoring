#!/usr/bin/env python3
"""Inventory acceptance debt without manufacturing missing historical evidence."""
from pathlib import Path
import argparse
import json
import tomllib
from collections import Counter
from pyshacl import validate
from rdflib import Namespace, RDF
from continuum_bench.config import load_config
from continuum_bench.ontology import load_graph
from continuum_bench.queries import load_catalog
from continuum_bench.specification import validate_release_contract

ROOT = Path(__file__).resolve().parents[1]
SH = Namespace('http://www.w3.org/ns/shacl#')
ACTIONS = {
    'hasAHPScore': 'Recompute from recorded pairwise criteria and alternative inputs; historical source lacks these inputs.',
    'lastUpdated': 'Recover the actual model-version timestamp from the originating model registry; do not use audit time.',
    'trustWindowStart': 'Recover the historical measurement-window start from source telemetry.',
    'trustWindowEnd': 'Recover the historical measurement-window end from source telemetry.',
}
THRESHOLDS = {'T_migration_max','T_sparql_monitor','T_decision_max','E_device_max','N_agents','T_node_join','D_delegation_max','T_reselection_max','AHP_consistency_threshold'}

def review(config, dispositions):
    graph = load_graph(config.resolve(p) for p in config.ontology_files)
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    contract = validate_release_contract(graph, specs)
    gaps = set(contract['unreferenced_requirements'] + contract['unreferenced_policies'])
    errors = []
    if set(dispositions) != gaps:
        errors.append(f'Review mismatch: missing={sorted(gaps-set(dispositions))}, stale={sorted(set(dispositions)-gaps)}')
    for key, item in dispositions.items():
        if item.get('status') not in {'partial','deferred','software-check'} or not item.get('rationale'):
            errors.append(f'{key}: invalid review disposition')
        if not (config.root / item.get('evidence', '__missing__')).exists():
            errors.append(f'{key}: evidence path does not exist')
    shapes = load_graph(config.resolve(p) for p in config.shape_files)
    conforms, report, _ = validate(graph, shacl_graph=shapes, allow_warnings=True)
    findings = []
    for result in report.subjects(RDF.type, SH.ValidationResult):
        path = str(report.value(result, SH.resultPath))
        field = path.rsplit('#',1)[-1]
        action = ACTIONS.get(field)
        if field in THRESHOLDS:
            action = 'Define and justify a prospective campaign acceptance threshold before measuring; a timeout is not an acceptance threshold.'
        if not action:
            errors.append(f'Unreviewed SHACL finding: {path}')
        findings.append({'subject':str(report.value(result, SH.focusNode)), 'property':path,
                         'severity':str(report.value(result, SH.resultSeverity)),
                         'status':'blocked-on-source-evidence' if field in ACTIONS else 'requires-domain-decision',
                         'required_action': action})
    return {'review_complete':not errors,'scientific_acceptance_claimed':False,
            'interpretation':'Reviewed debt remains unresolved; dispositions are not waivers or compliance evidence.',
            'errors':errors,'shacl_conforms_allowing_warnings':conforms,
            'warning_count':len(findings),'counts_by_property':dict(Counter(x['property'] for x in findings)),
            'findings':sorted(findings,key=lambda x:(x['property'],x['subject'])),
            'query_coverage_review':dispositions}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/audit/validation-debt.json')
    args=parser.parse_args()
    config=load_config(ROOT/'configs/benchmark.toml')
    dispositions=tomllib.loads((ROOT/'configs/traceability-review.toml').read_text())['items']
    result=review(config,dispositions)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'findings','query_coverage_review'}},indent=2))
    return int(not result['review_complete'])

if __name__=='__main__':
    raise SystemExit(main())
