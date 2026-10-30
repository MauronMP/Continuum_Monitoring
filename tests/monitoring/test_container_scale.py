"""Container placements preserve physical limits and scientific comparison contracts."""

import json

import pytest

from continuum_bench.cli import _parser
from continuum_bench.monitoring.container_scale.config import load
from continuum_bench.monitoring.container_scale.deployment import (
    compose_document,
    doctor,
    render,
)
from continuum_bench.monitoring.container_scale.runner import workload, run
from continuum_bench.topology import load_topology


@pytest.fixture
def settings(root):
    return load(root / "configs/container-scale.toml", root)


def test_placement_roundtrip_preserves_host_and_authority(root, settings, tmp_path):
    topology = render(settings, root, tmp_path, 2)
    reloaded = load_topology(tmp_path / "topology.toml", "container-scale")
    assert reloaded.fingerprint == topology.fingerprint
    assert len(topology.active_nodes) == 12
    assert len({n.host for n in topology.active_nodes}) == 6
    assert len({n.endpoint for n in topology.active_nodes}) == 12
    assert len(topology.authority_nodes) == 8
    assert all(n.memory == "1536m" for n in topology.active_nodes)


def test_compose_limits_and_vpn_bind(settings):
    node = settings.topology.active_nodes[0]
    spec = compose_document(settings, node, 2)
    assert len(spec["services"]) == 2
    for service in spec["services"].values():
        assert service["build"]["network"] == "host"
        assert "network_mode" not in service
        assert service["cpus"] == 1
        assert service["mem_limit"] == service["memswap_limit"] == "1536m"
        assert service["ports"][0].startswith(node.host + ":")
        assert "privileged" not in service
        assert service["restart"] == "no"
        assert not any("docker.sock" in v for v in service["volumes"])
        assert service["logging"]["options"]["max-size"] == "5m"
    for remote in settings.topology.active_nodes:
        if not remote.local:
            for service in compose_document(settings, remote, 1)["services"].values():
                assert "network" not in service["build"]
                assert "network_mode" not in service


@pytest.mark.parametrize(
    "old,new",
    [
        ("containers_per_host = [1]", "containers_per_host = [10]"),
        ("containers_per_host = [1]", "containers_per_host = [0]"),
        ('reasoners = ["rdfs"]', 'reasoners = ["hermit"]'),
        ("base_port = 8491", "base_port = 65535"),
        ("repetitions = 3", "repetitions = 0"),
        ("concurrency = [1, 2, 4]", "concurrency = [4, 1]"),
    ],
)
def test_invalid_budgets_are_rejected(root, tmp_path, old, new):
    path = tmp_path / "config.toml"
    path.write_text(
        (root / "configs/container-scale.toml").read_text().replace(old, new)
    )
    with pytest.raises(ValueError):
        load(path, root)


def test_weak_load_scales_but_strong_does_not(settings):
    strong = next(s for s in settings.raw["scenarios"] if s["family"] == "strong")
    weak = next(s for s in settings.raw["scenarios"] if s["family"] == "weak")
    assert workload(settings, strong, 6).users == workload(settings, strong, 12).users
    assert workload(settings, weak, 12).users == 2 * workload(settings, weak, 6).users
    assert (
        workload(settings, weak, 12).target_triples[0]
        == 2 * workload(settings, weak, 6).target_triples[0]
    )
    assert workload(settings, strong, 6, True).repetitions == 1
    assert not workload(settings, strong, 6, True).semantic_validation


def test_doctor_uses_available_memory(settings, monkeypatch):
    from continuum_bench.monitoring.container_scale import deployment

    monkeypatch.setattr(
        deployment,
        "execute",
        lambda *a, **k: json.dumps(
            dict(
                docker_ok=True,
                compose_ok=True,
                memory_limit_supported=True,
                swap_limit_supported=True,
                cpu_quota_supported=True,
                pids_limit_supported=True,
                memory_available_mib=100,
                memory_total_mib=8192,
                disk_available_mib=10000,
                cpu_count=4,
            )
        ),
    )
    assert not any(r["ready"] for r in doctor(settings, 1))


def test_dry_run_does_not_contact_hosts(root, settings, tmp_path, monkeypatch):
    from continuum_bench.config import load_config
    from continuum_bench.monitoring.container_scale import deployment

    monkeypatch.setattr(
        deployment, "execute", lambda *a, **k: pytest.fail("dry-run contacted a host")
    )
    result = run(
        settings,
        load_config(root / "configs/benchmark.toml"),
        tmp_path,
        dry_run=True,
        scenario_names=["users-1"],
    )
    summary = json.loads((result / "campaign.json").read_text())
    assert summary["status"] == "planned"
    assert len(summary["steps"]) == 1
    assert (result / "placement-1/topology.toml").exists()


def test_cli_has_separate_battery():
    args = _parser().parse_args(
        ["--keep-going", "container-scale", "run", "--scenario", "users-1"]
    )
    assert args.command == "container-scale" and args.keep_going


def test_report_keeps_failures_visible_and_separates_host_ids(tmp_path):
    from continuum_bench.csv_utils import write_dict_rows
    from continuum_bench.monitoring.container_scale.reporting import report

    root = tmp_path
    (root / "configuration.json").write_text(
        json.dumps(
            {"scenarios": [{"name": "users-1", "family": "users", "users": 10}]}
        )
    )
    dest = root / "placement-1/users-1/measured/distributed-reasoning-scalability"
    row = dict(
        run_id="one",
        layout="distributed",
        reasoner="rdfs",
        status="completed",
        benchmark_end_to_end_ms=20,
        reasoning_ms=10,
        current_rss_kib_sum=4096,
        asserted_triples=100,
    )
    write_dict_rows(
        dest / "distributed-reasoning-summary.csv",
        [row, {**row, "status": "timeout", "run_id": "two"}],
        empty_message="No rows",
    )
    write_dict_rows(
        dest / "node-runs.csv",
        [
            dict(
                run_id="one",
                node_id="edge1-c1",
                layout="distributed",
                reasoner="rdfs",
                reasoning_ms=10,
                current_rss_kib=4096,
                process_cpu_ms=12,
            )
        ],
        empty_message="No nodes",
    )
    figures = report(root)
    manifest = json.loads((figures / "manifest.json").read_text())
    assert any(p.endswith("-hosts.png") for p in manifest["figures"])
    assert any(p.endswith("-status.png") for p in manifest["figures"])
    assert all((figures / p).stat().st_size > 1000 for p in manifest["figures"])
    assert not list(figures.glob("*.pdf"))


def test_doctor_rejects_ineffective_kernel_limits(settings, monkeypatch):
    from continuum_bench.monitoring.container_scale import deployment

    monkeypatch.setattr(
        deployment,
        "execute",
        lambda *a, **k: json.dumps(
            dict(
                docker_ok=True,
                compose_ok=True,
                memory_limit_supported=False,
                swap_limit_supported=False,
                cpu_quota_supported=True,
                pids_limit_supported=True,
                memory_available_mib=7000,
                memory_total_mib=8192,
                disk_available_mib=12000,
                cpu_count=4,
            )
        ),
    )
    rows = doctor(settings, 1)
    assert all(not r["ready"] for r in rows)
    assert all(any("cgroup" in e for e in r["errors"]) for r in rows)


def test_boot_edit_preserves_other_kernel_options(root, tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "enable_memory", root / "containers/worker/enable-memory-cgroup.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / "cmdline.txt"
    path.write_text(
        "console=tty1 root=PARTUUID=abc cgroup_disable=memory,io cgroup_memory=0 quiet\n"
    )
    assert module.enable(path)
    text = path.read_text()
    assert "root=PARTUUID=abc" in text and "cgroup_disable=io" in text
    assert "cgroup_memory=1" in text and "cgroup_enable=memory" in text
    assert not module.enable(path)
    assert len(list(tmp_path.glob("*.continuum-backup-*"))) == 1


def test_explicit_host_exclusion_is_recorded_without_editing_inventory(root):
    selected = load(root / "configs/container-scale.toml", root, exclude_hosts=["mist"])
    assert selected.deployment["exclude_hosts"] == ["mist"]
    assert len(selected.topology.active_nodes) == 5
    assert all(n.node_id != "mist" for n in selected.topology.active_nodes)
    assert (
        len(
            load_topology(
                root / "configs/topologies/physical/topology.toml", "physical"
            ).active_nodes
        )
        == 6
    )
    with pytest.raises(ValueError, match="Unknown excluded"):
        load(root / "configs/container-scale.toml", root, exclude_hosts=["typo"])
    with pytest.raises(ValueError, match="Cloud"):
        load(root / "configs/container-scale.toml", root, exclude_hosts=["cloud"])


def test_lifecycle_selection_keeps_experiment_topology(root):
    from continuum_bench.monitoring.container_scale.deployment import selected_hosts

    config = load(root / "configs/container-scale.toml", root, exclude_hosts=["mist"])
    assert [n.node_id for n in selected_hosts(config, ["fog"])] == ["fog"]
    assert len(config.topology.active_nodes) == 5
    with pytest.raises(ValueError, match="Unknown or excluded"):
        selected_hosts(config, ["mist"])


def test_user_workload_preserves_natural_graph_size(settings):
    from rdflib import Graph, URIRef
    from continuum_bench.synthetic import pad_to_target_triples

    scenario = next(s for s in settings.raw["scenarios"] if s["name"] == "users-1")
    target = workload(settings, scenario, 5).target_triples[0]
    assert target == 0
    graph = Graph()
    graph.add((URIRef("urn:s"), URIRef("urn:p"), URIRef("urn:o")))
    assert pad_to_target_triples(graph, target, mode="neutral") == 0
    assert len(graph) == 1


def test_cli_reasoner_matrix_enables_dl_and_records_canonical_names(root):
    args = _parser().parse_args([
        "container-scale", "run", "--reasoner", "rdf", "--reasoner", "jfact",
        "--reasoner", "rdf", "--dry-run",
    ])
    config = load(root / "configs/container-scale.toml", root, reasoners=args.reasoner)
    assert config.experiment["reasoners"] == ["rdfs", "jfact"]
    assert config.deployment["install_dl"] is True
    assert config.deployment["exclude_hosts"] == []


def test_invalid_reasoner_override_is_rejected(root):
    with pytest.raises(ValueError, match="reasoner matrix"):
        load(root / "configs/container-scale.toml", root, reasoners=["unknown"])


def test_reasoner_validation_continues_after_backend_failure(settings, monkeypatch, root):
    from continuum_bench.monitoring.container_scale import deployment
    settings.experiment["reasoners"] = ["jfact", "rdfs"]
    def execute(*args):
        if args[-1] == "jfact":
            raise RuntimeError("inference failed")
        return "verified"
    monkeypatch.setattr(deployment, "compose", execute)
    rows = deployment.validate_reasoners(settings, root, ["cloud"])
    assert [row["status"] for row in rows] == ["failed", "passed"]


def test_local_commands_pin_native_engine(settings, monkeypatch):
    from types import SimpleNamespace
    from continuum_bench.monitoring.container_scale import deployment
    calls = []
    monkeypatch.setenv("DOCKER_CONTEXT", "desktop-linux")
    monkeypatch.setattr(deployment.subprocess, "run", lambda *a, **kw: calls.append(kw) or SimpleNamespace(returncode=0, stdout="ok"))
    deployment.execute(settings, settings.topology.active_nodes[0], ["docker", "info"])
    assert calls[0]["env"]["DOCKER_CONTEXT"] == "default"


def test_dry_run_cannot_silently_execute_lifecycle_actions():
    from continuum_bench.monitoring.container_scale.cli import dispatch
    args = _parser().parse_args(["container-scale", "validate-reasoners", "--dry-run"])
    with pytest.raises(ValueError, match="supported only"):
        dispatch(args, None)


@pytest.mark.parametrize('failure,recover,expected_calls', [
    ('Temporary failure in name resolution', True, 2),
    ('Temporary failure in name resolution', False, 2),
    ('No matching distribution found', False, 1),
])
def test_build_retry_is_bounded_and_dns_specific(settings, root, tmp_path, monkeypatch,
                                                failure, recover, expected_calls):
    from continuum_bench.monitoring.container_scale import deployment
    calls = []
    def build(*args):
        calls.append(args)
        if len(calls) == 1 or not recover:
            raise RuntimeError(failure)
        return 'Build succeeded\n'
    monkeypatch.setattr(deployment, 'compose', build)
    monkeypatch.setattr(deployment.time, 'sleep', lambda _: None)
    node = settings.topology.active_nodes[0]
    if recover:
        deployment.build_image(settings, root, node, tmp_path)
        assert (tmp_path / 'cloud-build.log').read_text() == 'Build succeeded\n'
    else:
        with pytest.raises(RuntimeError, match=failure):
            deployment.build_image(settings, root, node, tmp_path)
    assert len(calls) == expected_calls
    assert failure in (tmp_path / 'cloud-build-attempt-1.log').read_text()


def test_scientific_summary_does_not_impute_timeouts_or_missing_references():
    from continuum_bench.monitoring.container_scale.synthesis import values, semantic_state
    rows = [{'status':'completed','cost':'12'}, {'status':'timeout','cost':'120'}]
    assert values(rows, 'cost') == [12]
    assert values([rows[1]], 'cost') == []
    assert semantic_state([{'status':'replicated_reference_unavailable'}]) == 'reference unavailable'
    assert semantic_state([{'status':'mismatch'}]) == 'mismatch'


def test_concurrency_override_is_archived_and_reaches_workload(root, tmp_path, monkeypatch):
    from continuum_bench.config import load_config
    from continuum_bench.monitoring.container_scale import cli, deployment
    monkeypatch.setattr(deployment, 'execute', lambda *a, **k: pytest.fail('Dry run contacted a host'))
    original = (root / 'configs/container-scale.toml').read_text()
    args = _parser().parse_args(['container-scale', 'run', '--dry-run', '--scenario', 'users-50',
        '--concurrency', '4', '1', '2', '--concurrency', '8', '2', '--output-dir', str(tmp_path)])
    assert cli.dispatch(args, load_config(root / 'configs/benchmark.toml')) == 0
    effective = json.loads(next(tmp_path.glob('*/configuration.json')).read_text())
    scenario = next(s for s in effective['scenarios'] if s['name'] == 'users-50')
    assert scenario['concurrency'] == [1, 2, 4, 8]
    assert next(s for s in effective['scenarios'] if s['name'] == 'users-1')['concurrency'] == [1]
    settings = load(root / 'configs/container-scale.toml', root)
    assert workload(settings, scenario, 6).query_concurrency == (1, 2, 4, 8)
    assert (root / 'configs/container-scale.toml').read_text() == original


@pytest.mark.parametrize('level', ['0', '-1'])
def test_concurrency_override_rejects_nonpositive_levels(root, level):
    from continuum_bench.config import load_config
    from continuum_bench.monitoring.container_scale.cli import dispatch
    args = _parser().parse_args(['container-scale', 'run', '--dry-run', '--concurrency', level])
    with pytest.raises(ValueError, match='positive integers'):
        dispatch(args, load_config(root / 'configs/benchmark.toml'))


def test_report_retains_failed_user_levels_and_concurrency_grid(tmp_path):
    import matplotlib
    matplotlib.use('Agg')
    from continuum_bench.monitoring.container_scale.synthesis import synthesis
    config = {'scenarios': [dict(name=f'users-{n}', family='users', users=n,
                concurrency=[1, 2, 4, 8]) for n in [1, 1000, 2000]],
              'experiment': {'reasoners': ['rdfs'], 'layouts': ['distributed', 'replicated']}}
    (tmp_path / 'configuration.json').write_text(json.dumps(config))
    (tmp_path / 'campaign.json').write_text(json.dumps({'steps': [
        dict(scenario=f'users-{n}', containers_per_host=1, status='failed', error='timed out')
        for n in [1, 1000, 2000]]}))
    figures = tmp_path / 'figures'; figures.mkdir()
    manifest = synthesis(tmp_path, figures)
    assert 'global-placement-1-rdfs-users-concurrency.png' in manifest
    assert 'global-placement-1-rdfs-users.png' in manifest
    import csv
    rows = list(csv.DictReader((tmp_path / 'analysis/global-costs.csv').open()))
    assert {r['scenario'] for r in rows} == {'users-1', 'users-1000', 'users-2000'}
    assert all(r['attempted'] == '0' and r['median'] == '' for r in rows)
    assert len(list(csv.DictReader((tmp_path / 'analysis/missing-measurements.csv').open()))) == 3


def test_node_resource_aggregation_sums_resources_but_not_parallel_wall_times():
    from continuum_bench.monitoring.container_scale.resources import aggregate_nodes
    common = dict(status='completed', layout='distributed', reasoner='rdfs', run_id='r')
    rows = [dict(common, node_id='edge1-c1', process_cpu_ms=1000, reasoning_ms=800),
            dict(common, node_id='edge1-c2', process_cpu_ms=2000, reasoning_ms=1200),
            dict(common, node_id='edge1-c3', process_cpu_ms=9999, reasoning_ms=9999, status='timeout')]
    assert list(aggregate_nodes(rows, 'process_cpu_ms', 1000).values()) == [3]
    assert list(aggregate_nodes(rows, 'reasoning_ms', 1000).values()) == [1.2]


def test_report_explains_failure_before_first_scenario(tmp_path):
    import matplotlib
    matplotlib.use('Agg')
    from continuum_bench.monitoring.container_scale.reporting import report

    (tmp_path / 'configuration.json').write_text(json.dumps({
        'scenarios': [dict(name='users-1', family='users', users=1)],
        'experiment': {'reasoners': ['rdfs'], 'layouts': ['distributed', 'replicated']},
    }))
    (tmp_path / 'campaign.json').write_text(json.dumps({
        'status': 'failed', 'steps': [],
        'error': 'edge2: ssh connection timed out',
    }))
    figures = report(tmp_path)
    manifest = json.loads((figures / 'manifest.json').read_text())['figures']
    assert manifest == [
        'campaign-early-failure-stage.png',
        'campaign-measurement-coverage.png',
    ]
    assert all((figures / name).stat().st_size > 1000 for name in manifest)
