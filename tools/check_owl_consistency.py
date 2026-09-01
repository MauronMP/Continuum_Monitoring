#!/usr/bin/env python3
"""Read-only HermiT check using an existing Protégé installation or classpath.

Optional release validation, not part of timed RDFS/OWL-RL benchmarks. Requires
Java 11+ (Java 17 recommended); Python uses only its standard library. Nothing
is downloaded, installed or modified in Protégé. Nested dependency jars are
extracted into a temporary directory and removed after the check.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile


ROOT = Path(__file__).resolve().parents[1]
REPORT_PREFIX = "CONTINUUM_OWL_REPORT\t"


def find_protege(explicit: Path | None) -> Path:
    if explicit is not None:
        if not explicit.is_dir():
            raise ValueError(f"Protégé directory does not exist: {explicit}")
        return explicit.resolve()
    configured = os.environ.get("PROTEGE_HOME")
    if configured:
        return find_protege(Path(configured))
    # Handles both accented Unicode spellings of the macOS application name.
    candidates = sorted(Path("/Applications").glob("Prot*.app"))
    if len(candidates) == 1:
        return candidates[0]
    raise ValueError(
        "Set --protege-home to the extracted Protégé directory, or pass "
        "--classpath with OWLAPI, HermiT and their dependencies. "
        "No reasoner is installed automatically."
    )


def protege_classpath(directory: Path, temporary: Path) -> str:
    owlapi = sorted(directory.rglob("owlapi-osgidistribution*.jar"))
    hermit = sorted(directory.rglob("org.semanticweb.hermit*.jar"))
    if len(owlapi) != 1 or len(hermit) != 1:
        raise ValueError(
            f"Expected one OWLAPI bundle and one HermiT plugin in {directory}; "
            f"found {len(owlapi)} and {len(hermit)}. Use --classpath for a "
            "different installation layout."
        )
    jars = sorted(owlapi[0].parent.glob("*.jar")) + hermit
    # OSGi resolves embedded jars automatically; a plain JVM needs them on its
    # classpath. Extract only jars, with basenames in a private temporary folder.
    for index, bundle in enumerate((owlapi[0], hermit[0])):
        with zipfile.ZipFile(bundle) as archive:
            for name in sorted(archive.namelist()):
                if name.endswith(".jar"):
                    target = temporary / f"{index}-{Path(name).name}"
                    with archive.open(name) as source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)
                    jars.append(target)
    return os.pathsep.join(str(path) for path in jars)


def parse_report(output: str) -> dict:
    reports = [line[len(REPORT_PREFIX):] for line in output.splitlines()
               if line.startswith(REPORT_PREFIX)]
    if len(reports) != 1:
        raise ValueError("HermiT did not return exactly one machine-readable report")
    report = json.loads(reports[0])
    if not isinstance(report.get("consistent"), bool):
        raise ValueError("HermiT report lacks a Boolean consistency result")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ontology", nargs="?", type=Path, default=(
        ROOT / "ontology/legacy/smartcity_continuum-v3.0.0.ttl"
    ))
    parser.add_argument("--protege-home", type=Path)
    parser.add_argument("--classpath", help="Explicit OWLAPI/HermiT dependency classpath")
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
            raise ValueError("Java 11+ is required for HermiT; use --java /path/to/java")
        # Hash BEFORE execution so that concurrent editing cannot silently
        # associate the report with different bytes.
        digest = hashlib.sha256(ontology.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="continuum-hermit-") as temp:
            temporary = Path(temp)
            classpath = args.classpath or protege_classpath(
                find_protege(args.protege_home), temporary
            )
            log_config = temporary / "logback.xml"
            log_config.write_text('<configuration><root level="WARN"/></configuration>\n')
            command = [java, "-Xmx2g", f"-Dlogback.configurationFile={log_config}",
                       "-cp", classpath, str(ROOT / "tools/owl/CheckOntology.java"),
                       str(ontology)]
            started = time.perf_counter()
            result = subprocess.run(command, text=True, encoding="utf-8", errors="replace",
                                    capture_output=True, timeout=args.timeout, check=False)
            elapsed = time.perf_counter() - started
        try:
            report = parse_report(result.stdout)
        except (ValueError, json.JSONDecodeError) as error:
            raise ValueError(
                f"{error}; Java exit={result.returncode}\n"
                f"{result.stdout[-3000:]}\n{result.stderr[-3000:]}"
            ) from error
        if digest != hashlib.sha256(ontology.read_bytes()).hexdigest():
            raise ValueError("Ontology changed while HermiT was running; repeat the check")
        report.update(ontology_file=str(ontology), ontology_sha256=digest,
                      elapsed_seconds=elapsed, java_exit_code=result.returncode,
                      scope="OWLAPI logical axioms; not SHACL or operational compliance")
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
        print(f"HermiT timed out after {args.timeout:g}s; consistency is unknown.",
              file=sys.stderr)
        return 2
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"OWL consistency check failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
