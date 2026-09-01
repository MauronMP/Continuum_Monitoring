#!/usr/bin/env python3
"""Generate the English v3 reference manuals from executable artefacts.

The generated Markdown is deliberately data-driven. Requirement, policy and
ontology statements come from the canonical Turtle release; query execution
metadata comes from ``queries/catalog.csv``. This prevents the reference
manuals from silently drifting away from the assets used by the benchmarks.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import OWL


ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY = ROOT / "ontology/legacy/smartcity_continuum-v3.0.0.ttl"
CATALOG = ROOT / "queries/catalog.csv"
REFERENCE = ROOT / "docs/reference"
EX = Namespace("http://example.org/smartcity#")

REQUIREMENT_GROUPS = (
    ("Functional requirements", "RF-", EX.FunctionalRequirement),
    ("Non-functional requirements", "RNF-", EX.NonFunctionalRequirement),
    ("Validation requirements", "RV-", EX.ValidationRequirement),
)

QUERY_KIND_HELP = {
    "inventory": "Returns the resources that make up the declared inventory.",
    "report": "Returns explanatory evidence; rows are not violations by themselves.",
    "review": "Returns configuration gaps or evidence that requires human review.",
    "violation": "Must return zero rows after all validation preconditions pass.",
    "ASK": "Returns a Boolean operational assertion defined by the query.",
    "dashboard": "Returns aggregate coverage or migration-debt indicators.",
}

CATEGORY_HELP = {
    "topology": "continuum node, location and connectivity structure",
    "semantic_schema": "release artefacts and semantic schema coverage",
    "observability": "device, user and node operational state",
    "identity_consent": "identity, consent, contracts and authorization",
    "data_lifecycle": "data context, buffering, replication and transmission",
    "security_identity": "identifiers, encryption and protected transfer",
    "context_zones": "zone-aware and georestricted processing",
    "trust": "reproducible trust evidence and eligibility",
    "decision": "model-tier selection, AHP and model lifecycle",
    "policy_governance": "policy inventory, precedence and traceability",
    "adaptation": "migration, degradation and adaptive actions",
    "delegation": "temporary delegation and recovery",
    "federation": "federated learning and differential privacy",
    "audit_temporal": "audit chains and temporal validity",
    "validation": "acceptance, SHACL and campaign readiness",
    "wellbeing": "wearable, physiological, stress and sleep concepts",
}


@dataclass(frozen=True)
class QueryRow:
    order: int
    query_id: str
    tier: str
    category: str
    kind: str
    expectation: str
    expected_count: str
    expected_ask: str
    path: str
    requirements: tuple[str, ...]
    policies: tuple[str, ...]


def _ident(value: URIRef | Literal | None) -> str:
    if value is None:
        return ""
    text = str(value)
    return text.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def _literal(graph: Graph, subject: URIRef, predicate: URIRef) -> str:
    values = [str(value) for value in graph.objects(subject, predicate)]
    return values[0] if values else ""


def _label(graph: Graph, value: URIRef | Literal | None) -> str:
    if value is None:
        return ""
    if isinstance(value, Literal):
        return str(value)
    labels = [str(item) for item in graph.objects(value, RDFS.label)]
    return labels[0] if labels else _ident(value)


def _natural_key(identifier: str) -> tuple[str, int, str]:
    match = re.search(r"^(.*?)(\d+)$", identifier)
    if not match:
        return identifier, -1, identifier
    return match.group(1), int(match.group(2)), identifier


def _ids(graph: Graph, predicate: URIRef, prefix: str) -> list[URIRef]:
    resources = {
        subject
        for subject, value in graph.subject_objects(predicate)
        if str(value).startswith(prefix)
    }
    return sorted(resources, key=lambda item: _natural_key(_ident(item)))


def _csv_ids(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _queries() -> list[QueryRow]:
    with CATALOG.open(encoding="utf-8", newline="") as handle:
        return [
            QueryRow(
                order=int(row["order"]),
                query_id=row["id"],
                tier=row["tier"],
                category=row["category"],
                kind=row["kind"],
                expectation=row["expectation"],
                expected_count=row["expected_count"],
                expected_ask=row["expected_ask"],
                path=row["path"],
                requirements=_csv_ids(row["requirements"]),
                policies=_csv_ids(row["policies"]),
            )
            for row in csv.DictReader(handle)
        ]


def _codes(values: Iterable[str], empty: str = "None declared") -> str:
    items = list(values)
    return ", ".join(f"`{item}`" for item in items) if items else empty


def _front_matter(title: str, source: str) -> list[str]:
    return [
        f"# {title}",
        "",
        "> Generated reference for release v3.0.0. Do not edit individual",
        "> entries by hand. Regenerate with",
        "> `.venv/bin/python tools/generate_reference_docs.py`.",
        "",
        f"Canonical source: `{source}`.",
        "",
    ]


def requirements_document(graph: Graph, queries: list[QueryRow]) -> str:
    lines = _front_matter(
        "Functional, non-functional and validation requirements",
        "ontology/legacy/smartcity_continuum-v3.0.0.ttl",
    )
    lines.extend(
        [
            "This manual lists every requirement represented by the executable",
            "ontology. Links are direct RDF traceability assertions; the query",
            "coverage list is derived from `queries/catalog.csv`.",
            "",
            "| Family | Expected count |",
            "|---|---:|",
            "| Functional (`RF`) | 72 |",
            "| Non-functional (`RNF`) | 39 |",
            "| Validation (`RV`) | 5 |",
            "| **Total** | **116** |",
            "",
        ]
    )
    by_requirement: dict[str, list[str]] = {}
    for query in queries:
        for requirement in query.requirements:
            by_requirement.setdefault(requirement, []).append(query.query_id)
    for heading, prefix, requirement_type in REQUIREMENT_GROUPS:
        resources = [
            item
            for item in _ids(graph, EX.requirementIdentifier, prefix)
            if (item, RDF.type, requirement_type) in graph
        ]
        lines.extend([f"## {heading}", ""])
        for resource in resources:
            identifier = _literal(graph, resource, EX.requirementIdentifier)
            label = _label(graph, resource)
            statement = _literal(graph, resource, EX.requirementStatement)
            policies = sorted(
                (_ident(item) for item in graph.objects(resource, EX.tracedToPolicy)),
                key=_natural_key,
            )
            mechanisms = sorted(
                (
                    _ident(item)
                    for item in graph.objects(resource, EX.tracedToMechanism)
                ),
                key=_natural_key,
            )
            query_ids = sorted(by_requirement.get(identifier, []), key=_natural_key)
            lines.extend(
                [
                    f"### {identifier} — {label}",
                    "",
                    statement,
                    "",
                    f"- Direct policies: {_codes(policies)}",
                    f"- Direct mechanisms: {_codes(mechanisms)}",
                    f"- Catalogued queries: {_codes(query_ids)}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def policies_document(graph: Graph, queries: list[QueryRow]) -> str:
    lines = _front_matter(
        "Policies and enforcement mechanisms",
        "ontology/legacy/smartcity_continuum-v3.0.0.ttl",
    )
    lines.extend(
        [
            "The release declares 79 policies in 12 categories and 55",
            "enforcement mechanisms. Hard constraints are applied before",
            "optimization: effective authorization is the most restrictive",
            "intersection of consent, semantic contract, zone, security and",
            "resource eligibility.",
            "",
            "## Policy categories",
            "",
            "| Category | Label |",
            "|---|---|",
        ]
    )
    categories = sorted(
        graph.subjects(RDF.type, EX.PolicyCategory), key=lambda item: _label(graph, item)
    )
    for category in categories:
        lines.append(f"| `{_ident(category)}` | {_label(graph, category)} |")
    lines.extend(["", "## Policies", ""])
    by_policy: dict[str, list[str]] = {}
    for query in queries:
        for policy in query.policies:
            by_policy.setdefault(policy, []).append(query.query_id)
    policies = _ids(graph, EX.policyIdentifier, "P-")
    for resource in policies:
        identifier = _literal(graph, resource, EX.policyIdentifier)
        policy_type = next(graph.objects(resource, EX.hasPolicyType), None)
        category = next(graph.objects(resource, EX.belongsToPolicyCategory), None)
        requirements = sorted(
            (_ident(item) for item in graph.objects(resource, EX.relatedRequirement)),
            key=_natural_key,
        )
        mechanisms = sorted(
            (_ident(item) for item in graph.objects(resource, EX.recommendedMechanism)),
            key=_natural_key,
        )
        lines.extend(
            [
                f"### {identifier} — {_label(graph, resource)}",
                "",
                _literal(graph, resource, EX.hasPolicyStatement),
                "",
                f"- Type: {_label(graph, policy_type)}",
                f"- Category: {_label(graph, category)} (`{_ident(category)}`)",
                f"- Version: `{_literal(graph, resource, EX.policyVersion)}`",
                f"- Related requirements: {_codes(requirements)}",
                f"- Recommended mechanisms: {_codes(mechanisms)}",
                f"- Catalogued queries: "
                f"{_codes(sorted(by_policy.get(identifier, []), key=_natural_key))}",
                "",
            ]
        )
    lines.extend(["## Enforcement mechanisms", ""])
    for resource in _ids(graph, EX.mechanismIdentifier, "M-"):
        identifier = _literal(graph, resource, EX.mechanismIdentifier)
        supported = sorted(
            (_ident(item) for item in graph.objects(resource, EX.supportsPolicy)),
            key=_natural_key,
        )
        lines.extend(
            [
                f"### {identifier} — {_label(graph, resource)}",
                "",
                _literal(graph, resource, EX.mechanismDescription),
                "",
                f"- Supported policies: {_codes(supported)}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def queries_document(queries: list[QueryRow]) -> str:
    lines = _front_matter(
        "SPARQL query battery",
        "queries/catalog.csv and queries/**/*.rq",
    )
    lines.extend(
        [
            "The battery contains 35 BASE queries and 80 EXT queries. Every",
            "entry below is executed by the validation gate and by cumulative",
            "and scalability benchmarks unless a scientific experiment",
            "explicitly selects a subset.",
            "",
            "## Interpretation",
            "",
        ]
    )
    for kind, meaning in QUERY_KIND_HELP.items():
        lines.append(f"- `{kind}`: {meaning}")
    lines.extend(
        [
            "",
            "A zero-row violation result is evidence only after `EXT-Q01`,",
            "`EXT-Q02`, `EXT-Q05`, `EXT-Q76` and `EXT-Q77` establish release",
            "identity, coverage, scenarios, acceptance parameters and campaign",
            "readiness. `EXT-Q76` and `EXT-Q77` are review gates and may",
            "legitimately report pending configuration.",
            "",
            "## Run the battery",
            "",
            "```bash",
            ".venv/bin/continuum-bench validate",
            ".venv/bin/continuum-bench benchmark cumulative --python-only",
            ".venv/bin/continuum-bench benchmark scalability --python-only",
            "```",
            "",
            "## Complete catalog",
            "",
        ]
    )
    for query in queries:
        expectation = query.expectation
        if query.expected_count:
            expectation += f"; reference count `{query.expected_count}`"
        if query.expected_ask:
            expectation += f"; reference ASK `{query.expected_ask}`"
        purpose = CATEGORY_HELP.get(query.category, query.category)
        relative_path = "../../" + query.path
        lines.extend(
            [
                f"### {query.query_id} — {query.category} / {query.kind}",
                "",
                f"Evaluates {purpose} using the executable query in "
                f"[`{query.path}`]({relative_path}).",
                "",
                f"- Order: `{query.order}`",
                f"- Tier: `{query.tier}`",
                f"- Category: `{query.category}`",
                f"- Kind: `{query.kind}`",
                f"- Expectation: {expectation}",
                f"- Requirements: {_codes(query.requirements)}",
                f"- Policies: {_codes(query.policies)}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _term_rows(graph: Graph, rdf_type: URIRef) -> list[URIRef]:
    return sorted(
        {item for item in graph.subjects(RDF.type, rdf_type) if isinstance(item, URIRef)},
        key=lambda item: (_ident(item).lower(), str(item)),
    )


def _term_table(graph: Graph, resources: Iterable[URIRef]) -> list[str]:
    lines = ["| Term | English label |", "|---|---|"]
    for resource in resources:
        lines.append(f"| `{_ident(resource)}` | {_label(graph, resource)} |")
    return lines


def ontology_document(graph: Graph) -> str:
    classes = _term_rows(graph, OWL.Class)
    object_properties = _term_rows(graph, OWL.ObjectProperty)
    datatype_properties = _term_rows(graph, OWL.DatatypeProperty)
    annotation_properties = _term_rows(graph, OWL.AnnotationProperty)
    ontologies = _term_rows(graph, OWL.Ontology)
    lines = _front_matter(
        "Continuum Monitoring Ontology v3.0.0 reference",
        "ontology/legacy/smartcity_continuum-v3.0.0.ttl",
    )
    lines.extend(
        [
            "## Scope",
            "",
            "The ontology models policy-aware monitoring and adaptation across",
            "IoT, mist, edge, fog and cloud. The reusable core covers topology,",
            "temporal state, consent, contracts, authorization, trust, policy",
            "governance, MAPE-K adaptation, delegation, model selection,",
            "federated learning, audit and validation. The wellbeing domain",
            "adds wearables, physiological observations, stress and sleep.",
            "",
            "Hard constraints are evaluated before optimization. Consent,",
            "contract, zone and security remain independent normative sources.",
            "Decisions are reified so their inputs, alternatives, selected tier,",
            "policies, trust evidence and resulting action can be audited.",
            "",
            "## Standards and serialization",
            "",
            "- RDF 1.1 and Turtle for serialization.",
            "- OWL 2 DL modeling, with an optional HermiT release check.",
            "- SHACL for closed-world structural validation.",
            "- SPARQL 1.1 for inventory, reports, review gates and violations.",
            "- SOSA/SSN, SAREF, FOAF and GeoSPARQL reuse where applicable.",
            "",
            "## Runtime modules",
            "",
            "| Area | Runtime artefacts |",
            "|---|---|",
            "| Core schema | `ontology/core/schema.ttl` |",
            "| Shared modules | `ontology/modules/*.ttl` |",
            "| Wellbeing extension | `ontology/domains/wellbeing/*.ttl` |",
            "| SHACL constraints | `ontology/shapes/*.ttl` |",
            "| Reference individuals | `ontology/examples/reference-system.ttl` |",
            "| Tier profiles | `ontology/profiles/*.ttl` |",
            "| Protégé source | `ontology/legacy/smartcity_continuum-v3.0.0.ttl` |",
            "",
            "## Release inventory",
            "",
            f"- Ontology declarations: **{len(ontologies)}**",
            f"- OWL classes: **{len(classes)}**",
            f"- Object properties: **{len(object_properties)}**",
            f"- Datatype properties: **{len(datatype_properties)}**",
            f"- Annotation properties: **{len(annotation_properties)}**",
            "- Requirements: **116** (`72 RF + 39 RNF + 5 RV`)",
            "- Policies: **79**",
            "- Mechanisms: **55**",
            "- Scenarios: **17**",
            "- SPARQL queries: **115**",
            "",
            "## Validation workflow",
            "",
            "```bash",
            ".venv/bin/continuum-bench validate",
            "python3 tools/check_owl_consistency.py --require-dl-profile \\",
            "  --output outputs/validation/ontology-hermit.json",
            "```",
            "",
            "The first command validates parsing, release contracts, query",
            "expectations, SHACL, RDFLib RDFS/OWL RL profiles and distributed",
            "fragment reconstruction. The second is the independent OWL 2 DL",
            "consistency/profile gate and requires Java plus Protégé/HermiT.",
            "",
            "## Known limits",
            "",
            "- Open-world OWL consistency is not equivalent to SHACL or",
            "  zero-row violation-query compliance.",
            "- Acceptance review queries `EXT-Q76` and `EXT-Q77` identify",
            "  campaign parameters that must be supplied before publication.",
            "- Distributed profiles are materialized locally; the benchmark",
            "  does not implement runtime resolution of remote `owl:imports`.",
            "- The wellbeing vocabulary is a domain extension and is not",
            "  required by continuum deployments in other application domains.",
            "",
            "## Complete class catalog",
            "",
            *_term_table(graph, classes),
            "",
            "## Complete object-property catalog",
            "",
            *_term_table(graph, object_properties),
            "",
            "## Complete datatype-property catalog",
            "",
            *_term_table(graph, datatype_properties),
            "",
            "## Complete annotation-property catalog",
            "",
            *_term_table(graph, annotation_properties),
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def generate(output: Path) -> list[Path]:
    graph = Graph().parse(ONTOLOGY)
    queries = _queries()
    documents = {
        "REQUIREMENTS.md": requirements_document(graph, queries),
        "POLICIES.md": policies_document(graph, queries),
        "SPARQL_QUERIES.md": queries_document(queries),
        "ONTOLOGY_REFERENCE.md": ontology_document(graph),
    }
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, content in documents.items():
        path = output / name
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate English v3 reference manuals"
    )
    parser.add_argument("--output", type=Path, default=REFERENCE)
    args = parser.parse_args(argv)
    for path in generate(args.output.resolve()):
        print(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
