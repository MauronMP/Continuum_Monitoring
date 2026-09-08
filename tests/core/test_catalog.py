from continuum_bench.ontology import load_graph
from continuum_bench.queries import (
    check_expectation,
    execute_query,
    load_catalog,
)


def test_catalog_contains_every_query_once(config):
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    assert len(specs) == 115
    assert len({spec.id for spec in specs}) == 115
    assert {spec.tier for spec in specs} == {"core", "domain"}
    assert {spec.category for spec in specs} == set(config.category_order)
    assert {spec.execution_scope for spec in specs} == {
        "cloud",
        "fog",
        "authorities",
        "authority_key:http://example.org/smartcity#UserA",
        "authority_key:http://example.org/smartcity#UserB",
    }
    assert all(spec.purpose for spec in specs)
    assert all(spec.requirements for spec in specs)
    assert all(spec.policies for spec in specs)
    assert all(spec.expected_count is not None for spec in specs)
    assert all(spec.authority for spec in specs)
    assert all(spec.privacy_class for spec in specs)
    assert all(spec.merge_strategy for spec in specs)
    q80 = next(spec for spec in specs if spec.id == "EXT-Q80")
    assert q80.execution_scope == "cloud"
    assert q80.merge_strategy == "single"


def test_all_queries_execute_and_meet_expectations(config):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    errors = []
    for spec in specs:
        measurement = execute_query(graph, spec)
        error = check_expectation(spec, measurement)
        if error:
            errors.append(error)
    assert errors == []


def test_identifier_inventory_preserves_result_bag_with_bound_types(config):
    from collections import Counter
    from rdflib import Graph
    from continuum_bench.synthetic import add_synthetic_data
    from continuum_bench.reasoners import materialize

    graph = Graph()
    for path in config.ontology_files:
        graph.parse(config.resolve(path), format="turtle")
    add_synthetic_data(graph, 5, 2026)
    optimized = (config.root / "queries/core/security_identity/ext-q26.rq").read_text()
    user = "  ?user a :User ; :hasIdentifier ?identifier .\n"
    types = "  VALUES ?identifierType {\n    :PseudonymousIdentifier :AnonymousIdentifier :DirectIdentifier\n  }\n"
    original = optimized.replace(types + user, user + types)
    assert original != optimized
    for reasoner in ("rdfs", "owlrl", "rdfs_owlrl"):
        closure = materialize(graph, reasoner).graph
        assert Counter(tuple(row) for row in closure.query(optimized)) == Counter(
            tuple(row) for row in closure.query(original)
        )
