"""Independent command entry point: python -m continuum_bench.monitoring.comparison."""
import argparse
import json
from pathlib import Path

from .config import load


def main():
    parser = argparse.ArgumentParser(description="Paired physical policy-decision comparison")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "run"):
        item = sub.add_parser(name)
        item.add_argument("--config", default="configs/comparison.toml")
        item.add_argument("--nodes", nargs="+", help="Physical inventory IDs; configured exclusions still apply")
        if name == "run":
            item.add_argument("--output", help="Override output root; a unique run directory is always created")
    item = sub.add_parser("report")
    item.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.command == "report":
        from .reporting import report
        report(args.directory)
        return 0
    config = load(args.config)
    from .runner import inventory_for, run
    if args.command == "check":
        from .transport import probe
        inventory, selected = inventory_for(config, args.nodes)
        results = [probe(node, inventory, config) for node in selected]
        print(json.dumps({"excluded_nodes": config["exclude_nodes"], "nodes": results}, indent=2))
        return int(any(not r["available"] for r in results))
    if args.output:
        config["output"] = args.output
    directory, failed = run(config, Path.cwd(), args.nodes)
    print(f"Results: {directory}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
