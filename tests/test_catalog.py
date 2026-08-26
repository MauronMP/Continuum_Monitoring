from continuum_bench.ontology import load_graph
from continuum_bench.queries import (
    check_expectation,
    execute_query,
    load_catalog,
)


def test_catalog_contains_every_query_once(config):
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    assert len(specs) == 69
    assert len({spec.id for spec in specs}) == 69
    assert {spec.tier for spec in specs} == {"core", "domain"}
    assert {spec.category for spec in specs} == set(config.category_order)
    assert {spec.execution_scope for spec in specs} == {
        "cloud",
        "fog",
        "edges",
        "cloud_edges",
    }
    assert all(spec.authority for spec in specs)
    assert all(spec.privacy_class for spec in specs)
    assert all(spec.merge_strategy for spec in specs)
    q33 = next(spec for spec in specs if spec.id == "BASE-Q33")
    assert q33.execution_scope == "fog"
    assert q33.merge_strategy == "single"


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
