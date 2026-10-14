import importlib.util
import json
import subprocess

import pytest



@pytest.fixture
def checker(root):
    spec = importlib.util.spec_from_file_location(
        "owl_checker_test", root / "tools/check_owl_consistency.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checker_rejects_missing_or_non_boolean_result(checker):
    with pytest.raises(ValueError, match="exactly one"):
        checker.parse_report("Java error")
    with pytest.raises(ValueError, match="Boolean"):
        checker.parse_report('CONTINUUM_OWL_REPORT\t{"consistent": "true"}')


@pytest.mark.parametrize("consistent,profile,require_profile,expected", [
    (True, True, False, 0), (False, True, False, 1),
    (True, False, False, 0), (True, False, True, 1),
])
def test_checker_separates_consistency_from_profile(
    checker, tmp_path, monkeypatch, consistent, profile, require_profile, expected,
):
    ontology = tmp_path / "ontology.ttl"
    ontology.write_text("# fixture\n", encoding="utf-8")
    output = tmp_path / "report.json"
    result = {"consistent": consistent, "owl2_dl_profile": profile,
              "unsatisfiable_classes": []}
    monkeypatch.setattr(checker.shutil, "which", lambda _: "/usr/bin/java")
    monkeypatch.setattr(checker.subprocess, "run", lambda *a, **kw:
                        subprocess.CompletedProcess(a, 0 if consistent else 1,
                            checker.REPORT_PREFIX + json.dumps(result), ""))
    args = [str(ontology), "--classpath", "fixture.jar", "--output", str(output)]
    if require_profile:
        args.append("--require-dl-profile")
    assert checker.main(args) == expected
    report = json.loads(output.read_text())
    assert report["ok"] is (expected == 0)
    assert len(report["ontology_sha256"]) == 64


def test_checker_timeout_is_not_reported_as_consistency(checker, tmp_path, monkeypatch):
    ontology = tmp_path / "ontology.ttl"
    ontology.write_text("# fixture\n", encoding="utf-8")
    monkeypatch.setattr(checker.shutil, "which", lambda _: "/usr/bin/java")

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("java", 1)

    monkeypatch.setattr(checker.subprocess, "run", timeout)
    output = tmp_path / "report.json"
    assert checker.main([str(ontology), "--classpath", "fixture.jar",
                         "--output", str(output), "--timeout", "1"]) == 2
    assert not output.exists()


def test_checker_uses_configured_heap(checker, tmp_path, monkeypatch):
    ontology = tmp_path / "ontology.ttl"
    ontology.write_text("# fixture\n")
    monkeypatch.setenv("CONTINUUM_OWL_JAVA_HEAP", "512m")
    monkeypatch.setattr(checker.shutil, "which", lambda _: "/usr/bin/java")

    def run(command, **kwargs):
        assert "-Xmx512m" in command
        report = {"consistent": True, "owl2_dl_profile": True,
                  "unsatisfiable_classes": []}
        return subprocess.CompletedProcess(command, 0,
            checker.REPORT_PREFIX + json.dumps(report), "")

    monkeypatch.setattr(checker.subprocess, "run", run)
    assert checker.main([str(ontology), "--classpath", "fixture.jar"]) == 0
