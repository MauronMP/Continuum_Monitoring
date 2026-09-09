from __future__ import annotations

import csv

from continuum_bench.experiment_reporting import plot_experiment_coverage


def test_experiment_coverage_keeps_timeouts_and_failures(tmp_path):
    summary = tmp_path / "physical/scale-out/summary.csv"
    summary.parent.mkdir(parents=True)
    with summary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("reasoner", "status"))
        writer.writeheader()
        writer.writerows(
            (
                {"reasoner": "rdfs", "status": "completed"},
                {"reasoner": "rdfs", "status": "timeout"},
                {"reasoner": "rdfs", "status": "skipped_after_timeout"},
                {"reasoner": "rdfs", "status": "failed"},
            )
        )

    outputs = plot_experiment_coverage(tmp_path, ("scale-out",))

    assert len(outputs) == 2
    with outputs[0].open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["completed_samples"] == "1"
    assert row["timeout_samples"] == "1"
    assert row["skipped_samples"] == "1"
    assert row["failed_or_other_samples"] == "1"
    assert float(row["completion_rate_percent"]) == 25
    assert all(path.is_file() for path in outputs)
