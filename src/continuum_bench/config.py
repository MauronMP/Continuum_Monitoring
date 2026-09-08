from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class DistributedConfig:
    """Bound one distributed request and the work performed behind it."""

    request_timeout_seconds: float
    request_retries: int
    query_batch_size: int
    worker_timeout_margin_seconds: float


@dataclass(frozen=True)
class ExecutionLimits:
    """Budgets for bounded benchmarks and right-censored observations."""

    phase_timeout_seconds: float
    point_timeout_seconds: float
    calibration_query_limit: int
    stop_scaling_after_timeout: bool


@dataclass(frozen=True)
class BenchmarkConfig:
    root: Path
    ontology_files: tuple[Path, ...]
    shape_files: tuple[Path, ...]
    query_catalog: Path
    topology_file: Path
    output_dir: Path
    reasoners: tuple[str, ...]
    category_order: tuple[str, ...]
    scale_users: tuple[int, ...]
    repetitions: int
    seed: int
    distributed: DistributedConfig
    limits: ExecutionLimits

    def resolve(self, path: Path) -> Path:
        return path if path.is_absolute() else self.root / path


def load_config(path: str | Path) -> BenchmarkConfig:
    config_path = Path(path).resolve()
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    root = config_path.parents[1]
    paths = raw["paths"]
    benchmark = raw["benchmark"]
    distributed_raw = raw.get("distributed", {})
    limits_raw = raw.get("limits", {})
    distributed = DistributedConfig(
        request_timeout_seconds=float(
            distributed_raw.get("request_timeout_seconds", 60.0)
        ),
        request_retries=int(distributed_raw.get("request_retries", 0)),
        query_batch_size=int(distributed_raw.get("query_batch_size", 8)),
        worker_timeout_margin_seconds=float(
            distributed_raw.get("worker_timeout_margin_seconds", 5.0)
        ),
    )
    if (
        not math.isfinite(distributed.request_timeout_seconds)
        or distributed.request_timeout_seconds <= 1
    ):
        raise ValueError("distributed.request_timeout_seconds must be > 1")
    if distributed.request_retries < 0:
        raise ValueError("distributed.request_retries must be >= 0")
    if distributed.query_batch_size < 1:
        raise ValueError("distributed.query_batch_size must be >= 1")
    if (
        not math.isfinite(distributed.worker_timeout_margin_seconds)
        or distributed.worker_timeout_margin_seconds <= 0
        or distributed.worker_timeout_margin_seconds
        >= distributed.request_timeout_seconds
    ):
        raise ValueError(
            "distributed.worker_timeout_margin_seconds must be positive and "
            "smaller than distributed.request_timeout_seconds"
        )
    limits = ExecutionLimits(
        phase_timeout_seconds=float(
            limits_raw.get(
                "phase_timeout_seconds",
                distributed.request_timeout_seconds,
            )
        ),
        point_timeout_seconds=float(
            limits_raw.get(
                "point_timeout_seconds",
                distributed.request_timeout_seconds,
            )
        ),
        calibration_query_limit=int(
            limits_raw.get("calibration_query_limit", 16)
        ),
        stop_scaling_after_timeout=bool(
            limits_raw.get("stop_scaling_after_timeout", True)
        ),
    )
    for field, value in (
        ("phase_timeout_seconds", limits.phase_timeout_seconds),
        ("point_timeout_seconds", limits.point_timeout_seconds),
    ):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"limits.{field} must be finite and positive")
    if limits.calibration_query_limit < 1:
        raise ValueError("limits.calibration_query_limit must be >= 1")
    config = BenchmarkConfig(
        root=root,
        ontology_files=tuple(Path(value) for value in paths["ontology_files"]),
        shape_files=tuple(Path(value) for value in paths["shape_files"]),
        query_catalog=Path(paths["query_catalog"]),
        topology_file=Path(
            paths.get(
                "topology_file",
                "configs/topologies/physical/topology.toml",
            )
        ),
        output_dir=Path(paths["output_dir"]),
        reasoners=tuple(benchmark["reasoners"]),
        category_order=tuple(benchmark["category_order"]),
        scale_users=tuple(int(value) for value in benchmark["scale_users"]),
        repetitions=int(benchmark["repetitions"]),
        seed=int(benchmark["seed"]),
        distributed=distributed,
        limits=limits,
    )
    _validate_benchmark(config)
    return config


def _validate_benchmark(config: BenchmarkConfig) -> None:
    supported_reasoners = {"rdfs", "owlrl", "rdfs_owlrl"}
    if not config.reasoners:
        raise ValueError("benchmark.reasoners cannot be empty")
    unknown_reasoners = sorted(set(config.reasoners) - supported_reasoners)
    if unknown_reasoners:
        raise ValueError(
            f"benchmark.reasoners contains unsupported values: {unknown_reasoners}"
        )
    if len(config.reasoners) != len(set(config.reasoners)):
        raise ValueError("benchmark.reasoners must not contain duplicates")
    if not config.category_order:
        raise ValueError("benchmark.category_order cannot be empty")
    if len(config.category_order) != len(set(config.category_order)):
        raise ValueError("benchmark.category_order must not contain duplicates")
    if config.repetitions < 1:
        raise ValueError("benchmark.repetitions must be >= 1")
    if not config.scale_users:
        raise ValueError("benchmark.scale_users cannot be empty")
    if any(value < 0 for value in config.scale_users):
        raise ValueError("benchmark.scale_users must be non-negative")
    if tuple(sorted(set(config.scale_users))) != config.scale_users:
        raise ValueError(
            "benchmark.scale_users must be unique and strictly increasing"
        )
