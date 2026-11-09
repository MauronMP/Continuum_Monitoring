import os
import socket
import subprocess
from pathlib import Path

from continuum_bench.adaptation.logic import ReplicaRouter, analyze_trigger, plan_adaptation
from continuum_bench.protocol import request_json, wait_ready
from continuum_bench.query_execution import execute_logical_query
from continuum_bench.topology import Host


def _port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _start(binary: Path, port: int, node_id: str):
    env = os.environ | {"CONTINUUM_BIND": f"127.0.0.1:{port}", "CONTINUUM_NODE_ID": node_id}
    return subprocess.Popen([str(binary)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def test_local_worker_replica_adaptation_flow(root):
    binary = root / "rust/target/debug/continuum-worker"
    cargo = Path.home() / ".cargo/bin/cargo"
    subprocess.run(
        [str(cargo), "build", "--manifest-path", str(root / "rust/Cargo.toml"), "-p", "continuum-worker"],
        check=True,
    )
    baseline_port, replica_port = _port(), _port()
    baseline_process = _start(binary, baseline_port, "edge1")
    replica_process = _start(binary, replica_port, "edge1-replica-on-edge2")
    try:
        baseline = Host("edge1", "edge", "partition-a", "127.0.0.1", baseline_port, True)
        replica = Host("edge1-replica-on-edge2", "edge", "partition-a", "127.0.0.1", replica_port, True)
        wait_ready(baseline.endpoint, deadline_seconds=10, require_idle=True)
        wait_ready(replica.endpoint, deadline_seconds=10, require_idle=True)
        payload = b"<urn:subject> <urn:property> <urn:value> .\n"
        prepared = []
        for host in (baseline, replica):
            prepared.append(
                request_json(
                    f"{host.endpoint}/prepare",
                    method="POST",
                    payload=payload,
                    headers={"content-type": "application/n-triples"},
                    timeout=10,
                )
            )
        assert prepared[0]["dataset_digest"] == prepared[1]["dataset_digest"]
        assert prepared[0]["closure_digest"] == prepared[1]["closure_digest"]

        trigger = {"triggered": True, "trigger_policy": "P-ADAPT-03", "observations": [], "experimental_thresholds": {}}
        analysis = analyze_trigger(trigger, "2026-01-01T00:00:00+00:00")
        candidate = {
            "id": "edge2",
            "tier": "edge",
            "connected": True,
            "worker_ready": True,
            "worker_idle": True,
            "available_memory_mib": 8000,
            "cpu_count": 4,
            "load_1m": 1.0,
            "replica_port_available": True,
        }
        config = type(
            "Config",
            (),
            {
                "allowed_target_tiers": ("edge",),
                "excluded_targets": (),
                "minimum_available_memory_mib": 3072,
                "maximum_host_load_per_cpu": 0.9,
                "require_distinct_from_source": True,
                "replica_source": "edge1",
                "preferred_target": "edge2",
                "fallback_to_ranked_candidate": True,
                "preferred_action": "deploy_read_only_replica",
            },
        )()
        plan = plan_adaptation(config, analysis, [candidate], "2026-01-01T00:00:00+00:00")
        assert plan["status"] == "planned"

        router = ReplicaRouter((baseline,), "edge1", replica)
        query = {
            "id": "VERIFY",
            "order": 1,
            "query": "SELECT ?s WHERE { ?s <urn:property> <urn:value> }",
            "execution_scope": "all",
            "merge_strategy": "set_union",
            "kind": "report",
        }
        outcomes = []
        for round_ in (1, 2):
            selected = router.select(query, round_, 0, "distributed")
            logical, physical = execute_logical_query(
                (baseline,),
                query,
                round_,
                0,
                "distributed",
                physical_timeout=10,
                logical_timeout=10,
                selected_hosts=selected,
            )
            outcomes.append((logical, physical))
        assert outcomes[0][0]["result_digest"] == outcomes[1][0]["result_digest"]
        assert outcomes[0][0]["selected_hosts"] == ["edge1"]
        assert outcomes[1][0]["selected_hosts"] == ["edge1-replica-on-edge2"]
        assert all(item[0]["status"] == "completed" for item in outcomes)
    finally:
        for process in (baseline_process, replica_process):
            process.terminate()
            process.wait(timeout=5)
