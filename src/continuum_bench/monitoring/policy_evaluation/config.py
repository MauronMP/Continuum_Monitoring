"""Configuration contracts for the four policy-monitoring experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import math
import tomllib


@dataclass(frozen=True)
class ResourceSpec:
    identifier: str
    tier: str


@dataclass(frozen=True)
class PolicyRule:
    identifier: str
    categories: tuple[str, ...]
    contexts: tuple[str, ...]
    tiers: tuple[str, ...]
    metrics: tuple[str, ...]
    actions: tuple[str, ...]
    sampling_interval_seconds: float


@dataclass(frozen=True)
class Scenario:
    identifier: str
    context: str
    category: str
    expected_policies: tuple[str, ...]
    expected_resources: tuple[str, ...]
    expected_metrics: tuple[str, ...]
    expected_actions: tuple[str, ...]
    expected_sampling_interval_seconds: float


@dataclass(frozen=True)
class StaticPlan:
    resources: tuple[str, ...]
    metrics: tuple[str, ...]
    actions: tuple[str, ...]
    sampling_interval_seconds: float


@dataclass(frozen=True)
class ScalabilityLevel:
    name: str
    resources: int
    policies: int
    categories: int
    events: int


@dataclass(frozen=True)
class PolicyEvaluationConfig:
    path: Path
    repetitions: int
    warmup: int
    seed: int
    reasoner: str
    observation_window_seconds: float
    bytes_per_observation: int
    cost_decisions_per_scenario: int
    transition_interval_seconds: float
    resources: tuple[ResourceSpec, ...]
    rules: tuple[PolicyRule, ...]
    scenarios: tuple[Scenario, ...]
    static_plan: StaticPlan
    scalability_levels: tuple[ScalabilityLevel, ...]

    @property
    def fingerprint(self) -> str:
        payload = self.path.read_bytes()
        return hashlib.sha256(payload).hexdigest()

    def public(self) -> dict:
        return {
            "config": str(self.path),
            "config_sha256": self.fingerprint,
            "repetitions": self.repetitions,
            "warmup": self.warmup,
            "seed": self.seed,
            "reasoner": self.reasoner,
            "observation_window_seconds": self.observation_window_seconds,
            "bytes_per_observation": self.bytes_per_observation,
            "cost_decisions_per_scenario": self.cost_decisions_per_scenario,
            "transition_interval_seconds": self.transition_interval_seconds,
            "resources": [resource.__dict__ for resource in self.resources],
            "rules": [rule.__dict__ for rule in self.rules],
            "scenarios": [scenario.__dict__ for scenario in self.scenarios],
            "static_plan": self.static_plan.__dict__,
            "scalability_levels": [level.__dict__ for level in self.scalability_levels],
        }


def _strings(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{field} must be a non-empty list of strings")
    return tuple(value)


def load_policy_evaluation_config(path: str | Path) -> PolicyEvaluationConfig:
    config_path = Path(path).resolve()
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    experiment = raw["experiment"]
    resources = tuple(
        ResourceSpec(str(item["id"]), str(item["tier"]))
        for item in raw["resources"]
    )
    rules = tuple(
        PolicyRule(
            identifier=str(item["id"]),
            categories=_strings(item["categories"], f"rules.{item['id']}.categories"),
            contexts=_strings(item["contexts"], f"rules.{item['id']}.contexts"),
            tiers=_strings(item["tiers"], f"rules.{item['id']}.tiers"),
            metrics=_strings(item["metrics"], f"rules.{item['id']}.metrics"),
            actions=_strings(item["actions"], f"rules.{item['id']}.actions"),
            sampling_interval_seconds=float(item["sampling_interval_seconds"]),
        )
        for item in raw["rules"]
    )
    scenarios = tuple(
        Scenario(
            identifier=str(item["id"]),
            context=str(item["context"]),
            category=str(item["category"]),
            expected_policies=_strings(item["expected_policies"], f"scenarios.{item['id']}.expected_policies"),
            expected_resources=_strings(item["expected_resources"], f"scenarios.{item['id']}.expected_resources"),
            expected_metrics=_strings(item["expected_metrics"], f"scenarios.{item['id']}.expected_metrics"),
            expected_actions=_strings(item["expected_actions"], f"scenarios.{item['id']}.expected_actions"),
            expected_sampling_interval_seconds=float(item["expected_sampling_interval_seconds"]),
        )
        for item in raw["scenarios"]
    )
    static_raw = raw["static_plan"]
    static_plan = StaticPlan(
        resources=_strings(static_raw["resources"], "static_plan.resources"),
        metrics=_strings(static_raw["metrics"], "static_plan.metrics"),
        actions=_strings(static_raw["actions"], "static_plan.actions"),
        sampling_interval_seconds=float(static_raw["sampling_interval_seconds"]),
    )
    levels = tuple(
        ScalabilityLevel(
            name=str(item["name"]),
            resources=int(item["resources"]),
            policies=int(item["policies"]),
            categories=int(item["categories"]),
            events=int(item["events"]),
        )
        for item in raw["scalability"]["levels"]
    )
    config = PolicyEvaluationConfig(
        path=config_path,
        repetitions=int(experiment["repetitions"]),
        warmup=int(experiment["warmup"]),
        seed=int(experiment["seed"]),
        reasoner=str(experiment.get("reasoner", "rdfs")),
        observation_window_seconds=float(experiment["observation_window_seconds"]),
        bytes_per_observation=int(experiment["bytes_per_observation"]),
        cost_decisions_per_scenario=int(experiment["cost_decisions_per_scenario"]),
        transition_interval_seconds=float(experiment["transition_interval_seconds"]),
        resources=resources,
        rules=rules,
        scenarios=scenarios,
        static_plan=static_plan,
        scalability_levels=levels,
    )
    _validate(config)
    return config


def _validate(config: PolicyEvaluationConfig) -> None:
    if config.repetitions < 1 or config.warmup < 0:
        raise ValueError("experiment.repetitions must be positive and warmup non-negative")
    for name, value in (
        ("observation_window_seconds", config.observation_window_seconds),
        ("transition_interval_seconds", config.transition_interval_seconds),
        ("static_plan.sampling_interval_seconds", config.static_plan.sampling_interval_seconds),
    ):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive")
    if config.bytes_per_observation < 1:
        raise ValueError("experiment.bytes_per_observation must be positive")
    if config.cost_decisions_per_scenario < 1:
        raise ValueError("experiment.cost_decisions_per_scenario must be positive")
    resource_ids = [item.identifier for item in config.resources]
    rule_ids = [item.identifier for item in config.rules]
    scenario_ids = [item.identifier for item in config.scenarios]
    for name, values in (("resources", resource_ids), ("rules", rule_ids), ("scenarios", scenario_ids)):
        if not values or len(values) != len(set(values)):
            raise ValueError(f"{name} must be non-empty and uniquely identified")
    known_resources = set(resource_ids)
    known_rules = set(rule_ids)
    known_tiers = {item.tier for item in config.resources}
    if set(config.static_plan.resources) - known_resources:
        raise ValueError("static_plan references unknown resources")
    for rule in config.rules:
        if set(rule.tiers) - known_tiers:
            raise ValueError(f"{rule.identifier} references unknown resource tiers")
        if not math.isfinite(rule.sampling_interval_seconds) or rule.sampling_interval_seconds <= 0:
            raise ValueError(f"{rule.identifier} has an invalid sampling interval")
    required_order = ("normal", "overload", "failure", "recovery")
    if tuple(item.context for item in config.scenarios) != required_order:
        raise ValueError(f"scenarios must follow the controlled sequence {required_order}")
    for scenario in config.scenarios:
        if set(scenario.expected_policies) - known_rules:
            raise ValueError(f"{scenario.identifier} expects unknown policies")
        if set(scenario.expected_resources) - known_resources:
            raise ValueError(f"{scenario.identifier} expects unknown resources")
        if not math.isfinite(scenario.expected_sampling_interval_seconds) or scenario.expected_sampling_interval_seconds <= 0:
            raise ValueError(f"{scenario.identifier} has an invalid expected interval")
    if not config.scalability_levels:
        raise ValueError("scalability.levels cannot be empty")
    previous = (0, 0, 0, 0)
    names: set[str] = set()
    for level in config.scalability_levels:
        values = (level.resources, level.policies, level.categories, level.events)
        if level.name in names or any(value < 1 for value in values):
            raise ValueError("scalability levels need unique names and positive values")
        if any(current <= earlier for current, earlier in zip(values, previous)):
            raise ValueError("every scalability variable must increase at each level")
        names.add(level.name)
        previous = values


def config_json(config: PolicyEvaluationConfig) -> str:
    return json.dumps(config.public(), indent=2, sort_keys=True)
