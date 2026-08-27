import importlib.util
import re
import subprocess

import pytest
import tomllib


@pytest.fixture
def bootstrap(root):
    spec = importlib.util.spec_from_file_location(
        "bootstrap_test", root / "tools/bootstrap.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_docker_runtime_dependencies_match_package(root):
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    declared = {
        re.split(r"[><=;\[]", item)[0].lower() for item in project["dependencies"]
    }
    runtime = {
        line
        for line in (root / "requirements/runtime.txt").read_text().splitlines()
        if line and not line.startswith(("#", "-"))
    }
    assert declared == runtime - {"setuptools"}


def test_worker_requirements_are_minimal_and_pinned(root):
    lines = (root / "requirements-node.txt").read_text().splitlines()
    packages = [line for line in lines if line and not line.startswith("#")]
    assert {line.split("==")[0] for line in packages} == {
        "rdflib",
        "owlrl",
        "pyparsing",
    }
    assert all("==" in line for line in packages)


def test_bootstrap_install_is_wheel_only_and_uses_constraints(
    root, tmp_path, bootstrap
):
    commands = bootstrap.install_commands(root, tmp_path / "python", worker=False)
    assert "--only-binary=:all:" in commands[0]
    assert "--no-build-isolation" in commands[1]
    assert str(root / "requirements/constraints.txt") in commands[1]
    assert all("sudo" not in command for command in commands)


def test_bootstrap_rejects_an_old_virtualenv(bootstrap, monkeypatch, tmp_path):
    monkeypatch.setattr(
        bootstrap.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(a, 1, "3.9.2 64 bits", ""),
    )
    with pytest.raises(RuntimeError, match="Virtualenv incompatible"):
        bootstrap.check_virtualenv(tmp_path / "python", worker=False)


def test_bootstrap_rejects_a_copied_virtualenv(bootstrap, tmp_path):
    with pytest.raises(RuntimeError, match="no es ejecutable"):
        bootstrap.check_virtualenv(tmp_path / "missing-python", worker=False)


def test_package_version_matches_metadata(root):
    from continuum_bench import __version__

    assert (
        __version__
        == tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    )
