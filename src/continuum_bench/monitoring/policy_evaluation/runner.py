"""Execution of policy effectiveness, adaptation, scalability and cost studies."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median, pstdev
from time import perf_counter_ns
from typing import Any, Iterable
import json
import math
import platform
import random
import subprocess

from rdflib import Graph, Literal, Namespace, RDF, RDFS

from ...csv_utils import write_dict_rows
from ...ontology import load_graph
from ...reasoners import get_reasoner, reasoner_provenance
from ...specification import EX, release_identity
from .config import (
    PolicyEvaluationConfig,
    PolicyRule,
    ResourceSpec,
    ScalabilityLevel,
    Scenario,
    config_json,
)
from .model import Decision, MonitoringPlan, PolicyEngine, static_decision
from .resources import ResourceSampler


EXPERIMENTS = (
    "effectiveness",
    "dynamic-adaptation",
    "scalability",
    "computational-cost",
)
RESULT_FILES = {
    "effectiveness": "policy_effectiveness.csv",
    "dynamic-adaptation": "dynamic_adaptation.csv",
    "scalability": "policy_scalability.csv",
    "computational-cost": "computational_cost.csv",
}
INTERNAL = Namespace("urn:continuum:policy-evaluation:")


def _common(
    experiment: str,
    scenario_id: str,
    strategy: str,
    load_size: str | int,
    repetition: int,
    category: str,
    seed: int,
) -> dict[str, Any]:
    return {
        "experiment_id": experiment,
        "scenario_id": scenario_id,
        "strategy": strategy,
        "load_size": load_size,
        "repetition": repetition,
        "policy_category": category,
        "seed": seed,
        "status": "completed",
    }


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _truth(scenario: Scenario, rules: tuple[PolicyRule, ...]) -> MonitoringPlan:
    categories = sorted(
        {
            category
            for rule in rules
            if rule.identifier in scenario.expected_policies
            for category in rule.categories
        }
    )
    return MonitoringPlan(
        resources=tuple(sorted(scenario.expected_resources)),
        policies=tuple(sorted(scenario.expected_policies)),
        categories=tuple(categories),
        metrics=tuple(sorted(scenario.expected_metrics)),
        sampling_interval_seconds=scenario.expected_sampling_interval_seconds,
        actions=tuple(sorted(scenario.expected_actions)),
    )


def _items(plan: MonitoringPlan) -> set[str]:
    values = {f"resource:{item}" for item in plan.resources}
    values.update(f"policy:{item}" for item in plan.policies)
    values.update(f"metric:{item}" for item in plan.metrics)
    values.update(f"action:{item}" for item in plan.actions)
    values.add(f"interval:{plan.sampling_interval_seconds:g}")
    return values


def _quality(actual: MonitoringPlan, expected: MonitoringPlan) -> dict[str, Any]:
    actual_items = _items(actual)
    expected_items = _items(expected)
    true_positive = len(actual_items & expected_items)
    false_positive = len(actual_items - expected_items)
    false_negative = len(expected_items - actual_items)
    precision = true_positive / len(actual_items) if actual_items else 1.0
    recall = true_positive / len(expected_items) if expected_items else 1.0
    return {
        "true_positive_plan_items": true_positive,
        "false_positive_plan_items": false_positive,
        "false_negative_plan_items": false_negative,
        "coverage_recall": recall,
        "precision": precision,
        "over_monitoring": false_positive / len(actual_items) if actual_items else 0.0,
        "under_monitoring": false_negative / len(expected_items) if expected_items else 0.0,
        "policies_activated_correctly": len(set(actual.policies) & set(expected.policies)),
        "policy_false_positives": len(set(actual.policies) - set(expected.policies)),
        "policy_false_negatives": len(set(expected.policies) - set(actual.policies)),
        "resources_selected_correctly": len(set(actual.resources) & set(expected.resources)),
        "metrics_selected_correctly": len(set(actual.metrics) & set(expected.metrics)),
        "sampling_interval_correct": math.isclose(
            actual.sampling_interval_seconds,
            expected.sampling_interval_seconds,
            rel_tol=0.0,
            abs_tol=1e-9,
        ),
        "ground_truth_match": actual == expected,
    }


def _validate_policy_identifiers(benchmark_config, config: PolicyEvaluationConfig) -> Graph:
    graph = load_graph(benchmark_config.resolve(path) for path in benchmark_config.ontology_files)
    ontology_ids = {str(value) for value in graph.objects(None, EX.policyIdentifier)}
    configured = {rule.identifier for rule in config.rules}
    missing = sorted(configured - ontology_ids)
    if missing:
        raise ValueError(f"Policy evaluation rules are absent from the ontology: {missing}")
    return graph


def _internal_graph(resources: int, policies: int, categories: int, events: int) -> Graph:
    graph = Graph()
    graph.bind("eval", INTERNAL)
    for class_name in ("Resource", "Policy", "Category", "ContextEvent"):
        graph.add((INTERNAL[class_name], RDFS.subClassOf, INTERNAL.MonitoringEntity))
    for index in range(resources):
        entity = INTERNAL[f"resource-{index:06d}"]
        graph.add((entity, RDF.type, INTERNAL.Resource))
        graph.add((entity, INTERNAL.tier, Literal(index % 4)))
    for index in range(categories):
        graph.add((INTERNAL[f"category-{index:04d}"], RDF.type, INTERNAL.Category))
    for index in range(policies):
        entity = INTERNAL[f"policy-{index:06d}"]
        graph.add((entity, RDF.type, INTERNAL.Policy))
        graph.add((entity, INTERNAL.belongsToCategory, INTERNAL[f"category-{index % categories:04d}"]))
    for index in range(events):
        entity = INTERNAL[f"event-{index:08d}"]
        graph.add((entity, RDF.type, INTERNAL.ContextEvent))
        graph.add((entity, INTERNAL.activatesPolicy, INTERNAL[f"policy-{index % policies:06d}"]))
    return graph


def _reason(graph: Graph, reasoner: str) -> tuple[float, int, int]:
    result = get_reasoner(reasoner).materialize(graph)
    return result.duration_ms, result.input_triples, result.output_triples


def _synthetic_engine(level: ScalabilityLevel) -> PolicyEngine:
    tiers = ("edge", "mist", "fog", "cloud")
    contexts = ("normal", "overload", "failure", "recovery")
    resources = tuple(
        ResourceSpec(f"resource-{index:06d}", tiers[index % len(tiers)])
        for index in range(level.resources)
    )
    rules = tuple(
        PolicyRule(
            identifier=f"synthetic-policy-{index:06d}",
            categories=(f"category-{index % level.categories:04d}",),
            contexts=(contexts[index % len(contexts)],),
            tiers=(tiers[index % len(tiers)],),
            metrics=(f"metric-{index % 8}",),
            actions=(f"action-{index % 6}",),
            sampling_interval_seconds=float((2, 5, 15, 30)[index % 4]),
        )
        for index in range(level.policies)
    )
    return PolicyEngine(resources, rules)


def _percentile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def run_effectiveness(config: PolicyEvaluationConfig) -> list[dict[str, Any]]:
    engine = PolicyEngine(config.resources, config.rules)
    rows: list[dict[str, Any]] = []
    for repetition in range(1, config.repetitions + 1):
        for scenario in config.scenarios:
            expected = _truth(scenario, config.rules)
            for strategy in ("static", "policy_driven"):
                decision = static_decision(config.static_plan) if strategy == "static" else engine.decide(scenario.context)
                rows.append(
                    {
                        **_common("policy-effectiveness", scenario.identifier, strategy, len(config.resources), repetition, scenario.category, config.seed),
                        "context": scenario.context,
                        "policies_evaluated": decision.policies_evaluated,
                        "policies_activated": len(decision.plan.policies),
                        "resources_selected": len(decision.plan.resources),
                        "metrics_selected": len(decision.plan.metrics),
                        "expected_sampling_interval_seconds": expected.sampling_interval_seconds,
                        "actual_sampling_interval_seconds": decision.plan.sampling_interval_seconds,
                        "policy_evaluation_ms": decision.policy_evaluation_ms,
                        "monitoring_plan_generation_ms": decision.plan_generation_ms,
                        **_quality(decision.plan, expected),
                        "monitoring_plan": _json(decision.plan.public()),
                        "ground_truth": _json(expected.public()),
                    }
                )
    return rows


def run_dynamic_adaptation(config: PolicyEvaluationConfig) -> list[dict[str, Any]]:
    engine = PolicyEngine(config.resources, config.rules)
    rows: list[dict[str, Any]] = []
    for repetition in range(1, config.repetitions + 1):
        previous_context = "initial"
        previous_plan = MonitoringPlan((), (), (), (), 0.0, ())
        for transition, scenario in enumerate(config.scenarios):
            detection_started = perf_counter_ns()
            observed_context = scenario.context
            detection_ms = (perf_counter_ns() - detection_started) / 1_000_000
            semantic_graph = _internal_graph(
                len(config.resources), len(config.rules),
                len({category for rule in config.rules for category in rule.categories}),
                transition + 1,
            )
            with ResourceSampler() as sampler:
                reasoning_ms, explicit_triples, closure_triples = _reason(semantic_graph, config.reasoner)
                decision = engine.decide(observed_context)
            resources = sampler.measurement()
            total_adaptation_ms = detection_ms + reasoning_ms + decision.policy_evaluation_ms + decision.plan_generation_ms
            expected = _truth(scenario, config.rules)
            activated = sorted(set(decision.plan.policies) - set(previous_plan.policies))
            deactivated = sorted(set(previous_plan.policies) - set(decision.plan.policies))
            stale = sorted(set(previous_plan.policies) - set(expected.policies) - set(deactivated))
            quality = _quality(decision.plan, expected)
            context_time = transition * config.transition_interval_seconds
            rows.append(
                {
                    **_common("dynamic-adaptation", scenario.identifier, "policy_driven", transition + 1, repetition, scenario.category, config.seed),
                    "transition": transition,
                    "context_timestamp_seconds": context_time,
                    "previous_context": previous_context,
                    "new_context": observed_context,
                    "policies_activated": _json(activated),
                    "policies_deactivated": _json(deactivated),
                    "active_policy_count": len(decision.plan.policies),
                    "active_metric_count": len(decision.plan.metrics),
                    "previous_monitoring_plan": _json(previous_plan.public()),
                    "monitoring_plan": _json(decision.plan.public()),
                    "decision_timestamp_seconds": context_time + total_adaptation_ms / 1000.0,
                    "detection_latency_ms": detection_ms,
                    "reasoning_ms": reasoning_ms,
                    "policy_evaluation_latency_ms": decision.policy_evaluation_ms,
                    "monitoring_plan_generation_latency_ms": decision.plan_generation_ms,
                    "total_adaptation_latency_ms": total_adaptation_ms,
                    "explicit_triples": explicit_triples,
                    "inferred_triples": closure_triples - explicit_triples,
                    "final_graph_triples": closure_triples,
                    "cpu_mean_percent": resources.cpu_mean_percent,
                    "cpu_max_percent": resources.cpu_max_percent,
                    "process_cpu_time_ms": resources.process_cpu_time_ms,
                    "memory_measurement_kind": resources.memory_measurement_kind,
                    "ram_mean_mib": resources.ram_mean_mib,
                    "ram_max_mib": resources.ram_max_mib,
                    "stale_policy_count": len(stale),
                    "recovery_coherent": scenario.context != "recovery" or (not stale and quality["ground_truth_match"]),
                    **quality,
                }
            )
            previous_context = observed_context
            previous_plan = decision.plan
    return rows


def run_scalability(config: PolicyEvaluationConfig) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    contexts = ("normal", "overload", "failure", "recovery")
    for level_index, level in enumerate(config.scalability_levels):
        engine = _synthetic_engine(level)
        for warmup in range(config.warmup):
            for event in range(min(level.events, 20)):
                engine.decide(contexts[(event + warmup) % len(contexts)])
        for repetition in range(1, config.repetitions + 1):
            randomizer = random.Random(config.seed + level_index * 10_000 + repetition)
            event_contexts = [contexts[index % len(contexts)] for index in range(level.events)]
            randomizer.shuffle(event_contexts)
            latencies: list[float] = []
            policy_evaluation_ms = 0.0
            generation_ms = 0.0
            activated_total = 0
            with ResourceSampler() as sampler:
                reasoning_ms, explicit_triples, closure_triples = _reason(
                    _internal_graph(level.resources, level.policies, level.categories, level.events),
                    config.reasoner,
                )
                for context in event_contexts:
                    decision = engine.decide(context)
                    latency = decision.policy_evaluation_ms + decision.plan_generation_ms
                    latencies.append(latency)
                    policy_evaluation_ms += decision.policy_evaluation_ms
                    generation_ms += decision.plan_generation_ms
                    activated_total += len(decision.plan.policies)
            resources = sampler.measurement()
            decision_wall_ms = sum(latencies)
            rows.append(
                {
                    **_common("policy-scalability", level.name, "policy_driven", level_index + 1, repetition, "multiple", config.seed),
                    "resource_count": level.resources,
                    "policy_count": level.policies,
                    "category_count": level.categories,
                    "event_count": level.events,
                    "policies_evaluated": level.policies * level.events,
                    "policies_activated": activated_total,
                    "resources_affected": level.resources,
                    "policy_evaluation_total_ms": policy_evaluation_ms,
                    "decision_latency_mean_ms": mean(latencies),
                    "decision_latency_median_ms": median(latencies),
                    "decision_latency_p95_ms": _percentile(latencies, 0.95),
                    "decision_latency_std_ms": pstdev(latencies) if len(latencies) > 1 else 0.0,
                    "monitoring_plan_generation_ms": generation_ms,
                    "reasoning_ms": reasoning_ms,
                    "total_processing_ms": resources.total_processing_ms,
                    "throughput_decisions_per_second": level.events / max(decision_wall_ms / 1000.0, 1e-12),
                    "end_to_end_throughput_events_per_second": level.events / max(resources.total_processing_ms / 1000.0, 1e-12),
                    "cpu_mean_percent": resources.cpu_mean_percent,
                    "cpu_max_percent": resources.cpu_max_percent,
                    "process_cpu_time_ms": resources.process_cpu_time_ms,
                    "memory_measurement_kind": resources.memory_measurement_kind,
                    "ram_mean_mib": resources.ram_mean_mib,
                    "ram_max_mib": resources.ram_max_mib,
                    "explicit_triples": explicit_triples,
                    "inferred_triples": closure_triples - explicit_triples,
                    "final_graph_triples": closure_triples,
                    "timeout_count": 0,
                    "failure_count": 0,
                }
            )
    return rows


def _observation_cost(
    plan: MonitoringPlan,
    window_seconds: float,
    bytes_per_observation: int,
) -> dict[str, Any]:
    frequency = (
        len(plan.resources) * len(plan.metrics) / plan.sampling_interval_seconds
        if plan.sampling_interval_seconds > 0
        else 0.0
    )
    observations = int(math.ceil(frequency * window_seconds))
    return {
        "metrics_activated": len(plan.metrics),
        "resources_monitored": len(plan.resources),
        "aggregate_sampling_frequency_hz": frequency,
        "observations_generated": observations,
        "event_volume": observations,
        "network_traffic_bytes": observations * bytes_per_observation,
        "traffic_measurement": f"estimated_{bytes_per_observation}_bytes_per_observation",
    }


def run_computational_cost(config: PolicyEvaluationConfig) -> list[dict[str, Any]]:
    engine = PolicyEngine(config.resources, config.rules)
    rows: list[dict[str, Any]] = []
    for repetition in range(1, config.repetitions + 1):
        for scenario in config.scenarios:
            expected = _truth(scenario, config.rules)
            paired: dict[str, dict[str, Any]] = {}
            for strategy in ("static", "policy_driven"):
                with ResourceSampler() as sampler:
                    if strategy == "policy_driven":
                        reasoning_ms, explicit_triples, closure_triples = _reason(
                            _internal_graph(
                                len(config.resources), len(config.rules),
                                len({category for rule in config.rules for category in rule.categories}), 1,
                            ),
                            config.reasoner,
                        )
                        decisions = [
                            engine.decide(scenario.context)
                            for _ in range(config.cost_decisions_per_scenario)
                        ]
                    else:
                        reasoning_ms, explicit_triples, closure_triples = 0.0, 0, 0
                        decisions = [
                            static_decision(config.static_plan)
                            for _ in range(config.cost_decisions_per_scenario)
                        ]
                resources = sampler.measurement()
                decision = decisions[-1]
                policy_evaluation_ms = sum(item.policy_evaluation_ms for item in decisions) / len(decisions)
                plan_generation_ms = sum(item.plan_generation_ms for item in decisions) / len(decisions)
                row = {
                    **_common("computational-cost", scenario.identifier, strategy, len(config.resources), repetition, scenario.category, config.seed),
                    "context": scenario.context,
                    "policies_evaluated": decision.policies_evaluated,
                    "policies_activated": len(decision.plan.policies),
                    "decision_iterations": config.cost_decisions_per_scenario,
                    "decision_time_ms": policy_evaluation_ms + plan_generation_ms,
                    "policy_evaluation_ms": policy_evaluation_ms,
                    "monitoring_plan_generation_ms": plan_generation_ms,
                    "reasoning_ms": reasoning_ms,
                    "materialization_ms": reasoning_ms,
                    "total_processing_ms": resources.total_processing_ms,
                    "cpu_mean_percent": resources.cpu_mean_percent,
                    "cpu_max_percent": resources.cpu_max_percent,
                    "process_cpu_time_ms": resources.process_cpu_time_ms,
                    "cpu_time_per_decision_ms": resources.process_cpu_time_ms / config.cost_decisions_per_scenario,
                    "memory_measurement_kind": resources.memory_measurement_kind,
                    "ram_mean_mib": resources.ram_mean_mib,
                    "ram_max_mib": resources.ram_max_mib,
                    "explicit_triples": explicit_triples,
                    "inferred_triples": closure_triples - explicit_triples,
                    "timeout_count": 0,
                    **_observation_cost(
                        decision.plan,
                        config.observation_window_seconds,
                        config.bytes_per_observation,
                    ),
                    **_quality(decision.plan, expected),
                    "monitoring_plan": _json(decision.plan.public()),
                }
                paired[strategy] = row
                rows.append(row)
            static = paired["static"]
            policy = paired["policy_driven"]
            for row in (static, policy):
                row.update(
                    {
                        "observation_reduction_percent": 100.0 * (static["observations_generated"] - policy["observations_generated"]) / max(static["observations_generated"], 1),
                        "unnecessary_monitoring_reduction": static["over_monitoring"] - policy["over_monitoring"],
                        "coverage_increase": policy["coverage_recall"] - static["coverage_recall"],
                        "cpu_mean_increase_percent_points": policy["cpu_mean_percent"] - static["cpu_mean_percent"],
                        "ram_max_increase_mib": policy["ram_max_mib"] - static["ram_max_mib"],
                        "additional_decision_cost_ms": policy["decision_time_ms"] - static["decision_time_ms"],
                    }
                )
    return rows


RUNNERS = {
    "effectiveness": run_effectiveness,
    "dynamic-adaptation": run_dynamic_adaptation,
    "scalability": run_scalability,
    "computational-cost": run_computational_cost,
}


def _git_commit(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _metadata(root: Path, benchmark_config, config: PolicyEvaluationConfig, selected: tuple[str, ...]) -> dict[str, Any]:
    return {
        **release_identity(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(root),
        "host": platform.node(),
        "platform": platform.platform(),
        "experiments": list(selected),
        "policy_evaluation": config.public(),
        "reasoner": reasoner_provenance(config.reasoner),
        "ontology_role": "identifier_validation_and_separate_reasoning_probe",
        "decision_mechanism": "procedural_context_rule_evaluation",
        "context_source": "configured_synthetic_contexts",
        "quality_contract": "mixed_plan_items_including_policy_identifiers",
        "volume_measurement": "estimated_from_plan_and_configured_window",
        "resource_scope": "current_python_process_excluding_native_reasoner_children",
    }


def run_policy_evaluation(
    benchmark_config,
    config: PolicyEvaluationConfig,
    output_root: Path,
    selected: Iterable[str] = EXPERIMENTS,
) -> dict[str, Any]:
    selected_names = tuple(dict.fromkeys(selected))
    unknown = sorted(set(selected_names) - set(EXPERIMENTS))
    if unknown:
        raise ValueError(f"Unknown policy evaluation experiments: {unknown}")
    _validate_policy_identifiers(benchmark_config, config)
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "configuration.json").write_text(config_json(config) + "\n", encoding="utf-8")
    metadata = _metadata(benchmark_config.root, benchmark_config, config, selected_names)
    (output_root / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    outputs: dict[str, str] = {}
    for name in selected_names:
        rows = RUNNERS[name](config)
        directory = output_root / name
        path = directory / RESULT_FILES[name]
        write_dict_rows(path, rows, empty_message=f"{name} produced no observations")
        outputs[name] = str(path)
    manifest = {"output": str(output_root), "results": outputs, "metadata": str(output_root / "metadata.json")}
    (output_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
