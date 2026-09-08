#!/usr/bin/env python3
"""Install the reproducible coordinator-side OWL validation runtime.

Java reasoners are resolved from the pinned Maven POM. Konclude uses an
already-installed native binary when present; otherwise its official Docker
image is pulled. No validator is installed on physical workers.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime"
JAVA_REASONERS = ("hermit", "openllet", "jfact")
CLASSPATH_FILES = {
    name: RUNTIME / f"owl-validation-{name}.classpath"
    for name in JAVA_REASONERS
}
# Kept as the OWLAPI conversion classpath used by the Konclude adapter and for
# compatibility with installations made before reasoner isolation.
CLASSPATH_FILE = RUNTIME / "owl-validation.classpath"
ENV_FILE = RUNTIME / "owl-reasoners.env"
KONCLUDE_IMAGE = "konclude/konclude"


def _run(command: list[str]) -> None:
    print("[owl-install] exec=" + shlex.join(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode:
        raise RuntimeError(
            f"Command failed with exit code {completed.returncode}: "
            f"{shlex.join(command)}"
        )


def _require(name: str, hint: str) -> str:
    executable = shutil.which(name)
    if not executable:
        raise RuntimeError(f"{name} is required. {hint}")
    return executable


def install_java_reasoners() -> dict[str, str]:
    _require("java", "Install OpenJDK 17.")
    maven = _require("mvn", "Install Maven 3.8 or newer.")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    classpaths: dict[str, str] = {}
    for name, output_file in CLASSPATH_FILES.items():
        output_file.unlink(missing_ok=True)
        _run(
            [
                maven,
                "-f",
                str(ROOT / "tools/owl/pom.xml"),
                f"-P{name}",
                "dependency:build-classpath",
                f"-Dmdep.outputFile={output_file}",
            ]
        )
        classpath = output_file.read_text(encoding="utf-8").strip()
        if not classpath:
            raise RuntimeError(
                f"Maven produced an empty {name} validation classpath"
            )
        if name == "jfact":
            jar_names = {
                Path(entry).name for entry in classpath.split(os.pathsep)
            }
            required = {"guice-5.1.0.jar", "guava-30.1-jre.jar"}
            missing = sorted(required - jar_names)
            if missing:
                raise RuntimeError(
                    "JFact classpath did not select its pinned Java-17 "
                    f"compatibility dependencies: missing={missing}"
                )
        classpaths[name] = classpath

    # Openllet's profile supplies a complete, known-working OWLAPI runtime for
    # serialization conversion. Konclude itself is not placed on this path.
    CLASSPATH_FILE.write_text(classpaths["openllet"] + "\n", encoding="utf-8")
    return classpaths


def verify_java_reasoners(classpaths: dict[str, str]) -> None:
    """Fail installation early if a pinned factory cannot be instantiated."""

    checker = ROOT / "tools/check_owl_consistency.py"
    fixture = ROOT / "tools/owl/smoke-ontology.ttl"
    for name, classpath in classpaths.items():
        command = [
            sys.executable,
            str(checker),
            str(fixture),
            "--reasoner",
            name,
            "--require-dl-profile",
            "--timeout",
            "60",
            "--classpath",
            classpath,
        ]
        print(f"[owl-install] verify={name}", flush=True)
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            diagnostic = (completed.stderr or completed.stdout).strip()
            raise RuntimeError(
                f"{name} installation self-check failed (exit "
                f"{completed.returncode}):\n{diagnostic[-4000:]}"
            )


def install_konclude(*, pull_image: bool) -> str:
    configured = os.environ.get("CONTINUUM_KONCLUDE_EXECUTABLE", "")
    native = configured or shutil.which("Konclude")
    if native:
        return f"native:{native}"
    if not pull_image:
        return "not-installed"
    docker = _require(
        "docker",
        "Install Docker or provide CONTINUUM_KONCLUDE_EXECUTABLE.",
    )
    _run([docker, "info"])
    _run([docker, "pull", KONCLUDE_IMAGE])
    return f"docker:{KONCLUDE_IMAGE}"


def verify_konclude(konclude: str, classpaths: dict[str, str]) -> None:
    """Exercise the actual native/container backend, not its help command."""

    if konclude == "not-installed":
        return
    environment = os.environ.copy()
    environment["CONTINUUM_OWL_CLASSPATH"] = classpaths["openllet"]
    environment["CONTINUUM_KONCLUDE_IMAGE"] = KONCLUDE_IMAGE
    if konclude.startswith("native:"):
        environment["CONTINUUM_KONCLUDE_EXECUTABLE"] = konclude.removeprefix(
            "native:"
        )
    command = [
        sys.executable,
        str(ROOT / "tools/owl/run_konclude.py"),
        "consistency",
        "-w",
        "AUTO",
        "-i",
        str(ROOT / "tools/owl/smoke-ontology.ttl"),
    ]
    print("[owl-install] verify=konclude", flush=True)
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            "Konclude installation self-check timed out after 60 s"
        ) from error
    output = completed.stdout + "\n" + completed.stderr
    reports_consistent = re.search(
        r"(?i)ontology(?:\s+['\"][^'\"]+['\"])?\s+is\s+consistent\b"
        r"|ontology\s+consistent\b|consistent\s*[:=]\s*true",
        output,
    )
    if completed.returncode != 0 or not reports_consistent:
        raise RuntimeError(
            "Konclude installation self-check did not report consistency "
            f"(exit {completed.returncode}):\n{output[-4000:]}"
        )


def write_environment(classpaths: dict[str, str], konclude: str) -> None:
    lines = [
        "# Generated by tools/install_owl_reasoners.py; do not commit.",
        f"export CONTINUUM_OWL_CLASSPATH={shlex.quote(classpaths['openllet'])}",
        f"export CONTINUUM_HERMIT_CLASSPATH={shlex.quote(classpaths['hermit'])}",
        f"export CONTINUUM_OPENLLET_CLASSPATH={shlex.quote(classpaths['openllet'])}",
        f"export CONTINUUM_JFACT_CLASSPATH={shlex.quote(classpaths['jfact'])}",
        f"export CONTINUUM_KONCLUDE_IMAGE={shlex.quote(KONCLUDE_IMAGE)}",
    ]
    if konclude.startswith("native:"):
        lines.append(
            "export CONTINUUM_KONCLUDE_EXECUTABLE="
            + shlex.quote(konclude.removeprefix("native:"))
        )
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-konclude-image",
        action="store_true",
        help="Prepare Java reasoners but do not pull the Konclude Docker image",
    )
    args = parser.parse_args(argv)
    try:
        classpaths = install_java_reasoners()
        verify_java_reasoners(classpaths)
        konclude = install_konclude(
            pull_image=not args.skip_konclude_image
        )
        verify_konclude(konclude, classpaths)
        write_environment(classpaths, konclude)
        for name, path in CLASSPATH_FILES.items():
            print(f"[owl-install] classpath[{name}]={path}")
        print(f"[owl-install] converter_classpath={CLASSPATH_FILE}")
        print(f"[owl-install] konclude={konclude}")
        print(f"[owl-install] environment={ENV_FILE}")
        print("[owl-install] ready; run: continuum-bench owl-validate --require-all")
        return 0
    except (OSError, RuntimeError) as error:
        print(f"[owl-install] ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
