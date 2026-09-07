from continuum_bench.load_reporting import _architecture_ratios


def _row(architecture: str, *, latency: float, throughput: float):
    return {
        "architecture": architecture,
        "dimension": "users",
        "profile": "users-100",
        "reasoner": "rdfs",
        "comparison_eligible": True,
        "synthetic_users_median": 100,
        "node_count_median": 5,
        "latency_p95_ms_median": latency,
        "events_processed_per_second_median": throughput,
        "inference_wall_ms_median": 20,
        "recovery_wall_ms_median": 10,
        "event_loss_percent_median": 0,
    }


def test_architecture_ratios_are_symmetric_and_workload_matched():
    rows = _architecture_ratios(
        [
            _row("docker", latency=50, throughput=200),
            _row("physical", latency=100, throughput=100),
        ]
    )

    docker = next(row for row in rows if row["architecture"] == "docker")
    physical = next(row for row in rows if row["architecture"] == "physical")
    assert docker["latency_speedup"] == 2
    assert docker["throughput_gain"] == 2
    assert docker["scale_out_efficiency_percent"] == 200
    assert physical["latency_speedup"] == 0.5
    assert physical["throughput_gain"] == 0.5
