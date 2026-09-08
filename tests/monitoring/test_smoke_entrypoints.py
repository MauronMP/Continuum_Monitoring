import csv

from continuum_bench import smoke


def _write_summary(path, statuses):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["status"])
        writer.writeheader()
        for status in statuses:
            writer.writerow({"status": status})


def test_smoke_cumulative_uses_isolated_output_and_passes_arguments(
    monkeypatch, tmp_path
):
    calls = []
    monkeypatch.chdir(tmp_path)
    (tmp_path / "configs").mkdir()
    summary = (
        tmp_path
        / "outputs/smoke/physical-monitoring/sharded/cumulative/summary.csv"
    )
    _write_summary(summary, ["completed"])
    monkeypatch.setattr(
        smoke.sys,
        "argv",
        ["continuum-smoke-cumulative", "--ssh-user", "pi"],
    )
    monkeypatch.setattr(smoke, "main", lambda args: calls.append(args) or 0)

    assert smoke.main_cumulative() == 0
    assert calls[0][-2:] == ["--ssh-user", "pi"]
    assert calls[0][2:4] == ["physical", "cumulative"]
    assert "outputs/smoke/physical-monitoring" in calls[0]


def test_smoke_scalability_honours_layout(monkeypatch, tmp_path):
    calls = []
    monkeypatch.chdir(tmp_path)
    (tmp_path / "configs").mkdir()
    summary = (
        tmp_path
        / "outputs/smoke/physical-monitoring/replicated/scalability/summary.csv"
    )
    _write_summary(summary, ["completed"])
    monkeypatch.setattr(
        smoke.sys,
        "argv",
        ["continuum-smoke-scalability", "--layout", "replicated"],
    )
    monkeypatch.setattr(smoke, "main", lambda args: calls.append(args) or 0)

    assert smoke.main_scalability() == 0
    assert calls[0][-2:] == ["--layout", "replicated"]


def test_smoke_rejects_censored_or_missing_results(tmp_path):
    timed_out = tmp_path / "timeout.csv"
    _write_summary(timed_out, ["completed", "timeout"])

    assert smoke._require_completed_summaries([timed_out]) == 1
    assert smoke._require_completed_summaries([tmp_path / "missing.csv"]) == 1
