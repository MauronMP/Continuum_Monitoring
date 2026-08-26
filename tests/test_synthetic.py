import pytest
from rdflib import Graph, RDF, RDFS, URIRef

from continuum_bench.synthetic import (
    SYN,
    add_synthetic_data,
    add_synthetic_rules,
    iter_synthetic_triples,
    pad_to_target_triples,
)


def test_synthetic_growth_is_deterministic_and_monotonic():
    first = Graph()
    second = Graph()
    added_10 = add_synthetic_data(first, 10, seed=7)
    added_10_again = add_synthetic_data(second, 10, seed=7)
    assert added_10 == added_10_again
    assert set(first) == set(second)

    larger = Graph()
    added_20 = add_synthetic_data(larger, 20, seed=7)
    assert added_20 > added_10


def test_zero_users_does_not_change_graph():
    graph = Graph()
    graph.add(
        (
            URIRef("urn:test:subject"),
            URIRef("urn:test:predicate"),
            URIRef("urn:test:object"),
        )
    )
    before = set(graph)

    added = add_synthetic_data(graph, users=0, seed=7)

    assert added == 0
    assert set(graph) == before


def test_streamed_triples_are_identical_to_graph_generation():
    triples = list(iter_synthetic_triples(users=10, seed=7))
    graph = Graph()

    added = add_synthetic_data(graph, users=10, seed=7)

    assert len(triples) == len(set(triples))
    assert set(triples) == set(graph)
    assert added == len(triples)


def test_rule_chain_and_exact_triple_padding():
    graph = Graph()

    rule_triples = add_synthetic_rules(graph, rule_count=4)
    padding_triples = pad_to_target_triples(graph, target_triples=25)

    assert rule_triples == 5
    assert padding_triples == 20
    assert len(graph) == 25
    assert (
        SYN["rule-class-00003"],
        RDFS.subClassOf,
        SYN["rule-class-00004"],
    ) in graph
    assert (SYN["rule-probe"], RDF.type, SYN["rule-class-00000"]) in graph


def test_target_triples_rejects_shrinking_the_graph():
    graph = Graph()
    add_synthetic_rules(graph, rule_count=2)

    with pytest.raises(ValueError, match="below current size"):
        pad_to_target_triples(graph, target_triples=1)


def test_neutral_padding_does_not_create_application_users():
    graph = Graph()

    added = pad_to_target_triples(graph, 10, mode="neutral")

    assert added == 10
    assert len(graph) == 10
    assert not any(graph.triples((None, RDF.type, None)))


def test_padding_rejects_unknown_mode():
    with pytest.raises(ValueError, match="padding mode"):
        pad_to_target_triples(Graph(), 10, mode="unknown")
