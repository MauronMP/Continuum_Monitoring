"""HTTP contract shared by continuum benchmark coordinators and workers."""

from __future__ import annotations

from typing import Any, Mapping


WORKER_SERVICE = "continuum-benchmark-node"
WORKER_PROTOCOL_VERSION = "4"
WORKER_ROLES = frozenset({"cloud", "fog", "edge1", "edge2", "edge3"})


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
    role = str(health.get("role", "")).strip()
    if role not in WORKER_ROLES:
        return f"role must be one of {sorted(WORKER_ROLES)}, got {role!r}"
    if expected_role is not None and role != expected_role:
        return f"role must be {expected_role!r}, got {role!r}"
    return None
