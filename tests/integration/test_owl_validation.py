from __future__ import annotations

import json
import subprocess
import time

from continuum_bench import owl_validation


def test_missing_external_reasoners_are_not_reported_as_success(
    root, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        owl_validation,
        "_run_owlapi",
        lambda root, ontology, name, definition, timeout: {
            "reasoner": name,
            "status": "unavailable",
            "consistent": None,
        },
    )
    monkeypatch.setattr(owl_validation.shutil, "which", lambda _: None)
    report = owl_validation.validate_external_reasoners(
        root,
        root / "configs/owl-reasoners.toml",
        tmp_path / "report.json",
    )

    by_name = {item["reasoner"]: item for item in report["reasoners"]}
    assert by_name["openllet"]["status"] == "unavailable"
    assert by_name["jfact"]["status"] == "unavailable"
    assert report["all_available"] is False


def test_owlapi_adapter_preserves_machine_readable_consistency(
    root, tmp_path, monkeypatch
):
    monkeypatch.setenv("CONTINUUM_OPENLLET_CLASSPATH", "fixture.jar")
    payload = {
        "consistent": True,
        "owl2_dl_profile": True,
        "unsatisfiable_classes": [],
        "elapsed_seconds": 0.5,
    }
    monkeypatch.setattr(
        owl_validation.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, json.dumps(payload), ""
        ),
    )

    result = owl_validation._run_owlapi(
        root,
        root / "ontology/legacy/smartcity_continuum-v3.0.0.ttl",
        "openllet",
        {"classpath_env": "CONTINUUM_OPENLLET_CLASSPATH"},
        10,
    )

    assert result["status"] == "completed"
    assert result["consistent"] is True


def test_owlapi_adapter_uses_installed_project_classpath(
    root, tmp_path, monkeypatch
):
    runtime = root / ".runtime"
    runtime.mkdir(exist_ok=True)
    classpath_file = runtime / "owl-validation-jfact.classpath"
    previous = classpath_file.read_text() if classpath_file.exists() else None
    classpath_file.write_text("project-runtime.jar\n")
    monkeypatch.delenv("CONTINUUM_JFACT_CLASSPATH", raising=False)
    observed = {}

    def execute(name, command, timeout):
        observed["command"] = command
        return {"reasoner": name, "status": "completed", "consistent": True}

    monkeypatch.setattr(owl_validation, "_execute_json", execute)
    try:
        owl_validation._run_owlapi(
            root,
            root / "ontology/legacy/smartcity_continuum-v3.0.0.ttl",
            "jfact",
            {"classpath_env": "CONTINUUM_JFACT_CLASSPATH"},
            10,
        )
    finally:
        if previous is None:
            classpath_file.unlink()
            runtime.rmdir()
        else:
            classpath_file.write_text(previous)

    assert "project-runtime.jar" in observed["command"]


def test_owlapi_adapter_prefers_isolated_reasoner_classpath(
    tmp_path, monkeypatch
):
    ontology = tmp_path / "ontology.ttl"
    ontology.write_text("<urn:test> a <http://www.w3.org/2002/07/owl#Ontology> .")
    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    (runtime / "owl-validation-hermit.classpath").write_text(
        "isolated-hermit.jar\n"
    )
    (runtime / "owl-validation.classpath").write_text("legacy-combined.jar\n")
    monkeypatch.setenv("CONTINUUM_HERMIT_CLASSPATH", "stale-env.jar")
    observed = {}

    def execute(name, command, timeout):
        observed["command"] = command
        return {"reasoner": name, "status": "completed", "consistent": True}

    monkeypatch.setattr(owl_validation, "_execute_json", execute)
    result = owl_validation._run_owlapi(
        tmp_path,
        ontology,
        "hermit",
        {"classpath_env": "CONTINUUM_HERMIT_CLASSPATH"},
        10,
    )

    assert "isolated-hermit.jar" in observed["command"]
    assert "stale-env.jar" not in observed["command"]
    assert result["classpath_source"].endswith(
        ".runtime/owl-validation-hermit.classpath"
    )


def test_command_reasoner_timeout_is_bounded_and_reported(root):
    started = time.perf_counter()
    result = owl_validation._run_command(
        root,
        root / "ontology/legacy/smartcity_continuum-v3.0.0.ttl",
        "fixture",
        {
            "command": [
                "{python}",
                "-c",
                "import time; print('started', flush=True); time.sleep(10)",
            ]
        },
        0.1,
    )

    assert result["status"] == "timeout"
    assert result["consistent"] is None
    assert result["timeout_seconds"] == 0.1
    assert "started" in result["detail"]
    assert time.perf_counter() - started < 3


def test_command_reasoner_accepts_konclude_native_consistency_wording(root):
    result = owl_validation._run_command(
        root,
        root / "ontology/legacy/smartcity_continuum-v3.0.0.ttl",
        "konclude-fixture",
        {
            "command": [
                "{python}",
                "-c",
                (
                    "print(\"Ontology '/tmp/ontology.owl.xml' "
                    "is consistent.\")"
                ),
            ],
            "consistent_pattern": (
                r"(?i)ontology(?:\s+['\"][^'\"]+['\"])?"
                r"\s+is\s+consistent\b"
            ),
            "inconsistent_pattern": r"(?i)\bis\s+inconsistent\b",
        },
        2,
    )

    assert result["status"] == "completed"
    assert result["consistent"] is True
