from __future__ import annotations

import json
import math
import os
import subprocess
import tarfile
import tempfile
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path

from .config import BenchmarkConfig
from .protocol import wait_ready
from .topology import Host, Topology


def semantic_environment(config: BenchmarkConfig, topology: Topology) -> dict[str, str]:
    catalog = json.loads((config.root / "queries/manifest.json").read_text())
    return {
        "CONTINUUM_TOPOLOGY_FINGERPRINT": topology.fingerprint,
        "CONTINUUM_ONTOLOGY_DIGEST": sha256((config.root / "ontology/benchmark/base.nt").read_bytes()).hexdigest(),
        "CONTINUUM_QUERY_CATALOG_DIGEST": catalog["query_catalog_digest"],
        "CONTINUUM_QUERY_COUNT": str(catalog["query_count"]),
        "CONTINUUM_MAX_PREPARE_BYTES": str(int(config.deployment["max_prepare_mib"]) * 1024 * 1024),
    }


def _run(
    command: list[str], *, timeout: float, cwd: Path | None = None, input_data: bytes | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, input=input_data, capture_output=True, timeout=timeout, check=True)


def _remote(host: Host, user: str, command: str, timeout: float) -> subprocess.CompletedProcess:
    if host.local:
        return _run(["bash", "-lc", command], timeout=timeout)
    return _run(["ssh", "-o", "BatchMode=yes", f"{user}@{host.address}", command], timeout=timeout)


def render(config: BenchmarkConfig, topology: Topology, output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"topology_fingerprint": topology.fingerprint, "hosts": []}
    semantic = semantic_environment(config, topology)
    for host in topology.hosts:
        env_file = output / f"{host.id}.env"
        env_file.write_text(
            "\n".join(
                [
                    f"CONTINUUM_IMAGE={config.deployment['image']}",
                    f"CONTINUUM_PORT={host.port}",
                    f"CONTINUUM_CPUS={config.deployment['cpu_per_container']}",
                    f"CONTINUUM_MEMORY={config.deployment['memory_mib_per_container']}m",
                    f"CONTINUUM_NODE_ID={host.id}",
                    f"CONTINUUM_TIER={host.tier}",
                    f"CONTINUUM_AUTHORITY={host.authority}",
                    *(f"{key}={value}" for key, value in semantic.items()),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        manifest["hosts"].append({"id": host.id, "env_file": env_file.name, "endpoint": host.endpoint})
    (output / "deployment.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output


def doctor(config: BenchmarkConfig, topology: Topology) -> list[dict]:
    user = str(config.deployment["ssh_user"])
    timeout = float(config.deployment["health_timeout_seconds"])
    script = "docker version --format '{{.Server.Version}}'; docker compose version --short; uname -m; docker version --format '{{.Server.Arch}}'; nproc; awk '/MemAvailable/{print $2}' /proc/meminfo; df -Pm . | awk 'NR==2{print $4}'; cat /sys/fs/cgroup/cgroup.controllers"
    evidence = []
    for host in topology.hosts:
        try:
            result = _remote(host, user, script, timeout)
            lines = result.stdout.decode().splitlines()
            cpu_count = int(lines[4])
            memory_kib = int(lines[5])
            disk_mib = int(lines[6])
            controllers = lines[7].split()
            required_memory = (
                int(config.deployment["memory_mib_per_container"]) + int(config.deployment["reserve_memory_mib"])
            ) * 1024
            required_cpus = math.ceil(
                float(config.deployment["cpu_per_container"]) * int(config.deployment["containers_per_host"])
            )
            checks = {
                "cpu": cpu_count >= required_cpus,
                "memory": memory_kib >= required_memory,
                "disk": disk_mib >= int(config.deployment["minimum_free_disk_mib"]),
                "cpu_quota": "cpu" in controllers,
                "memory_cgroup": "memory" in controllers,
                "pid_limit": "pids" in controllers,
            }
            evidence.append(
                {
                    "host": host.id,
                    "ready": all(checks.values()),
                    "checks": checks,
                    "docker": lines[0],
                    "compose": lines[1],
                    "host_architecture": lines[2],
                    "docker_architecture": lines[3],
                    "cpu_count": cpu_count,
                    "mem_available_kib": memory_kib,
                    "disk_available_mib": disk_mib,
                    "cgroup_controllers": controllers,
                }
            )
        except Exception as error:
            evidence.append({"host": host.id, "ready": False, "error": str(error)})
    return evidence


def deploy(config: BenchmarkConfig, topology: Topology, *, build: bool = True) -> list[dict]:
    root = config.root
    user = str(config.deployment["ssh_user"])
    remote_dir = str(config.deployment["remote_dir"])
    timeout = float(config.deployment["operation_timeout_seconds"])
    semantic = semantic_environment(config, topology)
    with tempfile.NamedTemporaryFile(suffix=".tar.gz") as archive:
        with tarfile.open(archive.name, "w:gz") as tar:
            for name in ("rust", "containers/worker"):
                tar.add(
                    root / name, arcname=name, filter=lambda info: None if "target" in Path(info.name).parts else info
                )
        payload = Path(archive.name).read_bytes()

    def deploy_host(host: Host) -> dict:
        try:
            if host.local:
                _run(
                    [
                        "bash",
                        "-lc",
                        (
                            f"fuser -k -TERM {host.port}/tcp >/dev/null 2>&1 || true; "
                            f"docker ps -aq --filter publish={host.port} | xargs -r docker rm -f; sleep 1"
                        ),
                    ],
                    timeout=60,
                )
                if build:
                    _run(
                        ["docker", "compose", "-f", "containers/worker/compose.yaml", "build"],
                        cwd=root,
                        timeout=timeout,
                    )
                env = (
                    os.environ
                    | semantic
                    | {
                        "CONTINUUM_NODE_ID": host.id,
                        "CONTINUUM_TIER": host.tier,
                        "CONTINUUM_AUTHORITY": host.authority,
                        "CONTINUUM_PORT": str(host.port),
                    }
                )
                subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        "containers/worker/compose.yaml",
                        "up",
                        "-d",
                        "--force-recreate",
                        "--remove-orphans",
                    ],
                    cwd=root,
                    env=env,
                    check=True,
                    timeout=timeout,
                )
            else:
                subprocess.run(
                    ["ssh", f"{user}@{host.address}", f"mkdir -p {remote_dir} && tar -xzf - -C {remote_dir}"],
                    input=payload,
                    check=True,
                    timeout=timeout,
                )
                variables = semantic | {
                    "CONTINUUM_NODE_ID": host.id,
                    "CONTINUUM_TIER": host.tier,
                    "CONTINUUM_AUTHORITY": host.authority,
                    "CONTINUUM_PORT": str(host.port),
                }
                prefix = " ".join(f"{key}={value}" for key, value in variables.items())
                command = (
                    f"fuser -k -TERM {host.port}/tcp >/dev/null 2>&1 || true; "
                    f"docker ps -aq --filter publish={host.port} | xargs -r docker rm -f; sleep 1; "
                    f"cd {remote_dir} && {prefix} docker compose -f containers/worker/compose.yaml "
                    f"up -d {'--build' if build else ''} --force-recreate --remove-orphans"
                )
                _remote(host, user, command, timeout)
            health = wait_ready(
                host.endpoint,
                deadline_seconds=float(config.deployment["health_timeout_seconds"]),
                require_idle=True,
                expected={
                    "topology_fingerprint": semantic["CONTINUUM_TOPOLOGY_FINGERPRINT"],
                    "ontology_digest": semantic["CONTINUUM_ONTOLOGY_DIGEST"],
                    "query_catalog_digest": semantic["CONTINUUM_QUERY_CATALOG_DIGEST"],
                    "query_count": int(semantic["CONTINUUM_QUERY_COUNT"]),
                    "max_prepare_bytes": int(semantic["CONTINUUM_MAX_PREPARE_BYTES"]),
                },
            )
            return {"host": host.id, "deployed": True, "health": health}
        except Exception as error:
            return {"host": host.id, "deployed": False, "error": str(error)}

    with ThreadPoolExecutor(max_workers=len(topology.hosts)) as pool:
        by_host = {item["host"]: item for item in pool.map(deploy_host, topology.hosts)}
    return [by_host[host.id] for host in topology.hosts]


def container_states(config: BenchmarkConfig, topology: Topology) -> list[dict]:
    user = str(config.deployment["ssh_user"])
    image = str(config.deployment["image"])
    command = f'id=$(docker ps -aq --filter ancestor={image} | head -1); test -n "$id" || id=$(docker ps -aq --filter label=com.docker.compose.service=worker | head -1); test -n "$id" && docker inspect $id --format \'{{"state":{{{{json .State}}}},"image_digest":"{{{{.Image}}}}","image_name":"{{{{.Config.Image}}}}"}}\''

    def inspect_host(host: Host) -> dict:
        try:
            result = _remote(host, user, command, 30)
            return {"host": host.id, **json.loads(result.stdout)}
        except Exception as error:
            return {"host": host.id, "error": str(error)}

    with ThreadPoolExecutor(max_workers=len(topology.hosts)) as pool:
        return list(pool.map(inspect_host, topology.hosts))


def restart_workers(config: BenchmarkConfig, topology: Topology, host_ids: set[str]) -> list[dict]:
    """Restart workers killed by a measured OOM after their evidence has been captured."""
    user = str(config.deployment["ssh_user"])
    image = str(config.deployment["image"])
    semantic = semantic_environment(config, topology)
    expected = {
        "topology_fingerprint": semantic["CONTINUUM_TOPOLOGY_FINGERPRINT"],
        "ontology_digest": semantic["CONTINUUM_ONTOLOGY_DIGEST"],
        "query_catalog_digest": semantic["CONTINUUM_QUERY_CATALOG_DIGEST"],
        "query_count": int(semantic["CONTINUUM_QUERY_COUNT"]),
        "max_prepare_bytes": int(semantic["CONTINUUM_MAX_PREPARE_BYTES"]),
    }

    def restart(host: Host) -> dict:
        if host.id not in host_ids:
            return {"host": host.id, "required": False}
        command = (
            f'id=$(docker ps -aq --filter ancestor={image} | head -1); test -n "$id" && docker start "$id" >/dev/null'
        )
        try:
            _remote(host, user, command, float(config.deployment["health_timeout_seconds"]))
            health = wait_ready(
                host.endpoint,
                deadline_seconds=float(config.deployment["health_timeout_seconds"]),
                require_idle=True,
                expected=expected,
            )
            return {"host": host.id, "required": True, "recovered": True, "health": health}
        except Exception as error:
            return {"host": host.id, "required": True, "recovered": False, "error": str(error)}

    with ThreadPoolExecutor(max_workers=len(topology.hosts)) as pool:
        return list(pool.map(restart, topology.hosts))
