import pytest

from continuum_bench.config import load_config
from continuum_bench.topology import load_topology


def test_scientific_matrix_is_fixed(root):
    config = load_config(root / "configs/benchmark.toml")
    assert [scenario.users for scenario in config.scenarios] == [
        1,
        50,
        100,
        500,
        1000,
        2000,
        4000,
        5000,
        6000,
        7000,
        10000,
        12000,
        14000,
        16000,
        18000,
        20000,
    ]
    assert config.experiment["layouts"] == ["distributed", "replicated"]
    assert config.experiment["query_rounds"] == 18


def test_topology_has_all_continuum_tiers(root):
    topology = load_topology(root / "configs/topology.toml")
    assert len(topology.hosts) == 6
    assert {host.tier for host in topology.hosts} == {"cloud", "fog", "mist", "edge"}
    assert len(topology.fingerprint) == 64


def test_operational_target_must_be_below_hard_timeout(root, tmp_path):
    text = (
        (root / "configs/benchmark.toml")
        .read_text()
        .replace("prepare_operational_target_seconds = 120", "prepare_operational_target_seconds = 600")
    )
    path = tmp_path / "invalid.toml"
    path.write_text(text)
    with pytest.raises(ValueError, match="operational target"):
        load_config(path)
