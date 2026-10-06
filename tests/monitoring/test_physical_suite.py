from pathlib import Path
from types import SimpleNamespace

import pytest

from continuum_bench.monitoring import physical_suite


def _result(root: Path, name: str, status: str) -> Path:
    output = root / name
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.csv").write_text(
        f"status,reasoner\n{status},rdfs\n", encoding="utf-8"
    )
    return output


def test_all_runs_every_family_before_reporting_invalid_evidence(
    tmp_path, monkeypatch, capsys,
):
    calls = []

    def cumulative(*args, **kwargs):
        calls.append("cumulative")
        return _result(tmp_path, "cumulative", "invalid_results")

    def scalability(*args, **kwargs):
        calls.append("scalability")
        return _result(tmp_path, "scalability", "completed")

    monkeypatch.setattr(physical_suite, "run_distributed_cumulative", cumulative)
    monkeypatch.setattr(physical_suite, "run_distributed_scalability", scalability)
    inventory = SimpleNamespace(
        nodes=[SimpleNamespace(endpoint="http://worker")], topology=None
    )

    with pytest.raises(RuntimeError, match="invalid_results=1"):
        physical_suite.run_physical_monitoring_suite(
            SimpleNamespace(), inventory, tmp_path,
            suite="all", layout="distributed",
        )

    assert calls == ["cumulative", "scalability"]
    progress = [
        line for line in capsys.readouterr().out.splitlines()
        if line.startswith("[physical-suite-progress]")
    ]
    assert "family=cumulative family_index=1/2 percent=0.0 status=running" in progress[0]
    assert "family=cumulative family_index=1/2 percent=50.0 status=completed" in progress[1]
    assert "family=scalability family_index=2/2 percent=50.0 status=running" in progress[2]
    assert "family=scalability family_index=2/2 percent=100.0 status=completed" in progress[3]


def test_timeouts_remain_censored_without_becoming_hard_failures(
    tmp_path, monkeypatch,
):
    monkeypatch.setattr(
        physical_suite,
        "run_physical_scalability",
        lambda *args, **kwargs: _result(tmp_path, "scalability", "timeout"),
    )
    inventory = SimpleNamespace(
        path=tmp_path / "inventory.toml", topology_name="physical"
    )

    result = physical_suite.run_physical_monitoring_suite(
        SimpleNamespace(), inventory, tmp_path,
        suite="scalability", layout="replicated",
    )

    assert result["scalability"].endswith("scalability")
