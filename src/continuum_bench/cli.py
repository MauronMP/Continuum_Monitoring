from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import webbrowser

from .benchmark import run_cumulative, run_scalability
from .config import load_config
from .validation import validate_project


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="continuum-bench",
        description="Validate and benchmark the continuum monitoring ontology.",
    )
    parser.add_argument(
        "--config",
        default="configs/benchmark.toml",
        help="TOML configuration file (default: configs/benchmark.toml)",
    )
    parser.add_argument(
        "--topology-file",
        help=(
            "Elastic topology manifest (default: topology_file from the "
            "benchmark config)"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor = subparsers.add_parser("doctor", help="Read-only installation, Docker and SSH diagnostics")
    doctor.add_argument("--docker", action="store_true")
    doctor.add_argument("--physical", action="store_true")
    doctor.add_argument("--json", action="store_true")
    subparsers.add_parser("validate", help="Run syntax, policy and reasoner checks")
    topology = subparsers.add_parser(
        "topology",
        help="Validate, inspect or manage a manifest-defined topology",
    )
    topology.add_argument(
        "action",
        choices=("validate", "show", "render", "up", "status", "logs", "down"),
    )
    topology.add_argument("--name", default="docker")
    topology.add_argument(
        "--output",
        help=(
            "Generated Compose path (default: "
            "outputs/runtime/docker-compose-NAME.yml)"
        ),
    )
    benchmark = subparsers.add_parser("benchmark", help="Run benchmark suites")
    benchmark.add_argument(
        "suite",
        choices=("cumulative", "scalability", "all"),
    )
    benchmark.add_argument(
        "--python-only",
        action="store_true",
        help="Skip the automatic Jena/RDF4J/RDFLib/Oxigraph product run",
    )
    benchmark.add_argument(
        "--engine-warmups",
        type=int,
        default=1,
        help="Unmeasured product-engine warm-ups (default: 1)",
    )
    benchmark.add_argument(
        "--keep-engine-services",
        action="store_true",
        help="Leave an automatically started engine stack running",
    )
    plot = subparsers.add_parser(
        "plot",
        help="Regenerate plots from existing benchmark CSV files",
    )
    plot.add_argument(
        "suite",
        choices=(
            "cumulative",
            "scalability",
            "all",
            "publication",
            "engines",
        ),
    )
    plot.add_argument(
        "--show",
        action="store_true",
        help="Open the generated PNG files with the system image viewer",
    )
    plot.add_argument(
        "--engine-dir",
        default="outputs/engines",
        help="Cross-engine result root used by 'plot engines'",
    )
    plot.add_argument(
        "--engine-suite",
        choices=("cumulative", "scalability", "all"),
        default="all",
        help="Engine figure subset used by 'plot engines' (default: all)",
    )
    engines = subparsers.add_parser(
        "engines",
        help="Benchmark independent RDF/reasoning engines",
    )
    engines.add_argument(
        "suite",
        choices=("cumulative", "scalability", "all"),
    )
    engines.add_argument(
        "--endpoints",
        default=(
            "http://127.0.0.1:8291,http://127.0.0.1:8292,"
            "http://127.0.0.1:8293,http://127.0.0.1:8294"
        ),
        help="Comma-separated RDFLib, Jena, RDF4J and Oxigraph URLs",
    )
    engines.add_argument(
        "--warmups",
        type=int,
        default=1,
        help="Unmeasured warm-up runs per engine and dataset (default: 1)",
    )
    engines.add_argument("--output-dir", default="outputs/engines")
    docker = subparsers.add_parser(
        "docker",
        help="Run a benchmark against an elastic Docker topology",
    )
    docker.add_argument(
        "suite",
        choices=("cumulative", "scalability", "all"),
    )
    docker.add_argument(
        "--endpoints",
        help="Optional comma-separated node URLs overriding the manifest",
    )
    docker.add_argument("--topology-name", default="docker")
    docker.add_argument(
        "--output-dir",
        default="outputs/docker",
    )
    docker.add_argument(
        "--layout",
        choices=("replicated", "sharded"),
        default="sharded",
        help=(
            "Data placement layout (default: sharded; results are written "
            "below OUTPUT_DIR/LAYOUT)"
        ),
    )
    docker.add_argument(
        "--topology-only",
        action="store_true",
        help="Skip the automatic independent semantic-engine product run",
    )
    docker.add_argument(
        "--engine-warmups",
        type=int,
        default=1,
        help="Unmeasured product-engine warm-ups (default: 1)",
    )
    docker.add_argument(
        "--keep-engine-services",
        action="store_true",
        help="Leave an automatically started engine stack running",
    )
    sharded = subparsers.add_parser(
        "sharded",
        help=(
            "Run the authority/privacy-partitioned benchmark on Docker or "
            "physical nodes"
        ),
    )
    sharded.add_argument("target", choices=("docker", "physical"))
    sharded.add_argument(
        "suite",
        choices=("cumulative", "scalability", "all"),
    )
    sharded.add_argument(
        "--endpoints",
        help="Optional Docker endpoint override; ignored for physical target",
    )
    sharded.add_argument(
        "--inventory",
        help="Legacy physical inventory override; ignored for Docker target",
    )
    sharded.add_argument(
        "--topology-name",
        help="Topology name (default: docker or physical, matching target)",
    )
    sharded.add_argument(
        "--output-dir",
        help="Result root (default: outputs/sharded-TARGET)",
    )
    sharded.add_argument(
        "--skip-result-validation",
        action="store_true",
        help=(
            "Do not compare merged results with the monolithic oracle "
            "(validation is enabled by default and excluded from timings)"
        ),
    )
    fragments = subparsers.add_parser(
        "fragments",
        help="Export one authority/privacy-aware RDF fragment per node",
    )
    fragments.add_argument("--users", type=int, default=0)
    fragments.add_argument(
        "--output-dir",
        default="outputs/fragments",
    )
    fragments.add_argument("--topology-name", default="docker")
    physical = subparsers.add_parser(
        "physical",
        help="Deploy, manage or benchmark an elastic physical continuum",
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
    physical.add_argument(
        "--inventory",
        help="Legacy physical inventory override",
    )
    physical.add_argument("--topology-name", default="physical")
    physical.add_argument(
        "--ssh-user",
        help="Override cluster.ssh_user for Raspberry Pi management",
    )
    physical.add_argument("--output-dir", default="outputs/physical")
    physical.add_argument(
        "--layout",
        choices=("replicated", "sharded"),
        default="sharded",
        help=(
            "Benchmark data placement layout (default: sharded; ignored by "
            "lifecycle actions)"
        ),
    )
    load = subparsers.add_parser(
        "load",
        help=(
            "Run or plot the rate-controlled multidimensional load benchmark"
        ),
    )
    load.add_argument(
        "target",
        choices=("monolith", "docker", "physical", "all", "plot"),
    )
    load.add_argument(
        "--load-config",
        default="configs/load-benchmark.toml",
        help="Load profile TOML (default: configs/load-benchmark.toml)",
    )
    load.add_argument(
        "--docker-endpoints",
        help="Optional Docker endpoint override",
    )
    load.add_argument(
        "--inventory",
        help="Legacy physical inventory override",
    )
    load.add_argument("--docker-topology", default="docker")
    load.add_argument("--physical-topology", default="physical")
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
        help="Run only this independent-variable series; repeatable",
    )
    load.add_argument(
        "--profile",
        action="append",
        help="Run only this named load profile; repeatable",
    )
    load.add_argument("--output-dir", default="outputs/load")
    load.add_argument(
        "--show",
        action="store_true",
        help="Open generated comparison PNG files (plot/all only)",
    )
    experiment = subparsers.add_parser(
        "experiment",
        help=(
            "Run separated query scale-out, hardware reasoning, or "
            "authority-partitioned ontology experiments"
        ),
    )
    experiment_commands = experiment.add_subparsers(
        dest="experiment_name",
        required=True,
    )

    def add_experiment_run_arguments(command_parser) -> None:
        command_parser.add_argument(
            "target",
            choices=("monolith", "docker", "physical", "all"),
        )
        command_parser.add_argument(
            "--experiment-config",
            default="configs/experiments.toml",
        )
        command_parser.add_argument(
            "--docker-endpoints",
            help="Optional Docker endpoint override",
        )
        command_parser.add_argument(
            "--inventory",
            help="Legacy physical inventory override",
        )
        command_parser.add_argument("--docker-topology", default="docker")
        command_parser.add_argument("--physical-topology", default="physical")
        command_parser.add_argument(
            "--output-dir",
            default="outputs/experiments",
        )
        command_parser.add_argument(
            "--reasoner",
            action="append",
            choices=("rdfs", "owlrl", "rdfs_owlrl"),
            help="Run only this reasoning profile; repeatable",
        )
        command_parser.add_argument(
            "--profile",
            action="append",
            help=(
                "Select reasoning-hardware profile by name; repeatable and "
                "ignored by the other experiments"
            ),
        )

    for experiment_name in (
        "scale-out",
        "reasoning-hardware",
        "distributed-ontology",
        "all",
    ):
        add_experiment_run_arguments(
            experiment_commands.add_parser(experiment_name)
        )
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
    experiment_plot.add_argument(
        "--output-dir",
        default="outputs/experiments",
    )
    experiment_plot.add_argument("--show", action="store_true")
    experiment_analyze = experiment_commands.add_parser(
        "analyze",
        help=(
            "Calculate matched speedups, costs, break-even and claim verdicts"
        ),
    )
    experiment_analyze.add_argument(
        "--output-dir",
        default="outputs/experiments",
    )
    experiment_analyze.add_argument("--show", action="store_true")
    compare = subparsers.add_parser(
        "compare",
        help="Compare monolithic and Docker benchmark CSV files",
    )
    compare.add_argument(
        "suite",
        choices=("cumulative", "scalability", "all"),
    )
    compare.add_argument("--monolith-dir", default="outputs")
    compare.add_argument(
        "--docker-dir",
        default="outputs/docker/sharded",
    )
    compare.add_argument("--output-dir", default="outputs/comparison")
    return parser


def _run_default_product_engines(
    config,
    suite: str,
    output_root: Path,
    *,
    warmups: int,
    keep_running: bool,
) -> list[str]:
    if warmups < 0:
        raise ValueError("Engine warm-ups must be zero or greater")
    from .engine_stack import semantic_engine_stack
    from .engines import (
        run_engine_cumulative,
        run_engine_scalability,
        validate_rdfs_equivalence,
    )
    from .plotting import plot_engine_benchmark

    paths: list[Path] = []
    with semantic_engine_stack(
        config.root,
        keep_running=keep_running,
    ) as endpoint_urls:
        if suite in {"cumulative", "all"}:
            run_engine_cumulative(
                config,
                list(endpoint_urls),
                output_root,
                warmups=warmups,
            )
            paths.append(
                validate_rdfs_equivalence(output_root, "cumulative")
            )
        if suite in {"scalability", "all"}:
            run_engine_scalability(
                config,
                list(endpoint_urls),
                output_root,
                warmups=warmups,
            )
            paths.append(
                validate_rdfs_equivalence(output_root, "scalability")
            )
    paths.extend(
        plot_engine_benchmark(
            output_root,
            suites=(
                ("cumulative", "scalability")
                if suite == "all"
                else (suite,)
            ),
        )
    )
    return [str(path) for path in paths]


def _manifest_path(config, override: str | None) -> Path:
    path = Path(override) if override else config.topology_file
    return path if path.is_absolute() else config.root / path


def _endpoint_override(value: str | None) -> list[str] | None:
    if not value:
        return None
    endpoints = [item.strip() for item in value.split(",") if item.strip()]
    if not endpoints:
        raise ValueError("Endpoint override cannot be empty")
    return endpoints


def _configured_endpoints(
    config,
    manifest_override: str | None,
    topology_name: str,
    endpoint_override: str | None = None,
) -> tuple[object, list[str]]:
    from .topology import load_topology

    manifest_path = _manifest_path(config, manifest_override)
    topology = load_topology(manifest_path, topology_name)
    endpoints = _endpoint_override(endpoint_override) or topology.endpoints()
    return topology, endpoints


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "doctor":
        from .environment import main as doctor_main
        options = ["--root", str(Path(args.config).resolve().parents[1])]
        options += [f"--{name}" for name in ("docker", "physical", "json") if getattr(args, name)]
        return doctor_main(options)
    config = load_config(args.config)

    if args.command == "topology":
        from .topology import (
            load_topology,
            load_topology_manifest,
            render_docker_compose,
            run_docker_topology,
        )

        manifest_path = _manifest_path(config, args.topology_file)
        manifest = load_topology_manifest(manifest_path)
        if args.action == "validate":
            print(json.dumps(manifest.public(), indent=2, ensure_ascii=False))
            return 0
        selected = load_topology(manifest_path, args.name)
        if args.action == "show":
            print(json.dumps(selected.public(), indent=2, ensure_ascii=False))
            return 0
        compose_path = (
            Path(args.output)
            if args.output
            else config.root
            / "outputs"
            / "runtime"
            / f"docker-compose-{selected.name}.yml"
        )
        if not compose_path.is_absolute():
            compose_path = config.root / compose_path
        if args.action == "render":
            result = render_docker_compose(
                selected,
                compose_path,
                root=config.root,
            )
            print(json.dumps({"compose_file": str(result)}, indent=2))
            return 0
        return run_docker_topology(
            selected,
            compose_path,
            args.action,
            root=config.root,
        )

    if (
        args.command == "benchmark" and not args.python_only
        or args.command == "docker" and not args.topology_only
    ):
        from .engine_stack import preflight
        preflight(config.root)

    if args.command == "validate":
        report = validate_project(config)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["ok"] else 1

    if args.command == "engines":
        from .engines import (
            run_engine_cumulative,
            run_engine_scalability,
            validate_rdfs_equivalence,
        )
        from .plotting import plot_engine_benchmark

        endpoints = [
            value.strip()
            for value in args.endpoints.split(",")
            if value.strip()
        ]
        if args.warmups < 0:
            raise ValueError("--warmups must be zero or greater")
        output_root = config.root / args.output_dir
        paths: list[Path] = []
        if args.suite in {"cumulative", "all"}:
            run_engine_cumulative(
                config,
                endpoints,
                output_root,
                warmups=args.warmups,
            )
            paths.append(
                validate_rdfs_equivalence(output_root, "cumulative")
            )
        if args.suite in {"scalability", "all"}:
            run_engine_scalability(
                config,
                endpoints,
                output_root,
                warmups=args.warmups,
            )
            paths.append(
                validate_rdfs_equivalence(output_root, "scalability")
            )
        paths.extend(
            plot_engine_benchmark(
                output_root,
                suites=(
                    ("cumulative", "scalability")
                    if args.suite == "all"
                    else (args.suite,)
                ),
            )
        )
        print(
            json.dumps(
                {"engines": [str(path) for path in paths]},
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    if args.command == "docker":
        from .distributed import (
            run_docker_cumulative,
            run_docker_scalability,
        )
        from .sharded import (
            run_sharded_cumulative,
            run_sharded_scalability,
        )

        topology, endpoints = _configured_endpoints(
            config,
            args.topology_file,
            args.topology_name,
            args.endpoints,
        )
        output_root = config.root / args.output_dir / args.layout
        outputs: dict[str, str] = {}
        cumulative_runner = (
            run_sharded_cumulative
            if args.layout == "sharded"
            else run_docker_cumulative
        )
        scalability_runner = (
            run_sharded_scalability
            if args.layout == "sharded"
            else run_docker_scalability
        )
        layout_options = (
            {
                "target": "docker",
                "validate_results": True,
                "topology": topology,
            }
            if args.layout == "sharded"
            else {"topology": topology}
        )
        if args.suite in {"cumulative", "all"}:
            outputs["cumulative"] = str(
                cumulative_runner(
                    config,
                    endpoints,
                    output_root,
                    **layout_options,
                )
            )
        if args.suite in {"scalability", "all"}:
            outputs["scalability"] = str(
                scalability_runner(
                    config,
                    endpoints,
                    output_root,
                    **layout_options,
                )
            )
        if not args.topology_only:
            outputs["engines"] = _run_default_product_engines(
                config,
                args.suite,
                output_root / "engines",
                warmups=args.engine_warmups,
                keep_running=args.keep_engine_services,
            )
        print(json.dumps(outputs, indent=2, ensure_ascii=False))
        return 0

    if args.command == "fragments":
        from .sharded import export_fragments
        from .topology import load_topology

        if args.users < 0:
            raise ValueError("--users must be zero or greater")
        manifest_path = _manifest_path(config, args.topology_file)
        topology = load_topology(manifest_path, args.topology_name)
        paths = export_fragments(
            config,
            args.users,
            config.root / args.output_dir,
            topology=topology,
        )
        print(
            json.dumps(
                {"fragments": [str(path) for path in paths]},
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    if args.command == "sharded":
        topology = None
        from .sharded import (
            run_sharded_cumulative,
            run_sharded_scalability,
        )

        if args.target == "physical":
            from .physical_cluster import load_physical_inventory

            topology_name = args.topology_name or "physical"
            inventory_path = (
                config.root / args.inventory
                if args.inventory
                else _manifest_path(config, args.topology_file)
            )
            inventory = load_physical_inventory(
                inventory_path,
                topology_name=topology_name,
            )
            endpoint_urls = [node.endpoint for node in inventory.nodes]
            topology = inventory.topology
        else:
            topology_name = args.topology_name or "docker"
            topology, endpoint_urls = _configured_endpoints(
                config,
                args.topology_file,
                topology_name,
                args.endpoints,
            )
        output_root = config.root / (
            args.output_dir or f"outputs/sharded-{args.target}"
        )
        sharded_outputs: dict[str, str] = {}
        run_options = {
            "target": args.target,
            "validate_results": not args.skip_result_validation,
        }
        if args.target == "docker":
            run_options["topology"] = topology
        elif topology is not None:
            run_options["topology"] = topology
        if args.suite in {"cumulative", "all"}:
            sharded_outputs["cumulative"] = str(
                run_sharded_cumulative(
                    config,
                    endpoint_urls,
                    output_root,
                    **run_options,
                )
            )
        if args.suite in {"scalability", "all"}:
            sharded_outputs["scalability"] = str(
                run_sharded_scalability(
                    config,
                    endpoint_urls,
                    output_root,
                    **run_options,
                )
            )
        print(json.dumps(sharded_outputs, indent=2, ensure_ascii=False))
        return 0

    if args.command == "physical":
        from .physical import (
            run_physical_cumulative,
            run_physical_scalability,
        )
        from .physical_cluster import (
            authorize_cluster,
            deploy_cluster,
            load_physical_inventory,
            start_cluster,
            status_cluster,
            stop_cluster,
        )

        inventory_path = (
            config.root / args.inventory
            if args.inventory
            else _manifest_path(config, args.topology_file)
        )
        inventory_options = {"ssh_user": args.ssh_user}
        if args.topology_name != "physical":
            inventory_options["topology_name"] = args.topology_name
        inventory = load_physical_inventory(
            inventory_path,
            **inventory_options,
        )
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

        output_root = config.root / args.output_dir / args.layout
        physical_outputs: dict[str, str] = {}
        if args.layout == "sharded":
            from .sharded import (
                run_sharded_cumulative,
                run_sharded_scalability,
            )

            endpoint_urls = [node.endpoint for node in inventory.nodes]
            cumulative_runner = run_sharded_cumulative
            scalability_runner = run_sharded_scalability
            layout_args = (config, endpoint_urls, output_root)
            layout_options = {
                "target": "physical",
                "validate_results": True,
            }
            if inventory.topology is not None:
                layout_options["topology"] = inventory.topology
        else:
            cumulative_runner = run_physical_cumulative
            scalability_runner = run_physical_scalability
            layout_args = (config, inventory_path, output_root)
            layout_options = (
                {}
                if args.topology_name == "physical"
                else {"topology_name": args.topology_name}
            )
        if args.action in {"cumulative", "all"}:
            physical_outputs["cumulative"] = str(
                cumulative_runner(
                    *layout_args,
                    **layout_options,
                )
            )
        if args.action in {"scalability", "all"}:
            physical_outputs["scalability"] = str(
                scalability_runner(
                    *layout_args,
                    **layout_options,
                )
            )
        print(json.dumps(physical_outputs, indent=2, ensure_ascii=False))
        return 0

    if args.command == "load":
        from .load_benchmark import run_load_benchmark
        from .load_config import load_load_config, select_load_profiles
        from .load_reporting import plot_load_comparison
        from .physical import inventory_endpoints

        output_root = config.root / args.output_dir
        if args.target == "plot":
            paths = plot_load_comparison(output_root)
            if args.show:
                for path in paths:
                    if path.suffix == ".png":
                        webbrowser.open(path.resolve().as_uri())
            print(
                json.dumps(
                    {"load_plots": [str(path) for path in paths]},
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
        workload = load_load_config(config.root / args.load_config)
        workload = select_load_profiles(
            workload,
            dimensions=args.dimension,
            names=args.profile,
        )
        _, docker_endpoints = _configured_endpoints(
            config,
            args.topology_file,
            args.docker_topology,
            args.docker_endpoints,
        )
        physical_inventory = (
            config.root / args.inventory
            if args.inventory
            else _manifest_path(config, args.topology_file)
        )
        targets = (
            ("monolith", "docker", "physical")
            if args.target == "all"
            else (args.target,)
        )
        outputs: dict[str, str | list[str]] = {}
        for target in targets:
            endpoints = (
                None
                if target == "monolith"
                else (
                    docker_endpoints
                    if target == "docker"
                    else inventory_endpoints(
                        physical_inventory,
                        args.physical_topology,
                    )
                )
            )
            outputs[target] = str(
                run_load_benchmark(
                    config,
                    workload,
                    target,
                    output_root,
                    endpoints,
                )
            )
        if args.target == "all":
            plot_paths = plot_load_comparison(output_root)
            outputs["plots"] = [str(path) for path in plot_paths]
            if args.show:
                for path in plot_paths:
                    if path.suffix == ".png":
                        webbrowser.open(path.resolve().as_uri())
        print(json.dumps(outputs, indent=2, ensure_ascii=False))
        return 0

    if args.command == "experiment":
        from dataclasses import replace

        from .experiment_analysis import analyze_experiments
        from .experiment_config import (
            load_experiment_config,
            select_reasoning_profiles,
        )
        from .experiment_reporting import (
            plot_claim_analysis,
            plot_experiments,
        )
        from .experiments import EXPERIMENTS, run_experiment
        from .physical import inventory_endpoints

        output_root = config.root / args.output_dir
        if args.experiment_name == "plot":
            selected = (
                EXPERIMENTS
                if args.suite == "all"
                else (args.suite,)
            )
            paths = plot_experiments(output_root, selected)
            if args.show:
                for path in paths:
                    if path.suffix == ".png":
                        webbrowser.open(path.resolve().as_uri())
            print(
                json.dumps(
                    {"experiment_plots": [str(path) for path in paths]},
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
        if args.experiment_name == "analyze":
            paths = analyze_experiments(output_root)
            paths.extend(plot_claim_analysis(output_root))
            if args.show:
                for path in paths:
                    if path.suffix == ".png":
                        webbrowser.open(path.resolve().as_uri())
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
        if args.reasoner:
            config = replace(config, reasoners=tuple(args.reasoner))
        _, docker_endpoints = _configured_endpoints(
            config,
            args.topology_file,
            args.docker_topology,
            args.docker_endpoints,
        )
        targets = (
            ("monolith", "docker", "physical")
            if args.target == "all"
            else (args.target,)
        )
        physical_endpoints = (
            inventory_endpoints(
                (
                    config.root / args.inventory
                    if args.inventory
                    else _manifest_path(config, args.topology_file)
                ),
                args.physical_topology,
            )
            if "physical" in targets
            else []
        )
        names = (
            EXPERIMENTS
            if args.experiment_name == "all"
            else (args.experiment_name,)
        )
        outputs: dict[str, str | list[str]] = {}
        for name in names:
            for target in targets:
                endpoints = (
                    None
                    if target == "monolith"
                    else (
                        docker_endpoints
                        if target == "docker"
                        else physical_endpoints
                    )
                )
                outputs[f"{name}:{target}"] = str(
                    run_experiment(
                        name,
                        config,
                        workload,
                        target,
                        output_root,
                        endpoints,
                    )
                )
        if args.target == "all":
            paths = plot_experiments(output_root, tuple(names))
            outputs["plots"] = [str(path) for path in paths]
            analysis_paths = analyze_experiments(output_root)
            analysis_paths.extend(plot_claim_analysis(output_root))
            outputs["analysis"] = [
                str(path) for path in analysis_paths
            ]
        print(json.dumps(outputs, indent=2, ensure_ascii=False))
        return 0

    if args.command == "compare":
        from .compare import compare_all, compare_suite
        from .plotting import plot_comparison

        monolith_root = config.root / args.monolith_dir
        docker_root = config.root / args.docker_dir
        output_root = config.root / args.output_dir
        if args.suite == "all":
            paths = compare_all(monolith_root, docker_root, output_root)
            paths.extend(plot_comparison(output_root))
        else:
            paths = list(
                compare_suite(
                    args.suite,
                    monolith_root,
                    docker_root,
                    output_root,
                )
            )
            paths.extend(plot_comparison(output_root, (args.suite,)))
        print(
            json.dumps(
                {"comparison": [str(path) for path in paths]},
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    from .plotting import (
        plot_cumulative,
        plot_engine_benchmark,
        plot_publication,
        plot_scalability,
    )

    outputs: dict[str, list[str]] = {}
    if args.command == "plot":
        output_root = config.resolve(config.output_dir)
        if args.suite == "engines":
            outputs["engines"] = [
                str(path)
                for path in plot_engine_benchmark(
                    config.root / args.engine_dir,
                    suites=(
                        ("cumulative", "scalability")
                        if args.engine_suite == "all"
                        else (args.engine_suite,)
                    ),
                )
            ]
        if args.suite == "publication":
            outputs["publication"] = [
                str(path) for path in plot_publication(output_root)
            ]
        if args.suite in {"cumulative", "all"}:
            outputs["cumulative"] = [
                str(path) for path in plot_cumulative(output_root / "cumulative")
            ]
        if args.suite in {"scalability", "all"}:
            outputs["scalability"] = [
                str(path)
                for path in plot_scalability(output_root / "scalability")
            ]
        if args.show:
            for paths in outputs.values():
                for path in paths:
                    webbrowser.open(Path(path).resolve().as_uri())
        print(json.dumps(outputs, indent=2, ensure_ascii=False))
        return 0

    output_root = config.resolve(config.output_dir)
    if args.suite in {"cumulative", "all"}:
        directory = run_cumulative(config)
        outputs["cumulative"] = [
            str(path) for path in plot_cumulative(directory)
        ]
    if args.suite in {"scalability", "all"}:
        directory = run_scalability(config)
        outputs["scalability"] = [
            str(path) for path in plot_scalability(directory)
        ]
    if not args.python_only:
        outputs["engines"] = _run_default_product_engines(
            config,
            args.suite,
            output_root / "engines",
            warmups=args.engine_warmups,
            keep_running=args.keep_engine_services,
        )
    print(json.dumps(outputs, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
