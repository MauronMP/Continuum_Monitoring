from collections import defaultdict
import tomllib

from rdflib import OWL, URIRef

from continuum_bench.ontology import load_graph
from continuum_bench.queries import execute_query, load_catalog
from continuum_bench.specification import (
    ONTOLOGY_VERSION,
    acceptance_status,
    validate_release_contract,
)
from tools import migrate_assets


def test_v3_release_inventory_and_traceability(config):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    specs = load_catalog(config.resolve(config.query_catalog), config.root)

    contract = validate_release_contract(graph, specs)

    assert contract["ok"], contract["errors"]
    assert contract["entity_counts"] == {
        "functional_requirements": 72,
        "nonfunctional_requirements": 39,
        "validation_requirements": 5,
        "policies": 79,
        "mechanisms": 55,
        "scenarios": 17,
        "policy_categories": 12,
    }
    assert contract["referenced_requirement_count"] == 102
    assert contract["referenced_policy_count"] == 69
    assert contract["unreferenced_requirements"] == [
        "RF-07",
        "RF-41",
        "RF-44",
        "RF-52",
        "RF-69",
        "RNF-03",
        "RNF-10",
        "RNF-11",
        "RNF-23",
        "RNF-24",
        "RNF-26",
        "RNF-31",
        "RNF-37",
        "RNF-38",
    ]
    assert contract["unreferenced_policies"] == [
        "P-ADAPT-08",
        "P-CONS-06",
        "P-GOV-02",
        "P-MODEL-09",
        "P-NODE-06",
        "P-OPS-04",
        "P-OPS-06",
        "P-VAL-02",
        "P-VAL-05",
        "P-ZONE-04",
    ]
    assert ONTOLOGY_VERSION in {
        str(value)
        for value in graph.objects(
            URIRef("http://example.org/smartcity"),
            OWL.versionInfo,
        )
    }


def test_acceptance_debt_is_reported_without_hiding_structural_validity(config):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    measurements = [execute_query(graph, spec) for spec in specs]

    status = acceptance_status(specs, measurements)

    assert status["checks"]["EXT-Q01"]
    assert status["checks"]["EXT-Q02"]
    assert status["checks"]["EXT-Q05"]
    assert not status["checks"]["EXT-Q76"]
    assert not status["checks"]["EXT-Q77"]
    assert not status["ready"]
    assert status["nonzero_violation_queries"] == {}
    assert not status["compliance_claim_permitted"]


def test_v3_migration_regenerates_the_elastic_execution_plan(config):
    source = migrate_assets.QUERY_SOURCE.read_text(encoding="utf-8")
    generated: dict[str, list[str]] = defaultdict(list)
    for match in migrate_assets.QUERY_RE.finditer(source):
        query_id = match.group(1)
        query = match.group(3).strip() + "\n"
        tier = (
            "domain" if migrate_assets.is_domain_query(query) else "core"
        )
        generated[
            migrate_assets.query_scope(
                query_id,
                tier,
                migrate_assets.category_for(query_id),
            )
        ].append(query_id)

    with (config.root / "queries/execution-plan.toml").open("rb") as handle:
        current = tomllib.load(handle)["scopes"]

    assert {
        scope: set(query_ids) for scope, query_ids in generated.items()
    } == {
        scope: set(query_ids) for scope, query_ids in current.items()
    }
    assert not {
        "edges",
        "edge1",
        "edge2",
        "edge3",
    }.intersection(generated)
