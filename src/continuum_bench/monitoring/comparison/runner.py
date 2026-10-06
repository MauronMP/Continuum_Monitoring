"""Paired physical execution, durable raw evidence and explicit outcome coverage."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import subprocess
from time import perf_counter
import uuid

from ...physical_cluster import load_physical_inventory
from ..lease import physical_lease, prevent_coordinator_suspension
from ..policy_evaluation.config import load_policy_evaluation_config
from .transport import invoke, probe, source_bundle
from .workload import digest, expand, trace


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def inventory_for(config, nodes=None):
    inventory = load_physical_inventory(Path(config["topology"]))
    known = {node.role for node in inventory.nodes}
    all_known = {node.node_id for node in inventory.topology.nodes}
    unknown_exclusions = set(config["exclude_nodes"]) - all_known
    if unknown_exclusions:
        raise ValueError(f"Unknown excluded nodes: {sorted(unknown_exclusions)}")
    if nodes and set(nodes) - known:
        raise ValueError(f"Unknown physical nodes: {sorted(set(nodes) - known)}")
    selected = [node for node in inventory.nodes if node.role not in config["exclude_nodes"] and (not nodes or node.role in nodes)]
    if not selected:
        raise ValueError("No physical nodes selected")
    return inventory, selected


def jobs(config):
    for experiment in config["experiments"]:
        sizes = config["multipliers"] if experiment == "scalability" else config["cumulative_cycles"] if experiment == "cumulative" else [1]
        for size in sizes:
            for repetition in range(1, config["repetitions"] + 1):
                strategies = list(config["strategies"])
                random.Random(f"{config['seed']}:{experiment}:{size}:{repetition}").shuffle(strategies)
                for strategy in strategies:
                    yield experiment, size, repetition, strategy


def run(config, root: Path, nodes=None):
    inventory, selected = inventory_for(config, nodes)
    policy = load_policy_evaluation_config(config["policy_config"])
    unknown = set(config["exclude_resources"]) - {r.identifier for r in policy.resources}
    if unknown:
        raise ValueError(f"Unknown excluded logical resources: {sorted(unknown)}")
    bundle = source_bundle()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    directory = root / config["output"] / run_id
    directory.mkdir(parents=True, exist_ok=False)
    source_hash = hashlib.sha256(bundle).hexdigest()
    (directory / "source.zip").write_bytes(bundle)
    # Resolve snapshots before any work starts, including the configured oracle.
    dump(directory / "configuration.json", config)
    dump(directory / "policy-configuration.json", policy.public())
    (directory / "policy-configuration.toml").write_bytes(Path(config["policy_config"]).read_bytes())
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True)
    metadata = {
        "schema_version": 1, "run_id": run_id, "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": source_hash, "git_commit": git.stdout.strip() if git.returncode == 0 else None,
        "config_sha256": digest(config), "policy_sha256": policy.fingerprint,
        "selected_nodes": [asdict(node) for node in selected],
        "topology": inventory.topology.public() if hasattr(inventory.topology, "public") else [asdict(n) for n in inventory.nodes],
        "excluded_nodes": config["exclude_nodes"], "excluded_resources": config["exclude_resources"],
        "oracle": "Configured acceptance plans; not independently expert-validated",
        "scope": "Physical per-host policy-decision microbenchmark; synthetic context replay",
        "baseline_provenance": "Controlled implementations, not published-system reproductions",
        "reasoner": "rdfs for semantic; not applicable for static/procedural",
        "status": "running",
    }
    dump(directory / "metadata.json", metadata)
    records = []
    schedule = list(jobs(config))
    total = len(schedule) * len(selected)
    try:
        with physical_lease(root), prevent_coordinator_suspension(True):
            checks = [probe(node, inventory, config) for node in selected]
            dump(directory / "preflight.json", checks)
            available = {item["node"] for item in checks if item["available"]}
            for node in selected:
                for experiment, size, repetition, strategy in schedule:
                    job_id = f"{experiment}-{node.role}-{size}-{repetition}-{strategy}"
                    multiplier = size if experiment == "scalability" else 1
                    cycles = size if experiment == "cumulative" else config["events_per_context"]
                    workload = expand(policy, set(config["exclude_resources"]), multiplier)
                    events = trace(workload, cycles, config["seed"] + repetition, experiment in ("adaptation", "cumulative"))
                    # Exact trace is identical across strategies and nodes in a paired block.
                    payload = {"strategy": strategy, "workload": workload, "events": events, "warmup": config["warmup"]}
                    print(f"[comparison {len(records)}/{total} {100*len(records)/total:.1f}%] {job_id}", flush=True)
                    started = perf_counter()
                    response = invoke(node, inventory, config, bundle, payload) if node.role in available else {
                        "status": "unavailable", "error": "Node failed preflight; see preflight.json"}
                    record = {
                        "job_id": job_id, "node": node.role, "tier": node.tier, "experiment": experiment,
                        "size": size, "repetition": repetition, "strategy": strategy,
                        "resource_count": len(workload["resources"]), "policy_count": len(workload["rules"]),
                        "event_count": len(events), "trace_sha256": digest(events), "workload_sha256": digest(workload),
                        "timeout_seconds": config["timeout_seconds"], "transport_wall_ms": (perf_counter()-started)*1000,
                        "source_sha256": source_hash, **response,
                    }
                    dump(directory / experiment / "raw" / f"{job_id}.json", {"request": payload, "result": record})
                    records.append(record)
                    with (directory / "jobs.jsonl").open("a") as handle:
                        handle.write(json.dumps(record, allow_nan=False) + "\n")
                    print(f"[comparison {len(records)}/{total} {100*len(records)/total:.1f}%] {response['status']}", flush=True)
    except BaseException:
        metadata["status"] = "interrupted"
        dump(directory / "metadata.json", metadata)
        raise
    failures = sum(r["status"] != "completed" for r in records)
    mismatches = sum(not e["plan_correct"] for r in records if r["status"] == "completed" and r["strategy"] != "static" for e in r["events"])
    metadata.update(status="completed_with_errors" if failures or mismatches else "completed", jobs=len(records),
                    failed_jobs=failures, adaptive_plan_mismatches=mismatches)
    dump(directory / "metadata.json", metadata)
    from .reporting import report
    report(directory)
    return directory, bool(failures or mismatches)
