"""Physical monitoring suite orchestration.

This module is the public boundary for current monitoring work. It delegates
to the lower-level replicated and authority-sharded coordinators, while keeping
the rest of the project focused on physical infrastructure.
"""

from __future__ import annotations

from pathlib import Path

from ..config import BenchmarkConfig
from ..physical import run_physical_cumulative, run_physical_scalability
from ..physical_cluster import PhysicalInventory
from ..sharded import (
    export_fragments,
    run_sharded_cumulative,
    run_sharded_scalability,
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
    if layout not in {"replicated", "sharded"}:
        raise ValueError("layout must be replicated or sharded")
    outputs: dict[str, str] = {}
    suite_root = output_root / layout
    if layout == "sharded":
        endpoints = [node.endpoint for node in inventory.nodes]
        options = {
            "target": "physical",
            "validate_results": validate_results,
        }
        if inventory.topology is not None:
            options["topology"] = inventory.topology
        if suite in {"cumulative", "all"}:
            outputs["cumulative"] = str(
                run_sharded_cumulative(config, endpoints, suite_root, **options)
            )
        if suite in {"scalability", "all"}:
            outputs["scalability"] = str(
                run_sharded_scalability(config, endpoints, suite_root, **options)
            )
        return outputs

    inventory_path = inventory.path
    options = (
        {}
        if inventory.topology_name == "physical"
        else {"topology_name": inventory.topology_name}
    )
    if suite in {"cumulative", "all"}:
        outputs["cumulative"] = str(
            run_physical_cumulative(config, inventory_path, suite_root, **options)
        )
    if suite in {"scalability", "all"}:
        outputs["scalability"] = str(
            run_physical_scalability(config, inventory_path, suite_root, **options)
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
