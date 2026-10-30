"""Executable boundaries for the explicitly adapted policy/requirement scope."""
import tomllib

from rdflib import Graph, Literal, Namespace, RDF, RDFS

from continuum_bench.ontology import load_graph
from continuum_bench.queries import load_catalog, execute_query
from continuum_bench.reasoners import materialize
from continuum_bench.monitoring.policy_evaluation.config import PolicyRule, ResourceSpec
from continuum_bench.monitoring.policy_evaluation.model import PolicyEngine
from continuum_bench.specification import ONTOLOGY_REVISION

MC = Namespace('http://example.org/monitoringcontinuum#')
SOSA = Namespace('http://www.w3.org/ns/sosa/')


def test_adapted_scope_matches_statements_and_real_query_links(config):
    manifest = tomllib.loads((config.root / 'configs/scope-contracts.toml').read_text())
    graph = load_graph(config.resolve(p) for p in config.ontology_files)
    catalog = {q.id: q for q in load_catalog(config.resolve(config.query_catalog), config.root)}
    assert manifest['ontology_revision'] == ONTOLOGY_REVISION
    assert len(manifest['items']) == 24
    for identifier, item in manifest['items'].items():
        prop = MC.hasPolicyStatement if identifier.startswith('P-') else MC.requirementStatement
        assert str(graph.value(MC[identifier], prop)) == item['statement']
        assert item['original_statement'] != item['statement']
        assert (config.root / item['evidence']).exists()
        assert item['verification_kind'] in {'software-check', 'model-query'}
        for query in item['queries']:
            spec = catalog[query]
            assert identifier in (*spec.requirements, *spec.policies)


def test_domain_specialization_and_supplied_provenance_survive_rdfs(config):
    graph = load_graph(config.resolve(p) for p in config.ontology_files)
    graph.add((MC.AuditWearableType, RDFS.subClassOf, MC.Wearable))
    graph.add((MC.AuditWearable, RDF.type, MC.AuditWearableType))
    graph.add((MC.AuditUser, MC.hasWearable, MC.AuditWearable))
    graph.add((MC.AuditState, MC.derivedFrom, MC.AuditObservation))
    closure = materialize(graph, 'rdfs').graph
    assert (MC.AuditWearable, RDF.type, MC.Wearable) in closure
    assert (MC.AuditUser, MC.hasWearable, MC.AuditWearable) in closure
    assert (MC.AuditState, RDF.type, MC.State) in closure
    assert (MC.AuditObservation, RDF.type, SOSA.Observation) in closure
    assert (MC.AuditState, MC.derivedFrom, MC.AuditObservation) in closure


def test_supplied_context_recomputes_plan_and_never_invents_resource():
    rules = (
        PolicyRule('overload', ('OPS',), ('overload',), ('edge',), ('cpu',), (), 1.0),
        PolicyRule('recover', ('OPS',), ('recovery',), ('mist',), ('cpu',), (), 30.0),
        PolicyRule('no-match', ('NODE',), ('unavailable',), ('fog',), ('cpu',), (), 10.0),
    )
    engine = PolicyEngine((ResourceSpec('edge1', 'edge'), ResourceSpec('mist', 'mist')), rules)
    overload = engine.decide('overload').plan
    recovery = engine.decide('recovery').plan
    assert overload.resources == ('edge1',)
    assert recovery.resources == ('mist',)
    assert recovery.policies == ('recover',)
    assert recovery.sampling_interval_seconds == 30.0
    assert engine.decide('unavailable').plan.resources == ()
    assert engine.decide('unknown').plan.resources == ()
    assert engine.decide('overload').plan == overload


def test_adapted_violation_queries_detect_injected_counterexamples(config):
    graph = load_graph(config.resolve(p) for p in config.ontology_files)
    specs = {q.id: q for q in load_catalog(config.resolve(config.query_catalog), config.root)}
    cases = {
        'EXT-Q34': [(MC.AuditReplication, RDF.type, MC.ReplicationEvent)],
        'EXT-Q72': [(MC.AuditAction, RDF.type, MC.AdaptationAction)],
        'EXT-Q56': [(MC.AuditEvaluation, RDF.type, MC.EvaluationState),
                   (MC.AuditEvaluation, MC.selectedModelTier, MC.CloudModelTier),
                   (MC.AuditEvaluation, MC.evaluationZone, MC.AuditZone),
                   (MC.AuditEvaluation, MC.hasAuthorizationDecision, MC.AuditAuthorization)],
        'EXT-Q37': [(MC.AuditZoneEvaluation, RDF.type, MC.EvaluationState),
                   (MC.AuditZoneEvaluation, MC.evaluationZone, MC.AuditRestricted),
                   (MC.AuditZoneEvaluation, MC.selectedModelTier, MC.CloudModelTier),
                   (MC.AuditRestricted, RDF.type, MC.RestrictedZone)],
    }
    for query, triples in cases.items():
        baseline = execute_query(graph, specs[query]).result_count
        mutated = Graph()
        for triple in graph:
            mutated.add(triple)
        for triple in triples:
            mutated.add(triple)
        assert execute_query(mutated, specs[query]).result_count > baseline, query
