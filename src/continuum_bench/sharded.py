"""Privacy-aware benchmark coordinator for Docker and physical continuum nodes."""

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
from .budget import (
    PhaseBudgetTimeout,
    error_text,
    failure_status,
    is_boundary_failure,
    local_phase_timeout,
    remaining_seconds,
)
from .distributed import (
    Endpoint,
    _combine_query_responses,
    _parallel,
    _write_csv,
    discover,
)
from .ontology import load_graph
from .queries import (
    QuerySpec,
    by_categories,
    execute_query_detailed,
    load_catalog,
    result_digest,
)
from .reasoners import materialize
from .specification import release_identity
from .synthetic import add_synthetic_data
from .topology import TIER_ORDER, authority_index


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
    transport = config.distributed
    timeout = min(
        timeout_seconds or config.limits.point_timeout_seconds,
        transport.request_timeout_seconds,
    )
    if timeout <= transport.worker_timeout_margin_seconds:
        raise PhaseBudgetTimeout("no time remains for partitioned prepare")
    return _parallel(
        endpoints,
        "/prepare",
        {
            endpoint.url: {
                "reasoner": reasoner,
                "users": users,
                "seed": seed,
                "mode": "partitioned",
                "phase_timeout_seconds": (
                    timeout
                    - transport.worker_timeout_margin_seconds
                ),
            }
            for endpoint in endpoints
        },
        phase="partitioned-prepare",
        timeout=timeout,
        retries=transport.request_retries,
    )


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
    )
    started = monotonic()
    batch_size = transport.query_batch_size
    batches = {
        url: [
            specs[index : index + batch_size]
            for index in range(0, len(specs), batch_size)
        ]
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
        remaining = point_timeout - (monotonic() - started)
        request_timeout = min(transport.request_timeout_seconds, remaining)
        if request_timeout <= transport.worker_timeout_margin_seconds:
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
            f"nodes={','.join(descriptions)} status=running",
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
                "query_id": item["query_id"],
                "execution_scope": item["execution_scope"],
                "distributed_count": item["result_count"],
                "monolith_count": expected_count,
                "distributed_ask": item["ask_result"],
                "monolith_ask": expected_ask,
                "distributed_digest": item["result_digest"],
                "monolith_digest": expected_digest,
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
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "suite": suite,
        "mode": f"{target}-elastic-authority-sharded",
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
        "timing_excludes_monolith_validation": True,
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


def run_sharded_cumulative(
    config: BenchmarkConfig,
    endpoint_urls: list[str],
    output_root: Path,
    *,
    target: str,
    validate_results: bool = True,
    topology=None,
) -> Path:
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
    baseline_cache: dict[
        str, dict[str, tuple[int, bool | None, str]]
    ] = {}
    topology_stopped = False
    stop_reason = ""

    for reasoner in config.reasoners:
        if validate_results and not topology_stopped:
            print(
                f"[{target}-sharded-cumulative] reasoner={reasoner} "
                "phase=monolith-validation status=running",
                flush=True,
            )
            try:
                with local_phase_timeout(
                    config.limits.point_timeout_seconds
                ):
                    baseline_cache[reasoner] = _baseline_counts(
                        config, specs, reasoner, 0
                    )
            except PhaseBudgetTimeout:
                print(
                    f"[{target}-sharded-cumulative] reasoner={reasoner} "
                    "phase=monolith-validation status=timeout; "
                    "distributed timing will continue without oracle",
                    flush=True,
                )
        for repetition in range(1, config.repetitions + 1):
            if topology_stopped:
                for stage, category in enumerate(
                    config.category_order, start=1
                ):
                    common = {
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "stage": stage,
                        "added_category": category,
                    }
                    row = _censored_summary(
                        common,
                        len(endpoints),
                        len(by_categories(specs, set(config.category_order[:stage]))),
                        "skipped_after_timeout",
                        "early-stop",
                        stop_reason,
                        config.limits.point_timeout_seconds,
                        0.0,
                    )
                    summaries.append(row)
                    detail = _censored_detail(
                        common,
                        "skipped_after_timeout",
                        "early-stop",
                        stop_reason,
                        config.limits.point_timeout_seconds,
                    )
                    details.append(detail)
                    node_details.append(detail)
                continue
            print(
                f"[{target}-sharded-cumulative] reasoner={reasoner} "
                f"repetition={repetition}/{config.repetitions} "
                f"nodes={len(endpoints)} phase=partitioned-prepare status=running",
                flush=True,
            )
            prepare_started = monotonic()
            try:
                prepare_wall_ms, prepared = _prepare(
                    config,
                    endpoints,
                    reasoner,
                    0,
                    config.seed,
                    timeout_seconds=config.limits.point_timeout_seconds,
                )
            except Exception as error:
                if not is_boundary_failure(error):
                    raise
                stop_reason = error_text(error)
                status = failure_status(error)
                for stage, category in enumerate(
                    config.category_order, start=1
                ):
                    common = {
                        "reasoner": reasoner,
                        "repetition": repetition,
                        "stage": stage,
                        "added_category": category,
                    }
                    row_status = status if stage == 1 else "skipped_after_timeout"
                    summaries.append(
                        _censored_summary(
                            common,
                            len(endpoints),
                            len(by_categories(specs, set(config.category_order[:stage]))),
                            row_status,
                            "partitioned-prepare",
                            stop_reason,
                            config.limits.point_timeout_seconds,
                            monotonic() - prepare_started if stage == 1 else 0.0,
                        )
                    )
                    detail = _censored_detail(
                        common,
                        row_status,
                        "partitioned-prepare",
                        stop_reason,
                        config.limits.point_timeout_seconds,
                    )
                    details.append(detail)
                    node_details.append(detail)
                topology_stopped = config.limits.stop_scaling_after_timeout
                print(
                    f"[{target}-sharded-cumulative] reasoner={reasoner} "
                    f"phase=partitioned-prepare status={status} "
                    f"limit_s={config.limits.point_timeout_seconds:g}",
                    flush=True,
                )
                continue
            active: set[str] = set()
            for stage, category in enumerate(config.category_order, start=1):
                active.add(category)
                active_specs = by_categories(specs, active)
                assignment = _assignment(active_specs, endpoints)
                loads = ",".join(
                    f"{endpoint.role}:{len(assignment[endpoint.url])}"
                    for endpoint in endpoints
                )
                print(
                    f"[{target}-sharded-cumulative] reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    f"stage={stage}/{len(config.category_order)} "
                    f"category={category} queries={len(active_specs)} "
                    f"sources={loads} status=running",
                    flush=True,
                )
                common = {
                    "reasoner": reasoner,
                    "repetition": repetition,
                    "stage": stage,
                    "added_category": category,
                }
                query_budget = max(
                    config.limits.point_timeout_seconds
                    - prepare_wall_ms / 1000,
                    0.001,
                )
                query_started = monotonic()
                try:
                    query_wall_ms, responses = _query(
                        config,
                        endpoints,
                        assignment,
                        timeout_seconds=query_budget,
                    )
                except Exception as error:
                    if not is_boundary_failure(error):
                        raise
                    stop_reason = error_text(error)
                    status = failure_status(error)
                    summaries.append(
                        _censored_summary(
                            common,
                            len(endpoints),
                            len(active_specs),
                            status,
                            "partitioned-queries",
                            stop_reason,
                            config.limits.point_timeout_seconds,
                            prepare_wall_ms / 1000
                            + monotonic()
                            - query_started,
                        )
                    )
                    detail = _censored_detail(
                        common,
                        status,
                        "partitioned-queries",
                        stop_reason,
                        config.limits.point_timeout_seconds,
                    )
                    details.append(detail)
                    node_details.append(detail)
                    for skipped_stage in range(
                        stage + 1, len(config.category_order) + 1
                    ):
                        skipped_common = {
                            "reasoner": reasoner,
                            "repetition": repetition,
                            "stage": skipped_stage,
                            "added_category": config.category_order[
                                skipped_stage - 1
                            ],
                        }
                        summaries.append(
                            _censored_summary(
                                skipped_common,
                                len(endpoints),
                                len(
                                    by_categories(
                                        specs,
                                        set(config.category_order[:skipped_stage]),
                                    )
                                ),
                                "skipped_after_timeout",
                                "early-stop",
                                stop_reason,
                                config.limits.point_timeout_seconds,
                                0.0,
                            )
                        )
                        skipped_detail = _censored_detail(
                            skipped_common,
                            "skipped_after_timeout",
                            "early-stop",
                            stop_reason,
                            config.limits.point_timeout_seconds,
                        )
                        details.append(skipped_detail)
                        node_details.append(skipped_detail)
                    topology_stopped = (
                        config.limits.stop_scaling_after_timeout
                    )
                    print(
                        f"[{target}-sharded-cumulative] reasoner={reasoner} "
                        f"stage={stage} status={status} "
                        f"limit_s={config.limits.point_timeout_seconds:g}",
                        flush=True,
                    )
                    break
                merged, raw = _merge_responses(
                    active_specs, endpoints, responses, common
                )
                details.extend(merged)
                node_details.extend(raw)
                summaries.append(
                    _summary(
                        common,
                        len(active_specs),
                        prepare_wall_ms,
                        query_wall_ms,
                        prepared,
                        responses,
                    )
                )
                if reasoner in baseline_cache:
                    validations.extend(
                        _validation_rows(merged, baseline_cache[reasoner])
                    )
                print(
                    f"[{target}-sharded-cumulative] reasoner={reasoner} "
                    f"stage={stage}/{len(config.category_order)} "
                    f"category={category} status=done "
                    f"wall_ms={prepare_wall_ms + query_wall_ms:.2f}",
                    flush=True,
                )

    output = output_root / "cumulative"
    _write_csv(output / "query-runs.csv", details)
    _write_csv(output / "node-query-runs.csv", node_details)
    _write_csv(output / "summary.csv", summaries)
    if validations:
        _write_csv(output / "result-validation.csv", validations)
        invalid = [item for item in validations if not item["valid"]]
        if invalid:
            sample = ", ".join(
                f"{item['reasoner']}:{item['query_id']}"
                for item in invalid[:8]
            )
            raise RuntimeError(
                f"Distributed result validation failed ({len(invalid)} rows): "
                f"{sample}"
            )
    metadata = _metadata(
        config, endpoints, target, "cumulative", validate_results
    )
    metadata["category_order"] = list(config.category_order)
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


def run_sharded_scalability(
    config: BenchmarkConfig,
    endpoint_urls: list[str],
    output_root: Path,
    *,
    target: str,
    validate_results: bool = True,
    topology=None,
) -> Path:
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
    topology_stopped = False
    stop_reason = ""

    for block, users in enumerate(config.scale_users, start=1):
        for reasoner in config.reasoners:
            baseline = None
            if validate_results and not topology_stopped:
                print(
                    f"[{target}-sharded-scalability] "
                    f"block={block}/{len(config.scale_users)} users={users} "
                    f"reasoner={reasoner} phase=monolith-validation "
                    "status=running",
                    flush=True,
                )
                try:
                    with local_phase_timeout(
                        config.limits.point_timeout_seconds
                    ):
                        baseline = _baseline_counts(
                            config, specs, reasoner, users
                        )
                except PhaseBudgetTimeout as error:
                    print(
                        f"[{target}-sharded-scalability] block={block} "
                        f"users={users} reasoner={reasoner} "
                        "phase=monolith-validation status=timeout "
                        f"limit_s={config.limits.point_timeout_seconds:g}; "
                        "distributed timing will continue without oracle",
                        flush=True,
                    )
            for repetition in range(1, config.repetitions + 1):
                common = {
                    "reasoner": reasoner,
                    "repetition": repetition,
                    "synthetic_users": users,
                    "synthetic_triples": "",
                }
                if topology_stopped:
                    row = _censored_summary(
                        common,
                        len(endpoints),
                        len(specs),
                        "skipped_after_timeout",
                        "early-stop",
                        stop_reason,
                        config.limits.point_timeout_seconds,
                        0.0,
                    )
                    summaries.append(row)
                    detail = _censored_detail(
                        common,
                        "skipped_after_timeout",
                        "early-stop",
                        stop_reason,
                        config.limits.point_timeout_seconds,
                    )
                    details.append(detail)
                    node_details.append(detail)
                    continue
                print(
                    f"[{target}-sharded-scalability] "
                    f"block={block}/{len(config.scale_users)} users={users} "
                    f"reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    f"nodes={len(endpoints)} phase=partitioned-prepare status=running",
                    flush=True,
                )
                point_started = monotonic()
                phase = "partitioned-prepare"
                try:
                    prepare_wall_ms, prepared = _prepare(
                        config,
                        endpoints,
                        reasoner,
                        users,
                        config.seed,
                        timeout_seconds=remaining_seconds(
                            point_started,
                            config.limits.point_timeout_seconds,
                        ),
                    )
                    assignment = _assignment(specs, endpoints)
                    loads = ",".join(
                        f"{endpoint.role}:{len(assignment[endpoint.url])}"
                        for endpoint in endpoints
                    )
                    print(
                        f"[{target}-sharded-scalability] "
                        f"block={block}/{len(config.scale_users)} users={users} "
                        f"reasoner={reasoner} phase=partitioned-queries "
                        f"sources={loads} status=running",
                        flush=True,
                    )
                    phase = "partitioned-queries"
                    query_wall_ms, responses = _query(
                        config,
                        endpoints,
                        assignment,
                        timeout_seconds=remaining_seconds(
                            point_started,
                            config.limits.point_timeout_seconds,
                        ),
                    )
                except Exception as error:
                    if not is_boundary_failure(error):
                        raise
                    status = failure_status(error)
                    stop_reason = error_text(error)
                    summaries.append(
                        _censored_summary(
                            common,
                            len(endpoints),
                            len(specs),
                            status,
                            phase,
                            stop_reason,
                            config.limits.point_timeout_seconds,
                            monotonic() - point_started,
                        )
                    )
                    detail = _censored_detail(
                        common,
                        status,
                        phase,
                        stop_reason,
                        config.limits.point_timeout_seconds,
                    )
                    details.append(detail)
                    node_details.append(detail)
                    topology_stopped = (
                        config.limits.stop_scaling_after_timeout
                    )
                    print(
                        f"[{target}-sharded-scalability] block={block} "
                        f"users={users} reasoner={reasoner} phase={phase} "
                        f"status={status} "
                        f"limit_s={config.limits.point_timeout_seconds:g}; "
                        "remaining larger points will be skipped",
                        flush=True,
                    )
                    continue
                common["synthetic_triples"] = next(
                    iter(prepared.values())
                )["synthetic_triples"]
                merged, raw = _merge_responses(
                    specs, endpoints, responses, common
                )
                details.extend(merged)
                node_details.extend(raw)
                summaries.append(
                    _summary(
                        common,
                        len(specs),
                        prepare_wall_ms,
                        query_wall_ms,
                        prepared,
                        responses,
                    )
                )
                if baseline is not None:
                    validations.extend(_validation_rows(merged, baseline))
                print(
                    f"[{target}-sharded-scalability] "
                    f"block={block}/{len(config.scale_users)} users={users} "
                    f"reasoner={reasoner} status=done "
                    f"wall_ms={prepare_wall_ms + query_wall_ms:.2f}",
                    flush=True,
                )

    output = output_root / "scalability"
    _write_csv(output / "query-runs.csv", details)
    _write_csv(output / "node-query-runs.csv", node_details)
    _write_csv(output / "summary.csv", summaries)
    if validations:
        _write_csv(output / "result-validation.csv", validations)
        invalid = [item for item in validations if not item["valid"]]
        if invalid:
            sample = ", ".join(
                f"{item['reasoner']}:{item['query_id']}"
                for item in invalid[:8]
            )
            raise RuntimeError(
                f"Distributed result validation failed ({len(invalid)} rows): "
                f"{sample}"
            )
    metadata = _metadata(
        config, endpoints, target, "scalability", validate_results
    )
    metadata["scale_users"] = list(config.scale_users)
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


def export_fragments(
    config: BenchmarkConfig,
    users: int,
    output_dir: Path,
    *,
    topology=None,
) -> list[Path]:
    from .partitioning import build_fragments, write_fragments

    started = perf_counter_ns()
    fragments = build_fragments(config, users, topology=topology)
    paths = write_fragments(fragments, output_dir)
    manifest = {
        **release_identity(),
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
