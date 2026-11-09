from __future__ import annotations

import json
import tomllib
import warnings
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from ..config import BenchmarkConfig, load_config
from ..continuous_monitoring.config import MonitoringConfig, load_monitoring_config


@dataclass(frozen=True)
class TriggerThresholds:
    cpu_p95_percent: float
    cpu_mean_percent: float
    cpu_saturation_fraction: float
    logical_latency_p95_ms: float
    monitoring_compliance_min: float
    timeouts: int


@dataclass(frozen=True)
class AdaptationConfig:
    path: Path
    benchmark: BenchmarkConfig
    monitoring: MonitoringConfig
    scenario: str
    layout: str
    demand_level: str
    stabilization_seconds: float
    measurement_seconds: float
    trigger_policy: str
    trigger_task_ids: tuple[str, ...]
    trigger_query_ids: tuple[str, ...]
    adaptation_context_query_id: str
    candidate_query_ids: tuple[str, ...]
    consecutive_trigger_cycles: int
    thresholds: TriggerThresholds
    preferred_action: str
    preferred_target: str
    replica_source: str
    trigger_resource_hosts: tuple[str, ...]
    replica_port: int
    allowed_target_tiers: tuple[str, ...]
    excluded_targets: tuple[str, ...]
    minimum_available_memory_mib: int
    maximum_host_load_per_cpu: float
    require_distinct_from_source: bool
    fallback_to_ranked_candidate: bool
    cpu_per_replica: float
    memory_mib_per_replica: int
    resource_sample_interval_seconds: float
    scalability_query_rounds: int

    @property
    def digest(self) -> str:
        payload = self.path.read_bytes() + self.benchmark.path.read_bytes() + self.monitoring.path.read_bytes()
        return sha256(payload).hexdigest()


def load_adaptation_config(path: Path) -> AdaptationConfig:
    path = path.resolve()
    data = tomllib.loads(path.read_text(encoding="utf-8"))["adaptation_experiment"]
    benchmark = load_config((path.parent / data["benchmark_config"]).resolve())
    demand_level = str(data["demand_level"])
    with warnings.catch_warnings(record=True) as monitoring_warnings:
        warnings.simplefilter("always", UserWarning)
        monitoring = load_monitoring_config((path.parent / data["monitoring_config"]).resolve())
    for warning in monitoring_warnings:
        if f"demand level {demand_level}" in str(warning.message):
            warnings.warn(str(warning.message), UserWarning, stacklevel=2)
    scenario = str(data["scenario"])
    if scenario not in {item.name for item in benchmark.scenarios}:
        raise ValueError(f"unknown adaptation scenario: {scenario}")
    layout = str(data["layout"])
    if layout not in benchmark.experiment["layouts"]:
        raise ValueError(f"unsupported adaptation layout: {layout}")
    if demand_level not in monitoring.demand_levels:
        raise ValueError(f"unknown adaptation demand level: {demand_level}")
    known_tasks = {str(item["task_id"]) for item in monitoring.tasks}
    trigger_tasks = tuple(str(value) for value in data["trigger_task_ids"])
    if not trigger_tasks or not set(trigger_tasks) <= known_tasks:
        raise ValueError("trigger_task_ids must select configured monitoring tasks")
    query_manifest = json.loads((benchmark.root / "queries/manifest.json").read_text())
    known_queries = {str(item["id"]) for item in query_manifest["queries"]}
    query_ids = tuple(str(value) for value in data["trigger_query_ids"])
    candidate_ids = tuple(str(value) for value in data["candidate_query_ids"])
    requested = set(query_ids) | set(candidate_ids) | {str(data["adaptation_context_query_id"])}
    if not requested <= known_queries:
        raise ValueError(f"adaptation configuration references unknown queries: {sorted(requested - known_queries)}")
    task_queries = {
        str(query_id)
        for task in monitoring.tasks
        if str(task["task_id"]) in trigger_tasks
        for query_id in task["query_ids"]
    }
    if not query_ids or not set(query_ids) <= task_queries:
        raise ValueError("trigger_query_ids must be executed by the selected trigger tasks")
    if str(data["trigger_policy"]) not in monitoring.known_policy_ids:
        raise ValueError("trigger_policy is not declared by the ontology")
    thresholds = TriggerThresholds(
        cpu_p95_percent=float(data["cpu_p95_percent"]),
        cpu_mean_percent=float(data["cpu_mean_percent"]),
        cpu_saturation_fraction=float(data["cpu_saturation_fraction"]),
        logical_latency_p95_ms=float(data["logical_latency_p95_ms"]),
        monitoring_compliance_min=float(data["monitoring_compliance_min"]),
        timeouts=int(data["timeouts"]),
    )
    if not 0 <= thresholds.monitoring_compliance_min <= 1:
        raise ValueError("monitoring_compliance_min must be between zero and one")
    if min(thresholds.cpu_p95_percent, thresholds.cpu_mean_percent, thresholds.logical_latency_p95_ms) <= 0:
        raise ValueError("adaptation thresholds must be positive")
    if not 0 < thresholds.cpu_saturation_fraction <= 1 or thresholds.timeouts < 1:
        raise ValueError("CPU saturation fraction and timeout threshold must be positive")
    if int(data["consecutive_trigger_cycles"]) < 1:
        raise ValueError("consecutive_trigger_cycles must be positive")
    if int(data["scalability_query_rounds"]) < 1:
        raise ValueError("scalability_query_rounds must be positive")
    positive = {
        "stabilization_seconds": float(data["stabilization_seconds"]),
        "measurement_seconds": float(data["measurement_seconds"]),
        "resource_sample_interval_seconds": float(data["resource_sample_interval_seconds"]),
        "cpu_per_replica": float(data["cpu_per_replica"]),
    }
    if any(value <= 0 for value in positive.values()):
        raise ValueError("adaptation durations and replica limits must be positive")
    replica_port = int(data["replica_port"])
    if not 1 <= replica_port <= 65535:
        raise ValueError("replica_port must be between 1 and 65535")
    if str(data["preferred_action"]) != "deploy_read_only_replica":
        raise ValueError("the controlled demonstration supports only deploy_read_only_replica")
    trigger_resource_hosts = tuple(str(value) for value in data["trigger_resource_hosts"])
    if not trigger_resource_hosts:
        raise ValueError("trigger_resource_hosts must contain at least one physical worker")
    allowed_tiers = tuple(str(value) for value in data["allowed_target_tiers"])
    if not allowed_tiers or not set(allowed_tiers) <= {"cloud", "fog", "mist", "edge"}:
        raise ValueError("allowed_target_tiers contains an unsupported tier")
    if (
        int(data["minimum_available_memory_mib"]) <= 0
        or int(data["memory_mib_per_replica"]) <= 0
        or float(data["maximum_host_load_per_cpu"]) <= 0
    ):
        raise ValueError("replica capacity thresholds and memory limits must be positive")
    return AdaptationConfig(
        path=path,
        benchmark=benchmark,
        monitoring=monitoring,
        scenario=scenario,
        layout=layout,
        demand_level=demand_level,
        stabilization_seconds=positive["stabilization_seconds"],
        measurement_seconds=positive["measurement_seconds"],
        trigger_policy=str(data["trigger_policy"]),
        trigger_task_ids=trigger_tasks,
        trigger_query_ids=query_ids,
        adaptation_context_query_id=str(data["adaptation_context_query_id"]),
        candidate_query_ids=candidate_ids,
        consecutive_trigger_cycles=int(data["consecutive_trigger_cycles"]),
        thresholds=thresholds,
        preferred_action=str(data["preferred_action"]),
        preferred_target=str(data["preferred_target"]),
        replica_source=str(data["replica_source"]),
        trigger_resource_hosts=trigger_resource_hosts,
        replica_port=replica_port,
        allowed_target_tiers=allowed_tiers,
        excluded_targets=tuple(str(value) for value in data.get("excluded_targets", [])),
        minimum_available_memory_mib=int(data["minimum_available_memory_mib"]),
        maximum_host_load_per_cpu=float(data["maximum_host_load_per_cpu"]),
        require_distinct_from_source=bool(data["require_distinct_from_source"]),
        fallback_to_ranked_candidate=bool(data["fallback_to_ranked_candidate"]),
        cpu_per_replica=positive["cpu_per_replica"],
        memory_mib_per_replica=int(data["memory_mib_per_replica"]),
        resource_sample_interval_seconds=positive["resource_sample_interval_seconds"],
        scalability_query_rounds=int(data["scalability_query_rounds"]),
    )
