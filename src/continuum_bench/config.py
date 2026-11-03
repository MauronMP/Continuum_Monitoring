from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Scenario:
    name: str
    users: int


@dataclass(frozen=True)
class BenchmarkConfig:
    path: Path
    deployment: dict
    experiment: dict
    scenarios: tuple[Scenario, ...]

    @property
    def root(self) -> Path:
        return self.path.parent.parent


def load_config(path: Path) -> BenchmarkConfig:
    path = path.resolve()
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    deployment = data["deployment"]
    experiment = dict(data["experiment"])
    legacy_query_timeout = experiment.get("request_timeout_seconds")
    if "physical_query_request_timeout_seconds" not in experiment:
        if legacy_query_timeout is None:
            raise ValueError("physical_query_request_timeout_seconds is required")
        experiment["physical_query_request_timeout_seconds"] = legacy_query_timeout
    if "logical_query_timeout_seconds" not in experiment:
        experiment["logical_query_timeout_seconds"] = experiment["physical_query_request_timeout_seconds"]
    if "recovery_timeout_seconds" not in experiment:
        experiment["recovery_timeout_seconds"] = deployment["health_timeout_seconds"]
    scenarios = tuple(Scenario(str(item["name"]), int(item["users"])) for item in data["scenarios"])
    if len({item.name for item in scenarios}) != len(scenarios):
        raise ValueError("scenario names must be unique")
    users = [item.users for item in scenarios]
    expected_users = [
        1,
        50,
        100,
        500,
        1000,
        2000,
        4000,
        5000,
        6000,
        7000,
        10000,
        12000,
        14000,
        16000,
        18000,
        20000,
    ]
    if users != expected_users:
        raise ValueError(f"The scientific scenario matrix must be {expected_users}")
    if experiment["layouts"] != ["distributed", "replicated"]:
        raise ValueError("layouts must be distributed and replicated")
    if int(deployment["containers_per_host"]) != 1:
        raise ValueError("the benchmark contract requires one container per host")
    if float(deployment["cpu_per_container"]) <= 0 or int(deployment["memory_mib_per_container"]) <= 0:
        raise ValueError("container CPU and memory limits must be positive")
    if int(deployment["max_prepare_mib"]) <= 0:
        raise ValueError("max_prepare_mib must be positive")
    for key in ("warmup", "repetitions", "query_rounds"):
        if int(experiment[key]) < 1:
            raise ValueError(f"{key} must be positive")
    if float(experiment["prepare_operational_target_seconds"]) >= float(experiment["prepare_hard_timeout_seconds"]):
        raise ValueError("the preparation operational target must be below the hard timeout")
    for key in (
        "physical_query_request_timeout_seconds",
        "logical_query_timeout_seconds",
        "recovery_timeout_seconds",
        "prepare_operational_target_seconds",
        "prepare_hard_timeout_seconds",
        "resource_sample_interval_seconds",
    ):
        if float(experiment[key]) <= 0:
            raise ValueError(f"{key} must be positive")
    for key in ("health_timeout_seconds", "operation_timeout_seconds"):
        if float(deployment[key]) <= 0:
            raise ValueError(f"{key} must be positive")
    for key in ("reserve_memory_mib", "minimum_free_disk_mib"):
        if int(deployment[key]) <= 0:
            raise ValueError(f"{key} must be positive")
    return BenchmarkConfig(path, deployment, experiment, scenarios)
