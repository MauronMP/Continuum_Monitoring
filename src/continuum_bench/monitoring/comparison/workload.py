"""Deterministic paired workloads and a separately supplied acceptance oracle."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math
import random


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def expand(config, excluded_resources: set[str], multiplier: int) -> dict:
    """Clone logical resources and rules, retaining the configured semantics.

    Expected plans are copied from explicit scenario fixtures, never computed
    by a decision adapter. This is a configured oracle, not external expert
    validation. Expansion is a workload-size experiment, not physical scale-out.
    """
    resources = [asdict(r) for r in config.resources if r.identifier not in excluded_resources]
    if not resources:
        raise ValueError("Exclusions removed every logical resource")
    retained = {r["identifier"] for r in resources}
    def names(values):
        return sorted(f"{name}#{i}" for i in range(multiplier) for name in values if name in retained)
    expanded_resources = [dict(r, identifier=f"{r['identifier']}#{i}") for i in range(multiplier) for r in resources]
    rules = [dict(asdict(r), identifier=f"{r.identifier}#{i}") for i in range(multiplier) for r in config.rules]
    static = asdict(config.static_plan)
    static["resources"] = names(static["resources"])
    scenarios = []
    for scenario in config.scenarios:
        scenarios.append({
            "id": scenario.identifier, "context": scenario.context,
            "expected": {
                "resources": names(scenario.expected_resources),
                "metrics": sorted(scenario.expected_metrics),
                "actions": sorted(scenario.expected_actions),
                "sampling_interval_seconds": scenario.expected_sampling_interval_seconds,
            },
        })
    return {"resources": expanded_resources, "rules": rules, "static_plan": static, "scenarios": scenarios}


def trace(workload: dict, cycles: int, seed: int, ordered: bool) -> list[dict]:
    events = [dict(scenario, event_index=i * len(workload["scenarios"]) + j)
              for i in range(cycles) for j, scenario in enumerate(workload["scenarios"])]
    if not ordered:
        random.Random(seed).shuffle(events)
    for i, event in enumerate(events):
        event["event_index"] = i
    return events


def operational(plan) -> dict:
    """Compare observable plans, not strategy-specific policy metadata."""
    return {"resources": sorted(plan.resources), "metrics": sorted(plan.metrics),
            "actions": sorted(plan.actions), "sampling_interval_seconds": plan.sampling_interval_seconds}


def quality(actual: dict, expected: dict) -> dict:
    actual_pairs = {(r, m) for r in actual["resources"] for m in actual["metrics"]}
    expected_pairs = {(r, m) for r in expected["resources"] for m in expected["metrics"]}
    tp = len(actual_pairs & expected_pairs)
    fp = len(actual_pairs - expected_pairs)
    fn = len(expected_pairs - actual_pairs)
    return {
        "pair_true_positive": tp, "pair_false_positive": fp, "pair_false_negative": fn,
        "coverage": tp / len(expected_pairs) if expected_pairs else 1.0,
        "over_monitoring": fp / len(actual_pairs) if actual_pairs else 0.0,
        "under_monitoring": fn / len(expected_pairs) if expected_pairs else 0.0,
        "actions_correct": actual["actions"] == expected["actions"],
        "interval_correct": math.isclose(actual["sampling_interval_seconds"], expected["sampling_interval_seconds"], abs_tol=1e-9),
        "plan_correct": actual == expected,
    }
