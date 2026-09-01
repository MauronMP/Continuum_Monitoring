"""Authority- and privacy-aware RDF fragmentation for continuum deployments."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re
import tomllib
from typing import Iterable

from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.namespace import FOAF

from .config import BenchmarkConfig
from .ontology import load_graph
from .synthetic import SYN, iter_synthetic_triples
from .topology import (
    Topology,
    TIERS,
    authority_index,
    infer_tier,
    load_topology,
    ordered_nodes,
)


EX = Namespace("http://example.org/smartcity#")
SYNTHETIC_PREFIX = "urn:continuum:synthetic:"
_SENSITIVE_CLASS_NAMES = {
    "User",
    "Wearable",
    "SmartWatch",
    "SmartRing",
    "SmartBand",
    "PhysiologicalSensor",
    "HeartRateSensor",
    "EDASensor",
    "SleepSensor",
    "AccelerometerSensor",
    "SpO2Sensor",
    "TemperatureSensor",
    "PhysiologicalObservation",
    "SleepObservation",
    "StressObservation",
    "PhysiologicalParametrizedData",
    "SleepParametrizedData",
    "ParametrizedData",
    # Pseudonymous mobile compute identities may be shared under the v3 policy
    # model. Raw/derived observations and personal context remain at their
    # data-owner edge.
    "DeviceState",
    "UserState",
    "SemanticContract",
    "NodeUserRelation",
    "ConsentRecord",
    "AuthorizationDecision",
    "Identifier",
    "AnonymousIdentifier",
    "PseudonymousIdentifier",
    "DirectIdentifier",
    "EvaluationState",
    "DecisionAlternative",
    "AdaptationAction",
    "ModelSelectionAction",
    "TransferEvent",
    "DataContext",
    "BufferRecord",
    "RetentionEvent",
    "DelegationEvent",
    "ModelGradientUpdate",
    "FederatedLearningSession",
}
_USER_COMPONENT_PREDICATES = {
    EX.hasWearable,
    EX.hasUserState,
    EX.hasMobileDevice,
    EX.hasDeviceState,
    EX.derivedFrom,
    EX.hasSemanticContract,
    EX.hasConsentRecord,
    EX.consentSubject,
    EX.hasIdentifier,
    EX.evaluationUser,
    EX.hasAuthorizationDecision,
    EX.basedOnConsentRecord,
    EX.hasDecisionAlternative,
    EX.resultedInAction,
    EX.hasDelegation,
    EX.delegatedBy,
    EX.transfersData,
    EX.authorizedByEvaluation,
    EX.hasDataContext,
    EX.carriesData,
    EX.transferSource,
    EX.originatesFromDevice,
    EX.contractSubject,
    EX.generatedBy,
    EX.originatesFromDevice,
    EX.relatesUser,
    URIRef("http://www.w3.org/ns/sosa/isHostedBy"),
    URIRef("http://www.w3.org/ns/sosa/madeBySensor"),
    URIRef("http://www.w3.org/ns/sosa/hasFeatureOfInterest"),
}
_GOVERNANCE_USER_PREDICATES = {
    RDF.type,
    EX.anonymizedID,
    EX.hasConsent,
    EX.hasActiveConsentRange,
    EX.hasSemanticContract,
    EX.governedBy,
}
_GOVERNANCE_CONTRACT_PREDICATES = {
    RDF.type,
    EX.contractSubject,
    EX.hasConsentRange,
    EX.hasProcessingPurpose,
    EX.governedBy,
    EX.validFrom,
    EX.validTo,
    EX.hasDecisionAlternative,
    EX.hasAHPScore,
}
_CROSS_AUTHORITY_PROJECTION_PREDICATES = {
    # Evaluation tickets expose only a pseudonymous contract identifier.
    EX.auditsContract,
}
_ALLOWED_SENSITIVE_PROJECTION_PREDICATES = {
    RDF.type,
    EX.anonymizedID,
    EX.hasConsent,
    EX.hasActiveConsentRange,
    EX.hasSemanticContract,
    EX.governedBy,
    EX.contractSubject,
    EX.hasConsentRange,
    EX.hasProcessingPurpose,
    EX.validFrom,
    EX.validTo,
    # Aggregated decision-quality evidence is projected without user identity
    # so EXT-Q80 can remain a complete cloud-level validation query.
    EX.hasDecisionAlternative,
    EX.hasAHPScore,
    *_CROSS_AUTHORITY_PROJECTION_PREDICATES,
}
@dataclass(frozen=True)
class FragmentSet:
    graphs: dict[str, Graph]
    substrate_triples: int
    substrate_triples_by_role: dict[str, int]
    placement_profiles: dict[str, str]
    reference_triples: int
    synthetic_triples: int
    sensitive_resources: frozenset[object]

    def union(self) -> Graph:
        graph = Graph()
        for fragment in self.graphs.values():
            _merge(graph, fragment)
        return graph


def _copy_namespaces(target: Graph, source: Graph) -> None:
    for prefix, namespace in source.namespaces():
        target.bind(prefix, namespace)


def _merge(target: Graph, source: Graph) -> None:
    _copy_namespaces(target, source)
    for triple in source:
        target.add(triple)


def _clone(source: Graph) -> Graph:
    target = Graph()
    _merge(target, source)
    return target


def _placement(config: BenchmarkConfig) -> dict[str, dict[str, object]]:
    path = config.root / "configs" / "ontology-placement.toml"
    with path.open("rb") as handle:
        document = tomllib.load(handle)
    declared = document.get("roles", {})
    if set(declared) != set(TIERS):
        raise ValueError(
            "Ontology placement must define cloud, fog, mist, edge and iot profiles"
        )
    allowed = {
        item.as_posix()
        for item in config.ontology_files
        if "ontology/examples/" not in item.as_posix()
    }
    for role, placement in declared.items():
        files = placement.get("files", [])
        unknown = set(map(str, files)) - allowed
        if unknown:
            raise ValueError(
                f"Ontology placement {role} contains unconfigured files: "
                f"{sorted(unknown)}"
            )
        if not files:
            raise ValueError(f"Ontology placement {role} is empty")
        profile = config.root / str(placement.get("profile", ""))
        if not profile.is_file():
            raise FileNotFoundError(
                f"Ontology placement profile does not exist: {profile}"
            )
    return declared


def load_substrate(
    config: BenchmarkConfig,
    role: str | None = None,
    *,
    topology: Topology | None = None,
    tier: str | None = None,
) -> Graph:
    """Load the immutable semantic substrate for a deployment role.

    Without a role this returns the logical monolithic substrate.  With a role
    it applies the explicit placement manifest, so validation shapes remain at
    cloud and wellbeing terms are not copied to fog.
    """
    if role is None:
        paths = [
            config.resolve(path)
            for path in config.ontology_files
            if "ontology/examples/" not in path.as_posix()
        ]
    else:
        if topology is not None:
            node_tier = topology.node(role).tier
        else:
            node_tier = tier or infer_tier(role)
        if node_tier not in TIERS:
            raise ValueError(f"Unknown substrate tier {node_tier!r}")
        placement = _placement(config)[node_tier]
        paths = [config.root / str(path) for path in placement["files"]]
    return load_graph(paths)


@lru_cache(maxsize=None)
def _logical_substrate_triple_count(config: BenchmarkConfig) -> int:
    """Cache the immutable logical TBox size across worker preparations."""

    return len(load_substrate(config))


def load_reference_abox(config: BenchmarkConfig) -> Graph:
    paths = [
        config.resolve(path)
        for path in config.ontology_files
        if "ontology/examples/" in path.as_posix()
    ]
    return load_graph(paths)


def _local_name(value: URIRef) -> str:
    text = str(value)
    return text.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def _authority_for(value: object, authority_nodes: tuple[str, ...]) -> str:
    if not authority_nodes:
        raise ValueError("Partitioned topology requires an authority node")
    return authority_nodes[authority_index(value, len(authority_nodes))]


def _reference_owners(
    reference: Graph,
    authority_nodes: tuple[str, ...],
) -> dict[object, str]:
    sensitive_subjects = {
        subject
        for subject, class_ in reference.subject_objects(RDF.type)
        if isinstance(class_, URIRef)
        and _local_name(class_) in _SENSITIVE_CLASS_NAMES
    }
    users = {
        subject for subject in reference.subjects(RDF.type, EX.User)
    }
    owners: dict[object, str] = {}
    for user in sorted(users, key=str):
        role = _authority_for(user, authority_nodes)
        pending = [user]
        while pending:
            subject = pending.pop()
            if subject in owners:
                continue
            owners[subject] = role
            for predicate, object_ in reference.predicate_objects(subject):
                if (
                    predicate in _USER_COMPONENT_PREDICATES
                    and isinstance(object_, URIRef)
                    and object_ in sensitive_subjects
                ):
                    pending.append(object_)
            for source, predicate in reference.subject_predicates(subject):
                if (
                    predicate in _USER_COMPONENT_PREDICATES
                    and source in sensitive_subjects
                ):
                    pending.append(source)
    for subject in sensitive_subjects:
        owners.setdefault(subject, _authority_for(subject, authority_nodes))
    return owners


def _reference_targets(
    triple: tuple[object, object, object],
    owners: dict[object, str],
    all_nodes: tuple[str, ...],
) -> set[str]:
    subject, predicate, object_ = triple
    owner = owners.get(subject)
    if owner:
        return {owner}
    if object_ in owners:
        targets = {owners[object_]}
        if predicate in _CROSS_AUTHORITY_PROJECTION_PREDICATES:
            targets.update(all_nodes)
        return targets
    return set(all_nodes)


def _add_reference_governance_projection(
    target: Graph,
    reference: Graph,
    owners: dict[object, str],
) -> None:
    for subject in owners:
        types = set(reference.objects(subject, RDF.type))
        if EX.User in types:
            for predicate, object_ in reference.predicate_objects(subject):
                if predicate in _GOVERNANCE_USER_PREDICATES:
                    target.add((subject, predicate, object_))
        if EX.SemanticContract in types:
            for predicate, object_ in reference.predicate_objects(subject):
                if predicate in _GOVERNANCE_CONTRACT_PREDICATES:
                    target.add((subject, predicate, object_))
        if EX.EvaluationState in types:
            for predicate, object_ in reference.predicate_objects(subject):
                if predicate in {RDF.type, EX.hasDecisionAlternative}:
                    target.add((subject, predicate, object_))
        if EX.DecisionAlternative in types:
            for predicate, object_ in reference.predicate_objects(subject):
                if predicate in {RDF.type, EX.hasAHPScore}:
                    target.add((subject, predicate, object_))


def _reference_fragments(
    reference: Graph,
    all_nodes: tuple[str, ...],
    authority_nodes: tuple[str, ...],
    cloud_nodes: tuple[str, ...],
) -> tuple[dict[str, Graph], frozenset[object]]:
    fragments = {role: Graph() for role in all_nodes}
    for graph in fragments.values():
        _copy_namespaces(graph, reference)
    owners = _reference_owners(reference, authority_nodes)
    for triple in reference:
        for role in _reference_targets(triple, owners, all_nodes):
            fragments[role].add(triple)

    # Cloud receives only pseudonymous governance projections for local users.
    for cloud_node in cloud_nodes:
        _add_reference_governance_projection(
            fragments[cloud_node],
            reference,
            owners,
        )
    return fragments, frozenset(owners)


def _reference_fragment(
    reference: Graph,
    role: str,
    all_nodes: tuple[str, ...],
    authority_nodes: tuple[str, ...],
    cloud_nodes: tuple[str, ...],
) -> tuple[Graph, frozenset[object]]:
    """Build only one role's reference ABox."""

    graph = Graph()
    _copy_namespaces(graph, reference)
    owners = _reference_owners(reference, authority_nodes)
    for triple in reference:
        if role in _reference_targets(triple, owners, all_nodes):
            graph.add(triple)
    if role in cloud_nodes:
        _add_reference_governance_projection(graph, reference, owners)
    return graph, frozenset(owners)


def _synthetic_owner(
    subject: object,
    authority_nodes: tuple[str, ...],
    cloud_nodes: tuple[str, ...],
) -> str | None:
    text = str(subject)
    if not text.startswith(SYNTHETIC_PREFIX):
        return None
    local = text[len(SYNTHETIC_PREFIX) :]
    if local.startswith(("edge-", "node-state-", "trust-assessment-")):
        return "node-summary"
    match = re.search(r"-(\d+)$", local)
    if match:
        return _authority_for(int(match.group(1)), authority_nodes)
    return cloud_nodes[0]


def _synthetic_local_name(subject: object) -> str:
    text = str(subject)
    return (
        text[len(SYNTHETIC_PREFIX) :]
        if text.startswith(SYNTHETIC_PREFIX)
        else ""
    )


def _synthetic_targets(
    triple: tuple[object, object, object],
    all_nodes: tuple[str, ...],
    authority_nodes: tuple[str, ...],
    cloud_nodes: tuple[str, ...],
) -> set[str]:
    subject, predicate, _ = triple
    owner = _synthetic_owner(subject, authority_nodes, cloud_nodes)
    if owner == "node-summary":
        return set(all_nodes)
    if owner in authority_nodes:
        targets = {owner}
        local_name = _synthetic_local_name(subject)
        if (
            re.fullmatch(r"user-\d+", local_name)
            and predicate in _GOVERNANCE_USER_PREDICATES
        ):
            targets.update(cloud_nodes)
        if (
            re.fullmatch(r"contract-\d+", local_name)
            and predicate in _GOVERNANCE_CONTRACT_PREDICATES
        ):
            targets.update(cloud_nodes)
        return targets
    return set(cloud_nodes)


def _synthetic_fragments(
    users: int,
    seed: int,
    all_nodes: tuple[str, ...],
    authority_nodes: tuple[str, ...],
    cloud_nodes: tuple[str, ...],
) -> tuple[dict[str, Graph], int, frozenset[object]]:
    fragments = {role: Graph() for role in all_nodes}
    for graph in fragments.values():
        graph.bind("syn", SYN)
    synthetic_count = 0
    sensitive_resources: set[object] = set()
    for triple in iter_synthetic_triples(users, seed):
        synthetic_count += 1
        subject = triple[0]
        if _synthetic_owner(subject, authority_nodes, cloud_nodes) in authority_nodes:
            sensitive_resources.add(subject)
        for role in _synthetic_targets(
            triple,
            all_nodes,
            authority_nodes,
            cloud_nodes,
        ):
            fragments[role].add(triple)
    return fragments, synthetic_count, frozenset(sensitive_resources)


def _synthetic_fragment(
    role: str,
    users: int,
    seed: int,
    all_nodes: tuple[str, ...],
    authority_nodes: tuple[str, ...],
    cloud_nodes: tuple[str, ...],
) -> tuple[Graph, int]:
    """Build one role's ABox while streaming over the logical dataset."""

    graph = Graph()
    graph.bind("syn", SYN)
    synthetic_count = 0
    for triple in iter_synthetic_triples(users, seed):
        synthetic_count += 1
        if role in _synthetic_targets(
            triple,
            all_nodes,
            authority_nodes,
            cloud_nodes,
        ):
            graph.add(triple)
    return graph, synthetic_count


def _resolve_topology(
    config: BenchmarkConfig,
    topology: Topology | None,
) -> Topology:
    return topology or load_topology(
        config.resolve(config.topology_file),
        "docker",
    )


def _partition_nodes(
    topology: Topology,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    nodes = ordered_nodes(topology.active_nodes)
    all_nodes = tuple(node.node_id for node in nodes)
    authority_nodes = tuple(
        node.node_id for node in nodes if node.authority
    )
    cloud_nodes = tuple(
        node.node_id for node in nodes if node.tier == "cloud"
    )
    if not authority_nodes or not cloud_nodes:
        raise ValueError(
            f"Topology {topology.name!r} requires cloud and authority nodes"
        )
    return all_nodes, authority_nodes, cloud_nodes


def build_fragments(
    config: BenchmarkConfig,
    users: int,
    seed: int | None = None,
    *,
    topology: Topology | None = None,
) -> FragmentSet:
    """Build one deterministic fragment per configured active node."""
    topology = _resolve_topology(config, topology)
    all_nodes, authority_nodes, cloud_nodes = _partition_nodes(topology)
    logical_substrate = load_substrate(config)
    substrates = {
        role: load_substrate(config, role, topology=topology)
        for role in all_nodes
    }
    placement = _placement(config)
    reference = load_reference_abox(config)
    references, reference_sensitive = _reference_fragments(
        reference,
        all_nodes,
        authority_nodes,
        cloud_nodes,
    )
    synthetic, synthetic_count, synthetic_sensitive = _synthetic_fragments(
        users,
        config.seed if seed is None else seed,
        all_nodes,
        authority_nodes,
        cloud_nodes,
    )
    graphs = {role: _clone(substrates[role]) for role in all_nodes}
    for role in all_nodes:
        _merge(graphs[role], references[role])
        _merge(graphs[role], synthetic[role])
    return FragmentSet(
        graphs=graphs,
        substrate_triples=len(logical_substrate),
        substrate_triples_by_role={
            role: len(graph) for role, graph in substrates.items()
        },
        placement_profiles={
            role: str(placement[topology.node(role).tier]["profile"])
            for role in all_nodes
        },
        reference_triples=len(reference),
        synthetic_triples=synthetic_count,
        sensitive_resources=reference_sensitive | synthetic_sensitive,
    )


def build_role_graph(
    config: BenchmarkConfig,
    role: str,
    users: int,
    seed: int | None = None,
    *,
    topology: Topology | None = None,
) -> tuple[Graph, FragmentSet]:
    topology = _resolve_topology(config, topology)
    all_nodes, authority_nodes, cloud_nodes = _partition_nodes(topology)
    if role not in all_nodes:
        raise ValueError(
            f"Unknown partition node {role!r} in topology {topology.name!r}"
        )
    local_substrate = load_substrate(config, role, topology=topology)
    reference = load_reference_abox(config)
    local_reference, reference_sensitive = _reference_fragment(
        reference,
        role,
        all_nodes,
        authority_nodes,
        cloud_nodes,
    )
    local_synthetic, synthetic_count = _synthetic_fragment(
        role,
        users,
        config.seed if seed is None else seed,
        all_nodes,
        authority_nodes,
        cloud_nodes,
    )
    graph = _clone(local_substrate)
    _merge(graph, local_reference)
    _merge(graph, local_synthetic)
    placement = _placement(config)
    placement_role = topology.node(role).tier
    fragments = FragmentSet(
        graphs={role: graph},
        substrate_triples=_logical_substrate_triple_count(config),
        substrate_triples_by_role={role: len(local_substrate)},
        placement_profiles={
            role: str(placement[placement_role]["profile"])
        },
        reference_triples=len(reference),
        synthetic_triples=synthetic_count,
        sensitive_resources=reference_sensitive,
    )
    return graph, fragments


def privacy_violations(
    graph: Graph,
    role: str,
    sensitive_resources: Iterable[object] = (),
    *,
    authority: bool | None = None,
) -> list[str]:
    """Return private facts or links that must not leave authority nodes."""
    if authority is None:
        try:
            authority = infer_tier(role) in {"edge", "iot"}
        except ValueError:
            authority = False
    if authority:
        return []
    errors: list[str] = []
    forbidden_predicates = {
        FOAF.name,
        EX.hasWearable,
        EX.hasUserState,
        EX.hasDeviceState,
        EX.derivedFrom,
    }
    forbidden_types = {
        EX.StressObservation,
        EX.PhysiologicalObservation,
        EX.SleepObservation,
        EX.SmartWatch,
        EX.SmartRing,
        EX.SmartBand,
        EX.UserState,
        EX.DeviceState,
    }
    sensitive = set(sensitive_resources)
    sensitive.update(
        subject
        for subject, class_ in graph.subject_objects(RDF.type)
        if isinstance(class_, URIRef)
        and _local_name(class_) in _SENSITIVE_CLASS_NAMES
    )
    for subject, predicate, object_ in graph:
        touches_sensitive = (
            subject in sensitive
            or object_ in sensitive
        )
        if predicate in forbidden_predicates and touches_sensitive:
            errors.append(f"{subject.n3()} uses forbidden {predicate.n3()}")
        if predicate == RDF.type and object_ in forbidden_types:
            errors.append(f"{subject.n3()} has forbidden type {object_.n3()}")
        if (
            touches_sensitive
            and predicate not in _ALLOWED_SENSITIVE_PROJECTION_PREDICATES
            and predicate not in forbidden_predicates
            and not (predicate == RDF.type and object_ in forbidden_types)
        ):
            errors.append(
                f"{subject.n3()} exposes sensitive endpoint via "
                f"{predicate.n3()}"
            )
    return sorted(errors)


def write_fragments(
    fragments: FragmentSet,
    output_dir: Path,
) -> list[Path]:
    """Persist every configured deterministic fragment as Turtle."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for role, graph in fragments.graphs.items():
        path = output_dir / f"{role}.ttl"
        graph.serialize(path, format="turtle")
        paths.append(path)
    return paths
