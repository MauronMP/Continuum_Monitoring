from __future__ import annotations

import csv

import pytest

from continuum_bench.engine_reporting import (
    ENGINE_ORDER,
    plot_engine_benchmarks,
)


def _summary(path, *, missing: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "engine",
        "status",
        "stage",
        "synthetic_users",
        "engine_total_ms",
        "query_ms",
        "reasoning_ms",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, engine in enumerate(ENGINE_ORDER, start=1):
            if engine == missing:
                continue
            writer.writerow(
                {
                    "engine": engine,
                    "status": "completed",
                    "stage": 1,
                    "synthetic_users": 5,
                    "engine_total_ms": 10 + index,
                    "query_ms": 5 + index,
                    "reasoning_ms": index,
                }
            )


def test_engine_figures_require_and_show_all_products(tmp_path):
    _summary(tmp_path / "cumulative/summary.csv")

    outputs = plot_engine_benchmarks(tmp_path, ("cumulative",))

    assert {path.suffix for path in outputs} == {".png"}
    assert all(path.stat().st_size > 0 for path in outputs)


def test_engine_figures_reject_missing_product(tmp_path):
    _summary(tmp_path / "scalability/summary.csv", missing="jena")

    with pytest.raises(ValueError, match="jena"):
        plot_engine_benchmarks(tmp_path, ("scalability",))
