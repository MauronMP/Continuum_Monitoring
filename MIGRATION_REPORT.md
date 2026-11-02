# Migration Report

## Final scope

The repository now contains one experiment: **Docker RDF Scalability Benchmark**. It studies how a containerized RDF monitoring service changes as monitored population and actual ABox grow through 1, 50, 100, 500, 1000, 2000, 4000, 5000, 6000, 7000, 10000, 12000, 14000, 16000, 18000, and 20000 users. The only reasoning contract is RDFS; concurrency is one. Distributed and replicated are layouts of the same experiment.

## Removed

The migration removed the former physical suites, strategy/static/procedural/adaptive comparisons, cumulative and legacy load batteries, smoke entrypoints, obsolete CLI/configuration/reporting, Python workers and semantic engines, Java/Maven and OWL DL reasoner adapters, pySHACL, runtime RDFLib/owlrl/pyoxigraph dependencies, generated ontology diagrams, historical generated outputs, and tests/documentation that only exercised removed code. Two SHACL-only inventory queries were removed; the executable catalog now contains 113 RDF/SPARQL queries.

## Final architecture and dependencies

Python is the control plane. Its production dependencies are NumPy and Matplotlib. It owns configuration/topology, SSH and Docker Compose, preflight/deployment/readiness, campaign control, deadlines, resource collection, aggregation, CSV/JSON, and figures.

Rust is the semantic data plane:

- `continuum-rdf`: RDF parsing through Oxigraph/oxrdf, canonical N-Triples, digests, deterministic synthetic ABox generation, partitioning, explicit RDFS closure, SPARQL, and canonical query outcomes.
- `continuum-rdf-tool`: coordinator-side generate, digest, reason, query, catalog, and partition operations with JSON contracts.
- `continuum-worker`: Axum/Tokio HTTP worker with capacity-one semantic execution.

The final worker image is a multi-stage Rust build on Debian slim. It contains no Python, Java, Maven, OWL DL reasoner, or SHACL engine. Builds are native on every physical host and expose Rust compiler/target data; image and container state are captured by the campaign.

## Semantic equivalence

Golden fixtures were captured from the previous Python implementation for 1, 10, and 50 users before its removal. They preserve input and closure counts/digests plus all query results. Rust matches the strict-RDF closure exactly in all fixtures. Every query cardinality matches; all final result digests match except `BASE-Q33`, whose decimal `AVG` lexical precision differs between RDFLib and Oxigraph. Its cardinality remains the explicit cross-engine assertion.

The strict fixtures exclude generalized triples with literal subjects because they cannot be represented by strict RDF/Oxigraph. This difference is recorded rather than silently normalized. OWL terms may remain ordinary RDF data; no OWL entailment is claimed.

## Protocol changes

`/health` now reports service/protocol/build identity, Rust compiler and target, node/tier/authority, topology/ontology/catalog fingerprints, query count, idle/active/queue state, prepared graph and closure digests, load state, and triple count. `/reset` clears the store. `/prepare` validates the canonical fragment digest, parses, materializes RDFS, loads Oxigraph, and returns internal timings/digests. `/query` executes one catalog query and returns canonical result count/digest/keys.

Python `wait_ready()` polls to a global deadline and checks protocol compatibility, semantic assets, and idle state. Every measured repetition records health before preparation and after the final catalog round. A prepared worker is additionally checked against the expected fragment and closure digests.

## Method changes

The independent variables are users and layout. TBox, query catalog, seed, resources, hosts, rounds, and concurrency remain controlled. Artificial `target_triples`, padding, request-concurrency matrices, and multiple reasoners were removed.

A canonical deterministic dataset is generated once per scenario. A reference partition establishes expected fragment and closure digests. Every warm-up and measured repetition then independently resets, partitions, serializes, transfers, parses/loads, materializes RDFS, validates, and executes 18 complete logical catalog rounds. Warm-up directories are excluded from aggregation.

Preparation is decomposed into partition, serialization, transfer, and remote load. RDFS time remains separate. One-second-target Docker/cgroup sampling records CPU percentage/counter, container memory, PIDs, and available network counters. Result states preserve completion within/over the operational target, hard/query timeout, OOM, incompatibility, semantic mismatch, and generic failure as categories.

## Repository structure

```text
configs/                 benchmark and six-host topology
containers/worker/       Rust multi-stage image and Compose limits
docs/                    architecture, method, deployment, semantic and catalogue documentation
ontology/                human Turtle modules and canonical benchmark base
queries/                 113 SPARQL files and executable manifest
rust/                    RDF library, tool, and worker workspace
src/continuum_bench/     Python control plane
tests/                   focused unit/integration and golden fixtures
outputs/                 ignored generated campaigns plus format guide
```

The public CLI is limited to `doctor`, `render`, `deploy`, `status`, `run`, and `report`. The default campaign uses one warm-up, three measured repetitions, 18 catalog rounds, a 120-second operational preparation target, 600-second preparation deadline, and 120-second query deadline. Diagnostic unlimited mode is explicit and marks the run non-comparable.

## Validation performed

- `cargo fmt --check --manifest-path rust/Cargo.toml --all`
- `cargo clippy --manifest-path rust/Cargo.toml --all-targets -- -D warnings`
- `cargo test --manifest-path rust/Cargo.toml`, including golden differential tests
- `ruff check src tests`
- `pytest`: local control-plane, semantic-source, documentation, deadline, distributed-equivalence, and Python-to-Rust integration tests
- release Rust build and native Docker worker build
- local minimum campaign with raw results, summaries, resource samples, manifest, and fourteen PNG figures
- six-host doctor covering Docker/Compose, host and Docker architecture, memory, disk, and CPU/memory/PID cgroups
- verified deployment of the current Rust protocol and semantic fingerprints on Cloud, Fog, Mist, Edge1, Edge2, and Edge3

CI runs formatting, lint, Rust tests, Python tests, and Docker build without the physical VPN. A complete six-host performance campaign was not run as part of the refactor, so this report makes no performance claim.

## Problems found and decisions

- Historical Python processes occupied port 8391 outside Docker. Deployment now releases the dedicated benchmark port, replaces the old process, and verifies the new Rust protocol before reporting success.
- Obsolete remote source directories, stopped legacy benchmark containers, and their old images were removed after the Rust workers were verified.
- The old aggregated preparation metric mixed phases. The new evidence separates coordinator and worker costs and does not treat payload bytes as VPN wire traffic.
- Reusing one partition across repetitions would have hidden partition/serialization variance. Each repetition now creates and verifies fresh fragments.
- The physical hosts are heterogeneous. Cloud builds `x86_64`; the Raspberry kernels report `aarch64` while their Docker server/userspace produces `armv7` worker images. Both host and worker target are recorded; results describe deployment behavior and do not claim a controlled Python-versus-Rust comparison.
- The fixed semantic base is replicated in distributed mode so every worker has the required schema. The growing synthetic ABox has deterministic, disjoint Edge ownership; shared synthetic node/state/trust facts are replicated across the authorities that answer those queries. Cloud receives only the user/consent projection needed by the global consent aggregate.

## Future work

Publication campaigns may increase repetitions while preserving the matrix. Packet-level VPN telemetry, stronger distributed aggregate-query algebra, additional hardware-homogeneous validation, and controlled concurrency are separate extensions. OWL DL, SHACL runtime, decentralized orchestration, and adaptive placement are intentionally outside this benchmark and should only return as independently scoped experiments.

## File summary

Added files include the Rust workspace/tool/worker, golden fixtures, compact control-plane modules, two final TOML files, worker Docker/Compose files, focused tests, CI, five technical documents, and this report. Modified semantic assets provide the canonical strict-RDF base and current external vocabulary reuse. Removed files comprise the prior batteries, adapters, generated reports/figures, legacy configurations, historical outputs, and their exclusive tests and documentation.
