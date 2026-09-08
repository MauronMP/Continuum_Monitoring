from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
import random

import pytest

from continuum_bench.study import analyze_category_costs, generate_study_trace
from continuum_bench.study.config import load_study_config
from continuum_bench.study.mobility import build_mobility_strategy
from continuum_bench.study.workload import _arrival_times, _choose_category
from continuum_bench.study.sparql import characterize_query
from continuum_bench.queries import load_catalog


def test_policy_cost_study_config_loads(config):
    study = load_study_config(config.root / "configs/policy-cost-study.toml")

    assert study.request_count >= 1
    assert study.workload.category_distribution == "zipf"
    assert study.mobility.model == "static"
    assert study.network.model == "distance_aware"


def test_query_characterization_uses_real_catalog(config):
    spec = next(
        spec
        for spec in load_catalog(
            config.resolve(config.query_catalog),
            config.root,
        )
        if spec.id == "EXT-Q70"
    )
    features = characterize_query(spec)

    assert features.query_id == "EXT-Q70"
    assert features.category == "audit_temporal"
    assert features.triple_patterns > 0
    assert features.structural_complexity >= features.triple_patterns


def test_generate_study_trace_is_reproducible(config, tmp_path):
    study = load_study_config(config.root / "configs/policy-cost-study.toml")

    first = generate_study_trace(config, study, tmp_path / "first")
    second = generate_study_trace(config, study, tmp_path / "second")

    assert Path(first[0]).read_text(encoding="utf-8") == Path(
        second[0]
    ).read_text(encoding="utf-8")
    with Path(first[0]).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == study.request_count
    assert {"policy_category", "policy_id", "query_id"} <= set(rows[0])
    assert {
        "client_x_m",
        "client_y_m",
        "estimated_network_latency_ms",
        "associated_edge",
        "connectivity_state",
        "handover_event",
    } <= set(rows[0])






def test_category_cost_analysis_joins_query_metadata(config, tmp_path):
    events = tmp_path / "event-runs.csv"
    events.write_text(
        "\n".join(
            [
                "query_id,processed,lost_reason,latency_ms,engine_duration_ms",
                "BASE-Q26,true,,12.0,3.0",
                "BASE-Q26,false,timeout,,",
                "EXT-Q03,true,,30.0,10.0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    outputs = analyze_category_costs(config, events, tmp_path / "analysis")

    assert {path.name for path in outputs} == {
        "category-cost-summary.csv",
        "policy-cost-summary.csv",
        "query-cost-summary.csv",
    }
    category_summary = (tmp_path / "analysis" / "category-cost-summary.csv")
    assert "observability" in category_summary.read_text(encoding="utf-8")
    assert "policy_governance" in category_summary.read_text(encoding="utf-8")
    with (
        tmp_path / "analysis" / "policy-cost-summary.csv"
    ).open(encoding="utf-8", newline="") as handle:
        policy_rows = list(csv.DictReader(handle))
    assert sum(
        float(row["attributed_request_equivalents"]) for row in policy_rows
    ) == pytest.approx(3.0)
    assert sum(float(row["popularity_share"]) for row in policy_rows) == (
        pytest.approx(1.0)
    )


def test_static_positions_are_reproducible(config):
    study = load_study_config(config.root / "configs/policy-cost-study.toml")
    model = build_mobility_strategy(study.mobility)
    a, b = model.position_at("client1", 0), model.position_at("client1", 20)
    assert (a.x_m,a.y_m) == (b.x_m,b.y_m)

@pytest.mark.parametrize("name", ["random_waypoint", "random_walk", "manhattan_grid", "gauss_markov"])
def test_future_mobility_requires_an_explicit_plugin(config, name):
    study = load_study_config(config.root / "configs/policy-cost-study.toml")
    with pytest.raises(ValueError, match="future plugin"):
        build_mobility_strategy(replace(study.mobility, model=name))


def test_trace_arrivals_are_replayed_exactly(config, tmp_path):
    study = load_study_config(config.root / "configs/policy-cost-study.toml")
    trace = tmp_path / "arrivals.csv"
    trace.write_text(
        "scheduled_timestamp_s\n0.1\n0.4\n1.2\n",
        encoding="utf-8",
    )
    workload = replace(
        study.workload,
        arrival_model="trace",
        trace_path=trace.name,
    )
    replay = replace(
        study,
        path=tmp_path / "study.toml",
        request_count=3,
        workload=workload,
    )

    assert _arrival_times(replay) == [0.1, 0.4, 1.2]


def test_weighted_category_selection_respects_zero_weights(config):
    study = load_study_config(config.root / "configs/policy-cost-study.toml")
    workload = replace(
        study.workload,
        category_distribution="weighted",
        category_weights={"selected": 1.0, "excluded": 0.0},
    )
    weighted = replace(study, workload=workload)
    rng = random.Random(123)
    observed = {
        _choose_category(weighted, ["selected", "excluded"], rng, index)
        for index in range(100)
    }
    assert observed == {"selected"}
