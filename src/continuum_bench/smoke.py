"""Bounded acceptance smokes for monitoring, load and experiment suites."""

from __future__ import annotations

import csv
from pathlib import Path
import sys
from typing import Callable

from .cli import main


def _project_root() -> Path:
    working_tree = Path.cwd()
    if (working_tree / "configs").is_dir():
        return working_tree
    editable_tree = Path(__file__).resolve().parents[2]
    if (editable_tree / "configs").is_dir():
        return editable_tree
    raise FileNotFoundError(
        "Run the smoke command from the project root containing configs/"
    )


def _option(arguments: list[str], name: str, default: str) -> str:
    value = default
    for index, argument in enumerate(arguments[:-1]):
        if argument == name:
            value = arguments[index + 1]
    return value


def _require_completed_summaries(paths: list[Path]) -> int:
    """Make a smoke fail when a bounded run is censored or incomplete."""

    failures: list[str] = []
    for path in paths:
        if not path.is_file():
            failures.append(f"missing summary: {path}")
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            failures.append(f"empty summary: {path}")
            continue
        if "status" not in rows[0]:
            failures.append(f"summary has no status contract: {path}")
            continue
        incomplete = [
            row for row in rows if row.get("status") != "completed"
        ]
        if incomplete:
            statuses: dict[str, int] = {}
            for row in incomplete:
                status = row.get("status") or "missing"
                statuses[status] = statuses.get(status, 0) + 1
            failures.append(
                f"{path}: "
                + ", ".join(
                    f"{status}={count}"
                    for status, count in sorted(statuses.items())
                )
            )
        reference_failures = [
            row for row in rows
            if row.get("reference_status")
            and row.get("reference_status") != "completed"
        ]
        if reference_failures:
            failures.append(
                f"{path}: reference_validation_incomplete="
                f"{len(reference_failures)}"
            )
        invalid_rates = [
            row for row in rows
            if row.get("result_validation_rate") not in {None, ""}
            and float(row["result_validation_rate"]) != 1.0
        ]
        if invalid_rates:
            failures.append(
                f"{path}: invalid_result_rates={len(invalid_rates)}"
            )
        lost_events = sum(
            int(float(row["events_lost"]))
            for row in rows
            if row.get("events_lost") not in {None, ""}
        )
        if lost_events:
            failures.append(f"{path}: events_lost={lost_events}")
    if failures:
        print("[smoke] acceptance=failed", file=sys.stderr)
        for failure in failures:
            print(f"[smoke] {failure}", file=sys.stderr)
        return 1
    print(
        f"[smoke] acceptance=passed summaries={len(paths)}",
        flush=True,
    )
    return 0


def _run_monitoring(target: str, suite: str) -> int:
    root = _project_root()
    arguments = list(sys.argv[1:])
    layout = _option(arguments, "--layout", "sharded")
    default_output = f"outputs/smoke/{target}-monitoring"
    output = _option(arguments, "--output-dir", default_output)
    status = main(
        [
            "--config",
            str(root / f"configs/smoke-{suite}.toml"),
            target,
            suite,
            "--output-dir",
            default_output,
            *arguments,
        ]
    )
    if status:
        return status
    output_root = Path(output)
    if not output_root.is_absolute():
        output_root = root / output_root
    return _require_completed_summaries(
        [output_root / layout / suite / "summary.csv"]
    )


def _run_local_monitoring(suite: str) -> int:
    root = _project_root()
    arguments = list(sys.argv[1:])
    default_output = "outputs/smoke/local-monitoring"
    output = _option(arguments, "--output-dir", default_output)
    status = main(
        [
            "--config",
            str(root / f"configs/smoke-{suite}.toml"),
            "local",
            suite,
            "--output-dir",
            default_output,
            *arguments,
        ]
    )
    if status:
        return status
    output_root = Path(output)
    if not output_root.is_absolute():
        output_root = root / output_root
    return _require_completed_summaries(
        [output_root / suite / "summary.csv"]
    )


def _with_docker_workers(operation: Callable[[], int]) -> int:
    """Run one smoke against Docker without stopping a pre-existing stack."""

    from .config import load_config
    from .distributed import discover
    from .docker_cluster import manage, wait_ready
    from .topology import load_topology

    root = _project_root()
    config = load_config(root / "configs/smoke-cumulative.toml")
    topology = load_topology(
        root / "configs/topologies/docker/topology.toml", "docker"
    )
    owned = False
    try:
        try:
            discover(
                topology.endpoints(),
                topology.active_nodes,
                topology.fingerprint,
            )
        except (OSError, RuntimeError, ValueError):
            if manage(config.root, topology, "up") != 0:
                raise RuntimeError("Docker Compose could not start smoke workers")
            owned = True
            wait_ready(topology, timeout_seconds=60)
        return operation()
    finally:
        if owned:
            manage(config.root, topology, "down")


def _run_load(target: str) -> int:
    root = _project_root()
    arguments = list(sys.argv[1:])
    default_output = "outputs/smoke/load"
    output = _option(arguments, "--output-dir", default_output)

    def operation() -> int:
        status = main(
            [
                "--config",
                str(root / "configs/smoke-cumulative.toml"),
                "load",
                target,
                "--load-config",
                "configs/load-smoke.toml",
                "--output-dir",
                default_output,
                *arguments,
            ]
        )
        if status:
            return status
        output_root = Path(output)
        if not output_root.is_absolute():
            output_root = root / output_root
        return _require_completed_summaries(
            [output_root / target / "summary.csv"]
        )

    return _with_docker_workers(operation) if target == "docker" else operation()


def _run_experiments(target: str) -> int:
    root = _project_root()
    arguments = list(sys.argv[1:])
    default_output = "outputs/smoke/experiments"
    output = _option(arguments, "--output-dir", default_output)

    def operation() -> int:
        status = main(
            [
                "--config",
                str(root / "configs/smoke-cumulative.toml"),
                "experiment",
                "all",
                target,
                "--experiment-config",
                "configs/experiments-smoke.toml",
                "--output-dir",
                default_output,
                *arguments,
            ]
        )
        if status:
            return status
        output_root = Path(output)
        if not output_root.is_absolute():
            output_root = root / output_root
        return _require_completed_summaries(
            [
                output_root / target / name / "summary.csv"
                for name in (
                    "scale-out",
                    "reasoning-hardware",
                    "distributed-ontology",
                )
            ]
        )

    return _with_docker_workers(operation) if target == "docker" else operation()


def main_cumulative() -> int:
    return _run_monitoring("physical", "cumulative")


def main_scalability() -> int:
    return _run_monitoring("physical", "scalability")


def main_docker_cumulative() -> int:
    return _run_monitoring("docker", "cumulative")


def main_docker_scalability() -> int:
    return _run_monitoring("docker", "scalability")


def main_local_cumulative() -> int:
    return _run_local_monitoring("cumulative")


def main_local_scalability() -> int:
    return _run_local_monitoring("scalability")


def main_physical_load() -> int:
    return _run_load("physical")


def main_docker_load() -> int:
    return _run_load("docker")


def main_local_load() -> int:
    return _run_load("local")


def main_physical_experiments() -> int:
    return _run_experiments("physical")


def main_docker_experiments() -> int:
    return _run_experiments("docker")


def main_local_experiments() -> int:
    return _run_experiments("local")


def main_engines() -> int:
    root = _project_root()
    arguments = list(sys.argv[1:])
    default_output = "outputs/smoke/engines"
    output = _option(arguments, "--output-dir", default_output)
    status = main(
        [
            "--config",
            str(root / "configs/smoke-scalability.toml"),
            "engines",
            "all",
            "--warmups",
            "0",
            "--output-dir",
            default_output,
            *arguments,
        ]
    )
    if status:
        return status
    output_root = Path(output)
    if not output_root.is_absolute():
        output_root = root / output_root
    return _require_completed_summaries(
        [
            output_root / "cumulative" / "summary.csv",
            output_root / "scalability" / "summary.csv",
        ]
    )
