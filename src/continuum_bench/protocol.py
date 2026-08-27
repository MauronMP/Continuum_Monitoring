"""HTTP contract shared by continuum benchmark coordinators and workers."""

from __future__ import annotations

from typing import Any, Mapping

from .specification import ONTOLOGY_VERSION
from .reasoners import REASONING_CONTRACT


WORKER_SERVICE = "continuum-benchmark-node"
WORKER_PROTOCOL_VERSION = "5"
WORKER_ROLES = frozenset({"cloud", "fog", "edge1", "edge2", "edge3"})
EXPECTED_QUERY_COUNT = 115


def worker_health_error(
    health: Mapping[str, Any],
    *,
    expected_role: str | None = None,
) -> str | None:
    """Return an actionable error for an incompatible worker response."""
    if health.get("status") != "ok":
        return f"status must be 'ok', got {health.get('status')!r}"
    if health.get("service") != WORKER_SERVICE:
        return (
            f"service must be {WORKER_SERVICE!r}, "
            f"got {health.get('service')!r}"
        )
    if str(health.get("protocol_version", "")) != WORKER_PROTOCOL_VERSION:
        return (
            f"protocol_version must be {WORKER_PROTOCOL_VERSION!r}, "
            f"got {health.get('protocol_version')!r}"
        )
    if str(health.get("ontology_version", "")) != ONTOLOGY_VERSION:
        return (
            f"ontology_version must be {ONTOLOGY_VERSION!r}, "
            f"got {health.get('ontology_version')!r}"
        )
    try:
        query_count = int(health.get("query_count", -1))
    except (TypeError, ValueError):
        query_count = -1
    if query_count != EXPECTED_QUERY_COUNT:
        return (
            f"query_count must be {EXPECTED_QUERY_COUNT}, "
            f"got {health.get('query_count')!r}"
        )
    if health.get("reasoning_contract") != REASONING_CONTRACT:
        return (
            f"reasoning_contract must be {REASONING_CONTRACT!r}, "
            f"got {health.get('reasoning_contract')!r}; rebuild/redeploy "
            "the worker to apply the RDFS datatype correction"
        )
    role = str(health.get("role", "")).strip()
    if role not in WORKER_ROLES:
        return f"role must be one of {sorted(WORKER_ROLES)}, got {role!r}"
    if expected_role is not None and role != expected_role:
        return f"role must be {expected_role!r}, got {role!r}"
    return None
