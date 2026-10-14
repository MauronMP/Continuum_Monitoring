# Physical continuum

## Inventory and network

The maintained deployment has six enabled nodes: Cloud `100.86.63.53`, Fog
`100.93.73.27`, Mist `100.72.111.107`, Edge 1 `100.101.178.35`, Edge 2
`100.70.9.117`, and Edge 3 `100.121.135.60`. Remote workers are Raspberry Pi 500
hosts; Cloud is the x86_64 coordinator. No five-node fallback is maintained.

`configs/topologies/physical/topology.toml` references the tier-specific node files.
Static resources describe CPU, RAM, storage, capacity and nominal network rate.
Runtime observations are separate; measured CPU/RSS must not overwrite capacity.
`network_mbps` never caps bandwidth. Physical campaigns use actual geographically
distributed Tailscale connections without traffic shaping. Region placeholders
are not measured coordinates, and analytical link models are not measurements.

## Placement

`replicated` prepares the complete application workload on each selected worker.
`distributed` prepares authority-aware instance fragments and tier-specific schema,
then merges routed query results. Shared schema can be repeated; there is no
shared-memory mode. [Ontology distribution](ONTOLOGY_DISTRIBUTION.md) contains the
exact file matrix and production/privacy limitations.

## Lifecycle

[Installation](INSTALLATION.md) documents setup and synchronization.
[Complete execution](COMPLETE_EXECUTION.md) lists the full and complementary commands
for both evaluation batteries. Check all six workers before acquisition. Code,
topology and semantic fingerprints must match the coordinator.

The HTTP worker is single-threaded because native timeout handling uses the main
thread. A health request can time out while reasoning is busy; that does not prove
the host is offline. SSH inspection can distinguish a running child process from
a missing service. A separate liveness plane remains unimplemented.

The managed stop helper waits five seconds. Old workers can disappear later,
causing exit 22 during startup; inspect and retry after exit. Never stop unrelated
processes. The coordinator's physical lease prevents local overlapping campaigns,
not jobs launched from another coordinator.

## Capacity and operating-system limits

The existing Pi deployment has a 64-bit kernel with 32-bit userspace/native
Konclude. Large replicated workloads have produced address-space allocation
failures despite available host RAM. Bounded timeouts preserve later independent
observations but do not solve memory exhaustion. A new 64-bit installation needs
its own validated runtime and fresh experiment evidence.

Supplied-context adaptation, fragment inference and worker-state reconstruction
are distinct from a production service's fault recovery. Do not combine them
under one recovery-latency claim. Historical results retain their own topology,
versions and validation status; a successful current health check cannot upgrade
an earlier incomplete experiment.
