#!/usr/bin/env python3
"""Check local ontology import closure, ownership and deployment profiles."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tomllib

from rdflib import Graph, OWL, RDF, RDFS, URIRef

ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = 'http://example.org/monitoringcontinuum#'


def audit(root: Path = ROOT) -> dict:
    graphs = {p.relative_to(root).as_posix(): Graph().parse(p)
              for p in (root / 'ontology').rglob('*.ttl')}
    owners: dict[URIRef, set[str]] = {}
    identifiers = {}
    errors = []
    for path, graph in graphs.items():
        for subject in graph.subjects(RDF.type, OWL.Ontology):
            if subject in identifiers:
                errors.append(f'Duplicate ontology identifier: {subject}')
            identifiers[subject] = path
        for kind in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty):
            for subject in graph.subjects(RDF.type, kind):
                if str(subject).startswith(NAMESPACE):
                    owners.setdefault(subject, set()).add(path)
                    for annotation in (RDFS.label, RDFS.comment):
                        if not any(graph.objects(subject, annotation)):
                            errors.append(f'{path}: {subject} lacks {annotation}')
    for subject, paths in owners.items():
        if len(paths) != 1:
            errors.append(f'Duplicate term ownership: {subject}: {sorted(paths)}')

    def closure(path: str, stack: tuple[str, ...] = ()) -> set[str]:
        if path in stack:
            errors.append('Cyclic imports: ' + ' -> '.join((*stack, path)))
            return set()
        result = {path}
        for imported in graphs[path].objects(None, OWL.imports):
            if imported not in identifiers:
                errors.append(f'{path}: unresolved import {imported}')
            else:
                result |= closure(identifiers[imported], (*stack, path))
        return result

    closures = {path: closure(path) for path in graphs}
    for path, graph in graphs.items():
        if '/examples/' in path:
            continue  # Example instances are loaded with the application manifest.
        for term in {term for triple in graph for term in triple}:
            if term in owners and not (owners[term] & closures[path]):
                errors.append(f'{path}: undeclared dependency for {term}: {sorted(owners[term])}')
        for expression in graph.subjects(OWL.unionOf, None):
            if not any(graph.subject_predicates(expression)):
                errors.append(f'{path}: orphan union {expression}')
    core = closures['ontology/core/schema.ttl']
    if any('/wellbeing/' in path or path.endswith('/federation.ttl') for path in core):
        errors.append('Core imports an optional application module')
    placement = tomllib.loads((root / 'configs/ontology-placement.toml').read_text())
    for role, entry in placement['roles'].items():
        profile = entry['profile']
        expected = closures[profile] - {profile}
        if set(entry['files']) != expected:
            errors.append(f'{role}: placement differs from profile imports: {sorted(set(entry["files"]) ^ expected)}')
        if not any(graphs[profile].subjects(RDF.type, URIRef(NAMESPACE + 'SemanticNodeProfile'))):
            errors.append(f'{role}: missing SemanticNodeProfile type')
    return {'ok': not errors, 'errors': sorted(set(errors)),
            'owned_terms': len(owners), 'core_closure': sorted(core),
            'profile_closures': {p: sorted(c - {p}) for p,c in closures.items() if '/profiles/' in p}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/audit/ontology-modules.json')
    args = parser.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return int(not result['ok'])


if __name__ == '__main__':
    raise SystemExit(main())
