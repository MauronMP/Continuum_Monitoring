import csv
from dataclasses import replace

import pytest

from continuum_bench.benchmark import run_cumulative


def _rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.smoke_cumulative
def test_cumulative_smoke_adds_every_category_and_finishes_with_all_queries(
    config,
    tmp_path,
    capsys,
):
    local = replace(
        config,
        output_dir=tmp_path,
        reasoners=("rdfs",),
        repetitions=1,
    )
    output = run_cumulative(local)
    rows = _rows(output / "summary.csv")

    assert [row["added_category"] for row in rows] == list(
        config.category_order
    )
    query_counts = [int(row["query_count"]) for row in rows]
    assert query_counts == sorted(query_counts)
    assert query_counts[-1] == 115

    detail = _rows(output / "query-runs.csv")
    final_stage_ids = {
        row["query_id"] for row in detail if int(row["stage"]) == len(rows)
    }
    assert len(final_stage_ids) == 115
    assert all(len(row["result_digest"]) == 64 for row in detail)

    terminal = capsys.readouterr().out
    assert "[cumulative]" in terminal
    assert "reasoner=rdfs" in terminal
    assert "category=topology" in terminal
    assert "category=wellbeing" in terminal
    final_stage = len(config.category_order)
    assert f"stage={final_stage}/{final_stage}" in terminal
