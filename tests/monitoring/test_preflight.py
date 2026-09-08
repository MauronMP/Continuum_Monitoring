from dataclasses import replace

import pytest

from continuum_bench.experiment_config import load_experiment_config
from continuum_bench.load_config import load_load_config
from continuum_bench.preflight import (
    WorkloadTarget,
    validate_experiment_workload,
    validate_load_workload,
    validate_workload_targets,
)


def test_repository_workloads_pass_capacity_preflight(config):
    load = load_load_config(config.root / "configs/load-benchmark.toml")
    experiments = load_experiment_config(
        config.root / "configs/experiments.toml"
    )

    assert validate_load_workload(config, load)["targets_checked"] == 23
    assert validate_experiment_workload(
        config, experiments, "configs/experiments.toml"
    )["targets_checked"] == 16


def test_preflight_rejects_target_that_would_shrink_graph(config):
    target = WorkloadTarget(
        source="invalid.toml",
        name="too-small",
        users=500,
        target_triples=25_000,
        rule_count=25,
    )

    with pytest.raises(ValueError, match=r"minimum=43097"):
        validate_workload_targets(config, [target])


def test_selected_load_profiles_are_checked(config):
    workload = load_load_config(config.root / "configs/load-smoke.toml")
    invalid = replace(
        workload,
        profiles=(replace(workload.profiles[0], target_triples=1),),
    )

    with pytest.raises(ValueError, match="eps-smoke"):
        validate_load_workload(config, invalid)
