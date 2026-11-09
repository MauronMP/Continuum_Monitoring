from __future__ import annotations

import json
import shlex
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import monotonic

from ..deployment import _remote, semantic_environment
from ..experiment import _prepare
from ..protocol import request_json, wait_ready
from ..topology import Host, Topology
from .config import AdaptationConfig


def collect_candidate_inventory(config: AdaptationConfig, topology: Topology) -> list[dict]:
    user = str(config.benchmark.deployment["ssh_user"])

    def inspect(host: Host) -> dict:
        command = (
            "nproc; awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo; "
            "cut -d' ' -f1 /proc/loadavg; "
            f"if (command -v ss >/dev/null && ss -ltn | awk '{{print $4}}' | grep -Eq ':{config.replica_port}$') "
            f"|| docker ps --format '{{{{.Ports}}}}' | grep -q ':{config.replica_port}->'; "
            "then echo busy; else echo free; fi; "
            f"if docker image inspect {shlex.quote(str(config.benchmark.deployment['image']))} >/dev/null 2>&1; "
            "then echo present; else echo missing; fi"
        )
        try:
            result = _remote(host, user, command, 30)
            lines = result.stdout.decode().splitlines()
            health = request_json(f"{host.endpoint}/health", timeout=10)
            return {
                "id": host.id,
                "tier": host.tier,
                "authority": host.authority,
                "connected": True,
                "worker_ready": health.get("status") == "ready" and health.get("graph_loaded") is True,
                "worker_idle": health.get("idle") is True,
                "cpu_count": int(lines[0]),
                "available_memory_mib": int(lines[1]),
                "load_1m": float(lines[2]),
                "replica_port_available": lines[3] == "free",
                "worker_image_available": lines[4] == "present",
                "health": health,
            }
        except Exception as error:
            return {
                "id": host.id,
                "tier": host.tier,
                "authority": host.authority,
                "connected": False,
                "worker_ready": False,
                "worker_idle": False,
                "available_memory_mib": 0,
                "replica_port_available": False,
                "worker_image_available": False,
                "error": str(error),
            }

    with ThreadPoolExecutor(max_workers=len(topology.hosts)) as pool:
        by_id = {item["id"]: item for item in pool.map(inspect, topology.hosts)}
    return [by_id[host.id] for host in topology.hosts]


def deploy_read_only_replica(
    config: AdaptationConfig,
    topology: Topology,
    run_dir: Path,
    plan: dict,
) -> dict:
    if plan.get("status") != "planned" or plan.get("action") != "deploy_read_only_replica":
        raise ValueError("execute requires a completed deploy_read_only_replica plan")
    target = next((host for host in topology.hosts if host.id == plan.get("target")), None)
    source = next((host for host in topology.hosts if host.id == plan.get("replica_source")), None)
    if target is None or source is None:
        raise ValueError("planned target and replica source must exist in the active topology")
    fragments = run_dir / "before/fragments"
    fragment_path = fragments / f"{source.id}.nt"
    expected_path = run_dir / "before/expected-semantics.json"
    if not fragment_path.is_file() or not expected_path.is_file():
        raise FileNotFoundError("baseline fragment and expected semantics are required before execute")
    expected_fragment = json.loads(expected_path.read_text())[source.id]
    semantic = semantic_environment(config.benchmark, topology)
    replica_id = f"{source.id}-replica-on-{target.id}"
    container_name = f"continuum-adaptation-{run_dir.name}"
    environment = {
        "CONTINUUM_NODE_ID": replica_id,
        "CONTINUUM_TIER": source.tier,
        "CONTINUUM_AUTHORITY": source.authority,
        **semantic,
    }
    env_args = " ".join(f"-e {shlex.quote(key + '=' + str(value))}" for key, value in environment.items())
    image = str(config.benchmark.deployment["image"])
    command = (
        f'test -z "$(docker ps -aq --filter name=^/{shlex.quote(container_name)}$)"; '
        f"docker run -d --name {shlex.quote(container_name)} --restart no "
        f"--cpus {config.cpu_per_replica} --memory {config.memory_mib_per_replica}m --pids-limit 512 "
        f"-p {config.replica_port}:8391 {env_args} {shlex.quote(image)}"
    )
    endpoint = f"http://{target.address}:{config.replica_port}"
    started = monotonic()
    _remote(target, str(config.benchmark.deployment["ssh_user"]), command, 120)
    wait_ready(
        endpoint,
        deadline_seconds=float(config.benchmark.deployment["health_timeout_seconds"]),
        require_idle=True,
        expected={
            "topology_fingerprint": semantic["CONTINUUM_TOPOLOGY_FINGERPRINT"],
            "ontology_digest": semantic["CONTINUUM_ONTOLOGY_DIGEST"],
            "query_catalog_digest": semantic["CONTINUUM_QUERY_CATALOG_DIGEST"],
            "query_count": int(semantic["CONTINUUM_QUERY_COUNT"]),
        },
    )
    container_start_seconds = monotonic() - started
    prepared = _prepare(
        Host(replica_id, source.tier, source.authority, target.address, config.replica_port),
        fragment_path.read_bytes(),
        float(config.benchmark.experiment["prepare_hard_timeout_seconds"]),
        expected_fragment["closure_digest"],
    )
    health = wait_ready(
        endpoint,
        deadline_seconds=float(config.benchmark.deployment["health_timeout_seconds"]),
        require_idle=True,
        expected={
            "dataset_digest": expected_fragment["dataset_digest"],
            "closure_digest": expected_fragment["closure_digest"],
        },
    )
    return {
        "stage": "execute",
        "mode": "scripted_manual",
        "status": "replica_ready",
        "action": "deploy_read_only_replica",
        "target": target.id,
        "replica_source": source.id,
        "replica": {
            "id": replica_id,
            "semantic_role": "read_only_replica",
            "physical_host": target.id,
            "endpoint": endpoint,
            "address": target.address,
            "port": config.replica_port,
            "tier": source.tier,
            "authority": source.authority,
            "local": target.local,
            "container_name": container_name,
            "cpu_limit": config.cpu_per_replica,
            "memory_limit_mib": config.memory_mib_per_replica,
        },
        "container_start_seconds": container_start_seconds,
        "transfer_seconds": prepared["transfer_seconds"],
        "reasoning_seconds": prepared["reasoning"]["reasoning_seconds"],
        "store_load_seconds": prepared["store_load_seconds"],
        "replica_ready_seconds": monotonic() - started,
        "dataset_digest": prepared["dataset_digest"],
        "closure_digest": prepared["closure_digest"],
        "preparation": prepared,
        "health": health,
    }
