from __future__ import annotations

from types import SimpleNamespace

from continuum_bench import cli, distributed, physical, physical_cluster, sharded


def test_distributed_layout_defaults_to_sharded():
    parser = cli._parser()

    docker = parser.parse_args(["docker", "cumulative"])
    physical = parser.parse_args(["physical", "scalability"])

    assert docker.layout == "sharded"
    assert physical.layout == "sharded"


def test_default_smoke_checks_docker_before_running_python(config, monkeypatch):
    from continuum_bench import engine_stack
    import pytest

    monkeypatch.setattr(engine_stack, "preflight", lambda root: (_ for _ in ()).throw(RuntimeError("docker.sock permission denied")))
    monkeypatch.setattr(cli, "run_cumulative", lambda config: pytest.fail("Python benchmark must not start before Docker preflight"))
    with pytest.raises(RuntimeError, match="docker.sock"):
        cli.main(["--config", str(config.root / "configs/smoke-cumulative.toml"), "benchmark", "cumulative"])


def test_distributed_layout_accepts_replicated():
    parser = cli._parser()

    docker = parser.parse_args(
        ["docker", "cumulative", "--layout", "replicated"]
    )
    physical = parser.parse_args(
        ["physical", "scalability", "--layout", "replicated"]
    )

    assert docker.layout == "replicated"
    assert physical.layout == "replicated"


def test_physical_cli_accepts_key_authorization_action():
    parser = cli._parser()

    physical = parser.parse_args(["physical", "authorize"])

    assert physical.action == "authorize"


def test_docker_cli_routes_sharded_layout_to_layout_directory(
    config,
    tmp_path,
    monkeypatch,
):
    calls = []

    def fake_sharded(config, endpoints, output_root, **options):
        calls.append((endpoints, output_root, options))
        return output_root / "cumulative"

    monkeypatch.setattr(sharded, "run_sharded_cumulative", fake_sharded)
    monkeypatch.setattr(
        distributed,
        "run_docker_cumulative",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("replicated runner must not be used")
        ),
    )

    status = cli.main(
        [
            "--config",
            str(config.root / "configs" / "smoke-cumulative.toml"),
            "docker",
            "cumulative",
            "--topology-only",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert status == 0
    assert len(calls) == 1
    endpoints, output_root, options = calls[0]
    assert endpoints == [
        "http://127.0.0.1:8191",
        "http://127.0.0.1:8192",
        "http://127.0.0.1:8193",
        "http://127.0.0.1:8194",
        "http://127.0.0.1:8195",
    ]
    assert output_root == tmp_path / "sharded"
    assert options["target"] == "docker"
    assert options["validate_results"] is True
    assert options["topology"].name == "docker"
    assert len(options["topology"].active_nodes) == 5


def test_physical_cli_routes_sharded_layout_to_layout_directory(
    config,
    tmp_path,
    monkeypatch,
):
    calls = []
    endpoints = [
        "http://cloud",
        "http://fog",
        "http://edge1",
        "http://edge2",
        "http://edge3",
    ]

    def fake_sharded(config, received, output_root, **options):
        calls.append((received, output_root, options))
        return output_root / "scalability"

    monkeypatch.setattr(
        physical_cluster,
        "load_physical_inventory",
        lambda path, ssh_user=None: SimpleNamespace(
            nodes=tuple(
                SimpleNamespace(endpoint=endpoint)
                for endpoint in endpoints
            ),
            topology=None,
        ),
    )
    monkeypatch.setattr(sharded, "run_sharded_scalability", fake_sharded)
    monkeypatch.setattr(
        physical,
        "run_physical_scalability",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("replicated runner must not be used")
        ),
    )

    status = cli.main(
        [
            "--config",
            str(config.root / "configs" / "smoke-cumulative.toml"),
            "physical",
            "scalability",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert status == 0
    assert calls == [
        (
            endpoints,
            tmp_path / "sharded",
            {"target": "physical", "validate_results": True},
        )
    ]


def test_physical_sharded_cli_passes_elastic_topology(
    config,
    tmp_path,
    monkeypatch,
):
    calls = []
    topology = SimpleNamespace(name="physical")
    inventory = SimpleNamespace(
        nodes=(SimpleNamespace(endpoint="http://physical-node"),),
        topology=topology,
    )

    monkeypatch.setattr(
        physical_cluster,
        "load_physical_inventory",
        lambda path, ssh_user=None: inventory,
    )
    monkeypatch.setattr(
        sharded,
        "run_sharded_cumulative",
        lambda config, endpoints, output_root, **options: (
            calls.append((endpoints, options)) or output_root / "cumulative"
        ),
    )

    status = cli.main(
        [
            "--config",
            str(config.root / "configs" / "smoke-cumulative.toml"),
            "physical",
            "cumulative",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert status == 0
    assert calls == [
        (
            ["http://physical-node"],
            {
                "target": "physical",
                "validate_results": True,
                "topology": topology,
            },
        )
    ]
