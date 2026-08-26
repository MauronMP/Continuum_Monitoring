from __future__ import annotations

import csv
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from time import perf_counter_ns
import tomllib
from typing import Iterable

from rdflib import Graph


@dataclass(frozen=True)
class QuerySpec:
    order: int
    id: str
    tier: str
    category: str
    kind: str
    expectation: str
    path: Path
    title: str
    execution_scope: str = "cloud"
    authority: str = "global"
    privacy_class: str = "internal"
    merge_strategy: str = "single"

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


@dataclass(frozen=True)
class QueryMeasurement:
    query_id: str
    category: str
    tier: str
    duration_ms: float
    result_count: int
    ask_result: bool | None
    result_digest: str = ""


@dataclass(frozen=True)
class QueryExecution:
    measurement: QueryMeasurement
    result_keys: tuple[str, ...]
    group_keys: tuple[str, ...]


def result_digest(
    result_keys: Iterable[str],
    ask_result: bool | None,
) -> str:
    """Return an order-independent digest that preserves bag cardinality."""
    if ask_result is not None:
        payload = f"ASK:{str(ask_result).lower()}"
    else:
        payload = "\n".join(sorted(result_keys))
    return sha256(payload.encode("utf-8")).hexdigest()


def load_catalog(catalog_path: Path, root: Path) -> list[QuerySpec]:
    with catalog_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    plan_path = catalog_path.with_name("execution-plan.toml")
    plan = {"scopes": {}, "privacy": {}, "merge": {}}
    if plan_path.is_file():
        with plan_path.open("rb") as handle:
            plan = tomllib.load(handle)
    def invert(section: str) -> dict[str, str]:
        output: dict[str, str] = {}
        for value, query_ids in plan.get(section, {}).items():
            for query_id in query_ids:
                if query_id in output:
                    raise ValueError(
                        f"{query_id} appears more than once in [{section}]"
                    )
                output[str(query_id)] = str(value)
        return output

    scopes = invert("scopes")
    privacy = invert("privacy")
    merge = invert("merge")

    specs = [
        QuerySpec(
            order=int(row["order"]),
            id=row["id"],
            tier=row["tier"],
            category=row["category"],
            kind=row["kind"],
            expectation=row["expectation"],
            path=root / row["path"],
            title=row["title"],
            execution_scope=row.get("execution_scope")
            or scopes.get(row["id"], "cloud"),
            authority=row.get("authority")
            or {
                "cloud": "global",
                "fog": "regional",
                "edges": "data_owner",
                "cloud_edges": "federated",
            }.get(scopes.get(row["id"], "cloud"), "global"),
            privacy_class=row.get("privacy_class")
            or privacy.get(row["id"], "internal"),
            merge_strategy=row.get("merge_strategy")
            or merge.get(row["id"])
            or (
                "boolean_or"
                if row["kind"] == "ask"
                else (
                    "set_union"
                    if scopes.get(row["id"], "cloud")
                    in {"edges", "cloud_edges"}
                    else "single"
                )
            ),
        )
        for row in rows
    ]
    ids = [spec.id for spec in specs]
    if len(ids) != len(set(ids)):
        raise ValueError("The query catalog contains duplicate IDs")
    missing = [str(spec.path) for spec in specs if not spec.path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing query files: {missing}")
    planned_ids = set(scopes)
    unknown_planned = planned_ids - set(ids)
    unplanned = set(ids) - planned_ids
    unknown_merge = set(merge) - set(ids)
    if unknown_planned or unplanned or unknown_merge:
        raise ValueError(
            "Execution plan/catalog mismatch: "
            f"unknown={sorted(unknown_planned)}, "
            f"unplanned={sorted(unplanned)}, "
            f"unknown_merge={sorted(unknown_merge)}"
        )
    allowed_scopes = {"cloud", "fog", "edges", "cloud_edges"}
    allowed_privacy = {"internal", "confidential", "restricted"}
    allowed_merge = {"single", "set_union", "boolean_or"}
    for spec in specs:
        if spec.execution_scope not in allowed_scopes:
            raise ValueError(
                f"{spec.id}: invalid execution scope "
                f"{spec.execution_scope!r}"
            )
        if spec.privacy_class not in allowed_privacy:
            raise ValueError(
                f"{spec.id}: invalid privacy class {spec.privacy_class!r}"
            )
        if spec.merge_strategy not in allowed_merge:
            raise ValueError(
                f"{spec.id}: unsafe/unknown merge strategy "
                f"{spec.merge_strategy!r}"
            )
        if spec.merge_strategy == "single" and spec.execution_scope in {
            "edges",
            "cloud_edges",
        }:
            raise ValueError(
                f"{spec.id}: multi-source scope requires a merge strategy"
            )
        if spec.kind == "ask" and spec.merge_strategy != "boolean_or":
            raise ValueError(
                f"{spec.id}: ASK queries require boolean_or"
            )
    return sorted(specs, key=lambda spec: spec.order)


def execute_query_detailed(graph: Graph, spec: QuerySpec) -> QueryExecution:
    started = perf_counter_ns()
    result = graph.query(spec.read())
    if result.type == "ASK":
        ask_result = bool(result.askAnswer)
        result_count = int(ask_result)
        result_keys = ("true",) if ask_result else ()
        group_keys = ()
    else:
        ask_result = None
        variables = tuple(str(variable) for variable in result.vars)
        keys = []
        groups = []
        for row in result:
            values = tuple(
                value.n3() if value is not None else ""
                for value in row
            )
            canonical = "\u001f".join(
                (*variables, "\u001e", *values)
            )
            keys.append(sha256(canonical.encode("utf-8")).hexdigest())
            groups.append(
                sha256(
                    (
                        variables[0]
                        + "\u001e"
                        + (
                            row[0].n3()
                            if row[0] is not None
                            else ""
                        )
                    ).encode("utf-8")
                ).hexdigest()
            )
        group_keys = tuple(groups)
        result_keys = tuple(keys)
        result_count = len(result_keys)
    duration_ms = (perf_counter_ns() - started) / 1_000_000
    return QueryExecution(
        measurement=QueryMeasurement(
            query_id=spec.id,
            category=spec.category,
            tier=spec.tier,
            duration_ms=duration_ms,
            result_count=result_count,
            ask_result=ask_result,
            result_digest=result_digest(result_keys, ask_result),
        ),
        result_keys=result_keys,
        group_keys=group_keys,
    )


def execute_query(graph: Graph, spec: QuerySpec) -> QueryMeasurement:
    return execute_query_detailed(graph, spec).measurement


def check_expectation(spec: QuerySpec, measurement: QueryMeasurement) -> str | None:
    if spec.expectation == "zero_rows" and measurement.result_count != 0:
        return f"{spec.id}: expected zero rows, got {measurement.result_count}"
    if spec.expectation == "non_empty" and measurement.result_count == 0:
        return f"{spec.id}: expected a non-empty result"
    if spec.expectation == "true" and measurement.ask_result is not True:
        return f"{spec.id}: expected ASK true, got {measurement.ask_result}"
    return None


def by_categories(
    specs: Iterable[QuerySpec], categories: set[str]
) -> list[QuerySpec]:
    return [spec for spec in specs if spec.category in categories]
