from __future__ import annotations

import json
import platform
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from time import monotonic

from .config import BenchmarkConfig, Scenario
from .deployment import container_states, restart_workers, semantic_environment
from .protocol import request_json, wait_ready
from .resources import ResourceSampler
from .topology import Host, Topology


def _run_id() -> str:
    return (
        datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
    )


def _tool(root: Path) -> Path:
    path = root / "rust/target/release/continuum-rdf-tool"
    cargo = Path.home() / ".cargo/bin/cargo"
    subprocess.run(
        [
            str(cargo),
            "build",
            "--release",
            "--quiet",
            "--manifest-path",
            str(root / "rust/Cargo.toml"),
            "-p",
            "continuum-rdf-tool",
        ],
        check=True,
    )
    return path


def generate_dataset(config: BenchmarkConfig, scenario: Scenario, directory: Path) -> tuple[Path, dict]:
    output = directory / "dataset.nt"
    result = subprocess.run(
        [
            str(_tool(config.root)),
            "generate",
            str(config.root / "ontology/benchmark/base.nt"),
            "--users",
            str(scenario.users),
            "--seed",
            str(config.experiment["seed"]),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    metadata = json.loads(result.stdout)
    (directory / "dataset.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return output, metadata


def partition_dataset(
    tool: Path, dataset: Path, base: Path, hosts: tuple[Host, ...], layout: str, output: Path
) -> tuple[dict[str, bytes], dict]:
    owners = hosts if layout == "replicated" else tuple(host for host in hosts if host.tier == "edge") or hosts
    result = subprocess.run(
        [
            str(tool),
            "partition",
            str(dataset),
            "--layout",
            layout,
            "--participants",
            ",".join(host.id for host in owners),
            "--output-dir",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    metadata = json.loads(result.stdout)
    fragments = {host.id: (output / f"{host.id}.nt").read_bytes() for host in owners}
    for host in hosts:
        if host.id not in fragments:
            fragments[host.id] = base.read_bytes()
            (output / f"{host.id}.nt").write_bytes(fragments[host.id])
            metadata["fragments"].append(
                {
                    "participant": host.id,
                    "role": "fixed-base-only",
                    "bytes": len(fragments[host.id]),
                    "digest": sha256(fragments[host.id]).hexdigest(),
                }
            )
    return fragments, metadata


def _prepare(host: Host, payload: bytes, timeout: float | None, expected_closure_digest: str) -> dict:
    digest = sha256(payload).hexdigest()
    started = monotonic()
    response = request_json(
        f"{host.endpoint}/prepare",
        method="POST",
        payload=payload,
        headers={"content-type": "application/n-triples", "x-expected-dataset-digest": digest},
        timeout=timeout,
    )
    response["transfer_and_remote_seconds"] = monotonic() - started
    response["transfer_seconds"] = max(
        0.0,
        response["transfer_and_remote_seconds"]
        - response["remote_load_seconds"]
        - response["reasoning"]["reasoning_seconds"],
    )
    response["host"] = host.id
    if response.get("dataset_digest") != digest or response.get("closure_digest") != expected_closure_digest:
        raise RuntimeError(
            f"semantic_mismatch: {host.id} returned dataset={response.get('dataset_digest')} "
            f"closure={response.get('closure_digest')}"
        )
    return response


def _expected_fragment_semantics(
    tool: Path, fragments: dict[str, bytes], fragment_dir: Path, output: Path
) -> dict[str, dict]:
    expected = {}
    for host_id, payload in fragments.items():
        fragment = fragment_dir / f"{host_id}.nt"
        result = subprocess.run([str(tool), "reason", str(fragment)], capture_output=True, text=True, check=True)
        reasoned = json.loads(result.stdout)
        expected[host_id] = {
            "dataset_digest": sha256(payload).hexdigest(),
            "closure_digest": reasoned["closure_digest"],
            "reasoning": reasoned["report"],
        }
    output.write_text(json.dumps(expected, indent=2) + "\n")
    return expected


def _failure_status(error: Exception) -> str:
    message = str(error).lower()
    if "payload_limit_exceeded" in message or "http 413" in message:
        return "payload_limit_exceeded"
    if "semantic_mismatch" in message or "http 422" in message:
        return "semantic_mismatch"
    if "did not become ready" in message and ("ready=false" in message or "assets=false" in message):
        return "incompatible_worker"
    if "timed out" in message or isinstance(error, TimeoutError):
        return "hard_timeout"
    return "failed"


def _catalog_round(
    hosts: tuple[Host, ...], queries: list[dict], round_: int, layout: str, timeout: float
) -> tuple[list[dict], list[dict]]:
    logical, physical = [], []
    for index, query in enumerate(queries):
        if layout == "replicated":
            selected = (hosts[(round_ + index) % len(hosts)],)
        else:
            scope = query["execution_scope"]
            if scope == "authorities":
                selected = tuple(host for host in hosts if host.tier == "edge") or hosts
            elif scope == "cloud_authorities":
                selected = tuple(host for host in hosts if host.tier in {"cloud", "edge"}) or hosts
            elif scope == "all":
                selected = hosts
            elif scope.startswith("authority_key:"):
                authorities = tuple(host for host in hosts if host.tier == "edge") or hosts
                selected = (authorities[int.from_bytes(sha256(scope.encode()).digest()[:8], "big") % len(authorities)],)
            else:
                candidates = tuple(host for host in hosts if host.tier == scope)
                selected = (
                    (candidates[(round_ + index) % len(candidates)],)
                    if candidates
                    else (hosts[(round_ + index) % len(hosts)],)
                )
        started_at = datetime.now(UTC).isoformat()
        started = monotonic()
        keys: set[str] = set()
        ask = False
        status = "completed"
        for host in selected:
            try:
                response = request_json(
                    f"{host.endpoint}/query",
                    method="POST",
                    timeout=timeout,
                    headers={"content-type": "application/json"},
                    payload=json.dumps({"query_id": query["id"], "query": query["query"], "round": round_}).encode(),
                )
                outcome = response["outcome"]
                keys.update(outcome["result_keys"])
                ask = ask or bool(outcome["ask_result"])
                physical.append(
                    {
                        "query_id": query["id"],
                        "round": round_,
                        "host": host.id,
                        "start_timestamp": started_at,
                        "duration_ms": outcome["duration_ms"],
                        "status": "completed",
                        "result_count": outcome["result_count"],
                        "result_digest": outcome["result_digest"],
                    }
                )
            except Exception as error:
                status = "query_timeout" if "timed out" in str(error).lower() else "failed"
                physical.append(
                    {"query_id": query["id"], "round": round_, "host": host.id, "status": status, "error": str(error)}
                )
        digest_payload = f"ASK:{str(ask).lower()}" if query["kind"] == "ask" else "\n".join(sorted(keys))
        logical.append(
            {
                "query_id": query["id"],
                "round": round_,
                "layout": layout,
                "participants": [h.id for h in selected],
                "start_timestamp": started_at,
                "duration_ms": (monotonic() - started) * 1000,
                "result_count": len(keys) if query["kind"] != "ask" else int(ask),
                "result_digest": sha256(digest_payload.encode()).hexdigest(),
                "status": status,
            }
        )
    return logical, physical


def run(
    config: BenchmarkConfig,
    topology: Topology,
    *,
    scenario_names: set[str] | None = None,
    diagnostic_unlimited: bool = False,
) -> Path:
    run_dir = config.root / "outputs" / _run_id()
    run_dir.mkdir(parents=True)
    query_manifest = json.loads((config.root / "queries/manifest.json").read_text())
    for query in query_manifest["queries"]:
        query["query"] = (config.root / query["path"]).read_text(encoding="utf-8")
    manifest = {
        "status": "running",
        "started_at": datetime.now(UTC).isoformat(),
        "non_comparable_diagnostic_run": diagnostic_unlimited,
        "query_count": query_manifest["query_count"],
        "query_catalog_digest": query_manifest["query_catalog_digest"],
        "topology_fingerprint": topology.fingerprint,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (run_dir / "configuration.toml").write_bytes(config.path.read_bytes())
    (run_dir / "topology.json").write_text(
        json.dumps({"name": topology.name, "hosts": [h.__dict__ for h in topology.hosts]}, indent=2) + "\n"
    )
    (run_dir / "campaign.json").write_text(
        json.dumps(
            {
                "scenarios": [s.__dict__ for s in config.scenarios],
                "layouts": config.experiment["layouts"],
                "warmup": config.experiment["warmup"],
                "repetitions": config.experiment["repetitions"],
                "query_rounds": config.experiment["query_rounds"],
            },
            indent=2,
        )
        + "\n"
    )
    semantic = semantic_environment(config, topology)
    expected = {
        "topology_fingerprint": semantic["CONTINUUM_TOPOLOGY_FINGERPRINT"],
        "ontology_digest": semantic["CONTINUUM_ONTOLOGY_DIGEST"],
        "query_catalog_digest": semantic["CONTINUUM_QUERY_CATALOG_DIGEST"],
        "query_count": int(semantic["CONTINUUM_QUERY_COUNT"]),
        "max_prepare_bytes": int(semantic["CONTINUUM_MAX_PREPARE_BYTES"]),
    }
    initial_health = []
    try:
        for host in topology.hosts:
            initial_health.append(
                wait_ready(
                    host.endpoint,
                    deadline_seconds=float(config.deployment["health_timeout_seconds"]),
                    require_idle=True,
                    expected=expected,
                )
            )
    except Exception as error:
        manifest["status"] = _failure_status(error)
        manifest["error"] = str(error)
        manifest["finished_at"] = datetime.now(UTC).isoformat()
        manifest["failures"] = 1
        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (run_dir / "failure.json").write_text(
            json.dumps(
                {"failure_scope": "initial_readiness", "status": manifest["status"], "error": str(error)}, indent=2
            )
            + "\n"
        )
        from .reporting import report

        report(run_dir)
        return run_dir
    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "rust": subprocess.run(
            [str(Path.home() / ".cargo/bin/rustc"), "--version"], capture_output=True, text=True, check=True
        ).stdout.strip(),
        "workers": initial_health,
    }
    (run_dir / "environment.json").write_text(json.dumps(environment, indent=2) + "\n")
    failures = []
    for scenario in config.scenarios:
        if scenario_names and scenario.name not in scenario_names:
            continue
        scenario_dir = run_dir / "scenarios" / scenario.name
        scenario_dir.mkdir(parents=True)
        try:
            dataset_path, metadata = generate_dataset(config, scenario, scenario_dir)
            rust_tool = _tool(config.root)
        except Exception as error:
            failure = {
                "scenario": scenario.name,
                "users": scenario.users,
                "status": _failure_status(error),
                "error": str(error),
                "failure_scope": "dataset_generation",
            }
            failures.append(failure)
            (scenario_dir / "failure.json").write_text(json.dumps(failure, indent=2) + "\n")
            continue
        for layout in config.experiment["layouts"]:
            layout_dir = scenario_dir / layout
            layout_dir.mkdir()
            try:
                reference_dir = layout_dir / "reference-fragments"
                reference_fragments, reference_partition = partition_dataset(
                    rust_tool,
                    dataset_path,
                    config.root / "ontology/benchmark/base.nt",
                    topology.hosts,
                    layout,
                    reference_dir,
                )
                expected_fragments = _expected_fragment_semantics(
                    rust_tool, reference_fragments, reference_dir, layout_dir / "expected-semantics.json"
                )
                (layout_dir / "reference-partition.json").write_text(json.dumps(reference_partition, indent=2) + "\n")
            except Exception as error:
                failure = {
                    "scenario": scenario.name,
                    "users": scenario.users,
                    "layout": layout,
                    "status": _failure_status(error),
                    "error": str(error),
                    "failure_scope": "reference_validation",
                }
                failures.append(failure)
                (layout_dir / "failure.json").write_text(json.dumps(failure, indent=2) + "\n")
                continue
            total = int(config.experiment["warmup"]) + int(config.experiment["repetitions"])
            for iteration in range(total):
                warmup = iteration < int(config.experiment["warmup"])
                rep = iteration + 1 if warmup else iteration - int(config.experiment["warmup"]) + 1
                rep_dir = layout_dir / (f"warmup-{rep:02}" if warmup else f"rep-{rep:02}")
                rep_dir.mkdir()
                record = {
                    "scenario": scenario.name,
                    "users": scenario.users,
                    "layout": layout,
                    "warmup": warmup,
                    "repetition": rep,
                    "status": "running",
                    "started_at": datetime.now(UTC).isoformat(),
                    "dataset": metadata,
                }
                try:
                    fragments, partition_metadata = partition_dataset(
                        rust_tool,
                        dataset_path,
                        config.root / "ontology/benchmark/base.nt",
                        topology.hosts,
                        layout,
                        rep_dir / "fragments",
                    )
                    (rep_dir / "partition.json").write_text(json.dumps(partition_metadata, indent=2) + "\n")
                    partition_seconds = partition_metadata["partition_seconds"]
                    serialize_seconds = partition_metadata["serialize_seconds"]
                    record["partition_seconds"] = partition_seconds
                    record["serialize_seconds"] = serialize_seconds
                    max_prepare_bytes = int(config.deployment["max_prepare_mib"]) * 1024 * 1024
                    largest_payload = max(len(payload) for payload in fragments.values())
                    record["largest_prepare_payload_bytes"] = largest_payload
                    record["max_prepare_bytes"] = max_prepare_bytes
                    if largest_payload > max_prepare_bytes:
                        raise RuntimeError(
                            f"payload_limit_exceeded: {largest_payload} bytes exceeds {max_prepare_bytes} bytes"
                        )
                    for host in topology.hosts:
                        if sha256(fragments[host.id]).hexdigest() != expected_fragments[host.id]["dataset_digest"]:
                            raise RuntimeError(f"semantic_mismatch: nondeterministic fragment for {host.id}")
                    with ResourceSampler(
                        topology.hosts,
                        str(config.deployment["ssh_user"]),
                        str(config.deployment["image"]),
                        rep_dir / "resources.jsonl",
                        float(config.experiment["resource_sample_interval_seconds"]),
                    ):
                        for host in topology.hosts:
                            request_json(f"{host.endpoint}/reset", method="POST", timeout=30)
                        record["worker_health_before"] = [
                            wait_ready(host.endpoint, deadline_seconds=60, require_idle=True, expected=expected)
                            for host in topology.hosts
                        ]
                        timeout = (
                            None if diagnostic_unlimited else float(config.experiment["prepare_hard_timeout_seconds"])
                        )
                        with ThreadPoolExecutor(max_workers=len(topology.hosts)) as pool:
                            prepared = [
                                future.result()
                                for future in as_completed(
                                    [
                                        pool.submit(
                                            _prepare,
                                            h,
                                            fragments[h.id],
                                            timeout,
                                            expected_fragments[h.id]["closure_digest"],
                                        )
                                        for h in topology.hosts
                                    ]
                                )
                            ]
                        record["preparation"] = prepared
                        record["preparation_seconds"] = (
                            partition_seconds
                            + serialize_seconds
                            + max(p["transfer_seconds"] + p["remote_load_seconds"] for p in prepared)
                        )
                        target = float(config.experiment["prepare_operational_target_seconds"])
                        record["status"] = (
                            "completed_within_target"
                            if record["preparation_seconds"] <= target
                            else "completed_over_target"
                        )
                        record["preparation_status"] = record["status"]
                        for host in topology.hosts:
                            prepared_health = {
                                "dataset_digest": expected_fragments[host.id]["dataset_digest"],
                                "closure_digest": expected_fragments[host.id]["closure_digest"],
                            }
                            wait_ready(
                                host.endpoint,
                                deadline_seconds=60,
                                require_idle=True,
                                expected=expected | prepared_health,
                            )
                        logical = []
                        physical = []
                        catalog_rounds = []
                        for round_ in range(1, int(config.experiment["query_rounds"]) + 1):
                            round_started = monotonic()
                            l, p = _catalog_round(
                                topology.hosts,
                                query_manifest["queries"],
                                round_,
                                layout,
                                float(config.experiment["request_timeout_seconds"]),
                            )
                            for row in (*l, *p):
                                row.update(users=scenario.users, repetition=rep)
                            logical += l
                            physical += p
                            catalog_rounds.append(
                                {
                                    "round": round_,
                                    "duration_seconds": monotonic() - round_started,
                                    "logical_queries": len(l),
                                    "physical_executions": len(p),
                                }
                            )
                        (rep_dir / "logical_queries.json").write_text(json.dumps(logical, indent=2) + "\n")
                        (rep_dir / "physical_queries.json").write_text(json.dumps(physical, indent=2) + "\n")
                        (rep_dir / "catalog_rounds.json").write_text(json.dumps(catalog_rounds, indent=2) + "\n")
                        record["query_failures"] = sum(row["status"] != "completed" for row in logical)
                        if record["query_failures"]:
                            record["status"] = (
                                "query_timeout"
                                if any(row["status"] == "query_timeout" for row in logical)
                                else "failed"
                            )
                        record["worker_health_after"] = [
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
                            for host in topology.hosts
                        ]
                except Exception as error:
                    record["status"] = _failure_status(error)
                    record["error"] = str(error)
                record["container_states"] = container_states(config, topology)
                oom_hosts = {
                    item["host"] for item in record["container_states"] if item.get("state", {}).get("OOMKilled")
                }
                if oom_hosts:
                    record["status"] = "oom_killed"
                    record["post_oom_recovery"] = restart_workers(config, topology, oom_hosts)
                if record["status"] in {
                    "failed",
                    "hard_timeout",
                    "query_timeout",
                    "oom_killed",
                    "incompatible_worker",
                    "semantic_mismatch",
                }:
                    failures.append(record.copy())
                record["finished_at"] = datetime.now(UTC).isoformat()
                (rep_dir / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    manifest["status"] = "completed_with_failures" if failures else "completed"
    manifest["finished_at"] = datetime.now(UTC).isoformat()
    manifest["failures"] = len(failures)
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    from .reporting import report

    report(run_dir)
    return run_dir
