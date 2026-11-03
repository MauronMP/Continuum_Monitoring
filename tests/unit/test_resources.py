import json

from continuum_bench.resources import ResourceSampler


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
