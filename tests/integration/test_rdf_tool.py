import json
import subprocess
from pathlib import Path


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
