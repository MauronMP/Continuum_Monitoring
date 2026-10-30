"""Validated container budgets and explicit, reproducible workload points."""

from dataclasses import dataclass, replace
import math
from pathlib import Path
import re
import tomllib

from ...topology import load_topology, Topology


@dataclass(frozen=True)
class ContainerConfig:
    path: Path
    raw: dict
    topology: Topology

    @property
    def deployment(self):
        return self.raw["deployment"]

    @property
    def experiment(self):
        return self.raw["experiment"]


def load(path: Path, root: Path, *, exclude_hosts=(), reasoners=None) -> ContainerConfig:
    raw = tomllib.loads(path.read_text())
    d, e = raw["deployment"], raw["experiment"]
    if reasoners is not None:
        e["reasoners"] = list(dict.fromkeys("rdfs" if r == "rdf" else r for r in reasoners))
        if set(e["reasoners"]) - {"rdfs"}:
            d["install_dl"] = True
    topology = load_topology(root / d["topology_file"], d["topology_name"])
    if len({n.host for n in topology.active_nodes}) != len(topology.active_nodes):
        raise ValueError(
            "Container deployment requires one inventory entry per physical host"
        )
    excluded = set(d.get("exclude_hosts", [])) | set(exclude_hosts)
    unknown = excluded - {n.node_id for n in topology.nodes}
    if unknown:
        raise ValueError(f"Unknown excluded physical hosts: {sorted(unknown)}")
    topology = replace(
        topology, nodes=tuple(n for n in topology.nodes if n.node_id not in excluded)
    )
    if (
        not any(n.tier == "cloud" for n in topology.active_nodes)
        or not topology.authority_nodes
    ):
        raise ValueError(
            "Selected hosts must retain a Cloud coordinator and at least one data authority"
        )
    d["exclude_hosts"] = sorted(excluded)
    counts = d["containers_per_host"]
    if (
        not counts
        or sorted(set(counts)) != counts
        or any(type(n) is not int or n < 1 for n in counts)
    ):
        raise ValueError(
            "containers_per_host must contain increasing positive integers"
        )
    for key in (
        "cpu_per_container",
        "memory_mib_per_container",
        "reserve_memory_mib",
        "minimum_free_disk_mib",
        "health_timeout_seconds",
        "operation_timeout_seconds",
    ):
        if not math.isfinite(float(d[key])) or float(d[key]) <= 0:
            raise ValueError(f"deployment.{key} must be finite and positive")
    for key in (
        "memory_mib_per_container",
        "reserve_memory_mib",
        "minimum_free_disk_mib",
    ):
        if type(d[key]) is not int:
            raise ValueError(f"{key} must be an integer number of MiB")
    if type(d["base_port"]) is not int or not 1024 <= d["base_port"] <= 65535 - max(
        counts
    ):
        raise ValueError("Invalid container port range")
    if any(
        n.port in range(d["base_port"], d["base_port"] + max(counts))
        for n in topology.active_nodes
    ):
        raise ValueError("Container ports must not overlap native worker ports")
    if (
        not re.fullmatch(r"/[a-zA-Z0-9_./-]+", d["remote_dir"])
        or ".." in Path(d["remote_dir"]).parts
        or d["remote_dir"] in ("/", "/home", "/home/pi")
    ):
        raise ValueError("remote_dir must be a dedicated absolute directory")
    remote = Path(d["remote_dir"])
    native = Path(topology.remote_dir)
    if remote == native or remote in native.parents or native in remote.parents:
        raise ValueError(
            "Container staging must be separate from native worker installation"
        )
    if not remote.name.startswith("continuum-container"):
        raise ValueError(
            "Use a dedicated remote staging directory named continuum-container..."
        )
    if not re.fullmatch(r"[a-z_][a-z0-9_-]*", d["ssh_user"]):
        raise ValueError("Invalid SSH user")
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._:/-]*", d["image"]):
        raise ValueError("Invalid Docker image reference")
    if not e["reasoners"] or set(e["reasoners"]) - {
        "rdfs",
        "hermit",
        "openllet",
        "jfact",
        "konclude",
    }:
        raise ValueError("Unsupported or empty reasoner matrix")
    if set(e["reasoners"]) != {"rdfs"} and not d["install_dl"]:
        raise ValueError(
            "Native reasoners require deployment.install_dl=true; no fallback is allowed"
        )
    if not e["layouts"] or set(e["layouts"]) - {"distributed", "replicated"}:
        raise ValueError("Unsupported or empty layout matrix")
    for key in ("repetitions",):
        if type(e[key]) is not int or e[key] < 1:
            raise ValueError(f"{key} must be a positive integer")
    if type(e["warmup"]) is not int or e["warmup"] < 0:
        raise ValueError("warmup must be a nonnegative integer")
    if not 5 < e["request_timeout_seconds"] <= e["point_timeout_seconds"] < math.inf:
        raise ValueError("Require finite point >= request > 5 second budgets")
    if type(e["seed"]) is not int or not 0 <= e["seed"] < 2**32:
        raise ValueError("seed must be an integer in [0, 2**32)")
    scenarios = raw["scenarios"]
    names = [s["name"] for s in scenarios]
    if not names or len(set(names)) != len(names):
        raise ValueError("Scenario names must be unique and nonempty")
    for s in scenarios:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", s["name"]):
            raise ValueError("Scenario names must be safe directory names")
        if s["family"] not in {"users", "data", "requests", "strong", "weak"}:
            raise ValueError("Unknown scenario family")
        for key in ("users", "target_triples", "query_rounds"):
            if type(s[key]) is not int or s[key] < (1 if key == "query_rounds" else 0):
                raise ValueError(f"Invalid scenario {key}")
        if (
            not s["concurrency"]
            or sorted(set(s["concurrency"])) != s["concurrency"]
            or any(type(n) is not int or n < 1 for n in s["concurrency"])
        ):
            raise ValueError("Concurrency must be increasing positive integers")
    for node in topology.active_nodes:
        if (
            max(counts) * d["memory_mib_per_container"] + d["reserve_memory_mib"]
            > node.to_domain().capacity.ram_mib
        ):
            raise ValueError(
                f"{node.node_id}: configured memory exceeds physical inventory"
            )
        if max(counts) * d["cpu_per_container"] > node.cpus:
            raise ValueError(
                f"{node.node_id}: configured CPU exceeds physical inventory"
            )
    return ContainerConfig(path.resolve(), raw, topology)


def logical_topology(config: ContainerConfig, count: int) -> Topology:
    d = config.deployment
    nodes = tuple(
        replace(
            n,
            node_id=f"{n.node_id}-c{i + 1}",
            port=d["base_port"] + i,
            endpoint=f"http://{n.host}:{d['base_port'] + i}",
            cpus=d["cpu_per_container"],
            memory=f"{d['memory_mib_per_container']}m",
            storage_mib=0,
            device_type=f"container-on-{n.device_type}",
        )
        for n in config.topology.active_nodes
        for i in range(count)
    )
    return replace(
        config.topology,
        name="container-scale",
        nodes=nodes,
        description="Logical participants on physical hosts; storage and network are shared",
    )
