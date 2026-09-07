"""Infrastructure-neutral distributed monitoring suite orchestration."""

from __future__ import annotations

from pathlib import Path

from ..config import BenchmarkConfig
from ..physical import run_physical_cumulative, run_physical_scalability
from ..sharded import run_sharded_cumulative, run_sharded_scalability
from ..topology import Topology


def run_distributed_monitoring_suite(
    config: BenchmarkConfig,
    topology: Topology,
    output_root: Path,
    *,
    suite: str,
    layout: str,
    validate_results: bool = True,
) -> dict[str, str]:
    if suite not in {"cumulative", "scalability", "all"}:
        raise ValueError("suite must be cumulative, scalability or all")
    if layout not in {"replicated", "sharded"}:
        raise ValueError("layout must be replicated or sharded")
    endpoints = topology.endpoints()
    output = output_root / layout
    if layout == "sharded":
        runners = (run_sharded_cumulative, run_sharded_scalability)
        options = {
            "target": topology.kind,
            "topology": topology,
            "validate_results": validate_results,
        }
    else:
        runners = (run_physical_cumulative, run_physical_scalability)
        options = {}

    def invoke(runner):
        if layout == "sharded":
            return runner(config, endpoints, output, **options)
        return runner(config, topology, output)
    results: dict[str, str] = {}
    if suite in {"cumulative", "all"}:
        results["cumulative"] = str(
            invoke(runners[0])
        )
    if suite in {"scalability", "all"}:
        results["scalability"] = str(
            invoke(runners[1])
        )
    return results
