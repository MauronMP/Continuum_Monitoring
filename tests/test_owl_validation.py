from __future__ import annotations

import json
import subprocess

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
    classpath_file = runtime / "owl-validation.classpath"
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
