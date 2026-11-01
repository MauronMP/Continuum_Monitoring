from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .deployment import deploy, doctor, render
from .experiment import run
from .protocol import request_json
from .reporting import report
from .topology import load_topology


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="continuum-bench", description="Docker RDF Scalability Benchmark")
    root.add_argument("--config", type=Path, default=Path("configs/benchmark.toml"))
    root.add_argument("--exclude-host", action="append", default=[])
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    render_parser = commands.add_parser("render")
    render_parser.add_argument("--output", type=Path, default=Path(".runtime/deployment"))
    deploy_parser = commands.add_parser("deploy")
    deploy_parser.add_argument("--no-build", action="store_true")
    commands.add_parser("status")
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--scenario", action="append")
    run_parser.add_argument(
        "--diagnostic-unlimited",
        action="store_true",
        help="remove the preparation deadline and mark the run non-comparable",
    )
    report_parser = commands.add_parser("report")
    report_parser.add_argument("run_dir", type=Path)
    return root


def main() -> int:
    args = parser().parse_args()
    config = load_config(args.config)
    topology = load_topology(config.root / config.deployment["topology_file"], set(args.exclude_host))
    if args.command == "doctor":
        result = doctor(config, topology)
    elif args.command == "render":
        result = {"output": str(render(config, topology, args.output))}
    elif args.command == "deploy":
        result = deploy(config, topology, build=not args.no_build)
    elif args.command == "status":
        result = []
        for host in topology.hosts:
            try:
                result.append({"host": host.id, "health": request_json(f"{host.endpoint}/health", timeout=5)})
            except Exception as error:
                result.append({"host": host.id, "error": str(error)})
    elif args.command == "run":
        result = {
            "results": str(
                run(
                    config,
                    topology,
                    scenario_names=set(args.scenario or []),
                    diagnostic_unlimited=args.diagnostic_unlimited,
                )
            )
        }
    else:
        result = {"summary": str(report(args.run_dir.resolve()))}
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
