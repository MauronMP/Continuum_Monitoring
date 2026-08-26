from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.namespace import OWL

from continuum_bench.ontology import (
    contradiction_count,
    load_graph,
    validate_shacl,
)
from continuum_bench.reasoners import available_reasoners, materialize

SH = Namespace("http://www.w3.org/ns/shacl#")


def test_modular_graph_preserves_legacy_terms_and_abox(config, root):
    legacy = Graph().parse(
        root / "ontology/legacy/smartcity_continuum-v2.2.0.ttl",
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

    # Modularization intentionally replaces several anonymous union-domain
    # axioms and evolves SHACL constraints.  Compatibility is therefore an
    # API/ABox contract, not byte-for-byte preservation of old TBox bnodes.
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


def test_three_reasoner_profiles_have_no_explicit_contradictions(config):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    assert len(available_reasoners()) >= 3
    for reasoner in config.reasoners:
        result = materialize(graph, reasoner)
        assert result.output_triples >= result.input_triples
        assert contradiction_count(result.graph) == 0
