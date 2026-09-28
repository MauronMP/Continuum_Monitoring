from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from time import perf_counter_ns
from typing import Type
from .core.contracts import Reasoner, ReasoningResult
from .owl_materialization import (
    NativeOWLReasoner, MaterializationError, InconsistentOntologyError,
    OWL_MATERIALIZATION_CONTRACT,
)

from owlrl import (
    DeductiveClosure,
    OWLRL_Semantics,
    RDFS_OWLRL_Semantics,
    RDFS_Semantics,
)
from rdflib import Graph, Literal


REASONING_CONTRACT = "rdfs-literal-value-space-v1"
IDENTITY_CONTRACT = "identity-graph-v1"
PHYSICAL_REASONERS = ("rdfs", "hermit", "openllet", "jfact", "konclude")


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
    "none": ReasonerEngine(
        name="Identity / no inference",
        profile="rdf",
        implementation="In-process graph copy",
        owl_fragment="RDF graph",
        supported=True,
        suitability="Infrastructure-only baseline with no semantic inference.",
    ),
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
    **{
        name: ReasonerEngine(
            name=label,
            profile="owl_dl",
            implementation="Native Konclude OWLlink" if name == "konclude" else "Isolated Java OWLAPI",
            owl_fragment="OWL 2 DL; named-class-individual-v1 output",
            supported=True,
            suitability="Local runtime required; startup and serialization are included in timing. No fallback.",
        )
        for name, label in (("hermit", "HermiT"), ("openllet", "Openllet"), ("jfact", "JFact"), ("konclude", "Konclude"))
    },
    "elk": ReasonerEngine(
        name="ELK",
        profile="owl_el",
        implementation="Isolated Java OWLAPI with ELK",
        owl_fragment="OWL 2 EL; named-class-individual-v1 output",
        supported=True,
        suitability="Specialized OWL 2 EL classification and realization reference.",
    ),
}


def available_reasoners() -> tuple[str, ...]:
    return (
        "none", "rdfs", "owlrl", "rdfs_owlrl", "elk",
        "hermit", "openllet", "jfact", "konclude",
    )


def reasoner_catalog() -> tuple[ReasonerEngine, ...]:
    """Return implemented profiles; native runtime availability is checked at execution."""

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


@dataclass(frozen=True)
class IdentityReasoner:
    name: str = "none"

    def materialize(self, source: Graph) -> ReasoningResult:
        started = perf_counter_ns()
        graph = Graph()
        for prefix, namespace in source.namespaces():
            graph.bind(prefix, namespace)
        for triple in source:
            graph.add(triple)
        return ReasoningResult(
            graph=graph,
            duration_ms=(perf_counter_ns() - started) / 1_000_000,
            input_triples=len(source),
            output_triples=len(graph),
        )


_BACKENDS: dict[str, Reasoner] = {name: OwlrlReasoner(name) for name in _PROFILES}
_BACKENDS["none"] = IdentityReasoner()
_BACKENDS.update({name: NativeOWLReasoner(name) for name in ("hermit", "openllet", "jfact", "konclude", "elk")})


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


def reasoner_contract(name: str) -> str:
    """Version of the output semantics, independent of worker wire protocol."""
    get_reasoner(name)
    if name in ("hermit", "openllet", "jfact", "konclude", "elk"):
        return OWL_MATERIALIZATION_CONTRACT
    if name == "none":
        return IDENTITY_CONTRACT
    if name == "rdfs":
        return REASONING_CONTRACT
    return f"{name}-closure-v1"


def reasoner_provenance(name: str) -> dict[str, str]:
    """Describe the selected backend without asserting runtime verification."""
    engine = REASONER_ENGINES.get(name)
    return {
        "backend": name,
        "contract": reasoner_contract(name),
        "implementation": engine.implementation if engine else type(get_reasoner(name)).__name__,
        "fallback": "none",
    }


def reasoner_semantics(name: str) -> dict[str, str | bool]:
    """Return the task/profile contract used to form comparable groups."""
    engine = REASONER_ENGINES[name]
    task = {
        "none": "identity",
        "rdfs": "rdfs_closure",
        "owlrl": "owl_rl_materialization",
        "rdfs_owlrl": "rdfs_owl_rl_materialization",
        "elk": "owl_el_classification_realization",
        "hermit": "owl_dl_classification_realization",
        "openllet": "owl_dl_classification_realization",
        "jfact": "owl_dl_classification_realization",
        "konclude": "owl_dl_classification_realization",
    }[name]
    return {
        "reasoning_task": task,
        "reasoning_contract": reasoner_contract(name),
        "reasoner_profile": engine.profile,
        "output_semantics": engine.owl_fragment,
        "profile_compatible": True,
    }


def reasoner_readiness(name: str) -> dict:
    """Read-only presence check; verification requires actual materialization."""
    import os
    import shutil
    from .owl_materialization import _classpath, ROOT

    backend = get_reasoner(name)
    missing = []
    if isinstance(backend, NativeOWLReasoner):
        if not shutil.which(os.environ.get("JAVA", "java")):
            missing.append("Java executable")
        if not (ROOT / "tools/owl/MaterializeOntology.java").is_file():
            missing.append("tools/owl/MaterializeOntology.java")
        try:
            _classpath(name)
        except MaterializationError as error:
            missing.append(str(error))
        if name == "konclude" and not shutil.which(os.environ.get("CONTINUUM_KONCLUDE_EXECUTABLE", "Konclude")):
            missing.append("Konclude executable")
    return {**reasoner_provenance(name), "runtime_present": not missing,
            "execution_verified": False, "missing": missing}
