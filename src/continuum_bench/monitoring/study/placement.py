from __future__ import annotations

from ..distributed import Endpoint
from ...queries import QuerySpec
from .models import Position


def default_node_positions(endpoints: list[Endpoint]) -> dict[str, Position]:
    """Return stable simulated positions for continuum roles."""

    positions: dict[str, Position] = {}
    edge_index = 0
    for endpoint in endpoints:
        role = endpoint.role
        tier = endpoint.tier or _tier_from_role(role)
        if tier == "cloud":
            positions[role] = Position(100.0, 100.0)
        elif tier == "fog":
            positions[role] = Position(50.0, 50.0)
        elif tier == "mist":
            positions[role] = Position(25.0, 50.0)
        elif tier == "edge":
            positions[role] = Position(20.0 + edge_index * 35.0, 20.0)
            edge_index += 1
        elif tier == "iot":
            positions[role] = Position(10.0, 10.0)
        else:
            positions[role] = Position(0.0, 0.0)
    return positions


def execution_candidates(
    spec: QuerySpec,
    endpoints: list[Endpoint],
    placement_strategy: str,
) -> list[Endpoint]:
    if placement_strategy in {"full_replication", "replicated"}:
        return endpoints
    preferred_tier = {
        "cloud_only": "cloud",
        "fog_only": "fog",
        "edge_local": "edge",
    }.get(placement_strategy)
    if preferred_tier:
        selected = [endpoint for endpoint in endpoints if endpoint.tier == preferred_tier]
        if not selected:
            raise ValueError(
                f"Placement {placement_strategy} requires an active {preferred_tier} node"
            )
        return selected
    scope = spec.execution_scope
    if scope in {"authorities", "cloud_authorities", "all"}:
        return endpoints
    if scope.startswith("node:"):
        role = scope.split(":", 1)[1]
        return [endpoint for endpoint in endpoints if endpoint.role == role]
    if scope.startswith("authority_key:"):
        authorities = [endpoint for endpoint in endpoints if endpoint.authority]
        return authorities or endpoints
    scoped = [
        endpoint for endpoint in endpoints
        if (endpoint.tier or _tier_from_role(endpoint.role)) == scope
    ]
    return scoped or endpoints


def data_locality_score(
    spec: QuerySpec,
    selected: Endpoint,
    placement_strategy: str,
) -> float:
    if placement_strategy in {"full_replication", "replicated"}:
        return 1.0
    tier = selected.tier or _tier_from_role(selected.role)
    if spec.execution_scope == tier or spec.execution_scope == f"node:{selected.role}":
        return 1.0
    if spec.execution_scope in {"authorities", "all"} and selected.authority:
        return 0.85
    if spec.execution_scope == "cloud_authorities" and tier == "cloud":
        return 0.75
    return 0.35


def _tier_from_role(role: str) -> str:
    if role.startswith("edge"):
        return "edge"
    if role.startswith("iot"):
        return "iot"
    if role.startswith("mist"):
        return "mist"
    return role
