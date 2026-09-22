#!/usr/bin/env python3
"""Verify installed runtimes by real DL entailment and inconsistency checks."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from rdflib import Graph, Namespace
from rdflib.namespace import OWL, RDF, RDFS
from continuum_bench.owl_materialization import NativeOWLReasoner, InconsistentOntologyError


def main():
    ex = Namespace("urn:continuum:materialization-smoke:")
    graph = Graph().parse(data='''
@prefix : <urn:continuum:materialization-smoke:> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
:A a owl:Class; rdfs:subClassOf :B . :B a owl:Class .
:C a owl:Class; owl:equivalentClass [ a owl:Restriction; owl:onProperty :p; owl:someValuesFrom :B ] .
:p a owl:ObjectProperty . :a :p :b . :b a :A .
''', format="turtle")
    name = sys.argv[1]
    backend = NativeOWLReasoner(name, timeout=60)
    result = backend.materialize(graph)
    if (ex.a, RDF.type, ex.C) not in result.graph or not set(graph) <= set(result.graph):
        raise RuntimeError(f"{name}: missing DL entailment or lost source triples")
    graph.add((ex.A, OWL.disjointWith, ex.B))
    try:
        backend.materialize(graph)
    except InconsistentOntologyError:
        print(f"{name}: native inference and inconsistency verified")
        return 0
    raise RuntimeError(f"{name}: failed to detect inconsistency")


if __name__ == "__main__":
    raise SystemExit(main())
