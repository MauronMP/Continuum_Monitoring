# Architecture

The project has one benchmark and two planes. Python validates configuration, manages the physical topology and Docker, controls repetitions, records metrics, and creates reports. Rust performs RDF parsing, deterministic serialization, RDFS closure, SPARQL, digests, dataset generation, and HTTP serving.

The Rust workspace contains `continuum-rdf`, `continuum-rdf-tool`, and the Axum/Tokio `continuum-worker`. A capacity-one semaphore serializes semantic work. `/health` reports identity, protocol/build data, Rust version and target, semantic fingerprints, queue depth, active requests, idle state, and graph digests. `/reset`, `/prepare`, and `/query` form the measured protocol. Python accepts a worker only when its protocol, topology, ontology, query catalog, query count, queue, and active-request state match the campaign.

In `replicated`, every worker receives the complete fixed semantic base and synthetic ABox. In `distributed`, every worker receives the fixed base while edge authorities receive deterministic, disjoint user partitions of the growing synthetic ABox. Fixed node/state/trust facts needed by multiple partitions remain shared. Query scopes route fixed knowledge to its tier and federated ABox work to the authorities; canonical result keys are merged according to the manifest contract. Reports separate a complete logical query from the physical worker executions used to answer it.

Cloud, Fog, Mist, and three Edge hosts communicate over Tailscale, but payload bytes are application payload, not measured VPN wire traffic. One native image is built on each host so x86_64 and ARM executions are not presented as a language-performance comparison.
