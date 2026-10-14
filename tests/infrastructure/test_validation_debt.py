"""Accepted validation debt remains reviewable."""
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
    assert len(result['query_coverage_review']) == 24
    entries.pop('RF-69')
    result = tool.review(config, entries)
    assert not result['review_complete']
    assert any('RF-69' in error for error in result['errors'])

