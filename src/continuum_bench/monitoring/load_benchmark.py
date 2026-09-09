"""Rate-controlled semantic alert workload for elastic deployments."""

from __future__ import annotations

from concurrent.futures import (
    FIRST_COMPLETED,
    Future,
    ThreadPoolExecutor,
    wait,
)
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import signal
import statistics
from time import perf_counter_ns, sleep
from typing import Any, Callable, Iterator

from .config import BenchmarkConfig
from ..csv_utils import write_dict_rows
from .distributed import Endpoint, _parallel, _request, discover
from .load_config import LoadBenchmarkConfig, LoadProfile
from ..queries import QuerySpec, load_catalog
from ..specification import release_identity
from .budget import execution_metadata


from .budget import unlimited_execution


class PhaseTimeout(TimeoutError):
    """Raised when a local prepare/recovery phase exceeds its budget."""


@contextmanager
def _local_timeout(seconds: float) -> Iterator[None]:
    if unlimited_execution() or not hasattr(signal, "setitimer"):
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)

    def alarm_handler(signum, frame):  # noqa: ARG001
        raise PhaseTimeout(f"local phase exceeded {seconds:.1f}s")

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def _is_timeout(error: str) -> bool:
    normalized = error.lower()
    return (
        "timeout" in normalized
        or "timed out" in normalized
        or "http error 408" in normalized
    )


def discover_load_endpoints(urls: list[str]) -> list[Endpoint]:
    return discover(urls)


def _workload_specs(config: BenchmarkConfig) -> list[QuerySpec]:
    """Return the full catalog while verifying the alert-evaluation subset."""

    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    alerts = [
        spec for spec in specs if spec.expectation in {"true", "zero_rows"}
    ]
    positives = [spec for spec in alerts if spec.expectation == "true"]
    negatives = [spec for spec in alerts if spec.expectation == "zero_rows"]
    if not positives or not negatives:
        raise ValueError(
            "Alert workload requires positive ASK and negative violation queries"
        )
    grouped = {
        category: [spec for spec in specs if spec.category == category]
        for category in config.category_order
    }
    interleaved = []
    for index in range(max(map(len, grouped.values()))):
        interleaved.extend(
            values[index]
            for values in grouped.values()
            if index < len(values)
        )
    if len(interleaved) != len(specs):
        raise ValueError("Load query schedule lost catalog entries")
    return interleaved


def _is_alert(spec: QuerySpec) -> bool:
    return spec.expectation in {"true", "zero_rows"}


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(
        values,
        n=100,
        method="inclusive",
    )[percentile - 1]


def _prediction(spec: QuerySpec, measurement: dict[str, Any]) -> bool:
    if measurement.get("ask_result") is not None:
        return bool(measurement["ask_result"])
    return int(measurement["result_count"]) > 0


def _truth(spec: QuerySpec) -> bool | str:
    return spec.expectation == "true" if _is_alert(spec) else ""


def _empty_role_metrics(endpoints: list[Endpoint]) -> dict[str, dict[str, float]]:
    return {
        endpoint.role: {
            "batches": 0,
            "events": 0,
            "process_cpu_ms": 0.0,
            "max_current_rss_kib": 0.0,
            "peak_rss_kib": 0.0,
            "disk_read_bytes": 0.0,
            "disk_write_bytes": 0.0,
            "request_bytes": 0.0,
            "response_bytes": 0.0,
        }
        for endpoint in endpoints
    }


def _run_event_stream(
    profile: LoadProfile,
    load_config: LoadBenchmarkConfig,
    specs: list[QuerySpec],
    endpoints: list[Endpoint],
    invoke: Callable[[Endpoint, list[str], float], dict[str, Any]],
    common: dict[str, Any],
    *,
    point_timeout_seconds: float | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, float]]]:
    offered = profile.offered_events
    batch_size = load_config.batch_size
    capacity = load_config.queue_capacity_events
    role_metrics = _empty_role_metrics(endpoints)
    rows: list[dict[str, Any]] = []
    latencies: list[float] = []
    tp = fp = tn = fn = 0
    alerts_evaluated = 0
    processed = 0
    lost = 0
    started = perf_counter_ns()
    point_budget = (
        load_config.point_timeout_seconds
        if point_timeout_seconds is None
        else point_timeout_seconds
    )
    if unlimited_execution():
        point_budget = float("inf")
    if point_budget <= 0:
        raise PhaseTimeout("no point budget remains for the event stream")
    query_offset = (
        (int(common.get("repetition", 1)) - 1) * offered
    ) % len(specs)

    def scheduled_spec(index: int) -> QuerySpec:
        return specs[(query_offset + index) % len(specs)]

    deadline = float("inf") if unlimited_execution() else started + int(point_budget * 1e9)
    event_index = 0
    batch_index = 0
    in_flight: dict[
        Future,
        tuple[Endpoint, list[tuple[int, QuerySpec, int]]],
    ] = {}

    def lost_rows(
        items: list[tuple[int, QuerySpec, int]],
        endpoint: Endpoint | None,
        reason: str,
    ) -> None:
        nonlocal lost
        lost += len(items)
        for event_id, spec, _ in items:
            rows.append(
                {
                    **common,
                    "event_id": event_id,
                    "query_id": spec.id,
                    "truth_alert": _truth(spec),
                    "predicted_alert": "",
                    "processed": False,
                    "lost_reason": reason,
                    "latency_ms": "",
                    "engine_duration_ms": "",
                    "role": endpoint.role if endpoint else "",
                    "endpoint": endpoint.url if endpoint else "",
                }
            )

    def harvest(done: set[Future]) -> None:
        nonlocal processed, tp, fp, tn, fn, alerts_evaluated
        completed_at = perf_counter_ns()
        for future in done:
            endpoint, items = in_flight.pop(future)
            try:
                response = future.result()
                measurements = response["measurements"]
                if len(measurements) != len(items):
                    raise RuntimeError(
                        f"worker returned {len(measurements)} measurements "
                        f"for {len(items)} events"
                    )
            except Exception as error:
                lost_rows(
                    items,
                    endpoint,
                    f"{type(error).__name__}: {error}",
                )
                continue
            metrics = role_metrics[endpoint.role]
            metrics["batches"] += 1
            metrics["events"] += len(items)
            for field in (
                "process_cpu_ms",
                "disk_read_bytes",
                "disk_write_bytes",
                "request_bytes",
                "response_bytes",
            ):
                metrics[field] += float(response.get(field, 0.0))
            metrics["peak_rss_kib"] = max(
                metrics["peak_rss_kib"],
                float(response.get("peak_rss_kib", 0.0)),
            )
            metrics["max_current_rss_kib"] = max(
                metrics["max_current_rss_kib"],
                float(response.get("current_rss_kib", 0.0)),
            )
            durations = [
                float(measurement.get("duration_ms", 0.0))
                for measurement in measurements
            ]
            duration_total = sum(durations)
            for (event_id, spec, scheduled), measurement in zip(
                items,
                measurements,
                strict=True,
            ):
                latency_ms = (completed_at - scheduled) / 1_000_000
                alert = _is_alert(spec)
                predicted = _prediction(spec, measurement) if alert else ""
                truth = _truth(spec)
                if alert:
                    alerts_evaluated += 1
                    if truth and predicted:
                        tp += 1
                    elif not truth and predicted:
                        fp += 1
                    elif truth and not predicted:
                        fn += 1
                    else:
                        tn += 1
                processed += 1
                latencies.append(latency_ms)
                duration = float(measurement.get("duration_ms", 0.0))
                attribution = (
                    duration / duration_total
                    if duration_total > 0
                    else 1.0 / len(measurements)
                )
                rows.append(
                    {
                        **common,
                        "event_id": event_id,
                        "query_id": spec.id,
                        "truth_alert": truth,
                        "predicted_alert": predicted,
                        "processed": True,
                        "lost_reason": "",
                        "latency_ms": latency_ms,
                        "engine_duration_ms": measurement["duration_ms"],
                        "process_cpu_ms": (
                            float(response.get("process_cpu_ms", 0.0))
                            * attribution
                        ),
                        "current_rss_kib": float(
                            response.get("current_rss_kib", 0.0)
                        ),
                        "peak_rss_kib": float(
                            response.get("peak_rss_kib", 0.0)
                        ),
                        "disk_read_bytes": (
                            float(response.get("disk_read_bytes", 0.0))
                            * attribution
                        ),
                        "disk_write_bytes": (
                            float(response.get("disk_write_bytes", 0.0))
                            * attribution
                        ),
                        "request_bytes": (
                            float(response.get("request_bytes", 0.0))
                            * attribution
                        ),
                        "response_bytes": (
                            float(response.get("response_bytes", 0.0))
                            * attribution
                        ),
                        "resource_attribution": (
                            "batch-duration-proportional;rss-observed"
                        ),
                        "role": endpoint.role,
                        "endpoint": endpoint.url,
                    }
                )

    executor = ThreadPoolExecutor(max_workers=max(1, len(endpoints) * 2))
    try:
        while event_index < offered:
            now = perf_counter_ns()
            if now >= deadline:
                remaining = [
                    (
                        index,
                        scheduled_spec(index),
                        started
                        + int((index / profile.events_per_second) * 1e9),
                    )
                    for index in range(event_index, offered)
                ]
                lost_rows(remaining, None, "point_timeout_before_dispatch")
                break
            due = started + int(
                (event_index / profile.events_per_second) * 1e9
            )
            if now < due:
                if in_flight:
                    done, _ = wait(
                        set(in_flight),
                        timeout=min((due - now) / 1e9, 0.05),
                        return_when=FIRST_COMPLETED,
                    )
                    harvest(done)
                else:
                    sleep(min((due - now) / 1e9, 0.05))
                continue
            done = {future for future in in_flight if future.done()}
            harvest(done)
            # A microbatch may contain only events whose scheduled arrival has
            # already happened. Including future events would make their
            # end-to-end latency negative or artificially small.
            due_events = max(
                1,
                int(
                    ((now - started) / 1e9)
                    * profile.events_per_second
                )
                + 1
                - event_index,
            )
            count = min(batch_size, offered - event_index, due_events)
            items = [
                (
                    index,
                    scheduled_spec(index),
                    started
                    + int((index / profile.events_per_second) * 1e9),
                )
                for index in range(event_index, event_index + count)
            ]
            pending_events = sum(len(value[1]) for value in in_flight.values())
            if pending_events + count > capacity:
                lost_rows(items, None, "queue_capacity")
            else:
                endpoint = endpoints[batch_index % len(endpoints)]
                query_ids = [item[1].id for item in items]
                future = executor.submit(
                    invoke,
                    endpoint,
                    query_ids,
                    min(
                        load_config.request_timeout_seconds,
                        point_budget,
                    ),
                )
                in_flight[future] = (endpoint, items)
                batch_index += 1
            event_index += count

        while in_flight and perf_counter_ns() < deadline:
            remaining_seconds = (deadline - perf_counter_ns()) / 1e9
            done, _ = wait(
                set(in_flight),
                timeout=max(min(remaining_seconds, 0.1), 0.0),
                return_when=FIRST_COMPLETED,
            )
            harvest(done)
        for future, (endpoint, items) in list(in_flight.items()):
            future.cancel()
            lost_rows(items, endpoint, "point_timeout_in_flight")
            in_flight.pop(future)
    finally:
        # Running thread futures cannot be cancelled. Waiting here would make
        # the point-level deadline advisory and can stall the coordinator on a
        # slow physical worker. HTTP calls retain their own bounded timeout;
        # detach them after recording the requests as right-censored.
        executor.shutdown(wait=False, cancel_futures=True)

    elapsed_ms = (perf_counter_ns() - started) / 1_000_000
    precision = tp / (tp + fp) if tp + fp else ""
    recall = tp / (tp + fn) if tp + fn else ""
    summary = {
        "events_offered": offered,
        "events_processed": processed,
        "events_lost": lost,
        "event_loss_percent": lost / offered * 100 if offered else 0.0,
        "events_processed_per_second": (
            processed / (elapsed_ms / 1000) if elapsed_ms else 0.0
        ),
        "workload_wall_ms": elapsed_ms,
        "latency_p50_ms": _percentile(latencies, 50),
        "latency_p95_ms": _percentile(latencies, 95),
        "latency_p99_ms": _percentile(latencies, 99),
        "alert_true_positive": tp,
        "alert_false_positive": fp,
        "alert_true_negative": tn,
        "alert_false_negative": fn,
        "alerts_evaluated": alerts_evaluated,
        "alert_evaluation_coverage_percent": (
            alerts_evaluated / processed * 100 if processed else 0.0
        ),
        "alert_precision": precision,
        "alert_accuracy": (
            (tp + tn) / alerts_evaluated if alerts_evaluated else ""
        ),
        "alert_recall": recall,
        "alert_f1": (
            2 * precision * recall / (precision + recall)
            if precision != "" and recall != "" and precision + recall
            else ""
        ),
        "timed_out": lost > 0 and perf_counter_ns() >= deadline,
    }
    return summary, rows, role_metrics


def _prepare_payload(
    profile: LoadProfile,
    reasoner: str,
    seed: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    return {
        "reasoner": reasoner,
        "users": profile.users,
        "seed": seed,
        "mode": "replicated",
        "rule_count": profile.rule_count,
        "target_triples": profile.target_triples,
        "phase_timeout_seconds": max(timeout_seconds - 1.0, 0.1),
    }


def _resource_summary(
    prepared: dict[str, dict[str, Any]],
    recovered: dict[str, dict[str, Any]],
    role_metrics: dict[str, dict[str, float]],
    endpoints: list[Endpoint],
    pipeline_wall_ms: float,
) -> dict[str, Any]:
    phases = [*prepared.values(), *recovered.values()]
    event_cpu = sum(item["process_cpu_ms"] for item in role_metrics.values())
    phase_cpu = sum(float(item.get("process_cpu_ms", 0.0)) for item in phases)
    cpu_time_ms = event_cpu + phase_cpu
    rss = [
        float(item.get("peak_rss_kib", 0.0)) for item in phases
    ] + [item["peak_rss_kib"] for item in role_metrics.values()]
    current_rss = [
        float(item.get("current_rss_kib", 0.0)) for item in phases
    ] + [
        item["max_current_rss_kib"] for item in role_metrics.values()
    ]
    disk_read = sum(
        float(item.get("disk_read_bytes", 0.0)) for item in phases
    ) + sum(item["disk_read_bytes"] for item in role_metrics.values())
    disk_write = sum(
        float(item.get("disk_write_bytes", 0.0)) for item in phases
    ) + sum(item["disk_write_bytes"] for item in role_metrics.values())
    network = sum(
        float(item.get("request_bytes", 0.0))
        + float(item.get("response_bytes", 0.0))
        for item in phases
    ) + sum(
        item["request_bytes"] + item["response_bytes"]
        for item in role_metrics.values()
    )
    return {
        "process_cpu_time_ms": cpu_time_ms,
        "cpu_percent_per_node_one_core": (
            cpu_time_ms / (pipeline_wall_ms * len(endpoints)) * 100
            if pipeline_wall_ms and endpoints
            else 0.0
        ),
        "max_peak_rss_kib": max(rss, default=0.0),
        "max_current_rss_kib": max(current_rss, default=0.0),
        "disk_read_bytes": disk_read,
        "disk_write_bytes": disk_write,
        "disk_io_bytes": disk_read + disk_write,
        "network_body_bytes": network,
    }


def run_load_benchmark(
    benchmark_config: BenchmarkConfig,
    load_config: LoadBenchmarkConfig,
    architecture: str,
    output_root: Path,
    endpoint_urls: list[str] | None = None,
) -> Path:
    if architecture not in {"physical"}:
        raise ValueError(
            "Load benchmark target must be physical"
        )
    all_endpoints = discover_load_endpoints(endpoint_urls or [])
    specs = _workload_specs(benchmark_config)
    summary_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    node_rows: list[dict[str, Any]] = []
    stopped_dimensions: dict[tuple[str, str], str] = {}

    for profile_index, profile in enumerate(load_config.profiles, start=1):
        requested_nodes = profile.node_count
        effective_nodes = requested_nodes
        if effective_nodes > len(all_endpoints):
            raise ValueError(
                f"{architecture} exposes {len(all_endpoints)} nodes but "
                f"profile {profile.name} requests {effective_nodes}"
            )
        endpoints = all_endpoints[:effective_nodes]
        for reasoner in benchmark_config.reasoners:
            for repetition in range(1, load_config.repetitions + 1):
                common = {
                    "architecture": architecture,
                    "profile": profile.name,
                    "dimension": profile.dimension,
                    "profile_index": profile_index,
                    "reasoner": reasoner,
                    "repetition": repetition,
                    "events_per_second": profile.events_per_second,
                    "duration_seconds": profile.duration_seconds,
                    "synthetic_users": profile.users,
                    "target_triples": profile.target_triples,
                    "rule_count": profile.rule_count,
                    "requested_node_count": requested_nodes,
                    "node_count": effective_nodes,
                }
                stop_key = (reasoner, profile.dimension)
                if (
                    load_config.stop_after_timeout
                    and profile.dimension != "node_count"
                    and stop_key in stopped_dimensions
                ):
                    summary_rows.append(
                        {
                            **common,
                            "status": "skipped_after_timeout",
                            "error": stopped_dimensions[stop_key],
                            "events_offered": profile.offered_events,
                            "events_processed": "",
                            "events_lost": "",
                            "timed_out": False,
                            "timeout_phase": "early-stop",
                            "timeout_seconds": load_config.point_timeout_seconds,
                        }
                    )
                    print(
                        "[load] "
                        f"architecture={architecture} profile={profile.name} "
                        f"dimension={profile.dimension} reasoner={reasoner} "
                        "status=skipped_after_timeout",
                        flush=True,
                    )
                    continue
                print(
                    "[load] "
                    f"architecture={architecture} profile={profile.name} "
                    f"dimension={profile.dimension} reasoner={reasoner} "
                    f"repetition={repetition}/{load_config.repetitions} "
                    f"eps={profile.events_per_second:g} users={profile.users} "
                    f"triples={profile.target_triples or 'generated'} "
                    f"rules={profile.rule_count} nodes={effective_nodes} "
                    "phase=prepare status=running",
                    flush=True,
                )
                pipeline_started = perf_counter_ns()
                prepared: dict[str, dict[str, Any]] = {}
                prepare_wall_ms = 0.0
                prepare_error = ""
                prepare_timeout = min(
                    load_config.request_timeout_seconds,
                    load_config.point_timeout_seconds,
                )
                payload = _prepare_payload(
                    profile,
                    reasoner,
                    load_config.seed,
                    prepare_timeout,
                )
                try:
                    prepare_wall_ms, prepared = _parallel(
                        endpoints,
                        "/prepare",
                        {endpoint.url: payload for endpoint in endpoints},
                        phase="load-prepare",
                        timeout=prepare_timeout,
                        retries=0,
                    )
                except Exception as error:
                    prepare_error = f"{type(error).__name__}: {error}"

                if prepare_error:
                    offered = profile.offered_events
                    failure_status = (
                        "prepare_timeout"
                        if _is_timeout(prepare_error)
                        else "prepare_failed"
                    )
                    summary_rows.append(
                        {
                            **common,
                            "status": failure_status,
                            "error": prepare_error,
                            "events_offered": offered,
                            "events_processed": 0,
                            "events_lost": offered,
                            "event_loss_percent": 100.0,
                            "timed_out": failure_status == "prepare_timeout",
                            "timeout_phase": (
                                "prepare"
                                if failure_status == "prepare_timeout"
                                else ""
                            ),
                            "timeout_seconds": (
                                load_config.request_timeout_seconds
                                if failure_status == "prepare_timeout"
                                else ""
                            ),
                            "prepare_wall_ms": prepare_wall_ms,
                            "inference_wall_ms": "",
                            "recovery_wall_ms": "",
                            "recovery_scope": "application_state_rebuild",
                        }
                    )
                    for event_id in range(offered):
                        query_offset = (
                            (repetition - 1) * offered
                        ) % len(specs)
                        spec = specs[(query_offset + event_id) % len(specs)]
                        event_rows.append(
                            {
                                **common,
                                "event_id": event_id,
                                "query_id": spec.id,
                                "truth_alert": _truth(spec),
                                "predicted_alert": "",
                                "processed": False,
                                "lost_reason": failure_status,
                                "latency_ms": "",
                                "engine_duration_ms": "",
                                "role": "",
                                "endpoint": "",
                            }
                        )
                    for endpoint in endpoints:
                        node_rows.append(
                            {
                                **common,
                                "endpoint": endpoint.url,
                                "role": endpoint.role,
                                "status": failure_status,
                                "error": prepare_error,
                            }
                        )
                    print(
                        "[load] "
                        f"architecture={architecture} profile={profile.name} "
                        f"reasoner={reasoner} phase=prepare status=failed "
                        f"error={prepare_error}",
                        flush=True,
                    )
                    if (
                        failure_status == "prepare_timeout"
                        and profile.dimension != "node_count"
                    ):
                        stopped_dimensions[stop_key] = prepare_error
                    continue

                def invoke(
                    endpoint: Endpoint,
                    query_ids: list[str],
                    timeout: float,
                ) -> dict[str, Any]:
                    return _request(
                        endpoint.url,
                        "/queries",
                        # Keep the server-side budget just below urllib's
                        # socket deadline so the worker remains reusable.
                        {
                            "query_ids": query_ids,
                            "phase_timeout_seconds": max(
                                timeout - 1.0,
                                0.1,
                            ),
                        },
                        timeout=timeout,
                        retries=0,
                    )

                elapsed_before_stream = (
                    perf_counter_ns() - pipeline_started
                ) / 1_000_000_000
                remaining_point_budget = (
                    load_config.point_timeout_seconds - elapsed_before_stream
                )
                if remaining_point_budget <= 0:
                    remaining_point_budget = 0.001
                stream_summary, events, role_metrics = _run_event_stream(
                    profile,
                    load_config,
                    specs,
                    endpoints,
                    invoke,
                    common,
                    point_timeout_seconds=remaining_point_budget,
                )
                event_rows.extend(events)

                recovery_wall_ms = 0.0
                recovered: dict[str, dict[str, Any]] = {}
                recovery_error = ""
                try:
                    recovery_wall_ms, recovered = _parallel(
                        endpoints,
                        "/recover",
                        {
                            endpoint.url: {
                                "phase_timeout_seconds": max(
                                    load_config.recovery_timeout_seconds
                                    - 1.0,
                                    0.1,
                                )
                            }
                            for endpoint in endpoints
                        },
                        phase="load-recovery",
                        timeout=load_config.recovery_timeout_seconds,
                        retries=0,
                    )
                except Exception as error:
                    recovery_error = f"{type(error).__name__}: {error}"

                pipeline_wall_ms = (
                    perf_counter_ns() - pipeline_started
                ) / 1_000_000
                first_prepared = next(iter(prepared.values()))
                inference_wall_ms = max(
                    float(item["reasoning_ms"]) for item in prepared.values()
                )
                resources = _resource_summary(
                    prepared,
                    recovered,
                    role_metrics,
                    endpoints,
                    pipeline_wall_ms,
                )
                status = (
                    (
                        "recovery_timeout"
                        if _is_timeout(recovery_error)
                        else "recovery_failed"
                    )
                    if recovery_error
                    else (
                        "workload_timeout"
                        if stream_summary["timed_out"]
                        else "completed"
                    )
                )
                if (
                    status in {"workload_timeout", "recovery_timeout"}
                    and profile.dimension != "node_count"
                ):
                    stopped_dimensions[stop_key] = (
                        recovery_error
                        or f"{profile.name} exceeded the configured point budget"
                    )
                summary_rows.append(
                    {
                        **common,
                        "status": status,
                        "error": recovery_error,
                        "timeout_phase": (
                            "recovery"
                            if status == "recovery_timeout"
                            else (
                                "workload"
                                if status == "workload_timeout"
                                else ""
                            )
                        ),
                        "timeout_seconds": (
                            load_config.recovery_timeout_seconds
                            if status == "recovery_timeout"
                            else (
                                load_config.point_timeout_seconds
                                if status == "workload_timeout"
                                else ""
                            )
                        ),
                        "input_triples_per_node": first_prepared[
                            "input_triples"
                        ],
                        "aggregate_input_triples": sum(
                            int(item["input_triples"])
                            for item in prepared.values()
                        ),
                        "synthetic_triples": first_prepared[
                            "synthetic_triples"
                        ],
                        "synthetic_elements": (
                            profile.users + profile.offered_events
                        ),
                        "output_triples_per_node": first_prepared[
                            "output_triples"
                        ],
                        "inferred_triples_per_node": first_prepared[
                            "inferred_triples"
                        ],
                        "prepare_wall_ms": prepare_wall_ms,
                        "inference_wall_ms": inference_wall_ms,
                        "inference_node_ms_sum": sum(
                            float(item["reasoning_ms"])
                            for item in prepared.values()
                        ),
                        "recovery_wall_ms": recovery_wall_ms,
                        "recovery_scope": "application_state_rebuild",
                        "pipeline_wall_ms": pipeline_wall_ms,
                        **stream_summary,
                        **resources,
                    }
                )
                endpoint_by_url = {
                    endpoint.url: endpoint for endpoint in endpoints
                }
                for url, item in prepared.items():
                    role = endpoint_by_url[url].role
                    event_metrics = role_metrics[role]
                    recovery_metrics = recovered.get(url, {})
                    phase_metrics = (item, recovery_metrics)
                    total_cpu_ms = (
                        sum(
                            float(phase.get("process_cpu_ms", 0.0))
                            for phase in phase_metrics
                        )
                        + event_metrics["process_cpu_ms"]
                    )
                    total_disk_read = (
                        sum(
                            float(phase.get("disk_read_bytes", 0.0))
                            for phase in phase_metrics
                        )
                        + event_metrics["disk_read_bytes"]
                    )
                    total_disk_write = (
                        sum(
                            float(phase.get("disk_write_bytes", 0.0))
                            for phase in phase_metrics
                        )
                        + event_metrics["disk_write_bytes"]
                    )
                    total_network = (
                        sum(
                            float(phase.get("request_bytes", 0.0))
                            + float(phase.get("response_bytes", 0.0))
                            for phase in phase_metrics
                        )
                        + event_metrics["request_bytes"]
                        + event_metrics["response_bytes"]
                    )
                    node_rows.append(
                        {
                            **common,
                            "endpoint": url,
                            "role": role,
                            "status": status,
                            "error": recovery_error,
                            "prepare_reasoning_ms": item["reasoning_ms"],
                            "prepare_cpu_ms": item["process_cpu_ms"],
                            "prepare_current_rss_kib": item[
                                "current_rss_kib"
                            ],
                            "prepare_peak_rss_kib": item["peak_rss_kib"],
                            "prepare_disk_read_bytes": item.get(
                                "disk_read_bytes", 0
                            ),
                            "prepare_disk_write_bytes": item.get(
                                "disk_write_bytes", 0
                            ),
                            "prepare_network_body_bytes": (
                                float(item.get("request_bytes", 0.0))
                                + float(item.get("response_bytes", 0.0))
                            ),
                            **event_metrics,
                            "recovery_ms": recovery_metrics.get(
                                "recovery_ms", ""
                            ),
                            "recovery_cpu_ms": recovery_metrics.get(
                                "process_cpu_ms", ""
                            ),
                            "recovery_current_rss_kib": recovery_metrics.get(
                                "current_rss_kib", ""
                            ),
                            "recovery_peak_rss_kib": recovery_metrics.get(
                                "peak_rss_kib", ""
                            ),
                            "recovery_disk_read_bytes": recovery_metrics.get(
                                "disk_read_bytes", ""
                            ),
                            "recovery_disk_write_bytes": recovery_metrics.get(
                                "disk_write_bytes", ""
                            ),
                            "recovery_network_body_bytes": (
                                float(recovery_metrics.get("request_bytes", 0.0))
                                + float(
                                    recovery_metrics.get(
                                        "response_bytes", 0.0
                                    )
                                )
                            ),
                            "node_process_cpu_time_ms": total_cpu_ms,
                            "node_disk_read_bytes": total_disk_read,
                            "node_disk_write_bytes": total_disk_write,
                            "node_disk_io_bytes": (
                                total_disk_read + total_disk_write
                            ),
                            "node_network_body_bytes": total_network,
                            "node_max_current_rss_kib": max(
                                float(item.get("current_rss_kib", 0.0)),
                                event_metrics["max_current_rss_kib"],
                                float(
                                    recovery_metrics.get(
                                        "current_rss_kib", 0.0
                                    )
                                ),
                            ),
                        }
                    )
                print(
                    "[load] "
                    f"architecture={architecture} profile={profile.name} "
                    f"reasoner={reasoner} status={status} "
                    f"processed={stream_summary['events_processed']}/"
                    f"{stream_summary['events_offered']} "
                    f"p95_ms={stream_summary['latency_p95_ms']:.2f} "
                    f"inference_ms={inference_wall_ms:.2f} "
                    f"recovery_ms={recovery_wall_ms:.2f}",
                    flush=True,
                )

    output = output_root / architecture
    write_dict_rows(
        output / "summary.csv",
        summary_rows,
        empty_message="Load benchmark produced no summary rows",
    )
    write_dict_rows(
        output / "event-runs.csv",
        event_rows,
        empty_message="Load benchmark produced no event rows",
    )
    write_dict_rows(
        output / "node-runs.csv",
        node_rows,
        empty_message="Load benchmark produced no node rows",
    )
    metadata = {
        **release_identity(),
        "execution_policy": execution_metadata(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "architecture": architecture,
        "topology": {"endpoint_override": list(endpoint_urls or [])},
        "python": platform.python_version(),
        "platform": platform.platform(),
        "project_root": str(benchmark_config.root),
        "load_config": str(load_config.path),
        "profiles": [asdict(profile) for profile in load_config.profiles],
        "available_endpoints": [
            {"url": endpoint.url, "role": endpoint.role}
            for endpoint in all_endpoints
        ],
        "reasoners": list(benchmark_config.reasoners),
        "query_ids": [spec.id for spec in specs],
        "query_count": len(specs),
        "alert_query_ids": [spec.id for spec in specs if _is_alert(spec)],
        "alert_query_count": sum(_is_alert(spec) for spec in specs),
        "event_definition": "one scheduled SPARQL alert evaluation",
        "event_loss_definition": (
            "queue-capacity rejection, request/phase timeout or worker error"
        ),
        "latency_definition": (
            "scheduled arrival to completed response; includes queue, "
            "transport and SPARQL execution"
        ),
        "recovery_scope": "application_state_rebuild, not host reboot",
        "timeout_semantics": (
            "local coordinator deadline; distributed workers use an internal "
            "Unix timer one second before the HTTP socket deadline"
        ),
        "resource_scope": (
            "worker process CPU/RSS and Linux procfs disk bytes; HTTP JSON "
            "body bytes exclude TCP/IP headers"
        ),
        "timeouts": {
            "request_seconds": load_config.request_timeout_seconds,
            "point_seconds": load_config.point_timeout_seconds,
            "stop_after_timeout": load_config.stop_after_timeout,
            "recovery_seconds": load_config.recovery_timeout_seconds,
        },
    }
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output
