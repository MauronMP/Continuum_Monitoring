"""Coordinator for replicated elastic continuum benchmarks."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from http.client import RemoteDisconnected
import json
from pathlib import Path
import platform
from time import monotonic, perf_counter_ns, sleep
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import BenchmarkConfig
from .budget import (
    PhaseBudgetTimeout,
    error_text,
    failure_status,
    is_boundary_failure,
)
from .csv_utils import write_dict_rows
from .protocol import worker_health_error
from .queries import QuerySpec, by_categories, load_catalog
from .specification import release_identity
from .topology import (
    TIER_ORDER,
    TopologyNode,
    default_categories,
    infer_tier,
)


@dataclass(frozen=True)
class Endpoint:
    url: str
    role: str
    tier: str = ""
    authority: bool = False
    categories: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.tier:
            object.__setattr__(self, "tier", infer_tier(self.role))
        if not self.categories:
            object.__setattr__(
                self,
                "categories",
                default_categories(self.tier),
            )
        if not self.authority and self.tier in {"edge", "iot"}:
            object.__setattr__(self, "authority", True)

    @property
    def node_id(self) -> str:
        return self.role


CLOUD_CATEGORIES = {
    "semantic_schema",
    "decision",
    "policy_governance",
    "validation",
}
FOG_CATEGORIES = {
    "topology",
    "data_lifecycle",
    "trust",
    "adaptation",
    "delegation",
    "federation",
    "audit_temporal",
}
EDGE_CATEGORIES = {
    "observability",
    "identity_consent",
    "security_identity",
    "context_zones",
    "wellbeing",
}

# Fallback for internal callers without an explicit benchmark configuration.
# Public runners use the TOML value and record an exceeded ceiling as censored.
DISTRIBUTED_REQUEST_TIMEOUT_SECONDS = 60.0
DISTRIBUTED_REQUEST_RETRIES = 0


def _payload_hint(payload: dict[str, Any]) -> str:
    query_ids = payload.get("query_ids")
    if isinstance(query_ids, list):
        values = [str(value) for value in query_ids]
        shown = ",".join(values[:12])
        suffix = f",...(+{len(values) - 12})" if len(values) > 12 else ""
        return f" query_ids={shown}{suffix}"
    return ""


def _request(
    url: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 300.0,
    retries: int = 0,
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request_url = f"{url.rstrip('/')}{path}"
    for attempt in range(retries + 1):
        request = Request(
            request_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="GET" if payload is None else "POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                result = json.loads(response.read())
                if isinstance(result, dict):
                    result["_coordinator_attempts"] = attempt + 1
                return result
        except HTTPError:
            # Application errors are deterministic and must not be hidden by
            # transport retries.
            raise
        except (
            ConnectionError,
            OSError,
            RemoteDisconnected,
            TimeoutError,
            URLError,
        ) as error:
            if attempt >= retries:
                raise
            delay_seconds = 0.5 * (2**attempt)
            print(
                "[distributed-http] "
                f"path={path} endpoint={url.rstrip('/')} "
                f"attempt={attempt + 1}/{retries + 1} "
                f"status=retrying delay_s={delay_seconds:.1f} "
                f"error={type(error).__name__}",
                flush=True,
            )
            sleep(delay_seconds)
    raise AssertionError("unreachable")


def discover(
    urls: Iterable[str],
    expected_nodes: Iterable[TopologyNode] | None = None,
    expected_topology_fingerprint: str | None = None,
) -> list[Endpoint]:
    expected_by_url = {
        node.endpoint.rstrip("/"): node for node in (expected_nodes or ())
    }
    endpoints = []
    for url in urls:
        normalized_url = url.rstrip("/")
        expected = expected_by_url.get(normalized_url)
        health = _request(url, "/health", timeout=5.0, retries=1)
        contract_error = worker_health_error(
            health,
            expected_node_id=expected.node_id if expected else None,
            expected_tier=expected.tier if expected else None,
            expected_authority=expected.authority if expected else None,
            expected_categories=expected.categories if expected else None,
            expected_topology_fingerprint=(
                expected_topology_fingerprint if expected else None
            ),
        )
        if contract_error is not None:
            raise RuntimeError(
                f"Incompatible continuum worker at {url}: {contract_error}. "
                "Stop the service occupying that port, or use a different "
                "physical-node port and redeploy."
            )
        endpoints.append(
            Endpoint(
                url=normalized_url,
                role=str(health.get("node_id", health["role"])),
                tier=str(health["tier"]),
                authority=(
                    expected.authority
                    if expected
                    else bool(health.get("authority", False))
                ),
                categories=(
                    expected.categories
                    if expected
                    else tuple(map(str, health.get("categories", ())))
                ),
            )
        )
    roles = [endpoint.role for endpoint in endpoints]
    endpoint_urls = [endpoint.url for endpoint in endpoints]
    if not endpoints:
        raise ValueError("At least one continuum endpoint is required")
    if len(roles) != len(set(roles)):
        raise ValueError(f"Duplicate continuum node ids: {roles}")
    if len(endpoint_urls) != len(set(endpoint_urls)):
        raise ValueError(f"Duplicate continuum endpoints: {endpoint_urls}")
    if expected_by_url and set(endpoint_urls) != set(expected_by_url):
        missing = sorted(set(expected_by_url) - set(endpoint_urls))
        extra = sorted(set(endpoint_urls) - set(expected_by_url))
        raise ValueError(
            f"Endpoint list does not match configured topology; "
            f"missing={missing}, extra={extra}"
        )
    return endpoints


def _parallel(
    endpoints: list[Endpoint],
    path: str,
    payloads: dict[str, dict[str, Any]],
    *,
    phase: str | None = None,
    timeout: float = DISTRIBUTED_REQUEST_TIMEOUT_SECONDS,
    retries: int = DISTRIBUTED_REQUEST_RETRIES,
) -> tuple[float, dict[str, dict[str, Any]]]:
    started = perf_counter_ns()
    results: dict[str, dict[str, Any]] = {}
    phase_name = phase or path.strip("/") or "request"
    with ThreadPoolExecutor(max_workers=len(endpoints)) as executor:
        submitted_at: dict[str, int] = {}
        futures = {
            executor.submit(
                _request,
                endpoint.url,
                path,
                payloads[endpoint.url],
                timeout,
                retries,
            ): endpoint
            for endpoint in endpoints
            if endpoint.url in payloads
        }
        for endpoint in futures.values():
            submitted_at[endpoint.url] = perf_counter_ns()
        for future in as_completed(futures):
            endpoint = futures[future]
            endpoint_ms = (
                perf_counter_ns() - submitted_at[endpoint.url]
            ) / 1_000_000
            try:
                results[endpoint.url] = future.result()
            except Exception as error:
                hint = _payload_hint(payloads[endpoint.url])
                detail = f";{hint}" if hint else ""
                print(
                    "[distributed-node] "
                    f"phase={phase_name} role={endpoint.role} "
                    f"endpoint={endpoint.url} status=failed "
                    f"elapsed_ms={endpoint_ms:.2f} "
                    f"error={type(error).__name__}: {error}{hint}",
                    flush=True,
                )
                raise RuntimeError(
                    f"Distributed phase {phase_name!r} failed on "
                    f"role={endpoint.role} endpoint={endpoint.url} after "
                    f"{endpoint_ms:.2f} ms: {type(error).__name__}: {error}"
                    f"{detail}"
                ) from error
            print(
                "[distributed-node] "
                f"phase={phase_name} role={endpoint.role} "
                f"endpoint={endpoint.url} status=done "
                f"elapsed_ms={endpoint_ms:.2f}",
                flush=True,
            )
    wall_ms = (perf_counter_ns() - started) / 1_000_000
    return wall_ms, results


def _assignment(
    specs: list[QuerySpec],
    endpoints: list[Endpoint],
) -> dict[str, list[QuerySpec]]:
    assigned = {endpoint.url: [] for endpoint in endpoints}
    category_indexes: dict[str, int] = {}
    for spec in specs:
        candidates = sorted(
            (
                endpoint
                for endpoint in endpoints
                if spec.category in endpoint.categories
            ),
            key=lambda endpoint: (
                TIER_ORDER[endpoint.tier],
                endpoint.role,
            ),
        )
        if not candidates:
            raise ValueError(
                f"No active node declares category {spec.category!r}; "
                "add it to a node in the selected architecture layer file"
            )
        index = category_indexes.get(spec.category, 0)
        endpoint = candidates[index % len(candidates)]
        category_indexes[spec.category] = index + 1
        assigned[endpoint.url].append(spec)
    return assigned


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_dict_rows(
        path,
        rows,
        empty_message=f"Cannot write empty CSV: {path}",
    )


def _metadata(
    config: BenchmarkConfig,
    endpoints: list[Endpoint],
    suite: str,
) -> dict[str, Any]:
    return {
        **release_identity(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "suite": suite,
        "mode": "docker-replicated-query-routing",
        "endpoints": [
            {
                "url": endpoint.url,
                "node_id": endpoint.role,
                "role": endpoint.role,
                "tier": endpoint.tier,
                "authority": endpoint.authority,
            }
            for endpoint in endpoints
        ],
        "reasoners": list(config.reasoners),
        "repetitions": config.repetitions,
        "seed": config.seed,
        "replica_count": len(endpoints),
        "node_count": len(endpoints),
        "execution_limits": {
            "phase_timeout_seconds": config.limits.phase_timeout_seconds,
            "point_timeout_seconds": config.limits.point_timeout_seconds,
            "stop_scaling_after_timeout": (
                config.limits.stop_scaling_after_timeout
            ),
            "timeout_semantics": "right-censored with monotone early stop",
        },
    }


def _prepare(
    config: BenchmarkConfig,
    endpoints: list[Endpoint],
    reasoner: str,
    users: int,
    seed: int,
) -> tuple[float, dict[str, dict[str, Any]]]:
    transport = config.distributed
    timeout = min(
        transport.request_timeout_seconds,
        config.limits.point_timeout_seconds,
    )
    payloads = {
        endpoint.url: {
            "reasoner": reasoner,
            "users": users,
            "seed": seed,
            "phase_timeout_seconds": (
                timeout - transport.worker_timeout_margin_seconds
            ),
        }
        for endpoint in endpoints
    }
    return _parallel(
        endpoints,
        "/prepare",
        payloads,
        phase="prepare",
        timeout=timeout,
        retries=transport.request_retries,
    )


def _combine_query_responses(
    responses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Combine sequential bounded query batches from one worker."""

    if not responses:
        raise ValueError("At least one query batch response is required")
    first = responses[0]
    combined = {
        key: first[key]
        for key in ("role", "mode", "reasoner", "synthetic_users")
    }
    for key in (
        "query_wall_ms",
        "query_cpu_ms",
        "process_cpu_ms",
        "disk_read_bytes",
        "disk_write_bytes",
        "request_bytes",
        "response_bytes",
    ):
        combined[key] = sum(float(item.get(key, 0)) for item in responses)
    combined["query_count"] = sum(
        int(item.get("query_count", 0)) for item in responses
    )
    for key in (
        "disk_read_bytes",
        "disk_write_bytes",
        "request_bytes",
        "response_bytes",
    ):
        combined[key] = int(combined[key])
    combined["current_rss_kib"] = int(
        responses[-1].get("current_rss_kib", 0)
    )
    combined["peak_rss_kib"] = max(
        int(item.get("peak_rss_kib", 0)) for item in responses
    )
    combined["measurements"] = [
        measurement
        for item in responses
        for measurement in item.get("measurements", [])
    ]
    combined["_coordinator_attempts"] = 1 + sum(
        max(int(item.get("_coordinator_attempts", 1)) - 1, 0)
        for item in responses
    )
    combined["query_batch_count"] = len(responses)
    return combined


def _query(
    config: BenchmarkConfig,
    endpoints: list[Endpoint],
    assignment: dict[str, list[QuerySpec]],
    *,
    timeout_seconds: float | None = None,
    phase: str = "queries",
) -> tuple[float, dict[str, dict[str, Any]]]:
    transport = config.distributed
    point_timeout = min(
        timeout_seconds or config.limits.point_timeout_seconds,
        config.limits.point_timeout_seconds,
    )
    started = monotonic()
    batches = {
        url: [
            specs[index : index + transport.query_batch_size]
            for index in range(0, len(specs), transport.query_batch_size)
        ]
        for url, specs in assignment.items() if specs
    }
    rounds = max((len(value) for value in batches.values()), default=0)
    collected: dict[str, list[dict[str, Any]]] = {
        url: [] for url in batches
    }
    wall_ms = 0.0
    endpoint_by_url = {endpoint.url: endpoint for endpoint in endpoints}
    for index in range(rounds):
        remaining = point_timeout - (monotonic() - started)
        request_timeout = min(transport.request_timeout_seconds, remaining)
        if request_timeout <= transport.worker_timeout_margin_seconds:
            raise PhaseBudgetTimeout(
                f"{phase} exceeded its {point_timeout:.1f}s point budget"
            )
        payloads = {}
        labels = []
        for url, endpoint_batches in batches.items():
            if index >= len(endpoint_batches):
                continue
            query_ids = [spec.id for spec in endpoint_batches[index]]
            payloads[url] = {
                "query_ids": query_ids,
                "phase_timeout_seconds": (
                    request_timeout
                    - transport.worker_timeout_margin_seconds
                ),
            }
            labels.append(f"{endpoint_by_url[url].role}:{len(query_ids)}")
        print(
            f"[distributed-batch] phase={phase} "
            f"batch={index + 1}/{rounds} nodes={','.join(labels)} "
            "status=running",
            flush=True,
        )
        batch_wall_ms, responses = _parallel(
            endpoints,
            "/queries",
            payloads,
            phase=f"{phase}-batch-{index + 1}-of-{rounds}",
            timeout=request_timeout,
            retries=transport.request_retries,
        )
        wall_ms += batch_wall_ms
        for url, response in responses.items():
            collected[url].append(response)
    return wall_ms, {
        url: _combine_query_responses(items)
        for url, items in collected.items()
    }


def _detail_rows(
    responses: dict[str, dict[str, Any]],
    endpoint_by_url: dict[str, Endpoint],
    common: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    for url, response in responses.items():
        endpoint = endpoint_by_url[url]
        for measurement in response["measurements"]:
            rows.append(
                {
                    **common,
                    "endpoint": url,
                    "role": endpoint.role,
                    "tier_name": endpoint.tier,
                    "status": "completed",
                    "censored": False,
                    **measurement,
                }
            )
    return rows


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
        "node_count": node_count,
        "query_count": query_count,
        "prepare_wall_ms": "",
        "query_wall_ms": "",
        "total_wall_ms": lower_bound_ms if status == "timeout" else "",
        "status": status,
        "censored": True,
        "censored_lower_bound_ms": lower_bound_ms,
        "failed_phase": phase,
        "timeout_seconds": timeout_seconds,
        "error": error,
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


def run_docker_cumulative(
    config: BenchmarkConfig,
    endpoint_urls: list[str],
    output_root: Path,
    *,
    topology=None,
) -> Path:
    endpoints = discover(
        endpoint_urls,
        topology.active_nodes if topology is not None else None,
        topology.fingerprint if topology is not None else None,
    )
    node_count = len(endpoints)
    endpoint_by_url = {endpoint.url: endpoint for endpoint in endpoints}
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    details: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    topology_stopped = False
    stop_reason = ""

    for reasoner in config.reasoners:
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
                    summaries.append(
                        _censored_summary(
                            common,
                            node_count,
                            len(by_categories(specs, set(config.category_order[:stage]))),
                            "skipped_after_timeout",
                            "early-stop",
                            stop_reason,
                            config.limits.point_timeout_seconds,
                            0.0,
                        )
                    )
                    details.append(
                        _censored_detail(
                            common,
                            "skipped_after_timeout",
                            "early-stop",
                            stop_reason,
                            config.limits.point_timeout_seconds,
                        )
                    )
                continue
            print(
                f"[docker-cumulative] reasoner={reasoner} "
                f"repetition={repetition}/{config.repetitions} "
                f"nodes={node_count} phase=prepare status=running",
                flush=True,
            )
            prepare_started = monotonic()
            try:
                prepare_wall_ms, prepared = _prepare(
                    config, endpoints, reasoner, 0, config.seed
                )
            except Exception as error:
                if not is_boundary_failure(error):
                    raise
                status = failure_status(error)
                stop_reason = error_text(error)
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
                            node_count,
                            len(by_categories(specs, set(config.category_order[:stage]))),
                            row_status,
                            "prepare",
                            stop_reason,
                            config.limits.point_timeout_seconds,
                            monotonic() - prepare_started if stage == 1 else 0.0,
                        )
                    )
                    details.append(
                        _censored_detail(
                            common,
                            row_status,
                            "prepare",
                            stop_reason,
                            config.limits.point_timeout_seconds,
                        )
                    )
                topology_stopped = config.limits.stop_scaling_after_timeout
                continue
            active: set[str] = set()
            for stage, category in enumerate(config.category_order, start=1):
                active.add(category)
                active_specs = by_categories(specs, active)
                assignment = _assignment(active_specs, endpoints)
                print(
                    f"[docker-cumulative] reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    f"stage={stage}/{len(config.category_order)} "
                    f"category={category} queries={len(active_specs)} "
                    "status=running",
                    flush=True,
                )
                common = {
                    "reasoner": reasoner,
                    "repetition": repetition,
                    "stage": stage,
                    "added_category": category,
                }
                query_started = monotonic()
                try:
                    query_wall_ms, responses = _query(
                        config,
                        endpoints,
                        assignment,
                        timeout_seconds=max(
                            config.limits.point_timeout_seconds
                            - prepare_wall_ms / 1000,
                            0.001,
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
                            node_count,
                            len(active_specs),
                            status,
                            "queries",
                            stop_reason,
                            config.limits.point_timeout_seconds,
                            prepare_wall_ms / 1000
                            + monotonic()
                            - query_started,
                        )
                    )
                    details.append(
                        _censored_detail(
                            common,
                            status,
                            "queries",
                            stop_reason,
                            config.limits.point_timeout_seconds,
                        )
                    )
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
                                node_count,
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
                        details.append(
                            _censored_detail(
                                skipped_common,
                                "skipped_after_timeout",
                                "early-stop",
                                stop_reason,
                                config.limits.point_timeout_seconds,
                            )
                        )
                    topology_stopped = (
                        config.limits.stop_scaling_after_timeout
                    )
                    break
                details.extend(
                    _detail_rows(responses, endpoint_by_url, common)
                )
                node_query_ms = sum(
                    float(response["query_cpu_ms"])
                    for response in responses.values()
                )
                summary = {
                    **common,
                    "node_count": node_count,
                    "query_count": len(active_specs),
                    "prepare_wall_ms": prepare_wall_ms,
                    "node_reasoning_ms_sum": sum(
                        float(item["reasoning_ms"])
                        for item in prepared.values()
                    ),
                    "max_node_reasoning_ms": max(
                        float(item["reasoning_ms"])
                        for item in prepared.values()
                    ),
                    "query_wall_ms": query_wall_ms,
                    "node_query_ms_sum": node_query_ms,
                    "total_wall_ms": prepare_wall_ms + query_wall_ms,
                    "input_triples_per_replica": next(
                        iter(prepared.values())
                    )["input_triples"],
                    "output_triples_per_replica": next(
                        iter(prepared.values())
                    )["output_triples"],
                    "status": "completed",
                    "censored": False,
                }
                summaries.append(summary)
                print(
                    f"[docker-cumulative] reasoner={reasoner} "
                    f"stage={stage}/{len(config.category_order)} "
                    f"category={category} status=done "
                    f"wall_ms={summary['total_wall_ms']:.2f}",
                    flush=True,
                )

    output = output_root / "cumulative"
    _write_csv(output / "query-runs.csv", details)
    _write_csv(output / "summary.csv", summaries)
    metadata = _metadata(config, endpoints, "cumulative")
    metadata["category_order"] = list(config.category_order)
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


def run_docker_scalability(
    config: BenchmarkConfig,
    endpoint_urls: list[str],
    output_root: Path,
    *,
    topology=None,
) -> Path:
    endpoints = discover(
        endpoint_urls,
        topology.active_nodes if topology is not None else None,
        topology.fingerprint if topology is not None else None,
    )
    node_count = len(endpoints)
    endpoint_by_url = {endpoint.url: endpoint for endpoint in endpoints}
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    assignment = _assignment(specs, endpoints)
    details: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    topology_stopped = False
    stop_reason = ""

    for block, users in enumerate(config.scale_users, start=1):
        for reasoner in config.reasoners:
            for repetition in range(1, config.repetitions + 1):
                common = {
                    "reasoner": reasoner,
                    "repetition": repetition,
                    "synthetic_users": users,
                    "synthetic_triples": "",
                }
                if topology_stopped:
                    summaries.append(
                        _censored_summary(
                            common,
                            node_count,
                            len(specs),
                            "skipped_after_timeout",
                            "early-stop",
                            stop_reason,
                            config.limits.point_timeout_seconds,
                            0.0,
                        )
                    )
                    details.append(
                        _censored_detail(
                            common,
                            "skipped_after_timeout",
                            "early-stop",
                            stop_reason,
                            config.limits.point_timeout_seconds,
                        )
                    )
                    continue
                print(
                    f"[docker-scalability] block={block}/{len(config.scale_users)} "
                    f"users={users} reasoner={reasoner} "
                    f"repetition={repetition}/{config.repetitions} "
                    f"nodes={node_count} phase=prepare status=running",
                    flush=True,
                )
                point_started = monotonic()
                phase = "prepare"
                try:
                    prepare_wall_ms, prepared = _prepare(
                        config, endpoints, reasoner, users, config.seed
                    )
                    phase = "queries"
                    query_wall_ms, responses = _query(
                        config,
                        endpoints,
                        assignment,
                        timeout_seconds=max(
                            config.limits.point_timeout_seconds
                            - (monotonic() - point_started),
                            0.001,
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
                            node_count,
                            len(specs),
                            status,
                            phase,
                            stop_reason,
                            config.limits.point_timeout_seconds,
                            monotonic() - point_started,
                        )
                    )
                    details.append(
                        _censored_detail(
                            common,
                            status,
                            phase,
                            stop_reason,
                            config.limits.point_timeout_seconds,
                        )
                    )
                    topology_stopped = (
                        config.limits.stop_scaling_after_timeout
                    )
                    print(
                        f"[docker-scalability] block={block} users={users} "
                        f"reasoner={reasoner} phase={phase} status={status} "
                        f"limit_s={config.limits.point_timeout_seconds:g}; "
                        "remaining larger points will be skipped",
                        flush=True,
                    )
                    continue
                common["synthetic_triples"] = next(
                    iter(prepared.values())
                )["synthetic_triples"]
                details.extend(
                    _detail_rows(responses, endpoint_by_url, common)
                )
                summary = {
                    **common,
                    "node_count": node_count,
                    "query_count": len(specs),
                    "prepare_wall_ms": prepare_wall_ms,
                    "node_generation_ms_sum": sum(
                        float(item["generation_ms"])
                        for item in prepared.values()
                    ),
                    "node_reasoning_ms_sum": sum(
                        float(item["reasoning_ms"])
                        for item in prepared.values()
                    ),
                    "max_node_reasoning_ms": max(
                        float(item["reasoning_ms"])
                        for item in prepared.values()
                    ),
                    "query_wall_ms": query_wall_ms,
                    "node_query_ms_sum": sum(
                        float(response["query_cpu_ms"])
                        for response in responses.values()
                    ),
                    "total_wall_ms": prepare_wall_ms + query_wall_ms,
                    "input_triples_per_replica": next(
                        iter(prepared.values())
                    )["input_triples"],
                    "output_triples_per_replica": next(
                        iter(prepared.values())
                    )["output_triples"],
                    "status": "completed",
                    "censored": False,
                }
                summaries.append(summary)
                print(
                    f"[docker-scalability] block={block}/{len(config.scale_users)} "
                    f"users={users} reasoner={reasoner} status=done "
                    f"queries={len(specs)} wall_ms={summary['total_wall_ms']:.2f}",
                    flush=True,
                )

    output = output_root / "scalability"
    _write_csv(output / "query-runs.csv", details)
    _write_csv(output / "summary.csv", summaries)
    metadata = _metadata(config, endpoints, "scalability")
    metadata["scale_users"] = list(config.scale_users)
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output
