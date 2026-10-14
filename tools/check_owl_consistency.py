#!/usr/bin/env python3
"""Read-only OWLAPI consistency check using an external reasoner classpath.

Release and native runtime validation, separate from timed benchmarks. Requires
Java 11+ (Java 17 recommended); Python uses only its standard library. Dependencies are supplied through the isolated installed classpath; no GUI
installation or implicit application-directory discovery is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
REPORT_PREFIX = "CONTINUUM_OWL_REPORT\t"
OWLAPI_FACTORIES = {
    "hermit": "org.semanticweb.HermiT.ReasonerFactory",
    "openllet": "openllet.owlapi.OpenlletReasonerFactory",
    "jfact": "uk.ac.manchester.cs.jfact.JFactFactory",
}


def parse_report(output: str) -> dict:
    reports = [line[len(REPORT_PREFIX):] for line in output.splitlines()
               if line.startswith(REPORT_PREFIX)]
    if len(reports) != 1:
        raise ValueError(
            "OWL reasoner did not return exactly one machine-readable report"
        )
    report = json.loads(reports[0])
    if not isinstance(report.get("consistent"), bool):
        raise ValueError("OWL reasoner report lacks a Boolean consistency result")
    return report


def diagnostic_excerpt(output: str, limit: int = 3000) -> str:
    """Keep the exception cause and stack-trace tail in bounded diagnostics."""

    if len(output) <= limit:
        return output
    separator = "\n... output truncated ...\n"
    half = (limit - len(separator)) // 2
    return output[:half] + separator + output[-half:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "ontology",
        type=Path,
        help=(
            "Ontology file to validate. The path is mandatory so this low-level "
            "tool cannot silently select the archived single-file release. Use "
            "'continuum-bench owl-validate' for the active modular ontology."
        ),
    )
    parser.add_argument(
        "--reasoner", choices=tuple(OWLAPI_FACTORIES), default="hermit",
        help="OWLAPI reasoner used for consistency checking",
    )
    parser.add_argument(
        "--classpath", help="Explicit isolated OWLAPI/reasoner dependency classpath"
    )
    parser.add_argument("--java", default="java", help="Java 11+ executable")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--require-dl-profile", action="store_true",
                        help="Also fail if the OWL 2 DL structural profile is violated")
    parser.add_argument("--output", type=Path, help="Optional JSON evidence file")
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        ontology = args.ontology.resolve()
        if not ontology.is_file():
            raise ValueError(f"Ontology file does not exist: {ontology}")
        java = shutil.which(args.java)
        if java is None:
            raise ValueError(
                "Java 11+ is required for OWL validation; use --java /path/to/java"
            )
        # Hash BEFORE execution so that concurrent editing cannot silently
        # associate the report with different bytes.
        digest = hashlib.sha256(ontology.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="continuum-hermit-") as temp:
            temporary = Path(temp)
            classpath = args.classpath
            if not classpath:
                environment_name = f"CONTINUUM_{args.reasoner.upper()}_CLASSPATH"
                classpath = os.environ.get(environment_name)
            if not classpath:
                raise ValueError(
                    f"Set --classpath or CONTINUUM_{args.reasoner.upper()}_CLASSPATH "
                    f"for {args.reasoner}."
                )
            log_config = temporary / "logback.xml"
            log_config.write_text(
                '<configuration><root level="WARN"/></configuration>\n'
            )
            heap = os.environ.get("CONTINUUM_OWL_JAVA_HEAP", "2g")
            if not re.fullmatch(r"[1-9][0-9]*[kKmMgG]?", heap):
                raise ValueError("CONTINUUM_OWL_JAVA_HEAP must be a Java heap size such as 512m or 2g")
            command = [java, f"-Xmx{heap}", f"-Dlogback.configurationFile={log_config}",
                       "-cp", classpath, str(ROOT / "tools/owl/CheckOntology.java"),
                       str(ontology), OWLAPI_FACTORIES[args.reasoner]]
            started = time.perf_counter()
            result = subprocess.run(
                command,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=args.timeout,
                check=False,
            )
            elapsed = time.perf_counter() - started
        try:
            report = parse_report(result.stdout)
        except (ValueError, json.JSONDecodeError) as error:
            raise ValueError(
                f"{error}; Java exit={result.returncode}\n"
                f"{diagnostic_excerpt(result.stdout)}\n"
                f"{diagnostic_excerpt(result.stderr)}"
            ) from error
        if digest != hashlib.sha256(ontology.read_bytes()).hexdigest():
            raise ValueError(
                "Ontology changed while the OWL reasoner was running; repeat the check"
            )
        report.update(requested_reasoner=args.reasoner,
                      ontology_file=str(ontology), ontology_sha256=digest,
                      elapsed_seconds=elapsed, java_exit_code=result.returncode,
                      scope=(
                          "OWLAPI logical axioms; not SHACL or operational compliance"
                      ))
        report["ok"] = (result.returncode == 0 and report["consistent"]
                        and not report["unsatisfiable_classes"]
                        and (not args.require_dl_profile or report["owl2_dl_profile"]))
        rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0 if report["ok"] else 1
    except subprocess.TimeoutExpired:
        print(
            f"{args.reasoner} timed out after {args.timeout:g}s; "
            "consistency is unknown.",
            file=sys.stderr,
        )
        return 2
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"OWL consistency check failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
