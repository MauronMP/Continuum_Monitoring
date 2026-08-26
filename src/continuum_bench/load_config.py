"""Configuration model for the multidimensional event-load benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class LoadProfile:
    name: str
    dimension: str
    events_per_second: float
    duration_seconds: float
    users: int
    target_triples: int
    rule_count: int
    node_count: int

    @property
    def offered_events(self) -> int:
        return max(1, round(self.events_per_second * self.duration_seconds))


@dataclass(frozen=True)
class LoadBenchmarkConfig:
    path: Path
    profiles: tuple[LoadProfile, ...]
    repetitions: int
    batch_size: int
    queue_capacity_events: int
    request_timeout_seconds: float
    point_timeout_seconds: float
    recovery_timeout_seconds: float
    seed: int


_DIMENSIONS = {
    "events_per_second",
    "users",
    "target_triples",
    "rule_count",
    "node_count",
}


def load_load_config(path: str | Path) -> LoadBenchmarkConfig:
    config_path = Path(path).resolve()
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    settings = raw["load"]
    profiles = tuple(
        LoadProfile(
            name=str(item["name"]),
            dimension=str(item["dimension"]),
            events_per_second=float(item["events_per_second"]),
            duration_seconds=float(
                item.get("duration_seconds", settings["duration_seconds"])
            ),
            users=int(item["users"]),
            target_triples=int(item.get("target_triples", 0)),
            rule_count=int(item["rule_count"]),
            node_count=int(item["node_count"]),
        )
        for item in raw.get("profiles", [])
    )
    if not profiles:
        raise ValueError(f"Load config contains no [[profiles]]: {config_path}")
    names = [profile.name for profile in profiles]
    if len(names) != len(set(names)):
        raise ValueError("Load profile names must be unique")
    for profile in profiles:
        if profile.dimension not in _DIMENSIONS:
            raise ValueError(
                f"{profile.name}: unknown dimension {profile.dimension!r}"
            )
        if profile.events_per_second <= 0 or profile.duration_seconds <= 0:
            raise ValueError(f"{profile.name}: event rate/duration must be > 0")
        if profile.users < 0 or profile.rule_count < 0:
            raise ValueError(f"{profile.name}: users/rules must be >= 0")
        if profile.target_triples < 0:
            raise ValueError(
                f"{profile.name}: target_triples must be >= 0"
            )
        if not 1 <= profile.node_count <= 5:
            raise ValueError(f"{profile.name}: node_count must be in [1, 5]")
    config = LoadBenchmarkConfig(
        path=config_path,
        profiles=profiles,
        repetitions=int(settings["repetitions"]),
        batch_size=int(settings["batch_size"]),
        queue_capacity_events=int(settings["queue_capacity_events"]),
        request_timeout_seconds=float(settings["request_timeout_seconds"]),
        point_timeout_seconds=float(settings["point_timeout_seconds"]),
        recovery_timeout_seconds=float(
            settings["recovery_timeout_seconds"]
        ),
        seed=int(settings.get("seed", 2026)),
    )
    if config.repetitions < 1:
        raise ValueError("load.repetitions must be >= 1")
    if config.batch_size < 1 or config.queue_capacity_events < 1:
        raise ValueError("batch_size and queue_capacity_events must be >= 1")
    if config.batch_size > config.queue_capacity_events:
        raise ValueError("batch_size cannot exceed queue_capacity_events")
    if min(
        config.request_timeout_seconds,
        config.point_timeout_seconds,
        config.recovery_timeout_seconds,
    ) <= 0:
        raise ValueError("All load timeouts must be > 0")
    return config


def select_load_profiles(
    config: LoadBenchmarkConfig,
    *,
    dimensions: list[str] | None = None,
    names: list[str] | None = None,
) -> LoadBenchmarkConfig:
    """Return a validated subset without changing experimental parameters."""

    known_names = {profile.name for profile in config.profiles}
    unknown = sorted(set(names or ()) - known_names)
    if unknown:
        raise ValueError(f"Unknown load profile names: {unknown}")
    selected = tuple(
        profile
        for profile in config.profiles
        if (not dimensions or profile.dimension in dimensions)
        and (not names or profile.name in names)
    )
    if not selected:
        raise ValueError(
            "No load profiles match the requested --dimension/--profile"
        )
    return LoadBenchmarkConfig(
        path=config.path,
        profiles=selected,
        repetitions=config.repetitions,
        batch_size=config.batch_size,
        queue_capacity_events=config.queue_capacity_events,
        request_timeout_seconds=config.request_timeout_seconds,
        point_timeout_seconds=config.point_timeout_seconds,
        recovery_timeout_seconds=config.recovery_timeout_seconds,
        seed=config.seed,
    )
