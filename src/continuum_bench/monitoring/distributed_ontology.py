"""Privacy-aware benchmark coordinator for physical continuum nodes."""

from __future__ import annotations

from dataclasses import asdict
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
from time import monotonic, perf_counter_ns
from typing import Any

from rdflib import Graph

from .config import BenchmarkConfig
from .resource_summary import native_resources
from ..reasoners import reasoner_provenance
from .budget import (
    PhaseBudgetTimeout,
    error_text,
    is_timeout_failure,
    TimeoutSkipState,
    skip_metadata,
    local_phase_timeout,
)
from .distributed import (
    Endpoint,
    _combine_query_responses,
    _interleaved_query_batches,
    _parallel,
    _write_csv,
    discover,
)
from ..ontology import load_graph
from ..queries import (
    QuerySpec,
    by_categories,
    execute_query_detailed,
    load_catalog,
    result_digest,
)
from ..reasoners import materialize
from ..specification import release_identity
from .budget import execution_metadata, unlimited_execution
from ..synthetic import add_synthetic_data
from ..topology import TIER_ORDER, authority_index


def _sources(
    spec: QuerySpec,
    endpoints: list[Endpoint],
) -> list[Endpoint]:
    ordered = sorted(
        endpoints,
        key=lambda item: (TIER_ORDER[item.tier], item.role),
    )
    authorities = [item for item in ordered if item.authority]
    scope = spec.execution_scope
    if scope in {"cloud", "fog", "mist", "edge", "iot"}:
        candidates = [item for item in ordered if item.tier == scope]
        if spec.merge_strategy == "single" and candidates:
            # A tier scope denotes a replica set. Deterministic query hashing
            # balances its catalogue across any number of same-tier nodes.
            sources = [
                candidates[authority_index(spec.id, len(candidates))]
            ]
        else:
            sources = candidates
    elif scope == "authorities":
        sources = authorities
    elif scope.startswith("authority_key:"):
        key = scope.split(":", 1)[1]
        if not authorities:
            sources = []
        else:
            sources = [
                authorities[authority_index(key, len(authorities))]
            ]
    elif scope == "cloud_authorities":
        sources = [
            item for item in ordered
            if item.tier == "cloud" or item.authority
        ]
    elif scope == "all":
        sources = ordered
    elif scope.startswith("node:"):
        node_id = scope.split(":", 1)[1]
        sources = [item for item in ordered if item.role == node_id]
    else:
        raise ValueError(f"{spec.id}: unsupported execution scope {scope!r}")
    if not sources:
        raise ValueError(
            f"{spec.id}: scope {scope!r} has no active source in this topology"
        )
    return sources


def _assignment(
    specs: list[QuerySpec],
    endpoints: list[Endpoint],
) -> dict[str, list[QuerySpec]]:
    assigned = {endpoint.url: [] for endpoint in endpoints}
    for spec in specs:
        for endpoint in _sources(spec, endpoints):
            assigned[endpoint.url].append(spec)
    return assigned


def _prepare(
    config: BenchmarkConfig,
    endpoints: list[Endpoint],
    reasoner: str,
    users: int,
    seed: int,
    *,
    timeout_seconds: float | None = None,
) -> tuple[float, dict[str, dict[str, Any]]]:
    # Placement and serialization are part of preparation wall time, just as
    # replicated worker graph construction is included in its HTTP phase.
    from urllib.parse import urlsplit
    from .budget import remaining_seconds
    from ..partitioning import build_fragments, serialize_fragment
    from ..topology import Topology, TopologyNode

    started = monotonic()
    transport = config.distributed
    point_budget = (
        config.limits.point_timeout_seconds
        if timeout_seconds is None else timeout_seconds
    )
    point_budget = min(point_budget, config.limits.phase_timeout_seconds)
    if not endpoints or len({item.role for item in endpoints}) != len(endpoints):
        raise ValueError("Distributed placement requires unique active node IDs")
    if len({item.url for item in endpoints}) != len(endpoints):
        raise ValueError("Distributed placement requires unique worker endpoints")
    topology = Topology(
        name="discovered-placement", kind="physical",
        description="Placement over the discovered physical workers",
        nodes=tuple(
            TopologyNode(
                node_id=item.role, tier=item.tier, endpoint=item.url,
                host=urlsplit(item.url).hostname or "",
                port=urlsplit(item.url).port or 80, local=False,
                authority=item.authority, categories=item.categories,
            )
            for item in endpoints
        ),
    )
    with local_phase_timeout(remaining_seconds(started, point_budget)):
        fragments = build_fragments(config, users, seed, topology=topology)
        payloads = {
            endpoint.url: {
                "reasoner": reasoner, "users": users, "seed": seed,
                "mode": "distributed",
                "fragment": serialize_fragment(
                    fragments, endpoint.role, users=users, seed=seed,
                ),
            }
            for endpoint in endpoints
        }
    placement_ms = (monotonic() - started) * 1000
    timeout = min(
        remaining_seconds(started, point_budget),
        transport.request_timeout_seconds,
    )
    if not unlimited_execution() and timeout <= transport.worker_timeout_margin_seconds:
        raise PhaseBudgetTimeout("no time remains for distributed prepare")
    for payload in payloads.values():
        payload["phase_timeout_seconds"] = (
            0 if unlimited_execution()
            else timeout - transport.worker_timeout_margin_seconds
        )
    print(
        f"[distributed-budget] phase=distributed-prepare "
        f"nodes={len(endpoints)} placement_ms={placement_ms:.2f} "
        f"request_limit_s={timeout:.1f}", flush=True,
    )
    _, prepared = _parallel(
        endpoints, "/prepare", payloads, phase="distributed-prepare",
        timeout=timeout, retries=transport.request_retries,
    )
    for endpoint in endpoints:
        expected = payloads[endpoint.url]["fragment"]
        response = prepared[endpoint.url]
        if (
            response.get("fragment_sha256") != expected["sha256"]
            or response.get("fragment_contract") != expected["contract"]
            or response.get("input_triples") != expected["triples"]
        ):
            raise ValueError(f"Worker {endpoint.role!r} did not confirm its assigned fragment")
        response["coordinator_placement_ms"] = placement_ms
        response["placement_validation"] = "observed-worker-fragment-match"
    return (monotonic() - started) * 1000, prepared


def _query(
    config: BenchmarkConfig,
    endpoints: list[Endpoint],
    assignment: dict[str, list[QuerySpec]],
    *,
    timeout_seconds: float | None = None,
) -> tuple[float, dict[str, dict[str, Any]]]:
    transport = config.distributed
    point_timeout = min(
        timeout_seconds or config.limits.point_timeout_seconds,
        config.limits.point_timeout_seconds,
        config.limits.phase_timeout_seconds,
    )
    started = monotonic()
    batches = {
        url: _interleaved_query_batches(
            specs,
            transport.query_batch_size,
        )
        for url, specs in assignment.items()
        if specs
    }
    batch_rounds = max((len(items) for items in batches.values()), default=0)
    wall_ms = 0.0
    collected: dict[str, list[dict[str, Any]]] = {
        url: [] for url in batches
    }
    endpoint_by_url = {endpoint.url: endpoint for endpoint in endpoints}
    for batch_index in range(batch_rounds):
        remaining = float("inf") if unlimited_execution() else point_timeout - (monotonic() - started)
        request_timeout = min(transport.request_timeout_seconds, remaining)
        if not unlimited_execution() and request_timeout <= transport.worker_timeout_margin_seconds:
            raise PhaseBudgetTimeout(
                "partitioned queries exceeded their "
                f"{point_timeout:.1f}s point budget"
            )
        payloads: dict[str, dict[str, Any]] = {}
        descriptions: list[str] = []
        for url, endpoint_batches in batches.items():
            if batch_index >= len(endpoint_batches):
                continue
            query_ids = [spec.id for spec in endpoint_batches[batch_index]]
            payloads[url] = {
                "query_ids": query_ids,
                "include_result_keys": True,
                "phase_timeout_seconds": (
                    request_timeout
                    - transport.worker_timeout_margin_seconds
                ),
            }
            descriptions.append(
                f"{endpoint_by_url[url].role}:{len(query_ids)}"
            )
        print(
            "[distributed-batch] phase=partitioned-queries "
            f"batch={batch_index + 1}/{batch_rounds} "
            f"nodes={','.join(descriptions)} "
            f"point_remaining_s={remaining:.1f} "
            f"request_limit_s={request_timeout:.1f} "
            "worker_limit_s="
            f"{request_timeout - transport.worker_timeout_margin_seconds:.1f} "
            "status=running",
            flush=True,
        )
        batch_wall_ms, responses = _parallel(
            endpoints,
            "/queries",
            payloads,
            phase=(
                "partitioned-queries-"
                f"batch-{batch_index + 1}-of-{batch_rounds}"
            ),
            timeout=request_timeout,
            retries=transport.request_retries,
        )
        wall_ms += batch_wall_ms
        for url, response in responses.items():
            collected[url].append(response)
        print(
            "[distributed-batch] phase=partitioned-queries "
            f"batch={batch_index + 1}/{batch_rounds} status=done "
            f"wall_ms={batch_wall_ms:.2f}",
            flush=True,
        )
    return wall_ms, {
        url: _combine_query_responses(items)
        for url, items in collected.items()
    }


def _merge_responses(
    specs: list[QuerySpec],
    endpoints: list[Endpoint],
    responses: dict[str, dict[str, Any]],
    common: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    endpoint_by_url = {item.url: item for item in endpoints}
    raw_by_query: dict[str, list[dict[str, Any]]] = {
        spec.id: [] for spec in specs
    }
    node_rows: list[dict[str, Any]] = []
    for url, response in responses.items():
        role = endpoint_by_url[url].role
        for measurement in response["measurements"]:
            node_rows.append(
                {
                    **common,
                    "endpoint": url,
                    "role": role,
                    "status": "completed",
                    "censored": False,
                    **measurement,
                }
            )
            raw_by_query[measurement["query_id"]].append(
                {"role": role, **measurement}
            )

    merged: list[dict[str, Any]] = []
    for spec in specs:
        parts = raw_by_query[spec.id]
        if not parts:
            raise RuntimeError(f"No source returned {spec.id}")
        if spec.merge_strategy == "boolean_or":
            ask_result = any(bool(part["ask_result"]) for part in parts)
            result_count = int(ask_result)
            merged_keys: list[str] = []
        elif spec.merge_strategy == "set_union":
            ask_result = None
            counters = [
                Counter(part.get("result_keys", [])) for part in parts
            ]
            merged_counter = Counter(
                {
                    key: max(counter[key] for counter in counters)
                    for key in {
                        key for counter in counters for key in counter
                    }
                }
            )
            merged_keys = list(merged_counter.elements())
            result_count = len(merged_keys)
        elif spec.merge_strategy == "group_union":
            raise ValueError(
                f"{spec.id}: group_union cannot preserve aggregate values; "
                "route aggregate queries to one authoritative source or "
                "declare an algebraic partial aggregate"
            )
        elif spec.merge_strategy == "single":
            if len(parts) != 1:
                raise RuntimeError(
                    f"{spec.id}: single merge received {len(parts)} sources"
                )
            ask_result = parts[0]["ask_result"]
            result_count = int(parts[0]["result_count"])
            merged_keys = list(parts[0].get("result_keys", []))
        else:
            raise ValueError(
                f"{spec.id}: unknown merge strategy {spec.merge_strategy}"
            )
        merged.append(
            {
                **common,
                "query_id": spec.id,
                "category": spec.category,
                "tier": spec.tier,
                "execution_scope": spec.execution_scope,
                "authority": spec.authority,
                "privacy_class": spec.privacy_class,
                "merge_strategy": spec.merge_strategy,
                "source_roles": "|".join(
                    sorted(str(part["role"]) for part in parts)
                ),
                "source_count": len(parts),
                "duration_ms": max(
                    float(part["duration_ms"]) for part in parts
                ),
                "node_duration_ms_sum": sum(
                    float(part["duration_ms"]) for part in parts
                ),
                "result_count": result_count,
                "ask_result": ask_result,
                "result_digest": result_digest(merged_keys, ask_result),
                "status": "completed",
                "censored": False,
            }
        )
    return merged, node_rows


def _full_source(config: BenchmarkConfig, users: int) -> Graph:
    graph = load_graph(
        config.resolve(path) for path in config.ontology_files
    )
    add_synthetic_data(graph, users, config.seed)
    return graph


def _baseline_counts(
    config: BenchmarkConfig,
    specs: list[QuerySpec],
    reasoner: str,
    users: int,
) -> dict[str, tuple[int, bool | None, str]]:
    reasoning = materialize(_full_source(config, users), reasoner)
    return {
        spec.id: (
            execution.measurement.result_count,
            execution.measurement.ask_result,
            result_digest(
                execution.result_keys,
                execution.measurement.ask_result,
            ),
        )
        for spec in specs
        for execution in [execute_query_detailed(reasoning.graph, spec)]
    }


def _validation_rows(
    merged: list[dict[str, Any]],
    baseline: dict[str, tuple[int, bool | None, str]],
) -> list[dict[str, Any]]:
    rows = []
    for item in merged:
        expected_count, expected_ask, expected_digest = baseline[
            item["query_id"]
        ]
        valid = (
            int(item["result_count"]) == expected_count
            and item["ask_result"] == expected_ask
            and item["result_digest"] == expected_digest
        )
        rows.append(
            {
                "reasoner": item["reasoner"],
                "synthetic_users": item.get("synthetic_users", 0),
                "repetition": item.get("repetition", ""),
                "stage": item.get("stage", ""),
                "added_category": item.get("added_category", ""),
                "query_id": item["query_id"],
                "execution_scope": item["execution_scope"],
                "distributed_count": item["result_count"],
                "canonical_count": expected_count,
                "distributed_ask": item["ask_result"],
                "canonical_ask": expected_ask,
                "distributed_digest": item["result_digest"],
                "canonical_digest": expected_digest,
                "valid": valid,
            }
        )
    return rows


def _summary(
    common: dict[str, Any],
    query_count: int,
    prepare_wall_ms: float,
    query_wall_ms: float,
    prepared: dict[str, dict[str, Any]],
    responses: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    aggregate_input = sum(
        int(item["input_triples"]) for item in prepared.values()
    )
    logical_input = max(
        int(item["logical_input_triples"])
        for item in prepared.values()
    )
    prepare_peak_rss = [
        int(item.get("peak_rss_kib", 0)) for item in prepared.values()
    ]
    query_peak_rss = [
        int(item.get("peak_rss_kib", 0)) for item in responses.values()
    ]
    prepare_current_rss = [
        int(item.get("current_rss_kib", 0)) for item in prepared.values()
    ]
    query_current_rss = [
        int(item.get("current_rss_kib", 0)) for item in responses.values()
    ]
    return {
        **common,
        **native_resources(prepared),
        "status": "completed",
        "censored": False,
        "node_count": len(prepared),
        "query_count": query_count,
        "source_query_executions": sum(
            int(item.get("query_count", 0)) for item in responses.values()
        ),
        "federation_fanout_factor": (
            sum(
                int(item.get("query_count", 0))
                for item in responses.values()
            )
            / query_count
            if query_count
            else 0.0
        ),
        "prepare_wall_ms": prepare_wall_ms,
        "node_generation_ms_sum": sum(
            float(item["generation_ms"]) for item in prepared.values()
        ),
        "node_reasoning_ms_sum": sum(
            float(item["reasoning_ms"]) for item in prepared.values()
        ),
        "max_node_reasoning_ms": max(
            float(item["reasoning_ms"]) for item in prepared.values()
        ),
        "query_wall_ms": query_wall_ms,
        "prepare_transport_retry_count": sum(
            max(int(item.get("_coordinator_attempts", 1)) - 1, 0)
            for item in prepared.values()
        ),
        "query_transport_retry_count": sum(
            max(int(item.get("_coordinator_attempts", 1)) - 1, 0)
            for item in responses.values()
        ),
        "node_query_batch_count_sum": sum(
            int(item.get("query_batch_count", 1))
            for item in responses.values()
        ),
        "max_node_query_batch_count": max(
            (
                int(item.get("query_batch_count", 1))
                for item in responses.values()
            ),
            default=0,
        ),
        "node_query_ms_sum": sum(
            float(item["query_cpu_ms"]) for item in responses.values()
        ),
        "node_prepare_process_cpu_ms_sum": sum(
            float(item.get("process_cpu_ms", 0.0))
            for item in prepared.values()
        ),
        "node_query_process_cpu_ms_sum": sum(
            float(item.get("process_cpu_ms", 0.0))
            for item in responses.values()
        ),
        "total_process_cpu_ms": sum(
            float(item.get("process_cpu_ms", 0.0))
            for item in (*prepared.values(), *responses.values())
        ),
        "max_node_prepare_peak_rss_kib": max(prepare_peak_rss, default=0),
        "max_node_query_peak_rss_kib": max(query_peak_rss, default=0),
        "max_node_peak_rss_kib": max(
            (*prepare_peak_rss, *query_peak_rss),
            default=0,
        ),
        "sum_node_prepare_current_rss_kib": sum(prepare_current_rss),
        "sum_node_query_current_rss_kib": sum(query_current_rss),
        "max_sum_node_current_rss_kib": max(
            sum(prepare_current_rss),
            sum(query_current_rss),
        ),
        "prepare_request_bytes_sum": sum(
            int(item.get("request_bytes", 0)) for item in prepared.values()
        ),
        "prepare_response_bytes_sum": sum(
            int(item.get("response_bytes", 0)) for item in prepared.values()
        ),
        "query_request_bytes_sum": sum(
            int(item.get("request_bytes", 0)) for item in responses.values()
        ),
        "query_response_bytes_sum": sum(
            int(item.get("response_bytes", 0)) for item in responses.values()
        ),
        "total_wall_ms": prepare_wall_ms + query_wall_ms,
        "logical_input_triples": logical_input,
        "aggregate_fragment_triples": aggregate_input,
        "aggregate_output_triples": sum(
            int(item.get("output_triples", item["input_triples"]))
            for item in prepared.values()
        ),
        "aggregate_inferred_triples": sum(
            int(item.get("inferred_triples", 0))
            for item in prepared.values()
        ),
        "max_fragment_triples": max(
            int(item["input_triples"]) for item in prepared.values()
        ),
        "max_fragment_fraction": (
            max(int(item["input_triples"]) for item in prepared.values())
            / logical_input
            if logical_input
            else 0.0
        ),
        "storage_replication_factor": (
            aggregate_input / logical_input if logical_input else 0.0
        ),
    }


def _censored_summary(
    common: dict[str, Any],
    node_count: int,
    query_count: int,
    status: str,
    phase: str,
    error: str,
    timeout_seconds: float,
    elapsed_seconds: float,
) -> dict[str, Any]:
    lower_bound_ms = min(max(elapsed_seconds, 0.0), timeout_seconds) * 1000
    return {
        **common,
        "status": status,
        "censored": True,
        "failed_phase": phase,
        "error": error,
        "timeout_seconds": timeout_seconds,
        "censored_lower_bound_ms": lower_bound_ms,
        "node_count": node_count,
        "query_count": query_count,
        "prepare_wall_ms": "",
        "query_wall_ms": "",
        "total_wall_ms": lower_bound_ms if status == "timeout" else "",
    }


def _censored_detail(
    common: dict[str, Any],
    status: str,
    phase: str,
    error: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    return {
        **common,
        "query_id": "__phase__",
        "category": "",
        "tier": "",
        "duration_ms": "",
        "result_count": "",
        "ask_result": "",
        "result_digest": "",
        "status": status,
        "censored": True,
        "failed_phase": phase,
        "timeout_seconds": timeout_seconds,
        "error": error,
    }


def _metadata(
    config: BenchmarkConfig,
    endpoints: list[Endpoint],
    target: str,
    suite: str,
    validate_results: bool,
) -> dict[str, Any]:
    return {
        **release_identity(),
        "execution_policy": execution_metadata(),
        "reasoner_backends": {name: reasoner_provenance(name) for name in config.reasoners},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "suite": suite,
        "mode": f"{target}-elastic-authority-distributed",
        "node_count": len(endpoints),
        "endpoints": [
            {
                "url": item.url,
                "node_id": item.role,
                "role": item.role,
                "tier": item.tier,
                "authority": item.authority,
            }
            for item in endpoints
        ],
        "reasoners": list(config.reasoners),
        "repetitions": config.repetitions,
        "seed": config.seed,
        "result_validation": validate_results,
        "result_validation_level": (
            "exact-order-independent-canonical-result-set; numeric lexical "
            "forms and duplicate solution rows are normalized"
        ),
        "timing_excludes_reference_validation": True,
        "ontology_placement_manifest": str(
            (config.root / "configs/ontology-placement.toml").resolve()
        ),
        "telemetry": {
            "process_cpu_ms": "per-process CPU time consumed during phase",
            "peak_rss_kib": (
                "process lifetime high-water RSS; not incremental phase memory"
            ),
            "request_response_bytes": (
                "HTTP JSON body bytes; excludes transport headers"
            ),
        },
        "worker_telemetry": {
            "process_cpu_ms": "per request process CPU time",
            "peak_rss_kib": "process high-water resident set size",
            "transport_bytes": "exact JSON HTTP request/response body sizes",
        },
        "transport": {
            "timeout_seconds": config.distributed.request_timeout_seconds,
            "retries": config.distributed.request_retries,
            "query_batch_size": config.distributed.query_batch_size,
            "worker_timeout_margin_seconds": (
                config.distributed.worker_timeout_margin_seconds
            ),
            "retry_delay_in_phase_wall_time": True,
            "retry_counts_in_summary": True,
            "timeout_scope": "one prepare request or one query batch",
        },
        "execution_limits": {
            **skip_metadata(config.limits),
            "phase_timeout_seconds": config.limits.phase_timeout_seconds,
            "point_timeout_seconds": config.limits.point_timeout_seconds,
            "stop_scaling_after_timeout": (
                config.limits.stop_scaling_after_timeout
            ),
            "timeout_semantics": (
                "right-censored; a failed distributed topology is not used "
                "for larger scalability points"
            ),
        },
        "routing": (
            "query source selection from queries/execution-plan.toml, "
            "parallel owner execution, deterministic set/ASK merge"
        ),
    }


def run_distributed_cumulative(
    config: BenchmarkConfig,
    endpoint_urls: list[str],
    output_root: Path,
    *,
    target: str,
    validate_results: bool = True,
    topology=None,
) -> Path:
    return _run_distributed(config, endpoint_urls, output_root, target=target,
                        validate_results=validate_results, topology=topology, suite="cumulative")


def run_distributed_scalability(
    config: BenchmarkConfig,
    endpoint_urls: list[str],
    output_root: Path,
    *,
    target: str,
    validate_results: bool = True,
    topology=None,
) -> Path:
    return _run_distributed(config, endpoint_urls, output_root, target=target,
                        validate_results=validate_results, topology=topology, suite="scalability")


def _run_distributed(config, *args, **kwargs):
    from .budget import execution_policy
    with execution_policy(unlimited_execution() or config.limits.timeout_mode == "unlimited"):
        return _run_distributed_impl(config, *args, **kwargs)


def _run_distributed_impl(config, endpoint_urls, output_root, *, target, validate_results, topology, suite):
    endpoints = discover(
        endpoint_urls,
        topology.active_nodes if topology is not None else None,
        topology.fingerprint if topology is not None else None,
    )
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    details: list[dict[str, Any]] = []
    node_details: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    validations: list[dict[str, Any]] = []
    skips = TimeoutSkipState(config.limits)
    cumulative = suite == "cumulative"
    for users in ((0,) if cumulative else config.scale_users):
        for reasoner in config.reasoners:
            baseline = None
            reference_status = "disabled" if not validate_results else "not_executed"
            first_stage = 1 if cumulative else 0
            if validate_results and skips.skipped(reasoner, users, 1, first_stage) is None:
                try:
                    with local_phase_timeout(config.limits.point_timeout_seconds):
                        baseline = _baseline_counts(config, specs, reasoner, users)
                        reference_status = "completed"
                except TimeoutError:
                    reference_status = "timeout"
                    print(f"[{target}-distributed-{suite}] reasoner={reasoner} "
                          "phase=reference-validation status=timeout; "
                          "physical timing will continue without reference results", flush=True)
            for repetition in range(1, config.repetitions + 1):
                prepared_data = None
                stages = enumerate(config.category_order, 1) if cumulative else [(0, None)]
                for stage, category in stages:
                    active_specs = (by_categories(specs, set(config.category_order[:stage])) if cumulative else specs)
                    common = {"reasoner": reasoner, "repetition": repetition, "reference_status": reference_status}
                    if cumulative:
                        common.update(stage=stage, added_category=category)
                    else:
                        common.update(synthetic_users=users, synthetic_triples="")
                    stop_reason = skips.skipped(reasoner, users, repetition, stage)
                    status = "skipped_after_timeout"
                    phase = "early-stop"
                    elapsed = 0.0
                    if stop_reason is None:
                        print(f"[{target}-distributed-{suite}] reasoner={reasoner} users={users} "
                              f"repetition={repetition} stage={stage} status=running", flush=True)
                        started = monotonic()
                        phase = "partitioned-prepare"
                        try:
                            if prepared_data is None:
                                prepared_data = _prepare(
                                    config, endpoints, reasoner, users, config.seed,
                                    timeout_seconds=config.limits.point_timeout_seconds,
                                )
                            prepare_wall_ms, prepared = prepared_data
                            assignment = _assignment(active_specs, endpoints)
                            phase = "partitioned-queries"
                            query_started = monotonic()
                            budget = config.limits.point_timeout_seconds - prepare_wall_ms / 1000
                            if budget <= 0 and not unlimited_execution():
                                raise PhaseBudgetTimeout("preparation exhausted the point budget")
                            query_wall_ms, responses = _query(
                                config, endpoints, assignment, timeout_seconds=max(budget, 0.001),
                            )
                        except Exception as error:
                            if not is_timeout_failure(error):
                                raise
                            skips.timeout(reasoner, users, repetition, stage, error)
                            stop_reason = error_text(error)
                            status = "timeout"
                            elapsed = monotonic() - started
                            if phase == "partitioned-queries":
                                elapsed = prepare_wall_ms / 1000 + monotonic() - query_started
                        else:
                            skips.completed(reasoner)
                            if not cumulative:
                                common["synthetic_triples"] = next(iter(prepared.values()))["synthetic_triples"]
                            merged, raw = _merge_responses(active_specs, endpoints, responses, common)
                            details.extend(merged)
                            node_details.extend(raw)
                            summaries.append(_summary(common, len(active_specs), prepare_wall_ms, query_wall_ms, prepared, responses))
                            if baseline is not None:
                                validations.extend(_validation_rows(merged, baseline))
                            print(f"[{target}-distributed-{suite}] reasoner={reasoner} stage={stage} status=done "
                                  f"wall_ms={prepare_wall_ms + query_wall_ms:.2f}", flush=True)
                            continue
                    summaries.append(_censored_summary(
                        common, len(endpoints), len(active_specs), status, phase,
                        stop_reason, config.limits.point_timeout_seconds, elapsed,
                    ))
                    detail = _censored_detail(common, status, phase, stop_reason, config.limits.point_timeout_seconds)
                    details.append(detail)
                    node_details.append(detail)
                    print(f"[{target}-distributed-{suite}] reasoner={reasoner} users={users} "
                          f"repetition={repetition} stage={stage} status={status}", flush=True)
    output = output_root / suite
    _write_csv(output / "query-runs.csv", details)
    _write_csv(output / "node-query-runs.csv", node_details)
    _write_csv(output / "summary.csv", summaries)
    metadata = _metadata(config, endpoints, target, suite, validate_results)
    metadata["category_order" if cumulative else "scale_users"] = list(config.category_order if cumulative else config.scale_users)
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if validations:
        invalid = [item for item in validations if not item["valid"]]
        if invalid:
            invalid_points = {
                (
                    item.get("reasoner"), item.get("synthetic_users", 0),
                    item.get("repetition", ""), item.get("stage", ""),
                )
                for item in invalid
            }
            for row in summaries:
                key = (
                    row.get("reasoner"), row.get("synthetic_users", 0),
                    row.get("repetition", ""), row.get("stage", ""),
                )
                if key in invalid_points and row.get("status") == "completed":
                    row["status"] = "invalid_results"
                    row["error"] = "Distributed query results differ from canonical reference"
            _write_csv(output / "summary.csv", summaries)
        _write_csv(output / "result-validation.csv", validations)
        if invalid:
            sample = ", ".join(f"{item['reasoner']}:{item['query_id']}" for item in invalid[:8])
            raise RuntimeError(f"Distributed result validation failed ({len(invalid)} rows): {sample}")
    completed = sum(row.get("status") == "completed" for row in summaries)
    censored = sum(row.get("status") == "timeout" for row in summaries)
    skipped = sum(row.get("status") == "skipped_after_timeout" for row in summaries)
    print(f"[{target}-distributed-{suite}] status=completed completed_points={completed} "
          f"timeout_points={censored} skipped_points={skipped} output={output}", flush=True)
    return output


def export_fragments(
    config: BenchmarkConfig,
    users: int,
    output_dir: Path,
    *,
    topology=None,
) -> list[Path]:
    from ..partitioning import build_fragments, write_fragments

    started = perf_counter_ns()
    fragments = build_fragments(config, users, topology=topology)
    paths = write_fragments(fragments, output_dir)
    manifest = {
        **release_identity(),
        "execution_policy": execution_metadata(),
        "reasoner_backends": {name: reasoner_provenance(name) for name in config.reasoners},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "synthetic_users": users,
        "node_count": len(fragments.graphs),
        "logical_triples": len(fragments.union()),
        "logical_substrate_triples": fragments.substrate_triples,
        "sensitive_resources": len(fragments.sensitive_resources),
        "fragments": {
            role: {
                "path": str((output_dir / f"{role}.ttl").resolve()),
                "triples": len(graph),
                "substrate_triples": (
                    fragments.substrate_triples_by_role[role]
                ),
                "profile": fragments.placement_profiles[role],
            }
            for role, graph in fragments.graphs.items()
        },
        "generation_ms": (perf_counter_ns() - started) / 1_000_000,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return [*paths, manifest_path]
