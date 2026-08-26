"""One-off deterministic migration from the v2.1 monoliths to project modules."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import OWL, SH

ROOT = Path(__file__).resolve().parents[1]
EX = Namespace("http://example.org/smartcity#")

QUERY_CATEGORY = {
    "topology": {
        "BASE-Q02", "BASE-Q04", "BASE-Q23", "BASE-Q29",
        "BASE-Q32", "BASE-Q34",
    },
    "semantic_schema": {
        "EXT-Q01", "EXT-Q33",
    },
    "observability": {
        "BASE-Q07", "BASE-Q08", "BASE-Q10", "BASE-Q26",
        "BASE-Q33", "EXT-Q14", "EXT-Q15",
    },
    "decision": {
        "BASE-Q19", "BASE-Q21", "EXT-Q18", "EXT-Q20", "EXT-Q21", "EXT-Q34",
    },
    "consent": {
        "BASE-Q01", "BASE-Q20", "BASE-Q31", "EXT-Q02",
    },
    "contract_compliance": {
        *{f"EXT-Q{i:02d}" for i in range(3, 9)},
        "EXT-Q24",
    },
    "access_control": {
        "BASE-Q06", "BASE-Q15", "BASE-Q25", "BASE-Q28", "EXT-Q19",
    },
    "policy": {
        *{f"EXT-Q{i:02d}" for i in range(9, 14)},
        "EXT-Q22", "EXT-Q23",
    },
    "migration": {
        "BASE-Q12", "BASE-Q13", "BASE-Q14", "BASE-Q22", "BASE-Q27",
        "BASE-Q35", "EXT-Q16", "EXT-Q17",
    },
    "delegation": {
        *{f"EXT-Q{i:02d}" for i in range(28, 33)},
    },
    "federation": {
        "BASE-Q16", "BASE-Q24", "BASE-Q30",
    },
    "privacy": {"EXT-Q25", "EXT-Q26", "EXT-Q27"},
    "context": {"BASE-Q17", "BASE-Q18"},
    "wellbeing": {"BASE-Q03", "BASE-Q05", "BASE-Q09", "BASE-Q11"},
}

DOMAIN_QUERY_IDS = {
    "BASE-Q03",
    "BASE-Q05",
    "BASE-Q09",
    "BASE-Q10",
    "BASE-Q11",
    "BASE-Q17",
    "BASE-Q20",
    "BASE-Q25",
    "BASE-Q28",
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
    "AdaptabilityLevel", "AvailabilityLevel", "BatteryLevel",
    "CommunicationLevel", "ConsentRange", "ConsentStatus",
    "DeviceConnectionStatus", "DistanceLevel", "EnergyLevel",
    "MAPESymptom", "MigrationCostLevel", "MigrationTimeLevel",
    "MobilityLevel", "ModelDegradationCause", "ModelTier",
    "OperationalStatus", "PerformanceLevel", "PolicyType",
    "PopulationDensity", "ProcessingLevel", "ProcessingPurpose",
    "ProfitabilityLevel", "ResidualCapacity", "TrafficWindow",
    "WorkloadLevel", "StressLevel", "PersonStatus",
}

QUERY_RE = re.compile(
    r"^# START QUERY ([A-Z]+-Q\d+):([^\n]*)\n"
    r"(.*?)"
    r"^# END QUERY \1:",
    re.MULTILINE | re.DOTALL,
)


def local_name(term: object) -> str:
    text = str(term)
    return text.rsplit("#", 1)[-1] if "#" in text else text.rsplit("/", 1)[-1]


def closure_from_roots(graph: Graph, roots: set[object]) -> set[object]:
    """Include blank nodes owned by a set of named roots."""
    selected = set(roots)
    pending = list(roots)
    while pending:
        subject = pending.pop()
        for _, _, obj in graph.triples((subject, None, None)):
            if isinstance(obj, BNode) and obj not in selected:
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
    comment: str,
    imports: tuple[str, ...] = (),
) -> None:
    subject = URIRef(iri)
    graph.add((subject, RDF.type, OWL.Ontology))
    graph.add((subject, RDFS.label, Literal(label, lang="en")))
    graph.add((subject, RDFS.comment, Literal(comment, lang="en")))
    graph.add((subject, OWL.versionInfo, Literal("2.2.0")))
    for imported in imports:
        graph.add((subject, OWL.imports, URIRef(imported)))


def serialize(graph: Graph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(path, format="turtle")


def split_ontology(source_path: Path) -> None:
    source = Graph()
    source.parse(source_path, format="turtle")
    source.bind("ex", EX)

    shape_roots = {
        subject
        for shape_type in (SH.NodeShape, SH.PropertyShape)
        for subject in source.subjects(RDF.type, shape_type)
    }
    shape_subjects = closure_from_roots(source, shape_roots)

    schema_types = {
        OWL.Ontology,
        OWL.Class,
        OWL.ObjectProperty,
        OWL.DatatypeProperty,
        OWL.AnnotationProperty,
    }
    schema_roots = {
        subject
        for schema_type in schema_types
        for subject in source.subjects(RDF.type, schema_type)
        if subject not in shape_subjects
    }
    domain_schema_roots = {
        subject for subject in schema_roots if local_name(subject) in DOMAIN_TERMS
    }
    domain_schema_subjects = closure_from_roots(source, domain_schema_roots)
    all_schema_subjects = closure_from_roots(source, schema_roots)
    core_schema_subjects = all_schema_subjects - domain_schema_subjects

    named_individuals = set(source.subjects(RDF.type, OWL.NamedIndividual))
    vocabulary_roots = {
        subject
        for subject in named_individuals
        if any(
            local_name(obj) in ENUM_CLASSES
            for obj in source.objects(subject, RDF.type)
        )
    }
    domain_vocabulary_roots = {
        subject
        for subject in vocabulary_roots
        if any(
            local_name(obj) in {"StressLevel", "PersonStatus"}
            for obj in source.objects(subject, RDF.type)
        )
    }
    core_vocabulary_roots = vocabulary_roots - domain_vocabulary_roots

    excluded = (
        all_schema_subjects
        | shape_subjects
        | core_vocabulary_roots
        | domain_vocabulary_roots
    )
    example_subjects = set(source.subjects()) - excluded

    core_schema = graph_for_subjects(source, core_schema_subjects)
    core_vocab = graph_for_subjects(source, core_vocabulary_roots)
    domain_schema = graph_for_subjects(source, domain_schema_subjects)
    domain_vocab = graph_for_subjects(source, domain_vocabulary_roots)
    examples = graph_for_subjects(source, example_subjects)
    shapes = graph_for_subjects(source, shape_subjects)

    add_module_metadata(
        core_vocab,
        "http://example.org/smartcity/modules/core-vocabulary",
        "Continuum Monitoring Core Vocabulary",
        "Controlled values shared by any continuum monitoring domain.",
        ("http://example.org/smartcity",),
    )
    add_module_metadata(
        domain_schema,
        "http://example.org/smartcity/modules/wellbeing",
        "Continuum Monitoring Wellbeing Profile",
        "Optional wearable, physiological, stress and sleep extension.",
        ("http://example.org/smartcity",),
    )
    add_module_metadata(
        domain_vocab,
        "http://example.org/smartcity/modules/wellbeing-vocabulary",
        "Continuum Monitoring Wellbeing Vocabulary",
        "Controlled values for the optional wellbeing profile.",
        ("http://example.org/smartcity/modules/wellbeing",),
    )
    add_module_metadata(
        examples,
        "http://example.org/smartcity/examples/reference-system",
        "Continuum Monitoring Reference System",
        "Reference ABox with policy-compliant scenarios used by tests.",
        (
            "http://example.org/smartcity",
            "http://example.org/smartcity/modules/core-vocabulary",
            "http://example.org/smartcity/modules/wellbeing",
            "http://example.org/smartcity/modules/wellbeing-vocabulary",
        ),
    )
    add_module_metadata(
        shapes,
        "http://example.org/smartcity/shapes/federated-learning",
        "Federated Learning Compliance Shapes",
        "SHACL constraints retained from the v2.1 ontology.",
        ("http://example.org/smartcity",),
    )

    serialize(core_schema, ROOT / "ontology/core/schema.ttl")
    serialize(core_vocab, ROOT / "ontology/core/vocabulary.ttl")
    serialize(domain_schema, ROOT / "ontology/domains/wellbeing/schema.ttl")
    serialize(domain_vocab, ROOT / "ontology/domains/wellbeing/vocabulary.ttl")
    serialize(examples, ROOT / "ontology/examples/reference-system.ttl")
    serialize(shapes, ROOT / "ontology/shapes/federated-learning.ttl")

    union = Graph()
    for graph in (core_schema, core_vocab, domain_schema, domain_vocab, examples, shapes):
        union += graph
    missing = set(source) - set(union)
    if missing:
        raise RuntimeError(f"Ontology split lost {len(missing)} triples")


def category_for(query_id: str) -> str:
    matches = [category for category, ids in QUERY_CATEGORY.items() if query_id in ids]
    if len(matches) != 1:
        raise RuntimeError(f"{query_id} belongs to {matches}, expected exactly one category")
    return matches[0]


def query_kind(query_id: str, title: str, query: str) -> tuple[str, str]:
    normalized = title.lower()
    if re.search(r"\bASK\b", query, re.IGNORECASE):
        return "ask", "true"
    if "violation" in normalized or (
        query_id == "EXT-Q21" and "not_normalized" in normalized
    ):
        return "violation", "zero_rows"
    if "warning" in normalized:
        return "warning", "zero_rows"
    if "inventory" in normalized:
        return "inventory", "non_empty"
    if "report" in normalized or "dashboard" in normalized:
        return "report", "non_empty"
    if "review" in normalized:
        return "review", "any"
    return "select", "any"


def split_queries(source_path: Path) -> None:
    text = source_path.read_text(encoding="utf-8")
    matches = list(QUERY_RE.finditer(text))
    if len(matches) != 69:
        raise RuntimeError(f"Expected 69 queries, found {len(matches)}")

    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for order, match in enumerate(matches, start=1):
        query_id, title, body = match.groups()
        if query_id in seen:
            raise RuntimeError(f"Duplicate query id: {query_id}")
        seen.add(query_id)

        query = body.split("# EXPECTED:", 1)[0].strip() + "\n"
        category = category_for(query_id)
        tier = "domain" if query_id in DOMAIN_QUERY_IDS else "core"
        relative = (
            Path("queries/domain/wellbeing") / category if tier == "domain"
            else Path("queries/core") / category
        ) / f"{query_id.lower()}.rq"
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(query, encoding="utf-8")

        kind, expectation = query_kind(query_id, title.strip(), query)
        rows.append(
            {
                "order": order,
                "id": query_id,
                "tier": tier,
                "category": category,
                "kind": kind,
                "expectation": expectation,
                "path": relative.as_posix(),
                "title": title.strip(),
            }
        )

    all_assigned = set().union(*QUERY_CATEGORY.values())
    if seen != all_assigned:
        raise RuntimeError(
            f"Catalog mismatch: missing={sorted(seen - all_assigned)}, "
            f"extra={sorted(all_assigned - seen)}"
        )

    catalog = ROOT / "queries/catalog.csv"
    with catalog.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    split_ontology(ROOT / "ontology/legacy/smartcity_continuum-v2.2.0.ttl")
    split_queries(ROOT / "queries/legacy/sparql_battery-v2.2.0.sparql")


if __name__ == "__main__":
    main()
