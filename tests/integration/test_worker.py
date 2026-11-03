import json
import os
import socket
import subprocess
from pathlib import Path

import pytest

from continuum_bench.continuous_monitoring.config import MonitoringTask, load_monitoring_config
from continuum_bench.continuous_monitoring.experiment import _task_executor
from continuum_bench.continuous_monitoring.reporting import report as monitoring_report
from continuum_bench.continuous_monitoring.scheduler import run_scheduler
from continuum_bench.protocol import request_json, wait_ready
from continuum_bench.topology import Host, Topology


def _port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_python_to_rust_worker(root, tmp_path):
    binary = root / "rust/target/debug/continuum-worker"
    cargo = Path.home() / ".cargo/bin/cargo"
    subprocess.run(
        [str(cargo), "build", "--manifest-path", str(root / "rust/Cargo.toml"), "-p", "continuum-worker"], check=True
    )
    port = _port()
    env = os.environ | {"CONTINUUM_BIND": f"127.0.0.1:{port}", "CONTINUUM_NODE_ID": "pytest"}
    process = subprocess.Popen([str(binary)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        health = wait_ready(f"http://127.0.0.1:{port}", deadline_seconds=10, require_idle=True)
        assert health["node_id"] == "pytest"
        assert health["protocol_version"] == "continuum-rdf-worker-v1"
        assert health["rust_version"].startswith("rustc ")
        assert health["build_target"]
        assert health["idle"] is True
        assert health["active_requests"] == 0
        assert health["queue_depth"] == 0
        payload = b"<urn:s> <urn:p> <urn:o> .\n"
        prepared = request_json(f"http://127.0.0.1:{port}/prepare", method="POST", payload=payload, timeout=10)
        assert prepared["status"] == "prepared"
        assert prepared["parse_and_digest_seconds"] >= 0
        assert prepared["reasoning"]["reasoning_seconds"] >= 0
        assert prepared["store_load_seconds"] >= 0
        assert prepared["remote_load_seconds"] == (
            prepared["parse_and_digest_seconds"] + prepared["store_load_seconds"]
        )
        loaded = request_json(f"http://127.0.0.1:{port}/health")
        assert loaded["dataset_digest"] == prepared["dataset_digest"]
        assert loaded["closure_digest"] == prepared["closure_digest"]
        assert loaded["graph_loaded"] is True
        query = request_json(
            f"http://127.0.0.1:{port}/query",
            method="POST",
            timeout=10,
            headers={"content-type": "application/json"},
            payload=json.dumps(
                {"query_id": "Q", "round": 1, "query": "SELECT ?s WHERE { ?s <urn:p> <urn:o> }"}
            ).encode(),
        )
        assert query["outcome"]["result_count"] == 1
        with pytest.warns(UserWarning):
            monitoring_config = load_monitoring_config(root / "configs/monitoring.toml")
        topology = Topology("integration", (Host("local", "edge", "local", "127.0.0.1", port, True),))
        query_contract = {
            "SMOKE": {
                "id": "SMOKE",
                "order": 1,
                "query": "SELECT ?s WHERE { ?s <urn:p> <urn:o> }",
                "execution_scope": "all",
                "merge_strategy": "set_union",
                "kind": "inventory",
                "expectation": "non_empty",
            }
        }
        execute, logical_rows, physical_rows = _task_executor(monitoring_config, topology, query_contract, "replicated")
        task = MonitoringTask("smoke-task", "P-TEST", ("SMOKE",), 1, "test", 0.05, 0.05)
        scheduler = run_scheduler((task,), 0.13, 1, execute)
        assert scheduler["scheduled_cycles"] == 2
        assert scheduler["completed_on_time"] == 2
        assert scheduler["monitoring_compliant_cycles"] == 2
        assert len(logical_rows) == len(physical_rows) == 2

        repetition = tmp_path / "monitoring-smoke/users-1/replicated/test/rep-01"
        repetition.mkdir(parents=True)
        events = scheduler.pop("events")
        result = {
            "scenario": "users-1",
            "users": 1,
            "layout": "replicated",
            "mode": "active",
            "demand_level": "test",
            "repetition": 1,
            "measurement_seconds": 0.13,
            "logical_queries": len(logical_rows),
            "physical_requests": len(physical_rows),
            "status": "completed",
            **scheduler,
        }
        (repetition / "result.json").write_text(json.dumps(result))
        (repetition / "scheduler_events.jsonl").write_text("".join(json.dumps(row) + "\n" for row in events))
        (repetition / "task_executions.jsonl").write_text("".join(json.dumps(row) + "\n" for row in events))
        (repetition / "logical_queries.jsonl").write_text("".join(json.dumps(row) + "\n" for row in logical_rows))
        (repetition / "physical_queries.jsonl").write_text("".join(json.dumps(row) + "\n" for row in physical_rows))
        (repetition / "phase_events.jsonl").write_text(
            json.dumps({"event": "phase_start", "phase": "monitoring_active"}) + "\n"
        )
        (repetition / "resource_samples.jsonl").write_text(
            "\n".join(
                json.dumps(row)
                for row in (
                    {
                        "host": "local",
                        "cpu_percent": 1.0,
                        "cpu_usage_seconds": 1.0,
                        "memory_bytes": 100,
                        "network_rx_bytes": 10,
                        "network_tx_bytes": 20,
                        "pids": 1,
                    },
                    {
                        "host": "local",
                        "cpu_percent": 2.0,
                        "cpu_usage_seconds": 1.1,
                        "memory_bytes": 110,
                        "network_rx_bytes": 20,
                        "network_tx_bytes": 40,
                        "pids": 1,
                    },
                )
            )
            + "\n"
        )
        summary = monitoring_report(tmp_path / "monitoring-smoke")
        assert (summary / "summary.csv").is_file()
        assert events[0]["execution_status"] == "completed"
        assert events[0]["schedule_status"] == "completed_on_time"
        assert events[0]["observation_outcome"] == "condition_detected"
        assert events[0]["monitoring_compliant"] is True
        assert (repetition / "task_executions.jsonl").is_file()
        assert (repetition / "physical_queries.jsonl").is_file()
        assert (repetition / "phase_events.jsonl").is_file()
        assert len(list((tmp_path / "monitoring-smoke/figures").glob("*.png"))) == 7
        request_json(f"http://127.0.0.1:{port}/reset", method="POST", timeout=10)
        assert request_json(f"http://127.0.0.1:{port}/health")["graph_loaded"] is False
    finally:
        process.terminate()
        process.wait(timeout=5)
