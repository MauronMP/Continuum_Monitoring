from rdflib import Graph, Literal, Namespace, RDF
from rdflib.compare import isomorphic
from rdflib.namespace import XSD

from continuum_bench.ontology import load_graph
from continuum_bench.partitioning import (
    ROLES,
    build_fragments,
    build_role_graph,
    privacy_violations,
)
from continuum_bench.queries import execute_query_detailed, load_catalog
from continuum_bench.synthetic import add_synthetic_data


EX = Namespace("http://example.org/smartcity#")

SH = Namespace("http://www.w3.org/ns/shacl#")


def test_fragments_reconstruct_monolithic_graph(config):
    expected = load_graph(
        config.resolve(path) for path in config.ontology_files
    )
    add_synthetic_data(expected, 5, config.seed)
    fragments = build_fragments(config, 5)

    assert set(fragments.graphs) == set(ROLES)
    assert isomorphic(fragments.union(), expected)


def test_cloud_and_fog_pass_synthetic_privacy_gate(config):
    fragments = build_fragments(config, 5)

    assert privacy_violations(
        fragments.graphs["cloud"],
        "cloud",
        fragments.sensitive_resources,
    ) == []
    assert privacy_violations(
        fragments.graphs["fog"],
        "fog",
        fragments.sensitive_resources,
    ) == []


def test_reference_links_to_private_objects_stay_at_their_authority(config):
    fragments = build_fragments(config, 0)
    private_link = (EX.Eval_S5, EX.evaluatesNode, EX.MobileA)
    containing_roles = {
        role
        for role, graph in fragments.graphs.items()
        if private_link in graph
    }

    assert len(containing_roles) == 1
    assert next(iter(containing_roles)).startswith("edge")

    cloud_with_leak = fragments.graphs["cloud"] + Graph()
    cloud_with_leak.add(private_link)
    violations = privacy_violations(
        cloud_with_leak,
        "cloud",
        fragments.sensitive_resources,
    )
    assert any("evaluatesNode" in violation for violation in violations)


def test_q17_and_q19_edge_union_matches_monolith(config):
    users = 10
    monolith = load_graph(
        config.resolve(path) for path in config.ontology_files
    )
    add_synthetic_data(monolith, users, config.seed)
    fragments = build_fragments(config, users)
    specs = {
        spec.id: spec
        for spec in load_catalog(
            config.resolve(config.query_catalog),
            config.root,
        )
    }

    for query_id in ("BASE-Q17", "BASE-Q19"):
        expected = execute_query_detailed(monolith, specs[query_id])
        edge_results = [
            execute_query_detailed(fragments.graphs[role], specs[query_id])
            for role in ("edge1", "edge2", "edge3")
        ]
        merged_keys = {
            key
            for result in edge_results
            for key in result.result_keys
        }

        assert merged_keys == set(expected.result_keys)
        assert len(expected.result_keys) == len(set(expected.result_keys))


def test_single_authority_queries_preserve_complete_bindings(config):
    monolith = load_graph(
        config.resolve(path) for path in config.ontology_files
    )
    add_synthetic_data(monolith, 10, config.seed)
    fragments = build_fragments(config, 10)
    specs = {
        spec.id: spec
        for spec in load_catalog(
            config.resolve(config.query_catalog),
            config.root,
        )
    }

    for query_id, role in (
        ("BASE-Q22", "fog"),
        ("BASE-Q33", "fog"),
        ("EXT-Q03", "cloud"),
        ("EXT-Q25", "cloud"),
    ):
        expected = execute_query_detailed(monolith, specs[query_id])
        actual = execute_query_detailed(
            fragments.graphs[role],
            specs[query_id],
        )

        assert sorted(actual.result_keys) == sorted(expected.result_keys)


def test_single_authority_aggregates_are_exact_without_synthetic_data(config):
    monolith = load_graph(
        config.resolve(path) for path in config.ontology_files
    )
    fragments = build_fragments(config, 0)
    specs = {
        spec.id: spec
        for spec in load_catalog(
            config.resolve(config.query_catalog),
            config.root,
        )
    }

    for query_id, role in (
        ("BASE-Q33", "fog"),
        ("EXT-Q03", "cloud"),
    ):
        expected = execute_query_detailed(monolith, specs[query_id])
        actual = execute_query_detailed(
            fragments.graphs[role],
            specs[query_id],
        )

        assert sorted(actual.result_keys) == sorted(expected.result_keys)


def test_resource_aggregate_normalizes_equal_numeric_lexical_forms(config):
    spec = next(
        spec
        for spec in load_catalog(
            config.resolve(config.query_catalog),
            config.root,
        )
        if spec.id == "BASE-Q33"
    )
    node = EX.TestCloudNode
    state_integer = EX.TestIntegerState
    state_decimal = EX.TestDecimalState
    triples = [
        (node, RDF.type, EX.CloudNode),
        (node, EX.hasNodeState, state_integer),
        (
            state_integer,
            EX.resourceUsagePercent,
            Literal(25, datatype=XSD.integer),
        ),
        (node, EX.hasNodeState, state_decimal),
        (
            state_decimal,
            EX.resourceUsagePercent,
            Literal("25.0", datatype=XSD.decimal),
        ),
    ]
    forward = Graph()
    reverse = Graph()
    for triple in triples:
        forward.add(triple)
    for triple in reversed(triples):
        reverse.add(triple)

    expected = execute_query_detailed(forward, spec)
    actual = execute_query_detailed(reverse, spec)

    assert actual.result_keys == expected.result_keys


def test_role_placement_keeps_shapes_at_cloud_and_domain_at_edges(config):
    fragments = build_fragments(config, 0)

    assert any(
        fragments.graphs["cloud"].triples((None, RDF.type, SH.NodeShape))
    )
    assert not any(
        fragments.graphs["fog"].triples((None, RDF.type, SH.NodeShape))
    )
    assert not any(
        fragments.graphs["edge1"].triples((None, RDF.type, SH.NodeShape))
    )
    assert (
        fragments.substrate_triples_by_role["fog"]
        < fragments.substrate_triples_by_role["cloud"]
    )
    assert fragments.placement_profiles["edge1"].endswith(
        "ontology/profiles/edge.ttl"
    )


def test_role_only_build_is_equivalent_to_full_fragment(config):
    full = build_fragments(config, 5)

    for role in ROLES:
        graph, descriptor = build_role_graph(config, role, 5)

        assert isomorphic(graph, full.graphs[role])
        assert set(descriptor.graphs) == {role}
        assert descriptor.substrate_triples == full.substrate_triples
        assert descriptor.reference_triples == full.reference_triples
        assert descriptor.synthetic_triples == full.synthetic_triples


def test_role_only_build_does_not_call_five_fragment_builders(
    config,
    monkeypatch,
):
    from continuum_bench import partitioning

    monkeypatch.setattr(
        partitioning,
        "_reference_fragments",
        lambda *args: (_ for _ in ()).throw(
            AssertionError("must not build all reference fragments")
        ),
    )
    monkeypatch.setattr(
        partitioning,
        "_synthetic_fragments",
        lambda *args: (_ for _ in ()).throw(
            AssertionError("must not build all synthetic fragments")
        ),
    )

    graph, descriptor = build_role_graph(config, "edge1", 5)

    assert len(graph) > 0
    assert descriptor.synthetic_triples > 0
