from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from time import perf_counter_ns
from typing import Type

from owlrl import (
    DeductiveClosure,
    OWLRL_Semantics,
    RDFS_OWLRL_Semantics,
    RDFS_Semantics,
)
from rdflib import Graph, Literal


REASONING_CONTRACT = "rdfs-literal-value-space-v1"


class DatatypeAwareRDFSSemantics(RDFS_Semantics):
    """Keep RDFS literal substitution inside RDF literal value spaces.

    OWL-RL's one-time RDFS rules compare ``Literal.value`` Python objects.
    Python equates True/1 and False/0 and ignores language tags on strings;
    those are not interchangeable RDF literals.  Use RDFLib's datatype- and
    language-aware value equality instead, retaining numeric equivalences.
    Override the public hook, not installed dependency files, so the same
    correction runs in the monolith, Docker engines and physical workers.
    """

    def one_time_rules(self) -> None:
        literals = {
            value for value in self.graph.objects()
            if isinstance(value, Literal)
        }
        for left, right in combinations(literals, 2):
            # Cheap rejection before the more expensive RDF value comparison.
            # Python equality is necessary here, never sufficient.
            if left.value != right.value:
                continue
            try:
                equal = left.eq(right) is True
            except (TypeError, ValueError):
                equal = False
            if not equal:
                continue
            for subject, predicate in self.graph.subject_predicates(left):
                self.store_triple((subject, predicate, right))
            for subject, predicate in self.graph.subject_predicates(right):
                self.store_triple((subject, predicate, left))


@dataclass(frozen=True)
class ReasoningMeasurement:
    graph: Graph
    duration_ms: float
    input_triples: int
    output_triples: int

    @property
    def inferred_triples(self) -> int:
        return self.output_triples - self.input_triples


_PROFILES: dict[str, Type] = {
    "rdfs": DatatypeAwareRDFSSemantics,
    "owlrl": OWLRL_Semantics,
    "rdfs_owlrl": RDFS_OWLRL_Semantics,
}


def available_reasoners() -> tuple[str, ...]:
    return tuple(_PROFILES)


def materialize(source: Graph, reasoner: str) -> ReasoningMeasurement:
    try:
        semantics = _PROFILES[reasoner]
    except KeyError as error:
        raise ValueError(
            f"Unknown reasoner {reasoner!r}; choose from {sorted(_PROFILES)}"
        ) from error
    graph = Graph()
    for prefix, namespace in source.namespaces():
        graph.bind(prefix, namespace)
    for triple in source:
        graph.add(triple)
    input_triples = len(graph)
    started = perf_counter_ns()
    DeductiveClosure(
        semantics,
        axiomatic_triples=False,
        datatype_axioms=False,
    ).expand(graph)
    duration_ms = (perf_counter_ns() - started) / 1_000_000
    return ReasoningMeasurement(
        graph=graph,
        duration_ms=duration_ms,
        input_triples=input_triples,
        output_triples=len(graph),
    )
