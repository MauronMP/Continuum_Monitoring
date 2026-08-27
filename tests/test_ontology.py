from dataclasses import replace

from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import OWL

from continuum_bench.ontology import (
    contradiction_count,
    load_graph,
    validate_shacl,
)
from continuum_bench.reasoners import available_reasoners, materialize
from continuum_bench.queries import execute_query, load_catalog
from continuum_bench.synthetic import add_synthetic_data
from continuum_bench import validation

SH = Namespace("http://www.w3.org/ns/shacl#")


def test_modular_graph_preserves_legacy_terms_and_abox(config, root):
    legacy = Graph().parse(
        root / "ontology/legacy/smartcity_continuum-v3.0.0.ttl",
        format="turtle",
    )
    modular = load_graph(config.resolve(path) for path in config.ontology_files)
    schema_types = {
        OWL.Class,
        OWL.ObjectProperty,
        OWL.DatatypeProperty,
        OWL.AnnotationProperty,
        OWL.NamedIndividual,
    }
    legacy_terms = {
        subject
        for subject, type_ in legacy.subject_objects(RDF.type)
        if type_ in schema_types and isinstance(subject, URIRef)
    }
    modular_terms = {
        subject
        for subject, type_ in modular.subject_objects(RDF.type)
        if type_ in schema_types and isinstance(subject, URIRef)
    }
    assert legacy_terms <= modular_terms

    # Stable skolemization changes anonymous node identifiers. Compatibility is
    # therefore checked as an API/ABox contract rather than raw bnode labels.
    meta_types = schema_types | {
        OWL.Ontology,
        SH.NodeShape,
        SH.PropertyShape,
        SH.SPARQLConstraint,
    }
    legacy_individuals = {
        subject
        for subject, type_ in legacy.subject_objects(RDF.type)
        if isinstance(subject, URIRef) and type_ not in meta_types
    }
    missing_abox = {
        triple
        for subject in legacy_individuals
        for triple in legacy.triples((subject, None, None))
        if triple not in modular
    }
    assert missing_abox == set()


def test_reference_data_conforms_to_shacl(config):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    conforms, report = validate_shacl(
        graph,
        (config.resolve(path) for path in config.shape_files),
    )
    assert conforms, report


def test_v3_synthetic_data_conforms_to_shacl(config):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    add_synthetic_data(graph, 3, config.seed)

    conforms, report = validate_shacl(
        graph,
        (config.resolve(path) for path in config.shape_files),
    )

    assert conforms, report


def test_v3_synthetic_data_does_not_trigger_violation_queries(config):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    add_synthetic_data(graph, 3, config.seed)
    specs = load_catalog(
        config.resolve(config.query_catalog),
        config.root,
    )

    failures = {
        spec.id: measurement.result_count
        for spec in specs
        if spec.kind == "violation"
        and (measurement := execute_query(graph, spec)).result_count
    }

    assert failures == {}


def test_three_reasoner_profiles_have_no_explicit_contradictions(config):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    assert len(available_reasoners()) >= 3
    for reasoner in config.reasoners:
        result = materialize(graph, reasoner)
        assert result.output_triples >= result.input_triples
        assert contradiction_count(result.graph) == 0
        specs = load_catalog(config.resolve(config.query_catalog), config.root)
        violations = {
            spec.id: measurement.result_count
            for spec in specs
            if spec.kind == "violation"
            and (measurement := execute_query(result.graph, spec)).result_count
        }
        assert violations == {}, reasoner


def test_validate_rejects_violation_introduced_only_by_reasoning(config, monkeypatch):
    ex = Namespace("http://example.org/smartcity#")

    def corrupt_materialization(source, reasoner):
        result = materialize(source, reasoner)
        result.graph.add((ex.GradientUpdate_S6_A, ex.hasNoiseApplied, Literal(1)))
        return result

    monkeypatch.setattr(validation, "materialize", corrupt_materialization)

    report = validation.validate_project(replace(config, reasoners=("rdfs",)))

    assert report["query_expectation_errors"] == []  # Asserted data is valid.
    assert report["reasoners"]["rdfs"]["owl_nothing_instances"] == 0
    assert any(
        "EXT-Q68" in error
        for error in report["reasoners"]["rdfs"]["violation_query_errors"]
    )
    assert report["ok"] is False
