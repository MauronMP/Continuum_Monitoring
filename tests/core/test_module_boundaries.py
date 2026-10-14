"""Regression gates for the modular monitoring ontology and namespace migration."""
from pathlib import Path
import runpy

from rdflib import Graph, Namespace, OWL, RDF, RDFS, XSD
from rdflib.collection import Collection

from continuum_bench.ontology import load_graph

MC = Namespace('http://example.org/monitoringcontinuum#')
SOSA = Namespace('http://www.w3.org/ns/sosa/')


def test_module_imports_are_closed_and_match_physical_profiles(root):
    audit = runpy.run_path(str(root / 'tools/audit_ontology_modules.py'))['audit']
    result = audit(root)
    assert result['ok'], result['errors']
    fog = result['profile_closures']['ontology/profiles/fog.ttl']
    assert not any('/wellbeing/' in p or p.endswith('/federation.ttl') for p in fog)
    assert 'ontology/modules/contracts.ttl' in result['core_closure']


def test_consent_domains_cover_the_subjects_used_by_the_model(config):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    for property_, required in [(MC.hasConsentRange, {MC.ConsentRecord}),
                               (MC.hasProcessingPurpose, {MC.ConsentRecord, MC.Service}),
                               (MC.requiresConsentRange, {MC.ModelTier})]:
        domain = graph.value(property_, RDFS.domain)
        members = set(Collection(graph, graph.value(domain, OWL.unionOf)))
        assert required <= members
    assert (MC.DirectIdentifier, OWL.disjointWith, MC.PseudonymousIdentifier) in graph
    assert (MC.DirectIdentifier, OWL.disjointWith, MC.AnonymousIdentifier) in graph
    assert not list(graph.triples((None, MC.expiresOnRecoveryOf, None)))


def test_controlled_identity_constraints_are_not_example_only(root):
    reference = Graph().parse(root / 'ontology/examples/reference-system.ttl')
    vocabulary = Graph().parse(root / 'ontology/core/vocabulary.ttl')
    assert not list(reference.subjects(RDF.type, OWL.AllDifferent))
    assert len(set(vocabulary.subjects(RDF.type, OWL.AllDifferent))) == 3


def test_observations_are_numeric_without_invented_units(config):
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    observations = list(graph.subject_objects(SOSA.hasSimpleResult))
    assert len(observations) == 3
    for observation, value in observations:
        assert value.datatype in {XSD.integer, XSD.decimal}
        assert str(graph.value(observation, MC.measurementUnitStatus)) == 'not-recorded-in-source'
        sensor = graph.value(observation, SOSA.madeBySensor)
        observable = graph.value(observation, SOSA.observedProperty)
        assert (observable, RDF.type, SOSA.ObservableProperty) in graph
        assert (sensor, SOSA.observes, observable) in graph
        assert not list(graph.objects(observation, MC.hasMeasurementUnit))


def test_multiple_policy_categories_validate_and_are_all_documented(config, root):
    from continuum_bench.ontology import validate_shacl
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    policy = MC['P-CONS-01']
    original = set(graph.objects(policy, MC.belongsToPolicyCategory))
    additional = next(c for c in sorted(graph.subjects(RDF.type, MC.PolicyCategory)) if c not in original)
    graph.add((policy, MC.belongsToPolicyCategory, additional))
    conforms, report = validate_shacl(graph, [config.resolve(p) for p in config.shape_files])
    assert conforms, report
    from continuum_bench.queries import load_catalog, execute_query
    inventory = next(q for q in load_catalog(config.resolve(config.query_catalog), config.root) if q.id == "EXT-Q03")
    assert execute_query(graph, inventory).result_count == len(set(graph.subjects(RDF.type, MC.Policy))) + 1
    generator = runpy.run_path(str(root / 'tools/generate_reference_docs.py'))
    text = generator['policies_document'](graph, [])
    section = text.split('### P-CONS-01 —', 1)[1].split('\n### ', 1)[0]
    for category in original | {additional}:
        assert str(category).split('#')[-1] in section
    # Cross-category membership does not waive the mandatory classification.
    graph.remove((policy, MC.belongsToPolicyCategory, None))
    conforms, report = validate_shacl(graph, [config.resolve(p) for p in config.shape_files])
    assert not conforms
