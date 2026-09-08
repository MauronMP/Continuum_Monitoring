"""Validated, deterministic one-factor-at-a-time physical campaign definitions."""
from __future__ import annotations
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
from pathlib import Path
import tomllib

DIMENSIONS = ("physical_nodes", "iot_devices", "users", "requests", "policies",
              "individuals", "requirements", "query_count", "query_complexity", "concurrency")

@dataclass(frozen=True)
class Workload:
    physical_nodes: int = 1
    iot_devices: int = 2
    users: int = 2
    requests: int = 4
    policies: int = 2
    individuals: int = 2
    requirements: int = 2
    query_count: int = 2
    query_complexity: int = 1
    concurrency: int = 1

@dataclass(frozen=True)
class Axis:
    name: str
    values: tuple[int, ...]

@dataclass(frozen=True)
class CampaignConfig:
    path: Path
    name: str
    reasoners: tuple[str, ...]
    modes: tuple[str, ...]
    policy_categories: tuple[str, ...]
    repetitions: int
    warmup: int
    seed: int
    request_timeout_seconds: float
    point_timeout_seconds: float
    baseline: Workload
    axes: tuple[Axis, ...]

    def public(self) -> dict:
        value = asdict(self)
        value.pop("path")
        return value

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(json.dumps(self.public(), sort_keys=True).encode()).hexdigest()

    def points(self):
        for axis in self.axes:
            for value in axis.values:
                yield axis.name, value, replace(self.baseline, **{axis.name: value})


def load_campaign(path: str | Path) -> CampaignConfig:
    path = Path(path).resolve()
    raw = tomllib.loads(path.read_text())
    settings = raw["campaign"]
    baseline = Workload(**raw["workload"])
    axes = tuple(Axis(str(a["name"]), tuple(a["values"])) for a in raw["axes"])
    config = CampaignConfig(
        path, str(settings["name"]), tuple(settings["reasoners"]), tuple(settings["modes"]),
        tuple(settings["policy_categories"]), int(settings["repetitions"]),
        int(settings["warmup"]), int(settings["seed"]),
        float(settings["request_timeout_seconds"]), float(settings["point_timeout_seconds"]),
        baseline, axes,
    )
    if not axes or len({a.name for a in axes}) != len(axes):
        raise ValueError("Campaign axes must be nonempty and unique")
    if config.repetitions < 1 or config.warmup < 0:
        raise ValueError("Repetitions must be positive and warmup nonnegative")
    if not config.reasoners or not config.policy_categories:
        raise ValueError("Reasoners and policy categories must be explicit")
    if not config.modes or set(config.modes) - {"replicated", "distributed", "shared"}:
        raise ValueError("Modes must be replicated, distributed or shared")
    for budget in (config.request_timeout_seconds, config.point_timeout_seconds):
        if not math.isfinite(budget) or budget <= 1:
            raise ValueError("Timeouts must be finite and greater than one second")
    for axis in axes:
        if axis.name not in DIMENSIONS or not axis.values or any(type(v) is not int or v < 1 for v in axis.values):
            raise ValueError(f"Invalid positive integer progression for {axis.name}")
        if any(a >= b for a, b in zip(axis.values, axis.values[1:])):
            raise ValueError(f"{axis.name} values must be strictly increasing")
    for name, value in asdict(baseline).items():
        if type(value) is not int or value < 1:
            raise ValueError(f"workload.{name} must be a positive integer")
    for axis, value, workload in config.points():
        if workload.requests < workload.query_count:
            raise ValueError(f"{axis}={value}: requests must cover every configured query")
        if workload.concurrency > workload.requests:
            raise ValueError(f"{axis}={value}: concurrency cannot exceed request count")
    return config
