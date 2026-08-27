"""Build the modular runtime assets from the canonical v3.0.0 artefacts.

The two files under ``ontology/legacy`` and ``queries/legacy`` are immutable
release inputs. This script splits the ontology without losing source triples,
extracts one SPARQL statement per file, and regenerates the distributed plan.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import OWL, SH


ROOT = Path(__file__).resolve().parents[1]
VERSION = "3.0.0"
EX = Namespace("http://example.org/smartcity#")
SKOLEM_PREFIX = f"urn:continuum:ontology:{VERSION}:node:"
ONTOLOGY_SOURCE = ROOT / "ontology/legacy/smartcity_continuum-v3.0.0.ttl"
QUERY_SOURCE = ROOT / "queries/legacy/sparql_battery-v3.0.0.sparql"

QUERY_RE = re.compile(
    r"^# START QUERY ([A-Z]+-Q\d+):([^\n]*)\n(.*?)^# END QUERY \1:",
    re.MULTILINE | re.DOTALL,
)
METADATA_RE = re.compile(
    r"^# (?P<key>Type|Purpose|Requirements|Policies|Current v3\.0\.0 result):"
    r"\s*(?P<value>.*)$",
    re.MULTILINE,
)


# Cumulative stages are independently deployable monitoring capabilities,
# finer grained than the seven editorial blocks in the source battery.
QUERY_CATEGORY: dict[str, set[str]] = {
    "topology": {"BASE-Q02", "BASE-Q23", "BASE-Q29", "BASE-Q34"},
    "semantic_schema": {"EXT-Q01", "EXT-Q02", "EXT-Q05", "EXT-Q06"},
    "observability": {
        "BASE-Q07", "BASE-Q08", "BASE-Q10", "BASE-Q26", "BASE-Q33",
    },
    "identity_consent": {
        "BASE-Q01", "BASE-Q06", "BASE-Q15", "BASE-Q20", "BASE-Q25",
        "BASE-Q28", "BASE-Q31", *{f"EXT-Q{i:02d}" for i in range(11, 22)},
    },
    "data_lifecycle": {
        "EXT-Q23", "EXT-Q24", "EXT-Q25",
        *{f"EXT-Q{i:02d}" for i in range(31, 36)},
    },
    "security_identity": {
        "EXT-Q22", *{f"EXT-Q{i:02d}" for i in range(26, 31)},
    },
    "context_zones": {
        "BASE-Q17", "BASE-Q18", *{f"EXT-Q{i:02d}" for i in range(36, 40)},
    },
    "trust": {f"EXT-Q{i:02d}" for i in range(40, 46)},
    "decision": {
        "BASE-Q04", "BASE-Q19", "BASE-Q21", "BASE-Q32",
        *{f"EXT-Q{i:02d}" for i in range(46, 59)},
    },
    "policy_governance": {
        "EXT-Q03", "EXT-Q04", "EXT-Q07", "EXT-Q08", "EXT-Q09",
        "EXT-Q10", "EXT-Q78", "EXT-Q79",
    },
    "adaptation": {
        "BASE-Q12", "BASE-Q13", "BASE-Q22", "BASE-Q27",
        *{f"EXT-Q{i:02d}" for i in range(59, 63)},
    },
    "delegation": {
        "BASE-Q14", "BASE-Q35", *{f"EXT-Q{i:02d}" for i in range(63, 66)},
    },
    "federation": {
        "BASE-Q16", "BASE-Q24", "BASE-Q30",
        *{f"EXT-Q{i:02d}" for i in range(66, 70)},
    },
    "audit_temporal": {f"EXT-Q{i:02d}" for i in range(70, 75)},
    "validation": {"EXT-Q75", "EXT-Q76", "EXT-Q77", "EXT-Q80"},
    "wellbeing": {"BASE-Q03", "BASE-Q05", "BASE-Q09", "BASE-Q11"},
}

DOMAIN_TERMS = {
    "Wearable", "SmartWatch", "SmartRing", "SmartBand",
    "PhysiologicalSensor", "HeartRateSensor", "EDASensor", "SleepSensor",
    "AccelerometerSensor", "SpO2Sensor", "TemperatureSensor",
    "PhysiologicalObservation", "SleepObservation", "StressObservation",
    "PhysiologicalParametrizedData", "SleepParametrizedData",
    "StressLevel", "PersonStatus", "generatedBy", "hasPersonStatus",
    "hasPredictedStressLevel", "hasWearable",
}

ENUM_CLASSES = {
    "AdaptabilityLevel", "AuthorizationOutcome", "AvailabilityLevel",
    "BatteryLevel", "CommunicationLevel", "ConflictResolutionStrategy",
    "ConsentRange", "DataCategory", "DataCriticality", "DataSensitivity",
    "DecisionMethod", "DeviceConnectionStatus", "DistanceLevel", "EnergyLevel",
    "MAPESymptom", "MigrationCostLevel", "MigrationTimeLevel", "MobilityLevel",
    "ModelDegradationCause", "ModelTier", "OperationalStatus", "PayloadType",
    "PerformanceLevel", "PersonStatus", "PolicyCategory", "PolicyRelationType",
    "PolicyType", "PopulationDensity", "ProcessingLevel", "ProcessingPurpose",
    "ProcessingScope", "ProfitabilityLevel", "QueryType", "ResidualCapacity",
    "StressLevel", "TrafficWindow",
}

MODULE_CLASSES = {
    "topology": {
        "CityArea", "CloudNode", "Community", "ComputationalNode", "EdgeNode",
        "FogNode", "Geometry", "MistNode", "MobileDevice", "NodeUserRelation",
        "PopulationDensity", "RestrictedZone", "RuralZone", "UrbanEnvironment",
        "UrbanZone", "DistanceLevel",
    },
    "observability": {
        "AvailabilityLevel", "BatteryLevel", "CommunicationLevel",
        "ComplianceMetric", "DataContext", "DeviceConnectionStatus",
        "DeviceState", "EnergyLevel", "MobilityLevel", "NodeState",
        "OperationalStatus", "PerformanceLevel", "ResidualCapacity", "State",
        "TemporalEntity", "TrafficWindow", "TrustAssessment", "TrustEvidence",
        "UserState", "WorkloadLevel",
    },
    "governance": {
        "AcceptanceProfile", "AnonymousIdentifier", "Artifact",
        "AuthorizationDecision", "AuthorizationOutcome", "ConsentRange",
        "ConsentRecord", "ConflictResolutionStrategy", "DataCategory",
        "DataCriticality", "DataSensitivity", "DifferentialPrivacyMechanism",
        "DirectIdentifier", "EncryptionMechanism", "FunctionalRequirement",
        "Identifier", "MechanismSpecification", "NonFunctionalRequirement",
        "OntologyArtifact", "Permission", "Policy", "PolicyArtifact",
        "PolicyCategory", "PolicyCategoryRelation", "PolicyRelationType",
        "PolicyType", "PrivacyMechanism", "ProcessingPurpose", "ProcessingScope",
        "PseudonymousIdentifier", "QueryCatalog", "QuerySpecification",
        "QueryType", "Requirement", "RequirementsArtifact", "Role", "Scenario",
        "ScenarioArtifact", "SecurityMechanism", "SemanticContract",
        "StandardSpecification", "ValidationCampaign", "ValidationRequirement",
        "ValidationResult",
    },
    "orchestration": {
        "AIModel", "AdaptabilityLevel", "AdaptationAction", "BufferRecord",
        "DecisionAlternative", "DecisionMethod", "DegradationEvent",
        "DelegationEvent", "EvaluationState", "Feature", "MigrationCostLevel",
        "MigrationEvent", "MigrationTimeLevel", "ModelDegradationCause",
        "ModelSelectionAction", "ModelTier", "OffloadingEvent", "PairwiseComparison",
        "ParametrizedData", "ProfitabilityLevel", "RecoveryCondition",
        "ReplicationEvent", "RetentionEvent", "RollbackEvent", "ScalingEvent",
        "Service", "ServiceState", "SynchronizationEvent", "TransferEvent",
    },
    "federation": {
        "FederatedLearningSession", "ModelGradientUpdate", "PayloadType",
        "PrivacyBudgetAccount",
    },
}

MODULE_PROPERTIES = {
    "topology": {
        "belongsToCommunity", "connectsTo", "coversArea", "hasDistance",
        "hasElasticity", "hasGeometry", "hasNeighborNode", "hasPopulationDensity",
        "isPreferredNode", "locatedIn", "locatedInZone", "relatesNode",
        "relatesUser", "continuumLevel",
    },
    "observability": {
        "contextDeviceState", "contextNodeState", "contextProcessingLevel",
        "contextPurpose", "contextZone", "hasAvailability", "hasBatteryLevel",
        "hasCommunication", "hasComplianceMetric", "hasConnectionStatus",
        "hasDataContext", "hasEnergyLevel", "hasMobility", "hasNodeState",
        "hasOperationalStatus", "hasPerformance", "hasPersonStatus",
        "hasPredictedStressLevel", "hasResidualCapacity", "hasTrustAssessment",
        "hasTrustEvidence", "hasTrustScore", "hasUserState", "hasWorkload",
        "parametrizedDataReady", "queuedRequests", "resourceUsagePercent",
        "stateDuration", "trustAssessmentForState", "trustRuleVersion",
        "trustWindowEnd", "trustWindowStart", "evidenceContribution",
        "evidenceFactor", "userFeedbackScore", "validFrom", "validTo",
    },
    "governance": {
        "appliedMechanism", "appliedPolicy", "appliedSecurityMechanism",
        "appliesInZone", "appliesTo", "appliesToZoneType", "basedOnConsentRecord",
        "basedOnContract", "basedOnZone", "belongsToPolicyCategory",
        "belongsToQueryCatalog", "consentSubject", "contractSubject",
        "definedInArtifact", "governedBy", "hasActiveConsentRange",
        "hasAuthorizationDecision", "hasAuthorizationOutcome",
        "hasAuthorizedDataCategory", "hasConsent", "hasConsentRange",
        "hasConsentRecord", "hasDataCategory", "hasDataCriticality",
        "hasDataSensitivity", "hasEffectiveConsentRange", "hasIdentifier",
        "hasPermission", "hasPolicyAction", "hasPolicyRelationType",
        "hasPolicyStatement", "hasPolicyType", "hasProcessingPurpose",
        "hasProcessingScope", "hasQueryType", "hasRole", "hasSemanticContract",
        "policyArtifactUsed", "recommendedMechanism", "relatedRequirement",
        "relationSourceCategory", "relationTargetCategory", "requiresConsent",
        "requiresConsentRange", "requirementsArtifactUsed", "scenarioMechanism",
        "scenarioPolicy", "supportsPolicy", "tracedToMechanism", "tracedToPolicy",
        "usesAcceptanceProfile", "usesIdentifier", "usesResolutionStrategy",
        "usesStandard", "validationUsesOntology", "validationUsesPolicies",
        "validationUsesQueries", "validationUsesScenarios", "hasValidationResult",
        "artifactIdentifier", "artifactStatus", "artifactVersion",
        "authorizationReason", "categoryCode", "conditionExpression",
        "configurationStatus", "containsPersistentIdentifier",
        "containsPersonalData", "identifierScope", "identifierValue",
        "mechanismDescription", "mechanismIdentifier", "policyIdentifier",
        "policyVersion", "protectsAtRest", "protectsInTransit", "queryIdentifier",
        "queryInterpretation", "queryPurpose", "relationCode",
        "requirementIdentifier", "requirementStatement", "scenarioIdentifier",
        "securityBaselineVersion", "strategyCode", "AHP_consistency_threshold",
        "D_delegation_max", "E_device_max", "N_agents", "T_decision_max",
        "T_inference_local", "T_migration_max", "T_node_join",
        "T_reselection_max", "T_sparql_monitor",
    },
    "orchestration": {
        "actionOriginNode", "actionTargetNode", "affectsModel", "affectsService",
        "alternativeModelTier", "appliesPolicy", "auditsContract",
        "authorizedByEvaluation", "carriesData", "criterionA", "criterionB",
        "delegatedBy", "delegatesTo", "derivedFrom", "evaluatesNode",
        "evaluatesService", "evaluationPurpose", "evaluationUser", "evaluationZone",
        "expiresOnRecoveryOf", "hasAdaptability", "hasDecisionAlternative",
        "hasDecisionMethod", "hasDegradationCause", "hasDelegation",
        "hasDetectedSymptom", "hasMigrationCost", "hasMigrationTime",
        "hasModelTier", "hasPairwiseComparison", "hasProcessingLevel",
        "hasProfitability", "hasRecoveryCondition", "hasReplicationEvent",
        "hasServiceState", "hostedOnNode", "hostsModel", "hostsService",
        "parentDelegation", "partOfScenario", "replicaOf", "replicationSource",
        "replicationTarget", "resultedInAction", "rollbackTarget",
        "selectedAlternative", "selectedModelTier", "supersedesModel",
        "transferDestination", "transferSource", "triggeredByState", "usesModel",
        "hasAHPScore", "hasConsistencyRatio", "hasConsistencyThreshold",
        "hasEvaluationTicketID", "hasLatencyWeight", "hasModelQualityWeight",
        "hasPrivacyWeight", "hasSelectionJustification", "hasTrustWeight",
        "idempotencyKey", "isEligible", "lastUpdated", "legacyDecisionScore",
        "migrationNote", "migrationStatus", "modelLineageStatus", "modelVersion",
        "observedModelQuality", "pairwiseValue", "plannedExpiry",
        "predictionConfidence", "estimatedPredictionError", "evaluationOrder",
        "eligibilityReason", "delegationDepth", "replicationVersion",
        "requiresRecalculation",
    },
    "federation": {
        "aggregatesData", "budgetForContract", "budgetForPurpose", "hasPayloadType",
        "hasPrivacyBudget", "hasPrivacyBudgetAccount", "hasPrivacyMechanism",
        "involvedNode", "originatesFromDevice", "sentToNode", "transfersData",
        "updatesModel", "containsIndividualizedGradients", "hasAnonymizationApplied",
        "hasNoiseApplied", "isRedundant", "noiseLevel", "privacyBudgetConsumed",
        "privacyBudgetMaximum", "privacyBudgetRemaining", "sendTimestamp",
        "sessionTime",
    },
}

MODULE_LABELS = {
    "foundation": "Continuum foundation module",
    "topology": "Continuum topology module",
    "observability": "Continuum observability module",
    "governance": "Continuum policy and governance module",
    "orchestration": "Continuum decision and adaptation module",
    "federation": "Continuum federated learning module",
}
MODULE_IMPORTS = {
    "foundation": (),
    "topology": ("foundation",),
    "observability": ("foundation", "topology"),
    "governance": ("foundation", "topology", "observability"),
    "orchestration": ("foundation", "topology", "observability", "governance"),
    "federation": ("foundation", "governance", "orchestration"),
}


def local_name(term: object) -> str:
    text = str(term)
    return text.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def stable_skolemize(graph: Graph) -> Graph:
    """Replace parser-local blank nodes with stable release-scoped IRIs.

    RDFLib's Turtle parser uses a random run prefix followed by a stable source
    order suffix (``b1``, ``b2``...). Persisting that suffix once in generated
    modules prevents five replicated workers from multiplying equivalent blank
    restrictions and makes fragment equality linear instead of exponential.
    """

    blank_nodes = sorted(
        {node for node in graph.all_nodes() if isinstance(node, BNode)},
        key=lambda node: int(
            re.search(r"b(\d+)$", str(node)).group(1)  # type: ignore[union-attr]
        ),
    )
    mapping = {
        node: URIRef(f"{SKOLEM_PREFIX}{index}")
        for index, node in enumerate(blank_nodes, start=1)
    }
    output = Graph()
    for prefix, namespace in graph.namespaces():
        output.bind(prefix, namespace)
    for subject, predicate, object_ in graph:
        output.add((
            mapping.get(subject, subject),
            predicate,
            mapping.get(object_, object_),
        ))
    return output


def is_owned_node(value: object) -> bool:
    return isinstance(value, BNode) or str(value).startswith(SKOLEM_PREFIX)


def closure_from_roots(graph: Graph, roots: set[object]) -> set[object]:
    selected = set(roots)
    pending = list(roots)
    while pending:
        subject = pending.pop()
        for obj in graph.objects(subject):
            if is_owned_node(obj) and obj not in selected:
                selected.add(obj)
                pending.append(obj)
    return selected


def graph_for_subjects(source: Graph, subjects: set[object]) -> Graph:
    target = Graph()
    for prefix, namespace in source.namespaces():
        target.bind(prefix, namespace)
    for subject in subjects:
        for triple in source.triples((subject, None, None)):
            target.add(triple)
    return target


def add_module_metadata(
    graph: Graph,
    iri: str,
    label: str,
    imports: tuple[str, ...] = (),
) -> None:
    subject = URIRef(iri)
    graph.add((subject, RDF.type, OWL.Ontology))
    graph.add((subject, RDFS.label, Literal(label, lang="en")))
    graph.add((subject, OWL.versionInfo, Literal(VERSION)))
    for imported in imports:
        graph.add((subject, OWL.imports, URIRef(imported)))


def serialize(graph: Graph, relative: str) -> Path:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    # RDFLib currently emits two trailing line breaks for Turtle.  Normalize
    # generated artefacts so regeneration is deterministic and passes the
    # repository whitespace checks on every supported platform.
    turtle = graph.serialize(format="turtle")
    path.write_text(turtle.rstrip() + "\n", encoding="utf-8")
    return path


def module_for_schema(subject: object) -> str:
    name = local_name(subject)
    if name in DOMAIN_TERMS:
        return "wellbeing"
    for module, terms in MODULE_CLASSES.items():
        if name in terms:
            return module
    for module, terms in MODULE_PROPERTIES.items():
        if name in terms:
            return module
    return "foundation"


def split_ontology(source_path: Path = ONTOLOGY_SOURCE) -> list[Path]:
    source = stable_skolemize(Graph().parse(source_path, format="turtle"))
    source.bind("ex", EX)
    shape_roots = {
        subject
        for shape_type in (SH.NodeShape, SH.PropertyShape)
        for subject in source.subjects(RDF.type, shape_type)
    }
    shape_subjects = closure_from_roots(source, shape_roots)
    schema_types = {
        OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
        OWL.AnnotationProperty,
    }
    schema_roots = {
        subject
        for schema_type in schema_types
        for subject in source.subjects(RDF.type, schema_type)
        if subject not in shape_subjects
    }
    schema_by_module: dict[str, set[object]] = defaultdict(set)
    claimed_schema_subjects: set[object] = set()
    for root in sorted(schema_roots, key=str):
        subjects = closure_from_roots(source, {root})
        module = module_for_schema(root)
        schema_by_module[module].update(subjects - claimed_schema_subjects)
        claimed_schema_subjects.update(subjects)

    named_individuals = set(source.subjects(RDF.type, OWL.NamedIndividual))
    vocabulary_roots = {
        subject
        for subject in named_individuals
        if any(local_name(type_) in ENUM_CLASSES
               for type_ in source.objects(subject, RDF.type))
    }
    domain_vocabulary_roots = {
        subject
        for subject in vocabulary_roots
        if any(local_name(type_) in {"StressLevel", "PersonStatus"}
               for type_ in source.objects(subject, RDF.type))
    }
    core_vocabulary_roots = vocabulary_roots - domain_vocabulary_roots
    core_vocabulary_subjects = closure_from_roots(source, core_vocabulary_roots)
    domain_vocabulary_subjects = closure_from_roots(source, domain_vocabulary_roots)
    ontology_subjects = set(source.subjects(RDF.type, OWL.Ontology))
    core_schema_subjects = closure_from_roots(source, ontology_subjects)
    core_schema_subjects -= claimed_schema_subjects | shape_subjects
    excluded = (
        claimed_schema_subjects | shape_subjects | core_schema_subjects
        | core_vocabulary_subjects | domain_vocabulary_subjects
    )
    example_subjects = set(source.subjects()) - excluded

    outputs: list[tuple[Graph, str]] = []
    root_graph = graph_for_subjects(source, core_schema_subjects)
    root_iri = "http://example.org/smartcity"
    for module in (
        "foundation", "topology", "observability", "governance",
        "orchestration", "federation",
    ):
        root_graph.add((URIRef(root_iri), OWL.imports, URIRef(
            f"http://example.org/smartcity/modules/{module}"
        )))
    root_graph.add((URIRef(root_iri), OWL.imports, URIRef(
        "http://example.org/smartcity/modules/wellbeing"
    )))
    outputs.append((root_graph, "ontology/core/schema.ttl"))

    for module in (
        "foundation", "topology", "observability", "governance",
        "orchestration", "federation",
    ):
        graph = graph_for_subjects(source, schema_by_module[module])
        imports = tuple(
            f"http://example.org/smartcity/modules/{dependency}"
            for dependency in MODULE_IMPORTS[module]
        )
        add_module_metadata(
            graph,
            f"http://example.org/smartcity/modules/{module}",
            MODULE_LABELS[module],
            imports,
        )
        outputs.append((graph, f"ontology/modules/{module}.ttl"))

    core_vocabulary = graph_for_subjects(source, core_vocabulary_subjects)
    add_module_metadata(
        core_vocabulary,
        "http://example.org/smartcity/modules/core-vocabulary",
        "Continuum controlled vocabulary",
        (root_iri,),
    )
    outputs.append((core_vocabulary, "ontology/core/vocabulary.ttl"))
    domain_schema = graph_for_subjects(source, schema_by_module["wellbeing"])
    add_module_metadata(
        domain_schema,
        "http://example.org/smartcity/modules/wellbeing",
        "Optional wellbeing monitoring profile",
        (
            "http://example.org/smartcity/modules/foundation",
            "http://example.org/smartcity/modules/observability",
        ),
    )
    outputs.append((domain_schema, "ontology/domains/wellbeing/schema.ttl"))
    domain_vocabulary = graph_for_subjects(source, domain_vocabulary_subjects)
    add_module_metadata(
        domain_vocabulary,
        "http://example.org/smartcity/modules/wellbeing-vocabulary",
        "Wellbeing controlled vocabulary",
        ("http://example.org/smartcity/modules/wellbeing",),
    )
    outputs.append((domain_vocabulary, "ontology/domains/wellbeing/vocabulary.ttl"))
    examples = graph_for_subjects(source, example_subjects)
    add_module_metadata(
        examples,
        "http://example.org/smartcity/examples/reference-system",
        "Versioned v3 reference ABox and validation artefacts",
        (root_iri,),
    )
    outputs.append((examples, "ontology/examples/reference-system.ttl"))

    fl_shape_roots = {
        shape for shape in shape_roots
        if any(
            local_name(target) in {
                "FederatedLearningSession", "ModelGradientUpdate",
                "PrivacyBudgetAccount",
            }
            for target in source.objects(shape, SH.targetClass)
        )
    }
    fl_shape_subjects = closure_from_roots(source, fl_shape_roots)
    core_shapes = graph_for_subjects(source, shape_subjects - fl_shape_subjects)
    add_module_metadata(
        core_shapes,
        "http://example.org/smartcity/shapes/core-compliance",
        "Continuum v3 core compliance shapes",
        (root_iri,),
    )
    outputs.append((core_shapes, "ontology/shapes/core-compliance.ttl"))
    fl_shapes = graph_for_subjects(source, fl_shape_subjects)
    add_module_metadata(
        fl_shapes,
        "http://example.org/smartcity/shapes/federated-learning",
        "Continuum v3 federated-learning compliance shapes",
        ("http://example.org/smartcity/modules/federation",),
    )
    outputs.append((fl_shapes, "ontology/shapes/federated-learning.ttl"))

    union = Graph()
    for graph, _ in outputs:
        union += graph
    missing = set(source) - set(union)
    if missing:
        raise RuntimeError(f"Ontology split lost {len(missing)} source triples")
    return [serialize(graph, relative) for graph, relative in outputs]


def category_for(query_id: str) -> str:
    matches = [
        name for name, query_ids in QUERY_CATEGORY.items()
        if query_id in query_ids
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"{query_id} belongs to {matches}; expected exactly one category"
        )
    return matches[0]


def is_domain_query(query: str) -> bool:
    return any(
        re.search(rf":{re.escape(term)}\b", query)
        for term in DOMAIN_TERMS
    )


def parse_result(value: str) -> tuple[int, bool | None]:
    normalized = value.strip().lower()
    if normalized == "true":
        return 1, True
    if normalized == "false":
        return 0, False
    match = re.match(r"(\d+)\s+filas?", normalized)
    if match:
        return int(match.group(1)), None
    raise ValueError(f"Unsupported reference result: {value!r}")


def expectation_for(kind: str, expected_count: int, expected_ask: bool | None) -> str:
    if expected_ask is not None:
        return "true" if expected_ask else "false"
    if kind == "violation":
        return "zero_rows"
    if kind in {"inventory", "report", "dashboard"} and expected_count > 0:
        return "non_empty"
    return "any"


def query_scope(query_id: str, tier: str, category: str) -> str:
    # These three inventory/aggregate queries require the complete v3 reference
    # Mist projection.  RingB is owned deterministically by edge2.
    if query_id in {"BASE-Q02", "BASE-Q04", "BASE-Q33"}:
        return "edge2"
    if query_id in {"BASE-Q11", "BASE-Q14", "EXT-Q36", "EXT-Q39"}:
        return "edge1"
    edge_ids = {
        "BASE-Q01", "BASE-Q15", "BASE-Q25",
        "BASE-Q18", "BASE-Q21", "BASE-Q23", "BASE-Q35",
        *{f"EXT-Q{i:02d}" for i in range(11, 22)},
        "EXT-Q23", "EXT-Q26", "EXT-Q27", "EXT-Q28", "EXT-Q35",
        "EXT-Q44", "EXT-Q45",
        *{f"EXT-Q{i:02d}" for i in range(46, 59)},
        *{f"EXT-Q{i:02d}" for i in range(59, 75)},
    }
    if (
        tier == "domain"
        or query_id in edge_ids
        or category in {
            "wellbeing", "data_lifecycle", "adaptation", "delegation",
            "federation", "audit_temporal",
        }
    ):
        return "edges"
    if category in {"semantic_schema", "policy_governance", "validation"}:
        return "cloud"
    if query_id in {"BASE-Q06", "BASE-Q31", "EXT-Q29", "EXT-Q30"}:
        return "cloud"
    return "fog"


def split_queries(source_path: Path = QUERY_SOURCE) -> list[Path]:
    text = source_path.read_text(encoding="utf-8")
    matches = list(QUERY_RE.finditer(text))
    expected_ids = {
        *{f"BASE-Q{i:02d}" for i in range(1, 36)},
        *{f"EXT-Q{i:02d}" for i in range(1, 81)},
    }
    if len(matches) != len(expected_ids):
        raise RuntimeError(
            f"Expected {len(expected_ids)} queries, found {len(matches)}"
        )

    # These files are generated artefacts. Remove stale v2 paths/categories so
    # the filesystem cannot silently advertise queries absent from the catalog.
    for generated_root in (ROOT / "queries/core", ROOT / "queries/domain"):
        if generated_root.is_dir():
            for path in generated_root.rglob("*.rq"):
                path.unlink()

    rows: list[dict[str, object]] = []
    paths: list[Path] = []
    seen: set[str] = set()
    scopes: dict[str, list[str]] = defaultdict(list)
    privacy: dict[str, list[str]] = defaultdict(list)
    merges: dict[str, list[str]] = defaultdict(list)
    for order, match in enumerate(matches, start=1):
        query_id, title, body = match.groups()
        if query_id in seen:
            raise RuntimeError(f"Duplicate query id: {query_id}")
        seen.add(query_id)
        metadata = {
            item.group("key"): item.group("value").strip()
            for item in METADATA_RE.finditer(body)
        }
        required = {
            "Type", "Purpose", "Requirements", "Policies",
            "Current v3.0.0 result",
        }
        if missing := required - set(metadata):
            raise RuntimeError(f"{query_id}: missing metadata {sorted(missing)}")

        query = body.strip() + "\n"
        category = category_for(query_id)
        tier = "domain" if is_domain_query(query) else "core"
        base = (
            Path("queries/domain/wellbeing") if tier == "domain"
            else Path("queries/core")
        )
        relative = base / category / f"{query_id.lower()}.rq"
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(query, encoding="utf-8")
        paths.append(target)

        kind = metadata["Type"].lower()
        expected_count, expected_ask = parse_result(
            metadata["Current v3.0.0 result"]
        )
        scope = query_scope(query_id, tier, category)
        scopes[scope].append(query_id)
        privacy_class = (
            "restricted" if scope.startswith("edge") and tier == "domain"
            else "confidential" if scope.startswith("edge") else "internal"
        )
        privacy[privacy_class].append(query_id)
        if scope == "edges":
            strategy = "boolean_or" if kind == "ask" else "set_union"
            merges[strategy].append(query_id)

        rows.append({
            "order": order,
            "id": query_id,
            "tier": tier,
            "category": category,
            "kind": kind,
            "expectation": expectation_for(kind, expected_count, expected_ask),
            "expected_count": expected_count,
            "expected_ask": (
                "" if expected_ask is None else str(expected_ask).lower()
            ),
            "path": relative.as_posix(),
            "title": title.strip(),
            "purpose": metadata["Purpose"],
            "requirements": metadata["Requirements"],
            "policies": metadata["Policies"],
        })

    if seen != expected_ids:
        raise RuntimeError(
            f"Query IDs mismatch: missing={sorted(expected_ids - seen)}, "
            f"extra={sorted(seen - expected_ids)}"
        )
    assigned = set().union(*QUERY_CATEGORY.values())
    if assigned != expected_ids:
        raise RuntimeError(
            f"Category map mismatch: missing={sorted(expected_ids - assigned)}, "
            f"extra={sorted(assigned - expected_ids)}"
        )

    catalog = ROOT / "queries/catalog.csv"
    with catalog.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=rows[0].keys(),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    plan = ROOT / "queries/execution-plan.toml"
    lines = [
        f'version = "{VERSION}"', "",
        "# Authority-aware source selection generated with the v3 catalogue.",
        "[scopes]",
    ]
    for scope in ("cloud", "fog", "edges", "edge1", "edge2", "edge3"):
        values = ", ".join(f'"{item}"' for item in scopes[scope])
        lines.append(f"{scope} = [{values}]")
    lines.extend(["", "[merge]"])
    for strategy in ("set_union", "boolean_or"):
        values = ", ".join(f'"{item}"' for item in merges[strategy])
        lines.append(f"{strategy} = [{values}]")
    lines.extend(["", "[privacy]"])
    for privacy_class in ("restricted", "confidential"):
        values = ", ".join(
            f'"{item}"' for item in privacy[privacy_class]
        )
        lines.append(f"{privacy_class} = [{values}]")
    plan.write_text("\n".join(lines) + "\n", encoding="utf-8")
    paths.extend([catalog, plan])
    return paths


def main() -> None:
    ontology_paths = split_ontology()
    query_paths = split_queries()
    print(
        f"Built v{VERSION}: {len(ontology_paths)} ontology modules, "
        f"{len(query_paths) - 2} queries, catalog and execution plan"
    )


if __name__ == "__main__":
    main()
