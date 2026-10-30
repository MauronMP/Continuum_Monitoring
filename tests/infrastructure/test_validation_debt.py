"""Reviewed validation debt remains unresolved and cannot hide new errors."""
import importlib.util
import tomllib



def _debt_tool(root):
    spec = importlib.util.spec_from_file_location('review_validation_debt', root / 'tools/review_validation_debt.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_debt_review_retains_missing_evidence_and_rejects_unreviewed_gap(config):
    tool = _debt_tool(config.root)
    entries = tomllib.loads((config.root / 'configs/traceability-review.toml').read_text())['items']
    result = tool.review(config, entries)
    assert result['review_complete']
    assert result['warning_count'] == 57
    assert not result['scientific_acceptance_claimed']
    assert len(result['query_coverage_review']) == 16
    entries.pop('RF-69')
    result = tool.review(config, entries)
    assert not result['review_complete']
    assert any('RF-69' in error for error in result['errors'])



def test_debt_review_rejects_invalid_value_on_reviewed_property(config, monkeypatch):
    from rdflib import Literal, Namespace
    tool = _debt_tool(config.root)
    entries = tomllib.loads((config.root / 'configs/traceability-review.toml').read_text())['items']
    original = tool.load_graph
    mc = Namespace('http://example.org/monitoringcontinuum#')

    def corrupt(paths):
        graph = original(paths)
        from rdflib import RDF
        subject = next(graph.subjects(RDF.type, mc.DecisionAlternative), None)
        if subject is not None:
            graph.add((subject, mc.hasAHPScore, Literal('invalid-score')))
        return graph

    monkeypatch.setattr(tool, 'load_graph', corrupt)
    result = tool.review(config, entries)
    assert not result['review_complete']
    assert any('DatatypeConstraintComponent' in e for e in result['errors'])
    assert any(f['status'] == 'unreviewed-error' for f in result['findings'])


def test_debt_review_rejects_blocking_violation(config, monkeypatch):
    from rdflib import Literal, Namespace, RDF
    tool = _debt_tool(config.root)
    entries = tomllib.loads((config.root / 'configs/traceability-review.toml').read_text())['items']
    original = tool.load_graph
    mc = Namespace('http://example.org/monitoringcontinuum#')

    def corrupt(paths):
        graph = original(paths)
        if (mc.State, RDF.type, None) in graph:
            subject = mc.AuditInvalidState
            graph.add((subject, RDF.type, mc.State))
            graph.add((subject, mc.validFrom, Literal('invalid-time')))
        return graph

    monkeypatch.setattr(tool, 'load_graph', corrupt)
    result = tool.review(config, entries)
    assert not result['review_complete']
    assert not result['shacl_conforms_allowing_warnings']
    assert result['violation_count'] > 0


def test_debt_review_rejects_release_contract_error(config, monkeypatch):
    tool = _debt_tool(config.root)
    entries = tomllib.loads((config.root / 'configs/traceability-review.toml').read_text())['items']
    original = tool.validate_release_contract

    def invalid_contract(graph, specs):
        result = original(graph, specs)
        result['errors'].append('ontology version mismatch')
        result['ok'] = False
        return result

    monkeypatch.setattr(tool, 'validate_release_contract', invalid_contract)
    result = tool.review(config, entries)
    assert not result['review_complete']
    assert 'ontology version mismatch' in result['errors']
