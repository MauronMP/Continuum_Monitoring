"""Behavioral contracts for independent paired decision comparisons."""
from copy import deepcopy
from pathlib import Path

import pytest
import sys
import shutil

requires_linux = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Physical process measurements require Linux procfs")

from continuum_bench.monitoring.comparison.adapters import build_adapter, SemanticAdapter, NS, term
from continuum_bench.monitoring.comparison.config import load
from continuum_bench.monitoring.comparison.reporting import paired_statistics
from continuum_bench.monitoring.comparison.runner import jobs
from continuum_bench.monitoring.comparison.worker import execute
from continuum_bench.monitoring.comparison.workload import expand, operational, quality, trace
from continuum_bench.monitoring.policy_evaluation.config import load_policy_evaluation_config
from rdflib import RDF

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def workload():
    config = load_policy_evaluation_config(ROOT / "tests/fixtures/policy-evaluation.toml")
    return expand(config, {"mist"}, 2)


@pytest.mark.parametrize("strategy", ["procedural", "semantic"])
def test_equivalent_operational_plans_against_explicit_fixtures(workload, strategy):
    adapter, _ = build_adapter(strategy, workload)
    for scenario in workload["scenarios"]:
        assert operational(adapter.decide(scenario["context"])) == scenario["expected"]
    assert all(not r["identifier"].startswith("mist#") for r in workload["resources"])


def test_inference_actually_changes_selection(workload):
    adapter, _ = build_adapter("semantic", workload)
    assert len(adapter.decide("normal").resources) == 6
    for resource in workload["resources"]:
        adapter.graph.remove((term("resource:"+resource["identifier"]), RDF.type, term("tier:"+resource["tier"])))
    assert not adapter.decide("normal").resources


def test_unknown_context_deactivates_all_policies(workload):
    for strategy in ("procedural", "semantic"):
        adapter, _ = build_adapter(strategy, workload)
        adapter.decide("failure")
        plan = adapter.decide("unknown-context")
        assert not plan.resources and not plan.policies and not plan.actions


def test_oracle_is_not_used_by_adapters(workload):
    corrupted = deepcopy(workload)
    corrupted["scenarios"][0]["expected"]["resources"] = []
    left, _ = build_adapter("semantic", workload)
    right, _ = build_adapter("semantic", corrupted)
    assert left.decide("normal") == right.decide("normal")
    assert not quality(operational(right.decide("normal")), corrupted["scenarios"][0]["expected"])["plan_correct"]


def test_trace_determinism_and_transitions(workload):
    assert trace(workload, 3, 42, False) == trace(workload, 3, 42, False)
    assert trace(workload, 3, 42, False) != trace(workload, 3, 43, False)
    assert [e["context"] for e in trace(workload, 1, 42, True)] == ["normal", "overload", "failure", "recovery"]


@requires_linux
def test_worker_measures_real_decisions_and_cumulative_sum(workload):
    result = execute({"strategy": "semantic", "workload": workload, "events": trace(workload, 2, 42, True), "warmup": 1})
    assert result["status"] == "completed"
    assert all(e["plan_correct"] for e in result["events"])
    assert result["reasoning_ms"] > 0
    assert result["closure_triples"] > result["explicit_triples"]
    assert result["events"][-1]["cumulative_decision_ms"] == pytest.approx(sum(e["decision_ms"] for e in result["events"]))
    assert result["measurement"]["ram_max_mib"] > 0


def test_schedule_is_paired_and_deterministic():
    config = load(ROOT / "configs/comparison.toml")
    assert list(jobs(config)) == list(jobs(config))
    assert len(list(jobs(config))) == (1+1+3+3)*5*3


def test_metrics_do_not_penalize_static_for_absent_policy_ids(workload):
    expected = workload["scenarios"][0]["expected"]
    assert quality(expected, expected)["plan_correct"]
    assert quality(expected, expected)["coverage"] == 1


def test_mismatched_traces_are_not_paired():
    rows = [dict(node="edge1", experiment="effectiveness", size=1, repetition=1, status="completed", strategy=s,
                 trace_sha256=s, workload_sha256="same") for s in ("semantic", "procedural")]
    assert paired_statistics(rows) == []


def test_config_rejects_unlimited_and_unknown_keys(tmp_path):
    text = (ROOT / "configs/comparison.toml").read_text()
    path = tmp_path / "invalid.toml"
    path.write_text(text.replace("timeout_seconds = 120", "timeout_seconds = 0"))
    with pytest.raises(ValueError, match="timeout_seconds"):
        load(path)


def test_timeout_continues_battery_and_marks_exit(tmp_path, monkeypatch):
    from continuum_bench.monitoring.comparison import runner, reporting
    config = load(ROOT / "configs/comparison.toml")
    config.update(output=str(tmp_path / "results"), experiments=["effectiveness"], repetitions=1)
    monkeypatch.setattr(runner, "probe", lambda node, *a: {"node": node.role, "available": True})
    attempted = []
    def fake_invoke(node, inventory, cfg, bundle, payload):
        attempted.append(payload["strategy"])
        return {"status": "timeout", "error": "controlled timeout"}
    monkeypatch.setattr(runner, "invoke", fake_invoke)
    monkeypatch.setattr(reporting, "report", lambda path: {})
    directory, failed = runner.run(config, tmp_path, ["cloud"])
    assert failed
    assert sorted(attempted) == ["procedural", "semantic", "static"]
    import json
    assert json.loads((directory / "metadata.json").read_text())["failed_jobs"] == 3
    assert len((directory / "jobs.jsonl").read_text().splitlines()) == 3


def test_transport_timeout_is_not_a_success(monkeypatch):
    import subprocess
    from types import SimpleNamespace
    from continuum_bench.monitoring.comparison import transport
    monkeypatch.setattr(transport.subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess([], 124, "", ""))
    result = transport.invoke(SimpleNamespace(local=True), None,
                              {"timeout_seconds": .1, "connect_timeout_seconds": 1}, b"", {})
    assert result["status"] == "timeout"


def test_bundle_contains_importable_current_sources():
    import io
    import zipfile
    from continuum_bench.monitoring.comparison.transport import source_bundle
    archive = zipfile.ZipFile(io.BytesIO(source_bundle()))
    assert "continuum_bench/monitoring/comparison/worker.py" in archive.namelist()
    assert source_bundle() == source_bundle()


@requires_linux
def test_report_preserves_failure_denominator_and_pngs(tmp_path, workload):
    import json
    from continuum_bench.monitoring.comparison.reporting import report
    result = execute({"strategy": "procedural", "workload": workload, "events": trace(workload, 1, 42, True), "warmup": 0})
    record = dict(job_id="one", node="cloud", tier="cloud", experiment="effectiveness", size=1, repetition=1,
                  strategy="procedural", resource_count=10, policy_count=14, event_count=4, trace_sha256="x",
                  workload_sha256="y", timeout_seconds=1, transport_wall_ms=10, **result)
    failure = dict(record, job_id="two", status="timeout", strategy="semantic", events=[])
    (tmp_path / "jobs.jsonl").write_text(json.dumps(record)+"\n"+json.dumps(failure)+"\n")
    manifest = report(tmp_path)
    assert manifest["completed_jobs"] == 1 and manifest["unsuccessful_jobs"] == 1
    assert (tmp_path / "effectiveness/figures/cloud.png").is_file()
    assert "effectiveness/figures/all-nodes.png" in manifest["figures"]
    assert "figures/cross-node-summary.png" in manifest["figures"]
    assert (tmp_path / "cross-node-summary-data.csv").is_file()
    assert not list(tmp_path.rglob("*.pdf"))
    assert "timeout" in (tmp_path / "summary.csv").read_text()


def test_transport_os_error_is_a_failed_job(monkeypatch):
    from types import SimpleNamespace
    from continuum_bench.monitoring.comparison import transport
    def fail(*args, **kwargs):
        raise FileNotFoundError("missing timeout executable")
    monkeypatch.setattr(transport.subprocess, "run", fail)
    assert transport.invoke(SimpleNamespace(local=True), None,
                            {"timeout_seconds": 1, "connect_timeout_seconds": 1}, b"", {})["status"] == "failed"


def test_misspelled_exclusion_is_rejected():
    from continuum_bench.monitoring.comparison.runner import inventory_for
    config = load(ROOT / "configs/comparison.toml")
    config["exclude_nodes"] = ["msit"]
    with pytest.raises(ValueError, match="Unknown excluded nodes"):
        inventory_for(config)


def test_uncertainty_needs_independent_repetitions():
    from continuum_bench.monitoring.comparison.statistics import estimate
    assert estimate([1, 2, 3, 4])["low"] is None
    result = estimate([1, 2, 3, 4, 5], "group")
    assert result == estimate([1, 2, 3, 4, 5], "group")
    assert result["low"] < result["mean"] < result["high"]
    with pytest.raises(ValueError, match="Non-finite"):
        estimate([float("nan")])


@pytest.fixture
def measured_record(workload):
    if not sys.platform.startswith("linux"):
        pytest.skip("Physical process measurements require Linux procfs")
    result = execute({"strategy": "procedural", "workload": workload,
                      "events": trace(workload, 2, 42, True), "warmup": 0})
    return dict(job_id="one", node="cloud", tier="cloud", experiment="adaptation", size=1, repetition=1,
                strategy="procedural", resource_count=10, policy_count=14, event_count=8,
                trace_sha256="trace", workload_sha256="workload", timeout_seconds=1, transport_wall_ms=10, **result)


def test_plot_uses_process_repetitions_not_event_count(measured_record):
    from continuum_bench.monitoring.comparison.reporting import summarize
    from continuum_bench.monitoring.comparison.figures import point_table
    points = point_table([measured_record], [summarize(measured_record)])
    assert all(p["n"] == 1 and p["low"] is None for p in points if p["strategy"] == "procedural")


@pytest.mark.parametrize("corruption", ["duplicate", "nan", "cumulative", "quality"])
def test_corrupt_evidence_is_rejected(measured_record, corruption):
    from continuum_bench.monitoring.comparison.validation import validate_records
    records = [deepcopy(measured_record)]
    if corruption == "duplicate":
        records.append(deepcopy(measured_record))
    elif corruption == "nan":
        records[0]["events"][0]["decision_ms"] = float("nan")
    elif corruption == "cumulative":
        records[0]["events"][0]["cumulative_decision_ms"] += 10
    else:
        records[0]["events"][0]["plan_correct"] = False
    with pytest.raises(ValueError):
        validate_records(records)


def test_report_handles_only_truncated_tail(tmp_path, measured_record):
    import json
    from continuum_bench.monitoring.comparison.reporting import report
    path = tmp_path / "jobs.jsonl"
    text = json.dumps(measured_record)
    path.write_text(text + '\n{"job_id":')
    assert report(tmp_path)["truncated_final_record_ignored"]
    path.write_text(text + '\n{"job_id":\n')
    with pytest.raises(json.JSONDecodeError):
        report(tmp_path)


def test_missing_middle_point_breaks_curve():
    import matplotlib.pyplot as plt
    import numpy as np
    from continuum_bench.monitoring.comparison.figures import _draw, COLORS
    points = []
    for strategy in COLORS:
        for size in (1, 2, 3):
            points.append(dict(strategy=strategy, x=size, mean=None if size==2 else float(size), low=None, high=None,
                               experiment="scalability", resource_count=size*5, event_count=4))
    fig, ax = plt.subplots()
    _draw(ax, points, "decision_mean_ms", [1, 2, 3], False)
    assert len(ax.lines) == 3
    assert all(np.isnan(line.get_ydata()[1]) for line in ax.lines)
    assert all(list(line.get_xdata()) == [5, 10, 15] for line in ax.lines)
    plt.close(fig)


@requires_linux
def test_warmup_covers_each_context(workload, monkeypatch):
    from continuum_bench.monitoring.comparison import worker
    adapter, setup_ms = build_adapter("procedural", workload)
    seen = []
    decide = adapter.decide
    def observed(context):
        seen.append(context)
        return decide(context)
    adapter.decide = observed
    monkeypatch.setattr(worker, "build_adapter", lambda *args: (adapter, setup_ms))
    worker.execute({"strategy":"procedural", "workload":workload,
                    "events":trace(workload, 2, 45, False), "warmup":1})
    assert seen[:4] == ["normal", "overload", "failure", "recovery"]


def test_report_all_timeouts_is_explicit(tmp_path, measured_record):
    import json
    from continuum_bench.monitoring.comparison.reporting import report
    record = dict(measured_record, status="timeout", events=[])
    (tmp_path / "jobs.jsonl").write_text(json.dumps(record)+"\n")
    manifest = report(tmp_path)
    assert manifest["minimum_completed_repetitions"] == 0
    assert manifest["unsuccessful_jobs"] == 1
    assert not (tmp_path / "paired-comparisons.csv").exists()


@requires_linux
@pytest.mark.skipif(shutil.which("timeout") is None, reason="GNU timeout required for physical executor")
def test_isolated_worker_protocol_validates_real_response(workload):
    from types import SimpleNamespace
    from continuum_bench.monitoring.comparison.transport import invoke, source_bundle
    payload = {"strategy":"semantic", "workload":workload, "events":trace(workload, 1, 42, True), "warmup":1}
    response = invoke(SimpleNamespace(local=True), None,
                      {"timeout_seconds":20, "connect_timeout_seconds":1}, source_bundle(), payload)
    assert response["status"] == "completed"
    assert response["measurement_contract"] == "comparison-v2-complete-context-warmup"


def test_default_comparison_includes_mist():
    from continuum_bench.monitoring.comparison.config import load
    from continuum_bench.monitoring.comparison.runner import inventory_for, jobs
    config = load("configs/comparison.toml")
    _, nodes = inventory_for(config, None)
    assert {n.role for n in nodes} == {"cloud", "fog", "mist", "edge1", "edge2", "edge3"}
    assert config["exclude_resources"] == []
    assert len(list(jobs(config))) * len(nodes) == 720
