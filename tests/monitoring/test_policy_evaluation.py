from __future__ import annotations

import csv
from pathlib import Path

from continuum_bench.monitoring.policy_evaluation.config import (
    load_policy_evaluation_config,
)
from continuum_bench.monitoring.policy_evaluation.model import PolicyEngine
from continuum_bench.monitoring.policy_evaluation.reporting import (
    plot_policy_evaluation,
)
from continuum_bench.monitoring.policy_evaluation.runner import (
    EXPERIMENTS,
    RESULT_FILES,
    run_policy_evaluation,
)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_policy_engine_matches_configured_ground_truth(config) -> None:
    evaluation = load_policy_evaluation_config(
        config.root / "tests/fixtures/policy-evaluation.toml"
    )
    engine = PolicyEngine(evaluation.resources, evaluation.rules)
    for scenario in evaluation.scenarios:
        plan = engine.decide(scenario.context).plan
        assert set(plan.policies) == set(scenario.expected_policies)
        assert set(plan.resources) == set(scenario.expected_resources)
        assert set(plan.metrics) == set(scenario.expected_metrics)
        assert set(plan.actions) == set(scenario.expected_actions)
        assert plan.sampling_interval_seconds == scenario.expected_sampling_interval_seconds


def test_four_policy_evaluations_export_reproducible_csv_and_png(config, tmp_path) -> None:
    evaluation = load_policy_evaluation_config(
        config.root / "tests/fixtures/policy-evaluation.toml"
    )
    manifest = run_policy_evaluation(config, evaluation, tmp_path, EXPERIMENTS)
    assert set(manifest["results"]) == set(EXPERIMENTS)
    for experiment, filename in RESULT_FILES.items():
        rows = _read(tmp_path / experiment / filename)
        assert rows
        assert {
            "experiment_id",
            "scenario_id",
            "strategy",
            "load_size",
            "repetition",
            "policy_category",
            "seed",
            "status",
        } <= set(rows[0])
        assert all(row["status"] == "completed" for row in rows)

    effectiveness = _read(
        tmp_path / "effectiveness" / "policy_effectiveness.csv"
    )
    policy_rows = [row for row in effectiveness if row["strategy"] == "policy_driven"]
    assert policy_rows and all(row["ground_truth_match"] == "True" for row in policy_rows)

    dynamic = _read(
        tmp_path / "dynamic-adaptation" / "dynamic_adaptation.csv"
    )
    recovery = [row for row in dynamic if row["new_context"] == "recovery"]
    assert recovery and all(row["stale_policy_count"] == "0" for row in recovery)
    assert all(row["recovery_coherent"] == "True" for row in recovery)

    scalability = _read(
        tmp_path / "scalability" / "policy_scalability.csv"
    )
    assert [int(row["resource_count"]) for row in scalability] == [8, 16]
    assert all(float(row["decision_latency_p95_ms"]) >= 0 for row in scalability)

    cost = _read(
        tmp_path / "computational-cost" / "computational_cost.csv"
    )
    assert {row["strategy"] for row in cost} == {"static", "policy_driven"}
    assert all(row["traffic_measurement"].startswith("estimated_") for row in cost)

    images = plot_policy_evaluation(tmp_path)
    assert len(images) == 4
    assert all(path.suffix == ".png" and path.stat().st_size > 10_000 for path in images)


def test_cost_breakdown_uses_consistent_per_decision_units():
    from continuum_bench.monitoring.policy_evaluation.reporting import _per_decision_cost
    row = {"reasoning_ms": "120", "decision_iterations": "60", "policy_evaluation_ms": "3"}
    assert _per_decision_cost(row, "reasoning_ms") == 2
    assert _per_decision_cost(row, "policy_evaluation_ms") == 3


def test_effectiveness_uncertainty_uses_repetitions_not_scenarios():
    from continuum_bench.monitoring.policy_evaluation.reporting import _repetition_means
    rows = [{"strategy": "static", "repetition": rep, "score": score}
            for rep in ("1", "2") for score in ("0", "1")]
    assert _repetition_means(rows, "static", "score") == [0.5, 0.5]


def test_missing_memory_is_not_reported_as_zero(monkeypatch):
    from continuum_bench.monitoring.policy_evaluation import resources
    monkeypatch.setattr(resources, "memory_measurement_kind", lambda: "unavailable")
    with resources.ResourceSampler() as sampler:
        pass
    result = sampler.measurement()
    assert result.ram_mean_mib is None
    assert result.ram_max_mib is None
    assert result.memory_measurement_kind == "unavailable"
