from continuum_bench import environment


def test_doctor_detects_incomplete_clone(tmp_path):
    assert environment.project_checks(tmp_path)[0].status == "error"
    assert (
        "smartcity_continuum-v3.0.0.ttl"
        in environment.project_checks(tmp_path)[0].detail
    )


def test_physical_checks_are_reported(monkeypatch):
    monkeypatch.setattr(environment.shutil, "which", lambda name: f"/usr/bin/{name}")

    checks = environment.physical_checks()

    assert {item.name for item in checks} == {"ssh", "ssh-copy-id", "rsync"}
    assert all(item.status == "ok" for item in checks)


def test_docker_check_reports_missing_binary(monkeypatch):
    monkeypatch.setattr(environment.shutil, "which", lambda name: None)

    checks = environment.docker_checks()

    assert checks[0].name == "docker"
    assert checks[0].status == "error"


def test_docker_check_distinguishes_compose_from_daemon(monkeypatch):
    class Result:
        def __init__(self, returncode, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    monkeypatch.setattr(
        environment.shutil, "which", lambda name: "/usr/bin/docker"
    )
    responses = iter(
        (
            Result(0, "Docker Compose version v2"),
            Result(1, stderr="Cannot connect to the Docker daemon"),
        )
    )
    monkeypatch.setattr(
        "subprocess.run", lambda *args, **kwargs: next(responses)
    )

    checks = environment.docker_checks()

    assert [item.name for item in checks] == [
        "docker-compose",
        "docker-daemon",
    ]
    assert checks[0].status == "ok"
    assert checks[1].status == "error"
    assert "Cannot connect" in checks[1].detail
