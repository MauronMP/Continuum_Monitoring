from __future__ import annotations

from dataclasses import replace

import pytest

from continuum_bench.config import _validate_benchmark
from continuum_bench.experiment_config import load_experiment_config
from continuum_bench.load_config import load_load_config


def test_benchmark_scale_must_be_strictly_increasing(config):
    with pytest.raises(ValueError, match="strictly increasing"):
        _validate_benchmark(replace(config, scale_users=(25, 5)))


def test_benchmark_rejects_unknown_reasoner(config):
    with pytest.raises(ValueError, match="unsupported"):
        _validate_benchmark(replace(config, reasoners=("rdfs", "unknown")))


def test_load_early_stop_dimensions_must_be_ordered(config, tmp_path):
    source = (config.root / "configs/load-benchmark.toml").read_text(
        encoding="utf-8"
    )
    path = tmp_path / "load.toml"
    path.write_text(
        source.replace(
            'name = "eps-200"\ndimension = "events_per_second"\n'
            "events_per_second = 200",
            'name = "eps-200"\ndimension = "events_per_second"\n'
            "events_per_second = 25",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="monotonic load"):
        load_load_config(path)


def test_distributed_ontology_scale_must_be_ordered(config, tmp_path):
    source = (config.root / "configs/experiments-smoke.toml").read_text(
        encoding="utf-8"
    )
    path = tmp_path / "experiments.toml"
    path.write_text(
        source.replace("users = [0, 10]", "users = [10, 0]"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="strictly increasing"):
        load_experiment_config(path)
