from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    x_m: float
    y_m: float
    z_m: float = 0.0


@dataclass(frozen=True)
class MobilitySample:
    timestamp_s: float
    node_id: str
    x_m: float
    y_m: float
    z_m: float
    speed_mps: float
    direction_degrees: float
    mobility_model: str
    mobility_state: str


@dataclass(frozen=True)
class LinkEstimate:
    source: str
    target: str
    distance_m: float
    latency_ms: float
    bandwidth_mbps: float
    packet_loss_probability: float
    jitter_ms: float


@dataclass(frozen=True)
class QueryFeatures:
    query_id: str
    category: str
    policy_count: int
    triple_patterns: int
    joins: int
    filters: int
    optional_clauses: int
    union_clauses: int
    distinct: bool
    aggregations: int
    group_by: bool
    order_by: bool
    limit_offset: bool
    basic_graph_patterns: int
    query_shape: str
    structural_complexity: float


@dataclass(frozen=True)
class RequestRecord:
    experiment_id: str
    configuration_id: str
    seed: int
    request_id: str
    scheduled_timestamp_s: float
    dispatch_timestamp_s: float | str
    completion_timestamp_s: float | str
    client_id: str
    client_x_m: float
    client_y_m: float
    client_z_m: float
    client_speed_mps: float
    client_direction_degrees: float
    associated_edge: str
    connectivity_state: str
    handover_event: str
    policy_category: str
    policy_id: str
    query_id: str
    query_template_id: str
    query_structural_complexity: float
    query_triple_patterns: int
    query_joins: int
    query_filters: int
    query_shape: str
    target_service: str
    entry_node: str
    execution_nodes: str
    ontology_placement: str
    routing_strategy: str
    mobility_model: str
    network_model: str
    estimated_network_latency_ms: float
    estimated_bandwidth_mbps: float
    estimated_packet_loss_probability: float
    data_locality_score: float
    request_status: str
