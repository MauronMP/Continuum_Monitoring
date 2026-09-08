"""Standard-library-only installation and infrastructure diagnostics.

Safe to import before pip installs the scientific dependencies. These checks
never install system packages, change permissions or start services.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import struct
import sys
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str
    hint: str = ""


def runtime_checks(*, worker: bool = False) -> list[Check]:
    checks = [
        Check(
            "python",
            "ok" if sys.version_info >= (3, 11) else "error",
            platform.python_version(),
            "Python >= 3.11 is required.",
        )
    ]
    supported = sys.platform.startswith("linux") or sys.platform == "darwin"
    checks.append(
        Check(
            "system",
            "ok" if supported else "error",
            platform.platform(),
            "Use Linux or macOS for the coordinator. On Windows, use WSL2.",
        )
    )
    bits = struct.calcsize("P") * 8
    checks.append(
        Check(
            "architecture",
            "ok" if worker or bits == 64 else "error",
            f"{platform.machine()}, Python {bits} bit",
            (
                "The coordinator requires 64-bit Python. A lightweight worker "
                "can run on 32-bit Raspberry Pi systems."
            ),
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
            pass
    return versions


def failure_hint(output: str) -> str:
    text = output.lower()
    if "permission denied" in text and ("ssh" in text or "rsync" in text):
        return (
            "Check SSH keys, remote user permissions and the configured "
            "remote_dir. Do not run the benchmark with sudo."
        )
    if any(value in text for value in ("timed out", "timeout", "no route", "unreachable")):
        return (
            "Check local-network reachability, IP addresses, firewall rules and "
            "that each physical worker is running on the configured port."
        )
    if "no space left" in text:
        return "Free storage on the coordinator or remote node before retrying."
    if any(value in text for value in ("out of memory", "oom", "killed")):
        return "Reduce workload size or reasoner complexity for constrained nodes."
    return "Review the last lines and the complete log before retrying."


def project_checks(root: Path) -> list[Check]:
    required = (
        "pyproject.toml",
        "configs/benchmark.toml",
        "configs/owl-reasoners.toml",
        "configs/topologies/physical/topology.toml",
        "engine-service/pom.xml",
        "queries/catalog.csv",
        "queries/execution-plan.toml",
        "ontology/core/schema.ttl",
        "ontology/legacy/smartcity_continuum-v3.0.0.ttl",
        "queries/legacy/sparql_battery-v3.0.0.sparql",
        "requirements/constraints.txt",
        "requirements-node.txt",
        "tools/check_owl_consistency.py",
        "tools/owl/CheckOntology.java",
        "tools/owl/pom.xml",
    )
    missing = [name for name in required if not (root / name).is_file()]
    checks = [
        Check(
            "repository",
            "error" if missing else "ok",
            ", ".join(missing) if missing else str(root),
            (
                "Run from a complete clone of this revision. Do not copy only "
                "src/ or reuse a virtual environment from another machine."
            ),
        )
    ]
    if not missing:
        try:
            from .topology import load_topology_manifest

            details = []
            for architecture in ("physical",):
                manifest = load_topology_manifest(
                    root
                    / f"configs/topologies/{architecture}/topology.toml"
                )
                details.extend(
                    f"{architecture}:{name}={len(topology.active_nodes)}"
                    for name, topology in manifest.topologies.items()
                )
            checks.append(Check("topology", "ok", ", ".join(details)))
        except (OSError, ValueError) as error:
            checks.append(
                Check(
                    "topology",
                    "error",
                    str(error),
                    (
                        "Fix configs/topologies/physical/*.toml and run "
                        "'continuum-bench topology validate'."
                    ),
                )
            )
    return checks


def physical_checks() -> list[Check]:
    return [
        Check(
            name,
            "ok" if shutil.which(name) else "error",
            shutil.which(name) or "not installed",
            (
                "Install openssh-client, ssh-copy-id and rsync on the "
                "coordinator. Raspberry Pi workers do not need Java."
            ),
        )
        for name in ("ssh", "ssh-copy-id", "rsync")
    ]




def owl_reasoner_checks() -> list[Check]:
    """Report external OWL validation prerequisites without installing them."""

    import os

    checks = []
    for executable in ("java", "mvn", "Konclude"):
        path = shutil.which(executable)
        checks.append(
            Check(
                f"owl-{executable.lower()}",
                "ok" if path else "warning",
                path or "not installed",
                "See docs/design/OWL_REASONERS.md.",
            )
        )
    project_root = Path(__file__).resolve().parents[2]
    for reasoner in ("HERMIT", "OPENLLET", "JFACT"):
        name = f"CONTINUUM_{reasoner}_CLASSPATH"
        value = os.environ.get(name, "")
        isolated_classpath = project_root / (
            f".runtime/owl-validation-{reasoner.lower()}.classpath"
        )
        configured = (
            str(isolated_classpath) if isolated_classpath.is_file() else value
        )
        checks.append(
            Check(
                f"owl-{reasoner.lower()}-classpath",
                "ok" if configured else "warning",
                configured or "not configured",
                (
                    "Run 'python3 tools/install_owl_reasoners.py' or set "
                    f"{name}; see docs/design/OWL_REASONERS.md."
                ),
            )
        )
    return checks


def require_checks(checks: list[Check]) -> None:
    errors = [item for item in checks if item.status == "error"]
    if errors:
        raise RuntimeError(
            "Environment check failed:\n"
            + "\n".join(
                f"[{item.name}] {item.detail}\n{item.hint}" for item in errors
            )
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only benchmark diagnostics, available before "
            "installing scientific dependencies."
        )
    )
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--physical", action="store_true")
    parser.add_argument("--owl", action="store_true")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    checks = runtime_checks(worker=args.worker) + project_checks(args.root.resolve())
    if args.physical:
        checks.extend(physical_checks())
    if args.owl:
        checks.extend(owl_reasoner_checks())
    if args.json:
        print(json.dumps([asdict(item) for item in checks], indent=2))
    else:
        for item in checks:
            print(f"[{item.status}] {item.name}: {item.detail}")
            if item.status != "ok" and item.hint:
                print(f"  {item.hint}")
    return int(any(item.status == "error" for item in checks))


if __name__ == "__main__":
    raise SystemExit(main())
