import json
import subprocess

import pytest

from continuum_bench import environment


def _mock_docker(monkeypatch, *, denied=False, server_os="linux", arch="x86_64"):
    monkeypatch.setattr(environment.shutil, "which", lambda *a, **k: "/usr/bin/docker")
    calls = []

    def probe(command, env, root):
        calls.append(command)
        if command[1:3] == ["compose", "version"]:
            return subprocess.CompletedProcess(command, 0, "2.39.1", "")
        if command[1] == "info":
            if denied:
                return subprocess.CompletedProcess(
                    command,
                    1,
                    "",
                    "permission denied while connecting to /var/run/docker.sock",
                )
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps(
                    {"os": server_os, "arch": arch, "memory_bytes": 16 * 1024**3}
                ),
                "",
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(environment, "_probe", probe)
    return calls


def test_ubuntu_permission_error_is_actionable_without_changing_permissions(
    monkeypatch, tmp_path
):
    calls = _mock_docker(monkeypatch, denied=True)
    checks = environment.docker_checks(tmp_path)
    with pytest.raises(RuntimeError, match="rootless"):
        environment.require_checks(checks)
    assert len(calls) == 2
    assert not any("sudo" in call or "chmod" in call for call in calls)


@pytest.mark.parametrize("arch", ["amd64", "x86_64", "arm64", "aarch64"])
def test_supported_linux_daemons(monkeypatch, tmp_path, arch):
    _mock_docker(monkeypatch, arch=arch)
    environment.require_checks(environment.docker_checks(tmp_path))


@pytest.mark.parametrize(
    ("server_os", "arch"), [("windows", "amd64"), ("linux", "armv7l")]
)
def test_unsupported_daemons_are_rejected(monkeypatch, tmp_path, server_os, arch):
    _mock_docker(monkeypatch, server_os=server_os, arch=arch)
    with pytest.raises(RuntimeError, match="64 bits"):
        environment.require_checks(environment.docker_checks(tmp_path))


def test_missing_docker_has_install_instructions(monkeypatch, tmp_path):
    monkeypatch.setattr(environment.shutil, "which", lambda *a, **k: None)
    checks = environment.docker_checks(tmp_path)
    assert checks[0].status == "error"
    assert "install/ubuntu" in checks[0].hint


def test_doctor_checks_buildx_before_building(monkeypatch, tmp_path):
    calls = _mock_docker(monkeypatch)
    environment.require_checks(environment.docker_checks(tmp_path))
    assert ["docker", "buildx", "version"] in calls


def test_registry_deadline_error_has_network_hint():
    assert "DNS" in environment.failure_hint(
        "DeadlineExceeded: context deadline exceeded"
    )


def test_missing_buildx_has_install_hint():
    assert "docker-buildx-plugin" in environment.failure_hint(
        "docker: unknown command: docker buildx"
    )


def test_pip_proxy_failure_does_not_suggest_restarting_docker():
    assert "DNS" in environment.failure_hint("pip: Cannot connect to proxy")


def test_doctor_detects_incomplete_clone(tmp_path):
    assert environment.project_checks(tmp_path)[0].status == "error"
    assert (
        "smartcity_continuum-v3.0.0.ttl"
        in environment.project_checks(tmp_path)[0].detail
    )


def test_docker_environment_preserves_user_context_and_proxy(monkeypatch):
    monkeypatch.setenv("DOCKER_HOST", "unix:///run/user/1000/docker.sock")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example:8080")
    value = environment.docker_environment()
    assert value["DOCKER_HOST"] == "unix:///run/user/1000/docker.sock"
    assert value["HTTPS_PROXY"] == "http://proxy.example:8080"


def test_doctor_probe_timeout_is_an_error(monkeypatch, tmp_path):
    _mock_docker(monkeypatch)
    monkeypatch.setattr(
        environment,
        "_probe",
        lambda *a: (_ for _ in ()).throw(subprocess.TimeoutExpired("docker", 20)),
    )
    assert environment.docker_checks(tmp_path)[0].status == "error"
