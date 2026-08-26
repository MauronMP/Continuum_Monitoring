"""Compare monolithic and five-node distributed benchmark results."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .csv_utils import write_dict_rows


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write(path: Path, rows: list[dict[str, Any]]) -> None:
    write_dict_rows(
        path,
        rows,
        empty_message=f"No comparison rows for {path}",
    )


def _summary_key(row: dict[str, str], suite: str) -> tuple[str, ...]:
    if suite == "cumulative":
        return row["reasoner"], row["repetition"], row["stage"]
    return row["reasoner"], row["repetition"], row["synthetic_users"]


def _detail_key(row: dict[str, str], suite: str) -> tuple[str, ...]:
    base = (row["reasoner"], row["repetition"], row["query_id"])
    if suite == "cumulative":
        return base + (row["stage"],)
    return base + (row["synthetic_users"],)


def _source_metadata(row: dict[str, str]) -> dict[str, str]:
    """Normalize replicated and authority-sharded result provenance."""
    role = row.get("role", "")
    endpoint = row.get("endpoint", "")
    source_roles = row.get("source_roles", "") or role
    source_count = row.get("source_count", "") or ("1" if role else "")
    return {
        # Historical columns retained for existing report consumers.
        "docker_role": role,
        "docker_endpoint": endpoint,
        # Sharded results may have several authorities and no single endpoint.
        "distributed_source_roles": source_roles,
        "distributed_source_count": source_count,
    }


def compare_suite(
    suite: str,
    monolith_root: Path,
    docker_root: Path,
    output_root: Path,
    node_count: int = 5,
) -> tuple[Path, Path]:
    monolith_summary = _read(monolith_root / suite / "summary.csv")
    docker_summary = _read(docker_root / suite / "summary.csv")
    docker_by_key = {
        _summary_key(row, suite): row for row in docker_summary
    }
    rows: list[dict[str, Any]] = []
    for monolith in monolith_summary:
        key = _summary_key(monolith, suite)
        if key not in docker_by_key:
            raise ValueError(f"Docker summary is missing {suite} run {key}")
        docker = docker_by_key[key]
        monolith_ms = float(monolith["total_ms"])
        docker_ms = float(docker["total_wall_ms"])
        speedup = monolith_ms / docker_ms if docker_ms else 0.0
        row: dict[str, Any] = {
            "suite": suite,
            "reasoner": monolith["reasoner"],
            "repetition": monolith["repetition"],
        }
        if suite == "cumulative":
            row.update(
                {
                    "stage": monolith["stage"],
                    "category": monolith["added_category"],
                    "query_count": monolith["query_count"],
                }
            )
        else:
            row.update(
                {
                    "synthetic_users": monolith["synthetic_users"],
                    "query_count": monolith["query_count"],
                    "input_triples": monolith["input_triples"],
                }
            )
        row.update(
            {
                "monolith_total_ms": monolith_ms,
                "docker_wall_ms": docker_ms,
                "speedup": speedup,
                "parallel_efficiency": speedup / node_count,
                "docker_change_percent": (
                    (docker_ms - monolith_ms) / monolith_ms * 100
                    if monolith_ms
                    else 0.0
                ),
                "docker_node_reasoning_ms_sum": docker[
                    "node_reasoning_ms_sum"
                ],
                "docker_node_query_ms_sum": docker["node_query_ms_sum"],
            }
        )
        rows.append(row)

    monolith_detail = _read(monolith_root / suite / "query-runs.csv")
    docker_detail = _read(docker_root / suite / "query-runs.csv")
    docker_details = {
        _detail_key(row, suite): row for row in docker_detail
    }
    validations: list[dict[str, Any]] = []
    for monolith in monolith_detail:
        key = _detail_key(monolith, suite)
        if key not in docker_details:
            raise ValueError(f"Docker query results are missing {key}")
        docker = docker_details[key]
        monolith_ask = monolith.get("ask_result", "")
        docker_ask = docker.get("ask_result", "")
        cardinality_ask_matches = (
            monolith["result_count"] == docker["result_count"]
            and monolith_ask == docker_ask
        )
        monolith_digest = monolith.get("result_digest", "")
        distributed_digest = docker.get("result_digest", "")
        digest_available = bool(monolith_digest and distributed_digest)
        matches = cardinality_ask_matches and (
            monolith_digest == distributed_digest
            if digest_available
            else True
        )
        validations.append(
            {
                "suite": suite,
                "reasoner": monolith["reasoner"],
                "repetition": monolith["repetition"],
                "query_id": monolith["query_id"],
                "stage_or_users": (
                    monolith["stage"]
                    if suite == "cumulative"
                    else monolith["synthetic_users"]
                ),
                "monolith_result_count": monolith["result_count"],
                "docker_result_count": docker["result_count"],
                "monolith_ask_result": monolith_ask,
                "docker_ask_result": docker_ask,
                "monolith_result_digest": monolith_digest,
                "distributed_result_digest": distributed_digest,
                "validation_level": (
                    "result_digest"
                    if digest_available
                    else "cardinality_ask"
                ),
                "matches": matches,
                **_source_metadata(docker),
            }
        )

    comparison_path = output_root / f"{suite}.csv"
    validation_path = output_root / f"{suite}-result-validation.csv"
    _write(comparison_path, rows)
    _write(validation_path, validations)
    mismatches = [row for row in validations if not row["matches"]]
    if mismatches:
        raise AssertionError(
            f"{len(mismatches)} distributed results differ from monolith"
        )
    return comparison_path, validation_path


def compare_all(
    monolith_root: Path,
    docker_root: Path,
    output_root: Path,
) -> list[Path]:
    paths = []
    for suite in ("cumulative", "scalability"):
        paths.extend(
            compare_suite(suite, monolith_root, docker_root, output_root)
        )
    return paths
