# Distributed Ontology Deployment

## Purpose and scope

This document defines how the current physical benchmark distributes semantic knowledge across Cloud, Fog, Mist, and Edge workers. It distinguishes the ontology source modules, the intended layer profiles, the executable benchmark graph, the growing instance data, query routing, and adaptation replicas.

The maintained implementation is a hybrid distribution:

- the fixed semantic base is available to every worker;
- the growing synthetic ABox is horizontally partitioned across the three Edge authorities;
- selected global facts are projected to Cloud;
- Fog and Mist normally retain only the fixed base;
- an adaptation action may place a read-only copy of one Edge fragment on another physical node.

It is not a module-per-node deployment, an RDF graph database shared over the network, or a decentralized peer-to-peer federation. Python currently coordinates preparation and query routing. Each Rust worker parses, materializes RDFS, stores, and queries its local graph independently.

## Semantic source files

The human-readable ontology is maintained as modular Turtle. The benchmark uses the canonical strict-RDF representation in `ontology/benchmark/base.nt`.

| File or directory | Semantic responsibility | Runtime role |
|---|---|---|
| `ontology/modules/foundation.ttl` | Users, processing levels, temporal entities, and the minimal common foundation. | Fixed base on every worker. |
| `ontology/modules/contracts.ttl` | Shared contracts such as services, states, models, transfers, and validation campaigns. | Fixed base on every worker. |
| `ontology/modules/topology.ttl` | Cloud, Fog, Mist and Edge nodes, locations, zones, distances, connectivity, communities, and node-user relations. | Fixed base on every worker; synthetic node-user relations grow in Edge fragments. |
| `ontology/modules/governance.ttl` | Policies, requirements, consent, authorization, policy categories, precedence, and governance evidence. | Fixed base on every worker; user-specific consent and authorization facts grow in Edge fragments. |
| `ontology/modules/observability.ttl` | Node, device and user state, resource and communication evidence, monitoring state, and trust evidence. | Fixed base on every worker; synthetic user/device states are partitioned, while selected node-state and trust facts are shared across Edge fragments. |
| `ontology/modules/orchestration.ttl` | Evaluation states, adaptation actions, migration, replication, offloading, retention, synchronization, and decision alternatives. | Fixed base on every worker; synthetic operational instances are partitioned by their subject owner. |
| `ontology/modules/deployment.ttl` | Authority scopes, deployment fragments, hosting, graph identity, privacy classes, replicas, and entailment profiles. | Fixed base on every worker and used to describe deployment semantics. |
| `ontology/modules/federation.ttl` | Federated-learning sessions, payloads, model updates, privacy budgets, and safeguards. | Included in the executable fixed base; queried mainly through Edge authorities. |
| `ontology/core/schema.ttl` | Application ontology entry point importing the domain-neutral core modules. | Source of the fixed core schema. |
| `ontology/core/vocabulary.ttl` | Controlled values for states, levels, policy categories, query kinds, purposes, and actions. | Fixed vocabulary on every worker. |
| `ontology/domains/wellbeing/schema.ttl` | Optional health and wellbeing extension: wearables, physiological sensors, observations, stress and sleep concepts. | Included in the current fixed benchmark base; growing wellbeing instances are partitioned across Edge authorities. |
| `ontology/domains/wellbeing/vocabulary.ttl` | Wellbeing values such as stress, sleep, person state, and observed-property terms. | Fixed vocabulary on every worker. |
| `ontology/alignments/health-vocabularies.ttl` | Pinned local use of SOSA, SAREF, SAREF4EHAW, SAREF4WEAR, QUDT, and related external terms. | Fixed alignment on every worker; avoids network retrieval during experiments. |
| `ontology/catalog/queries.ttl` | RDF representation of the 113 executable query specifications. | Fixed catalogue metadata in the canonical base. |
| `ontology/examples/reference-system.ttl` | Fixed reference individuals used by the query contract. | Fixed reference ABox on every worker. |
| `ontology/profiles/*.ttl` | Intended ontology bundles for deployment layers. | Source metadata and validation input; profile declarations and imports do not control benchmark fragment construction. |
| `ontology/benchmark/base.nt` | Canonical strict-RDF fixed graph. | The 8,704-triple, 1.47 MB base from which every runtime fragment starts. |
| `ontology/benchmark/manifest.json` | Source digests, canonical graph digest, byte size, and triple count. | Detects drift between modular sources and the executable base. |

OWL terms may remain as RDF data, but workers execute the maintained strict RDFS contract. They do not run OWL DL or SHACL during a benchmark.

## Intended ontology profiles

Profiles express the semantic bundle intended for a deployment layer. Imports are transitive: importing the core schema also brings Foundation, Contracts, Deployment, Governance, Observability, Orchestration, and Topology.

| Profile | Explicit files imported | Included through the core | Explicitly omitted from that profile |
|---|---|---|---|
| Cloud | Core schema, core vocabulary, federation, wellbeing schema, wellbeing vocabulary | Foundation, Contracts, Deployment, Governance, Observability, Orchestration, Topology | None of the maintained application modules. |
| Edge | Core schema, core vocabulary, federation, wellbeing schema, wellbeing vocabulary | Foundation, Contracts, Deployment, Governance, Observability, Orchestration, Topology | None of the maintained application modules. |
| Mist | Core schema, core vocabulary, federation, wellbeing schema, wellbeing vocabulary | Foundation, Contracts, Deployment, Governance, Observability, Orchestration, Topology | None of the maintained application modules. |
| Fog | Core schema and core vocabulary | Foundation, Contracts, Deployment, Governance, Observability, Orchestration, Topology | Federation, wellbeing schema, wellbeing vocabulary, and health alignment. |
| IoT | Core schema, core vocabulary, wellbeing schema, wellbeing vocabulary | Foundation, Contracts, Deployment, Governance, Observability, Orchestration, Topology, and health alignment | Federation. There is no IoT worker in the current physical benchmark. |
| Full | Core schema, core vocabulary, federation, wellbeing schema, wellbeing vocabulary | All core modules and health alignment | None. |

The current scalability runner does not construct fragments by resolving these profiles. It uses `base.nt` for all workers and then applies data partitioning. Consequently, profile-level omission is an architectural packaging declaration, not evidence that a class or property is absent from a benchmark worker.

## Runtime distribution by physical layer

### Cloud

Cloud has authority `global`.

It receives:

- the complete fixed canonical base;
- user type assertions required by the global dashboard;
- `hasActiveConsentRange` facts required for the global consent-count query;
- no complete synthetic wearable, observation, user-state, device-state, contract, authorization, or physiological history.

The additional Cloud projection is produced by `_consent_projection()` in `src/continuum_bench/experiment.py`. It is deliberately minimal and exists to preserve the result of the supported global consent aggregation without copying the complete growing ABox.

Cloud directly executes these query categories in the maintained catalogue:

- identity and consent;
- policy governance;
- security and identity;
- semantic schema;
- validation.

Cloud does not directly execute the following categories in the current catalogue:

- adaptation;
- temporal audit;
- context and zones;
- data lifecycle;
- decision;
- delegation;
- federation;
- observability;
- topology;
- trust;
- wellbeing.

Here, “does not directly execute” describes query routing. The associated schema remains present in the fixed graph.

### Fog

Fog has authority `regional`.

It receives:

- the complete fixed canonical base;
- no growing synthetic user partition;
- no global consent projection beyond fixed reference facts.

Fog directly executes:

- decision queries explicitly scoped to Fog;
- observability summaries scoped to Fog;
- topology summaries scoped to Fog;
- trust summaries scoped to Fog.

Fog does not directly execute:

- adaptation;
- temporal audit;
- context and zones;
- data lifecycle;
- delegation;
- federation;
- identity and consent;
- policy governance;
- security and identity;
- semantic schema;
- validation;
- wellbeing.

The intended Fog profile omits the federation and wellbeing bundles. The executable benchmark still provides their fixed terms through `base.nt`; Fog does not receive their growing user data or their query workload.

### Mist

Mist has authority `near-edge`.

In the baseline distributed benchmark it receives:

- the complete fixed canonical base;
- no growing synthetic user partition;
- no directly routed category from the current 113-query catalogue.

Therefore, Mist is semantically prepared but normally idle during the application query workload. This is intentional: it provides a measured physical target for future placement and for the current adaptation demonstration.

When adaptation deploys a read-only replica on Mist, it additionally receives:

- the exact N-Triples fragment of the selected Edge authority;
- the source authority identity;
- the expected dataset and RDFS-closure digests;
- its own local RDFS closure and Oxigraph store.

Mist then answers alternating reads for that authority. It does not become a fourth partition, and the source Edge worker remains active.

### Edge 1, Edge 2, and Edge 3

The Edge workers have authorities `partition-a`, `partition-b`, and `partition-c`.

Every Edge receives:

- the complete fixed canonical base;
- all non-synthetic triples;
- shared synthetic node descriptions;
- shared synthetic node-state facts;
- shared synthetic trust-assessment facts;
- one disjoint partition of the remaining synthetic ABox.

The partitioned data includes:

- users and external identifiers;
- wearables and sensors;
- physiological, stress, sleep, and other observations;
- user and device states;
- consent records and semantic contracts;
- authorization decisions;
- data contexts and parametrized data;
- user-node relationships;
- transfers, retention, delegation, evaluation, and adaptation-related synthetic facts when generated.

Edge workers directly execute these categories:

- adaptation;
- temporal audit;
- context and zones;
- data lifecycle;
- decision;
- delegation;
- federation;
- identity and consent;
- observability;
- security and identity;
- topology;
- trust;
- wellbeing.

They do not directly execute the Cloud-only catalogue categories:

- policy governance;
- semantic schema;
- validation.

Some Edge queries run on all three authorities. Queries with an `authority_key` run on one deterministic Edge authority.

## Layer and category matrix

The matrix records direct query execution in distributed mode. `Yes` means that at least one query in the category is routed to the layer. `No` does not mean that the category vocabulary is absent from the local fixed graph.

| Query category | Cloud | Fog | Mist baseline | Edge authorities |
|---|:---:|:---:|:---:|:---:|
| Adaptation | No | No | No | Yes |
| Temporal audit | No | No | No | Yes |
| Context and zones | No | No | No | Yes |
| Data lifecycle | No | No | No | Yes |
| Decision | No | Yes | No | Yes |
| Delegation | No | No | No | Yes |
| Federation | No | No | No | Yes |
| Identity and consent | Yes | No | No | Yes |
| Observability | No | Yes | No | Yes |
| Policy governance | Yes | No | No | No |
| Security and identity | Yes | No | No | Yes |
| Semantic schema | Yes | No | No | No |
| Topology | No | Yes | No | Yes |
| Trust | No | Yes | No | Yes |
| Validation | Yes | No | No | No |
| Wellbeing | No | No | No | Yes |

There are 83 queries with scope `authorities`, 18 with scope `cloud`, six with scope `fog`, and six with an `authority_key`. The baseline catalogue currently has no query scoped directly to Mist.

## Deterministic ABox partitioning

For distributed layout, the partition participants are the Edge workers in topology order: Edge 1, Edge 2, and Edge 3. Every synthetic subject with a numeric suffix is assigned using:

```text
owner_index = numeric_suffix mod number_of_edge_partitions
```

With three partitions:

| Numeric suffix remainder | Owner |
|---:|---|
| 0 | Edge 1 / `partition-a` |
| 1 | Edge 2 / `partition-b` |
| 2 | Edge 3 / `partition-c` |

Related generated subjects use the same numeric suffix, so a user's wearable, observations, consent, states, and associated records normally remain under the same authority. Subjects without a numeric suffix use a stable SHA-256-derived owner. The same seed and population therefore produce byte-identical fragments.

The generator adds 70 triples per user and 21 node triples per group of at most 100 users. It does not pad datasets to a target size.

## Measured 20,000-user example

The latest completed scalability campaign produced the following distributed fragments:

| Worker | Runtime role | Triples | Serialized bytes |
|---|---|---:|---:|
| Edge 1 | Partition A | 479,594 | 75,452,594 |
| Edge 2 | Partition B | 479,594 | 75,532,598 |
| Edge 3 | Partition C | 479,524 | 75,441,594 |
| Cloud | Fixed base plus consent projection | Not recorded by the partition tool | 7,471,395 |
| Fog | Fixed base only | 8,704 before local RDFS closure | 1,471,394 |
| Mist | Fixed base only | 8,704 before local RDFS closure | 1,471,394 |

The Edge difference is caused by deterministic integer partitioning and fixed/shared facts. It is not random load imbalance.

## Query routing and result assembly

Each query in `queries/manifest.json` declares an execution scope and a merge strategy.

| Execution scope | Selected workers in distributed mode |
|---|---|
| `authorities` | Edge 1, Edge 2, and Edge 3 concurrently. |
| `cloud_authorities` | Cloud and all Edge authorities concurrently. The current catalogue does not use this scope. |
| `all` | All six workers concurrently. The current catalogue does not use this scope. |
| `authority_key:<IRI>` | One deterministic Edge authority selected from the key. |
| `cloud` | Cloud. |
| `fog` | Fog. |
| `mist` | Mist. The current catalogue does not use this scope. |
| `edge` | One Edge candidate selected deterministically for the round and query position. |

Supported merge contracts are:

- `single`: exactly one physical result is the logical result;
- `set_union`: canonical result rows from every selected authority are deduplicated and merged;
- `boolean_or`: distributed ASK answers are combined with logical OR.

All physical requests belonging to one logical query run concurrently and share one logical deadline. The next logical query does not begin until the current query completes or fails. If any required participant fails or times out, partial physical evidence is retained, but no valid complete logical digest is produced.

## Local reasoning and semantic validation

Each worker performs RDFS materialization locally after receiving its fragment. There is no cross-node reasoning phase. The replicated schema allows local domain, range, subclass, and subproperty consequences to be derived without retrieving the TBox from another node.

Before measurement, the coordinator verifies for every worker:

- the serialized dataset digest;
- the expected RDFS closure digest;
- ontology and query-catalog fingerprints;
- query count and protocol version;
- loaded graph and idle state.

Integration checks compare supported distributed query results with the complete-graph reference. This establishes equivalence for the maintained catalogue. It does not prove equivalence for arbitrary SPARQL joins, aggregates, property paths, or future ontology extensions.

## Distributed versus replicated layout

| Property | Distributed | Replicated |
|---|---|---|
| Fixed semantic base | Present on every worker | Present on every worker |
| Growing synthetic ABox | Split across Edge authorities; minimal Cloud projection | Complete copy on every worker |
| Edge ownership | Disjoint deterministic partitions | Every worker owns the complete dataset |
| Logical query routing | Scope-dependent fan-out and merge | One rotating complete replica per logical query |
| Local RDFS cost | Applied to each smaller local fragment | Applied to the complete graph on every worker |
| Storage growth | Concentrated and divided across Edge | Repeated on all six workers |
| Coordinator | Required | Required |
| General decentralized federation | Not implemented | Not implemented |

## Adaptation replica semantics

An adaptation replica copies an existing authority; it does not repartition the whole ontology.

For example, replicating Edge 3 on Mist performs these steps:

1. Keep Edge 3 active with `partition-c`.
2. Transfer the exact Edge 3 fragment to a new container on Mist.
3. Verify the fragment digest.
4. Compute and verify the same local RDFS closure.
5. Register the new worker as a read-only equivalent of Edge 3.
6. Alternate eligible reads between Edge 3 and the Mist replica.
7. Preserve the original fan-out size and merge contract.

This increases read capacity and reduces source pressure, but duplicates the fragment's memory and storage cost. It does not transfer authority, stop the source, or make Mist an independent partition owner.

## Current limitations

- Fragment placement is coordinated centrally.
- Query decomposition is catalogue-driven rather than a general federated SPARQL planner.
- Reasoning is local; rules requiring joins across remote fragments are not supported.
- Fog and Mist do not own growing baseline ABox partitions.
- Profile imports do not currently construct runtime layer-specific graphs.
- Cloud receives one purpose-built consent projection rather than a general materialized global view.
- Replicas are read-only and do not implement update propagation or consistency protocols.
- Tailscale provides connectivity, but VPN wire-level bytes and energy consumption are not measured.
- The current equivalence guarantee applies only to the pinned ontology, generator, RDFS contract, and 113-query catalogue.

## Implementation references

- Physical roles and authorities: `configs/topology.toml`
- Canonical ontology contract: `ontology/benchmark/manifest.json`
- Dataset generation and Cloud projection: `src/continuum_bench/experiment.py`
- Deterministic graph partitioning: `rust/continuum-rdf/src/partition.rs`
- Query selection and merge contracts: `src/continuum_bench/query_execution.py`
- Executable query metadata: `queries/manifest.json`
- Replica deployment: `src/continuum_bench/adaptation/deployment.py`
- Replica-aware execution: `src/continuum_bench/adaptation/experiment.py`

