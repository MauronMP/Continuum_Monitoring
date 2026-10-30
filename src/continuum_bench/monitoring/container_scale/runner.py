"""Run sequential container placements through the existing semantic experiment engine."""

from dataclasses import asdict
from datetime import datetime, timezone
import csv
import json
import uuid

from ..distributed_reasoning_config import DistributedReasoningConfig
from ..distributed_reasoning_scalability import run_distributed_reasoning_scalability
from . import deployment


def workload(config, scenario, participants, warmup=False):
    e = config.experiment
    multiplier = participants if scenario["family"] == "weak" else 1
    return DistributedReasoningConfig(
        path=config.path,
        repetitions=e["warmup"] if warmup else e["repetitions"],
        request_timeout_seconds=e["request_timeout_seconds"],
        point_timeout_seconds=e["point_timeout_seconds"],
        seed=e["seed"],
        users=scenario["users"] * multiplier,
        rule_count=0,
        padding_mode="neutral",
        target_triples=(scenario["target_triples"] * multiplier,),
        node_counts=(participants,),
        reasoners=tuple(e["reasoners"]),
        tasks=("rdfs_closure", "owl_dl_classification_realization"),
        layouts=tuple(e["layouts"]),
        strong_scaling=True,
        weak_scaling=False,
        weak_triples_per_node=1,
        stop_after_timeout=False,
        bootstrap_samples=1000,
        confidence_level=0.95,
        query_concurrency=tuple(scenario["concurrency"]),
        query_rounds=scenario["query_rounds"],
        semantic_validation=False if warmup else e["semantic_validation"],
    )


def read_rows(path):
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def run(
    config,
    benchmark,
    output_root,
    *,
    dry_run=False,
    scenario_names=None,
    keep_going=True,
):
    output = output_root / (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:8]
    )
    output.mkdir(parents=True)
    scenarios = [
        s
        for s in config.raw["scenarios"]
        if not scenario_names or s["name"] in scenario_names
    ]
    if not scenarios or (
        scenario_names and set(scenario_names) - {s["name"] for s in scenarios}
    ):
        raise ValueError("Unknown scenario selection")
    (output / "configuration.json").write_text(json.dumps(config.raw, indent=2) + "\n")
    (output / "source-config.toml").write_bytes(config.path.read_bytes())
    (output / "benchmark-config.json").write_text(
        json.dumps(asdict(benchmark), indent=2, default=str) + "\n"
    )
    summary = {
        "status": "planned" if dry_run else "running",
        "steps": [],
        "scope": "Coordinated container participants on physical hosts; not decentralized",
        "warmup_excluded": True,
        "physical_host_count": len(config.topology.active_nodes),
    }

    def checkpoint():
        (output / "campaign.json").write_text(json.dumps(summary, indent=2) + "\n")

    checkpoint()
    total = len(config.deployment["containers_per_host"]) * len(scenarios)
    try:
        for count in config.deployment["containers_per_host"]:
            placement = output / f"placement-{count}"
            topology = deployment.render(config, benchmark.root, placement, count)
            if not dry_run:
                # Remove only this module's previous placement before checking free RAM.
                # First deployment may have no existing project, so inspect directories first.
                for node in config.topology.active_nodes:
                    dest = deployment.host_directory(config, benchmark.root, node)
                    exists = deployment.execute(
                        config,
                        node,
                        [
                            "python3",
                            "-c",
                            "import sys; from pathlib import Path; print(Path(sys.argv[1]).exists())",
                            dest + "/compose.json",
                        ],
                    ).strip()
                    if exists == "True":
                        deployment.compose(
                            config, benchmark.root, node, "down", "--timeout", "15"
                        )
                topology = deployment.deploy(
                    config, benchmark.root, placement, count, build=True
                )
            for scenario in scenarios:
                step = {
                    "scenario": scenario["name"],
                    "family": scenario["family"],
                    "containers_per_host": count,
                    "logical_participants": len(topology.active_nodes),
                    "status": "planned" if dry_run else "running",
                }
                summary["steps"].append(step)
                checkpoint()
                print(
                    f"[container-scale] step={len(summary['steps'])}/{total} percent={100 * (len(summary['steps']) - 1) / total:.1f} scenario={scenario['name']} participants={len(topology.active_nodes)} status={step['status']}",
                    flush=True,
                )
                if dry_run:
                    continue
                if len(summary["steps"]) > 1 and summary["steps"][-2]["status"] in (
                    "partial",
                    "failed",
                ):
                    for node in config.topology.active_nodes:
                        deployment.compose(
                            config, benchmark.root, node, "up", "-d", "--no-build"
                        )
                    deployment.wait_ready(config, topology)
                    step["recovery_action"] = (
                        "restart stopped module containers before next scenario"
                    )
                destination = placement / scenario["name"]
                destination.mkdir(parents=True, exist_ok=True)
                (destination / "before.json").write_text(
                    json.dumps(deployment.collect(config, benchmark.root), indent=2)
                    + "\n"
                )
                try:
                    if config.experiment["warmup"]:
                        warm = run_distributed_reasoning_scalability(
                            benchmark,
                            workload(
                                config, scenario, len(topology.active_nodes), True
                            ),
                            "physical",
                            destination / "warmup",
                            topology.endpoints(),
                            topology,
                        )
                        step["warmup_statuses"] = [
                            r["status"]
                            for r in read_rows(
                                warm / "distributed-reasoning-summary.csv"
                            )
                        ]
                    # A timed-out warm-up client may leave requests queued at a
                    # sequential worker. Wait for readiness before rediscovery.
                    deployment.wait_ready(config, topology)
                    results = run_distributed_reasoning_scalability(
                        benchmark,
                        workload(config, scenario, len(topology.active_nodes)),
                        "physical",
                        destination / "measured",
                        topology.endpoints(),
                        topology,
                        query_each_repetition=True,
                    )
                    rows = read_rows(results / "distributed-reasoning-summary.csv")
                    queries = read_rows(results / "query-scalability.csv")
                    from ...csv_utils import write_dict_rows

                    for q in queries:
                        q["successful_client_requests"] = int(
                            q["client_requests"]
                        ) - int(q["error_count"])
                        q["client_requests_per_second"] = (
                            1000
                            * q["successful_client_requests"]
                            / float(q["query_wall_ms"])
                        )
                        q["request_unit"] = (
                            "one complete catalog evaluation; worker fan-out is not extra throughput"
                        )
                    if queries:
                        write_dict_rows(
                            results / "client-throughput.csv",
                            queries,
                            empty_message="No query requests",
                        )
                    step["statuses"] = {
                        status: sum(r["status"] == status for r in rows)
                        for status in {r["status"] for r in rows}
                    }
                    bad_queries = any(
                        r.get("status") not in (None, "", "completed") for r in queries
                    )
                    bad_semantics = config.experiment["semantic_validation"] and any(
                        r.get("semantic_equivalence_status")
                        not in ("query_projection_equivalent", "not_sampled")
                        for r in rows
                    )
                    step["status"] = (
                        "completed"
                        if rows
                        and all(r["status"] == "completed" for r in rows)
                        and not bad_queries
                        and not bad_semantics
                        else "partial"
                    )
                    step["results"] = str(results.relative_to(output))
                except Exception as error:
                    import traceback
                    step.update(status="failed", error=str(error), error_type=type(error).__name__)
                    (destination / "failure.log").write_text(traceback.format_exc())
                    if not keep_going:
                        raise
                finally:
                    (destination / "after.json").write_text(
                        json.dumps(deployment.collect(config, benchmark.root), indent=2)
                        + "\n"
                    )
                    checkpoint()
                    print(
                        f"[container-scale] step={len(summary['steps'])}/{total} percent={100 * len(summary['steps']) / total:.1f} scenario={scenario['name']} status={step['status']}",
                        flush=True,
                    )
                if not keep_going and step["status"] != "completed":
                    break
            if not keep_going and any(
                s["status"] not in ("completed", "planned") for s in summary["steps"]
            ):
                break
        summary["status"] = (
            "planned"
            if dry_run
            else (
                "completed"
                if all(s["status"] == "completed" for s in summary["steps"])
                else "partial"
            )
        )
    except BaseException as error:
        summary.update(
            status="interrupted" if isinstance(error, KeyboardInterrupt) else "failed",
            error=str(error),
        )
        raise
    finally:
        checkpoint()
        print(
            f"[container-scale] status={summary['status']} evidence={output}",
            flush=True,
        )
    if not dry_run:
        from .reporting import report

        report(output)
    return output
