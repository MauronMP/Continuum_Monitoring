from dataclasses import replace
import os

import pytest

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD
from rdflib.namespace import DCTERMS, OWL

from continuum_bench.ontology import (
    contradiction_count,
    datatype_range_errors,
    load_graph,
    validate_shacl,
)
from continuum_bench.reasoners import available_reasoners, materialize
from continuum_bench.queries import execute_query, load_catalog
from continuum_bench.synthetic import add_synthetic_data
from continuum_bench import validation

SH = Namespace("http://www.w3.org/ns/shacl#")
EX = Namespace("http://example.org/monitoringcontinuum#")


@pytest.mark.parametrize("language", ["es", "en"])
def test_requirement_language_literal_is_not_an_xsd_string(language):
    graph = Graph()
    graph.add((EX.requirementStatement, RDF.type, OWL.DatatypeProperty))
    graph.add((EX.requirementStatement, RDFS.range, XSD.string))
    graph.add((EX["RF-22"], EX.requirementStatement,
               Literal("The system must support federated learning.", lang=language)))

    # This is exactly the two-axiom Protégé explanation. No explicit bottom
    # instance exists, but the datatype clash must fail validation anyway.
    assert contradiction_count(graph) == 0
    errors = datatype_range_errors(graph)
    assert len(errors) == 1
    assert errors[0]["subject"] == str(EX["RF-22"])
    assert errors[0]["range"] == str(XSD.string)


def test_datatype_guard_respects_subproperties_and_string_subtypes():
    graph = Graph()
    graph.add((EX.description, RDFS.subPropertyOf, EX.requirementStatement))
    graph.add((EX.requirementStatement, RDFS.range, XSD.string))
    graph.add((EX.a, EX.description, Literal("A valid token", datatype=XSD.token)))
    graph.add((EX.age, RDFS.range, XSD.integer))
    graph.add((EX.a, EX.age, Literal(1, datatype=XSD.int)))
    assert datatype_range_errors(graph) == []

    graph.add((EX.a, EX.description, Literal("English is still a langString", lang="en")))
    assert len(datatype_range_errors(graph)) == 1


def test_modular_ontology_is_english_and_datatype_safe(config):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    assert datatype_range_errors(graph) == []
    assert (URIRef("http://example.org/monitoringcontinuum"), DCTERMS.language,
            Literal("en")) in graph
    assert {value.language for value in graph.objects()
            if isinstance(value, Literal)} <= {None, "en"}
    for property_, expected in (
        (EX.requirementStatement, 116),
        (EX.hasPolicyStatement, 79),
        (EX.mechanismDescription, 55),
    ):
        values = list(graph.objects(None, property_))
        assert len(values) == expected
        assert all(value.language is None and value.datatype in (None, XSD.string)
                   for value in values)
        assert not any(str(value).startswith(("El sistema", "Toda ", "Todo ",
                                              "La ", "Las ", "Los ", "Debe "))
                       for value in values)
    assert str(graph.value(EX["RF-22"], EX.requirementStatement)) == (
        "The system must support federated or hierarchical learning between "
        "devices and Edge, Fog and Cloud nodes."
    )
    assert str(graph.value(EX["P-CONS-04"], RDFS.label)) == (
        "Effective authorization and inconsistencies"
    )


def test_validation_rejects_inferred_datatype_clash_without_bottom(config, monkeypatch):
    def corrupt_materialization(source, reasoner):
        result = materialize(source, reasoner)
        result.graph.add((EX["RF-22"], EX.requirementStatement,
                          Literal("The system must support FL.", lang="en")))
        return result

    monkeypatch.setattr(validation, "materialize", corrupt_materialization)
    report = validation.validate_project(replace(config, reasoners=("rdfs",)))
    assert report["datatype_range_errors"] == []
    assert report["reasoners"]["rdfs"]["owl_nothing_instances"] == 0
    assert report["reasoners"]["rdfs"]["datatype_range_errors"]
    assert report["owl_dl_consistency"]["status"] == "not_checked"
    assert not report["ok"]


def test_policy_zone_types_use_explicit_owl2_punning(config):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    assert (EX.appliesToZoneType, RDF.type, OWL.ObjectProperty) in graph
    assert (EX.appliesToZoneType, RDFS.range, EX.ZoneType) in graph
    assert (EX.appliesToZoneType, RDFS.range, OWL.Class) not in graph
    for zone in (EX.UrbanZone, EX.RuralZone, EX.RestrictedZone):
        for type_ in (OWL.Class, OWL.NamedIndividual, EX.ZoneType):
            assert (zone, RDF.type, type_) in graph
    assert (XSD.duration, RDF.type, RDFS.Datatype) in graph
    assert (SH.NodeShape, RDF.type, OWL.Class) in graph
    for predicate in set(graph.predicates()):
        if str(predicate).startswith(str(SH)):
            assert (predicate, RDF.type, OWL.AnnotationProperty) in graph


def test_modular_graph_contains_schema_and_reference_data(config):
    modular = load_graph(config.resolve(path) for path in config.ontology_files)
    schema_types = {
        OWL.Class,
        OWL.ObjectProperty,
        OWL.DatatypeProperty,
        OWL.AnnotationProperty,
        OWL.NamedIndividual,
    }
    modular_terms = {
        subject
        for subject, type_ in modular.subject_objects(RDF.type)
        if type_ in schema_types and isinstance(subject, URIRef)
    }
    assert EX.ComputationalNode in modular_terms
    assert EX.Policy in modular_terms
    assert EX.Requirement in modular_terms
    assert EX.QuerySpecification in modular_terms
    assert (EX.UserA, RDF.type, EX.User) in modular
    assert (EX["P-CONS-01"], RDF.type, EX.Policy) in modular


def test_reference_data_conforms_to_shacl(config):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    conforms, report = validate_shacl(
        graph,
        (config.resolve(path) for path in config.shape_files),
    )
    assert conforms, report


def test_release_synthetic_data_conforms_to_shacl(config):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    add_synthetic_data(graph, 3, config.seed)

    conforms, report = validate_shacl(
        graph,
        (config.resolve(path) for path in config.shape_files),
    )

    assert conforms, report


def test_release_synthetic_data_does_not_trigger_violation_queries(config):
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


@pytest.mark.parametrize("reasoner", [
    "rdfs",
    *[pytest.param(name, marks=pytest.mark.skipif(
        os.environ.get("CONTINUUM_TEST_NATIVE_OWL") != "1",
        reason="canonical native ontology check requires CONTINUUM_TEST_NATIVE_OWL=1",
    )) for name in ("hermit", "openllet", "jfact", "konclude")],
])
def test_configured_reasoner_profiles_have_no_explicit_contradictions(config, reasoner):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    assert len(available_reasoners()) >= 3
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
    ex = Namespace("http://example.org/monitoringcontinuum#")

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
