from __future__ import annotations

import csv
from dataclasses import replace

import pytest

from continuum_bench import physical, sharded
from continuum_bench.distributed import Endpoint
from continuum_bench.topology import load_topology


def _statuses(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            (row["synthetic_users"], row["reasoner"], row["status"])
            for row in csv.DictReader(handle)
        ]


@pytest.mark.parametrize(
    ("runner", "module", "extra"),
    (
        (physical.run_physical_scalability, physical, {}),
        (
            sharded.run_sharded_scalability,
            sharded,
            {"target": "physical", "validate_results": False},
        ),
    ),
)
def test_distributed_scalability_timeout_continues_other_reasoners(
    config,
    tmp_path,
    monkeypatch,
    runner,
    module,
    extra,
):
    selected = replace(
        config,
        reasoners=("rdfs", "owlrl"),
        scale_users=(5, 25),
        repetitions=1,
    )
    endpoint = Endpoint(
        "http://worker:8391",
        "cloud",
        tier="cloud",
        authority=True,
        categories=selected.category_order,
    )
    calls = []

    def timeout(*args, **kwargs):
        calls.append((args, kwargs))
        raise TimeoutError("HTTP Error 408: Request Timeout")

    monkeypatch.setattr(module, "discover", lambda *args, **kwargs: [endpoint])
    monkeypatch.setattr(module, "_prepare", timeout)
    topology = load_topology(
        config.root / "configs/topologies/physical/topology.toml",
        "physical",
    )

    output = runner(
        selected,
        topology if module is physical else [endpoint.url],
        tmp_path,
        **extra,
    )

    assert len(calls) == 2
    assert _statuses(output / "summary.csv") == [
        ("5", "rdfs", "timeout"),
        ("5", "owlrl", "timeout"),
        ("25", "rdfs", "skipped_after_timeout"),
        ("25", "owlrl", "skipped_after_timeout"),
    ]
