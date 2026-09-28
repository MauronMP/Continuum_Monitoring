"""External OWL reasoner validation with explicit availability semantics."""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from typing import Any

from rdflib import Graph, OWL, RDF

from .ontology import load_graph


def validate_external_reasoners(
    root: Path,
    config_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Run configured validators without treating missing tools as success."""

    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    validation = raw["validation"]
    configured_files = tuple(
        root / str(path) for path in validation.get("ontology_files", ())
    )
    if not configured_files:
        raise ValueError(
            "validation.ontology_files must list the active modular ontology"
        )
    missing = [str(path) for path in configured_files if not path.is_file()]
    if missing:
        raise ValueError(f"Ontology modules do not exist: {missing}")
    timeout = float(validation.get("timeout_seconds", 180))
    if timeout <= 0:
        raise ValueError("validation.timeout_seconds must be positive")
    requested = tuple(str(item) for item in validation["reasoners"])
    definitions = raw.get("reasoners", {})
    graph = load_graph(configured_files)
    declared_ontologies = set(graph.subjects(RDF.type, OWL.Ontology))
    imports = sorted(
        {(str(subject), str(target)) for subject, target in graph.subject_objects(OWL.imports)}
    )
    unresolved_imports = sorted(
        target
        for target in {target for _, target in graph.subject_objects(OWL.imports)}
        if target not in declared_ontologies
    )
    if unresolved_imports:
        raise ValueError(
            "The modular ontology has unresolved owl:imports: "
            + ", ".join(str(item) for item in unresolved_imports)
        )
    # OWLAPI resolves owl:imports as documents even when every imported graph is
    # already present in the flattened RDF union. Remove only those locally
    # resolved import declarations from the temporary closed-world document.
    compiled_graph = Graph()
    for prefix, namespace in graph.namespaces():
        compiled_graph.bind(prefix, namespace)
    for triple in graph:
        if triple[1] != OWL.imports:
            compiled_graph.add(triple)
    serialized = "\n".join(
        sorted(
            f"{subject.n3()} {predicate.n3()} {object_.n3()} ."
            for subject, predicate, object_ in compiled_graph
        )
    ) + "\n"
    with tempfile.TemporaryDirectory(prefix="continuum-modular-owl-") as temp:
        ontology = Path(temp) / "runtime-ontology.nt"
        ontology.write_text(serialized, encoding="utf-8")
        results = [
            _run_reasoner(
                root, ontology, name, definitions.get(name, {}), timeout
            )
            for name in requested
        ]
    report = {
        "ontology_files": [
            str(path.resolve()) for path in configured_files
        ],
        "compiled_ontology_sha256": hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest(),
        "source_ontology_triples": len(graph),
        "compiled_ontology_triples": len(compiled_graph),
        "resolved_imports": [
            {"ontology": source, "import": target}
            for source, target in imports
        ],
        "reasoners": results,
        "all_available": all(item["status"] != "unavailable" for item in results),
        "all_consistent": all(
            item["status"] == "completed" and item.get("consistent") is True
            for item in results
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def _run_reasoner(
    root: Path,
    ontology: Path,
    name: str,
    definition: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    kind = str(definition.get("kind", ""))
    reasoner_timeout = float(definition.get("timeout_seconds", timeout))
    if reasoner_timeout <= 0:
        return {
            "reasoner": name,
            "status": "invalid_configuration",
            "consistent": None,
            "detail": "reasoner timeout_seconds must be positive",
        }
    if kind == "owlapi":
        return _run_owlapi(root, ontology, name, definition, reasoner_timeout)
    if kind == "command":
        return _run_command(root, ontology, name, definition, reasoner_timeout)
    return {"reasoner": name, "status": "invalid_configuration", "consistent": None}


def _run_owlapi(
    root: Path,
    ontology: Path,
    name: str,
    definition: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    classpath_env = str(definition.get("classpath_env", ""))
    # The per-reasoner file is authoritative. A shared classpath previously
    # caused OWLAPI version collisions between HermiT, Openllet and JFact.
    installed_classpath = root / f".runtime/owl-validation-{name}.classpath"
    classpath = ""
    classpath_source = ""
    if installed_classpath.is_file():
        classpath = installed_classpath.read_text(encoding="utf-8").strip()
        classpath_source = str(installed_classpath)
    elif classpath_env and os.environ.get(classpath_env, ""):
        classpath = os.environ[classpath_env]
        classpath_source = classpath_env
    if not classpath:
        return {
            "reasoner": name,
            "status": "unavailable",
            "consistent": None,
            "detail": (
                "Run 'python3 tools/install_owl_reasoners.py' or set "
                f"{classpath_env} to the isolated {name} classpath."
            ),
        }
    command = [
        sys.executable,
        str(root / "tools/check_owl_consistency.py"),
        str(ontology),
        "--reasoner",
        name,
        "--require-dl-profile",
        "--timeout",
        str(timeout),
    ]
    if classpath:
        command.extend(("--classpath", classpath))
    result = _execute_json(name, command, timeout + 15)
    result["classpath_source"] = classpath_source
    return result


def _run_command(
    root: Path,
    ontology: Path,
    name: str,
    definition: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    template = [str(value) for value in definition.get("command", [])]
    if not template:
        return {"reasoner": name, "status": "invalid_configuration", "consistent": None}
    values = {
        "ontology": str(ontology),
        "root": str(root),
        "python": sys.executable,
    }
    rendered = [value.format(**values) for value in template]
    executable = shutil.which(rendered[0])
    if executable is None:
        return {
            "reasoner": name,
            "status": "unavailable",
            "consistent": None,
            "detail": f"Executable not found: {rendered[0]}",
        }
    command = [executable, *rendered[1:]]
    started = time.perf_counter()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=os.name != "nt",
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        _terminate_process_tree(process)
        stdout, stderr = process.communicate()
        captured = (stdout or "") + "\n" + (stderr or "")
        if not captured.strip():
            captured = _timeout_output(error)
        return {
            "reasoner": name,
            "status": "timeout",
            "consistent": None,
            "elapsed_seconds": time.perf_counter() - started,
            "timeout_seconds": timeout,
            "detail": _diagnostic_excerpt(captured) if captured else (
                f"Validation exceeded the configured {timeout:g} s limit; "
                "consistency remains unknown."
            ),
        }
    output = stdout + "\n" + stderr
    inconsistent = re.search(str(definition.get("inconsistent_pattern", "$^")), output)
    consistent = re.search(str(definition.get("consistent_pattern", "$^")), output)
    if inconsistent:
        value: bool | None = False
    elif consistent:
        value = True
    else:
        value = None
    return {
        "reasoner": name,
        "status": (
            "completed"
            if value is not None and process.returncode == 0
            else "failed"
        ),
        "consistent": value,
        "exit_code": process.returncode,
        "elapsed_seconds": time.perf_counter() - started,
        "output_excerpt": _diagnostic_excerpt(output),
    }


def _execute_json(name: str, command: list[str], timeout: float) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        captured = _timeout_output(error)
        return {
            "reasoner": name,
            "status": "timeout",
            "consistent": None,
            "elapsed_seconds": time.perf_counter() - started,
            "timeout_seconds": timeout,
            "detail": _diagnostic_excerpt(captured) if captured else (
                f"Validation exceeded the configured {timeout:g} s limit; "
                "consistency remains unknown."
            ),
        }
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        detail = _diagnostic_excerpt(completed.stderr or completed.stdout)
        unavailable = "classpath" in detail.lower() or "protégé" in detail.lower()
        return {
            "reasoner": name,
            "status": "unavailable" if unavailable else "failed",
            "consistent": None,
            "detail": detail,
            "elapsed_seconds": time.perf_counter() - started,
        }
    return {
        "reasoner": name,
        "status": "completed" if completed.returncode in {0, 1} else "failed",
        "consistent": payload.get("consistent"),
        "owl2_dl_profile": payload.get("owl2_dl_profile"),
        "unsatisfiable_classes": payload.get("unsatisfiable_classes", []),
        "elapsed_seconds": payload.get(
            "elapsed_seconds", time.perf_counter() - started
        ),
        "detail": payload,
    }


def _timeout_output(error: subprocess.TimeoutExpired) -> str:
    stdout = (
        error.stdout.decode(errors="replace")
        if isinstance(error.stdout, bytes)
        else error.stdout
    )
    stderr = (
        error.stderr.decode(errors="replace")
        if isinstance(error.stderr, bytes)
        else error.stderr
    )
    return (stdout or "") + "\n" + (stderr or "")


def _diagnostic_excerpt(output: str, limit: int = 4000) -> str:
    """Preserve both the causal exception and the bottom of a Java stack trace."""

    normalized = output.strip()
    if len(normalized) <= limit:
        return normalized
    half = (limit - len("\n... output truncated ...\n")) // 2
    return (
        normalized[:half]
        + "\n... output truncated ...\n"
        + normalized[-half:]
    )


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    """Stop a timed-out wrapper and its native reasoning child."""

    if process.poll() is not None:
        return
    if os.name != "nt":
        os.killpg(process.pid, signal.SIGTERM)
    else:  # pragma: no cover - Windows coordinator compatibility
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            os.killpg(process.pid, signal.SIGKILL)
        else:  # pragma: no cover - Windows coordinator compatibility
            process.kill()
