#!/usr/bin/env python3
"""Run native Konclude after deterministic OWL/XML conversion."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
SUPPORTED_COMMANDS = {
    "classification",
    "consistency",
    "realization",
    "satisfiability",
}


def _input_index(arguments: list[str]) -> int:
    if not arguments or arguments[0] not in SUPPORTED_COMMANDS:
        raise ValueError(
            "the first argument must be a Konclude operation (for project "
            "validation use 'consistency'); '-i ONTOLOGY' alone only prints "
            "Konclude help and does not validate the ontology"
        )
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
            print(
                f"[konclude-wrapper] phase=conversion source={source}",
                file=sys.stderr,
                flush=True,
            )
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
                print(
                    f"[konclude-wrapper] phase=reasoning backend=native "
                    f"operation={arguments[0]}",
                    file=sys.stderr,
                    flush=True,
                )
                return subprocess.run([native, *arguments], check=False).returncode
            raise ValueError("Install native Konclude or set CONTINUUM_KONCLUDE_EXECUTABLE")
    except (OSError, ValueError) as error:
        print(f"Konclude wrapper failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
