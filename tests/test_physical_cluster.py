from continuum_bench import physical_cluster
from continuum_bench.physical_cluster import load_physical_inventory
import subprocess
import pytest


def _legacy_inventory(tmp_path, remote_dir):
    path = tmp_path / "legacy-inventory.toml"
    path.write_text(
        "[cluster]\n"
        'ssh_user = "pi"\n'
        f'remote_dir = "{remote_dir}"\n'
        f'remote_python = "{remote_dir}/.venv-node/bin/python"\n'
        "[[nodes]]\n"
        'role = "cloud"\n'
        'host = "127.0.0.1"\n'
        'endpoint = "http://127.0.0.1:8391"\n'
        "local = true\n"
        "port = 8391\n",
        encoding="utf-8",
    )
    return path


def test_status_rejects_wrong_worker_contract(config, monkeypatch):
    inventory = load_physical_inventory(
        config.resolve(config.topology_file)
    )
    monkeypatch.setattr(
        physical_cluster,
        "_request",
        lambda *args, **kwargs: {
            "status": "ok",
            "protocol_version": "5",
            "node_role": "edge",
            "build_id": "continuum-v5-contract",
        },
    )

    statuses = physical_cluster.status_cluster(
        inventory,
        print_output=False,
    )

    assert all(not item["healthy"] for item in statuses)
    assert all(
        "service must be" in item["detail"]["contract_error"]
        for item in statuses
    )


def test_elastic_manifest_is_the_default_physical_inventory(config):
    inventory = load_physical_inventory(
        config.resolve(config.topology_file)
    )

    assert inventory.topology_name == "physical"
    assert inventory.topology is not None
    assert inventory.topology.name == "physical"
    assert [node.tier for node in inventory.nodes] == [
        "cloud",
        "fog",
        "edge",
        "edge",
        "edge",
    ]
    assert [node.role for node in inventory.nodes] == [
        "cloud",
        "fog",
        "edge1",
        "edge2",
        "edge3",
    ]


def test_manifest_ssh_override_updates_remote_paths(config):
    inventory = load_physical_inventory(
        config.resolve(config.topology_file),
        ssh_user="benchmark",
    )

    assert inventory.ssh_user == "benchmark"
    assert inventory.remote_dir == "/home/benchmark/continuum-bench"
    assert inventory.remote_python.startswith(
        "/home/benchmark/continuum-bench/"
    )


def test_authorize_installs_key_on_each_remote_node(config, monkeypatch):
    inventory = load_physical_inventory(
        config.resolve(config.topology_file)
    )
    commands = []
    monkeypatch.setattr(
        physical_cluster,
        "_run",
        lambda command: commands.append(command),
    )

    physical_cluster.authorize_cluster(inventory)

    assert commands == [
        ["ssh-copy-id", "pi@10.151.73.241"],
        ["ssh-copy-id", "pi@10.151.73.34"],
        ["ssh-copy-id", "pi@10.151.73.143"],
        ["ssh-copy-id", "pi@10.151.73.173"],
    ]


def test_ssh_lifecycle_commands_disable_password_prompts():
    command = physical_cluster._ssh(
        "pi@10.151.73.241",
        "true",
    )

    assert command[:3] == ["ssh", "-o", "BatchMode=yes"]


def test_remote_start_records_python_pid_not_background_shell(
    config,
    monkeypatch,
):
    inventory = load_physical_inventory(
        config.resolve(config.topology_file)
    )
    node = next(item for item in inventory.nodes if item.role == "edge2")
    commands = []
    monkeypatch.setattr(
        physical_cluster,
        "_run",
        lambda command: commands.append(command),
    )

    physical_cluster._remote_start(inventory, node)

    remote = commands[0][-1]
    assert "pgrep -f" in remote
    assert "worker_pid=$!" in remote
    assert 'echo "$worker_pid"' in remote
    assert "cd /home/pi/continuum-bench || exit 20; nohup" in remote
    assert "--topology-name physical" in remote


def test_remote_start_passes_elastic_manifest_to_worker(config, monkeypatch):
    inventory = load_physical_inventory(
        config.resolve(config.topology_file)
    )
    node = next(item for item in inventory.nodes if item.role == "edge2")
    commands = []
    monkeypatch.setattr(
        physical_cluster,
        "_run",
        lambda command: commands.append(command),
    )

    physical_cluster._remote_start(inventory, node)

    remote = commands[0][-1]
    assert (
        "--topology-file /home/pi/continuum-bench/runtime/active-topology.toml"
        in remote
    )
    assert "--topology-name physical" in remote


def test_remote_stop_recovers_from_a_stale_pid_file(config, monkeypatch):
    inventory = load_physical_inventory(
        config.resolve(config.topology_file)
    )
    node = next(item for item in inventory.nodes if item.role == "edge2")
    commands = []
    monkeypatch.setattr(
        physical_cluster,
        "_run",
        lambda command: commands.append(command),
    )

    physical_cluster._safe_remote_stop(inventory, node)

    remote = commands[0][-1]
    assert "pgrep -f" in remote
    assert "continuum_bench" in remote
    assert "--node-id edge2" in remote
    assert "--port 8391" in remote
    assert 'for pid in $pids; do kill "$pid"' in remote
    assert 'while kill -0 "$pid"' in remote


def test_start_replaces_workers_with_a_stale_topology(config, monkeypatch):
    inventory = load_physical_inventory(
        config.resolve(config.topology_file)
    )
    status_calls = 0
    stopped = []
    started = []

    def status(current_inventory, print_output=False):
        nonlocal status_calls
        status_calls += 1
        healthy = status_calls > 1
        return [
            {"role": node.role, "healthy": healthy}
            for node in current_inventory.nodes
        ]

    monkeypatch.setattr(physical_cluster, "_verify_key_auth", lambda value: None)
    monkeypatch.setattr(physical_cluster, "status_cluster", status)
    monkeypatch.setattr(
        physical_cluster,
        "_safe_local_stop",
        lambda root, role: stopped.append(role),
    )
    monkeypatch.setattr(
        physical_cluster,
        "_safe_remote_stop",
        lambda current_inventory, node: stopped.append(node.role),
    )
    monkeypatch.setattr(
        physical_cluster,
        "_local_start",
        lambda root, current_inventory, node: started.append(node.role),
    )
    monkeypatch.setattr(
        physical_cluster,
        "_remote_start",
        lambda current_inventory, node: started.append(node.role),
    )

    physical_cluster.start_cluster(config.root, inventory, wait_seconds=0.1)

    assert stopped == [node.role for node in inventory.nodes]
    assert started == [node.role for node in inventory.nodes]


def test_deploy_checks_all_remotes_before_copying(config, monkeypatch):
    inventory = load_physical_inventory(config.resolve(config.topology_file))
    monkeypatch.setattr(physical_cluster, "_verify_key_auth", lambda inventory: None)
    monkeypatch.setattr(physical_cluster, "physical_checks", lambda: [])
    calls = []
    def probe(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 1, "", "No module named venv")
    monkeypatch.setattr(physical_cluster.subprocess, "run", probe)
    monkeypatch.setattr(physical_cluster, "_run", lambda command: pytest.fail("Must not copy before checking all hosts"))
    with pytest.raises(RuntimeError, match="before copying any files"):
        physical_cluster.deploy_cluster(config.root, inventory)
    assert len(calls) == 4


@pytest.mark.parametrize("directory", ["/", "/home/pi", "/home/pi/", "/home/pi/../other", "/tmp", "/var/tmp/"])
def test_inventory_rejects_broad_deployment_targets(config, tmp_path, directory):
    path = _legacy_inventory(tmp_path, directory)
    with pytest.raises(ValueError, match="dedicated remote_dir"):
        load_physical_inventory(path)
