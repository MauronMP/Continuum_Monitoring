from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from time import perf_counter_ns
from typing import Type
from .core.contracts import Reasoner, ReasoningResult

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
    correction runs consistently in the coordinator and physical workers.
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


ReasoningMeasurement = ReasoningResult


@dataclass(frozen=True)
class ReasonerEngine:
    """Common reasoner descriptor used by benchmark configuration."""

    name: str
    profile: str
    implementation: str
    owl_fragment: str
    supported: bool
    suitability: str
    replacement: str = ""


_PROFILES: dict[str, Type] = {
    "rdfs": DatatypeAwareRDFSSemantics,
    "owlrl": OWLRL_Semantics,
    "rdfs_owlrl": RDFS_OWLRL_Semantics,
}


REASONER_ENGINES: dict[str, ReasonerEngine] = {
    "rdfs": ReasonerEngine(
        name="RDFLib RDFS",
        profile="rdfs",
        implementation="owlrl.DeductiveClosure with datatype-aware RDFS semantics",
        owl_fragment="RDFS",
        supported=True,
        suitability=(
            "Portable Python baseline suitable for low-resource physical "
            "nodes and deterministic bounded experiments."
        ),
    ),
    "owlrl": ReasonerEngine(
        name="OWL RL",
        profile="owlrl",
        implementation="owlrl.OWLRL_Semantics",
        owl_fragment="OWL 2 RL",
        supported=True,
        suitability=(
            "Rule-based OWL profile suitable for materialisation on constrained "
            "physical nodes."
        ),
    ),
    "rdfs_owlrl": ReasonerEngine(
        name="RDFS + OWL RL",
        profile="rdfs_owlrl",
        implementation="owlrl.RDFS_OWLRL_Semantics",
        owl_fragment="RDFS plus OWL 2 RL",
        supported=True,
        suitability=(
            "Combined closure used to quantify the cost of richer semantics."
        ),
    ),
    "hermit": ReasonerEngine(
        name="HermiT",
        profile="owl_dl",
        implementation="Java OWLAPI reasoner",
        owl_fragment="OWL 2 DL",
        supported=False,
        suitability=(
            "Technically valuable for consistency checking, but unsuitable as "
            "a default physical benchmark engine on 32-bit Raspberry Pi nodes "
            "because startup cost, memory use and JVM availability dominate "
            "the monitored workload."
        ),
        replacement="owlrl",
    ),
    "openllet": ReasonerEngine(
        name="Openllet",
        profile="owl_dl",
        implementation="Java OWLAPI reasoner",
        owl_fragment="OWL 2 DL",
        supported=False,
        suitability=(
            "Useful for offline OWL DL validation, but not integrated in the "
            "bounded physical-node worker because it requires a Java service "
            "layer not portable to every target node."
        ),
        replacement="rdfs_owlrl",
    ),
    "jfact": ReasonerEngine(
        name="JFact",
        profile="owl_dl",
        implementation="Java OWLAPI reasoner",
        owl_fragment="OWL 2 DL",
        supported=False,
        suitability=(
            "Appropriate for ontology development checks, but less suitable "
            "for repeated low-latency monitoring benchmarks on constrained "
            "nodes."
        ),
        replacement="owlrl",
    ),
    "konclude": ReasonerEngine(
        name="Konclude",
        profile="owl_dl",
        implementation="Native OWL reasoner",
        owl_fragment="OWL 2 DL",
        supported=False,
        suitability=(
            "High-performance native reasoning is attractive on servers, but "
            "the deployment target includes 32-bit Raspberry Pi nodes where "
            "portable packages and identical execution semantics are not "
            "guaranteed."
        ),
        replacement="rdfs",
    ),
}


def available_reasoners() -> tuple[str, ...]:
    return tuple(_BACKENDS)


def reasoner_catalog() -> tuple[ReasonerEngine, ...]:
    """Return supported profiles and documented rejected alternatives."""

    return tuple(REASONER_ENGINES.values())


def _materialize_owlrl(source: Graph, reasoner: str) -> ReasoningMeasurement:
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


@dataclass(frozen=True)
class OwlrlReasoner:
    name: str

    def materialize(self, source: Graph) -> ReasoningResult:
        return _materialize_owlrl(source, self.name)


_BACKENDS: dict[str, Reasoner] = {name: OwlrlReasoner(name) for name in _PROFILES}


def register_reasoner(backend: Reasoner, *, replace: bool = False) -> None:
    """Register a materialization backend without modifying experiment logic."""
    if not backend.name or (backend.name in _BACKENDS and not replace):
        raise ValueError(f"Duplicate or empty reasoner name: {backend.name!r}")
    _BACKENDS[backend.name] = backend


def get_reasoner(name: str) -> Reasoner:
    try:
        return _BACKENDS[name]
    except KeyError as error:
        raise ValueError(f"Unknown reasoner {name!r}; choose from {sorted(_BACKENDS)}") from error


def materialize(source: Graph, reasoner: str) -> ReasoningMeasurement:
    return get_reasoner(reasoner).materialize(source)
