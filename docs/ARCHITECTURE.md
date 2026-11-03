# Architecture

The project has two independent experiments and two implementation planes. Python validates configuration, manages the physical topology and Docker, controls repetitions, records metrics, and creates reports. Rust performs RDF parsing, deterministic serialization, RDFS closure, SPARQL, digests, dataset generation, and HTTP serving.

An independent `continuous_monitoring` control-plane module reuses the same workers, semantic preparation, routing, fan-out and resource sampler. Its fixed-rate scheduler maps existing policy identifiers to configured `MonitoringTask` query sets and measures deployed-idle versus active periodic operation. It does not alter the scalability runner or implement autonomous demand selection or infrastructure adaptation.

The Rust workspace contains `continuum-rdf`, `continuum-rdf-tool`, and the Axum/Tokio `continuum-worker`. A capacity-one semaphore serializes semantic work. `/health` reports identity, protocol/build data, Rust version and target, semantic fingerprints, queue depth, active requests, idle state, and graph digests. `/reset`, `/prepare`, and `/query` form the measured protocol. Python accepts a worker only when its protocol, topology, ontology, query catalog, query count, queue, and active-request state match the campaign.

Logical query concurrency remains one. The coordinator never starts logical query `Q(n+1)` before `Q(n)` completes or fails. Within one distributed logical query, physical requests to all required authorities run concurrently and share one logical deadline. Completed sets are merged only when every required participant succeeds; partial results remain evidence and never receive a valid logical digest.

In `replicated`, every worker receives the complete fixed semantic base and synthetic ABox. In `distributed`, every worker receives the fixed base while Edge authorities receive deterministic, disjoint user partitions of the growing synthetic ABox. Fixed node, state, and trust facts needed by multiple Edge partitions remain shared. Cloud additionally receives a minimal projection containing user type and active-consent-range facts so the global consent-count dashboard remains semantically equivalent without replicating the complete ABox. Fog and Mist retain the fixed base.

Query scopes route schema and fixed knowledge to their tier and growing ABox work to the Edge authorities. `single`, `set_union`, and `boolean_or` are executable merge contracts rather than descriptive metadata. Node-state and trust queries fan out to the authorities that own the synthetic facts. Reports separate one logical query from all physical executions required to answer it.

The benchmark validates exact fragment and RDFS-closure digests before measurement. Local integration tests also compare every query whose routing changed against its full-graph result. This establishes workload equivalence for the current catalogue; it is not a general distributed SPARQL federation engine or aggregate algebra.

Cloud, Fog, Mist, and three Edge hosts communicate over Tailscale, but payload bytes are application payload, not measured VPN wire traffic. One native image is built on each host so x86_64 and ARM executions are not presented as a language-performance comparison.
