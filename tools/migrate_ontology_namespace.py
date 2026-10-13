#!/usr/bin/env python3
"""Copy an external RDF graph into the monitoringcontinuum namespace.

This renames RDF identifiers only. It does not upgrade axioms or certify a
version-3 graph as version 4. Load the maintained version-4 schema and validate
imported instance data before using it in an experiment.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from rdflib import Graph, URIRef

OLD = 'http://example.org/smartcity'
NEW = 'http://example.org/monitoringcontinuum'


def migrate(source: Path, destination: Path) -> int:
    graph = Graph().parse(source)
    output = Graph(bind_namespaces='none')
    output.bind('mc', URIRef(NEW + '#'))
    changed = set()
    def rename(term):
        if isinstance(term, URIRef) and (str(term) == OLD or str(term).startswith((OLD + '#', OLD + '/'))):
            changed.add(term)
            return URIRef(NEW + str(term)[len(OLD):])
        return term
    for triple in graph:
        output.add(tuple(rename(term) for term in triple))
    # Exclusive creation preserves both source and any pre-existing destination.
    with destination.open('x', encoding='utf-8') as handle:
        handle.write(output.serialize(format='turtle'))
    return len(changed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    count = migrate(args.source, args.destination)
    print(f'Renamed {count} distinct RDF identifiers; schema upgrade and validation are still required.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
