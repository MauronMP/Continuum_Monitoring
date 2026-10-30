"""CLI integration for the third, containerized scalability battery."""

import json
import math
from pathlib import Path

from .config import load
from . import deployment
from .runner import run


def register(subparsers):
    parser = subparsers.add_parser(
        "container-scale",
        help="Containerized scalability on physical hosts using Compose",
    )
    parser.add_argument(
        "action",
        choices=("doctor", "render", "deploy", "status", "stop", "run", "report", "validate-reasoners"),
    )
    parser.add_argument("--container-config", default="configs/container-scale.toml")
    parser.add_argument("--output-dir", default="outputs/container-scale")
    parser.add_argument("--input-dir", help="Existing campaign directory for report")
    parser.add_argument(
        "--containers-per-host",
        type=int,
        help="Override configured placements with a single positive count",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        help="Run only this named scenario; repeat to select more",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--concurrency", type=int, nargs="+", action="extend",
        help="Positive concurrent catalog-request levels for selected run scenarios, e.g. --concurrency 1 2 4 8; repeatable.",
    )
    parser.add_argument(
        "--reasoner", action="append",
        choices=("rdf", "rdfs", "hermit", "openllet", "jfact", "konclude"),
        help="Select a reasoner; repeat to build a matrix replacing the configured list. rdf is an alias for RDFS closure. DL choices enable the DL image.",
    )
    parser.add_argument(
        "--host",
        action="append",
        help="Target lifecycle operations at this host without changing logical topology; repeat as needed",
    )
    parser.add_argument(
        "--exclude-host",
        action="append",
        default=[],
        help="Explicitly exclude an unavailable physical host ID; repeat as needed",
    )


def dispatch(args, benchmark):
    if args.dry_run and args.action != "run":
        raise ValueError("--dry-run is supported only for container-scale run")
    config = load(
        benchmark.resolve(Path(args.container_config)),
        benchmark.root,
        exclude_hosts=args.exclude_host, reasoners=args.reasoner,
    )
    if args.containers_per_host is not None:
        # Apply overrides through the same validator, without writing the source file.
        import tempfile

        text = config.path.read_text()
        import re

        text = re.sub(
            r"^containers_per_host\s*=.*$",
            f"containers_per_host = [{args.containers_per_host}]",
            text,
            flags=re.M,
        )
        with tempfile.NamedTemporaryFile("w", suffix=".toml") as handle:
            handle.write(text)
            handle.flush()
            from dataclasses import replace

            config = replace(
                load(
                    Path(handle.name), benchmark.root, exclude_hosts=args.exclude_host, reasoners=args.reasoner
                ),
                path=config.path,
            )
    if args.repetitions is not None:
        if args.repetitions < 1:
            raise ValueError("repetitions must be positive")
        config.experiment["repetitions"] = args.repetitions
    if args.concurrency is not None:
        if args.action != "run":
            raise ValueError("--concurrency is supported only for container-scale run")
        if any(level < 1 for level in args.concurrency):
            raise ValueError("--concurrency levels must be positive integers")
        levels = sorted(set(args.concurrency))
        for scenario in config.raw["scenarios"]:
            if not args.scenario or scenario["name"] in args.scenario:
                scenario["concurrency"] = list(levels)
    for scope in ("request", "point"):
        value = args.timeout_seconds or getattr(args, f"{scope}_timeout_seconds")
        if value is not None:
            config.experiment[f"{scope}_timeout_seconds"] = value
    if (
        not 5
        < config.experiment["request_timeout_seconds"]
        <= config.experiment["point_timeout_seconds"]
        < math.inf
    ):
        raise ValueError("Require point >= request > 5 second budgets")
    if args.host and args.action not in {"doctor", "deploy", "status", "stop", "validate-reasoners"}:
        raise ValueError(
            "--host is for lifecycle operations; use --exclude-host to select experiment participants"
        )
    output = benchmark.resolve(Path(args.output_dir))
    count = max(config.deployment["containers_per_host"])
    if args.action == "doctor":
        rows = deployment.doctor(config, count, args.host)
        print(json.dumps(rows, indent=2))
        return 0 if all(r["ready"] for r in rows) else 1
    if args.action == "render":
        deployment.render(config, benchmark.root, output / "deployment", count)
        print(output / "deployment")
    elif args.action == "deploy":
        deployment.deploy(
            config, benchmark.root, output / "deployment", count, host_ids=args.host
        )
    elif args.action == "validate-reasoners":
        rows = deployment.validate_reasoners(config, benchmark.root, args.host)
        output.mkdir(parents=True, exist_ok=True)
        (output / "reasoner-validation.json").write_text(json.dumps(rows, indent=2) + "\n")
        print(json.dumps(rows, indent=2))
        return 0 if all(r["status"] == "passed" for r in rows) else 1
    elif args.action == "status":
        print(
            json.dumps(deployment.collect(config, benchmark.root, args.host), indent=2)
        )
    elif args.action == "stop":
        deployment.stop(config, benchmark.root, args.host)
    elif args.action == "run":
        result = run(
            config,
            benchmark,
            output,
            dry_run=args.dry_run,
            scenario_names=args.scenario,
            keep_going=args.keep_going,
        )
        print(f"Results: {result}")
        return (
            0
            if json.loads((result / "campaign.json").read_text())["status"]
            in ("completed", "planned")
            else 1
        )
    elif args.action == "report":
        if not args.input_dir:
            raise ValueError(
                "report requires --input-dir pointing to an existing campaign"
            )
        from .reporting import report

        print(report(benchmark.resolve(Path(args.input_dir))))
    return 0
