"""HTTP contract shared by continuum benchmark coordinators and workers."""

from __future__ import annotations

from typing import Any, Mapping

from .specification import ONTOLOGY_REVISION, ONTOLOGY_VERSION
from .reasoners import REASONING_CONTRACT
from .topology import NODE_ID_PATTERN, TIERS


WORKER_SERVICE = "continuum-benchmark-node"
WORKER_PROTOCOL_VERSION = "6"
EXPECTED_QUERY_COUNT = 115


def worker_health_error(
    health: Mapping[str, Any],
    *,
    expected_role: str | None = None,
    expected_node_id: str | None = None,
    expected_tier: str | None = None,
    expected_authority: bool | None = None,
    expected_categories: tuple[str, ...] | None = None,
    expected_topology_fingerprint: str | None = None,
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
    if health.get("ontology_revision") != ONTOLOGY_REVISION:
        return (
            f"ontology_revision must be {ONTOLOGY_REVISION!r}, "
            f"got {health.get('ontology_revision')!r}; rebuild/redeploy "
            "the worker with the English, datatype-corrected ontology"
        )
    node_id = str(health.get("node_id", health.get("role", ""))).strip()
    if not NODE_ID_PATTERN.fullmatch(node_id):
        return f"node_id is invalid, got {node_id!r}"
    tier = str(health.get("tier", "")).strip().lower()
    if tier not in TIERS:
        return f"tier must be one of {list(TIERS)}, got {tier!r}"
    expected_id = expected_node_id or expected_role
    if expected_id is not None and node_id != expected_id:
        return f"node_id must be {expected_id!r}, got {node_id!r}"
    if expected_tier is not None and tier != expected_tier:
        return f"tier must be {expected_tier!r}, got {tier!r}"
    if (
        expected_authority is not None
        and bool(health.get("authority")) != expected_authority
    ):
        return (
            f"authority must be {expected_authority!r}, "
            f"got {health.get('authority')!r}"
        )
    if expected_categories is not None:
        actual_categories = health.get("categories")
        if not isinstance(actual_categories, list) or set(
            map(str, actual_categories)
        ) != set(expected_categories):
            return (
                f"categories must be {sorted(expected_categories)!r}, "
                f"got {actual_categories!r}"
            )
    if (
        expected_topology_fingerprint is not None
        and health.get("topology_fingerprint")
        != expected_topology_fingerprint
    ):
        return (
            "topology_fingerprint does not match the coordinator manifest; "
            "redeploy or recreate this worker"
        )
    return None
