from continuum_bench import physical_cluster
from continuum_bench.physical_cluster import load_physical_inventory


def test_status_rejects_wrong_worker_contract(config, monkeypatch):
    inventory = load_physical_inventory(
        config.root / "configs" / "physical-nodes.toml"
    )
    monkeypatch.setattr(
        physical_cluster,
        "_request",
        lambda *args, **kwargs: {
            "status": "ok",
            "protocol_version": "4",
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


def test_authorize_installs_key_on_each_remote_node(config, monkeypatch):
    inventory = load_physical_inventory(
        config.root / "configs" / "physical-nodes.toml"
    )
    commands = []
    monkeypatch.setattr(
        physical_cluster,
        "_run",
        lambda command: commands.append(command),
    )

    physical_cluster.authorize_cluster(inventory)

    assert commands == [
        ["ssh-copy-id", "pi@192.168.1.137"],
        ["ssh-copy-id", "pi@192.168.1.138"],
        ["ssh-copy-id", "pi@192.168.1.139"],
        ["ssh-copy-id", "pi@192.168.1.140"],
    ]


def test_ssh_lifecycle_commands_disable_password_prompts():
    command = physical_cluster._ssh(
        "pi@192.168.1.137",
        "true",
    )

    assert command[:3] == ["ssh", "-o", "BatchMode=yes"]


def test_remote_start_records_python_pid_not_background_shell(
    config,
    monkeypatch,
):
    inventory = load_physical_inventory(
        config.root / "configs" / "physical-nodes.toml"
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


def test_remote_stop_recovers_from_a_stale_pid_file(config, monkeypatch):
    inventory = load_physical_inventory(
        config.root / "configs" / "physical-nodes.toml"
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
    assert "--role edge2" in remote
    assert "--port 8391" in remote
    assert 'for pid in $pids; do kill "$pid"; done' in remote
