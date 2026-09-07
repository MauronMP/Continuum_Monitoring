from continuum_bench import smoke


def test_smoke_cumulative_passes_cli_arguments(monkeypatch, tmp_path):
    calls = []
    monkeypatch.chdir(tmp_path)
    (tmp_path / "configs").mkdir()
    monkeypatch.setattr(smoke.sys, "argv", ["continuum-smoke-cumulative", "--ssh-user", "pi"])
    monkeypatch.setattr(smoke, "main", lambda args: calls.append(args) or 0)

    assert smoke.main_cumulative() == 0
    assert calls[0][-2:] == ["--ssh-user", "pi"]
    assert calls[0][-4:-2] == ["physical", "cumulative"]


def test_smoke_scalability_passes_cli_arguments(monkeypatch, tmp_path):
    calls = []
    monkeypatch.chdir(tmp_path)
    (tmp_path / "configs").mkdir()
    monkeypatch.setattr(smoke.sys, "argv", ["continuum-smoke-scalability", "--ssh-user", "pi"])
    monkeypatch.setattr(smoke, "main", lambda args: calls.append(args) or 0)

    assert smoke.main_scalability() == 0
    assert calls[0][-2:] == ["--ssh-user", "pi"]
    assert calls[0][-4:-2] == ["physical", "scalability"]
