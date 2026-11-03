from __future__ import annotations

import json
import tomllib
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

from ..config import BenchmarkConfig, load_config


@dataclass(frozen=True)
class MonitoringTask:
    task_id: str
    policy_id: str
    query_ids: tuple[str, ...]
    priority: int
    demand_level: str
    interval_seconds: float
    deadline_seconds: float | None


@dataclass(frozen=True)
class MonitoringConfig:
    path: Path
    benchmark: BenchmarkConfig
    scenarios: tuple[str, ...]
    layouts: tuple[str, ...]
    demand_levels: tuple[str, ...]
    stabilization_seconds: float
    measurement_seconds: float
    repetitions: int
    sample_interval_seconds: float
    physical_timeout_seconds: float
    logical_timeout_seconds: float
    include_idle: bool
    tasks: tuple[dict, ...]

    @property
    def digest(self) -> str:
        return sha256(self.path.read_bytes()).hexdigest()

    def resolve_tasks(self, demand_level: str) -> tuple[MonitoringTask, ...]:
        if demand_level not in self.demand_levels:
            raise ValueError(f"unknown demand level: {demand_level}")
        resolved = []
        for item in self.tasks:
            intervals = item["intervals_seconds"]
            if demand_level not in intervals:
                raise ValueError(f"{item['task_id']} has no interval for {demand_level}")
            deadlines = item.get("deadlines_seconds", {})
            resolved.append(
                MonitoringTask(
                    task_id=str(item["task_id"]),
                    policy_id=str(item["policy_id"]),
                    query_ids=tuple(str(value) for value in item["query_ids"]),
                    priority=int(item.get("priority", 0)),
                    demand_level=demand_level,
                    interval_seconds=float(intervals[demand_level]),
                    deadline_seconds=float(deadlines[demand_level]) if demand_level in deadlines else None,
                )
            )
        return tuple(resolved)

    def resolved_digest(self, demand_level: str) -> str:
        payload = json.dumps([asdict(task) for task in self.resolve_tasks(demand_level)], sort_keys=True)
        return sha256(payload.encode()).hexdigest()


def load_monitoring_config(path: Path) -> MonitoringConfig:
    path = path.resolve()
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    experiment = data["monitoring_experiment"]
    benchmark_path = (path.parent / experiment["benchmark_config"]).resolve()
    benchmark = load_config(benchmark_path)
    scenarios = tuple(str(value) for value in experiment["scenarios"])
    known_scenarios = {scenario.name for scenario in benchmark.scenarios}
    if not scenarios or not set(scenarios) <= known_scenarios:
        raise ValueError(f"monitoring scenarios must be selected from {sorted(known_scenarios)}")
    layouts = tuple(str(value) for value in experiment["layouts"])
    if not layouts or not set(layouts) <= {"distributed", "replicated"}:
        raise ValueError("monitoring layouts must contain distributed and/or replicated")
    demand_levels = tuple(str(value) for value in experiment["demand_levels"])
    if not demand_levels or len(set(demand_levels)) != len(demand_levels):
        raise ValueError("demand levels must be non-empty and unique")
    tasks = tuple(data.get("monitoring_task", []))
    if not tasks:
        raise ValueError("at least one monitoring_task is required")
    query_manifest = json.loads((benchmark.root / "queries/manifest.json").read_text())
    query_ids = {item["id"] for item in query_manifest["queries"]}
    ontology_text = "\n".join(path.read_text() for path in (benchmark.root / "ontology").rglob("*.ttl"))
    task_ids = [str(item["task_id"]) for item in tasks]
    if len(set(task_ids)) != len(task_ids):
        raise ValueError("monitoring task identifiers must be unique")
    for task in tasks:
        if not task.get("policy_id") or not task.get("query_ids"):
            raise ValueError(f"{task.get('task_id')} requires policy_id and query_ids")
        if str(task["policy_id"]) not in ontology_text:
            raise ValueError(f"{task['task_id']} references an unknown ontology policy: {task['policy_id']}")
        unknown = set(task["query_ids"]) - query_ids
        if unknown:
            raise ValueError(f"{task['task_id']} references unknown queries: {sorted(unknown)}")
        if set(task["intervals_seconds"]) != set(demand_levels):
            raise ValueError(f"{task['task_id']} must define every configured demand level")
        if any(float(value) <= 0 for value in task["intervals_seconds"].values()):
            raise ValueError(f"{task['task_id']} intervals must be positive")
        deadlines = task.get("deadlines_seconds", {})
        if not set(deadlines) <= set(demand_levels) or any(float(value) <= 0 for value in deadlines.values()):
            raise ValueError(f"{task['task_id']} deadlines must be positive configured demand levels")
    numeric = {
        "stabilization_seconds": float(experiment["stabilization_seconds"]),
        "measurement_seconds": float(experiment["measurement_seconds"]),
        "resource_sample_interval_seconds": float(experiment["resource_sample_interval_seconds"]),
        "physical_query_request_timeout_seconds": float(experiment["physical_query_request_timeout_seconds"]),
        "logical_query_timeout_seconds": float(experiment["logical_query_timeout_seconds"]),
    }
    if any(value <= 0 for value in numeric.values()) or int(experiment["repetitions"]) < 1:
        raise ValueError("monitoring durations, timeouts and repetitions must be positive")
    config = MonitoringConfig(
        path=path,
        benchmark=benchmark,
        scenarios=scenarios,
        layouts=layouts,
        demand_levels=demand_levels,
        stabilization_seconds=numeric["stabilization_seconds"],
        measurement_seconds=numeric["measurement_seconds"],
        repetitions=int(experiment["repetitions"]),
        sample_interval_seconds=numeric["resource_sample_interval_seconds"],
        physical_timeout_seconds=numeric["physical_query_request_timeout_seconds"],
        logical_timeout_seconds=numeric["logical_query_timeout_seconds"],
        include_idle=bool(experiment.get("include_idle", True)),
        tasks=tasks,
    )
    for level in demand_levels:
        config.resolve_tasks(level)
    return config
