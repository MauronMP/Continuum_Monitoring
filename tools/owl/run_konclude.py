#!/usr/bin/env python3
"""Run native or containerized Konclude after deterministic OWL/XML conversion."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IMAGE = "konclude/konclude"


def _input_index(arguments: list[str]) -> int:
    try:
        flag = arguments.index("-i")
        return flag + 1
    except (ValueError, IndexError) as error:
        raise ValueError("Konclude invocation requires '-i ONTOLOGY'") from error


def main(argv: list[str] | None = None) -> int:
    arguments = list(argv if argv is not None else sys.argv[1:])
    try:
        input_index = _input_index(arguments)
        source = Path(arguments[input_index]).resolve()
        if not source.is_file():
            raise ValueError(f"Ontology does not exist: {source}")
        classpath_file = ROOT / ".runtime/owl-validation.classpath"
        classpath = os.environ.get("CONTINUUM_OWL_CLASSPATH", "")
        if not classpath and classpath_file.is_file():
            classpath = classpath_file.read_text(encoding="utf-8").strip()
        java = shutil.which(os.environ.get("JAVA", "java"))
        if not java or not classpath:
            raise ValueError(
                "Java runtime/classpath unavailable; run "
                "'python3 tools/install_owl_reasoners.py'"
            )
        with tempfile.TemporaryDirectory(prefix="continuum-konclude-") as temp:
            temporary = Path(temp)
            converted = temporary / "ontology.owl.xml"
            conversion = subprocess.run(
                [
                    java,
                    "-cp",
                    classpath,
                    str(ROOT / "tools/owl/ConvertOntology.java"),
                    str(source),
                    str(converted),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if conversion.returncode:
                sys.stderr.write(conversion.stdout + conversion.stderr)
                return conversion.returncode
            arguments[input_index] = str(converted)
            configured = os.environ.get("CONTINUUM_KONCLUDE_EXECUTABLE", "")
            native = configured or shutil.which("Konclude")
            if native:
                return subprocess.run([native, *arguments], check=False).returncode
            docker = shutil.which("docker")
            if not docker:
                raise ValueError(
                    "Neither a native Konclude executable nor Docker is available"
                )
            arguments[input_index] = "/data/ontology.owl.xml"
            image = os.environ.get("CONTINUUM_KONCLUDE_IMAGE", DEFAULT_IMAGE)
            command = [
                docker,
                "run",
                "--rm",
                "--network=none",
                "--volume",
                f"{temporary}:/data:ro",
                image,
                *arguments,
            ]
            return subprocess.run(command, check=False).returncode
    except (OSError, ValueError) as error:
        print(f"Konclude wrapper failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
