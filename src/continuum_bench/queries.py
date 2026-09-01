from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from time import perf_counter_ns
import tomllib
from typing import Iterable

from rdflib import Graph, Literal
from rdflib.namespace import XSD


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
    expected_count: int | None = None
    expected_ask: bool | None = None
    purpose: str = ""
    requirements: tuple[str, ...] = ()
    policies: tuple[str, ...] = ()
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
    """Return an order-independent digest of the canonical result set."""
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
        if str(plan.get("version", "")) != "3.0.0":
            raise ValueError(
                f"{plan_path}: expected execution plan version '3.0.0', "
                f"got {plan.get('version')!r}"
            )
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

    def identifiers(value: str | None) -> tuple[str, ...]:
        return tuple(
            item.strip() for item in (value or "").split(",")
            if item.strip()
        )

    def optional_bool(value: str | None) -> bool | None:
        normalized = (value or "").strip().lower()
        if not normalized:
            return None
        if normalized not in {"true", "false"}:
            raise ValueError(f"Invalid catalog boolean: {value!r}")
        return normalized == "true"

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
            expected_count=(
                int(row["expected_count"])
                if row.get("expected_count", "").strip()
                else None
            ),
            expected_ask=optional_bool(row.get("expected_ask")),
            purpose=row.get("purpose", "").strip(),
            requirements=identifiers(row.get("requirements")),
            policies=identifiers(row.get("policies")),
            execution_scope=row.get("execution_scope")
            or scopes.get(row["id"], "cloud"),
            authority=row.get("authority")
            or {
                "cloud": "global",
                "fog": "regional",
                "mist": "near_edge",
                "edge": "data_owner_tier",
                "iot": "data_owner_tier",
                "authorities": "data_owner",
                "cloud_authorities": "federated",
                "all": "federated_all",
            }.get(
                scopes.get(row["id"], "cloud"),
                (
                    "data_owner"
                    if scopes.get(row["id"], "").startswith("authority_key:")
                    else "global"
                ),
            ),
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
                    in {"authorities", "cloud_authorities", "all"}
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
    allowed_scopes = {
        "cloud", "fog", "mist", "edge", "iot", "authorities",
        "cloud_authorities", "all",
    }
    allowed_privacy = {"internal", "confidential", "restricted"}
    allowed_merge = {"single", "set_union", "boolean_or"}
    for spec in specs:
        if (
            spec.execution_scope not in allowed_scopes
            and not spec.execution_scope.startswith("node:")
            and not spec.execution_scope.startswith("authority_key:")
        ):
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
            "authorities",
            "cloud_authorities",
            "all",
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
    query_text = spec.read()
    result = graph.query(query_text)
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
        has_group_concat = "GROUP_CONCAT" in query_text.upper()

        def canonical_value(value: object | None) -> str:
            if value is None:
                return ""
            if has_group_concat and isinstance(value, Literal):
                lexical = str(value)
                if ", " in lexical:
                    normalized = ", ".join(sorted(lexical.split(", ")))
                    value = Literal(
                        normalized,
                        lang=value.language,
                        datatype=value.datatype,
                    )
            if isinstance(value, Literal) and value.datatype in {
                XSD.decimal,
                XSD.double,
                XSD.float,
                XSD.integer,
                XSD.int,
                XSD.long,
                XSD.short,
                XSD.nonNegativeInteger,
                XSD.positiveInteger,
                XSD.nonPositiveInteger,
                XSD.negativeInteger,
            }:
                python_value = value.toPython()
                if isinstance(python_value, Decimal):
                    lexical = format(python_value.normalize(), "f")
                    if "." not in lexical:
                        lexical += ".0"
                else:
                    lexical = str(python_value)
                value = Literal(lexical, datatype=value.datatype, normalize=False)
            return value.n3()  # type: ignore[union-attr]

        for row in result:
            values = tuple(
                canonical_value(value)
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
                            canonical_value(row[0])
                        )
                    ).encode("utf-8")
                ).hexdigest()
            )
        # Distributed execution uses set-union. Canonical set semantics avoids
        # false disagreement from RDFS producing numerically equivalent lexical
        # forms (for example 0.25 and 0.250000) or duplicate solution rows.
        group_keys = tuple(sorted(set(groups)))
        result_keys = tuple(sorted(set(keys)))
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
    if (
        spec.expected_count is not None
        and measurement.result_count != spec.expected_count
    ):
        return (
            f"{spec.id}: expected reference cardinality "
            f"{spec.expected_count}, got {measurement.result_count}"
        )
    if (
        spec.expected_ask is not None
        and measurement.ask_result is not spec.expected_ask
    ):
        return (
            f"{spec.id}: expected ASK {spec.expected_ask}, "
            f"got {measurement.ask_result}"
        )
    if spec.expectation == "zero_rows" and measurement.result_count != 0:
        return f"{spec.id}: expected zero rows, got {measurement.result_count}"
    if spec.expectation == "non_empty" and measurement.result_count == 0:
        return f"{spec.id}: expected a non-empty result"
    if spec.expectation == "true" and measurement.ask_result is not True:
        return f"{spec.id}: expected ASK true, got {measurement.ask_result}"
    if spec.expectation == "false" and measurement.ask_result is not False:
        return f"{spec.id}: expected ASK false, got {measurement.ask_result}"
    return None


def by_categories(
    specs: Iterable[QuerySpec], categories: set[str]
) -> list[QuerySpec]:
    return [spec for spec in specs if spec.category in categories]
