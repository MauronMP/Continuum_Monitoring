"""Host-local Compose deployment, bounded SSH operations and capacity probes."""

import json
import os
import shlex
import subprocess
import tarfile
import time
from urllib.request import urlopen

from ...topology import render_flat_topology
from .config import logical_topology

# Read actual availability, rather than treating SD-card size as RAM.
PROBE = """import json,os,platform,shutil,subprocess
from pathlib import Path
m={l.split(':')[0]:int(l.split()[1])//1024 for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith(('MemTotal:','MemAvailable:'))}
p=subprocess.run(['docker','info','--format','{{json .}}'],capture_output=True,text=True)
v=subprocess.run(['docker','compose','version','--short'],capture_output=True,text=True)
info=json.loads(p.stdout) if p.returncode==0 else {}
docker_path=Path(info.get('DockerRootDir','/'))
while not os.access(docker_path,os.R_OK|os.X_OK) and docker_path.parent!=docker_path: docker_path=docker_path.parent
print(json.dumps(dict(memory_total_mib=m['MemTotal'],memory_available_mib=m['MemAvailable'],cpu_count=os.cpu_count(),disk_available_mib=shutil.disk_usage(docker_path).free//1048576,architecture=platform.machine(),docker_operating_system=info.get('OperatingSystem',''),docker_name=info.get('Name',''),docker_ok=p.returncode==0,compose_ok=v.returncode==0,docker_error=p.stderr.strip(),memory_limit_supported=info.get('MemoryLimit',False),swap_limit_supported=info.get('SwapLimit',False),cpu_quota_supported=info.get('CpuCfsQuota',False),pids_limit_supported=info.get('PidsLimit',False),docker_version=info.get('ServerVersion'),docker_root=info.get('DockerRootDir'),docker_architecture=info.get('Architecture'),compose_version=v.stdout.strip())))
"""


def execute(config, node, arguments, *, input=None, timeout=None):
    command = (
        list(arguments)
        if node.local
        else [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=10",
            "-o",
            "ServerAliveInterval=10",
            "-o",
            "ServerAliveCountMax=3",
            f"{config.deployment['ssh_user']}@{node.host}",
            shlex.join(arguments),
        ]
    )
    result = subprocess.run(
        command,
        input=input,
        capture_output=True,
        text=True,
        timeout=timeout or config.deployment["operation_timeout_seconds"],
        # The local physical host must not silently become a Docker Desktop VM.
        env={**os.environ, "DOCKER_CONTEXT": "default"} if node.local else None,
    )
    if result.returncode:
        raise RuntimeError(
            f"{node.node_id}: command failed ({result.returncode}): {result.stderr[-8000:]} {result.stdout[-2000:]}"
        )
    return result.stdout


def selected_hosts(config, host_ids=None):
    nodes = config.topology.active_nodes
    if host_ids:
        unknown = set(host_ids) - {n.node_id for n in nodes}
        if unknown:
            raise ValueError(f"Unknown or excluded lifecycle hosts: {sorted(unknown)}")
        nodes = tuple(n for n in nodes if n.node_id in host_ids)
    return nodes


def doctor(config, count, host_ids=None):
    rows = []
    for node in selected_hosts(config, host_ids):
        try:
            data = json.loads(
                execute(config, node, ["python3", "-c", PROBE], timeout=60)
            )
            reasons = []
            if "docker desktop" in data.get("docker_operating_system", "").lower() or data.get("docker_name") == "docker-desktop":
                reasons.append("Physical campaigns require the native host Docker Engine, not Docker Desktop")
            if not data["docker_ok"] or not data["compose_ok"]:
                reasons.append(
                    "Docker Engine and Compose must be accessible to the deployment user"
                )
            if not all(
                data.get(k, False)
                for k in (
                    "memory_limit_supported",
                    "swap_limit_supported",
                    "cpu_quota_supported",
                    "pids_limit_supported",
                )
            ):
                reasons.append(
                    "Kernel cgroup resource limits unavailable; enable memory cgroups and reboot before acquisition"
                )
            needed = (
                count * config.deployment["memory_mib_per_container"]
                + config.deployment["reserve_memory_mib"]
            )
            if data["memory_available_mib"] < needed:
                reasons.append(f"Available RAM below {needed} MiB deployment budget")
            if data["disk_available_mib"] < config.deployment["minimum_free_disk_mib"]:
                reasons.append("Insufficient free disk space")
            if data["cpu_count"] < count * config.deployment["cpu_per_container"]:
                reasons.append("CPU budget exceeds detected cores")
            rows.append(
                dict(
                    host_id=node.node_id,
                    host=node.host,
                    tier=node.tier,
                    **data,
                    ready=not reasons,
                    errors=reasons,
                )
            )
        except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
            rows.append(
                dict(
                    host_id=node.node_id,
                    host=node.host,
                    ready=False,
                    errors=[str(error)],
                )
            )
        print(
            f"[container-scale] doctor host={node.node_id} ready={rows[-1]['ready']}",
            flush=True,
        )
    return rows


def compose_document(config, node, count):
    d = config.deployment
    topology = logical_topology(config, count)
    services = {}
    for participant in topology.active_nodes:
        if participant.host != node.host:
            continue
        services[participant.node_id] = {
            "image": d["image"],
            "build": {
                "context": ".",
                "dockerfile": "Dockerfile",
                # Use the coordinator's resolver during dependency downloads.
                # This does not change the experiment container's runtime network.
                **({"network": "host"} if node.local else {}),
                "args": {"INSTALL_DL": str(d["install_dl"]).lower()},
            },
            "init": True,
            "restart": "no",
            "cpus": d["cpu_per_container"],
            "mem_limit": f"{d['memory_mib_per_container']}m",
            "memswap_limit": f"{d['memory_mib_per_container']}m",
            "pids_limit": 256,
            "security_opt": ["no-new-privileges:true"],
            "cap_drop": ["ALL"],
            "ports": [f"{node.host}:{participant.port}:8080"],
            "volumes": ["./topology.toml:/app/configs/container-topology.toml:ro"],
            "command": [
                "--node-id",
                participant.node_id,
                "--tier",
                node.tier,
                "--topology-file",
                "configs/container-topology.toml",
                "--topology-name",
                "container-scale",
            ],
            "logging": {
                "driver": "json-file",
                "options": {"max-size": "5m", "max-file": "2"},
            },
            "healthcheck": {
                "test": [
                    "CMD",
                    "python",
                    "-c",
                    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)",
                ],
                "interval": "30s",
                "timeout": "5s",
                "retries": 3,
            },
            "labels": {
                "continuum.physical_host": node.node_id,
                "continuum.tier": node.tier,
            },
        }
    return {"name": "continuum-container-scale", "services": services}


def build_image(config, root, node, directory):
    """Retry transient DNS failures once; preserve both attempts for diagnosis."""
    for attempt in range(1, 3):
        log = directory / f"{node.node_id}-build-attempt-{attempt}.log"
        try:
            output = compose(config, root, node, "build", f"{node.node_id}-c1")
        except RuntimeError as error:
            detail = str(error)
            log.write_text(detail + "\n")
            (directory / f"{node.node_id}-build.log").write_text(detail + "\n")
            if attempt == 2 or "temporary failure in name resolution" not in detail.lower():
                raise
            print(
                f"[container-scale] host={node.node_id} phase=build "
                "status=retrying reason=temporary-dns-failure attempt=2/2 delay_s=10",
                flush=True,
            )
            time.sleep(10)
        else:
            log.write_text(output)
            (directory / f"{node.node_id}-build.log").write_text(output)
            return


def render(config, root, directory, count):
    directory.mkdir(parents=True, exist_ok=True)
    topology = logical_topology(config, count)
    render_flat_topology(topology, directory / "topology.toml")
    for node in config.topology.active_nodes:
        (directory / f"{node.node_id}.compose.json").write_text(
            json.dumps(compose_document(config, node, count), indent=2) + "\n"
        )
    (directory / "placement.json").write_text(
        json.dumps(
            {
                "physical_hosts": [n.public() for n in config.topology.active_nodes],
                "participants": [n.public() for n in topology.active_nodes],
                "containers_per_host": count,
                "topology_fingerprint": topology.fingerprint,
                "network_shaping": False,
            },
            indent=2,
        )
        + "\n"
    )
    return topology


def host_directory(config, root, node):
    return (
        str(root / "outputs/runtime/container-scale/host")
        if node.local
        else config.deployment["remote_dir"]
    )


def compose(config, root, node, *args):
    directory = host_directory(config, root, node)
    return execute(
        config,
        node,
        [
            "docker",
            "compose",
            "--project-directory",
            directory,
            "-f",
            f"{directory}/compose.json",
            *args,
        ],
    )


def deploy(config, root, directory, count, *, build=True, host_ids=None):
    probes = doctor(config, count, host_ids)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "preflight.json").write_text(json.dumps(probes, indent=2) + "\n")
    if not all(p["ready"] for p in probes):
        raise RuntimeError(
            f"Capacity/runtime preflight failed; inspect {directory / 'preflight.json'}"
        )
    topology = render(config, root, directory, count)
    archive = directory / "context.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        for name in (
            "src",
            "configs",
            "ontology",
            "queries",
            "tools",
            "requirements-node.txt",
        ):
            bundle.add(
                root / name,
                arcname=name,
                filter=lambda item: (
                    None
                    if "__pycache__" in item.name
                    or item.name.endswith((".pyc", ".local.toml"))
                    or item.name.startswith("configs/local")
                    else item
                ),
            )
        bundle.add(root / "containers/worker/Dockerfile", arcname="Dockerfile")
        bundle.add(directory / "topology.toml", arcname="topology.toml")
    for node in selected_hosts(config, host_ids):
        dest = host_directory(config, root, node)
        execute(config, node, ["mkdir", "-p", dest])
        # Clear only managed build-input directories to prevent deleted source files
        # surviving a later deployment and changing the worker source fingerprint.
        execute(
            config,
            node,
            [
                "python3",
                "-c",
                "import pathlib,shutil,sys; root=pathlib.Path(sys.argv[1]); "
                "[(p.unlink() if p.is_symlink() or p.is_file() else shutil.rmtree(p)) "
                "for p in (root/n for n in ('src','configs','ontology','queries','tools')) if p.exists() or p.is_symlink()]",
                dest,
            ],
        )
        if node.local:
            execute(config, node, ["tar", "-xzf", str(archive), "-C", dest])
        else:
            subprocess.run(
                [
                    "scp",
                    "-q",
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "ConnectTimeout=10",
                    str(archive),
                    f"{config.deployment['ssh_user']}@{node.host}:{dest}/context.tar.gz",
                ],
                check=True,
                timeout=config.deployment["operation_timeout_seconds"],
            )
            execute(config, node, ["tar", "-xzf", f"{dest}/context.tar.gz", "-C", dest])
            execute(config, node, ["rm", "-f", f"{dest}/context.tar.gz"])
        execute(
            config,
            node,
            [
                "python3",
                "-c",
                "import sys; from pathlib import Path; Path(sys.argv[1]).write_text(sys.stdin.read())",
                f"{dest}/compose.json",
            ],
            input=json.dumps(compose_document(config, node, count)),
        )
        compose(config, root, node, "config", "--quiet")
        print(f"[container-scale] deploy host={node.node_id} build={build}", flush=True)
        if build:
            # One image per host; all participants reuse its layers.
            build_image(config, root, node, directory)
        compose(
            config,
            root,
            node,
            "up",
            "-d",
            "--no-build",
            "--remove-orphans",
            "--force-recreate",
        )
    wait_ready(config, topology, host_ids)
    return topology


def wait_ready(config, topology, host_ids=None, *, node_ids=None):
    from ...protocol import worker_health_error

    deadline = time.monotonic() + config.deployment["health_timeout_seconds"]
    hosts = {n.host for n in selected_hosts(config, host_ids)}
    pending = {n.endpoint: n for n in topology.active_nodes if n.host in hosts and (node_ids is None or n.node_id in node_ids)}
    errors = {}
    while pending and time.monotonic() < deadline:
        for url, node in list(pending.items()):
            try:
                with urlopen(url + "/health", timeout=2) as response:
                    health = json.load(response)
                error = worker_health_error(
                    health,
                    expected_node_id=node.node_id,
                    expected_tier=node.tier,
                    expected_authority=node.authority,
                    expected_categories=node.categories,
                    expected_topology_fingerprint=topology.fingerprint,
                )
                if error is None:
                    pending.pop(url)
                    errors.pop(url, None)
                else:
                    errors[url] = error
            except (OSError, ValueError) as error:
                errors[url] = str(error)
        if pending:
            time.sleep(1)
    if pending:
        raise RuntimeError(f"Container workers did not become ready: {errors}")


def collect(config, root, host_ids=None):
    evidence = []
    for node in selected_hosts(config, host_ids):
        record = {"physical_host": node.node_id, "host": node.host, "tier": node.tier}
        try:
            ids = compose(config, root, node, "ps", "-aq").split()
            record["containers"] = (
                json.loads(execute(config, node, ["docker", "inspect", *ids]))
                if ids
                else []
            )
            record["stats"] = (
                execute(
                    config,
                    node,
                    ["docker", "stats", "--no-stream", "--format", "{{json .}}", *ids],
                )
                if ids
                else ""
            )
        except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
            record["error"] = str(error)
        evidence.append(record)
    return evidence


def stop(config, root, host_ids=None):
    errors = []
    for node in selected_hosts(config, host_ids):
        try:
            compose(config, root, node, "down", "--timeout", "15")
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            errors.append(f"{node.node_id}: {error}")
    if errors:
        raise RuntimeError("; ".join(errors))


def validate_reasoners(config, root, host_ids=None):
    """Exercise real entailment as the unprivileged user of every host image."""
    evidence = []
    for node in selected_hosts(config, host_ids):
        for reasoner in config.experiment["reasoners"]:
            record = {"host": node.node_id, "reasoner": reasoner}
            try:
                record["output"] = compose(
                    config, root, node, "exec", "-T", f"{node.node_id}-c1",
                    "python", "tools/owl/verify_materialization.py", reasoner,
                )
                record["status"] = "passed"
            except (OSError, RuntimeError, subprocess.SubprocessError) as error:
                record.update(status="failed", error=str(error))
            evidence.append(record)
            print(f"[container-scale] host={node.node_id} reasoner={reasoner} status={record['status']}", flush=True)
    return evidence
