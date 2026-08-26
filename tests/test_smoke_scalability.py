import csv
from dataclasses import replace

import pytest

from continuum_bench.benchmark import run_scalability


def _rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.smoke_scalability
def test_scalability_smoke_grows_the_graph_and_runs_the_full_battery(
    config,
    tmp_path,
    capsys,
):
    local = replace(
        config,
        output_dir=tmp_path,
        reasoners=("rdfs",),
        scale_users=(2, 4),
        repetitions=1,
    )
    output = run_scalability(local)
    rows = _rows(output / "summary.csv")

    assert [int(row["synthetic_users"]) for row in rows] == [2, 4]
    assert int(rows[1]["input_triples"]) > int(rows[0]["input_triples"])
    assert all(int(row["query_count"]) == 69 for row in rows)

    detail = _rows(output / "query-runs.csv")
    for users in (2, 4):
        query_ids = {
            row["query_id"]
            for row in detail
            if int(row["synthetic_users"]) == users
        }
        assert len(query_ids) == 69
    assert all(len(row["result_digest"]) == 64 for row in detail)

    terminal = capsys.readouterr().out
    assert "[scalability]" in terminal
    assert "block=1/2" in terminal
    assert "block=2/2" in terminal
    assert "users=2" in terminal
    assert "users=4" in terminal
    assert "reasoner=rdfs" in terminal
