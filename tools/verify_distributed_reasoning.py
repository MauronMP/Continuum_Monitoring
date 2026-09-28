#!/usr/bin/env python3
"""Verify distributed answers offline without making performance claims."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from continuum_bench.config import load_config  # noqa: E402
from continuum_bench.monitoring.distributed import Endpoint  # noqa: E402
from continuum_bench.monitoring.distributed_ontology import (  # noqa: E402
    _assignment,
    _baseline_counts,
    _merge_responses,
    _validation_rows,
)
from continuum_bench.partitioning import (  # noqa: E402
    build_fragments,
    deserialize_fragment,
    serialize_fragment,
)
from continuum_bench.queries import (  # noqa: E402
    execute_query_detailed,
    load_catalog,
)
from continuum_bench.reasoners import materialize  # noqa: E402
from continuum_bench.topology import load_topology  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmark-config",
        "--config",
        dest="benchmark_config",
        type=Path,
        default=Path("configs/smoke-scalability.toml"),
        help=(
            "Monitoring benchmark configuration containing paths, topology and "
            "reasoners; --config remains as a compatibility alias"
        ),
    )
    parser.add_argument("--users", type=int, default=1)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/validation/readiness/distributed-reasoning.json"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.users < 1:
        raise SystemExit("--users must be a positive integer")
    try:
        config = load_config(args.benchmark_config)
    except (KeyError, OSError, ValueError) as error:
        raise SystemExit(
            f"Invalid monitoring benchmark configuration "
            f"{args.benchmark_config}: {error}"
        ) from error

    topology = load_topology(config.resolve(config.topology_file), "physical")
    endpoints = [
        Endpoint(
            node.endpoint,
            node.node_id,
            tier=node.tier,
            authority=node.authority,
            categories=node.categories,
        )
        for node in topology.active_nodes
    ]
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    assignment = _assignment(specs, endpoints)
    fragments = build_fragments(
        config,
        args.users,
        config.seed,
        topology=topology,
    )
    report = {
        "mode": "offline-semantic-check",
        "remote_contacted": False,
        "benchmark_config": str(args.benchmark_config.resolve()),
        "topology_fingerprint": topology.fingerprint,
        "node_count": len(endpoints),
        "users": args.users,
        "reasoners": [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)

    for reasoner in config.reasoners:
        print(
            f"[offline] {reasoner} canonical and {len(endpoints)} local fragments",
            flush=True,
        )
        baseline = _baseline_counts(config, specs, reasoner, args.users)
        responses = {}
        for endpoint in endpoints:
            payload = serialize_fragment(
                fragments,
                endpoint.role,
                users=args.users,
                seed=config.seed,
            )
            source, _ = deserialize_fragment(
                payload,
                endpoint.role,
                users=args.users,
                seed=config.seed,
            )
            graph = materialize(source, reasoner).graph
            measurements = []
            for spec in assignment[endpoint.url]:
                execution = execute_query_detailed(graph, spec)
                measurements.append(
                    {
                        **asdict(execution.measurement),
                        "result_keys": execution.result_keys,
                    }
                )
            responses[endpoint.url] = {"measurements": measurements}
        merged, _ = _merge_responses(
            specs,
            endpoints,
            responses,
            {"reasoner": reasoner},
        )
        validation = _validation_rows(merged, baseline)
        invalid = [row for row in validation if not row["valid"]]
        report["reasoners"].append(
            {
                "reasoner": reasoner,
                "checks": len(validation),
                "mismatch_count": len(invalid),
                "mismatches": invalid,
            }
        )
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(
            f"[offline] {reasoner} checks={len(validation)} "
            f"mismatches={len(invalid)}",
            flush=True,
        )
    return int(any(row["mismatches"] for row in report["reasoners"]))


if __name__ == "__main__":
    raise SystemExit(main())
