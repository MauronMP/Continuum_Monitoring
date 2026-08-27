"""Standard-library-only installation and Docker diagnostics.

Safe to import before pip installs the scientific dependencies. These checks
never install system packages, change groups, chmod sockets or start daemons.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Mapping

DOCKER_INSTALL_URL = "https://docs.docker.com/engine/install/ubuntu/"
DOCKER_PERMISSIONS_URL = "https://docs.docker.com/engine/install/linux-postinstall/"
DOCKER_INFO_FORMAT = (
    '{"version":{{json .ServerVersion}},"os":{{json .OSType}},'
    '"arch":{{json .Architecture}},"cpus":{{json .NCPU}},'
    '"memory_bytes":{{json .MemTotal}}}'
)


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str
    hint: str = ""


def docker_environment() -> dict[str, str]:
    environment = dict(os.environ)
    desktop = Path("/Applications/Docker.app/Contents/Resources/bin")
    # Append helpers without overriding the user's selected Docker CLI/context.
    if desktop.is_dir() and str(desktop) not in environment.get("PATH", "").split(
        os.pathsep
    ):
        environment["PATH"] = environment.get("PATH", "") + os.pathsep + str(desktop)
    environment.setdefault("BUILDKIT_PROGRESS", "plain")
    environment.setdefault("COMPOSE_PARALLEL_LIMIT", "1")
    return environment


def failure_hint(output: str) -> str:
    text = output.lower()
    if "buildx" in text and any(
        value in text
        for value in ("not a docker command", "unknown command", "missing", "required")
    ):
        return f"Instale el plugin docker-buildx-plugin junto con Docker Compose. {DOCKER_INSTALL_URL}"
    if "permission denied" in text and ("docker" in text or "sock" in text):
        return (
            "El usuario actual no puede acceder a Docker. Compruebe 'docker info' "
            "sin sudo. Un administrador debe configurar acceso al daemon o Docker "
            "rootless; el grupo docker concede privilegios equivalentes a root. "
            f"No use chmod 666 ni sudo para el benchmark. {DOCKER_PERMISSIONS_URL}"
        )
    if any(value in text for value in ("docker", "daemon", ".sock")) and any(
        value in text
        for value in (
            "cannot connect",
            "is the docker daemon running",
            "connection refused",
        )
    ):
        return "Arranque Docker Desktop o pida al administrador arrancar el servicio Docker; revise 'docker context show' y DOCKER_HOST."
    if "compose" in text and any(
        value in text
        for value in ("not a docker command", "unknown command", "unknown flag")
    ):
        return f"Instale/actualice el plugin Docker Compose (comando 'docker compose', no Compose v1). {DOCKER_INSTALL_URL}"
    if any(
        value in text
        for value in (
            "port is already allocated",
            "address already in use",
            "ports are not available",
        )
    ):
        return "Hay un puerto ocupado. Revise 'docker ps'; los motores usan 8291–8294 y los nodos 8191–8195. No detenga contenedores ajenos."
    if any(
        value in text
        for value in (
            "no matching manifest",
            "exec format error",
            "unsupported platform",
        )
    ):
        return "Las imágenes de productos requieren Linux amd64/arm64 de 64 bits. En Raspberry de 32 bits use únicamente el worker de requirements-node.txt."
    if "credential" in text:
        return "Revise el gestor de credenciales de Docker y 'docker login' en esta sesión. No borre ~/.docker ni publique credenciales."
    if any(
        value in text
        for value in (
            "x509",
            "certificate",
            "tls handshake",
            "resolve",
            "timed out",
            "too many requests",
            "429",
            "deadline exceeded",
            "deadlineexceeded",
            "cannot connect",
            "connection refused",
        )
    ):
        return "Revise red, DNS, proxy, certificados y límites del registro (Docker Hub/PyPI/Maven Central). No desactive la verificación TLS."
    if "no space left" in text:
        return "Falta espacio en el almacenamiento de Docker; revise 'docker system df' sin borrar datos automáticamente."
    if any(value in text for value in ("out of memory", "oomkilled", "exit code: 137")):
        return "Revise la memoria disponible/asignada a Docker. Los límites de contenedor no reservan RAM ni garantizan que el host pueda atenderlos."
    return "Revise las últimas líneas y el log completo. La instalación inicial requiere acceso a Docker Hub, PyPI y Maven Central."


def runtime_checks(*, worker: bool = False) -> list[Check]:
    checks = [
        Check(
            "python",
            "ok" if sys.version_info >= (3, 11) else "error",
            platform.python_version(),
            "Se requiere Python >=3.11; use python3.11, python3.12 o python3.13.",
        )
    ]
    supported = sys.platform.startswith("linux") or sys.platform == "darwin"
    checks.append(
        Check(
            "sistema",
            "ok" if supported else "error",
            platform.platform(),
            "El runtime usa POSIX: en Windows ejecute dentro de WSL2, no en Python nativo de Windows.",
        )
    )
    bits = struct.calcsize("P") * 8
    checks.append(
        Check(
            "arquitectura",
            "ok" if worker or bits == 64 else "error",
            f"{platform.machine()}, Python {bits} bits",
            "El coordinador completo necesita 64 bits. Para Raspberry de 32 bits use --profile worker.",
        )
    )
    return checks


def installed_versions() -> dict[str, str]:
    versions = {}
    for name in (
        "continuum-ontology-benchmark",
        "rdflib",
        "owlrl",
        "pyshacl",
        "pyoxigraph",
        "numpy",
        "matplotlib",
    ):
        try:
            versions[name] = version(name)
        except PackageNotFoundError:
            pass  # Minimal physical workers intentionally omit native packages.
    return versions


def project_checks(root: Path) -> list[Check]:
    required = (
        "pyproject.toml",
        "configs/benchmark.toml",
        "queries/catalog.csv",
        "queries/execution-plan.toml",
        "ontology/core/schema.ttl",
        "ontology/legacy/smartcity_continuum-v3.0.0.ttl",
        "queries/legacy/sparql_battery-v3.0.0.sparql",
        "requirements/constraints.txt",
        "requirements-node.txt",
    )
    missing = [name for name in required if not (root / name).is_file()]
    return [
        Check(
            "repositorio",
            "error" if missing else "ok",
            ", ".join(missing) if missing else str(root),
            "Ejecute desde un clon completo de esta revisión; no copie solo src/ ni el entorno .venv de otro equipo.",
        )
    ]


def _probe(
    command: list[str], environment: Mapping[str, str], root: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=root,
        env=dict(environment),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )


def docker_checks(
    root: Path, *, compose_file: str = "docker-compose.engines.yml"
) -> list[Check]:
    environment = docker_environment()
    if shutil.which("docker", path=environment.get("PATH")) is None:
        return [
            Check(
                "docker-cli",
                "error",
                "No se encuentra docker en PATH",
                f"Instale Docker Engine + Compose en Ubuntu, o Docker Desktop en macOS/Windows. {DOCKER_INSTALL_URL}",
            )
        ]
    checks: list[Check] = []
    commands = (
        ("compose", ["docker", "compose", "version", "--short"]),
        ("docker-daemon", ["docker", "info", "--format", DOCKER_INFO_FORMAT]),
        ("buildx", ["docker", "buildx", "version"]),
        (
            "compose-config",
            ["docker", "compose", "-f", str(root / compose_file), "config", "--quiet"],
        ),
    )
    for name, command in commands:
        try:
            result = _probe(command, environment, root)
        except (OSError, subprocess.TimeoutExpired) as error:
            checks.append(
                Check(
                    name,
                    "error",
                    str(error),
                    "La comprobación tiene un timeout de 20 s. Revise Docker/contexto/permisos antes de medir.",
                )
            )
            break
        detail = (result.stdout + result.stderr).strip()
        if result.returncode:
            checks.append(Check(name, "error", detail[-6000:], failure_hint(detail)))
            break
        if name == "compose":
            match = re.search(r"v?(\d+)\.(\d+)", result.stdout)
            if not match or int(match[1]) < 2:
                checks.append(
                    Check(
                        name,
                        "error",
                        detail,
                        "Se requiere el plugin 'docker compose' versión 2 o posterior.",
                    )
                )
                break
        if name == "docker-daemon":
            try:
                info = json.loads(result.stdout)
            except (TypeError, ValueError):
                checks.append(
                    Check(
                        name,
                        "error",
                        detail,
                        "Respuesta inesperada de 'docker info'. Revise el contexto Docker.",
                    )
                )
                break
            if info.get("os") != "linux" or info.get("arch") not in {
                "amd64",
                "x86_64",
                "arm64",
                "aarch64",
            }:
                checks.append(
                    Check(
                        name,
                        "error",
                        detail,
                        "Active contenedores Linux amd64/arm64 de 64 bits; no contenedores Windows/ARM de 32 bits.",
                    )
                )
                break
            memory = int(info.get("memory_bytes") or 0)
            if memory and memory < 8 * 1024**3:
                checks.append(
                    Check(
                        "memoria-docker",
                        "warning",
                        f"{memory / 1024**3:.1f} GiB disponibles para el daemon",
                        "Hay cuatro motores y hasta cinco nodos. Los smokes pueden funcionar, pero una campaña grande puede agotar la memoria.",
                    )
                )
        checks.append(Check(name, "ok", detail or compose_file))
    return checks


def physical_checks() -> list[Check]:
    return [
        Check(
            name,
            "ok" if shutil.which(name) else "error",
            shutil.which(name) or "No instalado",
            "Instale openssh-client, ssh-copy-id y rsync en el coordinador. No hacen falta Java ni Docker en las Raspberry.",
        )
        for name in ("ssh", "ssh-copy-id", "rsync")
    ]


def require_checks(checks: list[Check]) -> None:
    errors = [item for item in checks if item.status == "error"]
    if errors:
        raise RuntimeError(
            "Comprobación de entorno fallida:\n"
            + "\n".join(f"[{item.name}] {item.detail}\n{item.hint}" for item in errors)
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Diagnóstico de solo lectura, disponible incluso antes de instalar dependencias."
    )
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--docker", action="store_true")
    parser.add_argument("--physical", action="store_true")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    checks = runtime_checks(worker=args.worker) + project_checks(args.root.resolve())
    if args.docker:
        checks.extend(docker_checks(args.root.resolve()))
    if args.physical:
        checks.extend(physical_checks())
    if args.json:
        print(
            json.dumps([asdict(item) for item in checks], indent=2, ensure_ascii=False)
        )
    else:
        for item in checks:
            print(f"[{item.status}] {item.name}: {item.detail}")
            if item.status != "ok" and item.hint:
                print(f"  {item.hint}")
    return int(any(item.status == "error" for item in checks))


if __name__ == "__main__":
    raise SystemExit(main())
