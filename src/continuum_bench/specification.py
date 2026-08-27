"""Machine-checkable contract for the canonical ontology release."""

from __future__ import annotations

from typing import Any, Iterable

from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.namespace import OWL

from .queries import QueryMeasurement, QuerySpec
from .reasoners import REASONING_CONTRACT
from .environment import installed_versions


EX = Namespace("http://example.org/smartcity#")
ONTOLOGY_IRI = URIRef("http://example.org/smartcity")
ONTOLOGY_VERSION = "3.0.0"
EXPECTED_QUERY_IDS = frozenset(
    {
        *{f"BASE-Q{i:02d}" for i in range(1, 36)},
        *{f"EXT-Q{i:02d}" for i in range(1, 81)},
    }
)
EXPECTED_ENTITY_COUNTS = {
    "functional_requirements": (EX.FunctionalRequirement, 72),
    "nonfunctional_requirements": (EX.NonFunctionalRequirement, 39),
    "validation_requirements": (EX.ValidationRequirement, 5),
    "policies": (EX.Policy, 79),
    "mechanisms": (EX.MechanismSpecification, 55),
    "scenarios": (EX.Scenario, 17),
    "policy_categories": (EX.PolicyCategory, 12),
}
ACCEPTANCE_PRECONDITIONS = (
    "EXT-Q01",
    "EXT-Q02",
    "EXT-Q05",
    "EXT-Q76",
    "EXT-Q77",
)


def release_identity() -> dict[str, Any]:
    """Return stable provenance fields shared by every benchmark output."""

    return {
        "ontology_version": ONTOLOGY_VERSION,
        "query_contract": "BASE-Q01..BASE-Q35;EXT-Q01..EXT-Q80",
        "query_count": len(EXPECTED_QUERY_IDS),
        "policy_artifact": "POLICIES-REV-01",
        "reasoning_contract": REASONING_CONTRACT,
        "runtime_versions": installed_versions(),
    }


def _identifier_values(graph: Graph, predicate: URIRef) -> set[str]:
    return {str(value) for value in graph.objects(None, predicate)}


def validate_release_contract(
    graph: Graph,
    specs: Iterable[QuerySpec],
) -> dict[str, Any]:
    """Check version, inventories and query-to-policy traceability."""

    specs = list(specs)
    errors: list[str] = []
    versions = sorted(
        str(value) for value in graph.objects(ONTOLOGY_IRI, OWL.versionInfo)
    )
    if ONTOLOGY_VERSION not in versions:
        errors.append(
            f"ontology version {ONTOLOGY_VERSION!r} not found: {versions}"
        )

    query_ids = {spec.id for spec in specs}
    if query_ids != EXPECTED_QUERY_IDS:
        errors.append(
            "query inventory mismatch: "
            f"missing={sorted(EXPECTED_QUERY_IDS - query_ids)}, "
            f"extra={sorted(query_ids - EXPECTED_QUERY_IDS)}"
        )

    counts: dict[str, int] = {}
    for name, (class_, expected) in EXPECTED_ENTITY_COUNTS.items():
        actual = len(set(graph.subjects(RDF.type, class_)))
        counts[name] = actual
        if actual != expected:
            errors.append(f"{name}: expected {expected}, got {actual}")

    requirement_ids = _identifier_values(graph, EX.requirementIdentifier)
    policy_ids = _identifier_values(graph, EX.policyIdentifier)
    referenced_requirements = {
        identifier for spec in specs for identifier in spec.requirements
    }
    referenced_policies = {
        identifier for spec in specs for identifier in spec.policies
    }
    unknown_requirements = sorted(referenced_requirements - requirement_ids)
    unknown_policies = sorted(referenced_policies - policy_ids)
    unreferenced_requirements = sorted(requirement_ids - referenced_requirements)
    unreferenced_policies = sorted(policy_ids - referenced_policies)
    if unknown_requirements:
        errors.append(
            f"catalog references unknown requirements: {unknown_requirements}"
        )
    if unknown_policies:
        errors.append(f"catalog references unknown policies: {unknown_policies}")

    missing_metadata = sorted(
        spec.id
        for spec in specs
        if not spec.purpose or not spec.requirements or not spec.policies
    )
    if missing_metadata:
        errors.append(f"queries without traceability metadata: {missing_metadata}")

    return {
        "ok": not errors,
        "ontology_iri": str(ONTOLOGY_IRI),
        "expected_version": ONTOLOGY_VERSION,
        "observed_versions": versions,
        "query_count": len(query_ids),
        "entity_counts": counts,
        "referenced_requirement_count": len(referenced_requirements),
        "referenced_policy_count": len(referenced_policies),
        "requirement_traceability_coverage": (
            len(referenced_requirements) / len(requirement_ids)
            if requirement_ids
            else 1.0
        ),
        "policy_traceability_coverage": (
            len(referenced_policies) / len(policy_ids)
            if policy_ids
            else 1.0
        ),
        # These are coverage gaps in the supplied query catalogue, not unknown
        # identifiers and therefore not structural release errors.  Reporting
        # them prevents an 87% mapping from being presented as full policy or
        # requirement coverage in a scientific evaluation.
        "unreferenced_requirements": unreferenced_requirements,
        "unreferenced_policies": unreferenced_policies,
        "unknown_requirements": unknown_requirements,
        "unknown_policies": unknown_policies,
        "errors": errors,
    }


def acceptance_status(
    specs: Iterable[QuerySpec],
    measurements: Iterable[QueryMeasurement],
) -> dict[str, Any]:
    """Report whether zero-row violation queries may support compliance claims.

    The v3 reference data intentionally exposes acceptance/campaign debt.  This
    status therefore does not redefine structural validity: it prevents an
    empty violation result from being over-interpreted before EXT-Q01, Q02,
    Q05, Q76 and Q77 meet their acceptance conditions.
    """

    spec_by_id = {spec.id: spec for spec in specs}
    measured = {item.query_id: item for item in measurements}
    checks = {
        "EXT-Q01": measured["EXT-Q01"].result_count >= 6,
        "EXT-Q02": measured["EXT-Q02"].result_count == 3,
        "EXT-Q05": measured["EXT-Q05"].result_count == 17,
        "EXT-Q76": measured["EXT-Q76"].result_count == 0,
        "EXT-Q77": measured["EXT-Q77"].result_count >= 7,
    }
    violation_rows = {
        spec.id: measured[spec.id].result_count
        for spec in spec_by_id.values()
        if spec.kind == "violation"
    }
    return {
        "ready": all(checks.values()),
        "preconditions": list(ACCEPTANCE_PRECONDITIONS),
        "checks": checks,
        "observed": {
            query_id: measured[query_id].result_count
            for query_id in ACCEPTANCE_PRECONDITIONS
        },
        "violation_query_count": len(violation_rows),
        "nonzero_violation_queries": {
            query_id: count
            for query_id, count in violation_rows.items()
            if count
        },
        "compliance_claim_permitted": (
            all(checks.values()) and not any(violation_rows.values())
        ),
        "interpretation": (
            "Structural v3 validation is separate from scientific acceptance; "
            "review queries may expose documented migration debt."
        ),
    }
