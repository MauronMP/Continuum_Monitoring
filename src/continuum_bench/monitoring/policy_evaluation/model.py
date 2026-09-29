"""Domain objects for policy decisions and monitoring plans."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns

from .config import PolicyRule, ResourceSpec, StaticPlan


@dataclass(frozen=True)
class MonitoringPlan:
    resources: tuple[str, ...]
    policies: tuple[str, ...]
    categories: tuple[str, ...]
    metrics: tuple[str, ...]
    sampling_interval_seconds: float
    actions: tuple[str, ...]

    def public(self) -> dict:
        return {
            "resources": list(self.resources),
            "policies": list(self.policies),
            "categories": list(self.categories),
            "metrics": list(self.metrics),
            "sampling_interval_seconds": self.sampling_interval_seconds,
            "actions": list(self.actions),
        }


@dataclass(frozen=True)
class Decision:
    plan: MonitoringPlan
    policies_evaluated: int
    policy_evaluation_ms: float
    plan_generation_ms: float


class PolicyEngine:
    """Evaluate policy conditions, then build a technology-neutral plan."""

    def __init__(self, resources: tuple[ResourceSpec, ...], rules: tuple[PolicyRule, ...]):
        self.resources = resources
        self.rules = rules

    def decide(self, context: str) -> Decision:
        evaluation_started = perf_counter_ns()
        active = tuple(rule for rule in self.rules if context in rule.contexts)
        evaluation_ms = (perf_counter_ns() - evaluation_started) / 1_000_000
        generation_started = perf_counter_ns()
        tiers = {tier for rule in active for tier in rule.tiers}
        plan = MonitoringPlan(
            resources=tuple(sorted(resource.identifier for resource in self.resources if resource.tier in tiers)),
            policies=tuple(sorted(rule.identifier for rule in active)),
            categories=tuple(sorted({category for rule in active for category in rule.categories})),
            metrics=tuple(sorted({metric for rule in active for metric in rule.metrics})),
            sampling_interval_seconds=min((rule.sampling_interval_seconds for rule in active), default=0.0),
            actions=tuple(sorted({action for rule in active for action in rule.actions})),
        )
        generation_ms = (perf_counter_ns() - generation_started) / 1_000_000
        return Decision(plan, len(self.rules), evaluation_ms, generation_ms)


def static_decision(plan: StaticPlan) -> Decision:
    started = perf_counter_ns()
    monitoring_plan = MonitoringPlan(
        resources=tuple(sorted(plan.resources)),
        policies=(),
        categories=(),
        metrics=tuple(sorted(plan.metrics)),
        sampling_interval_seconds=plan.sampling_interval_seconds,
        actions=tuple(sorted(plan.actions)),
    )
    generation_ms = (perf_counter_ns() - started) / 1_000_000
    return Decision(monitoring_plan, 0, 0.0, generation_ms)
