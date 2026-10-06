"""Acceptance debt and explicit five-node configurations remain reviewable."""
from pathlib import Path
import importlib.util
import tomllib

from continuum_bench.topology import load_topology
from continuum_bench.monitoring.load_config import load_load_config


def _debt_tool(root):
    spec = importlib.util.spec_from_file_location('review_validation_debt', root / 'tools/review_validation_debt.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_five_node_profiles_do_not_schedule_unavailable_mist(config):
    topology = load_topology(config.root / 'configs/topologies/physical/without-mist.toml', 'physical')
    assert {node.node_id for node in topology.active_nodes} == {'cloud', 'fog', 'edge1', 'edge2', 'edge3'}
    workload = load_load_config(config.root / 'configs/load-five-nodes.toml')
    assert max(profile.node_count for profile in workload.profiles) == 5
    for name, section in [('experiments', 'scale_out'), ('distributed-reasoning', 'matrix')]:
        document = tomllib.loads((config.root / f'configs/{name}-five-nodes.toml').read_text())
        assert max(document[section]['node_counts']) == 5
    campaign = tomllib.loads((config.root / 'configs/campaign-five-nodes.toml').read_text())
    assert max(next(axis['values'] for axis in campaign['axes'] if axis['name']=='physical_nodes')) == 5


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


def test_five_node_variants_change_only_available_capacity(config):
    import copy
    for name, section in [('experiments', 'scale_out'), ('distributed-reasoning', 'matrix')]:
        original = tomllib.loads((config.root / f'configs/{name}.toml').read_text())
        expected = copy.deepcopy(original)
        expected[section]['node_counts'] = [n for n in expected[section]['node_counts'] if n <= 5]
        actual = tomllib.loads((config.root / f'configs/{name}-five-nodes.toml').read_text())
        assert actual == expected
    original = tomllib.loads((config.root / 'configs/campaign.toml').read_text())
    for axis in original['axes']:
        if axis['name'] == 'physical_nodes':
            axis['values'] = [n for n in axis['values'] if n <= 5]
    assert tomllib.loads((config.root / 'configs/campaign-five-nodes.toml').read_text()) == original
    original = tomllib.loads((config.root / 'configs/load-benchmark.toml').read_text())
    original['profiles'] = [p for p in original['profiles']
                            if not (p['dimension'] == 'node_count' and p['node_count'] > 5)]
    for profile in original['profiles']:
        profile['node_count'] = min(profile['node_count'], 5)
    assert tomllib.loads((config.root / 'configs/load-five-nodes.toml').read_text()) == original
