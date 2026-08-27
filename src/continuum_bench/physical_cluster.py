"""Deployment and lifecycle helpers for the five-host physical inventory."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
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
    host: str
    endpoint: str
    local: bool
    port: int


@dataclass(frozen=True)
class PhysicalInventory:
    path: Path
    ssh_user: str
    remote_dir: str
    remote_python: str
    nodes: tuple[PhysicalNode, ...]


def load_physical_inventory(
    path: Path,
    ssh_user: str | None = None,
) -> PhysicalInventory:
    with path.open("rb") as handle:
        document = tomllib.load(handle)
    cluster = document.get("cluster", {})
    nodes = tuple(
        PhysicalNode(
            role=str(item["role"]),
            host=str(item["host"]),
            endpoint=str(item["endpoint"]).rstrip("/"),
            local=bool(item.get("local", False)),
            port=int(item.get("port", 8080)),
        )
        for item in document.get("nodes", [])
    )
    roles = {node.role for node in nodes}
    expected = {"cloud", "fog", "edge1", "edge2", "edge3"}
    if roles != expected or len(nodes) != 5:
        raise ValueError(
            f"Inventory must define exactly {sorted(expected)}, "
            f"got {sorted(roles)}"
        )
    if sum(node.local for node in nodes) != 1:
        raise ValueError("Inventory must define exactly one local cloud node")
    user = ssh_user or str(cluster.get("ssh_user", "")).strip()
    if not user:
        raise ValueError("Set cluster.ssh_user or pass --ssh-user")
    remote_dir = str(cluster.get("remote_dir", "")).strip().format(
        ssh_user=user
    )
    remote_python = str(cluster.get("remote_python", "")).strip().format(
        ssh_user=user
    )
    if not remote_dir.startswith("/") or not remote_python.startswith("/"):
        raise ValueError("remote_dir and remote_python must be absolute paths")
    return PhysicalInventory(
        path=path,
        ssh_user=user,
        remote_dir=remote_dir,
        remote_python=remote_python,
        nodes=nodes,
    )


def _run(command: list[str]) -> None:
    print(f"[physical-cluster] exec={shlex.join(command)}", flush=True)
    subprocess.run(command, check=True)


def _ssh(target: str, *remote_command: str) -> list[str]:
    return ["ssh", *_SSH_OPTIONS, target, *remote_command]


def authorize_cluster(inventory: PhysicalInventory) -> None:
    """Install the local public key once, using one password prompt per host."""
    for node in inventory.nodes:
        if node.local:
            continue
        target = f"{inventory.ssh_user}@{node.host}"
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
    for node in inventory.nodes:
        if node.local:
            continue
        target = f"{inventory.ssh_user}@{node.host}"
        result = subprocess.run(
            _ssh(target, "true"),
            check=False,
            capture_output=True,
            text=True,
        )
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


def deploy_cluster(
    root: Path,
    inventory: PhysicalInventory,
) -> None:
    """Copy only worker runtime assets and install minimal dependencies."""
    _verify_key_auth(inventory)
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
    for node in inventory.nodes:
        if node.local:
            continue
        target = f"{inventory.ssh_user}@{node.host}"
        _run(
            _ssh(
                target,
                "mkdir",
                "-p",
                inventory.remote_dir,
                f"{inventory.remote_dir}/runtime",
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
                    f"{target}:{inventory.remote_dir}/",
                ]
            )
        setup = (
            f"python3 -m venv {shlex.quote(inventory.remote_dir + '/.venv-node')}"
            f" && {shlex.quote(inventory.remote_dir + '/.venv-node/bin/pip')}"
            f" install -r "
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


def _local_start(root: Path, node: PhysicalNode) -> None:
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
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "continuum_bench.node",
            "--root",
            str(root),
            "--role",
            node.role,
            "--host",
            "0.0.0.0",
            "--port",
            str(node.port),
        ],
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
        + r" -m continuum_bench\.node .*--role "
        + re.escape(node.role)
        + r" .*--port "
        + str(node.port)
        + r"( |$)"
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
        f"--role {shlex.quote(node.role)} --host 0.0.0.0 "
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
            _local_start(root, node)
        else:
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
            print("[physical-cluster] nodes=5 status=ready", flush=True)
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
    if "continuum_bench.node" not in command or f"--role {role}" not in command:
        raise RuntimeError(
            f"Refusing to stop PID {pid}: it is not the expected {role} worker"
        )
    os.kill(pid, signal.SIGTERM)
    pid_path.unlink()


def _safe_remote_stop(
    inventory: PhysicalInventory,
    node: PhysicalNode,
) -> None:
    target = f"{inventory.ssh_user}@{node.host}"
    pid_path = f"{inventory.remote_dir}/runtime/{node.role}.pid"
    worker_pattern = (
        "^"
        + re.escape(inventory.remote_python)
        + r" -m continuum_bench\.node .*--role "
        + re.escape(node.role)
        + r" .*--port "
        + str(node.port)
        + r"( |$)"
    )
    command = (
        f"pids=$(pgrep -f {shlex.quote(worker_pattern)} 2>/dev/null || true); "
        'for pid in $pids; do kill "$pid"; done; '
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
                expected_role=node.role,
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
                "host": node.host,
                "endpoint": node.endpoint,
                "healthy": healthy,
                "detail": detail,
            }
        )
    if print_output:
        print(json.dumps(statuses, indent=2, ensure_ascii=False))
    return statuses
