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
    monitor_parser = commands.add_parser("monitor")
    monitor_parser.add_argument("--config", dest="monitor_config", type=Path, default=Path("configs/monitoring.toml"))
    monitor_parser.add_argument("--demand-level", action="append")
    monitor_report_parser = commands.add_parser("monitor-report")
    monitor_report_parser.add_argument("run_dir", type=Path)
    adaptation_parser = commands.add_parser("adaptation")
    adaptation_stages = adaptation_parser.add_subparsers(dest="adaptation_stage", required=True)
    for stage in ("observe", "analyze", "plan", "execute", "verify"):
        stage_parser = adaptation_stages.add_parser(stage)
        stage_parser.add_argument(
            "--config", dest="adaptation_config", type=Path, default=Path("configs/adaptation.toml")
        )
        if stage != "observe":
            stage_parser.add_argument("run_dir", type=Path)
    adaptation_report = adaptation_stages.add_parser("report")
    adaptation_report.add_argument("run_dir", type=Path)
    report_parser = commands.add_parser("report")
    report_parser.add_argument("run_dir", type=Path)
    return root


def main() -> int:
    args = parser().parse_args()
    if args.command == "monitor":
        from .continuous_monitoring.config import load_monitoring_config
        from .continuous_monitoring.experiment import run as run_monitoring

        monitoring = load_monitoring_config(args.monitor_config)
        topology = load_topology(
            monitoring.benchmark.root / monitoring.benchmark.deployment["topology_file"], set(args.exclude_host)
        )
        result = {"results": str(run_monitoring(monitoring, topology, set(args.demand_level or [])))}
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "monitor-report":
        from .continuous_monitoring.reporting import report as report_monitoring

        result = {"summary": str(report_monitoring(args.run_dir.resolve()))}
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "adaptation":
        from .adaptation.config import load_adaptation_config
        from .adaptation.experiment import analyze, execute, observe, plan, verify
        from .adaptation.reporting import report as report_adaptation

        if args.adaptation_stage == "report":
            result = {"comparison": str(report_adaptation(args.run_dir.resolve()))}
        else:
            adaptation = load_adaptation_config(args.adaptation_config)
            topology = load_topology(
                adaptation.benchmark.root / adaptation.benchmark.deployment["topology_file"],
                set(args.exclude_host),
            )
            if args.adaptation_stage == "observe":
                result = {"results": str(observe(adaptation, topology))}
            else:
                run_dir = args.run_dir.resolve()
                if args.adaptation_stage == "analyze":
                    result = analyze(adaptation, run_dir)
                elif args.adaptation_stage == "plan":
                    result = plan(adaptation, topology, run_dir)
                elif args.adaptation_stage == "execute":
                    result = execute(adaptation, topology, run_dir)
                else:
                    result = verify(adaptation, topology, run_dir)
        print(json.dumps(result, indent=2))
        return 0
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
