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
    assert config.experiment["physical_query_request_timeout_seconds"] == 120
    assert config.experiment["logical_query_timeout_seconds"] == 120
    assert config.experiment["recovery_timeout_seconds"] == 120


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


def test_legacy_query_timeout_is_a_backward_compatible_alias(root, tmp_path):
    text = (root / "configs/benchmark.toml").read_text()
    text = text.replace("physical_query_request_timeout_seconds = 120\n", "request_timeout_seconds = 37\n")
    text = text.replace("logical_query_timeout_seconds = 120\n", "")
    path = tmp_path / "legacy.toml"
    path.write_text(text)
    config = load_config(path)
    assert config.experiment["physical_query_request_timeout_seconds"] == 37
    assert config.experiment["logical_query_timeout_seconds"] == 37


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("health_timeout_seconds = 120", "health_timeout_seconds = -1", "health_timeout_seconds"),
        ("minimum_free_disk_mib = 4096", "minimum_free_disk_mib = 0", "minimum_free_disk_mib"),
        ('name = "users-50"', 'name = "users-1"', "scenario names"),
    ],
)
def test_invalid_operational_configuration_is_rejected(root, tmp_path, old, new, message):
    path = tmp_path / "invalid.toml"
    path.write_text((root / "configs/benchmark.toml").read_text().replace(old, new, 1))
    with pytest.raises(ValueError, match=message):
        load_config(path)
