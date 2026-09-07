from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class WorkloadModel:
    arrival_model: str
    execution_mode: str
    concurrency: int
    trace_path: str
    request_rate_per_second: float
    category_distribution: str
    zipf_exponent: float
    hotspot_fraction: float
    hotspot_share: float
    burst_probability: float
    burst_size: int
    ramp_start_rate_per_second: float
    ramp_end_rate_per_second: float
    category_weights: dict[str, float]


@dataclass(frozen=True)
class MobilityModel:
    model: str
    seed: int
    area_width_m: float
    area_height_m: float
    min_speed_mps: float
    max_speed_mps: float
    pause_seconds: float
    step_seconds: float
    boundary: str
    grid_spacing_m: float
    turn_probability: float
    gauss_markov_alpha: float
    mean_speed_mps: float
    mean_direction_degrees: float


@dataclass(frozen=True)
class NetworkModel:
    model: str
    base_latency_ms: float
    latency_per_meter_ms: float
    base_bandwidth_mbps: float
    bandwidth_decay_per_meter: float
    packet_loss_per_meter: float
    jitter_ms: float


@dataclass(frozen=True)
class PlacementModel:
    strategy: str


@dataclass(frozen=True)
class SchedulerModel:
    strategy: str


@dataclass(frozen=True)
class PolicyCostStudyConfig:
    path: Path
    experiment_id: str
    seed: int
    duration_seconds: float
    request_count: int
    client_count: int
    warmup_seconds: float
    workload: WorkloadModel
    mobility: MobilityModel
    network: NetworkModel
    placement: PlacementModel
    scheduler: SchedulerModel


def load_study_config(path: str | Path) -> PolicyCostStudyConfig:
    config_path = Path(path).resolve()
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    study = raw["study"]
    workload = raw["workload"]
    mobility = raw["mobility"]
    network = raw["network"]
    config = PolicyCostStudyConfig(
        path=config_path,
        experiment_id=str(study["experiment_id"]),
        seed=int(study["seed"]),
        duration_seconds=float(study["duration_seconds"]),
        request_count=int(study["request_count"]),
        client_count=int(study["client_count"]),
        warmup_seconds=float(study.get("warmup_seconds", 0.0)),
        workload=WorkloadModel(
            arrival_model=str(workload["arrival_model"]),
            execution_mode=str(workload.get("execution_mode", "open_loop")),
            concurrency=int(workload.get("concurrency", 1)),
            trace_path=str(workload.get("trace_path", "")),
            request_rate_per_second=float(workload["request_rate_per_second"]),
            category_distribution=str(workload["category_distribution"]),
            zipf_exponent=float(workload.get("zipf_exponent", 1.1)),
            hotspot_fraction=float(workload.get("hotspot_fraction", 0.2)),
            hotspot_share=float(workload.get("hotspot_share", 0.8)),
            burst_probability=float(workload.get("burst_probability", 0.0)),
            burst_size=int(workload.get("burst_size", 1)),
            ramp_start_rate_per_second=float(
                workload.get("ramp_start_rate_per_second", 1.0)
            ),
            ramp_end_rate_per_second=float(
                workload.get("ramp_end_rate_per_second", 1.0)
            ),
            category_weights={
                str(key): float(value)
                for key, value in workload.get("category_weights", {}).items()
            },
        ),
        mobility=MobilityModel(
            model=str(mobility["model"]),
            seed=int(mobility.get("seed", study["seed"])),
            area_width_m=float(mobility["area_width_m"]),
            area_height_m=float(mobility["area_height_m"]),
            min_speed_mps=float(mobility.get("min_speed_mps", 0.0)),
            max_speed_mps=float(mobility.get("max_speed_mps", 0.0)),
            pause_seconds=float(mobility.get("pause_seconds", 0.0)),
            step_seconds=float(mobility.get("step_seconds", 1.0)),
            boundary=str(mobility.get("boundary", "reflect")),
            grid_spacing_m=float(mobility.get("grid_spacing_m", 10.0)),
            turn_probability=float(mobility.get("turn_probability", 0.25)),
            gauss_markov_alpha=float(mobility.get("gauss_markov_alpha", 0.75)),
            mean_speed_mps=float(mobility.get("mean_speed_mps", 1.0)),
            mean_direction_degrees=float(
                mobility.get("mean_direction_degrees", 0.0)
            ),
        ),
        network=NetworkModel(
            model=str(network["model"]),
            base_latency_ms=float(network["base_latency_ms"]),
            latency_per_meter_ms=float(network["latency_per_meter_ms"]),
            base_bandwidth_mbps=float(network["base_bandwidth_mbps"]),
            bandwidth_decay_per_meter=float(
                network["bandwidth_decay_per_meter"]
            ),
            packet_loss_per_meter=float(network["packet_loss_per_meter"]),
            jitter_ms=float(network.get("jitter_ms", 0.0)),
        ),
        placement=PlacementModel(
            strategy=str(raw.get("placement", {}).get("strategy", "replicated"))
        ),
        scheduler=SchedulerModel(
            strategy=str(raw.get("scheduler", {}).get("strategy", "round_robin"))
        ),
    )
    _validate(config)
    return config


def _validate(config: PolicyCostStudyConfig) -> None:
    if config.request_count < 1:
        raise ValueError("study.request_count must be >= 1")
    if config.client_count < 1:
        raise ValueError("study.client_count must be >= 1")
    if config.duration_seconds <= 0:
        raise ValueError("study.duration_seconds must be > 0")
    if config.workload.arrival_model not in {
        "uniform",
        "poisson",
        "bursty",
        "ramp",
        "trace",
    }:
        raise ValueError("Unsupported workload arrival model")
    if config.workload.execution_mode not in {"open_loop", "closed_loop"}:
        raise ValueError("workload.execution_mode must be open_loop or closed_loop")
    if config.workload.concurrency < 1:
        raise ValueError("workload.concurrency must be >= 1")
    if config.workload.category_distribution not in {
        "uniform",
        "weighted",
        "zipf",
        "hotspot",
        "dynamic_hotspot",
    }:
        raise ValueError("Unsupported category distribution")
    if config.workload.request_rate_per_second <= 0:
        raise ValueError("workload.request_rate_per_second must be positive")
    if config.workload.arrival_model == "trace" and not config.workload.trace_path:
        raise ValueError("workload.trace_path is required for trace arrivals")
    if config.mobility.model not in {
        "static",
        "constant_velocity",
        "random_waypoint",
        "random_walk",
        "manhattan_grid",
        "gauss_markov",
    }:
        raise ValueError("Unsupported mobility model")
    if config.mobility.boundary not in {"reflect", "wrap"}:
        raise ValueError("mobility.boundary must be reflect or wrap")
    if config.mobility.area_width_m <= 0 or config.mobility.area_height_m <= 0:
        raise ValueError("mobility simulation bounds must be positive")
    if config.mobility.min_speed_mps < 0:
        raise ValueError("mobility.min_speed_mps must be non-negative")
    if config.mobility.max_speed_mps < config.mobility.min_speed_mps:
        raise ValueError("mobility.max_speed_mps must be >= min_speed_mps")
    if (
        config.mobility.model != "static"
        and config.mobility.max_speed_mps <= 0
    ):
        raise ValueError("non-static mobility requires a positive maximum speed")
    if not 0 <= config.mobility.gauss_markov_alpha <= 1:
        raise ValueError("mobility.gauss_markov_alpha must be in [0, 1]")
    if config.network.model != "distance_aware":
        raise ValueError("Only the distance_aware network model is supported")
    if config.placement.strategy not in {
        "cloud_only",
        "fog_only",
        "edge_local",
        "full_replication",
        "replicated",
        "partial_replication",
        "selective_replication",
        "distributed",
        "partitioned",
        "partitioned_selective_replication",
        "hybrid",
    }:
        raise ValueError("Unsupported ontology placement strategy")
    if config.scheduler.strategy not in {
        "cloud_only",
        "fog_only",
        "edge_first",
        "random",
        "round_robin",
        "nearest_node",
        "latency_aware",
        "data_locality_aware",
        "resource_aware",
        "mobility_aware",
    }:
        raise ValueError("Unsupported scheduling strategy")
