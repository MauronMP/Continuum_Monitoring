"""Reject corrupted scientific evidence instead of plotting plausible results."""
from __future__ import annotations

import math


def nonnegative(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"Invalid {label}: expected a finite, non-negative measurement")


def validate_measurement(record, expected_count):
    events = record.get("events")
    if not isinstance(events, list) or len(events) != expected_count or not events:
        raise ValueError("Completed job has missing/extra events")
    total = 0.0
    for index, event in enumerate(events):
        if event["event_index"] != index:
            raise ValueError("Non-contiguous event indices")
        nonnegative(event["decision_ms"], "decision latency")
        total += event["decision_ms"]
        if not math.isclose(event["cumulative_decision_ms"], total, rel_tol=1e-9, abs_tol=1e-8):
            raise ValueError("Cumulative time is not the sum of decision times")
        for key in ("coverage", "over_monitoring", "under_monitoring"):
            nonnegative(event[key], key)
            if event[key] > 1:
                raise ValueError(f"{key} exceeds one")
        if type(event["plan_correct"]) is not bool:
            raise ValueError("plan_correct must be a Boolean")
        from .workload import quality
        checked = quality(event["actual"], event["expected"])
        if any(event[key] != value for key, value in checked.items()):
            raise ValueError("Stored correctness scores disagree with actual/expected plans")
    for key in ("setup_ms", "reasoning_ms", "throughput_decisions_per_second", "setup_amortized_throughput"):
        nonnegative(record[key], key)
    for phase in ("measurement", "setup_measurement"):
        for key, value in record[phase].items():
            if key == "memory_measurement_kind":
                if value not in ("sampled-current-process-rss", "process-lifetime-peak-rss", "unavailable"):
                    raise ValueError("Unknown memory measurement kind")
                continue
            nonnegative(value, f"{phase}.{key}")


def validate_records(records):
    seen = set()
    identifiers = set()
    traces = {}
    contracts = set()
    for record in records:
        key = (record["node"], record["experiment"], record["size"], record["repetition"], record["strategy"])
        if record["job_id"] in identifiers:
            raise ValueError("Duplicate job identifier")
        identifiers.add(record["job_id"])
        if key in seen:
            raise ValueError(f"Duplicate repetition would inflate sample size: {key}")
        seen.add(key)
        if record["status"] not in ("completed", "timeout", "failed", "unavailable", "invalid"):
            raise ValueError(f"Unknown outcome: {record['status']}")
        block = key[:-1]
        signature = (record["trace_sha256"], record["workload_sha256"])
        if block in traces and traces[block] != signature:
            raise ValueError("Strategies in a paired block received different inputs")
        traces[block] = signature
        if record["status"] == "completed":
            validate_measurement(record, record["event_count"])
            contracts.add(record.get("measurement_contract", "comparison-v1"))
    if len(contracts) > 1:
        raise ValueError("Mixed measurement contracts require separate reports")
