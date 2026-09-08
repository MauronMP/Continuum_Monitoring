from continuum_bench.load_reporting import (
    _architecture_ratios,
    _plot_reference_overview,
    _reference_summary,
)


def _row(architecture: str, *, latency: float, throughput: float):
    return {
        "architecture": architecture,
        "dimension": "users",
        "profile": "users-100",
        "reasoner": "rdfs",
        "comparison_eligible": True,
        "synthetic_users_median": 100,
        "node_count_median": 1 if architecture == "local" else 5,
        "latency_p95_ms_median": latency,
        "events_processed_per_second_median": throughput,
        "inference_wall_ms_median": 20,
        "recovery_wall_ms_median": 10,
        "event_loss_percent_median": 0,
    }


def test_distributed_architecture_ratios_use_matched_monolith_baseline():
    rows = _architecture_ratios(
        [
            _row("local", latency=100, throughput=100),
            _row("docker", latency=50, throughput=200),
            _row("physical", latency=200, throughput=50),
        ]
    )

    docker = next(row for row in rows if row["architecture"] == "docker")
    physical = next(row for row in rows if row["architecture"] == "physical")
    assert docker["latency_speedup"] == 2
    assert docker["throughput_gain"] == 2
    assert docker["baseline_architecture"] == "local"
    assert docker["scale_out_efficiency_percent"] == 40
    assert physical["latency_speedup"] == 0.5
    assert physical["throughput_gain"] == 0.5
    assert physical["scale_out_efficiency_percent"] == 10


def test_reference_overview_accepts_partial_architecture_matrix(tmp_path):
    rows = [
        {
            "architecture": "local",
            "reasoner": "rdfs",
            "dimension": "events_per_second",
            "comparison_eligible": True,
            "profile": profile,
            "events_per_second_median": eps,
            "events_processed_per_second_median": eps,
            "event_loss_percent_median": loss,
            "latency_p95_seconds_median": 0.1,
            "cpu_percent_per_node_one_core_median": 10,
            "max_current_rss_mib_median": 50,
            "inference_wall_seconds_median": 0.2,
            "recovery_wall_seconds_median": 0.05,
        }
        for profile, eps, loss in (
            ("eps-200", 200, 2),
            ("eps-2500", 2500, 5),
        )
    ]

    summary = _reference_summary(rows)
    assert summary[0]["max_tested_loss_free_eps"] == ""

    outputs = _plot_reference_overview(
        summary,
        tmp_path,
        {"local": "tab:blue", "docker": "tab:orange", "physical": "tab:green"},
    )
    assert len(outputs) == 3
    assert all(path.is_file() for path in outputs)
