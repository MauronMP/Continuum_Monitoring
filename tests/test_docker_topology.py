from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from continuum_bench import cli
from continuum_bench.topology import (
    docker_compose_command,
    load_topology,
    render_docker_compose,
)


def docker_topology(root: Path):
    return load_topology(
        root / "configs/topologies/docker/topology.toml", "docker"
    )


def test_docker_topology_is_elastic_and_layered(root):
    topology = docker_topology(root)

    assert topology.kind == "docker"
    assert len(topology.active_nodes) == 5
    assert topology.node("cloud").tier == "cloud"
    assert topology.node("edge3").authority is True


def test_compose_is_generated_from_every_active_node(root, tmp_path):
    topology = docker_topology(root)
    path = render_docker_compose(topology, tmp_path / "compose.yml", root=root)
    text = path.read_text(encoding="utf-8")

    for node in topology.active_nodes:
        assert f"  {node.node_id}:" in text
        assert f"127.0.0.1:{node.port}:8080" in text
    assert text.count("    build:") == 1


def test_compose_lifecycle_commands_are_scoped(root, tmp_path):
    topology = docker_topology(root)
    command = docker_compose_command(topology, tmp_path / "compose.yml", "down")

    assert command[:4] == ["docker", "compose", "-p", "continuum-monitoring"]
    assert command[-2:] == ["down", "--remove-orphans"]


def test_docker_cli_defaults_to_sharded():
    args = cli._parser().parse_args(["docker", "cumulative"])

    assert args.layout == "sharded"


def test_target_manifest_selects_docker_manifest(root):
    config = SimpleNamespace(root=root)

    selected = cli._target_manifest_path(config, None, "docker")

    assert selected == root / "configs/topologies/docker/topology.toml"
