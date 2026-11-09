import csv
import json
import subprocess

from continuum_bench import deployment
from continuum_bench.config import load_config
from continuum_bench.deployment import render, restart_workers
from continuum_bench.experiment import _failure_status, _snapshot_semantic_contract
from continuum_bench.reporting import _failure_cause, report
from continuum_bench.resources import _bytes, _io_pair
from continuum_bench.topology import load_topology


def test_failure_categories_are_explicit():
    assert _failure_status(RuntimeError("semantic_mismatch: digest")) == "semantic_mismatch"
    assert _failure_status(RuntimeError("payload_limit_exceeded: 3 > 2")) == "payload_limit_exceeded"
    assert _failure_status(TimeoutError("operation timed out")) == "hard_timeout"
    assert _failure_status(RuntimeError("did not become ready: ready=False assets=False")) == "incompatible_worker"
    assert _failure_status(RuntimeError("connection reset")) == "failed"
    assert _failure_cause("Remote end closed connection", "oom_killed") == "out_of_memory"
    assert _failure_cause("request failed", "query_timeout") == "timeout"


def test_resource_units_are_parsed():
    assert _bytes("1.5 MiB") == 1_572_864
    assert _io_pair("2kB / 3kB") == (2000, 3000)


def test_render_emits_one_compatible_environment_per_host(root, tmp_path):
    config = load_config(root / "configs/benchmark.toml")
    topology = load_topology(root / "configs/topology.toml")
    output = render(config, topology, tmp_path / "deployment")
    manifest = json.loads((output / "deployment.json").read_text())
    assert len(manifest["hosts"]) == 6
    for host in topology.hosts:
        text = (output / f"{host.id}.env").read_text()
        assert "CONTINUUM_QUERY_COUNT=113" in text
        assert "CONTINUUM_MAX_PREPARE_BYTES=268435456" in text
        assert f"CONTINUUM_NODE_ID={host.id}" in text


def test_oom_recovery_skips_hosts_that_do_not_require_restart(root):
    config = load_config(root / "configs/benchmark.toml")
    topology = load_topology(root / "configs/topology.toml")
    assert restart_workers(config, topology, set()) == [{"host": host.id, "required": False} for host in topology.hosts]


def test_worker_baseline_restarts_selected_container(root, monkeypatch):
    config = load_config(root / "configs/benchmark.toml")
    topology = load_topology(root / "configs/topology.toml")
    commands = []

    def fake_remote(_host, _user, command, _timeout):
        commands.append(command)
        return subprocess.CompletedProcess([], 0, b"", b"")

    monkeypatch.setattr(deployment, "_remote", fake_remote)
    monkeypatch.setattr(deployment, "wait_ready", lambda *_args, **_kwargs: {"status": "ready"})
    evidence = restart_workers(config, topology, {"cloud"})

    assert len(commands) == 1
    assert "docker restart" in commands[0]
    assert evidence[0]["restarted"] is True
    assert all(item["required"] is False for item in evidence[1:])


def test_report_excludes_warmup_and_emits_auditable_outputs(tmp_path):
    run_dir = tmp_path / "run"
    measured = run_dir / "scenarios/users-1/distributed/rep-01"
    warmup = run_dir / "scenarios/users-1/distributed/warmup-01"
    measured.mkdir(parents=True)
    warmup.mkdir(parents=True)
    result = {
        "scenario": "users-1",
        "users": 1,
        "layout": "distributed",
        "warmup": False,
        "repetition": 1,
        "status": "completed_within_target",
        "partition_seconds": 0.1,
        "serialize_seconds": 0.2,
        "preparation_seconds": 0.7,
        "ready_seconds": 1.1,
        "dataset": {
            "actual_input_triples": 100,
            "dataset_bytes": 1000,
            "dataset_digest": "dataset",
            "dataset_generation_seconds": 0.01,
        },
        "preparation": [
            {
                "host": "edge1",
                "transfer_seconds": 0.1,
                "remote_load_seconds": 0.3,
                "transfer_and_remote_seconds": 0.5,
                "payload_bytes": 1000,
                "dataset_digest": "fragment",
                "closure_digest": "closure",
                "reasoning": {
                    "reasoning_seconds": 0.1,
                    "triples_before_reasoning": 100,
                    "triples_after_reasoning": 120,
                },
                "parse_and_digest_seconds": 0.02,
                "store_load_seconds": 0.03,
            }
        ],
    }
    (measured / "result.json").write_text(json.dumps(result))
    (warmup / "result.json").write_text(json.dumps(result | {"warmup": True, "preparation_seconds": 999}))
    (measured / "logical_queries.json").write_text(
        json.dumps(
            [
                {
                    "query_id": "Q1",
                    "round": 1,
                    "layout": "distributed",
                    "users": 1,
                    "repetition": 1,
                    "duration_ms": 5.0,
                    "status": "completed",
                }
            ]
        )
    )
    (measured / "physical_queries.json").write_text(
        json.dumps(
            [
                {
                    "query_id": "Q1",
                    "round": 1,
                    "host": "edge1",
                    "layout": "distributed",
                    "users": 1,
                    "repetition": 1,
                    "duration_ms": 4.0,
                    "status": "completed",
                }
            ]
        )
    )
    (measured / "catalog_rounds.json").write_text(
        json.dumps([{"round": 1, "duration_seconds": 2.0, "logical_queries": 10, "physical_executions": 20}])
    )
    samples = [
        {
            "host": "edge1",
            "phase": "preparation",
            "cpu_percent": 10.0,
            "cpu_usage_seconds": 2.0,
            "memory_bytes": 100,
            "network_rx_bytes": 1000,
            "network_tx_bytes": 2000,
        },
        {
            "host": "edge1",
            "phase": "preparation",
            "cpu_percent": 20.0,
            "cpu_usage_seconds": 3.5,
            "memory_bytes": 200,
            "network_rx_bytes": 1500,
            "network_tx_bytes": 2600,
        },
        {
            "host": "edge1",
            "phase": "queries",
            "cpu_percent": 30.0,
            "cpu_usage_seconds": 4.0,
            "memory_bytes": 300,
            "network_rx_bytes": 1700,
            "network_tx_bytes": 2800,
        },
        {
            "host": "edge1",
            "phase": "queries",
            "cpu_percent": 40.0,
            "cpu_usage_seconds": 6.0,
            "memory_bytes": 400,
            "network_rx_bytes": 2100,
            "network_tx_bytes": 3200,
        },
    ]
    (measured / "resources.jsonl").write_text("\n".join(json.dumps(row) for row in samples) + "\n")

    summary = report(run_dir)
    with (summary / "scalability.csv").open() as handle:
        row = next(csv.DictReader(handle))
    assert float(row["preparation_seconds_median"]) == 0.7
    assert float(row["ready_seconds_median"]) == 1.1
    assert float(row["cpu_seconds_median"]) == 4.0
    assert float(row["network_rx_bytes_median"]) == 1100
    assert float(row["catalog_throughput_per_second"]) == 5
    assert (summary / "preparation.csv").is_file()
    with (summary / "phase_resources.csv").open() as handle:
        phases = {item["phase"]: item for item in csv.DictReader(handle)}
    assert float(phases["preparation"]["cpu_mean_percent"]) == 15
    assert float(phases["queries"]["cpu_mean_percent"]) == 35
    assert float(phases["preparation"]["cpu_seconds_median"]) == 1.5
    assert float(phases["queries"]["cpu_seconds_median"]) == 2.0
    with (summary / "physical_queries.csv").open() as handle:
        physical = next(csv.DictReader(handle))
    assert physical["host"] == "edge1"
    assert len(list((run_dir / "figures").glob("*.png"))) == 25
    figure_manifest = json.loads((run_dir / "figures/manifest.json").read_text())
    assert figure_manifest["figure_count"] == 25


def test_semantic_contract_snapshot_is_self_contained(root, tmp_path):
    manifest = json.loads((root / "queries/manifest.json").read_text())
    _snapshot_semantic_contract(root, tmp_path, manifest)
    assert (tmp_path / "semantic-contract/ontology/benchmark/base.nt").is_file()
    assert (tmp_path / "semantic-contract/ontology/benchmark/manifest.json").is_file()
    assert (tmp_path / "semantic-contract/queries/manifest.json").is_file()
    assert len(list((tmp_path / "semantic-contract/queries").rglob("*.rq"))) == 113
