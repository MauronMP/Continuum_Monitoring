from __future__ import annotations

from types import SimpleNamespace

from continuum_bench import cli


def test_physical_layout_defaults_to_sharded():
    parser = cli._parser()

    args = parser.parse_args(["physical", "scalability"])

    assert args.layout == "sharded"


def test_physical_layout_accepts_replicated():
    parser = cli._parser()

    args = parser.parse_args(["physical", "cumulative", "--layout", "replicated"])

    assert args.layout == "replicated"


def test_physical_cli_routes_to_monitoring_module(config, tmp_path, monkeypatch):
    from contextlib import nullcontext
    from continuum_bench.monitoring import lease
    monkeypatch.setattr(lease, "physical_lease", lambda root: nullcontext())
    calls = []

    monkeypatch.setattr(
        cli,
        "_physical_inventory",
        lambda config, args: SimpleNamespace(path=config.root / "inventory.toml"),
    )

    def fake_suite(config, inventory, output_root, **options):
        calls.append((inventory, output_root, options))
        return {"scalability": str(output_root / "sharded" / "scalability")}

    import continuum_bench.monitoring as monitoring

    monkeypatch.setattr(monitoring, "run_physical_monitoring_suite", fake_suite)

    status = cli.main(
        [
            "--config",
            str(config.root / "configs" / "smoke-scalability.toml"),
            "physical",
            "scalability",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert status == 0
    assert calls == [
        (
            SimpleNamespace(path=config.root / "inventory.toml"),
            tmp_path,
            {
                "suite": "scalability",
                "layout": "sharded",
                "validate_results": True,
            },
        )
    ]
