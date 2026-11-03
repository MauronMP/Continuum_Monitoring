from __future__ import annotations

import json
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, wait
from datetime import UTC, datetime
from hashlib import sha256
from time import monotonic

from .protocol import request_json
from .topology import Host

RequestFunction = Callable[..., dict]
Clock = Callable[[], float]


def select_hosts(hosts: tuple[Host, ...], query: dict, round_: int, query_index: int, layout: str) -> tuple[Host, ...]:
    if layout == "replicated":
        return (hosts[(round_ + query_index) % len(hosts)],)
    scope = query["execution_scope"]
    if scope == "authorities":
        return tuple(host for host in hosts if host.tier == "edge") or hosts
    if scope == "cloud_authorities":
        return tuple(host for host in hosts if host.tier in {"cloud", "edge"}) or hosts
    if scope == "all":
        return hosts
    if scope.startswith("authority_key:"):
        authorities = tuple(host for host in hosts if host.tier == "edge") or hosts
        index = int.from_bytes(sha256(scope.encode()).digest()[:8], "big") % len(authorities)
        return (authorities[index],)
    candidates = tuple(host for host in hosts if host.tier == scope)
    return (
        (candidates[(round_ + query_index) % len(candidates)],)
        if candidates
        else (hosts[(round_ + query_index) % len(hosts)],)
    )


def _physical_query(
    host: Host,
    query: dict,
    round_: int,
    logical_deadline: float,
    physical_timeout: float,
    request: RequestFunction,
    clock: Clock,
) -> dict:
    started_at = datetime.now(UTC).isoformat()
    started = clock()
    remaining = logical_deadline - started
    if remaining <= 0:
        return {
            "query_id": query["id"],
            "round": round_,
            "host": host.id,
            "start_timestamp": started_at,
            "duration_ms": 0.0,
            "request_duration_ms": 0.0,
            "physical_timeout_seconds": 0.0,
            "status": "query_timeout",
            "result_count": None,
            "result_digest": None,
            "error": "logical query deadline exhausted before dispatch",
        }
    effective_timeout = min(physical_timeout, remaining)
    try:
        response = request(
            f"{host.endpoint}/query",
            method="POST",
            timeout=effective_timeout,
            headers={"content-type": "application/json"},
            payload=json.dumps({"query_id": query["id"], "query": query["query"], "round": round_}).encode(),
        )
        outcome = response["outcome"]
        return {
            "query_id": query["id"],
            "round": round_,
            "host": host.id,
            "start_timestamp": started_at,
            "duration_ms": outcome["duration_ms"],
            "request_duration_ms": (clock() - started) * 1000,
            "physical_timeout_seconds": effective_timeout,
            "status": "completed",
            "result_count": outcome["result_count"],
            "result_digest": outcome["result_digest"],
            "_result_keys": outcome["result_keys"],
            "_ask_result": bool(outcome["ask_result"]),
        }
    except Exception as error:
        status = "query_timeout" if "timed out" in str(error).lower() or "deadline" in str(error).lower() else "failed"
        return {
            "query_id": query["id"],
            "round": round_,
            "host": host.id,
            "start_timestamp": started_at,
            "duration_ms": (clock() - started) * 1000,
            "request_duration_ms": (clock() - started) * 1000,
            "physical_timeout_seconds": effective_timeout,
            "status": status,
            "result_count": None,
            "result_digest": None,
            "error": str(error),
        }


def execute_logical_query(
    hosts: tuple[Host, ...],
    query: dict,
    round_: int,
    query_index: int,
    layout: str,
    *,
    physical_timeout: float,
    logical_timeout: float,
    request: RequestFunction = request_json,
    clock: Clock = monotonic,
    wait_for_futures=wait,
) -> tuple[dict, list[dict]]:
    """Execute one logical query; only its required physical fan-out is concurrent."""
    logical_started_at = datetime.now(UTC).isoformat()
    logical_started = clock()
    deadline = logical_started + logical_timeout
    selected = select_hosts(hosts, query, round_, query_index, layout)
    executor = ThreadPoolExecutor(max_workers=len(selected), thread_name_prefix="query-fanout")
    futures: dict[Future, Host] = {
        executor.submit(
            _physical_query,
            host,
            query,
            round_,
            deadline,
            physical_timeout,
            request,
            clock,
        ): host
        for host in selected
    }
    remaining = max(0.0, deadline - clock())
    done, pending = wait_for_futures(set(futures), timeout=remaining)
    physical = [future.result() for future in done]
    pending_hosts = []
    for future in pending:
        host = futures[future]
        pending_hosts.append(host.id)
        future.cancel()
        physical.append(
            {
                "query_id": query["id"],
                "round": round_,
                "host": host.id,
                "start_timestamp": logical_started_at,
                "duration_ms": logical_timeout * 1000,
                "request_duration_ms": logical_timeout * 1000,
                "physical_timeout_seconds": min(physical_timeout, logical_timeout),
                "status": "query_timeout",
                "result_count": None,
                "result_digest": None,
                "error": "logical query deadline exceeded while worker request was pending",
            }
        )
    executor.shutdown(wait=False, cancel_futures=True)
    by_host = {row["host"]: row for row in physical}
    physical = [by_host[host.id] for host in selected]
    successful = [row for row in physical if row["status"] == "completed"]
    failed = [row for row in physical if row["status"] != "completed"]
    status = "completed"
    if failed:
        status = "query_timeout" if any(row["status"] == "query_timeout" for row in failed) else "failed"

    merge_started = clock()
    result_count = None
    result_digest = None
    if status == "completed":
        strategy = query["merge_strategy"]
        if strategy == "single" and len(selected) != 1:
            raise RuntimeError(f"Query {query['id']} requires one participant, received {len(selected)}")
        if strategy == "boolean_or" and query["kind"] != "ask":
            raise RuntimeError(f"Query {query['id']} uses boolean_or but is not ASK")
        if strategy not in {"single", "set_union", "boolean_or"}:
            raise RuntimeError(f"Unsupported merge strategy for {query['id']}: {strategy}")
        keys = {key for row in successful for key in row["_result_keys"]}
        ask = any(row["_ask_result"] for row in successful)
        digest_payload = f"ASK:{str(ask).lower()}" if strategy == "boolean_or" else "\n".join(sorted(keys))
        result_count = int(ask) if strategy == "boolean_or" else len(keys)
        result_digest = sha256(digest_payload.encode()).hexdigest()
        if clock() > deadline:
            status = "query_timeout"
            result_count = None
            result_digest = None
    merge_duration_ms = (clock() - merge_started) * 1000
    for row in physical:
        row.pop("_result_keys", None)
        row.pop("_ask_result", None)
    failed_hosts = [row["host"] for row in physical if row["status"] != "completed"]
    logical_duration_ms = (clock() - logical_started) * 1000
    logical = {
        "query_id": query["id"],
        "round": round_,
        "layout": layout,
        "participants": [host.id for host in selected],
        "selected_hosts": [host.id for host in selected],
        "fanout_size": len(selected),
        "start_timestamp": logical_started_at,
        "logical_start_timestamp": logical_started_at,
        "duration_ms": logical_duration_ms,
        "logical_duration_ms": logical_duration_ms,
        "merge_duration_ms": merge_duration_ms,
        "status": status,
        "logical_status": status,
        "result_count": result_count,
        "result_digest": result_digest,
        "successful_hosts": [row["host"] for row in successful],
        "failed_hosts": failed_hosts,
        "pending_hosts": sorted(pending_hosts),
        "partial_results": [
            {"host": row["host"], "result_count": row["result_count"], "result_digest": row["result_digest"]}
            for row in successful
        ]
        if status != "completed"
        else [],
    }
    return logical, physical
