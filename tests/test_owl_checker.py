import importlib.util
import json
import re
import subprocess
import zipfile

import pytest


@pytest.fixture
def checker(root):
    spec = importlib.util.spec_from_file_location(
        "owl_checker_test", root / "tools/check_owl_consistency.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checker_extracts_embedded_dependencies_safely(checker, tmp_path):
    bundles = tmp_path / "protege" / "bundles"
    plugins = tmp_path / "protege" / "plugins"
    dependencies = tmp_path / "dependencies"
    for path in (bundles, plugins, dependencies):
        path.mkdir(parents=True)
    with zipfile.ZipFile(bundles / "owlapi-osgidistribution.jar", "w") as archive:
        archive.writestr("lib/caffeine.jar", b"owlapi-dependency")
        archive.writestr("../../escape.jar", b"safe-basename")
        archive.writestr("README.txt", "not a dependency")
    with zipfile.ZipFile(plugins / "org.semanticweb.hermit-1.4.jar", "w") as archive:
        archive.writestr("automaton.jar", b"hermit-dependency")

    classpath = checker.protege_classpath(tmp_path / "protege", dependencies)

    assert "owlapi-osgidistribution.jar" in classpath
    assert "org.semanticweb.hermit-1.4.jar" in classpath
    assert (dependencies / "0-caffeine.jar").read_bytes() == b"owlapi-dependency"
    assert (dependencies / "0-escape.jar").read_bytes() == b"safe-basename"
    assert not (tmp_path / "escape.jar").exists()
    assert not (dependencies / "README.txt").exists()


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


@pytest.mark.owl_consistency
def test_canonical_ontology_with_installed_protege_hermit(checker, tmp_path):
    try:
        protege = checker.find_protege(None)
    except ValueError:
        pytest.skip("Optional HermiT integration requires PROTEGE_HOME")
    java = checker.shutil.which("java")
    if java is None:
        pytest.skip("Optional HermiT integration requires Java 11+")
    # macOS can expose a java shim even when no JDK is installed.
    try:
        version = subprocess.run([java, "-version"], capture_output=True,
                                 text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        pytest.skip("Optional HermiT integration requires a working Java 11+")
    match = re.search(r'(?:openjdk|java)(?: version)?\s+"?(\d+)',
                      version.stdout + "\n" + version.stderr)
    if version.returncode or not match or int(match.group(1)) < 11:
        pytest.skip("Optional HermiT integration requires a working Java 11+")
    output = tmp_path / "hermit.json"
    assert checker.main(["--protege-home", str(protege), "--require-dl-profile",
                         "--output", str(output)]) == 0
    result = json.loads(output.read_text())
    assert result["consistent"] is True
    assert result["unsatisfiable_classes"] == []
    assert result["profile_violation_count"] == 0
