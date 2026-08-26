from continuum_bench.distributed import Endpoint
from continuum_bench.physical import (
    balanced_assignment,
    inventory_endpoints,
)
from continuum_bench.queries import load_catalog


def test_physical_inventory_has_expected_addresses(config):
    endpoints = inventory_endpoints(
        config.root / "configs" / "physical-nodes.toml"
    )

    assert endpoints == [
        "http://127.0.0.1:8391",
        "http://192.168.1.137:8391",
        "http://192.168.1.138:8391",
        "http://192.168.1.139:8391",
        "http://192.168.1.140:8391",
    ]


def test_balancer_assigns_every_query_once_and_uses_fast_node(config):
    specs = load_catalog(config.resolve(config.query_catalog), config.root)[:10]
    endpoints = [
        Endpoint("http://cloud", "cloud"),
        Endpoint("http://fog", "fog"),
        Endpoint("http://edge1", "edge1"),
        Endpoint("http://edge2", "edge2"),
        Endpoint("http://edge3", "edge3"),
    ]
    calibration = {
        endpoint.url: {
            spec.id: {
                "duration_ms": 1.0 if endpoint.role == "cloud" else 10.0
            }
            for spec in specs
        }
        for endpoint in endpoints
    }

    assignment, predicted = balanced_assignment(
        specs,
        endpoints,
        calibration,
    )
    query_ids = [
        spec.id for assigned in assignment.values() for spec in assigned
    ]

    assert len(query_ids) == len(specs)
    assert len(set(query_ids)) == len(specs)
    assert len(assignment["http://cloud"]) > len(assignment["http://fog"])
    assert all(value >= 0 for value in predicted.values())
