from __future__ import annotations

from types import SimpleNamespace

from continuum_bench import cli


def test_physical_layout_defaults_to_distributed():
    parser = cli._parser()

    args = parser.parse_args(["physical", "scalability"])

    assert args.layout == "distributed"


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
        return {"scalability": str(output_root / "distributed" / "scalability")}

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
                "layout": "distributed",
                "validate_results": True,
            },
        )
    ]


def test_physical_cli_applies_independent_limits_and_skip_policy(config, tmp_path, monkeypatch):
    from contextlib import nullcontext
    from continuum_bench.monitoring import lease
    import continuum_bench.monitoring as monitoring
    captured = []
    monkeypatch.setattr(lease, 'physical_lease', lambda root: nullcontext())
    monkeypatch.setattr(cli, '_physical_inventory', lambda *a: SimpleNamespace())
    monkeypatch.setattr(monitoring, 'run_physical_monitoring_suite', lambda cfg, *a, **k: captured.append(cfg) or {})
    assert cli.main(['--request-timeout-seconds', '40', '--phase-timeout-seconds', '35',
                     '--point-timeout-seconds', '100', '--skip-after-timeouts', '2',
                     '--no-skip-repetitions', '--skip-larger-points', '--no-skip-cumulative-stages',
                     'physical', 'all', '--reasoner', 'hermit', '--reasoner', 'jfact',
                     '--output-dir', str(tmp_path)]) == 0
    cfg = captured[0]
    assert cfg.reasoners == ('hermit', 'jfact')
    assert cfg.distributed.request_timeout_seconds == 40
    assert cfg.limits.phase_timeout_seconds == 35
    assert cfg.limits.point_timeout_seconds == 100
    assert cfg.limits.consecutive_timeout_threshold == 2
    assert cfg.limits.skip_repetitions_after_timeout is False
    assert cfg.limits.skip_larger_sizes_after_timeout is True
    assert cfg.limits.skip_cumulative_stages_after_timeout is False


def test_physical_prepare_is_offline_and_does_not_take_worker_lease(tmp_path, monkeypatch):
    from continuum_bench import physical_cluster
    from continuum_bench.monitoring import lease
    monkeypatch.setattr(lease, 'physical_lease', lambda root: (_ for _ in ()).throw(AssertionError('lease')))
    monkeypatch.setattr(cli, '_physical_inventory', lambda *a: SimpleNamespace())
    monkeypatch.setattr(physical_cluster, 'write_offline_manifest', lambda *a: {'local_files_ready': True, 'remote_contacted': False})
    monkeypatch.setattr(physical_cluster, 'start_cluster', lambda *a: (_ for _ in ()).throw(AssertionError('network')))
    assert cli.main(['physical', 'prepare', '--output-dir', str(tmp_path)]) == 0


def test_new_comparison_defaults_and_removed_layout(config):
    import pytest
    assert config.reasoners == ('rdfs', 'hermit', 'openllet', 'jfact', 'konclude')
    with pytest.raises(SystemExit):
        cli._parser().parse_args(['physical', 'all', '--layout', 'sharded'])
