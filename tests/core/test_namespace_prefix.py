"""The public prefix changes notation, never the identity of domain concepts."""
from rdflib import Graph
from rdflib.plugins.sparql import prepareQuery

NAMESPACE = 'http://example.org/monitoringcontinuum#'


def test_ontology_uses_comon_without_changing_entity_iris(root):
    graph = Graph().parse(root/'ontology/modules/foundation.ttl', format='turtle')
    assert str(dict(graph.namespaces())['comon']) == NAMESPACE
    assert any(str(subject) == NAMESPACE+'User' for subject in graph.subjects())
    assert 'mc' not in dict(graph.namespaces())


def test_catalog_queries_declare_and_parse_comon(root):
    from continuum_bench.queries import load_catalog
    queries = load_catalog(root/'queries/catalog.csv', root)
    assert len(queries) == 115
    for spec in queries:
        text = spec.read()
        assert f'PREFIX comon: <{NAMESPACE}>' in text, spec.id
        assert 'PREFIX mc:' not in text, spec.id
        prepareQuery(text)
