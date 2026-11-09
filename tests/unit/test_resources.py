import json

from continuum_bench.resources import ResourceSampler
from continuum_bench.topology import Host


def test_resource_samples_and_events_are_phase_labelled(tmp_path):
    output = tmp_path / "resources.jsonl"
    with ResourceSampler((), "pi", "worker", output, 60) as sampler:
        sampler.set_phase("preparation")
        sampler._record_sample({"timestamp": "t1", "host": "edge1", "cpu_percent": 10})
        sampler.set_phase("queries")
        sampler._record_sample({"timestamp": "t2", "host": "edge1", "cpu_percent": 20})

    rows = [json.loads(line) for line in output.read_text().splitlines()]
    events = [(row.get("event"), row.get("phase")) for row in rows if "event" in row]
    samples = [row for row in rows if "host" in row]
    assert events == [
        ("phase_start", "preparation"),
        ("phase_end", "preparation"),
        ("phase_start", "queries"),
        ("phase_end", "queries"),
    ]
    assert [row["phase"] for row in samples] == ["preparation", "queries"]


def test_resource_sampler_selects_base_worker_by_published_port(tmp_path):
    host = Host("mist", "mist", "near-edge", "100.72.111.107", 8391)
    sampler = ResourceSampler((host,), "pi", "continuum-worker:rust-v1", tmp_path / "samples.jsonl", 1)
    selector = sampler._container_selector(host)
    assert "publish=8391" in selector
    assert "com.docker.compose.service" not in selector


def test_resource_sampler_uses_explicit_replica_name(tmp_path):
    replica = Host("edge3-replica-on-mist", "edge", "partition-c", "100.72.111.107", 8491)
    sampler = ResourceSampler(
        (replica,),
        "pi",
        "continuum-worker:rust-v1",
        tmp_path / "samples.jsonl",
        1,
        container_names={replica.id: "continuum-adaptation-run"},
    )
    assert "name=^/continuum-adaptation-run$" in sampler._container_selector(replica)
