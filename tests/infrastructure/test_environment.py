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
