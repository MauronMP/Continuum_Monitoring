import hashlib
import json
import subprocess
from pathlib import Path

from continuum_bench.config import Scenario, load_config
from continuum_bench.experiment import generate_dataset, partition_dataset
from continuum_bench.topology import load_topology


def test_rust_generation_and_partition_are_deterministic(root, tmp_path):
    cargo = Path.home() / ".cargo/bin/cargo"
    tool = root / "rust/target/debug/continuum-rdf-tool"
    subprocess.run(
        [str(cargo), "build", "--manifest-path", str(root / "rust/Cargo.toml"), "-p", "continuum-rdf-tool"], check=True
    )
    outputs = []
    for name in ("first.nt", "second.nt"):
        path = tmp_path / name
        subprocess.run(
            [
                str(tool),
                "generate",
                str(root / "ontology/benchmark/base.nt"),
                "--users",
                "10",
                "--seed",
                "2026",
                "--output",
                str(path),
            ],
            check=True,
            capture_output=True,
        )
        outputs.append(path.read_bytes())
    assert outputs[0] == outputs[1]
    result = subprocess.run(
        [
            str(tool),
            "partition",
            str(tmp_path / "first.nt"),
            "--layout",
            "distributed",
            "--participants",
            "a,b",
            "--output-dir",
            str(tmp_path / "parts"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    metadata = json.loads(result.stdout)
    assert len(metadata["fragments"]) == 2
    assert (tmp_path / "parts/a.nt").is_file()


def test_distributed_routing_preserves_full_graph_results(root, tmp_path):
    config = load_config(root / "configs/benchmark.toml")
    topology = load_topology(root / "configs/topology.toml")
    dataset, _ = generate_dataset(config, Scenario("users-1", 1), tmp_path)
    tool = root / "rust/target/release/continuum-rdf-tool"
    fragments, _ = partition_dataset(
        tool,
        dataset,
        root / "ontology/benchmark/base.nt",
        topology.hosts,
        "distributed",
        tmp_path / "fragments",
    )
    manifest = json.loads((root / "queries/manifest.json").read_text())
    selected_ids = {"BASE-Q07", "BASE-Q19", "BASE-Q31", "EXT-Q40", "EXT-Q42", "EXT-Q43"}

    def query(input_path, query_path):
        completed = subprocess.run(
            [str(tool), "query", str(input_path), str(root / query_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)["query"]

    for entry in (item for item in manifest["queries"] if item["id"] in selected_ids):
        expected = query(dataset, entry["path"])
        if entry["execution_scope"] == "cloud":
            path = tmp_path / "cloud.nt"
            path.write_bytes(fragments["cloud"])
            actual = query(path, entry["path"])
            assert actual["result_count"] == expected["result_count"], entry["id"]
            assert actual["result_digest"] == expected["result_digest"], entry["id"]
            continue
        keys = set()
        for host in (host for host in topology.hosts if host.tier == "edge"):
            path = tmp_path / f"{host.id}.nt"
            path.write_bytes(fragments[host.id])
            keys.update(query(path, entry["path"])["result_keys"])
        digest = hashlib.sha256("\n".join(sorted(keys)).encode()).hexdigest()
        assert len(keys) == expected["result_count"], entry["id"]
        assert digest == expected["result_digest"], entry["id"]
