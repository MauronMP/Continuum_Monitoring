"""Physical monitoring suite orchestration.

This module is the public boundary for current monitoring work. It delegates
to the lower-level replicated and authority-distributed coordinators, while keeping
the rest of the project focused on physical infrastructure.
"""

from __future__ import annotations

import csv
from pathlib import Path

from ..config import BenchmarkConfig
from .physical import run_physical_cumulative, run_physical_scalability
from ..physical_cluster import PhysicalInventory
from .distributed_ontology import (
    export_fragments,
    run_distributed_cumulative,
    run_distributed_scalability,
)


def run_physical_monitoring_suite(
    config: BenchmarkConfig,
    inventory: PhysicalInventory,
    output_root: Path,
    *,
    suite: str,
    layout: str,
    validate_results: bool = True,
) -> dict[str, str]:
    """Run cumulative, scalability or both monitoring suites on real nodes."""

    if suite not in {"cumulative", "scalability", "all"}:
        raise ValueError("suite must be cumulative, scalability or all")
    if layout not in {"replicated", "distributed"}:
        raise ValueError("layout must be replicated or distributed")
    outputs: dict[str, str] = {}
    suite_root = output_root / layout
    selected = (
        ("cumulative", "scalability") if suite == "all" else (suite,)
    )
    completed_families = 0
    hard_failures: list[str] = []

    def inspect(name: str, directory: str) -> None:
        path = Path(directory) / "summary.csv"
        if not path.is_file():
            hard_failures.append(f"{name}: missing summary.csv")
            return
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        counts: dict[str, int] = {}
        for row in rows:
            status = row.get("status", "unknown")
            if status in {"failed", "invalid_results", "unvalidated_results"}:
                counts[status] = counts.get(status, 0) + 1
        if counts:
            hard_failures.append(
                f"{name}: "
                + ", ".join(
                    f"{status}={count}" for status, count in sorted(counts.items())
                )
            )

    def announce(name: str, status: str) -> None:
        nonlocal completed_families
        if status == "completed":
            completed_families += 1
            position = completed_families
        else:
            position = completed_families + 1
        percent = 100 * completed_families / len(selected)
        print(
            "[physical-suite-progress] "
            f"layout={layout} family={name} family_index={position}/{len(selected)} "
            f"percent={percent:.1f} status={status}",
            flush=True,
        )
    if layout == "distributed":
        endpoints = [node.endpoint for node in inventory.nodes]
        options = {
            "target": "physical",
            "validate_results": validate_results,
        }
        if inventory.topology is not None:
            options["topology"] = inventory.topology
        if suite in {"cumulative", "all"}:
            announce("cumulative", "running")
            outputs["cumulative"] = str(
                run_distributed_cumulative(config, endpoints, suite_root, **options)
            )
            inspect("cumulative", outputs["cumulative"])
            announce("cumulative", "completed")
        if suite in {"scalability", "all"}:
            announce("scalability", "running")
            outputs["scalability"] = str(
                run_distributed_scalability(config, endpoints, suite_root, **options)
            )
            inspect("scalability", outputs["scalability"])
            announce("scalability", "completed")
        if hard_failures:
            raise RuntimeError(
                "Physical monitoring completed all selected families with "
                "invalid evidence: " + "; ".join(hard_failures)
            )
        return outputs

    inventory_path = inventory.path
    options = (
        {}
        if inventory.topology_name == "physical"
        else {"topology_name": inventory.topology_name}
    )
    if suite in {"cumulative", "all"}:
        announce("cumulative", "running")
        outputs["cumulative"] = str(
            run_physical_cumulative(config, inventory_path, suite_root, **options)
        )
        inspect("cumulative", outputs["cumulative"])
        announce("cumulative", "completed")
    if suite in {"scalability", "all"}:
        announce("scalability", "running")
        outputs["scalability"] = str(
            run_physical_scalability(config, inventory_path, suite_root, **options)
        )
        inspect("scalability", outputs["scalability"])
        announce("scalability", "completed")
    if hard_failures:
        raise RuntimeError(
            "Physical monitoring completed all selected families with invalid "
            "evidence: " + "; ".join(hard_failures)
        )
    return outputs


def export_physical_fragments(
    config: BenchmarkConfig,
    inventory: PhysicalInventory,
    users: int,
    output_dir: Path,
) -> list[Path]:
    """Export the authority-aware RDF fragments for a physical topology."""

    if inventory.topology is None:
        raise ValueError("Fragment export requires an elastic topology manifest")
    return export_fragments(
        config,
        users,
        output_dir,
        topology=inventory.topology,
    )
