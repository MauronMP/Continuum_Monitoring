from __future__ import annotations

import re

from ..queries import QuerySpec
from .models import QueryFeatures


_TRIPLE_PATTERN = re.compile(
    r"(?:^|[.;{]\s*)"
    r"(?:\?[A-Za-z_][A-Za-z0-9_]*|<[^>]+>|(?:[A-Za-z_][\w-]*)?:[\w-]+|a)\s+"
    r"(?:\?[A-Za-z_][A-Za-z0-9_]*|<[^>]+>|(?:[A-Za-z_][\w-]*)?:[\w-]+|a)\s+"
    r"(?:\?[A-Za-z_][A-Za-z0-9_]*|<[^>]+>|(?:[A-Za-z_][\w-]*)?:[\w-]+|\"[^\"]*\"|[0-9.]+)",
    re.MULTILINE,
)


def characterize_query(spec: QuerySpec) -> QueryFeatures:
    text = _strip_comments(spec.read())
    upper = text.upper()
    variables = re.findall(r"\?[A-Za-z_][A-Za-z0-9_]*", text)
    repeated_variables = {
        variable for variable in variables if variables.count(variable) > 1
    }
    triple_patterns = len(_TRIPLE_PATTERN.findall(text))
    filters = upper.count("FILTER")
    optional_clauses = upper.count("OPTIONAL")
    union_clauses = upper.count("UNION")
    aggregations = sum(
        upper.count(function)
        for function in ("COUNT(", "SUM(", "AVG(", "MIN(", "MAX(")
    )
    joins = max(0, len(repeated_variables) - 1)
    distinct = "DISTINCT" in upper
    group_by = "GROUP BY" in upper
    order_by = "ORDER BY" in upper
    limit_offset = "LIMIT" in upper or "OFFSET" in upper
    basic_graph_patterns = max(1, text.count("{"))
    if aggregations or group_by:
        query_shape = "aggregate"
    elif union_clauses:
        query_shape = "complex"
    elif joins >= 3:
        query_shape = "multi_join"
    elif triple_patterns == 1:
        query_shape = "lookup"
    elif joins == 0:
        query_shape = "linear"
    elif triple_patterns >= 3:
        query_shape = "star"
    else:
        query_shape = "snowflake"
    structural_complexity = (
        triple_patterns
        + 1.5 * joins
        + 2.0 * filters
        + 2.0 * optional_clauses
        + 2.5 * union_clauses
        + 2.0 * aggregations
        + (1.0 if distinct else 0.0)
        + (1.0 if group_by else 0.0)
        + (1.0 if order_by else 0.0)
        + (0.5 if limit_offset else 0.0)
    )
    return QueryFeatures(
        query_id=spec.id,
        category=spec.category,
        policy_count=len(spec.policies),
        triple_patterns=triple_patterns,
        joins=joins,
        filters=filters,
        optional_clauses=optional_clauses,
        union_clauses=union_clauses,
        distinct=distinct,
        aggregations=aggregations,
        group_by=group_by,
        order_by=order_by,
        limit_offset=limit_offset,
        basic_graph_patterns=basic_graph_patterns,
        query_shape=query_shape,
        structural_complexity=structural_complexity,
    )


def _strip_comments(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )
