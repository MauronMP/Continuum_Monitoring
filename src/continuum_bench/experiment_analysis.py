"""Cross-architecture analysis for monitoring experiments."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any

from .csv_utils import write_dict_rows
from .result_contract import require_release_metadata


EXPERIMENTS = ("scale-out", "reasoning-hardware", "distributed-ontology")
ARCHITECTURES = ("local", "docker", "physical")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    if path.name == "summary.csv":
        require_release_metadata(path.parent)
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _float(row: dict[str, str], field: str) -> float | None:
    value = row.get(field, "")
    return None if value in {"", None} else float(value)


def _median(values: list[float]) -> float | str:
    return median(values) if values else ""


def _group(rows: list[dict[str, str]], keys: tuple[str, ...], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("status") == "completed":
            buckets[tuple(row.get(key, "") for key in keys)].append(row)
    output: list[dict[str, Any]] = []
    for key_values, samples in sorted(buckets.items()):
        item = dict(zip(keys, key_values, strict=True))
        item["samples"] = len(samples)
        for field in fields:
            item[f"{field}_median"] = _median(
                [
                    value
                    for sample in samples
                    if (value := _float(sample, field)) is not None
                ]
            )
        output.append(item)
    return output


def analyze_experiments(root: Path) -> list[Path]:
    """Create compact per-architecture summaries for existing outputs."""

    root = root.resolve()
    data_root = root / "analysis"
    outputs: list[Path] = []
    specifications = {
        "scale-out": (
            ("reasoner", "node_count"),
            ("queries_per_second", "latency_p95_ms", "query_wall_ms"),
        ),
        "reasoning-hardware": (
            ("reasoner", "role", "dimension", "dimension_value"),
            ("reasoning_ms", "process_cpu_ms", "current_rss_kib"),
        ),
        "distributed-ontology": (
            ("reasoner", "synthetic_users", "node_count"),
            ("total_wall_ms", "prepare_wall_ms", "query_wall_ms"),
        ),
    }
    manifest: dict[str, Any] = {"architectures": {}, "experiments": {}}
    for architecture in ARCHITECTURES:
        manifest["architectures"][architecture] = {}
        for experiment, (keys, fields) in specifications.items():
            rows = _read_csv(root / architecture / experiment / "summary.csv")
            grouped = _group(rows, keys, fields)
            output = data_root / f"{experiment}-{architecture}-summary.csv"
            if grouped:
                write_dict_rows(
                    output,
                    grouped,
                    empty_message=(
                        f"No completed {architecture} {experiment} rows "
                        "were available for analysis"
                    ),
                )
                outputs.append(output)
            else:
                output.unlink(missing_ok=True)
            manifest["architectures"][architecture][experiment] = {
                "input_rows": len(rows),
                "completed_rows": sum(
                    row.get("status") == "completed" for row in rows
                ),
                "summary": str(output) if grouped else None,
            }
    metadata = data_root / "analysis-metadata.json"
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    outputs.append(metadata)
    return outputs
