"""Lifecycle boundary for an elastic local Docker Compose continuum."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
from time import monotonic, sleep

from .distributed import Endpoint, discover
from .topology import Topology, render_docker_compose, run_docker_topology


def require_docker() -> None:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker is not installed or is not on PATH")
    result = subprocess.run(
        ["docker", "compose", "version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Docker Compose v2 is unavailable: {detail}")


def compose_path(root: Path, topology: Topology) -> Path:
    return root / "outputs" / "runtime" / f"docker-compose-{topology.name}.yml"


def manage(root: Path, topology: Topology, action: str) -> int:
    require_docker()
    return run_docker_topology(
        topology,
        compose_path(root, topology),
        action,
        root=root,
    )


def render(root: Path, topology: Topology) -> Path:
    return render_docker_compose(
        topology, compose_path(root, topology), root=root
    )


def wait_ready(
    topology: Topology, timeout_seconds: float = 180.0
) -> list[Endpoint]:
    deadline = monotonic() + timeout_seconds
    last_error: Exception | None = None
    while monotonic() < deadline:
        try:
            return discover(
                topology.endpoints(),
                topology.active_nodes,
                topology.fingerprint,
            )
        except Exception as error:
            last_error = error
            sleep(1.0)
    raise RuntimeError(
        f"Docker workers did not become healthy within {timeout_seconds:g}s: "
        f"{last_error}"
    )
