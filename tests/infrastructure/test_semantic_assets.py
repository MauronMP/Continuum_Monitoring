"""Stale semantic files must not pass worker compatibility checks."""
from dataclasses import replace
from pathlib import Path
import shutil

import pytest

from continuum_bench.config import load_config
from continuum_bench.node import NodeRuntime
from continuum_bench.protocol import worker_health_error, WORKER_PROTOCOL_VERSION, WORKER_SERVICE, SOFTWARE_BUILD_ID
from continuum_bench.semantic_assets import semantic_assets_digest
from continuum_bench.specification import release_identity


@pytest.fixture
def replica(root, tmp_path):
    for name in ('configs', 'queries', 'ontology'):
        shutil.copytree(root / name, tmp_path / name, ignore=shutil.ignore_patterns('diagrams'))
    return load_config(tmp_path / 'configs/benchmark.toml')


def test_semantic_identity_is_path_independent_and_excludes_workload_sizes(config, replica):
    assert semantic_assets_digest(config) == semantic_assets_digest(replica)
    assert semantic_assets_digest(config) == semantic_assets_digest(replace(config, scale_users=(999,)))


@pytest.mark.parametrize('relative', ['ontology/modules/governance.ttl', 'queries/core/policy_governance/ext-q03.rq', 'configs/ontology-placement.toml'])
def test_same_version_file_change_alters_semantic_identity(replica, relative):
    before = semantic_assets_digest(replica)
    path = replica.root / relative
    path.write_text(path.read_text() + '\n# A same-version edit\n')
    assert semantic_assets_digest(replica) != before


def test_missing_input_is_not_a_valid_semantic_identity(replica):
    (replica.root / 'ontology/modules/governance.ttl').unlink()
    with pytest.raises(FileNotFoundError):
        semantic_assets_digest(replica)


def test_worker_rejects_assets_changed_after_startup(replica):
    runtime = NodeRuntime(replica.root, 'cloud')
    path = replica.root / 'ontology/modules/governance.ttl'
    path.write_text(path.read_text() + '\n# Edited after startup\n')
    with pytest.raises(ValueError, match='changed after worker startup'):
        runtime.prepare('rdfs', users=0, seed=2026)
    assert runtime.base_graph is None


def test_health_contract_checks_semantic_identity(config):
    expected = semantic_assets_digest(config)
    health = {**release_identity(), 'status':'ok', 'service':WORKER_SERVICE,
              'protocol_version':WORKER_PROTOCOL_VERSION, 'build_id':SOFTWARE_BUILD_ID,
              'role':'cloud', 'node_id':'cloud', 'tier':'cloud', 'semantic_assets_digest':expected}
    assert worker_health_error(health, expected_semantic_digest=expected) is None
    health['semantic_assets_digest'] = '0' * 64
    assert 'semantic_assets_digest' in worker_health_error(health, expected_semantic_digest=expected)


def test_physical_metadata_records_semantic_inputs_for_both_layouts(config):
    from continuum_bench.monitoring import physical, distributed_ontology
    from continuum_bench.topology import load_topology
    from continuum_bench.monitoring.distributed import Endpoint
    topology = load_topology(config.resolve(config.topology_file), 'physical')
    endpoints = [Endpoint(n.endpoint, n.node_id, n.tier, n.authority, n.categories)
                 for n in topology.active_nodes]
    expected = semantic_assets_digest(config)
    replicated = physical._metadata(config, endpoints, 'scalability', topology)
    distributed = distributed_ontology._metadata(config, endpoints, 'physical', 'scalability', True, topology)
    assert replicated['semantic_assets_digest'] == expected
    assert distributed['semantic_assets_digest'] == expected
