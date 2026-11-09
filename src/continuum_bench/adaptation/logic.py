from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from math import ceil

from ..query_execution import select_hosts
from ..topology import Host
from .config import AdaptationConfig


def percentile(values: list[float], percentile_value: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile_value
    lower = int(position)
    upper = min(len(ordered) - 1, ceil(position))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def evaluate_trigger(config: AdaptationConfig, scheduler: dict, resources: list[dict]) -> dict:
    events = [
        event
        for event in scheduler.get("events", [])
        if event.get("task_id") in config.trigger_task_ids and event.get("actual_end_utc")
    ]
    events.sort(key=lambda item: str(item["actual_end_utc"]))
    candidate_samples = [
        row
        for row in resources
        if row.get("timestamp")
        and row.get("cpu_percent") is not None
        and row.get("host") in config.trigger_resource_hosts
    ]
    per_host_resource_metrics = {}
    for host in config.trigger_resource_hosts:
        values = [float(row["cpu_percent"]) for row in candidate_samples if row.get("host") == host]
        per_host_resource_metrics[host] = {
            "cpu_mean_percent": sum(values) / len(values) if values else None,
            "cpu_p95_percent": percentile(values, 0.95),
            "cpu_peak_percent": max(values) if values else None,
            "cpu_saturation_fraction": (
                sum(value >= config.thresholds.cpu_p95_percent for value in values) / len(values) if values else None
            ),
            "resource_sample_count": len(values),
        }
    observed_hosts = [
        host for host in config.trigger_resource_hosts if per_host_resource_metrics[host]["resource_sample_count"]
    ]
    selected_source = (
        max(
            observed_hosts,
            key=lambda host: (
                bool(
                    float(per_host_resource_metrics[host]["cpu_p95_percent"] or 0) >= config.thresholds.cpu_p95_percent
                    and (
                        float(per_host_resource_metrics[host]["cpu_mean_percent"] or 0)
                        >= config.thresholds.cpu_mean_percent
                        or float(per_host_resource_metrics[host]["cpu_saturation_fraction"] or 0)
                        >= config.thresholds.cpu_saturation_fraction
                    )
                ),
                float(per_host_resource_metrics[host]["cpu_saturation_fraction"] or 0),
                float(per_host_resource_metrics[host]["cpu_mean_percent"] or 0),
                float(per_host_resource_metrics[host]["cpu_p95_percent"] or 0),
                host,
            ),
        )
        if observed_hosts
        else config.replica_source
    )
    samples = [row for row in candidate_samples if row.get("host") == selected_source]
    samples.sort(key=lambda item: str(item["timestamp"]))
    latencies = [
        (float(event["actual_end_monotonic"]) - float(event["actual_start_monotonic"])) * 1000 for event in events
    ]
    cpu_values = [float(row["cpu_percent"]) for row in samples]
    cpu_peak = max(cpu_values, default=0.0)
    cpu_mean = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
    cpu_p95 = percentile(cpu_values, 0.95) or 0.0
    saturation_fraction = (
        sum(value >= config.thresholds.cpu_p95_percent for value in cpu_values) / len(cpu_values) if cpu_values else 0.0
    )
    latency_p95 = percentile(latencies, 0.95) or 0.0
    compliance = float(scheduler.get("monitoring_compliance") or 0.0)
    timeouts = int(scheduler.get("logical_timeouts", 0))
    aggregate_conditions = {
        "cpu_sustained_pressure_threshold": cpu_p95 >= config.thresholds.cpu_p95_percent
        and (
            cpu_mean >= config.thresholds.cpu_mean_percent
            or saturation_fraction >= config.thresholds.cpu_saturation_fraction
        ),
        "logical_latency_p95_threshold": latency_p95 >= config.thresholds.logical_latency_p95_ms,
        "monitoring_compliance_threshold": compliance < config.thresholds.monitoring_compliance_min,
        "timeout_threshold": timeouts >= config.thresholds.timeouts,
    }
    observations = []
    previous_end: datetime | None = None
    for event, latency in zip(events, latencies, strict=True):
        end = datetime.fromisoformat(str(event["actual_end_utc"]))
        window = [
            row
            for row in samples
            if (previous_end is None or datetime.fromisoformat(str(row["timestamp"])) > previous_end)
            and datetime.fromisoformat(str(row["timestamp"])) <= end
        ]
        if not window:
            prior = [row for row in samples if datetime.fromisoformat(str(row["timestamp"])) <= end]
            window = prior[-1:]
        cycle_cpu = [float(row["cpu_percent"]) for row in window]
        cycle_cpu_peak = max(cycle_cpu, default=0.0)
        cycle_cpu_mean = sum(cycle_cpu) / len(cycle_cpu) if cycle_cpu else 0.0
        cycle_cpu_p95 = percentile(cycle_cpu, 0.95) or 0.0
        cycle_saturation_fraction = (
            sum(value >= config.thresholds.cpu_p95_percent for value in cycle_cpu) / len(cycle_cpu)
            if cycle_cpu
            else 0.0
        )
        resource_pressure = cycle_cpu_p95 >= config.thresholds.cpu_p95_percent and (
            cycle_cpu_mean >= config.thresholds.cpu_mean_percent
            or cycle_saturation_fraction >= config.thresholds.cpu_saturation_fraction
        )
        conditions = {
            "resource_pressure": resource_pressure,
            "latency_degradation": latency >= config.thresholds.logical_latency_p95_ms,
            "timeout": event.get("execution_status") == "logical_timeout",
            "compliance_degradation": not bool(event.get("monitoring_compliant")),
            "semantic_saturation": event.get("observation_outcome")
            in {"boolean_true", "unexpected_boolean_observed", "condition_detected"},
        }
        observations.append(
            {
                "task_id": event["task_id"],
                "scheduled_at_utc": event["scheduled_at_utc"],
                "logical_latency_ms": latency,
                "cpu_peak_percent": cycle_cpu_peak,
                "cpu_mean_percent": cycle_cpu_mean,
                "cpu_p95_percent": cycle_cpu_p95,
                "cpu_saturation_fraction": cycle_saturation_fraction,
                "resource_sample_count": len(cycle_cpu),
                "monitoring_compliant": bool(event.get("monitoring_compliant")),
                "observation_outcome": event.get("observation_outcome"),
                "conditions": conditions,
                "condition_holds": any(conditions.values()),
            }
        )
        previous_end = end
    consecutive = maximum_consecutive([bool(item["condition_holds"]) for item in observations])
    aggregate_degradation = any(aggregate_conditions.values())
    sustained_resource_samples = (
        aggregate_conditions["cpu_sustained_pressure_threshold"]
        and len(cpu_values) >= config.consecutive_trigger_cycles
        and saturation_fraction >= config.thresholds.cpu_saturation_fraction
    )
    consecutive_cycle_degradation = aggregate_degradation and consecutive >= config.consecutive_trigger_cycles
    triggered = sustained_resource_samples or consecutive_cycle_degradation
    return {
        "stage": "monitor_trigger",
        "mode": "measured_threshold_evaluation",
        "triggered": triggered,
        "trigger_policy": config.trigger_policy,
        "trigger_query_ids": list(config.trigger_query_ids),
        "trigger_resource_host": selected_source,
        "configured_trigger_resource_hosts": list(config.trigger_resource_hosts),
        "per_host_resource_metrics": per_host_resource_metrics,
        "experimental_thresholds": asdict(config.thresholds),
        "required_consecutive_cycles": config.consecutive_trigger_cycles,
        "maximum_consecutive_degraded_cycles": consecutive,
        "sustained_resource_samples": sustained_resource_samples,
        "consecutive_cycle_degradation": consecutive_cycle_degradation,
        "persistence_basis": (
            "resource_sample_series"
            if sustained_resource_samples
            else "consecutive_monitoring_cycles"
            if consecutive_cycle_degradation
            else "not_satisfied"
        ),
        "aggregate_conditions": aggregate_conditions,
        "metrics": {
            "cpu_peak_percent": cpu_peak,
            "cpu_mean_percent": cpu_mean,
            "cpu_p95_percent": cpu_p95,
            "cpu_saturation_fraction": saturation_fraction,
            "resource_sample_count": len(cpu_values),
            "logical_latency_p95_ms": latency_p95,
            "monitoring_compliance": compliance,
            "logical_timeouts": timeouts,
        },
        "observations": observations,
        "reason": "persistent_observed_degradation" if triggered else "trigger_not_satisfied",
    }


def maximum_consecutive(values: list[bool]) -> int:
    maximum = current = 0
    for value in values:
        current = current + 1 if value else 0
        maximum = max(maximum, current)
    return maximum


def analyze_trigger(trigger: dict, timestamp: str) -> dict:
    triggered = bool(trigger.get("triggered"))
    return {
        "stage": "analyze",
        "mode": "simulated_rule_based",
        "timestamp": timestamp,
        "trigger_policy": trigger.get("trigger_policy"),
        "replica_source": trigger.get("trigger_resource_host"),
        "trigger_observations": trigger.get("observations", []),
        "thresholds": trigger.get("experimental_thresholds", {}),
        "conclusion": "additional_capacity_required" if triggered else "no_adaptation_required",
        "status": "completed" if triggered else "no_action",
    }


def plan_adaptation(config: AdaptationConfig, analysis: dict, candidates: list[dict], timestamp: str) -> dict:
    replica_source = str(analysis.get("replica_source") or config.replica_source)
    if analysis.get("conclusion") != "additional_capacity_required":
        return {
            "stage": "plan",
            "mode": "simulated_rule_based",
            "timestamp": timestamp,
            "status": "no_action",
            "action": None,
            "target": None,
            "selected_target": None,
            "eligible_candidates": [],
            "rejected_candidates": {},
            "reason": "analysis_did_not_require_capacity",
        }
    eligible: list[dict] = []
    rejected: dict[str, list[str]] = {}
    for candidate in candidates:
        reasons = []
        if not candidate.get("connected") or not candidate.get("worker_ready"):
            reasons.append("availability_or_connectivity")
        if not candidate.get("worker_idle"):
            reasons.append("worker_not_idle")
        if candidate.get("tier") not in config.allowed_target_tiers or candidate.get("id") in config.excluded_targets:
            reasons.append("governance_constraint")
        if int(candidate.get("available_memory_mib", 0)) < config.minimum_available_memory_mib:
            reasons.append("insufficient_residual_memory")
        cpu_count = int(candidate.get("cpu_count", 0))
        if cpu_count <= 0 or float(candidate.get("load_1m", cpu_count)) / cpu_count > config.maximum_host_load_per_cpu:
            reasons.append("insufficient_cpu_capacity")
        if not candidate.get("replica_port_available"):
            reasons.append("replica_port_unavailable")
        if not candidate.get("worker_image_available", True):
            reasons.append("worker_image_unavailable")
        observed_p95 = candidate.get("workload_cpu_p95_percent")
        observed_mean = candidate.get("workload_cpu_mean_percent")
        if (
            isinstance(observed_p95, (int, float))
            and isinstance(observed_mean, (int, float))
            and observed_p95 >= config.thresholds.cpu_p95_percent
            and observed_mean >= config.thresholds.cpu_mean_percent
        ):
            reasons.append("saturated_during_observed_workload")
        if config.require_distinct_from_source and candidate.get("id") == replica_source:
            reasons.append("same_as_replica_source")
        if reasons:
            rejected[str(candidate["id"])] = reasons
        else:
            eligible.append(candidate)
    eligible.sort(key=lambda item: (-int(item.get("available_memory_mib", 0)), str(item["id"])))
    eligible_ids = [str(item["id"]) for item in eligible]
    target = config.preferred_target if config.preferred_target in eligible_ids else None
    selection_rule = "eligible_preferred_target"
    if target is None and config.fallback_to_ranked_candidate and eligible_ids:
        target = eligible_ids[0]
        selection_rule = "deterministic_residual_memory_then_id"
    status = "planned" if target else "planning_failed"
    return {
        "stage": "plan",
        "mode": "simulated_rule_based",
        "timestamp": timestamp,
        "status": status,
        "action": config.preferred_action if target else None,
        "target": target,
        "selected_target": target,
        "replica_source": replica_source,
        "eligible_candidates": eligible_ids,
        "rejected_candidates": rejected,
        "candidate_evidence": candidates,
        "governance_policy_ids": ["P-NODE-02", "P-NODE-05"],
        "selection_rule": selection_rule if target else None,
        "reason": "additional_capacity_required" if target else "no_eligible_candidate",
    }


class ReplicaRouter:
    """Replace one partition participant with an equivalent read-only replica in deterministic alternation."""

    def __init__(self, hosts: tuple[Host, ...], source_id: str, replica: Host):
        self.hosts = hosts
        self.source_id = source_id
        self.replica = replica
        self._source_selections = 0

    def select(self, query: dict, round_: int, query_index: int, layout: str) -> tuple[Host, ...]:
        baseline = select_hosts(self.hosts, query, round_, query_index, layout)
        if not any(host.id == self.source_id for host in baseline):
            return baseline
        use_replica = self._source_selections % 2 == 1
        self._source_selections += 1
        if not use_replica:
            return baseline
        return tuple(self.replica if host.id == self.source_id else host for host in baseline)
