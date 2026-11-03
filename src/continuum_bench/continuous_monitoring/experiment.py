from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from time import monotonic, sleep

from ..deployment import container_states, semantic_environment
from ..experiment import (
    _expected_fragment_semantics,
    _prepare_workers,
    _tool,
    generate_dataset,
    partition_dataset,
)
from ..protocol import request_json, wait_ready
from ..query_execution import execute_logical_query
from ..resources import ResourceSampler
from ..topology import Topology
from .config import MonitoringConfig, MonitoringTask
from .scheduler import run_scheduler


def _run_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"monitoring-{stamp}-{sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:8]}"


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def _split_resources(path: Path, phase_path: Path) -> None:
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.is_file() else []
    events = [row for row in rows if "event" in row]
    samples = [row for row in rows if "event" not in row]
    _write_jsonl(path, samples)
    _write_jsonl(phase_path, events)


def _source_identity(root: Path) -> dict:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
    status = subprocess.run(["git", "status", "--short"], cwd=root, capture_output=True, text=True, check=False)
    return {
        "git_commit": result.stdout.strip() if result.returncode == 0 else None,
        "dirty": bool(status.stdout.strip()),
    }


def _task_executor(config: MonitoringConfig, topology: Topology, queries: dict[str, dict], layout: str):
    logical_rows: list[dict] = []
    physical_rows: list[dict] = []

    def execute(task: MonitoringTask, scheduled: float, task_deadline: float) -> dict:
        started = monotonic()
        query_count = 0
        physical_count = 0
        for query_id in task.query_ids:
            remaining = task_deadline - (monotonic() - started)
            if remaining <= 0:
                return {
                    "status": "logical_timeout",
                    "logical_queries": query_count,
                    "physical_requests": physical_count,
                }
            query = queries[query_id]
            logical, physical = execute_logical_query(
                topology.hosts,
                query,
                round_=1,
                query_index=int(query["order"]) - 1,
                layout=layout,
                physical_timeout=config.physical_timeout_seconds,
                logical_timeout=min(config.logical_timeout_seconds, remaining),
            )
            context = {
                "task_id": task.task_id,
                "policy_id": task.policy_id,
                "demand_level": task.demand_level,
                "scheduled_at_monotonic": scheduled,
            }
            logical.update(context)
            for row in physical:
                row.update(context, layout=layout)
            logical_rows.append(logical)
            physical_rows.extend(physical)
            query_count += 1
            physical_count += len(physical)
            if logical["status"] == "query_timeout":
                return {
                    "status": "logical_timeout",
                    "logical_queries": query_count,
                    "physical_requests": physical_count,
                }
            if logical["status"] != "completed":
                return {
                    "status": "physical_failure",
                    "logical_queries": query_count,
                    "physical_requests": physical_count,
                }
            if query.get("expectation") == "non_empty" and int(logical["result_count"]) == 0:
                return {
                    "status": "semantic_failure",
                    "logical_queries": query_count,
                    "physical_requests": physical_count,
                }
        return {"status": "completed", "logical_queries": query_count, "physical_requests": physical_count}

    return execute, logical_rows, physical_rows


def run(config: MonitoringConfig, topology: Topology, demand_levels: set[str] | None = None) -> Path:
    root = config.benchmark.root
    run_dir = root / "outputs" / _run_id()
    run_dir.mkdir(parents=True)
    query_manifest = json.loads((root / "queries/manifest.json").read_text())
    queries = {item["id"]: item | {"query": (root / item["path"]).read_text()} for item in query_manifest["queries"]}
    levels = tuple(level for level in config.demand_levels if not demand_levels or level in demand_levels)
    if demand_levels and set(levels) != demand_levels:
        raise ValueError(f"unknown demand levels: {sorted(demand_levels - set(levels))}")
    semantic = semantic_environment(config.benchmark, topology)
    expected = {
        "topology_fingerprint": semantic["CONTINUUM_TOPOLOGY_FINGERPRINT"],
        "ontology_digest": semantic["CONTINUUM_ONTOLOGY_DIGEST"],
        "query_catalog_digest": semantic["CONTINUUM_QUERY_CATALOG_DIGEST"],
        "query_count": int(semantic["CONTINUUM_QUERY_COUNT"]),
        "max_prepare_bytes": int(semantic["CONTINUUM_MAX_PREPARE_BYTES"]),
    }
    manifest = {
        "experiment": "policy-driven-periodic-monitoring-overhead",
        "status": "running",
        "started_at": datetime.now(UTC).isoformat(),
        "source": _source_identity(root),
        "configuration_digest": config.digest,
        "ontology_digest": expected["ontology_digest"],
        "query_catalog_digest": expected["query_catalog_digest"],
        "topology_fingerprint": topology.fingerprint,
        "policy_configuration_digest": sha256(
            json.dumps(config.tasks, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "demand_levels": levels,
    }
    _write_json(run_dir / "manifest.json", manifest)
    (run_dir / "configuration.toml").write_bytes(config.path.read_bytes())
    (run_dir / "benchmark-configuration.toml").write_bytes(config.benchmark.path.read_bytes())
    _write_json(run_dir / "topology.json", {"name": topology.name, "hosts": [host.__dict__ for host in topology.hosts]})
    worker_build_identity = [
        wait_ready(
            host.endpoint,
            deadline_seconds=config.benchmark.deployment["health_timeout_seconds"],
            require_idle=True,
            expected=expected,
        )
        for host in topology.hosts
    ]
    manifest["worker_build_identity"] = worker_build_identity
    _write_json(run_dir / "manifest.json", manifest)
    failures = 0
    rust_tool = _tool(root)
    for scenario in config.benchmark.scenarios:
        if scenario.name not in config.scenarios:
            continue
        scenario_dir = run_dir / scenario.name
        scenario_dir.mkdir()
        dataset_path, dataset = generate_dataset(config.benchmark, scenario, scenario_dir)
        for layout in config.layouts:
            layout_dir = scenario_dir / layout
            layout_dir.mkdir()
            reference_dir = layout_dir / "reference-fragments"
            reference, partition = partition_dataset(
                rust_tool, dataset_path, root / "ontology/benchmark/base.nt", topology.hosts, layout, reference_dir
            )
            expected_fragments = _expected_fragment_semantics(
                rust_tool, reference, reference_dir, layout_dir / "expected-semantics.json"
            )
            _write_json(layout_dir / "reference-partition.json", partition)
            conditions = (("idle", None),) if config.include_idle else ()
            conditions += tuple((level, level) for level in levels)
            for condition, level in conditions:
                condition_dir = layout_dir / condition
                condition_dir.mkdir()
                resolved = config.resolve_tasks(level) if level else ()
                _write_json(condition_dir / "resolved-tasks.json", [asdict(task) for task in resolved])
                for repetition in range(1, config.repetitions + 1):
                    rep_dir = condition_dir / f"rep-{repetition:02}"
                    rep_dir.mkdir()
                    result = {
                        "scenario": scenario.name,
                        "users": scenario.users,
                        "layout": layout,
                        "mode": "deployed_idle" if level is None else "active",
                        "demand_level": condition,
                        "repetition": repetition,
                        "dataset_digest": dataset["dataset_digest"],
                        "measurement_seconds": config.measurement_seconds,
                        "stabilization_seconds": config.stabilization_seconds,
                        "resolved_tasks_digest": config.resolved_digest(level) if level else None,
                    }
                    try:
                        for host in topology.hosts:
                            request_json(f"{host.endpoint}/reset", method="POST", timeout=30)
                        fragments, partition_meta = partition_dataset(
                            rust_tool,
                            dataset_path,
                            root / "ontology/benchmark/base.nt",
                            topology.hosts,
                            layout,
                            rep_dir / "fragments",
                        )
                        prepare_started = monotonic()
                        prepared = _prepare_workers(
                            topology.hosts,
                            fragments,
                            float(config.benchmark.experiment["prepare_hard_timeout_seconds"]),
                            expected_fragments,
                        )
                        for host in topology.hosts:
                            wait_ready(
                                host.endpoint,
                                deadline_seconds=config.benchmark.deployment["health_timeout_seconds"],
                                require_idle=True,
                                expected=expected
                                | {
                                    "dataset_digest": expected_fragments[host.id]["dataset_digest"],
                                    "closure_digest": expected_fragments[host.id]["closure_digest"],
                                },
                            )
                        result["preparation_seconds"] = monotonic() - prepare_started
                        result["partition"] = partition_meta
                        result["preparation"] = prepared
                        sleep(config.stabilization_seconds)
                        health_before = [
                            wait_ready(host.endpoint, deadline_seconds=30, require_idle=True, expected=expected)
                            for host in topology.hosts
                        ]
                        _write_json(rep_dir / "worker_health_before.json", health_before)
                        execute, logical, physical = _task_executor(config, topology, queries, layout)
                        resource_path = rep_dir / "resource_samples.jsonl"
                        with ResourceSampler(
                            topology.hosts,
                            str(config.benchmark.deployment["ssh_user"]),
                            str(config.benchmark.deployment["image"]),
                            resource_path,
                            config.sample_interval_seconds,
                        ) as sampler:
                            sampler.set_phase("monitoring_idle" if level is None else "monitoring_active")
                            if level is None:
                                sleep(config.measurement_seconds)
                                scheduler = {
                                    "events": [],
                                    "scheduled_cycles": 0,
                                    "completed_on_time": 0,
                                    "completed_late": 0,
                                    "missed_cycles": 0,
                                    "logical_timeouts": 0,
                                    "semantic_failures": 0,
                                    "physical_failures": 0,
                                    "monitoring_compliance": None,
                                    "scheduler_busy_seconds": 0.0,
                                    "scheduler_idle_seconds": config.measurement_seconds,
                                    "scheduler_utilization": 0.0,
                                    "max_pending_monitoring_tasks": 0,
                                }
                            else:
                                scheduler = run_scheduler(
                                    resolved, config.measurement_seconds, config.logical_timeout_seconds, execute
                                )
                        _split_resources(resource_path, rep_dir / "phase_events.jsonl")
                        events = scheduler.pop("events")
                        _write_jsonl(rep_dir / "scheduler_events.jsonl", events)
                        _write_jsonl(rep_dir / "task_executions.jsonl", [e for e in events if not e["missed_cycle"]])
                        _write_jsonl(rep_dir / "logical_queries.jsonl", logical)
                        _write_jsonl(rep_dir / "physical_queries.jsonl", physical)
                        result.update(scheduler)
                        result["logical_queries"] = len(logical)
                        result["physical_requests"] = len(physical)
                        result["status"] = "completed"
                        _write_json(
                            rep_dir / "worker_health_after.json",
                            [
                                wait_ready(host.endpoint, deadline_seconds=30, require_idle=True, expected=expected)
                                for host in topology.hosts
                            ],
                        )
                    except Exception as error:
                        failures += 1
                        result.update(status="failed", error=str(error))
                    for filename in (
                        "scheduler_events.jsonl",
                        "task_executions.jsonl",
                        "logical_queries.jsonl",
                        "physical_queries.jsonl",
                        "resource_samples.jsonl",
                        "phase_events.jsonl",
                    ):
                        path = rep_dir / filename
                        if not path.exists():
                            path.write_text("")
                    for filename in ("worker_health_before.json", "worker_health_after.json"):
                        path = rep_dir / filename
                        if not path.exists():
                            _write_json(path, [])
                    _write_json(rep_dir / "container_state.json", container_states(config.benchmark, topology))
                    _write_json(rep_dir / "result.json", result)
    manifest.update(
        status="completed_with_failures" if failures else "completed",
        failures=failures,
        finished_at=datetime.now(UTC).isoformat(),
    )
    _write_json(run_dir / "manifest.json", manifest)
    from .reporting import report

    report(run_dir)
    return run_dir
