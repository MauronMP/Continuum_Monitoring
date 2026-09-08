from __future__ import annotations

import csv
from dataclasses import asdict
import json
from pathlib import Path
import random

from ..config import BenchmarkConfig
from ..csv_utils import write_dict_rows
from ..distributed import Endpoint
from ..queries import QuerySpec, load_catalog
from ..topology import load_topology
from .config import PolicyCostStudyConfig
from .mobility import build_mobility_strategy
from .models import Position, QueryFeatures, RequestRecord
from .network import estimate_link
from .placement import (
    data_locality_score,
    default_node_positions,
    execution_candidates,
)
from .sparql import characterize_query


def generate_study_trace(
    config: BenchmarkConfig,
    study: PolicyCostStudyConfig,
    output_dir: Path,
    *,
    topology_name: str | None = None,
    target: str = "physical",
) -> list[Path]:
    """Generate reproducible request, mobility and query-feature datasets."""

    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    if target not in {"local", "docker", "physical"}:
        raise ValueError("Study target must be local, docker or physical")
    topology_key = "monolith" if target == "local" else target
    selected_name = topology_name or topology_key
    topology_path = (
        config.root / f"configs/topologies/{topology_key}/topology.toml"
    )
    topology = load_topology(topology_path, selected_name)
    endpoints = [
        Endpoint(
            node.endpoint,
            node.node_id,
            tier=node.tier,
            authority=node.authority,
            categories=node.categories,
        )
        for node in topology.nodes
        if node.enabled
    ]
    features = {spec.id: characterize_query(spec) for spec in specs}
    schedule = _arrival_times(study)
    rng = random.Random(study.seed)
    mobility = build_mobility_strategy(study.mobility)
    node_positions = default_node_positions(endpoints)
    clients = [f"client{i + 1}" for i in range(study.client_count)]
    rows: list[RequestRecord] = []
    mobility_rows = []
    connectivity_events = []
    previous_association: dict[str, str] = {}
    categories = sorted({spec.category for spec in specs})
    category_queries = {
        category: [spec for spec in specs if spec.category == category]
        for category in categories
    }

    for index, timestamp in enumerate(schedule):
        client_id = clients[index % len(clients)]
        sample = mobility.position_at(client_id, timestamp)
        client_position = Position(sample.x_m, sample.y_m, sample.z_m)
        edge_candidates = [endpoint for endpoint in endpoints if endpoint.tier == "edge"]
        associated_edge = (
            min(
                edge_candidates,
                key=lambda endpoint: (
                    (node_positions[endpoint.role].x_m - sample.x_m) ** 2
                    + (node_positions[endpoint.role].y_m - sample.y_m) ** 2
                ),
            ).role
            if edge_candidates
            else ""
        )
        previous = previous_association.get(client_id, "")
        handover = ""
        if previous and associated_edge != previous:
            handover = "association_changed"
            connectivity_events.append(
                {
                    "experiment_id": study.experiment_id,
                    "timestamp_s": timestamp,
                    "client_id": client_id,
                    "event": handover,
                    "previous_edge": previous,
                    "new_edge": associated_edge,
                }
            )
        previous_association[client_id] = associated_edge
        category = _choose_category(study, categories, rng, index)
        spec = rng.choice(category_queries[category])
        candidates = execution_candidates(
            spec,
            endpoints,
            study.placement.strategy,
        )
        selected = _select_endpoint(
            candidates,
            sample,
            node_positions,
            study.scheduler.strategy,
            index,
            features[spec.id],
            study.seed,
        )
        link = estimate_link(
            study.network,
            client_id,
            client_position,
            selected.role,
            node_positions[selected.role],
        )
        policy_id = _choose_policy(spec, rng)
        connectivity_state = (
            "disconnected"
            if link.packet_loss_probability >= 1.0
            else "connected"
        )
        mobility_rows.append(
            {
                **asdict(sample),
                "associated_edge": associated_edge,
                "connectivity_state": connectivity_state,
                "handover_event": handover,
            }
        )
        rows.append(
            RequestRecord(
                experiment_id=study.experiment_id,
                configuration_id=study.path.stem,
                seed=study.seed,
                request_id=f"req-{index + 1:08d}",
                scheduled_timestamp_s=timestamp,
                dispatch_timestamp_s="",
                completion_timestamp_s="",
                client_id=client_id,
                client_x_m=sample.x_m,
                client_y_m=sample.y_m,
                client_z_m=sample.z_m,
                client_speed_mps=sample.speed_mps,
                client_direction_degrees=sample.direction_degrees,
                associated_edge=associated_edge,
                connectivity_state=connectivity_state,
                handover_event=handover,
                policy_category=category,
                policy_id=policy_id,
                query_id=spec.id,
                query_template_id=spec.id,
                query_structural_complexity=(
                    features[spec.id].structural_complexity
                ),
                query_triple_patterns=features[spec.id].triple_patterns,
                query_joins=features[spec.id].joins,
                query_filters=features[spec.id].filters,
                query_shape=features[spec.id].query_shape,
                target_service=spec.execution_scope,
                entry_node=selected.role,
                execution_nodes=",".join(endpoint.role for endpoint in candidates),
                ontology_placement=study.placement.strategy,
                routing_strategy=study.scheduler.strategy,
                mobility_model=study.mobility.model,
                network_model=study.network.model,
                estimated_network_latency_ms=link.latency_ms,
                estimated_bandwidth_mbps=link.bandwidth_mbps,
                estimated_packet_loss_probability=(
                    link.packet_loss_probability
                ),
                data_locality_score=data_locality_score(
                    spec,
                    selected,
                    study.placement.strategy,
                ),
                request_status="scheduled",
            )
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    request_path = output_dir / "request-trace.csv"
    mobility_path = output_dir / "mobility-trace.csv"
    features_path = output_dir / "query-features.csv"
    events_path = output_dir / "connectivity-events.csv"
    metadata_path = output_dir / "metadata.json"
    write_dict_rows(
        request_path,
        [asdict(row) for row in rows],
        empty_message="No request trace rows",
    )
    write_dict_rows(
        mobility_path,
        mobility_rows,
        empty_message="No mobility trace rows",
    )
    _write_features(features_path, features.values())
    if connectivity_events:
        write_dict_rows(
            events_path,
            connectivity_events,
            empty_message="No connectivity events",
        )
    else:
        events_path.write_text(
            "experiment_id,timestamp_s,client_id,event,previous_edge,new_edge\n",
            encoding="utf-8",
        )
    metadata_path.write_text(
        json.dumps(
            {
                "experiment_id": study.experiment_id,
                "configuration": str(study.path),
                "seed": study.seed,
                "request_count": len(rows),
                "client_count": study.client_count,
                "mobility_model": study.mobility.model,
                "network_model": study.network.model,
                "placement_strategy": study.placement.strategy,
                "scheduler_strategy": study.scheduler.strategy,
                "topology_name": selected_name,
                "target": target,
                "node_count": len(endpoints),
                "arrival_model": study.workload.arrival_model,
                "execution_mode": study.workload.execution_mode,
                "concurrency": study.workload.concurrency,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return [request_path, mobility_path, features_path, events_path, metadata_path]


def _write_features(path: Path, features: object) -> None:
    rows = [asdict(feature) for feature in features]
    write_dict_rows(path, rows, empty_message="No query features")


def _arrival_times(study: PolicyCostStudyConfig) -> list[float]:
    rng = random.Random(study.seed)
    model = study.workload.arrival_model
    if model == "uniform":
        step = study.duration_seconds / study.request_count
        return [index * step for index in range(study.request_count)]
    if model == "poisson":
        current = 0.0
        values = []
        rate = study.workload.request_rate_per_second
        for _ in range(study.request_count):
            current += rng.expovariate(rate)
            values.append(min(current, study.duration_seconds))
        return values
    if model == "bursty":
        values = []
        current = 0.0
        while len(values) < study.request_count:
            current += 1.0 / study.workload.request_rate_per_second
            burst = (
                study.workload.burst_size
                if rng.random() < study.workload.burst_probability
                else 1
            )
            values.extend([min(current, study.duration_seconds)] * burst)
        return values[: study.request_count]
    if model == "ramp":
        values = []
        current = 0.0
        for index in range(study.request_count):
            fraction = index / max(1, study.request_count - 1)
            rate = (
                study.workload.ramp_start_rate_per_second
                + fraction
                * (
                    study.workload.ramp_end_rate_per_second
                    - study.workload.ramp_start_rate_per_second
                )
            )
            current += 1.0 / max(rate, 0.001)
            values.append(min(current, study.duration_seconds))
        return values
    if model == "trace":
        trace_path = Path(study.workload.trace_path)
        if not trace_path.is_absolute():
            trace_path = study.path.parent / trace_path
        with trace_path.open(encoding="utf-8", newline="") as handle:
            trace = list(csv.DictReader(handle))
        values = []
        for row in trace[: study.request_count]:
            raw = row.get("scheduled_timestamp_s", row.get("timestamp_s", ""))
            if raw == "":
                raise ValueError(
                    "Arrival trace requires scheduled_timestamp_s or timestamp_s"
                )
            values.append(float(raw))
        if not values:
            raise ValueError("Arrival trace is empty")
        if values != sorted(values) or values[0] < 0:
            raise ValueError("Arrival trace timestamps must be non-negative and ordered")
        return values
    raise AssertionError(f"Unhandled arrival model: {model}")


def _choose_category(
    study: PolicyCostStudyConfig,
    categories: list[str],
    rng: random.Random,
    index: int,
) -> str:
    model = study.workload.category_distribution
    if model == "uniform":
        return rng.choice(categories)
    if model == "weighted":
        return _weighted_choice(
            categories,
            [study.workload.category_weights.get(category, 1.0) for category in categories],
            rng,
        )
    if model == "zipf":
        weights = [
            1.0 / ((rank + 1) ** study.workload.zipf_exponent)
            for rank, _ in enumerate(categories)
        ]
        return _weighted_choice(categories, weights, rng)
    hotspot_count = max(1, round(len(categories) * study.workload.hotspot_fraction))
    hotspots = categories[:hotspot_count]
    if model == "dynamic_hotspot":
        offset = (index // max(1, study.request_count // 4)) % len(categories)
        hotspots = [
            categories[(offset + item) % len(categories)]
            for item in range(hotspot_count)
        ]
    if rng.random() < study.workload.hotspot_share:
        return rng.choice(hotspots)
    return rng.choice([item for item in categories if item not in hotspots] or categories)


def _weighted_choice(
    values: list[str],
    weights: list[float],
    rng: random.Random,
) -> str:
    total = sum(max(0.0, weight) for weight in weights)
    if total <= 0:
        return rng.choice(values)
    pick = rng.random() * total
    cumulative = 0.0
    for value, weight in zip(values, weights, strict=True):
        cumulative += max(0.0, weight)
        if cumulative >= pick:
            return value
    return values[-1]


def _choose_policy(spec: QuerySpec, rng: random.Random) -> str:
    return rng.choice(spec.policies) if spec.policies else ""


def _select_endpoint(
    candidates,
    client_sample,
    node_positions,
    strategy: str,
    index: int,
    features: QueryFeatures,
    seed: int,
):
    preferred_tier = {
        "cloud_only": "cloud",
        "fog_only": "fog",
        "edge_first": "edge",
    }.get(strategy)
    if preferred_tier:
        preferred = [item for item in candidates if item.tier == preferred_tier]
        if preferred:
            candidates = preferred
    if strategy == "round_robin":
        return candidates[index % len(candidates)]
    if strategy == "random":
        return random.Random(
            f"{seed}:{client_sample.node_id}:{index}"
        ).choice(candidates)
    if strategy in {"nearest_node", "latency_aware", "mobility_aware"}:
        return min(
            candidates,
            key=lambda endpoint: (
                (node_positions[endpoint.role].x_m - client_sample.x_m) ** 2
                + (node_positions[endpoint.role].y_m - client_sample.y_m) ** 2
            ),
        )
    if strategy in {"data_locality_aware", "resource_aware"}:
        return min(
            candidates,
            key=lambda endpoint: (
                features.structural_complexity
                * (0.75 if endpoint.authority else 1.0),
                endpoint.role,
            ),
        )
    if preferred_tier:
        return candidates[index % len(candidates)]
    raise ValueError(f"Unsupported scheduler strategy: {strategy}")
