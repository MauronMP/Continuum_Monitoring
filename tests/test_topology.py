from pathlib import Path
import shutil

import pytest
from rdflib.compare import isomorphic

from continuum_bench.distributed import Endpoint
from continuum_bench.ontology import load_graph
from continuum_bench.partitioning import build_fragments
from continuum_bench.queries import load_catalog
from continuum_bench.sharded import _sources
from continuum_bench.topology import (
    authority_index,
    docker_compose_command,
    load_topology,
    load_topology_manifest,
    render_docker_compose,
    render_flat_topology,
)


def _copied_catalog(root: Path, tmp_path: Path) -> Path:
    configs = tmp_path / "configs"
    shutil.copytree(root / "configs" / "topologies", configs / "topologies")
    shutil.copy2(root / "configs" / "topology.toml", configs / "topology.toml")
    return configs / "topology.toml"


def _expanded_manifest(root: Path, tmp_path: Path) -> Path:
    path = _copied_catalog(root, tmp_path)
    mist_path = path.parent / "topologies" / "docker" / "nodes" / "mist.toml"
    mist_source = mist_path.read_text(encoding="utf-8")
    mist_source += """

[[nodes]]
id = "mist1"
endpoint = "http://127.0.0.1:8196"
port = 8196
local = true
authority = false
"""
    mist_path.write_text(mist_source, encoding="utf-8")

    iot_path = path.parent / "topologies" / "docker" / "nodes" / "iot.toml"
    iot_source = iot_path.read_text(encoding="utf-8")
    iot_source += """

[[nodes]]
id = "iot1"
endpoint = "http://127.0.0.1:8197"
port = 8197
local = true
authority = true
"""
    iot_path.write_text(iot_source, encoding="utf-8")
    return path


def test_default_manifest_defines_all_architecture_topologies(root):
    manifest = load_topology_manifest(root / "configs" / "topology.toml")

    assert set(manifest.topologies) == {"monolith", "docker", "physical"}
    assert manifest.topology("monolith").kind == "monolith"
    assert len(manifest.topology("monolith").active_nodes) == 1
    assert len(manifest.topology("docker").active_nodes) == 5
    assert len(manifest.topology("physical").active_nodes) == 5


def test_manifest_accepts_mist_iot_and_more_nodes(root, tmp_path):
    topology = load_topology(_expanded_manifest(root, tmp_path), "docker")

    assert len(topology.active_nodes) == 7
    assert topology.node("mist1").tier == "mist"
    assert topology.node("iot1").tier == "iot"
    assert topology.node("iot1").authority


def test_topology_fingerprint_is_independent_of_node_order(root, tmp_path):
    topology = load_topology(_expanded_manifest(root, tmp_path), "docker")
    reordered = type(topology)(
        **{
            **topology.__dict__,
            "nodes": tuple(reversed(topology.nodes)),
        }
    )

    assert reordered.fingerprint == topology.fingerprint


def test_physical_manifest_rejects_two_nodes_on_same_listener(root, tmp_path):
    path = _copied_catalog(root, tmp_path)
    edge_path = (
        path.parent / "topologies" / "physical" / "nodes" / "edge.toml"
    )
    source = edge_path.read_text(encoding="utf-8")
    source = source.replace(
        'host = "192.168.1.139"',
        'host = "192.168.1.138"',
    )
    edge_path.write_text(source, encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate host/port listeners"):
        load_topology_manifest(path)


def test_layer_file_rejects_a_node_from_another_tier(root, tmp_path):
    path = _copied_catalog(root, tmp_path)
    edge_path = (
        path.parent / "topologies" / "docker" / "nodes" / "edge.toml"
    )
    source = edge_path.read_text(encoding="utf-8")
    edge_path.write_text(
        source.replace('id = "edge1"', 'id = "edge1"\ntier = "fog"'),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="layer file is 'edge'"):
        load_topology_manifest(path)


def test_flat_deployment_snapshot_preserves_topology_fingerprint(root, tmp_path):
    topology = load_topology(root / "configs" / "topology.toml", "physical")
    snapshot = render_flat_topology(topology, tmp_path / "effective.toml")
    deployed_manifest = load_topology_manifest(snapshot)
    deployed = deployed_manifest.topology("physical")

    assert deployed_manifest.version == 1
    assert deployed.fingerprint == topology.fingerprint
    assert deployed.public()["tier_counts"] == topology.public()["tier_counts"]


def test_catalog_rejects_circular_architecture_includes(tmp_path):
    first = tmp_path / "first.toml"
    second = tmp_path / "second.toml"
    first.write_text(
        '[manifest]\nversion = 2\ntopology_files = ["second.toml"]\n',
        encoding="utf-8",
    )
    second.write_text(
        '[manifest]\nversion = 2\ntopology_files = ["first.toml"]\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Circular topology manifest include"):
        load_topology_manifest(first)


def test_layer_rejects_unknown_query_category(root, tmp_path):
    path = _copied_catalog(root, tmp_path)
    cloud_path = (
        path.parent / "topologies" / "docker" / "nodes" / "cloud.toml"
    )
    source = cloud_path.read_text(encoding="utf-8")
    cloud_path.write_text(
        source + '\ncategories = ["misspelled-category"]\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown categories"):
        load_topology_manifest(path)


def test_compose_renderer_emits_every_active_node(root, tmp_path):
    topology = load_topology(_expanded_manifest(root, tmp_path), "docker")
    output = render_docker_compose(
        topology,
        tmp_path / "compose.yml",
        root=root,
    )
    rendered = output.read_text(encoding="utf-8")

    assert "  mist1:" in rendered
    assert "  iot1:" in rendered
    assert 'CONTINUUM_TIER: "mist"' in rendered
    assert 'CONTINUUM_TIER: "iot"' in rendered
    assert '"127.0.0.1:8197:8080"' in rendered


def test_compose_lifecycle_removes_nodes_deleted_from_manifest(root):
    topology = load_topology(root / "configs" / "topology.toml", "docker")

    assert "--remove-orphans" in docker_compose_command(
        topology,
        root / "compose.yml",
        "up",
    )
    assert "--remove-orphans" in docker_compose_command(
        topology,
        root / "compose.yml",
        "down",
    )


def test_elastic_fragments_reconstruct_the_logical_graph(
    config,
    root,
    tmp_path,
):
    topology = load_topology(_expanded_manifest(root, tmp_path), "docker")
    fragments = build_fragments(config, 1, topology=topology)
    expected = load_graph(
        config.resolve(path) for path in config.ontology_files
    )
    from continuum_bench.synthetic import add_synthetic_data

    add_synthetic_data(expected, 1, config.seed)
    assert set(fragments.graphs) == {
        node.node_id for node in topology.active_nodes
    }
    assert isomorphic(fragments.union(), expected)


def test_owner_key_routing_uses_same_elastic_authority_hash(
    config,
    root,
    tmp_path,
):
    topology = load_topology(_expanded_manifest(root, tmp_path), "docker")
    endpoints = [
        Endpoint(
            node.endpoint,
            node.node_id,
            node.tier,
            node.authority,
            node.categories,
        )
        for node in topology.active_nodes
    ]
    spec = next(
        item
        for item in load_catalog(
            config.resolve(config.query_catalog),
            config.root,
        )
        if item.id == "BASE-Q04"
    )
    # Deliberately reverse discovery order: routing must follow the same
    # canonical tier/id order used for fragment ownership, not manifest or
    # network response order.
    selected = _sources(spec, list(reversed(endpoints)))
    authorities = sorted(
        (node for node in endpoints if node.authority),
        key=lambda node: (
            ("cloud", "fog", "mist", "edge", "iot").index(node.tier),
            node.role,
        ),
    )
    expected_index = authority_index(
        "http://example.org/smartcity#UserB",
        len(authorities),
    )

    assert selected == [authorities[expected_index]]
