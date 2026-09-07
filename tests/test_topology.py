from continuum_bench.topology import load_topology, load_topology_manifest


def test_physical_manifest_loads_layered_nodes(config):
    manifest = load_topology_manifest(config.resolve(config.topology_file))

    assert set(manifest.topologies) == {"physical"}
    topology = manifest.topology("physical")
    assert topology.kind == "physical"
    assert len(topology.active_nodes) == 5
    assert topology.node("cloud").local is True
    assert topology.node("edge1").authority is True


def test_physical_nodes_expose_resources_and_location(config):
    topology = load_topology(config.resolve(config.topology_file), "physical")
    cloud = topology.node("cloud")
    edge = topology.node("edge1")

    assert cloud.cpus >= 1
    assert cloud.memory.endswith("g")
    assert cloud.storage_mib > 0
    assert cloud.network_mbps > 0
    assert cloud.region == "local-lab"
    assert edge.device_type == "raspberry-pi-500"
    assert edge.processing_capacity > 0


def test_topology_public_shape_is_physical_only(config):
    topology = load_topology(config.resolve(config.topology_file), "physical")
    value = topology.public()

    assert value["name"] == "physical"
    assert value["tier_counts"]["cloud"] == 1
    assert value["tier_counts"]["edge"] == 3
    assert "fingerprint" in value
