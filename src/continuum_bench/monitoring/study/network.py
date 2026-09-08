from __future__ import annotations

from math import dist

from .config import NetworkModel
from .models import LinkEstimate, Position


def estimate_link(
    config: NetworkModel,
    source_id: str,
    source: Position,
    target_id: str,
    target: Position,
) -> LinkEstimate:
    distance_m = dist((source.x_m, source.y_m, source.z_m), (target.x_m, target.y_m, target.z_m))
    latency_ms = config.base_latency_ms + distance_m * config.latency_per_meter_ms
    bandwidth = max(
        1.0,
        config.base_bandwidth_mbps
        - distance_m * config.bandwidth_decay_per_meter,
    )
    packet_loss = min(1.0, max(0.0, distance_m * config.packet_loss_per_meter))
    return LinkEstimate(
        source=source_id,
        target=target_id,
        distance_m=distance_m,
        latency_ms=latency_ms,
        bandwidth_mbps=bandwidth,
        packet_loss_probability=packet_loss,
        jitter_ms=config.jitter_ms,
    )
