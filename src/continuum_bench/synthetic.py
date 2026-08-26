from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
import random

from rdflib import Graph, Literal, Namespace, RDF, RDFS
from rdflib.namespace import FOAF, XSD
from rdflib.term import Node

EX = Namespace("http://example.org/smartcity#")
SYN = Namespace("urn:continuum:synthetic:")
SOSA = Namespace("http://www.w3.org/ns/sosa/")
Triple = tuple[Node, Node, Node]


def _time(index: int) -> Literal:
    value = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=index)
    return Literal(value.isoformat().replace("+00:00", "Z"), datatype=XSD.dateTime)


def iter_synthetic_triples(
    users: int,
    seed: int = 2026,
) -> Iterator[Triple]:
    """Yield the deterministic policy-compliant synthetic ABox.

    Keeping generation as a stream lets a distributed worker retain only the
    triples owned by its role instead of first constructing the complete ABox.
    """

    if users < 0:
        raise ValueError("users must be non-negative")
    randomizer = random.Random(seed)

    nodes: list = []
    for node_index in range((users + 99) // 100):
        node = SYN[f"edge-{node_index:05d}"]
        state = SYN[f"node-state-{node_index:05d}"]
        nodes.append(node)
        yield node, RDF.type, EX.EdgeNode
        yield node, EX.hasElasticity, Literal(False)
        yield node, EX.hasNodeState, state
        yield node, EX.governedBy, EX.TrustBasedNodeSelectionPolicy
        yield state, RDF.type, EX.NodeState
        yield state, EX.hasAvailability, EX.Available
        yield state, EX.hasCommunication, EX.StableComm
        yield state, EX.hasWorkload, EX.MediumWorkload
        yield state, EX.hasResidualCapacity, EX.MediumResidual
        yield state, EX.hasOperationalStatus, EX.Operational
        yield (
            state,
            EX.hasTrustScore,
            Literal(
                f"{0.80 + randomizer.random() * 0.19:.4f}",
                datatype=XSD.decimal,
            ),
        )
        yield (
            state,
            EX.hasTrustWeight,
            Literal("0.25", datatype=XSD.decimal),
        )
        yield (
            state,
            EX.resourceUsagePercent,
            Literal("50.0", datatype=XSD.decimal),
        )
        yield state, EX.queuedRequests, Literal(2, datatype=XSD.integer)
        yield state, EX.validFrom, _time(node_index)

    ranges = (EX.RangeLocalOnly, EX.RangeCommunityAgg, EX.RangeGlobalAgg)
    for index in range(users):
        user = SYN[f"user-{index:08d}"]
        wearable = SYN[f"wearable-{index:08d}"]
        device_state = SYN[f"device-state-{index:08d}"]
        user_state = SYN[f"user-state-{index:08d}"]
        observation = SYN[f"observation-{index:08d}"]
        contract = SYN[f"contract-{index:08d}"]
        relation = SYN[f"relation-{index:08d}"]
        node = nodes[index % len(nodes)]
        consent_range = ranges[index % len(ranges)]
        consent = EX.ConsentDenied if consent_range == EX.RangeLocalOnly else EX.ConsentGiven

        yield user, RDF.type, EX.User
        yield user, FOAF.name, Literal(f"Synthetic participant {index}")
        yield user, EX.anonymizedID, Literal(f"SYN-{index:08d}")
        yield user, EX.hasConsent, consent
        yield user, EX.hasActiveConsentRange, consent_range
        yield user, EX.hasSemanticContract, contract
        yield user, EX.hasWearable, wearable
        yield user, EX.hasUserState, user_state
        yield user, EX.governedBy, EX.ConsentAwareProcessingPolicy

        yield wearable, RDF.type, EX.SmartWatch
        yield wearable, EX.hasDeviceState, device_state
        yield wearable, EX.connectsTo, node
        yield device_state, RDF.type, EX.DeviceState
        yield device_state, EX.hasBatteryLevel, EX.BatteryMedium
        yield device_state, EX.hasConnectionStatus, EX.Connected
        yield device_state, EX.parametrizedDataReady, Literal(True)
        yield device_state, EX.validFrom, _time(index + 10_000)

        yield user_state, RDF.type, EX.UserState
        yield user_state, EX.hasMobility, EX.Walking
        yield user_state, EX.hasPersonStatus, EX.Calm
        yield user_state, EX.hasPredictedStressLevel, EX.StressLow
        yield user_state, EX.validFrom, _time(index + 20_000)
        yield user_state, EX.derivedFrom, observation
        yield observation, RDF.type, EX.StressObservation
        yield observation, SOSA.resultTime, _time(index + 20_000)

        yield contract, RDF.type, EX.SemanticContract
        yield contract, EX.contractSubject, user
        yield contract, EX.hasConsentRange, consent_range
        yield contract, EX.hasProcessingPurpose, EX.PurposeLocalPrediction
        yield contract, EX.governedBy, EX.ConsentAwareProcessingPolicy
        yield contract, EX.validFrom, _time(index)

        yield relation, RDF.type, EX.NodeUserRelation
        yield relation, EX.relatesNode, node
        yield relation, EX.relatesUser, user
        yield relation, EX.hasDistance, EX.Close
        yield relation, EX.isPreferredNode, Literal(True)
        yield relation, EX.validFrom, _time(index)


def add_synthetic_data(graph: Graph, users: int, seed: int = 2026) -> int:
    """Add a deterministic, policy-compliant ABox and return triples added."""

    before = len(graph)
    graph.bind("syn", SYN)
    for triple in iter_synthetic_triples(users, seed):
        graph.add(triple)

    return len(graph) - before


def add_synthetic_rules(graph: Graph, rule_count: int) -> int:
    """Add an exact, deterministic RDFS rule-chain workload.

    Each ``rdfs:subClassOf`` axiom is counted as one synthetic rule. A probe
    instance activates the complete chain so increasing the rule count changes
    both schema size and materialisation work.
    """

    if rule_count < 0:
        raise ValueError("rule_count must be non-negative")
    before = len(graph)
    graph.bind("syn", SYN)
    if rule_count:
        graph.add((SYN["rule-probe"], RDF.type, SYN["rule-class-00000"]))
    for index in range(rule_count):
        graph.add(
            (
                SYN[f"rule-class-{index:05d}"],
                RDFS.subClassOf,
                SYN[f"rule-class-{index + 1:05d}"],
            )
        )
    return len(graph) - before


def pad_to_target_triples(
    graph: Graph,
    target_triples: int,
    *,
    mode: str = "semantic",
) -> int:
    """Grow a graph to an exact target using semantic or neutral payload facts.

    ``semantic`` preserves the original workload: every added resource is an
    ``ex:User`` and deliberately activates ontology axioms. ``neutral`` uses a
    benchmark-only predicate outside the application vocabulary. RDFS can
    still derive generic RDF/RDFS facts, so callers must report both asserted
    and materialised sizes, but the application class hierarchy is not
    multiplied by the padding.
    """

    if target_triples < 0:
        raise ValueError("target_triples must be non-negative")
    if mode not in {"semantic", "neutral"}:
        raise ValueError("padding mode must be 'semantic' or 'neutral'")
    if target_triples and target_triples < len(graph):
        raise ValueError(
            f"target_triples={target_triples} is below current size={len(graph)}"
        )
    before = len(graph)
    while target_triples and len(graph) < target_triples:
        index = len(graph) - before
        subject = SYN[f"padding-{index:09d}"]
        if mode == "semantic":
            graph.add((subject, RDF.type, EX.User))
        else:
            graph.add(
                (
                    subject,
                    SYN["benchmarkPayload"],
                    Literal(index, datatype=XSD.integer),
                )
            )
    return len(graph) - before
