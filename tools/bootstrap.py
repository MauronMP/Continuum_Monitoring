"""Install into a project virtualenv; never mutate host packages or Docker permissions."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path

if sys.version_info < (3, 11):
    raise SystemExit(
        "Se requiere Python >=3.11; seleccione ese intérprete antes de crear .venv (Ubuntu 24.04 incluye Python 3.12)."
    )

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from continuum_bench.environment import (  # noqa: E402 - source import before installation
    docker_checks,
    project_checks,
    require_checks,
    runtime_checks,
)
from continuum_bench.processes import CommandFailure, run_logged  # noqa: E402


def check_virtualenv(python: Path, *, worker: bool) -> None:
    """Reject copied/old environments before asking pip to modify them."""
    probe = (
        "import struct, sys; "
        "print(sys.version.split()[0], str(struct.calcsize('P') * 8) + ' bits'); "
        "sys.exit(0 if sys.version_info >= (3, 11) and "
        f"({worker!r} or struct.calcsize('P') == 8) else 1)"
    )
    try:
        result = subprocess.run(
            [str(python), "-c", probe],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(
            f"El virtualenv no es ejecutable en este equipo: {python}. "
            "Use --venv con un directorio nuevo; no se borrará el existente."
        ) from error
    if result.returncode:
        raise RuntimeError(
            f"Virtualenv incompatible: {(result.stdout + result.stderr).strip()}. "
            "Se requiere Python >=3.11 y 64 bits para el coordinador. "
            "Use --venv con un directorio nuevo."
        )


def install_commands(root: Path, python: Path, *, worker: bool) -> list[list[str]]:
    prefix = [
        str(python),
        "-m",
        "pip",
        "install",
        "--only-binary=:all:",
        "--retries",
        "2",
        "--timeout",
        "60",
    ]
    commands = [
        prefix + ["-c", str(root / "requirements/constraints.txt"), "pip", "setuptools"]
    ]
    if worker:
        commands.append(prefix + ["-r", str(root / "requirements-node.txt")])
    else:
        commands.append(
            prefix
            + [
                "--no-build-isolation",
                "-c",
                str(root / "requirements/constraints.txt"),
                "-e",
                f"{root}[dev]",
            ]
        )
    commands.append([str(python), "-m", "pip", "check"])
    return commands


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile", choices=("coordinator", "worker"), default="coordinator"
    )
    parser.add_argument(
        "--venv",
        type=Path,
        help="Por defecto .venv (coordinador) o .venv-node (worker)",
    )
    parser.add_argument(
        "--with-docker",
        action="store_true",
        help="Comprobar Docker y construir las dos imágenes compartidas; no iniciar nodos ni benchmarks",
    )
    args = parser.parse_args(argv)
    worker = args.profile == "worker"
    if worker and args.with_docker:
        parser.error("El worker ligero no usa Docker; omita --with-docker")
    checks = runtime_checks(worker=worker) + project_checks(ROOT)
    if args.with_docker:
        checks.extend(docker_checks(ROOT))
    try:
        require_checks(checks)
        destination = args.venv or ROOT / (".venv-node" if worker else ".venv")
        if not destination.is_absolute():
            destination = ROOT / destination
        if destination.is_symlink():
            raise RuntimeError(f"No se modifica un entorno enlazado: {destination}")
        if destination.exists() and not (destination / "pyvenv.cfg").is_file():
            raise RuntimeError(
                f"{destination} existe pero no es un virtualenv. Elija --venv con un directorio nuevo; no se borrará nada."
            )
        if not destination.exists():
            print(f"[bootstrap] creando {destination}", flush=True)
            try:
                venv.EnvBuilder(with_pip=True).create(destination)
            except (OSError, subprocess.SubprocessError) as error:
                raise RuntimeError(
                    "No se pudo crear el virtualenv. En Ubuntu instale python3-venv (o python3.X-venv para el intérprete elegido). El instalador no ejecuta sudo ni modifica Python del sistema."
                ) from error
        python = destination / "bin" / "python"
        check_virtualenv(python, worker=worker)
        environment = dict(os.environ)
        environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        # A writable project cache avoids root-owned/shared ~/.cache/pip and
        # accelerates repeated setup without copying a machine-specific venv.
        environment.setdefault("PIP_CACHE_DIR", str(ROOT / ".cache" / "pip"))
        for command in install_commands(ROOT, python, worker=worker):
            run_logged(command, root=ROOT, environment=environment, label="install")
        if args.with_docker:
            run_logged(
                [
                    str(python),
                    "-m",
                    "continuum_bench.engine_stack",
                    "prepare",
                    "--root",
                    str(ROOT),
                ],
                root=ROOT,
                environment=environment,
                timeout=2 * float(environment.get("CONTINUUM_COMPOSE_TIMEOUT", "1200"))
                + 200,
                label="docker-prepare",
            )
        print(f"[bootstrap] listo: {destination}", flush=True)
        if worker:
            print(f"Worker: PYTHONPATH=src {python} -m continuum_bench.node --help")
        else:
            print(f"Validación: {python} -m continuum_bench validate")
        return 0
    except (RuntimeError, OSError, ValueError) as error:
        print(f"[bootstrap] ERROR: {error}", file=sys.stderr)
        if isinstance(error, CommandFailure):
            print(
                "No se compilan dependencias nativas automáticamente. Si falta un wheel, use CPython 3.11–3.13 en Linux/macOS de 64 bits. No se desactiva TLS.",
                file=sys.stderr,
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
