"""Deployment and lifecycle helpers for an elastic physical topology."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import signal
import subprocess
import sys
import time
import tomllib
from typing import Any
from urllib.error import URLError

from .distributed import _request
from .protocol import worker_health_error
from .environment import physical_checks, require_checks
from .topology import (
    Topology,
    default_categories,
    infer_tier,
    load_topology,
    render_flat_topology,
)


_SSH_OPTIONS = (
    "-o",
    "BatchMode=yes",
    "-o",
    "ConnectTimeout=10",
    "-o",
    "ServerAliveInterval=5",
    "-o",
    "ServerAliveCountMax=2",
)
_RSYNC_SSH = "ssh " + " ".join(_SSH_OPTIONS)


@dataclass(frozen=True)
class PhysicalNode:
    role: str
    tier: str
    host: str
    endpoint: str
    local: bool
    port: int
    authority: bool
    categories: tuple[str, ...]

    @property
    def node_id(self) -> str:
        return self.role


@dataclass(frozen=True)
class PhysicalInventory:
    path: Path
    ssh_user: str
    remote_dir: str
    remote_python: str
    nodes: tuple[PhysicalNode, ...]
    topology_name: str = "physical"
    topology: Topology | None = None


def load_physical_inventory(
    path: Path,
    ssh_user: str | None = None,
    topology_name: str = "physical",
) -> PhysicalInventory:
    with path.open("rb") as handle:
        document = tomllib.load(handle)
    configured_topology: Topology | None = None
    manifest_metadata = document.get("manifest", {})
    is_topology_manifest = (
        "topologies" in document
        or "topology" in document
        or "topology_files" in manifest_metadata
    )
    project_root = path.parent
    if is_topology_manifest:
        configured_topology = load_topology(path, topology_name)
        if configured_topology.kind != "physical":
            raise ValueError(
                f"Topology {topology_name!r} is not a physical topology"
            )
        nodes = tuple(
            PhysicalNode(
                role=item.node_id,
                tier=item.tier,
                host=item.host,
                endpoint=item.endpoint,
                local=item.local,
                port=item.port,
                authority=item.authority,
                categories=item.categories,
            )
            for item in configured_topology.active_nodes
        )
        user = ssh_user or configured_topology.ssh_user
        # Preserve placeholders until the optional command-line SSH user is
        # known. Otherwise --ssh-user would leave /home/{old-user} paths.
        remote_dir_template = configured_topology.remote_dir_template
        remote_python_template = configured_topology.remote_python_template
        project_root = configured_topology.project_root or path.parent
    else:
        # Backward-compatible reader for old experiment inventories. New
        # deployments should use the composed topology catalogue.
        cluster = document.get("cluster", {})
        nodes = tuple(
            PhysicalNode(
                role=str(item["role"]),
                tier=str(item.get("tier", infer_tier(str(item["role"])))),
                host=str(item["host"]),
                endpoint=str(item["endpoint"]).rstrip("/"),
                local=bool(item.get("local", False)),
                port=int(item.get("port", 8080)),
                authority=bool(
                    item.get(
                        "authority",
                        infer_tier(str(item["role"])) in {"edge", "iot"},
                    )
                ),
                categories=tuple(
                    item.get(
                        "categories",
                        default_categories(
                            str(item.get("tier", infer_tier(str(item["role"]))))
                        ),
                    )
                ),
            )
            for item in document.get("nodes", [])
        )
        user = ssh_user or str(cluster.get("ssh_user", "")).strip()
        remote_dir_template = str(cluster.get("remote_dir", ""))
        remote_python_template = str(cluster.get("remote_python", ""))
    if not nodes:
        raise ValueError("Physical inventory must define at least one node")
    roles = [node.role for node in nodes]
    endpoints = [node.endpoint for node in nodes]
    if len(roles) != len(set(roles)):
        raise ValueError(f"Duplicate physical node ids: {roles}")
    if len(endpoints) != len(set(endpoints)):
        raise ValueError(f"Duplicate physical endpoints: {endpoints}")
    if not any(node.local for node in nodes):
        raise ValueError("Inventory must define at least one local node")
    if not user:
        raise ValueError("Set cluster.ssh_user or pass --ssh-user")
    remote_dir = remote_dir_template.strip().format(
        ssh_user=user,
        root=str(project_root),
    )
    remote_python = remote_python_template.strip().format(
        ssh_user=user,
        root=str(project_root),
    )
    if not remote_dir.startswith("/") or not remote_python.startswith("/"):
        raise ValueError("remote_dir and remote_python must be absolute paths")
    directory = PurePosixPath(remote_dir)
    if (
        len(directory.parts) < 3
        or ".." in directory.parts
        or str(directory) in {f"/home/{user}", f"/Users/{user}", "/root", "/tmp", "/var/tmp"}
        or not PurePosixPath(remote_python).is_relative_to(directory)
        or ".." in PurePosixPath(remote_python).parts
    ):
        raise ValueError("Use a dedicated remote_dir below the user's home and a remote_python inside that directory; broad deployment targets are unsafe")
    return PhysicalInventory(
        path=path,
        ssh_user=user,
        remote_dir=remote_dir,
        remote_python=remote_python,
        nodes=nodes,
        topology_name=topology_name,
        topology=configured_topology,
    )


def _run(command: list[str]) -> None:
    print(f"[physical-cluster] exec={shlex.join(command)}", flush=True)
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError as error:
        raise RuntimeError(f"Required command not installed: {command[0]}. Run 'python3 tools/doctor.py --physical'.") from error


def _ssh(target: str, *remote_command: str) -> list[str]:
    return ["ssh", *_SSH_OPTIONS, target, *remote_command]


def authorize_cluster(inventory: PhysicalInventory) -> None:
    """Install the local public key once, using one password prompt per host."""
    seen: set[str] = set()
    for node in inventory.nodes:
        if node.local:
            continue
        target = f"{inventory.ssh_user}@{node.host}"
        if target in seen:
            continue
        seen.add(target)
        print(
            f"[physical-cluster] role={node.role} host={node.host} "
            "phase=ssh-key-authorization",
            flush=True,
        )
        try:
            _run(["ssh-copy-id", target])
        except (FileNotFoundError, subprocess.CalledProcessError) as error:
            raise RuntimeError(
                f"Could not authorize SSH key for {target}. Ensure a local "
                "key exists with 'ssh-keygen -t ed25519', then retry "
                "'physical authorize'."
            ) from error


def _verify_key_auth(inventory: PhysicalInventory) -> None:
    """Fail before lifecycle work instead of blocking on password prompts."""
    failed: list[str] = []
    require_checks([item for item in physical_checks() if item.name == "ssh"])
    seen: set[str] = set()
    for node in inventory.nodes:
        if node.local:
            continue
        target = f"{inventory.ssh_user}@{node.host}"
        if target in seen:
            continue
        seen.add(target)
        try:
            result = subprocess.run(
                _ssh(target, "true"),
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            failed.append(f"{target}: {error}")
            continue
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            failed.append(f"{target}: {detail or 'authentication failed'}")
    if failed:
        raise RuntimeError(
            "Passwordless SSH is required for physical lifecycle commands. "
            "Run 'continuum-bench physical authorize --ssh-user USER' first. "
            "Failures: "
            + "; ".join(failed)
        )


def _verify_remote_dependencies(inventory: PhysicalInventory) -> None:
    """Check every remote before rsync mutates any deployed release."""
    require_checks([item for item in physical_checks() if item.name in {"ssh", "rsync"}])
    python_check = (
        "import sys, venv, ensurepip; "
        "assert sys.version_info >= (3, 11), 'Python >=3.11 required'; "
        "print(sys.version.split()[0])"
    )
    command = " && ".join([
        "command -v rsync", "command -v pgrep", "command -v nohup",
        "python3 -c " + shlex.quote(python_check),
    ])
    failures = []
    seen: set[str] = set()
    for node in inventory.nodes:
        if node.local:
            continue
        target = f"{inventory.ssh_user}@{node.host}"
        if target in seen:
            continue
        seen.add(target)
        try:
            result = subprocess.run(_ssh(target, command), capture_output=True, text=True, timeout=25, check=False)
            if result.returncode:
                failures.append(f"{target}: {(result.stderr or result.stdout).strip()}")
        except (OSError, subprocess.TimeoutExpired) as error:
            failures.append(f"{target}: {error}")
    if failures:
        raise RuntimeError(
            "Remote prerequisites failed before copying any files. Install Python >=3.11, python3-venv, rsync and procps on every Raspberry. "
            + "; ".join(failures)
        )


def deploy_cluster(
    root: Path,
    inventory: PhysicalInventory,
) -> None:
    """Copy only worker runtime assets and install minimal dependencies."""
    _verify_key_auth(inventory)
    _verify_remote_dependencies(inventory)
    sources = (
        root / "src",
        root / "configs",
        root / "ontology",
        root / "queries",
        root / "requirements-node.txt",
    )
    for source in sources:
        if not source.exists():
            raise FileNotFoundError(source)
    effective_topology = (
        render_flat_topology(
            inventory.topology,
            _runtime_dir(root) / "active-topology.toml",
        )
        if inventory.topology is not None
        else None
    )
    seen: set[str] = set()
    for node in inventory.nodes:
        if node.local:
            continue
        target = f"{inventory.ssh_user}@{node.host}"
        if target in seen:
            continue
        seen.add(target)
        _run(
            _ssh(
                target,
                "mkdir -p " + shlex.quote(inventory.remote_dir) + " "
                + shlex.quote(f"{inventory.remote_dir}/runtime"),
            )
        )
        for source in sources:
            rsync_options = ["rsync", "-az"]
            if source.is_dir():
                # Deployment directories are release-owned. Mirroring them
                # removes stale v2 query/category files without touching the
                # worker runtime, virtualenv, logs or any parent directory.
                rsync_options.append("--delete")
            _run(
                [
                    *rsync_options,
                    "-e",
                    _RSYNC_SSH,
                    str(source),
                    f"{target}:{shlex.quote(inventory.remote_dir + '/')}",
                ]
            )
        if inventory.topology is not None:
            # The selected catalogue or leaf may live at any path.
            # Copy it to a stable runtime path so deploy and start always use
            # exactly the topology validated by the coordinator.
            _run(
                [
                    "rsync",
                    "-az",
                    "-e",
                    _RSYNC_SSH,
                    str(effective_topology),
                    (
                        f"{target}:"
                        f"{shlex.quote(inventory.remote_dir + '/runtime/' + 'active-topology.toml')}"
                    ),
                ]
            )
        setup = (
            f"python3 -m venv {shlex.quote(inventory.remote_dir + '/.venv-node')}"
            f" && {shlex.quote(inventory.remote_dir + '/.venv-node/bin/pip')}"
            f" install --only-binary=:all: --retries 2 --timeout 60 -r "
            f"{shlex.quote(inventory.remote_dir + '/requirements-node.txt')}"
        )
        _run(_ssh(target, setup))
        print(
            f"[physical-cluster] role={node.role} host={node.host} "
            "status=deployed",
            flush=True,
        )


def _runtime_dir(root: Path) -> Path:
    path = root / "outputs" / "physical" / "runtime"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _local_start(
    root: Path,
    inventory: PhysicalInventory,
    node: PhysicalNode,
) -> None:
    runtime = _runtime_dir(root)
    pid_path = runtime / f"{node.role}.pid"
    if pid_path.is_file():
        pid = int(pid_path.read_text(encoding="utf-8").strip())
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pid_path.unlink()
        else:
            raise RuntimeError(
                f"Local {node.role} appears to be running with PID {pid}"
            )
    log = (runtime / f"{node.role}.log").open("a", encoding="utf-8")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(root / "src")
    command = [
        sys.executable,
        "-m",
        "continuum_bench.node",
        "--root",
        str(root),
        "--node-id",
        node.role,
        "--tier",
        node.tier,
    ]
    if inventory.topology is not None:
        command.extend(
            [
                "--topology-file",
                str(inventory.path),
                "--topology-name",
                inventory.topology_name,
            ]
        )
    command.extend(["--host", "0.0.0.0", "--port", str(node.port)])
    process = subprocess.Popen(
        command,
        cwd=root,
        env=environment,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    pid_path.write_text(f"{process.pid}\n", encoding="utf-8")


def _remote_start(
    inventory: PhysicalInventory,
    node: PhysicalNode,
) -> None:
    target = f"{inventory.ssh_user}@{node.host}"
    runtime = f"{inventory.remote_dir}/runtime"
    pid_path = f"{runtime}/{node.role}.pid"
    log_path = f"{runtime}/{node.role}.log"
    worker_pattern = (
        "^"
        + re.escape(inventory.remote_python)
        + r" -m continuum_bench\.node .*--node-id "
        + re.escape(node.role)
        + r" .*--port "
        + str(node.port)
        + r"( |$)"
    )
    topology_arguments = (
        f"--topology-file "
        f"{shlex.quote(inventory.remote_dir + '/runtime/active-topology.toml')} "
        f"--topology-name {shlex.quote(inventory.topology_name)} "
        if inventory.topology is not None
        else ""
    )
    command = (
        f"mkdir -p {shlex.quote(runtime)} && "
        f"existing=$(pgrep -f {shlex.quote(worker_pattern)} "
        "2>/dev/null | head -n 1 || true); "
        'if test -n "$existing"; then '
        f"echo \"$existing\" > {shlex.quote(pid_path)}; exit 17; fi; "
        f"rm -f {shlex.quote(pid_path)}; "
        f"cd {shlex.quote(inventory.remote_dir)} || exit 20; "
        f"nohup env PYTHONPATH={shlex.quote(inventory.remote_dir + '/src')} "
        f"{shlex.quote(inventory.remote_python)} "
        "-m continuum_bench.node "
        f"--root {shlex.quote(inventory.remote_dir)} "
        f"--node-id {shlex.quote(node.role)} "
        f"--tier {shlex.quote(node.tier)} "
        f"{topology_arguments}"
        "--host 0.0.0.0 "
        f"--port {node.port} > {shlex.quote(log_path)} 2>&1 "
        "< /dev/null & worker_pid=$!; "
        f"echo \"$worker_pid\" > {shlex.quote(pid_path)}; "
        'sleep 1; if ! kill -0 "$worker_pid" 2>/dev/null; then '
        f"rm -f {shlex.quote(pid_path)}; "
        f"tail -n 20 {shlex.quote(log_path)} >&2; exit 21; fi"
    )
    _run(_ssh(target, command))


def start_cluster(
    root: Path,
    inventory: PhysicalInventory,
    wait_seconds: float = 30.0,
) -> None:
    _verify_key_auth(inventory)
    current = {
        item["role"]: item
        for item in status_cluster(inventory, print_output=False)
    }
    for node in inventory.nodes:
        if current[node.role]["healthy"]:
            print(
                f"[physical-cluster] role={node.role} host={node.host} "
                "status=already-running",
                flush=True,
            )
            continue
        if node.local:
            _safe_local_stop(root, node.role)
            _local_start(root, inventory, node)
        else:
            # A worker with a stale topology fingerprint is unhealthy by
            # contract but may still own the port. Stop only the exact managed
            # process before starting the current manifest revision.
            _safe_remote_stop(inventory, node)
            _remote_start(inventory, node)
        print(
            f"[physical-cluster] role={node.role} host={node.host} "
            "status=starting",
            flush=True,
        )
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        statuses = status_cluster(inventory, print_output=False)
        if all(item["healthy"] for item in statuses):
            print(
                f"[physical-cluster] nodes={len(inventory.nodes)} status=ready",
                flush=True,
            )
            return
        time.sleep(0.5)
    raise TimeoutError(
        "Physical nodes did not become healthy; run 'physical status' "
        "and inspect outputs/physical/runtime/cloud.log plus remote runtime logs"
    )


def _safe_local_stop(root: Path, role: str) -> None:
    pid_path = _runtime_dir(root) / f"{role}.pid"
    if not pid_path.is_file():
        return
    pid = int(pid_path.read_text(encoding="utf-8").strip())
    command = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="],
        check=False,
        capture_output=True,
        text=True,
    ).stdout
    if (
        "continuum_bench.node" not in command
        or f"--node-id {role}" not in command
    ):
        raise RuntimeError(
            f"Refusing to stop PID {pid}: it is not the expected {role} worker"
        )
    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + 5.0
    while True:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Local {role} worker PID {pid} did not stop within 5 seconds"
            )
        time.sleep(0.05)
    pid_path.unlink(missing_ok=True)


def _safe_remote_stop(
    inventory: PhysicalInventory,
    node: PhysicalNode,
) -> None:
    target = f"{inventory.ssh_user}@{node.host}"
    pid_path = f"{inventory.remote_dir}/runtime/{node.role}.pid"
    worker_pattern = (
        "^"
        + re.escape(inventory.remote_python)
        + r" -m continuum_bench\.node .*--node-id "
        + re.escape(node.role)
        + r" .*--port "
        + str(node.port)
        + r"( |$)"
    )
    command = (
        f"pids=$(pgrep -f {shlex.quote(worker_pattern)} 2>/dev/null || true); "
        'for pid in $pids; do kill "$pid"; '
        'attempt=0; while kill -0 "$pid" 2>/dev/null; do '
        'attempt=$((attempt + 1)); '
        'if test "$attempt" -ge 50; then exit 22; fi; sleep 0.1; '
        'done; done; '
        f"rm -f {shlex.quote(pid_path)}"
    )
    _run(_ssh(target, command))


def stop_cluster(root: Path, inventory: PhysicalInventory) -> None:
    _verify_key_auth(inventory)
    for node in inventory.nodes:
        if node.local:
            _safe_local_stop(root, node.role)
        else:
            _safe_remote_stop(inventory, node)
        print(
            f"[physical-cluster] role={node.role} host={node.host} "
            "status=stopped",
            flush=True,
        )


def status_cluster(
    inventory: PhysicalInventory,
    *,
    print_output: bool = True,
) -> list[dict[str, Any]]:
    statuses: list[dict[str, Any]] = []
    for node in inventory.nodes:
        try:
            health = _request(node.endpoint, "/health", timeout=2.0)
            contract_error = worker_health_error(
                health,
                expected_node_id=node.role,
                expected_tier=node.tier,
                expected_authority=node.authority,
                expected_categories=node.categories,
                expected_topology_fingerprint=(
                    inventory.topology.fingerprint
                    if inventory.topology is not None
                    else None
                ),
            )
            healthy = contract_error is None
            detail = {
                **health,
                **(
                    {}
                    if contract_error is None
                    else {"contract_error": contract_error}
                ),
            }
        except (OSError, URLError, TimeoutError) as error:
            healthy = False
            detail = {"error": str(error)}
        statuses.append(
            {
                "role": node.role,
                "node_id": node.role,
                "tier": node.tier,
                "host": node.host,
                "endpoint": node.endpoint,
                "healthy": healthy,
                "detail": detail,
            }
        )
    if print_output:
        print(json.dumps(statuses, indent=2, ensure_ascii=False))
    return statuses
