"""Install the coordinator or worker virtual environment safely."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path

if sys.version_info < (3, 11):
    raise SystemExit("Python >= 3.11 is required before creating a virtualenv.")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from continuum_bench.environment import (  # noqa: E402
    project_checks,
    require_checks,
    runtime_checks,
)
from continuum_bench.processes import CommandFailure, run_logged  # noqa: E402


def check_virtualenv(python: Path, *, worker: bool) -> None:
    probe = (
        "import struct, sys; "
        "print(sys.version.split()[0], str(struct.calcsize('P') * 8) + ' bit'); "
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
            f"The virtualenv is not executable on this machine: {python}. "
            "Use --venv with a new directory; existing environments are not removed."
        ) from error
    if result.returncode:
        raise RuntimeError(
            f"Incompatible virtualenv: {(result.stdout + result.stderr).strip()}. "
            "The coordinator requires Python >= 3.11 and 64-bit execution."
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
        help="Default: .venv for coordinator or .venv-node for worker",
    )
    parser.add_argument(
        "--with-owl-reasoners",
        action="store_true",
        help=(
            "Install pinned HermiT/Openllet/JFact dependencies and prepare "
            "the Konclude Docker backend (coordinator only)"
        ),
    )
    args = parser.parse_args(argv)
    worker = args.profile == "worker"
    checks = runtime_checks(worker=worker) + project_checks(ROOT)
    try:
        require_checks(checks)
        destination = args.venv or ROOT / (".venv-node" if worker else ".venv")
        if not destination.is_absolute():
            destination = ROOT / destination
        if destination.is_symlink():
            raise RuntimeError(f"Refusing to modify a linked environment: {destination}")
        if destination.exists() and not (destination / "pyvenv.cfg").is_file():
            raise RuntimeError(
                f"{destination} exists but is not a virtualenv. Choose --venv "
                "with a new directory; nothing will be deleted."
            )
        if not destination.exists():
            print(f"[bootstrap] creating {destination}", flush=True)
            try:
                venv.EnvBuilder(with_pip=True).create(destination)
            except (OSError, subprocess.SubprocessError) as error:
                raise RuntimeError(
                    "Could not create the virtualenv. On Ubuntu, install "
                    "python3-venv or python3.X-venv for the selected interpreter."
                ) from error
        python = destination / "bin" / "python"
        check_virtualenv(python, worker=worker)
        environment = dict(os.environ)
        environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        environment.setdefault("PIP_CACHE_DIR", str(ROOT / ".cache" / "pip"))
        for command in install_commands(ROOT, python, worker=worker):
            run_logged(command, root=ROOT, environment=environment, label="install")
        if args.with_owl_reasoners:
            if worker:
                raise RuntimeError(
                    "OWL validators belong on the coordinator, not a worker"
                )
            run_logged(
                [str(python), str(ROOT / "tools/install_owl_reasoners.py")],
                root=ROOT,
                environment=environment,
                label="owl-install",
            )
        print(f"[bootstrap] ready: {destination}", flush=True)
        if worker:
            print(f"Worker: PYTHONPATH=src {python} -m continuum_bench.node --help")
        else:
            print(f"Validation: {python} -m continuum_bench validate")
            print(
                "Optional targets: run 'continuum-bench doctor --docker' or "
                "'continuum-bench doctor --physical' before those suites."
            )
        return 0
    except (RuntimeError, OSError, ValueError) as error:
        print(f"[bootstrap] ERROR: {error}", file=sys.stderr)
        if isinstance(error, CommandFailure):
            print(
                "Native dependency builds are not attempted automatically. "
                "Use CPython 3.11-3.13 with binary wheels available.",
                file=sys.stderr,
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
