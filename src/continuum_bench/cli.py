from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
import webbrowser

from .config import load_config
from .validation import validate_project


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="continuum-bench",
        description=(
            "Validate and benchmark the policy-aware monitoring ontology on "
            "physical continuum infrastructure."
        ),
    )
    parser.add_argument(
        "--config",
        default="configs/benchmark.toml",
        help="Benchmark TOML file (default: configs/benchmark.toml)",
    )
    parser.add_argument(
        "--topology-file",
        help="Physical topology manifest override",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    campaign = subparsers.add_parser("campaign", help="Run configurable physical scalability and policy-cost axes")
    campaign.add_argument("--campaign-config", default="configs/campaign-smoke.toml")
    campaign.add_argument("--output-dir", default="outputs/campaigns")
    campaign.add_argument("--axis", action="append")
    campaign.add_argument("--topology-name", default="physical")
    campaign.add_argument("--validate-only", action="store_true")

    doctor = subparsers.add_parser(
        "doctor",
        help="Read-only installation and SSH diagnostics",
    )
    doctor.add_argument("--physical", action="store_true")
    doctor.add_argument("--owl", action="store_true")
    doctor.add_argument("--json", action="store_true")

    subparsers.add_parser(
        "validate",
        help="Run syntax, ontology, policy and query checks",
    )

    preflight = subparsers.add_parser(
        "preflight",
        help="Validate load/experiment sizes before contacting workers",
    )
    preflight.add_argument(
        "--load-config", default="configs/load-benchmark.toml"
    )
    preflight.add_argument(
        "--experiment-config", default="configs/experiments.toml"
    )

    owl_validate = subparsers.add_parser(
        "owl-validate",
        help="Validate OWL consistency with external DL reasoners",
    )
    owl_validate.add_argument(
        "--reasoner-config", default="configs/owl-reasoners.toml"
    )

    engines = subparsers.add_parser(
        "engines",
        help="Run all RDFLib, Jena, RDF4J and Oxigraph engine benchmarks",
    )
    engines.add_argument(
        "suite", choices=("cumulative", "scalability", "all", "plot")
    )
    engines.add_argument(
        "--plot-suite",
        choices=("cumulative", "scalability", "all"),
        default="all",
        help="Suite selected when the engines action is plot",
    )
    engines.add_argument(
        "--endpoints",
        help=(
            "Comma-separated native engine URLs; defaults to the four "
            "local native service ports"
        ),
    )
    engines.add_argument("--warmups", type=int, default=1)
    engines.add_argument("--output-dir", default="outputs/engines")
    engines.add_argument("--keep-running", action="store_true")
    owl_validate.add_argument(
        "--output", default="outputs/validation/owl-reasoners.json"
    )
    owl_validate.add_argument(
        "--require-all",
        action="store_true",
        help="Fail when any configured reasoner is unavailable or inconsistent",
    )

    topology = subparsers.add_parser(
        "topology",
        help="Validate or inspect a topology manifest",
    )
    topology.add_argument("action", choices=("validate", "show"))
    topology.add_argument("--name", default="physical")



    fragments = subparsers.add_parser(
        "fragments",
        help="Export authority-aware RDF fragments for physical nodes",
    )
    fragments.add_argument("--users", type=int, default=0)
    fragments.add_argument("--topology-name", default="physical")
    fragments.add_argument("--output-dir", default="outputs/fragments/physical")
    fragments.add_argument("--ssh-user")

    physical = subparsers.add_parser(
        "physical",
        help="Deploy, manage or benchmark a physical continuum",
    )
    physical.add_argument(
        "action",
        choices=(
            "authorize",
            "deploy",
            "start",
            "status",
            "stop",
            "cumulative",
            "scalability",
            "all",
        ),
    )
    physical.add_argument("--topology-name", default="physical")
    physical.add_argument("--ssh-user")
    physical.add_argument("--output-dir", default="outputs/physical")
    physical.add_argument(
        "--layout",
        choices=("replicated", "sharded"),
        default="sharded",
        help="Physical placement strategy (default: sharded)",
    )
    physical.add_argument(
        "--skip-result-validation",
        action="store_true",
        help="Skip bounded reference validation for sharded query results",
    )

    load = subparsers.add_parser(
        "load",
        help="Run or plot the distributed load benchmark",
    )
    load.add_argument(
        "target", choices=("physical", "plot")
    )
    load.add_argument(
        "--load-config",
        default="configs/load-benchmark.toml",
        help="Load profile TOML (default: configs/load-benchmark.toml)",
    )
    load.add_argument("--topology-name")
    load.add_argument(
        "--dimension",
        action="append",
        choices=(
            "events_per_second",
            "users",
            "target_triples",
            "rule_count",
            "node_count",
        ),
    )
    load.add_argument("--profile", action="append")
    load.add_argument("--output-dir", default="outputs/load")
    load.add_argument("--show", action="store_true")

    experiment = subparsers.add_parser(
        "experiment",
        help=(
            "Run physical scale-out, hardware reasoning or "
            "distributed-ontology experiments"
        ),
    )
    experiment_commands = experiment.add_subparsers(
        dest="experiment_name",
        required=True,
    )

    def add_experiment_arguments(command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument(
            "target",
            choices=("physical",),
            nargs="?",
            default="physical",
        )
        command_parser.add_argument(
            "--experiment-config",
            default="configs/experiments.toml",
        )
        command_parser.add_argument("--topology-name")
        command_parser.add_argument("--output-dir", default="outputs/experiments")
        command_parser.add_argument(
            "--reasoner",
            action="append",
            choices=("rdfs", "owlrl", "rdfs_owlrl"),
        )
        command_parser.add_argument("--profile", action="append")

    for name in (
        "scale-out",
        "reasoning-hardware",
        "distributed-ontology",
        "all",
    ):
        add_experiment_arguments(experiment_commands.add_parser(name))

    experiment_plot = experiment_commands.add_parser("plot")
    experiment_plot.add_argument(
        "suite",
        choices=(
            "scale-out",
            "reasoning-hardware",
            "distributed-ontology",
            "all",
        ),
    )
    experiment_plot.add_argument("--output-dir", default="outputs/experiments")
    experiment_plot.add_argument("--show", action="store_true")

    experiment_analyze = experiment_commands.add_parser("analyze")
    experiment_analyze.add_argument("--output-dir", default="outputs/experiments")
    experiment_analyze.add_argument("--show", action="store_true")

    study = subparsers.add_parser(
        "study",
        help="Generate reproducible traces and policy-category cost summaries",
    )
    study.add_argument("action", choices=("trace", "category-cost"))
    study.add_argument(
        "--study-config",
        default="configs/policy-cost-study.toml",
        help="Policy-cost study TOML file",
    )
    study.add_argument(
        "--topology-name",
        help="Topology name (defaults to the selected target)",
    )
    study.add_argument(
        "--target",
        choices=("physical",),
        default="physical",
        help="Execution topology used to generate the trace",
    )
    study.add_argument("--output-dir", default="outputs/study")
    study.add_argument(
        "--events",
        default="outputs/load/physical/event-runs.csv",
        help="Request/event CSV used by category-cost analysis",
    )
    return parser


def _manifest_path(config, override: str | None) -> Path:
    path = Path(override) if override else config.topology_file
    return path if path.is_absolute() else config.root / path


def _target_manifest_path(config, override: str | None, target: str) -> Path:
    if override:
        return _manifest_path(config, override)
    if target in {"physical"}:
        return config.root / f"configs/topologies/{target}/topology.toml"
    return _manifest_path(config, None)


def _target_topology(config, args, target: str):
    from .topology import load_topology

    name = getattr(args, "topology_name", None) or target
    return load_topology(
        _target_manifest_path(config, args.topology_file, target), name
    )


def _physical_inventory(config, args):
    from .physical_cluster import load_physical_inventory

    return load_physical_inventory(
        _manifest_path(config, args.topology_file),
        ssh_user=getattr(args, "ssh_user", None),
        topology_name=getattr(args, "topology_name", "physical"),
    )


def _open_paths(paths: list[Path]) -> None:
    for path in paths:
        if path.suffix == ".png":
            webbrowser.open(path.resolve().as_uri())


def _dispatch(args) -> int:
    if args.command == "doctor":
        from .environment import main as doctor_main

        config_path = Path(args.config).resolve()
        options = ["--root", str(config_path.parents[1])]
        if args.physical:
            options.append("--physical")
        if args.owl:
            options.append("--owl")
        if args.json:
            options.append("--json")
        return doctor_main(options)

    config = load_config(args.config)

    if args.command == "campaign":
        from .monitoring.campaign_config import load_campaign
        from .monitoring.campaign import run_campaign
        from .monitoring.campaign_infrastructure import PhysicalInfrastructure
        campaign = load_campaign(config.resolve(Path(args.campaign_config)))
        if args.axis:
            missing = set(args.axis) - {axis.name for axis in campaign.axes}
            if missing:
                raise ValueError(f"Unknown campaign axes: {sorted(missing)}")
            campaign = replace(campaign, axes=tuple(a for a in campaign.axes if a.name in args.axis))
        topology = _target_topology(config, args, "physical")
        if max(w.physical_nodes for _, _, w in campaign.points()) > len(topology.active_nodes):
            raise ValueError("Campaign requests more physical nodes than configured")
        if args.validate_only:
            print(json.dumps(campaign.public(), indent=2))
            return 0
        directory, failures = run_campaign(campaign, PhysicalInfrastructure(topology), config.resolve(Path(args.output_dir)))
        print(json.dumps({"output": str(directory), "failed_points": failures}, indent=2))
        return 1 if failures else 0

    if args.command == "validate":
        report = validate_project(config)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["ok"] else 1

    if args.command == "preflight":
        from .preflight import validate_default_workloads

        load_path = config.root / args.load_config
        experiment_path = config.root / args.experiment_config
        report = validate_default_workloads(config, load_path, experiment_path)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    if args.command == "owl-validate":
        from .owl_validation import validate_external_reasoners

        reasoner_config = Path(args.reasoner_config)
        if not reasoner_config.is_absolute():
            reasoner_config = config.root / reasoner_config
        output = Path(args.output)
        if not output.is_absolute():
            output = config.root / output
        report = validate_external_reasoners(
            config.root, reasoner_config, output
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        completed = [
            item for item in report["reasoners"]
            if item["status"] == "completed"
        ]
        success = bool(completed) and all(
            item.get("consistent") is True for item in completed
        )
        if args.require_all:
            success = success and report["all_available"] and report["all_consistent"]
        return 0 if success else 1

    if args.command == "engines":
        from contextlib import nullcontext

        if args.suite == "plot":
            from .engine_reporting import plot_engine_benchmarks

            output_root = Path(args.output_dir)
            if not output_root.is_absolute():
                output_root = config.root / output_root
            selected = (
                ("cumulative", "scalability")
                if args.plot_suite == "all"
                else (args.plot_suite,)
            )
            paths = plot_engine_benchmarks(output_root, selected)
            print(
                json.dumps(
                    {"engine_plots": [str(path) for path in paths]},
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0

        from .engine_stack import semantic_engine_stack
        from .engines import (
            run_engine_cumulative,
            run_engine_scalability,
            validate_rdfs_equivalence,
        )

        if args.warmups < 0:
            raise ValueError("--warmups must be zero or greater")
        output_root = Path(args.output_dir)
        if not output_root.is_absolute():
            output_root = config.root / output_root
        if args.endpoints:
            urls = tuple(
                value.strip()
                for value in args.endpoints.split(",")
                if value.strip()
            )
            context = nullcontext(urls)
        else:
            context = semantic_engine_stack(
                config.root, keep_running=args.keep_running
            )
        outputs: dict[str, str] = {}
        with context as endpoint_urls:
            if args.suite in {"cumulative", "all"}:
                path = run_engine_cumulative(
                    config, list(endpoint_urls), output_root, args.warmups
                )
                validate_rdfs_equivalence(output_root, "cumulative")
                outputs["cumulative"] = str(path)
            if args.suite in {"scalability", "all"}:
                path = run_engine_scalability(
                    config, list(endpoint_urls), output_root, args.warmups
                )
                validate_rdfs_equivalence(output_root, "scalability")
                outputs["scalability"] = str(path)
        print(json.dumps(outputs, indent=2, ensure_ascii=False))
        return 0

    if args.command == "topology":
        from .topology import load_topology, load_topology_manifest

        manifest_path = _target_manifest_path(
            config, args.topology_file, args.name
        )
        if args.action == "validate":
            manifest = load_topology_manifest(manifest_path)
            print(json.dumps(manifest.public(), indent=2, ensure_ascii=False))
            return 0
        selected = load_topology(manifest_path, args.name)
        print(json.dumps(selected.public(), indent=2, ensure_ascii=False))
        return 0


    if args.command == "fragments":
        from .monitoring import export_physical_fragments

        if args.users < 0:
            raise ValueError("--users must be zero or greater")
        inventory = _physical_inventory(config, args)
        paths = export_physical_fragments(
            config,
            inventory,
            args.users,
            config.root / args.output_dir,
        )
        print(json.dumps({"fragments": [str(path) for path in paths]}, indent=2))
        return 0

    if args.command == "physical":
        from .monitoring import run_physical_monitoring_suite
        from .physical_cluster import (
            authorize_cluster,
            deploy_cluster,
            start_cluster,
            status_cluster,
            stop_cluster,
        )

        inventory = _physical_inventory(config, args)
        if args.action == "authorize":
            authorize_cluster(inventory)
            return 0
        if args.action == "deploy":
            deploy_cluster(config.root, inventory)
            return 0
        if args.action == "start":
            start_cluster(config.root, inventory)
            return 0
        if args.action == "status":
            statuses = status_cluster(inventory)
            return 0 if all(item["healthy"] for item in statuses) else 1
        if args.action == "stop":
            stop_cluster(config.root, inventory)
            return 0

        outputs = run_physical_monitoring_suite(
            config,
            inventory,
            config.root / args.output_dir,
            suite=args.action,
            layout=args.layout,
            validate_results=not args.skip_result_validation,
        )
        print(json.dumps(outputs, indent=2, ensure_ascii=False))
        return 0

    if args.command == "load":
        from .load_benchmark import run_load_benchmark
        from .load_config import load_load_config, select_load_profiles

        output_root = config.root / args.output_dir
        if args.target == "plot":
            from .load_reporting import plot_load_comparison

            paths = plot_load_comparison(output_root)
            if args.show:
                _open_paths(paths)
            print(json.dumps({"load_plots": [str(path) for path in paths]}, indent=2))
            return 0
        workload = select_load_profiles(
            load_load_config(config.root / args.load_config),
            dimensions=args.dimension,
            names=args.profile,
        )
        from .preflight import validate_load_workload

        validate_load_workload(config, workload)
        endpoints = None
        topology = _target_topology(config, args, args.target)
        endpoints = topology.endpoints()
        output = run_load_benchmark(
            config,
            workload,
            args.target,
            output_root,
            endpoints,
        )
        print(json.dumps({args.target: str(output)}, indent=2, ensure_ascii=False))
        return 0

    if args.command == "experiment":
        from .experiment_config import (
            load_experiment_config,
            select_reasoning_profiles,
        )
        from .experiments import EXPERIMENTS, run_experiment

        output_root = config.root / args.output_dir
        if args.experiment_name == "plot":
            from .experiment_reporting import plot_experiments

            selected = EXPERIMENTS if args.suite == "all" else (args.suite,)
            paths = plot_experiments(output_root, selected)
            if args.show:
                _open_paths(paths)
            print(
                json.dumps(
                    {"experiment_plots": [str(path) for path in paths]},
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
        if args.experiment_name == "analyze":
            from .experiment_analysis import analyze_experiments
            from .experiment_reporting import plot_claim_analysis

            paths = analyze_experiments(output_root)
            paths.extend(plot_claim_analysis(output_root))
            if args.show:
                _open_paths(paths)
            print(
                json.dumps(
                    {"experiment_analysis": [str(path) for path in paths]},
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0

        experiment_path = Path(args.experiment_config)
        if not experiment_path.is_absolute():
            experiment_path = config.root / experiment_path
        workload = select_reasoning_profiles(
            load_experiment_config(experiment_path),
            args.profile,
        )
        from .preflight import validate_experiment_workload

        validate_experiment_workload(config, workload, experiment_path)
        if args.reasoner:
            config = replace(config, reasoners=tuple(args.reasoner))
        endpoints = None
        topology = _target_topology(config, args, args.target)
        endpoints = topology.endpoints()
        selected = (
            EXPERIMENTS
            if args.experiment_name == "all"
            else (args.experiment_name,)
        )
        outputs = {
            name: str(
                run_experiment(
                    name,
                    config,
                    workload,
                    args.target,
                    output_root,
                    endpoint_urls=endpoints,
                )
            )
            for name in selected
        }
        print(json.dumps(outputs, indent=2, ensure_ascii=False))
        return 0

    if args.command == "study":
        from .study import analyze_category_costs, generate_study_trace
        from .study.config import load_study_config

        output_root = config.root / args.output_dir
        if args.action == "trace":
            study_config_path = Path(args.study_config)
            if not study_config_path.is_absolute():
                study_config_path = config.root / study_config_path
            paths = generate_study_trace(
                config,
                load_study_config(study_config_path),
                output_root,
                topology_name=args.topology_name,
                target=args.target,
            )
            print(
                json.dumps(
                    {"study_trace": [str(path) for path in paths]},
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
        events_path = Path(args.events)
        if not events_path.is_absolute():
            events_path = config.root / events_path
        paths = analyze_category_costs(
            config,
            events_path,
            output_root / "category-cost",
        )
        print(
            json.dumps(
                {"category_cost": [str(path) for path in paths]},
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    raise AssertionError(f"Unhandled command: {args.command}")



def main(argv: list[str] | None = None) -> int:
    import time
    started_ns = time.time_ns()
    args = _parser().parse_args(argv)
    physical_work = (
        args.command == "campaign" and not args.validate_only
        or args.command == "physical" and args.action not in {"status", "authorize"}
        or args.command in {"load", "experiment"} and getattr(args, "target", None) == "physical"
    )
    from contextlib import nullcontext
    from .monitoring.lease import physical_lease
    lease = physical_lease(load_config(args.config).root) if physical_work else nullcontext()
    with lease:
        status = _dispatch(args)
        if args.command in {"physical", "load", "experiment", "engines"} and hasattr(args, "output_dir"):
            from .monitoring.normalize import normalize_completed_outputs
            config = load_config(args.config)
            normalize_completed_outputs(config, config.resolve(Path(args.output_dir)), started_ns)
        return status


if __name__ == "__main__":
    raise SystemExit(main())
