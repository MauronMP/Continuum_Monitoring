"""External OWL reasoner validation with explicit availability semantics."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import tomllib
from typing import Any


def validate_external_reasoners(
    root: Path,
    config_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Run configured validators without treating missing tools as success."""

    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    validation = raw["validation"]
    ontology = root / str(validation["ontology"])
    if not ontology.is_file():
        raise ValueError(f"Ontology does not exist: {ontology}")
    timeout = float(validation.get("timeout_seconds", 180))
    if timeout <= 0:
        raise ValueError("validation.timeout_seconds must be positive")
    requested = tuple(str(item) for item in validation["reasoners"])
    definitions = raw.get("reasoners", {})
    results = [
        _run_reasoner(root, ontology, name, definitions.get(name, {}), timeout)
        for name in requested
    ]
    report = {
        "ontology": str(ontology.resolve()),
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
    if kind == "owlapi":
        return _run_owlapi(root, ontology, name, definition, timeout)
    if kind == "command":
        return _run_command(ontology, name, definition, timeout)
    return {"reasoner": name, "status": "invalid_configuration", "consistent": None}


def _run_owlapi(
    root: Path,
    ontology: Path,
    name: str,
    definition: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    classpath_env = str(definition.get("classpath_env", ""))
    classpath = os.environ.get(classpath_env, "") if classpath_env else ""
    if name != "hermit" and not classpath:
        return {
            "reasoner": name,
            "status": "unavailable",
            "consistent": None,
            "detail": f"Set {classpath_env} to the OWLAPI reasoner classpath.",
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
    return _execute_json(name, command, timeout + 15)


def _run_command(
    ontology: Path,
    name: str,
    definition: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    template = [str(value) for value in definition.get("command", [])]
    if not template:
        return {"reasoner": name, "status": "invalid_configuration", "consistent": None}
    executable = shutil.which(template[0])
    if executable is None:
        return {
            "reasoner": name,
            "status": "unavailable",
            "consistent": None,
            "detail": f"Executable not found: {template[0]}",
        }
    command = [executable, *(value.format(ontology=str(ontology)) for value in template[1:])]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"reasoner": name, "status": "timeout", "consistent": None}
    output = completed.stdout + "\n" + completed.stderr
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
        "status": "completed" if value is not None else "failed",
        "consistent": value,
        "exit_code": completed.returncode,
        "elapsed_seconds": time.perf_counter() - started,
        "output_tail": output[-2000:],
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
    except subprocess.TimeoutExpired:
        return {"reasoner": name, "status": "timeout", "consistent": None}
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        detail = (completed.stderr or completed.stdout)[-2000:]
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
