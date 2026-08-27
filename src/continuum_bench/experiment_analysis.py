"""Matched, claim-oriented analysis for the three architecture experiments."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Iterable

from .csv_utils import write_dict_rows
from .result_contract import require_release_metadata


ARCHITECTURES = ("monolith", "docker", "physical")
DISTRIBUTED_ARCHITECTURES = ("docker", "physical")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    if path.name == "summary.csv":
        require_release_metadata(path.parent)
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _float(row: dict[str, str], field: str) -> float | None:
    value = row.get(field, "")
    return None if value in {"", None} else float(value)


def _median(rows: Iterable[dict[str, str]], field: str) -> float | None:
    values = [
        value for row in rows if (value := _float(row, field)) is not None
    ]
    return median(values) if values else None


def _minimum(rows: Iterable[dict[str, str]], field: str) -> float | None:
    values = [
        value for row in rows if (value := _float(row, field)) is not None
    ]
    return min(values) if values else None


def _maximum(rows: Iterable[dict[str, str]], field: str) -> float | None:
    values = [
        value for row in rows if (value := _float(row, field)) is not None
    ]
    return max(values) if values else None


def _ratio(numerator: float | None, denominator: float | None) -> float | str:
    if numerator is None or denominator in {None, 0.0}:
        return ""
    return numerator / denominator


def _expected_repetitions(
    root: Path,
    architecture: str,
    experiment: str,
) -> int:
    metadata = _read_json(
        root / architecture / experiment / "metadata.json"
    )
    return int(metadata.get("repetitions", 0))


def _expected_scale_out_samples(root: Path, architecture: str) -> int:
    metadata = _read_json(
        root / architecture / "scale-out" / "metadata.json"
    )
    return (
        int(metadata.get("repetitions", 0))
        * int(metadata.get("query_rounds", 0))
    )


def _scale_out_digest_equivalence(
    root: Path,
) -> dict[tuple[str, str, int], bool]:
    baseline: dict[tuple[str, str], set[str]] = defaultdict(set)
    observed: dict[tuple[str, str, int, str], set[str]] = defaultdict(set)
    for architecture in ARCHITECTURES:
        rows = _read_csv(
            root / architecture / "scale-out" / "query-runs.csv"
        )
        for row in rows:
            reasoner = row["reasoner"]
            query_id = row["query_id"]
            digest = row.get("result_digest", "")
            if architecture == "monolith":
                baseline[(reasoner, query_id)].add(digest)
            observed[
                (
                    architecture,
                    reasoner,
                    int(row["node_count"]),
                    query_id,
                )
            ].add(digest)
    result: dict[tuple[str, str, int], bool] = {}
    groups = {
        (architecture, reasoner, nodes)
        for architecture, reasoner, nodes, _ in observed
    }
    for architecture, reasoner, nodes in groups:
        query_ids = {
            query_id
            for item_architecture, item_reasoner, item_nodes, query_id
            in observed
            if (
                item_architecture,
                item_reasoner,
                item_nodes,
            ) == (architecture, reasoner, nodes)
        }
        result[(architecture, reasoner, nodes)] = bool(query_ids) and all(
            len(observed[(architecture, reasoner, nodes, query_id)]) == 1
            and observed[(architecture, reasoner, nodes, query_id)]
            == baseline.get((reasoner, query_id), set())
            for query_id in query_ids
        )
    return result


def analyze_scale_out(root: Path) -> list[dict[str, Any]]:
    all_rows: list[dict[str, str]] = []
    for architecture in ARCHITECTURES:
        all_rows.extend(
            _read_csv(root / architecture / "scale-out" / "summary.csv")
        )
    groups: dict[tuple[str, str, int], list[dict[str, str]]] = defaultdict(list)
    for row in all_rows:
        groups[
            (
                row["architecture"],
                row["reasoner"],
                int(row["node_count"]),
            )
        ].append(row)
    aggregates: dict[tuple[str, str, int], dict[str, Any]] = {}
    for key, rows in groups.items():
        architecture, _, _ = key
        completed = [row for row in rows if row["status"] == "completed"]
        expected = _expected_scale_out_samples(root, architecture)
        aggregates[key] = {
            "complete_samples": len(completed),
            "expected_samples": expected,
            "fully_complete": bool(expected) and len(completed) == expected,
            "queries_per_second": _median(completed, "queries_per_second"),
            "queries_per_second_min": _minimum(
                completed, "queries_per_second"
            ),
            "queries_per_second_max": _maximum(
                completed, "queries_per_second"
            ),
            "query_wall_ms": _median(completed, "query_wall_ms"),
            "latency_p95_ms": _median(
                completed, "query_latency_p95_ms"
            ),
            "query_process_cpu_ms": _median(
                completed, "node_query_process_cpu_ms_sum"
            ),
            "sum_current_rss_kib": _median(
                completed, "sum_current_rss_kib"
            ),
        }
    digest_equivalence = _scale_out_digest_equivalence(root)
    output: list[dict[str, Any]] = []
    for (architecture, reasoner, nodes), values in sorted(aggregates.items()):
        architecture_one = aggregates.get((architecture, reasoner, 1), {})
        monolith = aggregates.get(("monolith", reasoner, 1), {})
        own_speedup = _ratio(
            values["queries_per_second"],
            architecture_one.get("queries_per_second"),
        )
        versus_monolith = _ratio(
            values["queries_per_second"],
            monolith.get("queries_per_second"),
        )
        output.append(
            {
                "architecture": architecture,
                "reasoner": reasoner,
                "node_count": nodes,
                **values,
                "semantic_equivalent_to_monolith": (
                    True
                    if architecture == "monolith"
                    else digest_equivalence.get(
                        (architecture, reasoner, nodes), False
                    )
                ),
                "throughput_speedup_vs_own_1_node": own_speedup,
                "throughput_speedup_conservative_vs_own_1_node": _ratio(
                    values["queries_per_second_min"],
                    architecture_one.get("queries_per_second_max"),
                ),
                "scale_out_efficiency_vs_own_1_node": (
                    own_speedup / nodes
                    if isinstance(own_speedup, float)
                    else ""
                ),
                "throughput_speedup_vs_monolith": versus_monolith,
                "latency_speedup_vs_monolith": _ratio(
                    monolith.get("latency_p95_ms"),
                    values["latency_p95_ms"],
                ),
                "cpu_cost_ratio_vs_monolith": _ratio(
                    values["query_process_cpu_ms"],
                    monolith.get("query_process_cpu_ms"),
                ),
                "rss_cost_ratio_vs_monolith": _ratio(
                    values["sum_current_rss_kib"],
                    monolith.get("sum_current_rss_kib"),
                ),
            }
        )
    return output


def analyze_reasoning_hardware(root: Path) -> list[dict[str, Any]]:
    groups: dict[
        tuple[str, str, str, str, int],
        list[dict[str, str]],
    ] = defaultdict(list)
    for architecture in ARCHITECTURES:
        for row in _read_csv(
            root
            / architecture
            / "reasoning-hardware"
            / "summary.csv"
        ):
            groups[
                (
                    architecture,
                    row["role"],
                    row["reasoner"],
                    row["profile"],
                    int(row["dimension_value"]),
                )
            ].append(row)
    aggregates: dict[tuple[str, str, str, str, int], dict[str, Any]] = {}
    for key, rows in groups.items():
        architecture, _, _, _, _ = key
        completed = [row for row in rows if row["status"] == "completed"]
        expected = _expected_repetitions(
            root, architecture, "reasoning-hardware"
        )
        aggregates[key] = {
            "complete_repetitions": len(completed),
            "expected_repetitions": expected,
            "fully_complete": bool(expected) and len(completed) == expected,
            "reasoning_ms": _median(completed, "reasoning_ms"),
            "prepare_wall_ms": _median(completed, "prepare_wall_ms"),
            "process_cpu_ms": _median(completed, "process_cpu_ms"),
            "current_rss_kib": _median(completed, "current_rss_kib"),
            "input_triples": _median(completed, "input_triples"),
            "output_triples": _median(completed, "output_triples"),
            "closure_expansion_factor": _median(
                completed, "closure_expansion_factor"
            ),
        }
    output: list[dict[str, Any]] = []
    for (
        architecture,
        role,
        reasoner,
        profile,
        dimension_value,
    ), values in sorted(aggregates.items()):
        monolith = aggregates.get(
            ("monolith", "cloud", reasoner, profile, dimension_value),
            {},
        )
        output.append(
            {
                "architecture": architecture,
                "role": role,
                "reasoner": reasoner,
                "profile": profile,
                "dimension_value": dimension_value,
                **values,
                "reasoning_slowdown_vs_monolith": _ratio(
                    values["reasoning_ms"],
                    monolith.get("reasoning_ms"),
                ),
                "cpu_cost_ratio_vs_monolith": _ratio(
                    values["process_cpu_ms"],
                    monolith.get("process_cpu_ms"),
                ),
                "rss_cost_ratio_vs_monolith": _ratio(
                    values["current_rss_kib"],
                    monolith.get("current_rss_kib"),
                ),
                "asserted_graph_equivalent": bool(
                    monolith
                    and values["input_triples"]
                    == monolith.get("input_triples")
                ),
                "materialized_graph_size_equivalent": bool(
                    monolith
                    and values["output_triples"]
                    == monolith.get("output_triples")
                ),
            }
        )
    return output


def _distributed_aggregates(
    root: Path,
) -> tuple[
    dict[tuple[str, str, int], dict[str, Any]],
    dict[tuple[str, str, int], list[dict[str, str]]],
]:
    groups: dict[tuple[str, str, int], list[dict[str, str]]] = defaultdict(list)
    for architecture in ARCHITECTURES:
        for row in _read_csv(
            root
            / architecture
            / "distributed-ontology"
            / "summary.csv"
        ):
            groups[
                (
                    architecture,
                    row["reasoner"],
                    int(row["synthetic_users"]),
                )
            ].append(row)
    aggregates: dict[tuple[str, str, int], dict[str, Any]] = {}
    for key, rows in groups.items():
        architecture, _, _ = key
        completed = [row for row in rows if row["status"] == "completed"]
        expected = _expected_repetitions(
            root, architecture, "distributed-ontology"
        )
        validation_values = [
            float(row["result_validation_rate"])
            for row in completed
            if row.get("result_validation_rate", "") != ""
        ]
        aggregates[key] = {
            "complete_repetitions": len(completed),
            "expected_repetitions": expected,
            "fully_complete": bool(expected) and len(completed) == expected,
            "prepare_wall_ms": _median(completed, "prepare_wall_ms"),
            "query_wall_ms": _median(completed, "query_wall_ms"),
            "total_wall_ms": _median(completed, "total_wall_ms"),
            "total_wall_ms_min": _minimum(completed, "total_wall_ms"),
            "total_wall_ms_max": _maximum(completed, "total_wall_ms"),
            "total_process_cpu_ms": _median(
                completed, "total_process_cpu_ms"
            ),
            "total_current_rss_kib": _median(
                completed, "max_sum_node_current_rss_kib"
            ),
            "logical_input_triples": _median(
                completed, "logical_input_triples"
            ),
            "aggregate_fragment_triples": _median(
                completed, "aggregate_fragment_triples"
            ),
            "max_fragment_triples": _median(
                completed, "max_fragment_triples"
            ),
            "max_fragment_fraction": _median(
                completed, "max_fragment_fraction"
            ),
            "storage_replication_factor": _median(
                completed, "storage_replication_factor"
            ),
            "federation_fanout_factor": _median(
                completed, "federation_fanout_factor"
            ),
            "network_body_bytes": sum(
                value or 0.0
                for value in (
                    _median(completed, "prepare_request_bytes_sum"),
                    _median(completed, "prepare_response_bytes_sum"),
                    _median(completed, "query_request_bytes_sum"),
                    _median(completed, "query_response_bytes_sum"),
                )
            ),
            "semantic_valid": (
                bool(completed)
                and len(validation_values) == len(completed)
                and all(value == 1.0 for value in validation_values)
            ),
            "oracle_complete": (
                architecture == "monolith"
                or (
                    bool(completed)
                    and all(
                        row.get("oracle_status") == "completed"
                        for row in completed
                    )
                )
            ),
        }
    return aggregates, groups


def _timeout_lower_bound_ms(rows: list[dict[str, str]]) -> float | None:
    values = [
        float(row["timeout_seconds"]) * 1000
        for row in rows
        if row["status"] == "timeout"
        and row.get("timeout_seconds", "") != ""
    ]
    return min(values) if values else None


def analyze_distributed_ontology(root: Path) -> list[dict[str, Any]]:
    aggregates, raw_groups = _distributed_aggregates(root)
    output: list[dict[str, Any]] = []
    for architecture in DISTRIBUTED_ARCHITECTURES:
        points = sorted(
            (
                reasoner,
                users,
                values,
            )
            for (item_architecture, reasoner, users), values
            in aggregates.items()
            if item_architecture == architecture
        )
        for reasoner, users, distributed in points:
            monolith = aggregates.get(("monolith", reasoner, users), {})
            monolith_timeout_ms = _timeout_lower_bound_ms(
                raw_groups.get(("monolith", reasoner, users), [])
            )
            total_speedup = _ratio(
                monolith.get("total_wall_ms"),
                distributed["total_wall_ms"],
            )
            conservative_speedup = _ratio(
                monolith.get("total_wall_ms_min"),
                distributed["total_wall_ms_max"],
            )
            lower_bound = (
                monolith_timeout_ms / distributed["total_wall_ms"]
                if monolith_timeout_ms is not None
                and distributed["total_wall_ms"] not in {None, 0.0}
                else ""
            )
            performance_supported = bool(
                distributed["fully_complete"]
                and distributed["semantic_valid"]
                and (
                    (
                        isinstance(total_speedup, float)
                        and total_speedup > 1.0
                        and isinstance(conservative_speedup, float)
                        and conservative_speedup > 1.0
                    )
                    or (
                        isinstance(lower_bound, float)
                        and lower_bound > 1.0
                    )
                )
            )
            cpu_ratio = _ratio(
                distributed["total_process_cpu_ms"],
                monolith.get("total_process_cpu_ms"),
            )
            rss_ratio = _ratio(
                distributed["total_current_rss_kib"],
                monolith.get("total_current_rss_kib"),
            )
            output.append(
                {
                    "architecture": architecture,
                    "reasoner": reasoner,
                    "synthetic_users": users,
                    **{
                        f"distributed_{key}": value
                        for key, value in distributed.items()
                    },
                    "monolith_fully_complete": monolith.get(
                        "fully_complete", False
                    ),
                    "monolith_total_wall_ms": monolith.get(
                        "total_wall_ms", ""
                    ),
                    "monolith_timeout_lower_bound_ms": (
                        monolith_timeout_ms
                        if monolith_timeout_ms is not None
                        else ""
                    ),
                    "prepare_speedup_vs_monolith": _ratio(
                        monolith.get("prepare_wall_ms"),
                        distributed["prepare_wall_ms"],
                    ),
                    "query_speedup_vs_monolith": _ratio(
                        monolith.get("query_wall_ms"),
                        distributed["query_wall_ms"],
                    ),
                    "total_speedup_vs_monolith": total_speedup,
                    "total_speedup_conservative": conservative_speedup,
                    "total_speedup_lower_bound": lower_bound,
                    "cpu_cost_ratio_vs_monolith": cpu_ratio,
                    "rss_cost_ratio_vs_monolith": rss_ratio,
                    "largest_fragment_data_reduction": (
                        1.0 / distributed["max_fragment_fraction"]
                        if distributed["max_fragment_fraction"]
                        not in {None, 0.0}
                        else ""
                    ),
                    "cpu_efficiency_supported": (
                        isinstance(cpu_ratio, float) and cpu_ratio <= 1.0
                    ),
                    "rss_efficiency_supported": (
                        isinstance(rss_ratio, float) and rss_ratio <= 1.0
                    ),
                    "performance_claim_supported": performance_supported,
                }
            )
    return output


def _as_float(value: Any) -> float | None:
    return value if isinstance(value, float) else None


def build_claim_verdict(
    scale_out: list[dict[str, Any]],
    distributed: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    verdicts: list[dict[str, Any]] = []
    reasoners = sorted(
        {
            row["reasoner"]
            for row in (*scale_out, *distributed)
        }
    )
    for architecture in DISTRIBUTED_ARCHITECTURES:
        for reasoner in reasoners:
            scale_points = [
                row
                for row in scale_out
                if row["architecture"] == architecture
                and row["reasoner"] == reasoner
            ]
            highest_scale_point = max(
                scale_points,
                key=lambda row: int(row["node_count"]),
                default=None,
            )
            scale_candidates = [
                row
                for row in scale_points
                if row["fully_complete"]
                and row["semantic_equivalent_to_monolith"]
            ]
            scale_point = (
                highest_scale_point
                if highest_scale_point in scale_candidates
                else None
            )
            distributed_points = [
                row
                for row in distributed
                if row["architecture"] == architecture
                and row["reasoner"] == reasoner
            ]
            highest_distributed_point = max(
                distributed_points,
                key=lambda row: int(row["synthetic_users"]),
                default=None,
            )
            distributed_candidates = [
                row
                for row in distributed_points
                if row["distributed_fully_complete"]
                and row["distributed_semantic_valid"]
            ]
            distributed_point = (
                highest_distributed_point
                if highest_distributed_point in distributed_candidates
                else None
            )
            ordered_speedups = [
                (
                    int(row["synthetic_users"]),
                    _as_float(row["total_speedup_vs_monolith"])
                    or _as_float(row["total_speedup_lower_bound"]),
                )
                for row in sorted(
                    distributed_candidates,
                    key=lambda row: int(row["synthetic_users"]),
                )
            ]
            ordered_speedups = [
                item for item in ordered_speedups if item[1] is not None
            ]
            speedup_increases = (
                len(ordered_speedups) >= 2
                and ordered_speedups[-1][1] > ordered_speedups[0][1]
            )
            scale_supported = bool(
                scale_point
                and isinstance(
                    scale_point[
                        "throughput_speedup_conservative_vs_own_1_node"
                    ],
                    float,
                )
                and scale_point[
                    "throughput_speedup_conservative_vs_own_1_node"
                ] > 1
            )
            distributed_supported = bool(
                distributed_point
                and distributed_point["performance_claim_supported"]
            )
            if not scale_point or not distributed_point:
                verdict = "insufficient_data"
            elif scale_supported and distributed_supported:
                verdict = "supported"
            else:
                verdict = "not_supported"
            verdicts.append(
                {
                    "architecture": architecture,
                    "reasoner": reasoner,
                    "verdict": verdict,
                    "scale_out_supported": scale_supported,
                    "scale_out_nodes_evaluated": (
                        highest_scale_point["node_count"]
                        if highest_scale_point else ""
                    ),
                    "scale_out_throughput_speedup": (
                        scale_point["throughput_speedup_vs_own_1_node"]
                        if scale_point else ""
                    ),
                    "scale_out_conservative_speedup": (
                        scale_point[
                            "throughput_speedup_conservative_vs_own_1_node"
                        ]
                        if scale_point else ""
                    ),
                    "distributed_performance_supported": (
                        distributed_supported
                    ),
                    "highest_validated_users": (
                        distributed_point["synthetic_users"]
                        if distributed_point else ""
                    ),
                    "highest_attempted_users": (
                        highest_distributed_point["synthetic_users"]
                        if highest_distributed_point else ""
                    ),
                    "high_scale_total_speedup": (
                        (
                            distributed_point["total_speedup_vs_monolith"]
                            or distributed_point[
                                "total_speedup_lower_bound"
                            ]
                        )
                        if distributed_point
                        else ""
                    ),
                    "high_scale_conservative_speedup": (
                        (
                            distributed_point[
                                "total_speedup_conservative"
                            ]
                            or distributed_point[
                                "total_speedup_lower_bound"
                            ]
                        )
                        if distributed_point
                        else ""
                    ),
                    "speedup_increases_with_scale": speedup_increases,
                    "semantic_equivalence": bool(
                        scale_point
                        and distributed_point
                        and distributed_point["distributed_semantic_valid"]
                    ),
                    "cpu_efficiency_at_high_scale": bool(
                        distributed_point
                        and distributed_point["cpu_efficiency_supported"]
                    ),
                    "rss_efficiency_at_high_scale": bool(
                        distributed_point
                        and distributed_point["rss_efficiency_supported"]
                    ),
                }
            )
    return verdicts


def _report(
    root: Path,
    verdicts: list[dict[str, Any]],
) -> Path:
    path = root / "analysis" / "REPORT.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Verificación de la hipótesis continuum",
        "",
        "La hipótesis no se presupone: se acepta únicamente cuando el punto de "
        "mayor escala validado conserva equivalencia semántica, el scale-out "
        "aumenta throughput y el tiempo total distribuido es menor que el "
        "monolítico (o su límite inferior censurado).",
        "",
        "| Arquitectura | Razonador | Veredicto | Speedup consultas | "
        "Usuarios altos | Speedup total | Crece con escala | CPU eficiente | "
        "RSS eficiente |",
        "|---|---|---|---:|---:|---:|---|---|---|",
    ]
    for row in verdicts:
        lines.append(
            "| {architecture} | {reasoner} | {verdict} | {query} | "
            "{users} | {total} | {growth} | {cpu} | {rss} |".format(
                architecture=row["architecture"],
                reasoner=row["reasoner"],
                verdict=row["verdict"],
                query=(
                    f"{row['scale_out_throughput_speedup']:.3f}×"
                    if isinstance(
                        row["scale_out_throughput_speedup"], float
                    )
                    else "—"
                ),
                users=row["highest_validated_users"] or "—",
                total=(
                    f"{row['high_scale_total_speedup']:.3f}×"
                    if isinstance(row["high_scale_total_speedup"], float)
                    else "—"
                ),
                growth="sí" if row["speedup_increases_with_scale"] else "no",
                cpu="sí" if row["cpu_efficiency_at_high_scale"] else "no",
                rss="sí" if row["rss_efficiency_at_high_scale"] else "no",
            )
        )
    lines.extend(
        [
            "",
            "## Reglas de lectura",
            "",
            "- `supported` no significa que toda carga distribuida sea más "
            "rápida; significa que la hipótesis predefinida se cumple en el "
            "mayor punto comparable y validado.",
            "- `not_supported` es un resultado experimental válido: la "
            "distribución o el hardware no compensan su sobrecoste.",
            "- `insufficient_data` aparece si faltan repeticiones, equivalencia "
            "con el oráculo o un punto monolítico comparable/censurado.",
            "- CPU y RSS son criterios secundarios independientes; una mejora "
            "de tiempo no implica menor coste agregado.",
            "",
            "Tablas: `scale-out-comparison.csv`, `hardware-comparison.csv`, "
            "`distributed-comparison.csv` y `claim-verdict.csv`.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def analyze_experiments(root: Path) -> list[Path]:
    scale_out = analyze_scale_out(root)
    hardware = analyze_reasoning_hardware(root)
    distributed = analyze_distributed_ontology(root)
    verdicts = build_claim_verdict(scale_out, distributed)
    output = root / "analysis"
    paths: list[Path] = []
    if scale_out:
        path = output / "scale-out-comparison.csv"
        write_dict_rows(path, scale_out, empty_message="No scale-out rows")
        paths.append(path)
    if hardware:
        path = output / "hardware-comparison.csv"
        write_dict_rows(path, hardware, empty_message="No hardware rows")
        paths.append(path)
    if distributed:
        path = output / "distributed-comparison.csv"
        write_dict_rows(
            path, distributed, empty_message="No distributed rows"
        )
        paths.append(path)
    if verdicts:
        path = output / "claim-verdict.csv"
        write_dict_rows(path, verdicts, empty_message="No verdict rows")
        paths.append(path)
        paths.append(_report(root, verdicts))
    return paths
