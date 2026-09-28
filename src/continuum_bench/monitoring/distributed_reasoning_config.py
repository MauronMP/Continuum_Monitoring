"""Configuration for distributed reasoning scalability experiments."""
from __future__ import annotations

from dataclasses import dataclass, replace
import math
from pathlib import Path
import tomllib

from ..reasoners import PHYSICAL_REASONERS, get_reasoner


@dataclass(frozen=True)
class DistributedReasoningConfig:
    path: Path
    repetitions: int
    request_timeout_seconds: float
    point_timeout_seconds: float
    seed: int
    users: int
    rule_count: int
    padding_mode: str
    target_triples: tuple[int, ...]
    node_counts: tuple[int, ...]
    reasoners: tuple[str, ...]
    tasks: tuple[str, ...]
    layouts: tuple[str, ...]
    strong_scaling: bool
    weak_scaling: bool
    weak_triples_per_node: int
    stop_after_timeout: bool
    bootstrap_samples: int
    confidence_level: float
    query_concurrency: tuple[int, ...]
    query_rounds: int
    semantic_validation: bool


REASONING_TASKS = {
    "none": "identity",
    "rdfs": "rdfs_closure",
    "owlrl": "owl_rl_materialization",
    "rdfs_owlrl": "rdfs_owl_rl_materialization",
    "elk": "owl_el_classification_realization",
    "hermit": "owl_dl_classification_realization",
    "openllet": "owl_dl_classification_realization",
    "jfact": "owl_dl_classification_realization",
    "konclude": "owl_dl_classification_realization",
}


def load_distributed_reasoning_config(path: str | Path) -> DistributedReasoningConfig:
    config_path = Path(path).resolve()
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    experiment = raw["experiment"]
    matrix = raw["matrix"]
    scaling = raw["scaling"]
    statistics = raw.get("statistics", {})
    queries = raw.get("queries", {})
    config = DistributedReasoningConfig(
        path=config_path,
        repetitions=int(experiment["repetitions"]),
        request_timeout_seconds=float(experiment["request_timeout_seconds"]),
        point_timeout_seconds=float(experiment["point_timeout_seconds"]),
        seed=int(experiment["seed"]),
        users=int(experiment.get("users", 0)),
        rule_count=int(experiment.get("rule_count", 0)),
        padding_mode=str(experiment.get("padding_mode", "neutral")),
        stop_after_timeout=bool(experiment.get("stop_after_timeout", False)),
        target_triples=tuple(int(value) for value in matrix["target_triples"]),
        node_counts=tuple(int(value) for value in matrix["node_counts"]),
        reasoners=tuple(map(str, matrix["reasoners"])),
        tasks=tuple(map(str, matrix["tasks"])),
        layouts=tuple(map(str, matrix["layouts"])),
        strong_scaling=bool(scaling.get("strong", True)),
        weak_scaling=bool(scaling.get("weak", True)),
        weak_triples_per_node=int(scaling["weak_triples_per_node"]),
        bootstrap_samples=int(statistics.get("bootstrap_samples", 2000)),
        confidence_level=float(statistics.get("confidence_level", 0.95)),
        query_concurrency=tuple(int(value) for value in queries.get("concurrency", [])),
        query_rounds=int(queries.get("rounds", 1)),
        semantic_validation=bool(experiment.get("semantic_validation", True)),
    )
    validate_distributed_reasoning_config(config)
    return config


def validate_distributed_reasoning_config(config: DistributedReasoningConfig) -> None:
    if config.repetitions < 1:
        raise ValueError("experiment.repetitions must be positive")
    if not (math.isfinite(config.request_timeout_seconds) and config.request_timeout_seconds > 1):
        raise ValueError("request_timeout_seconds must be finite and greater than one")
    if not (math.isfinite(config.point_timeout_seconds) and config.point_timeout_seconds >= config.request_timeout_seconds):
        raise ValueError("point_timeout_seconds must be at least request_timeout_seconds")
    if config.padding_mode not in {"neutral", "semantic"}:
        raise ValueError("padding_mode must be neutral or semantic")
    for name, values in (("target_triples", config.target_triples), ("node_counts", config.node_counts)):
        if not values or tuple(sorted(set(values))) != values or min(values) < 1:
            raise ValueError(f"matrix.{name} must be non-empty, unique and increasing")
    if not config.reasoners or not config.layouts or not config.tasks:
        raise ValueError("reasoners, tasks and layouts cannot be empty")
    for reasoner in config.reasoners:
        if reasoner not in PHYSICAL_REASONERS:
            raise ValueError(
                f"matrix.reasoners must use the physical matrix {PHYSICAL_REASONERS}; "
                f"got {reasoner!r}"
            )
        get_reasoner(reasoner)
        if REASONING_TASKS[reasoner] not in config.tasks:
            raise ValueError(f"Task {REASONING_TASKS[reasoner]!r} required by {reasoner!r} is not enabled")
    if set(config.layouts) - {"distributed", "replicated"}:
        raise ValueError("layouts must contain only distributed and replicated")
    if config.weak_triples_per_node < 1:
        raise ValueError("weak_triples_per_node must be positive")
    if config.bootstrap_samples < 100 or not 0 < config.confidence_level < 1:
        raise ValueError("statistics require at least 100 bootstrap samples and confidence in (0,1)")
    if tuple(sorted(set(config.query_concurrency))) != config.query_concurrency or any(value < 1 for value in config.query_concurrency):
        raise ValueError("queries.concurrency must be unique, increasing positive integers")
    if config.query_rounds < 1:
        raise ValueError("queries.rounds must be positive")


def override_distributed_reasoning_config(
    config: DistributedReasoningConfig, *, repetitions: int | None = None,
    timeout_seconds: float | None = None,
    request_timeout_seconds: float | None = None,
    point_timeout_seconds: float | None = None,
    reasoners: list[str] | None = None,
) -> DistributedReasoningConfig:
    updates = {}
    if repetitions is not None:
        updates["repetitions"] = repetitions
    if timeout_seconds is not None:
        updates.update(request_timeout_seconds=timeout_seconds, point_timeout_seconds=timeout_seconds)
    else:
        if request_timeout_seconds is not None:
            updates["request_timeout_seconds"] = request_timeout_seconds
        if point_timeout_seconds is not None:
            updates["point_timeout_seconds"] = point_timeout_seconds
    if reasoners:
        updates["reasoners"] = tuple(reasoners)
    selected = replace(config, **updates)
    validate_distributed_reasoning_config(selected)
    return selected
