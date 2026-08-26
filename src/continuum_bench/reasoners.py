from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns
from typing import Type

from owlrl import (
    DeductiveClosure,
    OWLRL_Semantics,
    RDFS_OWLRL_Semantics,
    RDFS_Semantics,
)
from rdflib import Graph


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
    "rdfs": RDFS_Semantics,
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

