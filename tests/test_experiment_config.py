import pytest

from continuum_bench import cli
from continuum_bench.experiment_config import (
    load_experiment_config,
    select_reasoning_profiles,
)


def test_experiment_smoke_config_defines_all_three_families(config):
    workload = load_experiment_config(
        config.root / "configs/experiments-smoke.toml"
    )

    assert workload.scale_out_node_counts == (1, 3, 5)
    assert {item.dimension for item in workload.reasoning_profiles} == {
        "target_triples",
        "rule_count",
        "users",
    }
    assert workload.distributed_users == (0, 10)


def test_reasoning_profile_selection_is_explicit(config):
    workload = load_experiment_config(
        config.root / "configs/experiments-smoke.toml"
    )

    selected = select_reasoning_profiles(workload, ["rules-5"])

    assert [item.name for item in selected.reasoning_profiles] == ["rules-5"]
    with pytest.raises(ValueError, match="Unknown reasoning profiles"):
        select_reasoning_profiles(workload, ["missing"])


def test_experiment_cli_commands_are_distinct():
    parser = cli._parser()

    scale_out = parser.parse_args(["experiment", "scale-out", "monolith"])
    hardware = parser.parse_args(
        ["experiment", "reasoning-hardware", "docker"]
    )
    distributed = parser.parse_args(
        ["experiment", "distributed-ontology", "physical"]
    )
    plot = parser.parse_args(["experiment", "plot", "all"])
    analyze = parser.parse_args(["experiment", "analyze"])

    assert scale_out.experiment_name == "scale-out"
    assert hardware.experiment_name == "reasoning-hardware"
    assert distributed.experiment_name == "distributed-ontology"
    assert plot.suite == "all"
    assert analyze.experiment_name == "analyze"
