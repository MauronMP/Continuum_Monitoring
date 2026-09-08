from __future__ import annotations

import csv
from dataclasses import replace

from continuum_bench import experiments
from continuum_bench.experiment_config import load_experiment_config


def test_scale_out_timeout_skips_repetitions_but_continues_reasoners(
    config,
    tmp_path,
    monkeypatch,
):
    workload = replace(
        load_experiment_config(config.root / "configs/experiments-smoke.toml"),
        repetitions=3,
        scale_out_node_counts=(1,),
    )
    selected_config = replace(config, reasoners=("rdfs", "owlrl"))
    from continuum_bench.distributed import Endpoint
    monkeypatch.setattr(experiments, "discover", lambda *_: [Endpoint("http://worker:8391", "cloud")])
    monkeypatch.setattr(experiments, "_metadata", lambda *args: {})
    calls = []

    def timeout(*args, **kwargs):
        calls.append((args, kwargs))
        raise TimeoutError("bounded prepare timeout")

    monkeypatch.setattr(experiments, "_replicated_prepare", timeout)

    output = experiments.run_scale_out(
        selected_config,
        workload,
        "physical",
        tmp_path,
    )

    with (output / "summary.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(calls) == 2
    for reasoner in selected_config.reasoners:
        statuses = [
            row["status"] for row in rows if row["reasoner"] == reasoner
        ]
        assert statuses == [
            "timeout",
            "skipped_after_timeout",
            "skipped_after_timeout",
        ]
