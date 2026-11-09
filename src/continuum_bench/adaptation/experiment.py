from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import UTC, datetime
from functools import partial
from hashlib import sha256
from pathlib import Path
from statistics import fmean
from threading import Thread
from time import monotonic, sleep

from ..continuous_monitoring.experiment import _recover_after_timeout, _task_executor
from ..continuous_monitoring.scheduler import run_scheduler
from ..deployment import semantic_environment
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
from ..topology import Host, Topology
from .config import AdaptationConfig
from .deployment import collect_candidate_inventory, deploy_read_only_replica
from .logic import ReplicaRouter, analyze_trigger, evaluate_trigger, percentile, plan_adaptation


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _run_id() -> str:
    return (
        "adaptation-"
        + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + sha256(_timestamp().encode()).hexdigest()[:8]
    )


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, values: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(value) + "\n" for value in values), encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.is_file() else []


def _queries(config: AdaptationConfig) -> tuple[dict, dict[str, dict]]:
    manifest = json.loads((config.benchmark.root / "queries/manifest.json").read_text())
    queries = {
        item["id"]: item | {"query": (config.benchmark.root / item["path"]).read_text(encoding="utf-8")}
        for item in manifest["queries"]
    }
    return manifest, queries


def _expected_worker_contract(config: AdaptationConfig, topology: Topology) -> dict:
    semantic = semantic_environment(config.benchmark, topology)
    return {
        "topology_fingerprint": semantic["CONTINUUM_TOPOLOGY_FINGERPRINT"],
        "ontology_digest": semantic["CONTINUUM_ONTOLOGY_DIGEST"],
        "query_catalog_digest": semantic["CONTINUUM_QUERY_CATALOG_DIGEST"],
        "query_count": int(semantic["CONTINUUM_QUERY_COUNT"]),
        "max_prepare_bytes": int(semantic["CONTINUUM_MAX_PREPARE_BYTES"]),
    }


def _resource_rows(path: Path) -> list[dict]:
    return [row for row in _read_jsonl(path) if row.get("event") is None and row.get("error") is None]


def summarize_window(
    scheduler: dict,
    logical: list[dict],
    physical: list[dict],
    resources: list[dict],
    application_duration_seconds: float | None = None,
) -> dict:
    logical_latencies = [float(row["logical_duration_ms"]) for row in logical if row.get("logical_duration_ms")]
    schedule_lags = [
        float(row["schedule_lag_seconds"]) for row in scheduler["events"] if row.get("schedule_lag_seconds") is not None
    ]
    cpu = [float(row["cpu_percent"]) for row in resources if row.get("cpu_percent") is not None]
    memory = [float(row["memory_bytes"]) for row in resources if row.get("memory_bytes") is not None]
    by_host = {}
    for host in sorted({str(row["host"]) for row in resources if row.get("host")}):
        rows = [row for row in resources if row.get("host") == host]
        host_cpu = [float(row["cpu_percent"]) for row in rows if row.get("cpu_percent") is not None]
        host_memory = [float(row["memory_bytes"]) for row in rows if row.get("memory_bytes") is not None]
        rx = [int(row["network_rx_bytes"]) for row in rows if row.get("network_rx_bytes") is not None]
        tx = [int(row["network_tx_bytes"]) for row in rows if row.get("network_tx_bytes") is not None]
        by_host[host] = {
            "cpu_mean_percent": fmean(host_cpu) if host_cpu else None,
            "cpu_p95_percent": percentile(host_cpu, 0.95),
            "cpu_peak_percent": max(host_cpu) if host_cpu else None,
            "memory_mean_bytes": fmean(host_memory) if host_memory else None,
            "memory_peak_bytes": max(host_memory) if host_memory else None,
            "network_rx_bytes": max(rx) - min(rx) if len(rx) > 1 else 0,
            "network_tx_bytes": max(tx) - min(tx) if len(tx) > 1 else 0,
        }
    network_rx = sum(int(item["network_rx_bytes"]) for item in by_host.values())
    network_tx = sum(int(item["network_tx_bytes"]) for item in by_host.values())
    application = [row for row in logical if row.get("workload_kind") == "scalability_catalog"]
    monitoring = [row for row in logical if row.get("workload_kind") == "policy_monitoring"]
    application_latencies = [float(row["logical_duration_ms"]) for row in application if row.get("logical_duration_ms")]
    monitoring_latencies = [float(row["logical_duration_ms"]) for row in monitoring if row.get("logical_duration_ms")]
    return {
        "logical_latency_p50_ms": percentile(logical_latencies, 0.50),
        "logical_latency_p95_ms": percentile(logical_latencies, 0.95),
        "logical_latency_p99_ms": percentile(logical_latencies, 0.99),
        "logical_timeouts": int(scheduler.get("logical_timeouts", 0)),
        "monitoring_compliance": scheduler.get("monitoring_compliance"),
        "schedule_lag_p50_seconds": percentile(schedule_lags, 0.50),
        "schedule_lag_p95_seconds": percentile(schedule_lags, 0.95),
        "schedule_lag_p99_seconds": percentile(schedule_lags, 0.99),
        "cpu_mean_percent": fmean(cpu) if cpu else None,
        "cpu_peak_percent": max(cpu) if cpu else None,
        "memory_mean_bytes": fmean(memory) if memory else None,
        "memory_peak_bytes": max(memory) if memory else None,
        "network_rx_bytes": network_rx,
        "network_tx_bytes": network_tx,
        "physical_query_executions": len(physical),
        "completed_physical_query_executions": sum(row.get("status") == "completed" for row in physical),
        "application_queries": len(application),
        "application_completed_queries": sum(row.get("status") == "completed" for row in application),
        "application_timeouts": sum(row.get("status") == "query_timeout" for row in application),
        "application_duration_seconds": application_duration_seconds,
        "application_throughput_qps": (
            sum(row.get("status") == "completed" for row in application) / application_duration_seconds
            if application_duration_seconds
            else None
        ),
        "application_latency_p50_ms": percentile(application_latencies, 0.50),
        "application_latency_p95_ms": percentile(application_latencies, 0.95),
        "application_latency_p99_ms": percentile(application_latencies, 0.99),
        "monitoring_queries": len(monitoring),
        "monitoring_latency_p95_ms": percentile(monitoring_latencies, 0.95),
        "per_host": by_host,
    }


def _run_scalability_catalog(
    config: AdaptationConfig,
    topology: Topology,
    queries: dict[str, dict],
    *,
    host_selector=None,
    replay_plan: list[dict] | None = None,
) -> dict:
    """Replay the scalability query catalog while policy monitoring observes the same workers."""
    ordered = sorted(queries.values(), key=lambda item: int(item["order"]))
    logical: list[dict] = []
    physical: list[dict] = []
    rounds: list[dict] = []
    aborted = None
    started = monotonic()
    users = next(item.users for item in config.benchmark.scenarios if item.name == config.scenario)
    by_id = {str(query["id"]): (index, query) for index, query in enumerate(ordered)}

    def execute_one(round_: int, index: int, query: dict) -> tuple[dict, list[dict]]:
        selected = host_selector(query, round_, index, config.layout) if host_selector else None
        logical_row, physical_rows = execute_logical_query(
            topology.hosts,
            query,
            round_,
            index,
            config.layout,
            physical_timeout=config.monitoring.physical_timeout_seconds,
            logical_timeout=config.monitoring.logical_timeout_seconds,
            selected_hosts=selected,
        )
        logical_row.update(
            workload_kind="scalability_catalog",
            scenario=config.scenario,
            users=users,
        )
        for row in physical_rows:
            row.update(
                workload_kind="scalability_catalog",
                scenario=config.scenario,
                users=users,
            )
        logical.append(logical_row)
        physical.extend(physical_rows)
        return logical_row, physical_rows

    try:
        if replay_plan is None:
            for round_ in range(1, config.scalability_query_rounds + 1):
                round_started = monotonic()
                round_logical = 0
                round_physical = 0
                for index, query in enumerate(ordered):
                    logical_row, physical_rows = execute_one(round_, index, query)
                    round_logical += 1
                    round_physical += len(physical_rows)
                    if logical_row["status"] == "query_timeout":
                        aborted = {
                            "failed_round": round_,
                            "failed_query_id": query["id"],
                            "failed_hosts": logical_row["failed_hosts"],
                        }
                        break
                rounds.append(
                    {
                        "round": round_,
                        "duration_seconds": monotonic() - round_started,
                        "logical_queries": round_logical,
                        "physical_executions": round_physical,
                    }
                )
                if aborted:
                    break
        else:
            round_started = monotonic()
            current_round = None
            round_logical = round_physical = 0
            for item in replay_plan:
                round_ = int(item["round"])
                if current_round is not None and round_ != current_round:
                    rounds.append(
                        {
                            "round": current_round,
                            "duration_seconds": monotonic() - round_started,
                            "logical_queries": round_logical,
                            "physical_executions": round_physical,
                        }
                    )
                    round_started = monotonic()
                    round_logical = round_physical = 0
                current_round = round_
                index, query = by_id[str(item["query_id"])]
                _, physical_rows = execute_one(round_, index, query)
                round_logical += 1
                round_physical += len(physical_rows)
            if current_round is not None:
                rounds.append(
                    {
                        "round": current_round,
                        "duration_seconds": monotonic() - round_started,
                        "logical_queries": round_logical,
                        "physical_executions": round_physical,
                    }
                )
        return {
            "status": "aborted_on_timeout" if aborted else "completed",
            "mode": "baseline" if replay_plan is None else "exact_baseline_sequence_replay",
            "configured_rounds": config.scalability_query_rounds,
            "completed_rounds": sum(item["logical_queries"] == len(ordered) for item in rounds),
            "query_catalog_size": len(ordered),
            "duration_seconds": monotonic() - started,
            "rounds": rounds,
            "aborted": aborted,
            "execution_plan": [{"round": row["round"], "query_id": row["query_id"]} for row in logical],
            "logical": logical,
            "physical": physical,
        }
    except Exception as error:
        return {
            "status": "failed",
            "mode": "baseline" if replay_plan is None else "exact_baseline_sequence_replay",
            "configured_rounds": config.scalability_query_rounds,
            "completed_rounds": sum(item["logical_queries"] == len(ordered) for item in rounds),
            "query_catalog_size": len(ordered),
            "duration_seconds": monotonic() - started,
            "rounds": rounds,
            "error": str(error),
            "execution_plan": [{"round": row["round"], "query_id": row["query_id"]} for row in logical],
            "logical": logical,
            "physical": physical,
        }


def require_same_workload(before: dict, after: dict) -> None:
    if before != after:
        raise RuntimeError("before and after monitoring workloads are not identical")


def _require_run_context(config: AdaptationConfig, run_dir: Path, topology: Topology | None = None) -> None:
    manifest = json.loads((run_dir / "manifest.json").read_text())
    if manifest.get("configuration_digest") != config.digest:
        raise ValueError("adaptation configuration differs from the configuration used by Observe")
    if topology is not None and manifest.get("topology_fingerprint") != topology.fingerprint:
        raise ValueError("active topology differs from the topology used by Observe")


def _run_monitoring_window(
    config: AdaptationConfig,
    topology: Topology,
    directory: Path,
    queries: dict[str, dict],
    fragments: dict[str, bytes],
    expected_fragments: dict[str, dict],
    expected: dict,
    *,
    host_selector=None,
    replica: Host | None = None,
    replica_container_name: str | None = None,
    application_replay_plan: list[dict] | None = None,
) -> dict:
    resolved = config.monitoring.resolve_tasks(config.demand_level)
    workload_identity = {
        "scenario": config.scenario,
        "layout": config.layout,
        "demand_level": config.demand_level,
        "measurement_seconds": config.measurement_seconds,
        "tasks": [asdict(task) for task in resolved],
        "resolved_tasks_digest": config.monitoring.resolved_digest(config.demand_level),
        "application_load": {
            "kind": "scalability_query_catalog_replay",
            "query_rounds": config.scalability_query_rounds,
            "query_catalog_size": len(queries),
            "concurrent_with_policy_monitoring": True,
        },
    }
    _write_json(directory / "workload.json", workload_identity)
    recover_baseline = partial(
        _recover_after_timeout,
        config.monitoring,
        topology,
        fragments=fragments,
        expected_fragments=expected_fragments,
        expected=expected,
    )

    def recover(host_ids: set[str]) -> dict:
        baseline_ids = host_ids & {host.id for host in topology.hosts}
        evidence = (
            recover_baseline(baseline_ids)
            if baseline_ids
            else {
                "recovery_count": 0,
                "recovery_seconds": 0.0,
                "worker_restart_count": 0,
                "recovery_succeeded": True,
            }
        )
        if replica is None or replica.id not in host_ids:
            return evidence
        try:
            source_expected = expected_fragments[
                next(key for key in expected_fragments if replica.id.startswith(key + "-"))
            ]
            wait_ready(
                replica.endpoint,
                deadline_seconds=config.monitoring.recovery_idle_timeout_seconds,
                require_idle=True,
                expected={
                    "dataset_digest": source_expected["dataset_digest"],
                    "closure_digest": source_expected["closure_digest"],
                },
            )
            return evidence
        except Exception as error:
            return evidence | {
                "recovery_count": int(evidence.get("recovery_count", 0)) + 1,
                "recovery_succeeded": False,
                "recovery_error": f"read-only replica did not recover to idle: {error}",
            }

    execute, logical, physical = _task_executor(
        config.monitoring,
        topology,
        queries,
        config.layout,
        recover,
        host_selector=host_selector,
    )
    sample_hosts = topology.hosts + ((replica,) if replica else ())
    names = {replica.id: replica_container_name} if replica and replica_container_name else {}
    resource_path = directory / "resource_samples.jsonl"
    application_outcome: dict = {}

    def application_load() -> None:
        application_outcome.update(
            _run_scalability_catalog(
                config,
                topology,
                queries,
                host_selector=host_selector,
                replay_plan=application_replay_plan,
            )
        )

    sleep(config.stabilization_seconds)
    with ResourceSampler(
        sample_hosts,
        str(config.benchmark.deployment["ssh_user"]),
        str(config.benchmark.deployment["image"]),
        resource_path,
        config.resource_sample_interval_seconds,
        names,
    ) as sampler:
        sampler.set_phase("adaptation_before" if replica is None else "adaptation_after")
        load_thread = Thread(target=application_load, name="adaptation-scalability-load")
        load_thread.start()
        scheduler = run_scheduler(
            resolved,
            config.measurement_seconds,
            config.monitoring.logical_timeout_seconds,
            execute,
        )
        load_thread.join()
    for row in logical:
        row["workload_kind"] = "policy_monitoring"
    for row in physical:
        row["workload_kind"] = "policy_monitoring"
    application_logical = list(application_outcome.pop("logical", []))
    application_physical = list(application_outcome.pop("physical", []))
    combined_logical = logical + application_logical
    combined_physical = physical + application_physical
    for row in combined_physical:
        row["routing_role"] = (
            "read_only_replica" if replica and row.get("host") == replica.id else "partition_participant"
        )
    resources = _resource_rows(resource_path)
    summary = summarize_window(
        scheduler,
        combined_logical,
        combined_physical,
        resources,
        application_outcome.get("duration_seconds"),
    )
    _write_jsonl(directory / "scheduler_events.jsonl", scheduler["events"])
    _write_jsonl(directory / "monitoring_logical_queries.jsonl", logical)
    _write_jsonl(directory / "monitoring_physical_queries.jsonl", physical)
    _write_jsonl(directory / "application_logical_queries.jsonl", application_logical)
    _write_jsonl(directory / "application_physical_queries.jsonl", application_physical)
    _write_jsonl(directory / "logical_queries.jsonl", combined_logical)
    _write_jsonl(directory / "physical_queries.jsonl", combined_physical)
    _write_json(directory / "application_load.json", application_outcome)
    _write_json(directory / "application_execution_plan.json", application_outcome.get("execution_plan", []))
    result = {
        "stage": "verification" if replica else "monitor",
        "mode": "measured",
        "status": "completed" if not scheduler.get("scheduler_halted") else "recovery_failed",
        "timestamp": _timestamp(),
        "policy_ids": sorted({task.policy_id for task in resolved}),
        "query_ids": sorted({query_id for task in resolved for query_id in task.query_ids}),
        "input_evidence": "execute/result.json" if replica else "configuration.toml",
        "workload": workload_identity,
        "scheduler": {key: value for key, value in scheduler.items() if key != "events"},
        "application_load": application_outcome,
        "metrics": summary,
    }
    _write_json(directory / "result.json", result)
    return {
        "result": result,
        "scheduler": scheduler,
        "logical": combined_logical,
        "physical": combined_physical,
        "resources": resources,
    }


def _policy_query(
    config: AdaptationConfig,
    topology: Topology,
    query: dict,
    *,
    round_: int = 1,
) -> dict:
    logical, physical = execute_logical_query(
        topology.hosts,
        query,
        round_,
        int(query["order"]) - 1,
        config.layout,
        physical_timeout=config.monitoring.physical_timeout_seconds,
        logical_timeout=config.monitoring.logical_timeout_seconds,
    )
    return {"query_id": query["id"], "logical": logical, "physical": physical}


def observe(config: AdaptationConfig, topology: Topology) -> Path:
    root = config.benchmark.root
    topology_ids = {host.id for host in topology.hosts}
    missing_trigger_hosts = set(config.trigger_resource_hosts) - topology_ids
    if missing_trigger_hosts:
        raise ValueError(
            f"adaptation trigger hosts are absent from the active topology: {sorted(missing_trigger_hosts)}"
        )
    if config.replica_source not in topology_ids:
        raise ValueError(f"fallback replica source is absent from the active topology: {config.replica_source}")
    run_dir = root / "outputs" / _run_id()
    before = run_dir / "before"
    before.mkdir(parents=True)
    manifest_queries, queries = _queries(config)
    expected = _expected_worker_contract(config, topology)
    manifest = {
        "experiment": "controlled-policy-driven-adaptation-demonstration",
        "status": "observing",
        "started_at": _timestamp(),
        "configuration_digest": config.digest,
        "scenario": config.scenario,
        "layout": config.layout,
        "stage_semantics": {
            "monitor": "real",
            "analyze": "simulated_rule_based",
            "plan": "simulated_rule_based",
            "execute": "scripted_manual",
            "verification": "real",
        },
        "query_catalog_digest": manifest_queries["query_catalog_digest"],
        "topology_fingerprint": topology.fingerprint,
    }
    _write_json(run_dir / "manifest.json", manifest)
    shutil.copy2(config.path, run_dir / "configuration.toml")
    shutil.copy2(config.benchmark.path, run_dir / "benchmark-configuration.toml")
    shutil.copy2(config.monitoring.path, run_dir / "monitoring-configuration.toml")
    _write_json(run_dir / "topology.json", {"name": topology.name, "hosts": [asdict(host) for host in topology.hosts]})
    for host in topology.hosts:
        wait_ready(host.endpoint, deadline_seconds=60, require_idle=True, expected=expected)
    scenario = next(item for item in config.benchmark.scenarios if item.name == config.scenario)
    dataset_path, dataset = generate_dataset(config.benchmark, scenario, before)
    fragments, partition = partition_dataset(
        _tool(root),
        dataset_path,
        root / "ontology/benchmark/base.nt",
        topology.hosts,
        config.layout,
        before / "fragments",
    )
    expected_fragments = _expected_fragment_semantics(
        _tool(root), fragments, before / "fragments", before / "expected-semantics.json"
    )
    for host in topology.hosts:
        request_json(f"{host.endpoint}/reset", method="POST", timeout=30)
    preparation = _prepare_workers(
        topology.hosts,
        fragments,
        float(config.benchmark.experiment["prepare_hard_timeout_seconds"]),
        expected_fragments,
    )
    for host in topology.hosts:
        wait_ready(
            host.endpoint,
            deadline_seconds=60,
            require_idle=True,
            expected=expected
            | {
                "dataset_digest": expected_fragments[host.id]["dataset_digest"],
                "closure_digest": expected_fragments[host.id]["closure_digest"],
            },
        )
    _write_json(before / "dataset-metadata.json", dataset)
    _write_json(before / "partition.json", partition)
    _write_json(before / "preparation.json", preparation)
    window = _run_monitoring_window(config, topology, before, queries, fragments, expected_fragments, expected)
    policy_context = _policy_query(config, topology, queries[config.adaptation_context_query_id])
    _write_json(before / "adaptation-policy-context.json", policy_context)
    trigger = evaluate_trigger(config, window["scheduler"], window["resources"])
    trigger["timestamp"] = _timestamp()
    trigger["input_evidence"] = "before/"
    _write_json(run_dir / "trigger.json", trigger)
    manifest.update(status="observed", observed_at=_timestamp(), trigger_satisfied=trigger["triggered"])
    _write_json(run_dir / "manifest.json", manifest)
    return run_dir


def analyze(config: AdaptationConfig, run_dir: Path) -> dict:
    _require_run_context(config, run_dir)
    if (run_dir / "analysis.json").exists():
        raise FileExistsError("Analyze evidence already exists for this run")
    trigger = json.loads((run_dir / "trigger.json").read_text())
    analysis = analyze_trigger(trigger, _timestamp())
    analysis["input_evidence"] = "trigger.json"
    analysis["policy_ids"] = [config.trigger_policy]
    analysis["query_ids"] = list(config.trigger_query_ids)
    _write_json(run_dir / "analysis.json", analysis)
    _update_manifest(run_dir, "analyzed")
    return analysis


def plan(config: AdaptationConfig, topology: Topology, run_dir: Path) -> dict:
    _require_run_context(config, run_dir, topology)
    if (run_dir / "plan.json").exists():
        raise FileExistsError("Plan evidence already exists for this run")
    analysis = json.loads((run_dir / "analysis.json").read_text())
    _, queries = _queries(config)
    capacity_required = analysis.get("conclusion") == "additional_capacity_required"
    semantic_evidence = (
        [_policy_query(config, topology, queries[query_id]) for query_id in config.candidate_query_ids]
        if capacity_required
        else []
    )
    candidates = collect_candidate_inventory(config, topology) if capacity_required else []
    before_metrics = json.loads((run_dir / "before/result.json").read_text()).get("metrics", {})
    measured_hosts = before_metrics.get("per_host", {})
    for candidate in candidates:
        observed = measured_hosts.get(str(candidate.get("id")), {})
        candidate["workload_cpu_mean_percent"] = observed.get("cpu_mean_percent")
        candidate["workload_cpu_p95_percent"] = observed.get("cpu_p95_percent")
        candidate["workload_cpu_peak_percent"] = observed.get("cpu_peak_percent")
    semantic_evidence_valid = bool(semantic_evidence) and all(
        item["logical"].get("status") == "completed" and int(item["logical"].get("result_count") or 0) > 0
        for item in semantic_evidence
    )
    result = plan_adaptation(config, analysis, candidates, _timestamp())
    if result.get("status") == "planned" and not semantic_evidence_valid:
        result.update(
            status="planning_failed",
            action=None,
            target=None,
            selected_target=None,
            reason="semantic_candidate_evidence_not_available",
        )
    result["semantic_candidate_evidence"] = semantic_evidence
    result["semantic_candidate_evidence_valid"] = semantic_evidence_valid
    result["policy_ids"] = [config.trigger_policy, "P-NODE-02", "P-NODE-05"]
    result["query_ids"] = list(config.candidate_query_ids)
    result["input_evidence"] = ["analysis.json", "before/result.json"]
    _write_json(run_dir / "plan.json", result)
    _update_manifest(run_dir, result["status"])
    return result


def execute(config: AdaptationConfig, topology: Topology, run_dir: Path) -> dict:
    _require_run_context(config, run_dir, topology)
    if (run_dir / "execute/result.json").exists():
        raise FileExistsError("Execute evidence already exists for this run")
    plan_result = json.loads((run_dir / "plan.json").read_text())
    if plan_result.get("status") == "no_action":
        result = {
            "stage": "execute",
            "mode": "scripted_manual",
            "status": "skipped_no_action",
            "action": None,
            "target": None,
            "reason": plan_result.get("reason", "analysis_did_not_require_capacity"),
            "infrastructure_changed": False,
        }
    else:
        result = deploy_read_only_replica(config, topology, run_dir, plan_result)
    result["timestamp"] = _timestamp()
    result["input_evidence"] = "plan.json"
    result["policy_ids"] = plan_result.get("policy_ids", [])
    result["query_ids"] = plan_result.get("query_ids", [])
    _write_json(run_dir / "execute/result.json", result)
    _update_manifest(run_dir, "execution_skipped_no_action" if result["status"] == "skipped_no_action" else "executed")
    return result


def verify(config: AdaptationConfig, topology: Topology, run_dir: Path) -> dict:
    _require_run_context(config, run_dir, topology)
    if (run_dir / "after").exists() or (run_dir / "verification/result.json").exists():
        raise FileExistsError("Verification evidence already exists for this run")
    execution = json.loads((run_dir / "execute/result.json").read_text())
    if execution.get("status") == "skipped_no_action":
        result = {
            "stage": "verify",
            "mode": "measured",
            "status": "skipped_no_action",
            "reason": "no_infrastructure_change_to_verify",
            "infrastructure_changed": False,
            "before_evidence_preserved": (run_dir / "before/result.json").is_file(),
            "timestamp": _timestamp(),
            "input_evidence": ["execute/result.json", "before/result.json"],
        }
        _write_json(run_dir / "verification/result.json", result)
        _update_manifest(run_dir, "verified_no_action")
        return result
    if execution.get("status") != "replica_ready":
        raise ValueError("verification requires a semantically ready replica")
    replica_data = execution["replica"]
    replica = Host(
        replica_data["id"],
        replica_data["tier"],
        replica_data["authority"],
        replica_data["address"],
        int(replica_data["port"]),
        bool(replica_data.get("local", False)),
    )
    expected_fragments = json.loads((run_dir / "before/expected-semantics.json").read_text())
    source_expected = expected_fragments[execution["replica_source"]]
    wait_ready(
        replica.endpoint,
        deadline_seconds=60,
        require_idle=True,
        expected={
            "dataset_digest": source_expected["dataset_digest"],
            "closure_digest": source_expected["closure_digest"],
        },
    )
    fragments = {path.stem: path.read_bytes() for path in (run_dir / "before/fragments").glob("*.nt")}
    expected = _expected_worker_contract(config, topology)
    for host in topology.hosts:
        wait_ready(
            host.endpoint,
            deadline_seconds=60,
            require_idle=True,
            expected=expected
            | {
                "dataset_digest": expected_fragments[host.id]["dataset_digest"],
                "closure_digest": expected_fragments[host.id]["closure_digest"],
            },
        )
    _, queries = _queries(config)
    router = ReplicaRouter(topology.hosts, execution["replica_source"], replica)
    application_replay_plan = json.loads((run_dir / "before/application_execution_plan.json").read_text())
    after = run_dir / "after"
    after.mkdir()
    outcome = _run_monitoring_window(
        config,
        topology,
        after,
        queries,
        fragments,
        expected_fragments,
        expected,
        host_selector=router.select,
        replica=replica,
        replica_container_name=replica_data["container_name"],
        application_replay_plan=application_replay_plan,
    )
    before_workload = json.loads((run_dir / "before/workload.json").read_text())
    after_workload = json.loads((after / "workload.json").read_text())
    require_same_workload(before_workload, after_workload)
    after_application_plan = json.loads((after / "application_execution_plan.json").read_text())
    if application_replay_plan != after_application_plan:
        raise RuntimeError("before and after application query sequences are not identical")
    outcome["result"]["same_workload_verified"] = True
    outcome["result"]["same_application_sequence_verified"] = True
    outcome["result"]["routing"] = {
        "strategy": "deterministic_round_robin_source_replica",
        "partition_participant": execution["replica_source"],
        "read_only_replica": replica.id,
    }
    _write_json(after / "result.json", outcome["result"])
    _update_manifest(run_dir, "verified")
    return outcome["result"]


def _update_manifest(run_dir: Path, status: str) -> None:
    path = run_dir / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["status"] = status
    manifest["updated_at"] = _timestamp()
    _write_json(path, manifest)
