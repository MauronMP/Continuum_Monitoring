import json
import os
import socket
import subprocess
from pathlib import Path

from continuum_bench.protocol import request_json, wait_ready


def _port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_python_to_rust_worker(root):
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
        request_json(f"http://127.0.0.1:{port}/reset", method="POST", timeout=10)
        assert request_json(f"http://127.0.0.1:{port}/health")["graph_loaded"] is False
    finally:
        process.terminate()
        process.wait(timeout=5)
