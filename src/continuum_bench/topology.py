"""Configuration-driven elastic continuum topologies.

Node identity is deliberately independent from the architectural tier.  A
topology can therefore contain any number of cloud, fog, mist, edge or IoT
nodes without adding role constants to the benchmark code.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tomllib
from typing import Any, Iterable
from urllib.parse import urlsplit


TIERS = ("cloud", "fog", "mist", "edge", "iot")
TIER_ORDER = {tier: index for index, tier in enumerate(TIERS)}
NODE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")

DEFAULT_CATEGORIES: dict[str, tuple[str, ...]] = {
    "cloud": (
        "semantic_schema",
        "decision",
        "policy_governance",
        "validation",
    ),
    "fog": (
        "topology",
        "data_lifecycle",
        "trust",
        "adaptation",
        "delegation",
        "federation",
        "audit_temporal",
    ),
    "mist": (
        "topology",
        "observability",
        "data_lifecycle",
        "context_zones",
        "trust",
        "adaptation",
    ),
    "edge": (
        "observability",
        "identity_consent",
        "security_identity",
        "context_zones",
        "wellbeing",
    ),
    "iot": (
        "observability",
        "identity_consent",
        "context_zones",
        "wellbeing",
    ),
}
KNOWN_CATEGORIES = frozenset(
    category
    for categories in DEFAULT_CATEGORIES.values()
    for category in categories
)


def infer_tier(node_id: str) -> str:
    """Infer a tier only for backward-compatible endpoint construction."""
    normalized = node_id.lower().replace("_", "-")
    for tier in TIERS:
        if normalized == tier or normalized.startswith(f"{tier}-"):
            return tier
        if normalized.startswith(tier) and normalized[len(tier) :].isdigit():
            return tier
    raise ValueError(
        f"Cannot infer a tier from node id {node_id!r}; configure tier as one "
        f"of {list(TIERS)}"
    )


def default_categories(tier: str) -> tuple[str, ...]:
    try:
        return DEFAULT_CATEGORIES[tier]
    except KeyError as error:
        raise ValueError(f"Unsupported continuum tier {tier!r}") from error


def authority_index(value: object, authority_count: int) -> int:
    """Return the deterministic privacy-authority shard for a resource key."""
    if authority_count < 1:
        raise ValueError("authority_count must be >= 1")
    digits = re.findall(r"\d+", str(value))
    number = int(digits[-1]) if digits else sum(str(value).encode("utf-8"))
    return number % authority_count


@dataclass(frozen=True)
class TopologyNode:
    node_id: str
    tier: str
    endpoint: str
    host: str
    port: int
    local: bool
    authority: bool
    categories: tuple[str, ...]
    enabled: bool = True
    cpus: float = 1.0
    memory: str = "1g"
    container_port: int = 8080

    @property
    def role(self) -> str:
        """Legacy name retained in CSVs and lifecycle code."""
        return self.node_id

    def public(self) -> dict[str, Any]:
        value = asdict(self)
        value["id"] = value.pop("node_id")
        return value


@dataclass(frozen=True)
class Topology:
    name: str
    kind: str
    description: str
    nodes: tuple[TopologyNode, ...]
    ssh_user: str = ""
    remote_dir: str = ""
    remote_python: str = ""
    compose_project: str = "continuum-benchmark"
    image: str = "continuum-benchmark-node:latest"
    dockerfile: str = "docker/Dockerfile"
    network: str = "continuum"
    bind_host: str = "127.0.0.1"
    source_path: Path | None = None
    project_root: Path | None = None
    remote_dir_template: str = ""
    remote_python_template: str = ""

    @property
    def active_nodes(self) -> tuple[TopologyNode, ...]:
        return tuple(node for node in self.nodes if node.enabled)

    @property
    def authority_nodes(self) -> tuple[TopologyNode, ...]:
        return tuple(node for node in self.active_nodes if node.authority)

    def node(self, node_id: str) -> TopologyNode:
        for node in self.active_nodes:
            if node.node_id == node_id:
                return node
        raise KeyError(f"Topology {self.name!r} has no active node {node_id!r}")

    def endpoints(self) -> list[str]:
        return [node.endpoint for node in self.active_nodes]

    @property
    def fingerprint(self) -> str:
        """Stable identity for every placement-relevant topology field."""
        payload = {
            "name": self.name,
            "kind": self.kind,
            "nodes": [
                {
                    "id": node.node_id,
                    "tier": node.tier,
                    "endpoint": node.endpoint,
                    "host": node.host,
                    "port": node.port,
                    "local": node.local,
                    "authority": node.authority,
                    "categories": sorted(node.categories),
                    "cpus": node.cpus,
                    "memory": node.memory,
                    "container_port": node.container_port,
                }
                for node in ordered_nodes(self.active_nodes)
            ],
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def public(self) -> dict[str, Any]:
        source = self.source_path
        if source is not None and self.project_root is not None:
            try:
                source = source.relative_to(self.project_root)
            except ValueError:
                pass
        return {
            "name": self.name,
            "kind": self.kind,
            "description": self.description,
            "source_file": str(source) if source is not None else "",
            "node_count": len(self.active_nodes),
            "fingerprint": self.fingerprint,
            "tier_counts": {
                tier: sum(node.tier == tier for node in self.active_nodes)
                for tier in TIERS
            },
            "nodes": [node.public() for node in self.active_nodes],
        }


@dataclass(frozen=True)
class TopologyManifest:
    path: Path
    version: int
    topologies: dict[str, Topology]

    def topology(self, name: str) -> Topology:
        try:
            return self.topologies[name]
        except KeyError as error:
            raise ValueError(
                f"Unknown topology {name!r}; available={sorted(self.topologies)}"
            ) from error

    def public(self) -> dict[str, Any]:
        return {
            "manifest": str(self.path),
            "version": self.version,
            "topologies": {
                name: topology.public()
                for name, topology in self.topologies.items()
            },
        }


def _as_path(root: Path, value: str, ssh_user: str) -> str:
    return value.format(root=str(root), ssh_user=ssh_user)


def _parse_node(raw: dict[str, Any], topology_name: str) -> TopologyNode:
    node_id = str(raw.get("id", "")).strip()
    tier = str(raw.get("tier", "")).strip().lower()
    endpoint = str(raw.get("endpoint", "")).strip().rstrip("/")
    host = str(raw.get("host", "")).strip()
    enabled = bool(raw.get("enabled", True))
    if not NODE_ID_PATTERN.fullmatch(node_id):
        raise ValueError(
            f"Topology {topology_name}: invalid node id {node_id!r}; use "
            "lowercase letters, digits, '_' or '-' and start with a letter"
        )
    if tier not in TIERS:
        raise ValueError(
            f"Topology {topology_name} node {node_id}: tier must be one of "
            f"{list(TIERS)}, got {tier!r}"
        )
    parsed = urlsplit(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(
            f"Topology {topology_name} node {node_id}: endpoint must be an "
            f"absolute HTTP(S) URL, got {endpoint!r}"
        )
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError(
            f"Topology {topology_name} node {node_id}: endpoint cannot contain "
            "a path, query or fragment"
        )
    port = int(raw.get("port", parsed.port or 8080))
    container_port = int(raw.get("container_port", 8080))
    if not 1 <= port <= 65535 or not 1 <= container_port <= 65535:
        raise ValueError(
            f"Topology {topology_name} node {node_id}: ports must be in [1, 65535]"
        )
    categories = tuple(
        dict.fromkeys(
            str(value).strip()
            for value in raw.get("categories", default_categories(tier))
            if str(value).strip()
        )
    )
    if not categories:
        raise ValueError(
            f"Topology {topology_name} node {node_id}: categories cannot be empty"
        )
    unknown_categories = sorted(set(categories) - KNOWN_CATEGORIES)
    if unknown_categories:
        raise ValueError(
            f"Topology {topology_name} node {node_id}: unknown categories "
            f"{unknown_categories}"
        )
    cpus = float(raw.get("cpus", 1.0))
    if cpus <= 0:
        raise ValueError(
            f"Topology {topology_name} node {node_id}: cpus must be positive"
        )
    memory = str(raw.get("memory", "1g")).strip().lower()
    if not re.fullmatch(r"[1-9][0-9]*(?:[kmgt]i?b?|b)?", memory):
        raise ValueError(
            f"Topology {topology_name} node {node_id}: invalid memory {memory!r}"
        )
    return TopologyNode(
        node_id=node_id,
        tier=tier,
        endpoint=endpoint,
        host=host or str(parsed.hostname),
        port=port,
        local=bool(raw.get("local", False)),
        authority=bool(raw.get("authority", tier in {"edge", "iot"})),
        categories=categories,
        enabled=enabled,
        cpus=cpus,
        memory=memory,
        container_port=container_port,
    )


def _validate_topology(topology: Topology) -> None:
    configured_ids = [node.node_id for node in topology.nodes]
    if len(configured_ids) != len(set(configured_ids)):
        raise ValueError(
            f"Topology {topology.name!r} has duplicate configured node ids: "
            f"{configured_ids}"
        )
    nodes = topology.active_nodes
    if not nodes:
        raise ValueError(f"Topology {topology.name!r} has no enabled nodes")
    endpoints = [node.endpoint for node in nodes]
    if len(endpoints) != len(set(endpoints)):
        raise ValueError(
            f"Topology {topology.name!r} has duplicate endpoints: {endpoints}"
        )
    if not any(node.tier == "cloud" for node in nodes):
        raise ValueError(
            f"Topology {topology.name!r} requires at least one cloud node"
        )
    if topology.kind != "monolith" and not topology.authority_nodes:
        raise ValueError(
            f"Topology {topology.name!r} requires at least one authority node "
            "for privacy-aware partitioning"
        )
    if topology.kind == "monolith":
        if len(nodes) != 1:
            raise ValueError(
                f"Monolith topology {topology.name!r} must define exactly "
                f"one active node, got {len(nodes)}"
            )
        if nodes[0].tier != "cloud" or not nodes[0].local:
            raise ValueError(
                f"Monolith topology {topology.name!r} requires one local "
                "cloud-tier node"
            )
    elif topology.kind == "docker":
        host_ports = [node.port for node in nodes]
        if len(host_ports) != len(set(host_ports)):
            raise ValueError(
                f"Docker topology {topology.name!r} has duplicate host ports: "
                f"{host_ports}"
            )
    elif topology.kind == "physical":
        if not any(node.local for node in nodes):
            raise ValueError(
                f"Physical topology {topology.name!r} requires at least one "
                "local coordinator node"
            )
        if not topology.ssh_user:
            raise ValueError(
                f"Physical topology {topology.name!r} requires ssh_user"
            )
        listeners = [(node.host, node.port) for node in nodes]
        if len(listeners) != len(set(listeners)):
            raise ValueError(
                f"Physical topology {topology.name!r} has duplicate "
                f"host/port listeners: {listeners}"
            )
        if (
            not topology.remote_dir.startswith("/")
            or not topology.remote_python.startswith("/")
        ):
            raise ValueError(
                f"Physical topology {topology.name!r} requires absolute "
                "remote_dir and remote_python paths"
            )
        directory = PurePosixPath(topology.remote_dir)
        python = PurePosixPath(topology.remote_python)
        if (
            len(directory.parts) < 3
            or ".." in directory.parts
            or str(directory)
            in {
                f"/home/{topology.ssh_user}",
                f"/Users/{topology.ssh_user}",
                "/root",
                "/tmp",
                "/var/tmp",
            }
            or not python.is_relative_to(directory)
            or ".." in python.parts
        ):
            raise ValueError(
                f"Physical topology {topology.name!r} must use a dedicated "
                "remote_dir below the SSH user's home and remote_python "
                "inside that directory"
            )
    else:
        raise ValueError(
            f"Topology {topology.name!r}: kind must be monolith, docker or "
            "physical"
        )


def _project_root(manifest_path: Path) -> Path:
    for parent in manifest_path.parents:
        if parent.name == "configs":
            return parent.parent
    return manifest_path.parent


def _load_layer_nodes(path: Path, topology_name: str) -> list[dict[str, Any]]:
    with path.open("rb") as handle:
        document = tomllib.load(handle)
    layer = document.get("layer", {})
    tier = str(layer.get("tier", "")).strip().lower()
    if tier not in TIERS:
        raise ValueError(
            f"Topology {topology_name!r} layer {path}: layer.tier must be one "
            f"of {list(TIERS)}, got {tier!r}"
        )
    nodes = document.get("nodes", [])
    if not isinstance(nodes, list):
        raise ValueError(f"{path}: nodes must be an array of tables")
    normalized: list[dict[str, Any]] = []
    for raw_node in nodes:
        if not isinstance(raw_node, dict):
            raise ValueError(f"{path}: every [[nodes]] entry must be a table")
        declared_tier = str(raw_node.get("tier", tier)).strip().lower()
        if declared_tier != tier:
            raise ValueError(
                f"{path}: node {raw_node.get('id')!r} declares tier "
                f"{declared_tier!r}, but the layer file is {tier!r}"
            )
        normalized.append({**raw_node, "tier": tier})
    return normalized


def _topology_from_settings(
    name: str,
    settings: dict[str, Any],
    source_path: Path,
) -> Topology:
    if not NODE_ID_PATTERN.fullmatch(name):
        raise ValueError(f"Invalid topology name {name!r}")
    root = _project_root(source_path)
    configured_nodes = settings.get("nodes", [])
    if not isinstance(configured_nodes, list):
        raise ValueError(f"Topology {name!r}: nodes must be an array of tables")
    # Never mutate the structure returned by tomllib.  A manifest can be
    # loaded more than once in one process (validation + execution).
    nodes_raw = list(configured_nodes)
    node_files = settings.get("node_files", [])
    if not isinstance(node_files, list):
        raise ValueError(f"Topology {name!r}: node_files must be an array")
    seen_files: set[Path] = set()
    for value in node_files:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Topology {name!r}: every node_files entry must be a "
                "non-empty string"
            )
        node_path = (source_path.parent / str(value)).resolve()
        if node_path in seen_files:
            raise ValueError(
                f"Topology {name!r}: duplicate node file {node_path}"
            )
        seen_files.add(node_path)
        if not node_path.is_file():
            raise FileNotFoundError(
                f"Topology {name!r}: node file does not exist: {node_path}"
            )
        nodes_raw.extend(_load_layer_nodes(node_path, name))
    if not nodes_raw:
        raise ValueError(
            f"Topology {name!r}: configure nodes or node_files"
        )
    ssh_user = str(settings.get("ssh_user", "")).strip()
    remote_dir_template = str(settings.get("remote_dir", ""))
    remote_python_template = str(settings.get("remote_python", ""))
    topology = Topology(
        name=name,
        kind=str(settings.get("kind", name)).strip().lower(),
        description=str(settings.get("description", "")).strip(),
        nodes=tuple(_parse_node(item, name) for item in nodes_raw),
        ssh_user=ssh_user,
        remote_dir=_as_path(root, remote_dir_template, ssh_user),
        remote_python=_as_path(root, remote_python_template, ssh_user),
        compose_project=str(
            settings.get("compose_project", f"continuum-{name}")
        ).strip(),
        image=str(
            settings.get("image", "continuum-benchmark-node:latest")
        ).strip(),
        dockerfile=str(
            settings.get("dockerfile", "docker/Dockerfile")
        ).strip(),
        network=str(settings.get("network", "continuum")).strip(),
        bind_host=str(settings.get("bind_host", "127.0.0.1")).strip(),
        source_path=source_path,
        project_root=root,
        remote_dir_template=remote_dir_template,
        remote_python_template=remote_python_template,
    )
    _validate_topology(topology)
    return topology


def _load_topologies(
    manifest_path: Path,
    loading: tuple[Path, ...] = (),
) -> dict[str, Topology]:
    if manifest_path in loading:
        chain = " -> ".join(map(str, (*loading, manifest_path)))
        raise ValueError(f"Circular topology manifest include: {chain}")
    with manifest_path.open("rb") as handle:
        raw = tomllib.load(handle)
    metadata = raw.get("manifest", {})
    version = int(metadata.get("version", 0))
    if version not in {1, 2}:
        raise ValueError(
            f"{manifest_path}: manifest.version must be 1 or 2, got {version}"
        )
    if "topology_files" in metadata:
        topology_files = metadata["topology_files"]
        if version != 2 or not isinstance(topology_files, list):
            raise ValueError(
                f"{manifest_path}: topology_files requires manifest.version=2"
            )
        if not topology_files:
            raise ValueError(f"{manifest_path}: topology_files cannot be empty")
        if "topology" in raw or "topologies" in raw:
            raise ValueError(
                f"{manifest_path}: an index with topology_files cannot also "
                "declare topology tables"
            )
        loaded: dict[str, Topology] = {}
        for value in topology_files:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{manifest_path}: every topology_files entry must be a "
                    "non-empty string"
                )
            child_path = (manifest_path.parent / str(value)).resolve()
            if not child_path.is_file():
                raise FileNotFoundError(
                    f"Topology manifest does not exist: {child_path}"
                )
            for name, topology in _load_topologies(
                child_path,
                (*loading, manifest_path),
            ).items():
                if name in loaded:
                    raise ValueError(
                        f"Duplicate topology {name!r} included by {manifest_path}"
                    )
                loaded[name] = topology
        return loaded
    if "topology" in raw:
        if version != 2:
            raise ValueError(
                f"{manifest_path}: [topology] requires manifest.version=2"
            )
        settings = raw["topology"]
        if not isinstance(settings, dict):
            raise ValueError(f"{manifest_path}: [topology] must be a table")
        name = str(settings.get("name", "")).strip()
        return {name: _topology_from_settings(name, settings, manifest_path)}
    declared = raw.get("topologies", {})
    if not isinstance(declared, dict) or not declared:
        raise ValueError(
            f"{manifest_path}: define [topology], [topologies.NAME], or "
            "manifest.topology_files"
        )
    loaded = {}
    for name, settings in declared.items():
        if not isinstance(settings, dict):
            raise ValueError(
                f"{manifest_path}: topologies.{name} must be a table"
            )
        loaded[str(name)] = _topology_from_settings(
            str(name), settings, manifest_path
        )
    return loaded


def load_topology_manifest(path: str | Path) -> TopologyManifest:
    manifest_path = Path(path).resolve()
    topologies = _load_topologies(manifest_path)
    if not topologies:
        raise ValueError(f"{manifest_path}: no topologies were loaded")
    with manifest_path.open("rb") as handle:
        root_document = tomllib.load(handle)
    version = int(root_document.get("manifest", {}).get("version", 0))
    return TopologyManifest(manifest_path, version, topologies)


def load_topology(path: str | Path, name: str) -> Topology:
    return load_topology_manifest(path).topology(name)


def render_flat_topology(topology: Topology, output: Path) -> Path:
    """Write one self-contained v1 manifest for deployment to a worker.

    Coordinators use composed v2 manifests. Remote workers receive this
    effective snapshot so relative include files cannot be missing or change
    during a campaign.
    """
    table = f"topologies.{topology.name}"
    lines = [
        "# Generated effective topology; edit the source manifests instead.",
        "[manifest]",
        "version = 1",
        "",
        f"[{table}]",
        f"kind = {json.dumps(topology.kind)}",
        f"description = {json.dumps(topology.description)}",
    ]
    settings = {
        "ssh_user": topology.ssh_user,
        "remote_dir": topology.remote_dir,
        "remote_python": topology.remote_python,
        "compose_project": topology.compose_project,
        "image": topology.image,
        "dockerfile": topology.dockerfile,
        "network": topology.network,
        "bind_host": topology.bind_host,
    }
    for key, value in settings.items():
        if value:
            lines.append(f"{key} = {json.dumps(value)}")
    for node in topology.active_nodes:
        lines.extend(
            [
                "",
                f"[[{table}.nodes]]",
                f"id = {json.dumps(node.node_id)}",
                f"tier = {json.dumps(node.tier)}",
                f"endpoint = {json.dumps(node.endpoint)}",
                f"host = {json.dumps(node.host)}",
                f"port = {node.port}",
                f"container_port = {node.container_port}",
                f"local = {str(node.local).lower()}",
                f"authority = {str(node.authority).lower()}",
                f"enabled = {str(node.enabled).lower()}",
                f"cpus = {node.cpus}",
                f"memory = {json.dumps(node.memory)}",
                "categories = [",
                *(f"  {json.dumps(value)}," for value in node.categories),
                "]",
            ]
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def ordered_nodes(nodes: Iterable[TopologyNode]) -> tuple[TopologyNode, ...]:
    return tuple(
        sorted(nodes, key=lambda node: (TIER_ORDER[node.tier], node.node_id))
    )


def render_docker_compose(
    topology: Topology,
    output: Path,
    *,
    root: Path,
) -> Path:
    """Render a Compose file for every enabled node in a Docker topology."""
    if topology.kind != "docker":
        raise ValueError(
            f"Topology {topology.name!r} is {topology.kind!r}, not docker"
        )
    nodes = topology.active_nodes
    lines = [
        "# Generated from the composed topology manifests;",
        "# edit those sources, not this file.",
        f"name: {json.dumps(topology.compose_project)}",
        "",
        "x-node: &node",
        f"  image: {json.dumps(topology.image)}",
        "  pull_policy: never",
        "  init: true",
        '  restart: "no"',
        "  networks:",
        f"    - {topology.network}",
        "",
        "services:",
    ]
    for index, node in enumerate(nodes):
        published_port = (
            f"{topology.bind_host}:{node.port}:{node.container_port}"
        )
        lines.extend(
            [
                f"  {node.node_id}:",
                "    <<: *node",
            ]
        )
        if index == 0:
            lines.extend(
                [
                    "    build:",
                    f"      context: {json.dumps(str(root))}",
                    f"      dockerfile: {json.dumps(topology.dockerfile)}",
                ]
            )
        lines.extend(
            [
                f"    hostname: {json.dumps(node.node_id)}",
                f"    cpus: {json.dumps(str(node.cpus))}",
                f"    mem_limit: {json.dumps(node.memory)}",
                "    environment:",
                f"      CONTINUUM_NODE_ID: {json.dumps(node.node_id)}",
                f"      CONTINUUM_TIER: {json.dumps(node.tier)}",
                f"      CONTINUUM_TOPOLOGY_NAME: {json.dumps(topology.name)}",
                "      CONTINUUM_TOPOLOGY_FILE: /app/configs/topology.toml",
                "    ports:",
                f"      - {json.dumps(published_port)}",
                "",
            ]
        )
    lines.extend(
        [
            "networks:",
            f"  {topology.network}:",
            "    driver: bridge",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def docker_compose_command(
    topology: Topology,
    compose_file: Path,
    action: str,
) -> list[str]:
    base = [
        "docker",
        "compose",
        "-p",
        topology.compose_project,
        "-f",
        str(compose_file),
    ]
    if action == "up":
        return [*base, "up", "-d", "--build", "--remove-orphans"]
    if action == "status":
        return [*base, "ps"]
    if action == "logs":
        return [*base, "logs", "--tail", "100"]
    if action == "down":
        return [*base, "down", "--remove-orphans"]
    raise ValueError(f"Unsupported Docker topology action {action!r}")


def run_docker_topology(
    topology: Topology,
    compose_file: Path,
    action: str,
    *,
    root: Path,
) -> int:
    render_docker_compose(topology, compose_file, root=root)
    command = docker_compose_command(topology, compose_file, action)
    result = subprocess.run(command, cwd=root, check=False)
    return int(result.returncode)
