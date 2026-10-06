"""One isolated physical-host measurement; JSON-only stdout protocol."""
from __future__ import annotations

from dataclasses import asdict
from importlib.metadata import version
import os
import platform
import sys
from time import perf_counter

from ..policy_evaluation.resources import ResourceSampler
from .adapters import build_adapter
from .workload import operational, quality


def execute(payload: dict) -> dict:
    if not sys.platform.startswith("linux"):
        raise RuntimeError("Physical comparison measurements require Linux procfs; portable unit checks do not constitute physical measurements")
    workload = payload["workload"]
    # Only public inputs are passed to adapters; the oracle stays in the runner.
    adapter_input = {key: workload[key] for key in ("resources", "rules", "static_plan")}
    with ResourceSampler() as sampler:
        adapter, setup_ms = build_adapter(payload["strategy"], adapter_input)
    setup_resources = asdict(sampler.measurement())
    for _ in range(payload["warmup"]):
        for event in workload["scenarios"]:
            adapter.decide(event["context"])
    rows = []
    decisions = []
    cumulative_ms = 0.0
    with ResourceSampler() as sampler:
        for event in payload["events"]:
            started = perf_counter()
            plan = adapter.decide(event["context"])
            latency = (perf_counter() - started) * 1000
            cumulative_ms += latency
            decisions.append((event, plan, latency, cumulative_ms))
    # Acceptance scoring is outside CPU/RSS and decision-throughput measurement.
    for event, plan, latency, cumulative in decisions:
        actual = operational(plan)
        rows.append({
            "event_index": event["event_index"], "scenario": event["id"], "context": event["context"],
            "decision_ms": latency, "cumulative_decision_ms": cumulative,
            "active_policy_count": len(plan.policies), "categories": list(plan.categories),
            "actual": actual, "expected": event["expected"], **quality(actual, event["expected"]),
        })
    measurements = asdict(sampler.measurement())
    return {
        "measurement_contract": "comparison-v2-complete-context-warmup",
        "status": "completed", "events": rows, "setup_ms": setup_ms,
        "reasoning_ms": adapter.reasoning_ms, "explicit_triples": adapter.explicit_triples,
        "closure_triples": adapter.closure_triples, "measurement": measurements,
        "setup_measurement": setup_resources,
        "throughput_decisions_per_second": len(rows) / max(measurements["total_processing_ms"] / 1000, 1e-12),
        "setup_amortized_throughput": len(rows) / max((setup_ms + measurements["total_processing_ms"]) / 1000, 1e-12),
        "host": {"hostname": platform.node(), "platform": platform.platform(), "python": sys.version,
                 "cpu_count": os.cpu_count(), "rdflib": version("rdflib"), "owlrl": version("owlrl"),
                 "memory_total_kib": _memory()},
    }


def _memory():
    try:
        with open("/proc/meminfo") as handle:
            return int(next(line for line in handle if line.startswith("MemTotal:")).split()[1])
    except (OSError, StopIteration):
        return None
