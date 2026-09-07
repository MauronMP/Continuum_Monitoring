# Elastic Docker and Physical Topologies

To add a node, choose `configs/topologies/docker` or
`configs/topologies/physical`, edit its tier file and add `[[nodes]]`.

Example edge node:

```toml
[[nodes]]
id = "edge4"
device_type = "raspberry-pi-500"
host = "192.168.1.141"
endpoint = "http://192.168.1.141:8391"
local = false
port = 8391
authority = true

[nodes.resources]
cpu_cores = 4
ram = "2g"
storage_mib = 32768
processing_capacity = 0.40
network_mbps = 100

[nodes.location]
latitude = 0.0
longitude = 0.0
altitude_m = 0.0
region = "physical-lab"
```

Rules:

- Node identifiers must be unique.
- Endpoints must be unique.
- At least one cloud node must exist.
- At least one authority node must exist for privacy-aware partitioning.
- Docker host ports must be unique and all endpoints local.
- Physical requires a local coordinator and safe dedicated remote paths.

Validate after every change:

```bash
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench topology show
.venv/bin/continuum-bench --topology-file \
  configs/topologies/docker/topology.toml topology validate --name docker
```

Docker Compose is generated dynamically, so node-count changes require no YAML
or Python edits. Physical deployment iterates the same node model over SSH.
