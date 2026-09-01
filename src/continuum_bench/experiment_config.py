from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class ReasoningProfile:
    name: str
    dimension: str
    users: int
    target_triples: int
    rule_count: int
    padding_mode: str = "neutral"


@dataclass(frozen=True)
class ExperimentConfig:
    repetitions: int
    request_timeout_seconds: float
    seed: int
    query_rounds: int
    warmup_query_rounds: int
    scale_out_users: int
    scale_out_target_triples: int
    scale_out_rule_count: int
    scale_out_node_counts: tuple[int, ...]
    scale_out_padding_mode: str
    reasoning_profiles: tuple[ReasoningProfile, ...]
    distributed_users: tuple[int, ...]


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    config_path = Path(path)
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    settings = raw["experiment"]
    scale_out = raw["scale_out"]
    reasoning = raw["reasoning_hardware"]
    distributed = raw["distributed_ontology"]
    profiles = tuple(
        ReasoningProfile(
            name=str(item["name"]),
            dimension=str(item["dimension"]),
            users=int(item.get("users", 0)),
            target_triples=int(item.get("target_triples", 0)),
            rule_count=int(item.get("rule_count", 0)),
            padding_mode=str(item.get("padding_mode", "neutral")),
        )
        for item in reasoning["profiles"]
    )
    config = ExperimentConfig(
        repetitions=int(settings["repetitions"]),
        request_timeout_seconds=float(settings["request_timeout_seconds"]),
        seed=int(settings["seed"]),
        query_rounds=int(settings["query_rounds"]),
        warmup_query_rounds=int(settings["warmup_query_rounds"]),
        scale_out_users=int(scale_out["users"]),
        scale_out_target_triples=int(scale_out.get("target_triples", 0)),
        scale_out_rule_count=int(scale_out.get("rule_count", 0)),
        scale_out_node_counts=tuple(
            int(value) for value in scale_out["node_counts"]
        ),
        scale_out_padding_mode=str(
            scale_out.get("padding_mode", "neutral")
        ),
        reasoning_profiles=profiles,
        distributed_users=tuple(
            int(value) for value in distributed["users"]
        ),
    )
    _validate(config)
    return config


def select_reasoning_profiles(
    config: ExperimentConfig,
    names: list[str] | None,
) -> ExperimentConfig:
    if not names:
        return config
    selected = tuple(
        profile for profile in config.reasoning_profiles
        if profile.name in set(names)
    )
    missing = sorted(set(names) - {profile.name for profile in selected})
    if missing:
        raise ValueError(f"Unknown reasoning profiles: {missing}")
    return replace(config, reasoning_profiles=selected)


def _validate(config: ExperimentConfig) -> None:
    if config.repetitions < 1:
        raise ValueError("experiment.repetitions must be >= 1")
    if config.request_timeout_seconds <= 1:
        raise ValueError("request_timeout_seconds must be > 1")
    if config.query_rounds < 1 or config.warmup_query_rounds < 1:
        raise ValueError(
            "query rounds and calibration warm-ups must both be >= 1"
        )
    if not config.scale_out_node_counts:
        raise ValueError("scale_out.node_counts cannot be empty")
    if any(value < 1 for value in config.scale_out_node_counts):
        raise ValueError("scale_out.node_counts values must be >= 1")
    if len(config.scale_out_node_counts) != len(
        set(config.scale_out_node_counts)
    ):
        raise ValueError("scale_out.node_counts values must be unique")
    if config.scale_out_node_counts != tuple(
        sorted(config.scale_out_node_counts)
    ):
        raise ValueError("scale_out.node_counts must be strictly increasing")
    if not config.reasoning_profiles:
        raise ValueError("reasoning_hardware.profiles cannot be empty")
    allowed_dimensions = {"target_triples", "rule_count", "users"}
    allowed_padding = {"neutral", "semantic"}
    names = [profile.name for profile in config.reasoning_profiles]
    if len(names) != len(set(names)):
        raise ValueError("Reasoning profile names must be unique")
    for profile in config.reasoning_profiles:
        if profile.dimension not in allowed_dimensions:
            raise ValueError(
                f"{profile.name}: invalid dimension {profile.dimension!r}"
            )
        if min(profile.users, profile.target_triples, profile.rule_count) < 0:
            raise ValueError(f"{profile.name}: values must be non-negative")
        if profile.padding_mode not in allowed_padding:
            raise ValueError(
                f"{profile.name}: padding_mode must be neutral or semantic"
            )
    if any(value < 0 for value in config.distributed_users):
        raise ValueError("distributed_ontology.users must be non-negative")
