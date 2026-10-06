"""Common decision port and equivalent procedural/semantic implementations."""
from __future__ import annotations

from time import perf_counter
from typing import Protocol
from urllib.parse import quote

from rdflib import Graph, Literal, Namespace, RDF, RDFS
from rdflib.plugins.sparql import prepareQuery

from ...reasoners import get_reasoner
from ..policy_evaluation.config import PolicyRule, ResourceSpec, StaticPlan
from ..policy_evaluation.model import MonitoringPlan, PolicyEngine, static_decision

NS = Namespace("urn:continuum:comparison:")
STRATEGIES = ("static", "procedural", "semantic")


def term(value: str):
    return NS[quote(value, safe="")]


class DecisionAdapter(Protocol):
    """Adapters receive context only, never the expected result."""
    reasoning_ms: float
    explicit_triples: int
    closure_triples: int

    def decide(self, context: str) -> MonitoringPlan: ...


class StaticAdapter:
    reasoning_ms = 0.0
    explicit_triples = 0
    closure_triples = 0

    def __init__(self, resources, rules, static):
        self.static = static

    def decide(self, context):
        return static_decision(self.static).plan


class ProceduralAdapter:
    reasoning_ms = 0.0
    explicit_triples = 0
    closure_triples = 0

    def __init__(self, resources, rules, static):
        self.engine = PolicyEngine(resources, rules)

    def decide(self, context):
        return self.engine.decide(context).plan


class SemanticAdapter:
    """RDFS class inference is consumed by the resource-selection query.

    Specialized device classes subclass tier classes. No direct tier typing
    is asserted on resources. Without inference, the selection query misses
    these devices. Policy conditions are explicit context memberships; this
    adapter does not infer clinical states or implement OWL policy conflict
    resolution. It evaluates an isolated executable projection of the rules.
    """
    def __init__(self, resources, rules, static):
        graph = Graph()
        self.rules = {rule.identifier: rule for rule in rules}
        for resource in resources:
            specialized = term("device-class:" + resource.tier)
            tier = term("tier:" + resource.tier)
            graph.add((specialized, RDFS.subClassOf, tier))
            graph.add((term("resource:" + resource.identifier), RDF.type, specialized))
            graph.add((term("resource:" + resource.identifier), NS.identifier, Literal(resource.identifier)))
        for rule in rules:
            policy = term("policy:" + rule.identifier)
            graph.add((policy, NS.identifier, Literal(rule.identifier)))
            for context in rule.contexts:
                graph.add((policy, NS.context, Literal(context)))
            for tier in rule.tiers:
                graph.add((policy, NS.targetTier, term("tier:" + tier)))
        result = get_reasoner("rdfs").materialize(graph)
        self.graph = result.graph
        self.reasoning_ms = result.duration_ms
        self.explicit_triples = result.input_triples
        self.closure_triples = result.output_triples
        self.policy_query = prepareQuery(
            "SELECT DISTINCT ?id WHERE { ?p c:context ?context; c:identifier ?id }",
            initNs={"c": NS},
        )
        self.resource_query = prepareQuery(
            "SELECT DISTINCT ?id WHERE { ?p c:context ?context; c:targetTier ?tier . "
            "?r a ?tier; c:identifier ?id }", initNs={"c": NS},
        )

    def decide(self, context):
        bindings = {"context": Literal(context)}
        identifiers = tuple(sorted(str(row.id) for row in self.graph.query(self.policy_query, initBindings=bindings)))
        resources = tuple(sorted(str(row.id) for row in self.graph.query(self.resource_query, initBindings=bindings)))
        active = [self.rules[key] for key in identifiers]
        return MonitoringPlan(
            resources, identifiers,
            tuple(sorted({c for rule in active for c in rule.categories})),
            tuple(sorted({m for rule in active for m in rule.metrics})),
            min((r.sampling_interval_seconds for r in active), default=0.0),
            tuple(sorted({a for rule in active for a in rule.actions})),
        )


ADAPTERS = {"static": StaticAdapter, "procedural": ProceduralAdapter, "semantic": SemanticAdapter}


def build_adapter(strategy: str, workload: dict):
    started = perf_counter()
    resources = tuple(ResourceSpec(**item) for item in workload["resources"])
    rules = tuple(PolicyRule(**item) for item in workload["rules"])
    static = StaticPlan(**workload["static_plan"])
    adapter = ADAPTERS[strategy](resources, rules, static)
    return adapter, (perf_counter() - started) * 1000
