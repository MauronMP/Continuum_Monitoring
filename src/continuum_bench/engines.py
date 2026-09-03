"""Cross-product benchmark for independent RDF and reasoning engines."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import statistics
from time import monotonic, perf_counter_ns
from typing import Any, Iterable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from rdflib import Graph

from .config import BenchmarkConfig
from .budget import (
    error_text,
    failure_status,
    is_boundary_failure,
    remaining_seconds,
)
from .csv_utils import write_dict_rows
from .engine_protocol import ENGINE_PROTOCOL_VERSION, ENGINE_SERVICE
from .ontology import graph_digest, load_graph
from .queries import QuerySpec, by_categories, load_catalog
from .reasoners import REASONING_CONTRACT
from .synthetic import add_synthetic_data
from .specification import release_identity


@dataclass(frozen=True)
class EngineEndpoint:
    url: str
    engine: str
    version: str
    inference_profile: str


def _request(
    url: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"{url.rstrip('/')}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"{request.full_url} returned HTTP {error.code}: {body}"
        ) from error


def discover(urls: Iterable[str], *, timeout: float = 5.0) -> list[EngineEndpoint]:
    endpoints = []
    for url in urls:
        health = _request(url, "/health", timeout=timeout)
        if health.get("status") != "ok":
            raise RuntimeError(f"Unhealthy semantic engine: {url}")
        if health.get("service") != ENGINE_SERVICE:
            raise RuntimeError(
                f"Incompatible semantic engine at {url}: expected service "
                f"{ENGINE_SERVICE!r}, got {health.get('service')!r}"
            )
        if str(health.get("protocol_version", "")) != ENGINE_PROTOCOL_VERSION:
            raise RuntimeError(
                f"Incompatible semantic engine at {url}: expected protocol "
                f"{ENGINE_PROTOCOL_VERSION!r}, got "
                f"{health.get('protocol_version')!r}"
            )
        if (
            health.get("engine") == "rdflib"
            and health.get("reasoning_contract") != REASONING_CONTRACT
        ):
            raise RuntimeError(
                f"Incompatible RDFLib reasoner at {url}: expected "
                f"reasoning_contract={REASONING_CONTRACT!r}, got "
                f"{health.get('reasoning_contract')!r}. Rebuild the Python "
                "engine image to apply the RDFS datatype correction."
            )
        endpoints.append(
            EngineEndpoint(
                url=url.rstrip("/"),
                engine=str(health["engine"]),
                version=str(health["version"]),
                inference_profile=str(health["inference_profile"]),
            )
        )
    names = [endpoint.engine for endpoint in endpoints]
    if len(names) != len(set(names)):
        raise ValueError(f"Duplicate semantic engines: {names}")
    required = {"rdflib", "jena", "rdf4j", "oxigraph"}
    if set(names) != required:
        raise ValueError(
            f"Expected engines={sorted(required)}, got={sorted(names)}"
        )
    return sorted(endpoints, key=lambda endpoint: endpoint.engine)


def _load(
    config: BenchmarkConfig,
) -> tuple[Graph, list[QuerySpec]]:
    graph = load_graph(config.resolve(path) for path in config.ontology_files)
    specs = load_catalog(
        config.resolve(config.query_catalog),
        config.root,
    )
    return graph, specs


def _clone(source: Graph) -> Graph:
    graph = Graph()
    for prefix, namespace in source.namespaces():
        graph.bind(prefix, namespace)
    for triple in source:
        graph.add(triple)
    return graph


def _ntriples(graph: Graph) -> str:
    serialized = graph.serialize(format="nt")
    return (
        serialized.decode("utf-8")
        if isinstance(serialized, bytes)
        else serialized
    )


def _query_payload(
    specs: list[QuerySpec],
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    payload = {
        "queries": [
            {
                "id": spec.id,
                "category": spec.category,
                "tier": spec.tier,
                "kind": spec.kind,
                "text": spec.read(),
            }
            for spec in specs
        ]
    }
    if timeout_seconds is not None:
        payload["phase_timeout_seconds"] = max(timeout_seconds - 1.0, 0.1)
    return payload


def _expectation_ok(spec: QuerySpec, measurement: dict[str, Any]) -> bool:
    count = int(measurement["result_count"])
    ask = measurement.get("ask_result")
    if spec.expectation == "zero_rows":
        return count == 0
    if spec.expectation == "non_empty":
        return count > 0
    if spec.expectation == "true":
        return ask is True
    if spec.expectation == "false":
        return ask is False
    return True


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_dict_rows(
        path,
        rows,
        empty_message=f"Cannot write empty engine benchmark: {path}",
    )


def _write_metadata(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _metadata(
    config: BenchmarkConfig,
    base: Graph,
    endpoints: list[EngineEndpoint],
    suite: str,
    warmups: int,
) -> dict[str, Any]:
    return {
        **release_identity(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suite": suite,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "graph_sha256": graph_digest(base),
        "base_triples": len(base),
        "repetitions": config.repetitions,
        "warmups": warmups,
        "seed": config.seed,
        "engines": [
            {
                "engine": endpoint.engine,
                "version": endpoint.version,
                "inference_profile": endpoint.inference_profile,
                "url": endpoint.url,
            }
            for endpoint in endpoints
        ],
    }


def _record_measurements(
    measurements: list[dict[str, Any]],
    specs: list[QuerySpec],
    common: dict[str, Any],
) -> list[dict[str, Any]]:
    by_id = {spec.id: spec for spec in specs}
    rows = []
    for measurement in measurements:
        spec = by_id[str(measurement["query_id"])]
        normalized = {
            "result_digest": "",
            **measurement,
        }
        rows.append(
            {
                **common,
                **normalized,
                "status": "completed",
                "censored": False,
                "expectation": spec.expectation,
                "expectation_ok": _expectation_ok(spec, measurement),
            }
        )
    return rows


def _validate_expectations(rows: list[dict[str, Any]]) -> None:
    failed = [
        row
        for row in rows
        if row.get("status", "completed") == "completed"
        and not row["expectation_ok"]
    ]
    if failed:
        descriptions = []
        for row in failed[:8]:
            location = (
                f"stage={row['stage']}" if "stage" in row
                else f"users={row.get('synthetic_users', '?')}"
            )
            descriptions.append(
                f"{row['engine']}:{row['query_id']} "
                f"({location}, repetition={row.get('repetition', '?')}, "
                f"count={row['result_count']}, "
                f"expected={row['expectation']})"
            )
        sample = ", ".join(descriptions)
        raise AssertionError(
            f"{len(failed)} cross-engine query expectations failed: {sample}"
        )


def _failure_detail(
    endpoint: EngineEndpoint,
    common: dict[str, Any],
    status: str,
    phase: str,
    error: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    return {
        **common,
        "engine": endpoint.engine,
        "inference_profile": endpoint.inference_profile,
        "query_id": "__phase__",
        "category": "",
        "tier": "",
        "duration_ms": "",
        "result_count": "",
        "ask_result": "",
        "result_digest": "",
        "expectation": "",
        "expectation_ok": "",
        "status": status,
        "censored": True,
        "failed_phase": phase,
        "timeout_seconds": timeout_seconds,
        "error": error,
    }


def _failure_summary(
    endpoint: EngineEndpoint,
    common: dict[str, Any],
    status: str,
    phase: str,
    error: str,
    timeout_seconds: float,
    elapsed_seconds: float,
) -> dict[str, Any]:
    lower_bound_ms = min(max(elapsed_seconds, 0.0), timeout_seconds) * 1000
    return {
        **common,
        "engine": endpoint.engine,
        "inference_profile": endpoint.inference_profile,
        "query_count": 0,
        "input_triples": "",
        "output_triples": "",
        "inferred_triples": "",
        "load_ms": "",
        "reasoning_ms": "",
        "prepare_ms": "",
        "query_ms": "",
        "engine_total_ms": lower_bound_ms if status == "timeout" else "",
        "mean_query_ms": "",
        "status": status,
        "censored": True,
        "censored_lower_bound_ms": lower_bound_ms,
        "failed_phase": phase,
        "timeout_seconds": timeout_seconds,
        "error": error,
    }


def run_engine_cumulative(
    config: BenchmarkConfig,
    endpoint_urls: list[str],
    output_root: Path,
    warmups: int = 0,
) -> Path:
    endpoints = discover(endpoint_urls)
    base, specs = _load(config)
    data = _ntriples(base)
    details: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    phase_timeout = config.limits.phase_timeout_seconds
    point_timeout = config.limits.point_timeout_seconds

    for endpoint in endpoints:
        endpoint_blocked = False
        blocked_status = "timeout"
        for warmup in range(1, warmups + 1):
            print(
                f"[engines-cumulative] engine={endpoint.engine} "
                f"inference={endpoint.inference_profile} "
                f"warmup={warmup}/{warmups} status=running",
                flush=True,
            )
            try:
                _request(
                    endpoint.url,
                    "/prepare",
                    {
                        "data_ntriples": data,
                        "phase_timeout_seconds": max(
                            phase_timeout - 1.0, 0.1
                        ),
                    },
                    timeout=phase_timeout,
                )
                _request(
                    endpoint.url,
                    "/queries",
                    _query_payload(specs, phase_timeout),
                    timeout=phase_timeout,
                )
            except Exception as error:
                if not is_boundary_failure(error):
                    raise
                endpoint_blocked = True
                blocked_status = failure_status(error)
                print(
                    f"[engines-cumulative] engine={endpoint.engine} "
                    f"warmup={warmup}/{warmups} status={blocked_status} "
                    f"limit_s={phase_timeout:g} error={error_text(error)}",
                    flush=True,
                )
                break
        for repetition in range(1, config.repetitions + 1):
            if endpoint_blocked:
                for stage, category in enumerate(
                    config.category_order, start=1
                ):
                    common = {
                        "repetition": repetition,
                        "stage": stage,
                        "added_category": category,
                    }
                    status = (
                        blocked_status
                        if repetition == 1 and stage == 1
                        else "skipped_after_timeout"
                    )
                    message = (
                        "engine warm-up exceeded the configured limit"
                        if status == "timeout"
                        else "larger/repeated point skipped after timeout"
                    )
                    summaries.append(
                        _failure_summary(
                            endpoint,
                            common,
                            status,
                            "warmup",
                            message,
                            phase_timeout,
                            phase_timeout if status == blocked_status else 0.0,
                        )
                    )
                    details.append(
                        _failure_detail(
                            endpoint,
                            common,
                            status,
                            "warmup",
                            message,
                            phase_timeout,
                        )
                    )
                continue
            print(
                f"[engines-cumulative] engine={endpoint.engine} "
                f"inference={endpoint.inference_profile} "
                f"repetition={repetition}/{config.repetitions} "
                "phase=prepare status=running",
                flush=True,
            )
            point_started = monotonic()
            try:
                prepared = _request(
                    endpoint.url,
                    "/prepare",
                    {
                        "data_ntriples": data,
                        "phase_timeout_seconds": max(
                            min(phase_timeout, point_timeout) - 1.0,
                            0.1,
                        ),
                    },
                    timeout=min(phase_timeout, point_timeout),
                )
            except Exception as error:
                if not is_boundary_failure(error):
                    raise
                status = failure_status(error)
                endpoint_blocked = config.limits.stop_scaling_after_timeout
                for stage, category in enumerate(
                    config.category_order, start=1
                ):
                    common = {
                        "repetition": repetition,
                        "stage": stage,
                        "added_category": category,
                    }
                    row_status = status if stage == 1 else "skipped_after_timeout"
                    summaries.append(
                        _failure_summary(
                            endpoint,
                            common,
                            row_status,
                            "prepare",
                            error_text(error),
                            point_timeout,
                            monotonic() - point_started if stage == 1 else 0.0,
                        )
                    )
                    details.append(
                        _failure_detail(
                            endpoint,
                            common,
                            row_status,
                            "prepare",
                            error_text(error),
                            point_timeout,
                        )
                    )
                print(
                    f"[engines-cumulative] engine={endpoint.engine} "
                    f"repetition={repetition} phase=prepare status={status} "
                    f"limit_s={point_timeout:g}",
                    flush=True,
                )
                continue
            active: set[str] = set()
            for stage, category in enumerate(config.category_order, start=1):
                stage_started = monotonic()
                active.add(category)
                active_specs = by_categories(specs, active)
                print(
                    f"[engines-cumulative] engine={endpoint.engine} "
                    f"inference={endpoint.inference_profile} "
                    f"repetition={repetition}/{config.repetitions} "
                    f"stage={stage}/{len(config.category_order)} "
                    f"category={category} queries={len(active_specs)} "
                    "status=running",
                    flush=True,
                )
                common = {
                    "engine": endpoint.engine,
                    "inference_profile": endpoint.inference_profile,
                    "repetition": repetition,
                    "stage": stage,
                    "added_category": category,
                }
                query_timeout = min(
                    phase_timeout,
                    max(
                        point_timeout
                        - float(prepared["prepare_ms"]) / 1000,
                        0.001,
                    ),
                )
                try:
                    response = _request(
                        endpoint.url,
                        "/queries",
                        _query_payload(active_specs, query_timeout),
                        timeout=query_timeout,
                    )
                except Exception as error:
                    if not is_boundary_failure(error):
                        raise
                    status = failure_status(error)
                    summaries.append(
                        _failure_summary(
                            endpoint,
                            common,
                            status,
                            "queries",
                            error_text(error),
                            point_timeout,
                            float(prepared["prepare_ms"]) / 1000
                            + monotonic()
                            - stage_started,
                        )
                    )
                    details.append(
                        _failure_detail(
                            endpoint,
                            common,
                            status,
                            "queries",
                            error_text(error),
                            point_timeout,
                        )
                    )
                    for skipped_stage in range(
                        stage + 1, len(config.category_order) + 1
                    ):
                        skipped_common = {
                            "repetition": repetition,
                            "stage": skipped_stage,
                            "added_category": config.category_order[
                                skipped_stage - 1
                            ],
                        }
                        summaries.append(
                            _failure_summary(
                                endpoint,
                                skipped_common,
                                "skipped_after_timeout",
                                "queries",
                                "larger cumulative stage skipped after timeout",
                                point_timeout,
                                0.0,
                            )
                        )
                        details.append(
                            _failure_detail(
                                endpoint,
                                skipped_common,
                                "skipped_after_timeout",
                                "queries",
                                "larger cumulative stage skipped after timeout",
                                point_timeout,
                            )
                        )
                    endpoint_blocked = config.limits.stop_scaling_after_timeout
                    print(
                        f"[engines-cumulative] engine={endpoint.engine} "
                        f"stage={stage} status={status} "
                        f"limit_s={point_timeout:g}",
                        flush=True,
                    )
                    break
                recorded = _record_measurements(
                    response["measurements"],
                    active_specs,
                    common,
                )
                details.extend(recorded)
                query_times = [
                    float(item["duration_ms"])
                    for item in response["measurements"]
                ]
                summaries.append(
                    {
                        **common,
                        "query_count": len(active_specs),
                        "input_triples": prepared["input_triples"],
                        "output_triples": prepared["output_triples"],
                        "inferred_triples": prepared["inferred_triples"],
                        "load_ms": prepared["load_ms"],
                        "reasoning_ms": prepared["reasoning_ms"],
                        "prepare_ms": prepared["prepare_ms"],
                        "query_ms": response["query_wall_ms"],
                        "engine_total_ms": (
                            float(prepared["prepare_ms"])
                            + float(response["query_wall_ms"])
                        ),
                        "mean_query_ms": statistics.fmean(query_times),
                        "status": "completed",
                        "censored": False,
                    }
                )
                print(
                    f"[engines-cumulative] engine={endpoint.engine} "
                    f"stage={stage}/{len(config.category_order)} "
                    f"category={category} status=done "
                    f"total_ms={summaries[-1]['engine_total_ms']:.2f}",
                    flush=True,
                )

    output = output_root / "cumulative"
    _write_csv(output / "query-runs.csv", details)
    _write_csv(output / "summary.csv", summaries)
    metadata = _metadata(
        config,
        base,
        endpoints,
        "cumulative",
        warmups,
    )
    metadata["category_order"] = list(config.category_order)
    metadata["execution_limits"] = {
        "phase_timeout_seconds": phase_timeout,
        "point_timeout_seconds": point_timeout,
        "stop_scaling_after_timeout": config.limits.stop_scaling_after_timeout,
        "timeout_semantics": "right-censored; later points are skipped",
    }
    _write_metadata(output / "metadata.json", metadata)
    _validate_expectations(details)
    return output


def run_engine_scalability(
    config: BenchmarkConfig,
    endpoint_urls: list[str],
    output_root: Path,
    warmups: int = 0,
) -> Path:
    endpoints = discover(endpoint_urls)
    base, specs = _load(config)
    details: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    phase_timeout = config.limits.phase_timeout_seconds
    point_timeout = config.limits.point_timeout_seconds
    blocked: dict[str, str] = {}

    for block, users in enumerate(config.scale_users, start=1):
        source = _clone(base)
        generated_at = perf_counter_ns()
        synthetic_triples = add_synthetic_data(source, users, config.seed)
        generation_ms = (perf_counter_ns() - generated_at) / 1_000_000
        data = _ntriples(source)
        for endpoint in endpoints:
            if endpoint.engine in blocked:
                for repetition in range(1, config.repetitions + 1):
                    common = {
                        "repetition": repetition,
                        "synthetic_users": users,
                        "synthetic_triples": synthetic_triples,
                        "generation_ms": generation_ms,
                    }
                    message = (
                        "larger scalability block skipped after timeout: "
                        f"{blocked[endpoint.engine]}"
                    )
                    summaries.append(
                        _failure_summary(
                            endpoint,
                            common,
                            "skipped_after_timeout",
                            "early-stop",
                            message,
                            point_timeout,
                            0.0,
                        )
                    )
                    details.append(
                        _failure_detail(
                            endpoint,
                            common,
                            "skipped_after_timeout",
                            "early-stop",
                            message,
                            point_timeout,
                        )
                    )
                continue
            warmup_error: Exception | None = None
            for warmup in range(1, warmups + 1):
                print(
                    f"[engines-scalability] block={block}/"
                    f"{len(config.scale_users)} users={users} "
                    f"engine={endpoint.engine} "
                    f"inference={endpoint.inference_profile} "
                    f"warmup={warmup}/{warmups} status=running",
                    flush=True,
                )
                try:
                    _request(
                        endpoint.url,
                        "/prepare",
                        {
                            "data_ntriples": data,
                            "phase_timeout_seconds": max(
                                phase_timeout - 1.0, 0.1
                            ),
                        },
                        timeout=phase_timeout,
                    )
                    _request(
                        endpoint.url,
                        "/queries",
                        _query_payload(specs, phase_timeout),
                        timeout=phase_timeout,
                    )
                except Exception as error:
                    if not is_boundary_failure(error):
                        raise
                    warmup_error = error
                    print(
                        f"[engines-scalability] block={block} users={users} "
                        f"engine={endpoint.engine} warmup={warmup}/{warmups} "
                        f"status={failure_status(error)} "
                        f"limit_s={phase_timeout:g}",
                        flush=True,
                    )
                    break
            for repetition in range(1, config.repetitions + 1):
                if warmup_error is not None:
                    status = (
                        failure_status(warmup_error)
                        if repetition == 1
                        else "skipped_after_timeout"
                    )
                    common = {
                        "repetition": repetition,
                        "synthetic_users": users,
                        "synthetic_triples": synthetic_triples,
                        "generation_ms": generation_ms,
                    }
                    summaries.append(
                        _failure_summary(
                            endpoint,
                            common,
                            status,
                            "warmup",
                            error_text(warmup_error),
                            phase_timeout,
                            phase_timeout
                            if status == failure_status(warmup_error)
                            else 0.0,
                        )
                    )
                    details.append(
                        _failure_detail(
                            endpoint,
                            common,
                            status,
                            "warmup",
                            error_text(warmup_error),
                            phase_timeout,
                        )
                    )
                    blocked[endpoint.engine] = error_text(warmup_error)
                    continue
                print(
                    f"[engines-scalability] block={block}/"
                    f"{len(config.scale_users)} users={users} "
                    f"engine={endpoint.engine} "
                    f"inference={endpoint.inference_profile} "
                    f"repetition={repetition}/{config.repetitions} "
                    "phase=prepare status=running",
                    flush=True,
                )
                common = {
                    "engine": endpoint.engine,
                    "inference_profile": endpoint.inference_profile,
                    "repetition": repetition,
                    "synthetic_users": users,
                    "synthetic_triples": synthetic_triples,
                    "generation_ms": generation_ms,
                }
                point_started = monotonic()
                phase = "prepare"
                try:
                    prepared = _request(
                        endpoint.url,
                        "/prepare",
                        {
                            "data_ntriples": data,
                            "phase_timeout_seconds": max(
                                min(phase_timeout, point_timeout) - 1.0,
                                0.1,
                            ),
                        },
                        timeout=min(phase_timeout, point_timeout),
                    )
                    phase = "queries"
                    query_timeout = min(
                        phase_timeout,
                        remaining_seconds(point_started, point_timeout),
                    )
                    response = _request(
                        endpoint.url,
                        "/queries",
                        _query_payload(specs, query_timeout),
                        timeout=query_timeout,
                    )
                except Exception as error:
                    if not is_boundary_failure(error):
                        raise
                    status = failure_status(error)
                    message = error_text(error)
                    summaries.append(
                        _failure_summary(
                            endpoint,
                            common,
                            status,
                            phase,
                            message,
                            point_timeout,
                            monotonic() - point_started,
                        )
                    )
                    details.append(
                        _failure_detail(
                            endpoint,
                            common,
                            status,
                            phase,
                            message,
                            point_timeout,
                        )
                    )
                    if config.limits.stop_scaling_after_timeout:
                        blocked[endpoint.engine] = message
                    print(
                        f"[engines-scalability] block={block} users={users} "
                        f"engine={endpoint.engine} phase={phase} "
                        f"status={status} limit_s={point_timeout:g}",
                        flush=True,
                    )
                    continue
                details.extend(
                    _record_measurements(
                        response["measurements"],
                        specs,
                        common,
                    )
                )
                query_times = [
                    float(item["duration_ms"])
                    for item in response["measurements"]
                ]
                engine_total = (
                    float(prepared["prepare_ms"])
                    + float(response["query_wall_ms"])
                )
                summaries.append(
                    {
                        **common,
                        "query_count": len(specs),
                        "generation_ms": generation_ms,
                        "input_triples": prepared["input_triples"],
                        "output_triples": prepared["output_triples"],
                        "inferred_triples": prepared["inferred_triples"],
                        "load_ms": prepared["load_ms"],
                        "reasoning_ms": prepared["reasoning_ms"],
                        "prepare_ms": prepared["prepare_ms"],
                        "query_ms": response["query_wall_ms"],
                        "engine_total_ms": engine_total,
                        "pipeline_total_ms": generation_ms + engine_total,
                        "queries_per_second": (
                            len(specs)
                            / (float(response["query_wall_ms"]) / 1000)
                        ),
                        "mean_query_ms": statistics.fmean(query_times),
                        "status": "completed",
                        "censored": False,
                    }
                )
                print(
                    f"[engines-scalability] block={block}/"
                    f"{len(config.scale_users)} users={users} "
                    f"engine={endpoint.engine} status=done "
                    f"total_ms={engine_total:.2f}",
                    flush=True,
                )

    output = output_root / "scalability"
    _write_csv(output / "query-runs.csv", details)
    _write_csv(output / "summary.csv", summaries)
    metadata = _metadata(
        config,
        base,
        endpoints,
        "scalability",
        warmups,
    )
    metadata["scale_users"] = list(config.scale_users)
    metadata["execution_limits"] = {
        "phase_timeout_seconds": phase_timeout,
        "point_timeout_seconds": point_timeout,
        "stop_scaling_after_timeout": config.limits.stop_scaling_after_timeout,
        "timeout_semantics": "right-censored; later blocks are skipped per engine",
    }
    _write_metadata(output / "metadata.json", metadata)
    _validate_expectations(details)
    return output


def validate_rdfs_equivalence(
    output_root: Path,
    suite: str,
) -> Path:
    """Compare RDFS engines at decision and exact-cardinality levels.

    RDFS implementations can legitimately expose different datatype-entailment
    duplicates. Therefore the executable conformance gate is the observable
    query outcome (ASK value or zero/non-zero result set); exact cardinality is
    retained as a diagnostic, including the Jena/RDF4J pair comparison.
    """

    path = output_root / suite / "query-runs.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rdfs_rows = [
        row
        for row in rows
        if row["inference_profile"] == "rdfs"
        and row.get("status", "completed") == "completed"
        and row.get("query_id") != "__phase__"
    ]
    key_fields = ["repetition", "query_id"]
    key_fields.append("stage" if suite == "cumulative" else "synthetic_users")
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in rdfs_rows:
        key = tuple(row[field] for field in key_fields)
        grouped.setdefault(key, []).append(row)
    validations = []
    for key, samples in grouped.items():
        exact_outcomes = {
            (
                sample["result_count"],
                sample.get("ask_result", ""),
            )
            for sample in samples
        }
        observable_outcomes = {
            (
                f"ask:{sample['ask_result'].lower()}"
                if sample.get("ask_result", "")
                else (
                    "rows:nonzero"
                    if int(sample["result_count"]) > 0
                    else "rows:zero"
                )
            )
            for sample in samples
        }
        by_engine = {sample["engine"]: sample for sample in samples}
        expected_engines = {"jena", "rdf4j", "rdflib"}
        complete = expected_engines.issubset(by_engine)
        jena_rdf4j_exact = (
            (
                by_engine["jena"]["result_count"],
                by_engine["jena"].get("ask_result", ""),
            )
            == (
                by_engine["rdf4j"]["result_count"],
                by_engine["rdf4j"].get("ask_result", ""),
            )
            if {"jena", "rdf4j"}.issubset(by_engine)
            else ""
        )
        validations.append(
            {
                "suite": suite,
                "repetition": key[0],
                "query_id": key[1],
                "stage_or_users": key[2],
                "engines": "|".join(
                    sorted(sample["engine"] for sample in samples)
                ),
                "result_counts": "|".join(
                    f"{sample['engine']}={sample['result_count']}"
                    for sample in sorted(
                        samples,
                        key=lambda item: item["engine"],
                    )
                ),
                "ask_results": "|".join(
                    f"{sample['engine']}={sample.get('ask_result', '')}"
                    for sample in sorted(
                        samples,
                        key=lambda item: item["engine"],
                    )
                ),
                "comparison_status": (
                    "complete" if complete else "insufficient_data"
                ),
                "outcome_equivalent": (
                    len(observable_outcomes) == 1 if complete else ""
                ),
                "exact_equivalent": (
                    len(exact_outcomes) == 1 if complete else ""
                ),
                "jena_rdf4j_exact_equivalent": jena_rdf4j_exact,
            }
        )
    if not validations:
        validations.append(
            {
                "suite": suite,
                "repetition": "",
                "query_id": "",
                "stage_or_users": "",
                "engines": "",
                "result_counts": "",
                "ask_results": "",
                "comparison_status": "no_completed_common_observations",
                "outcome_equivalent": "",
                "exact_equivalent": "",
                "jena_rdf4j_exact_equivalent": "",
            }
        )
    output = output_root / suite / "rdfs-equivalence.csv"
    _write_csv(output, validations)
    mismatches = [
        row
        for row in validations
        if row["comparison_status"] == "complete"
        and not row["outcome_equivalent"]
    ]
    summary = {
        "suite": suite,
        "comparisons": len(validations),
        "observable_outcome_agreements": sum(
            bool(row["outcome_equivalent"]) for row in validations
        ),
        "exact_cardinality_agreements": sum(
            bool(row["exact_equivalent"]) for row in validations
        ),
        "jena_rdf4j_exact_agreements": sum(
            bool(row["jena_rdf4j_exact_equivalent"])
            for row in validations
        ),
        "observable_outcome_mismatches": len(mismatches),
        "interpretation": (
            "Observable outcome is the conformance gate; exact cardinality "
            "is diagnostic because datatype entailment differs by engine."
        ),
    }
    _write_metadata(
        output_root / suite / "rdfs-equivalence-summary.json",
        summary,
    )
    if mismatches:
        raise AssertionError(
            f"{len(mismatches)} observable RDFS outcomes differ; "
            f"see {output}"
        )
    return output
