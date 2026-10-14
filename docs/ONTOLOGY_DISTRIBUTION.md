# Ontology distribution across the physical continuum

## Scope and evidence

Reviewed on 13 October 2026 against the current implementation, placement manifest,
physical inventory and a fresh local export with 12 synthetic users and seed 2026.
This is a reproducible inspection of configured deployment and generated graphs;
it does not assert that every running remote worker has this release loaded.
The export is under `outputs/audit/ontology-distribution-20261013/`.
Its `manifest.json` records the software build, semantic asset digest, versions,
fragment sizes and profile names. `module-audit.json` records the import audit.

The implementation distributes **instance data by authority** and repeats the
schema required by each tier. It is not an exclusive partition of all ontology
files, shared memory, or a globally complete distributed OWL reasoner.

## Nodes and active profiles

| Node | Tier | VPN address | Private-data authority | Profile |
| --- | --- | --- | --- | --- |
| cloud | Cloud | 100.86.63.53 | No | `ontology/profiles/cloud.ttl` |
| fog | Fog | 100.93.73.27 | No | `ontology/profiles/fog.ttl` |
| mist | Mist | 100.72.111.107 | Yes | `ontology/profiles/mist.ttl` |
| edge1 | Edge | 100.101.178.35 | Yes | `ontology/profiles/edge.ttl` |
| edge2 | Edge | 100.70.9.117 | Yes | `ontology/profiles/edge.ttl` |
| edge3 | Edge | 100.121.135.60 | Yes | `ontology/profiles/edge.ttl` |

The IoT profile exists but the physical inventory has no enabled IoT worker.
Mist is included in the active inventory and participates as an authority;
it is not a synonym for IoT. All three Edge nodes use the same schema profile
but receive different private instance partitions.

The source of truth is `configs/topologies/physical/topology.toml` and its
`nodes/{cloud,fog,mist,edge,iot}.toml` files. An endpoint is not a geographical
coordinate: the configured region labels do not establish distances or mobility.

## Exact file matrix

`configs/ontology-placement.toml` lists the following loaded substrate files.
“Yes” means included in that tier's distributed graph. Profile TTL files are
import manifests; the loader selects their listed closure rather than inserting
the profile descriptor itself as application data. The import audit checks that
the manifest and profile closures agree.

| File | Cloud | Fog | Mist | Edge 1–3 | IoT (inactive) |
| --- | --- | --- | --- | --- | --- |
| `ontology/core/schema.ttl` | Yes | Yes | Yes | Yes | Yes |
| `ontology/core/vocabulary.ttl` | Yes | Yes | Yes | Yes | Yes |
| `ontology/domains/wellbeing/schema.ttl` | Yes | — | Yes | Yes | Yes |
| `ontology/domains/wellbeing/vocabulary.ttl` | Yes | — | Yes | Yes | Yes |
| `ontology/modules/contracts.ttl` | Yes | Yes | Yes | Yes | Yes |
| `ontology/modules/deployment.ttl` | Yes | Yes | Yes | Yes | Yes |
| `ontology/modules/federation.ttl` | Yes | — | Yes | Yes | — |
| `ontology/modules/foundation.ttl` | Yes | Yes | Yes | Yes | Yes |
| `ontology/modules/governance.ttl` | Yes | Yes | Yes | Yes | Yes |
| `ontology/modules/observability.ttl` | Yes | Yes | Yes | Yes | Yes |
| `ontology/modules/orchestration.ttl` | Yes | Yes | Yes | Yes | Yes |
| `ontology/modules/topology.ttl` | Yes | Yes | Yes | Yes | Yes |
| `ontology/shapes/core-compliance.ttl` | Yes | — | — | — | — |
| `ontology/shapes/federated-learning.ttl` | Yes | — | — | — | — |

Cloud loads 14 substrate files, Fog 9, Mist and each Edge 12, and the optional
IoT profile 11. `ontology/examples/reference-system.ttl` is handled separately:
its instances are partitioned, not loaded wholesale into each distributed node.
Synthetic instances come from `src/continuum_bench/synthetic.py`; there is no
independent source TTL file for every generated user.

## Module responsibilities

| File or module | Responsibility |
| --- | --- |
| `core/schema.ttl` | Integration entry point for the reusable core imports. |
| `core/vocabulary.ttl` | Shared named vocabulary and controlled values. |
| `modules/foundation.ttl` | General entities and links to reused vocabularies. |
| `modules/contracts.ttl` | Minimal types shared across module boundaries, avoiding circular dependencies. |
| `modules/topology.ttl` | Computational nodes, infrastructure and spatial/topological relationships. |
| `modules/governance.ttl` | Policies, requirements, consent, contracts and authorization evidence. |
| `modules/observability.ttl` | Recorded state and monitoring/trust evidence. |
| `modules/orchestration.ttl` | Evaluation, adaptation, model-selection and delegation relationships. |
| `modules/deployment.ttl` | Semantic profiles and deployment fragments. |
| `modules/federation.ttl` | Federated-learning sessions and model-update relationships. |
| `domains/wellbeing/schema.ttl` | Optional health-domain concepts such as wearables and physiological observations. |
| `domains/wellbeing/vocabulary.ttl` | Domain-specific named values. |
| `shapes/core-compliance.ttl` | Core SHACL constraints. |
| `shapes/federated-learning.ttl` | Federated-learning SHACL constraints. |

A module describes knowledge; it does not automatically implement the activity
it models. In particular, federation classes do not establish an operational
training system. SHACL shapes are validation definitions, not OWL inference rules;
including them in Cloud's substrate does not mean every worker request runs SHACL.
Policy categories, query groups and ontology modules are different classifications.
A policy can span modules and categories; placement is not one category per node.

## Instance ownership and projections

`partitioning.py` orders active nodes by tier and identifier. With this inventory,
the authority order is `mist`, `edge1`, `edge2`, `edge3`. `authority_index` uses the
last digit sequence in a resource key, or otherwise the sum of its UTF-8 bytes,
modulo the number of authorities. This is deterministic assignment, not a
cryptographic hash, geographical placement or dynamic load balancing.

Reference users seed connected private components. Traversal through explicitly
listed relationships keeps wearables, observations, identifiers, consent,
contracts, state and related evaluation evidence with an authority. Other
sensitive resources have deterministic fallback ownership. Public facts are
repeated as needed. Selected cross-authority links and Cloud governance
projections are exceptions to exclusive ownership: Cloud may receive permitted
user/contract fields and decision evidence, but not the full private user graph.

The inspected reference instances assign UserA to Mist, UserB to Edge 1,
UserC to Edge 2 and UserD to Edge 3. Cloud also contains the four User type
assertions through governance projections; this does not mean it contains their
complete private components. Fog contains none of these four User instances.
`fragment-inspection.json` records this check and zero violations under the
implemented pre-inference privacy checker for all six exported fragments.
This checker is not an independent privacy proof.

Synthetic user-associated resources follow authority assignment. Node summaries
are repeated across nodes, while other global synthetic facts go to Cloud.
Consequently, similarly sized user partitions need not have equal triple counts.
The reference example also contributes an uneven fixed workload.

The coordinator builds all fragments using `build_fragments`, serializes them
with node, workload and digest metadata, and sends the designated fragment during
worker preparation. `NodeRuntime.prepare` accepts that graph in distributed mode,
checks the fragment contract and privacy constraints, and reasons locally.
`write_fragments` exports the same kind of asserted graph for inspection as
`cloud.ttl`, `fog.ttl`, `mist.ttl`, `edge1.ttl`, `edge2.ttl`, and `edge3.ttl`.
These are generated snapshots, not source modules or persisted inferred closures.

## Query routing and reasoning

`queries/catalog.csv` identifies the queries; `queries/execution-plan.toml`
provides routing and merge semantics. Of 115 configured queries, 20 target Cloud,
11 target Fog, 78 target the authorities, and 6 target a specific user authority
(UserA: 2; UserB: 3; UserD: 1). Multi-authority SELECT results use the specified
set union; three ASK queries use boolean OR. User-specific routing resolves the
same deterministic ownership function as fragmentation.

Each worker runs the selected RDFS, HermiT, Openllet, JFact or Konclude backend
against its prepared local graph. The coordinator merges query responses; it does
not exchange newly inferred triples until a global fixed point is reached.
Cross-partition joins or entailments requiring facts at different authorities
are therefore not generally supported. Agreement with a canonical reference
must be checked for the configured queries, dataset and reasoner; an agreement
result is not a proof for arbitrary future queries.

## Replicated versus distributed, and the comparison module

In `replicated` mode each worker loads the full configured application input
(including the reference example) and generates the workload locally. The
per-tier placement table above applies to `distributed`, not replicated mode.
The current worker API accepts these two names; “shared” describes repeated
schema or historical terminology, not a third supported execution layout.

Deployment copies release assets, including the ontology directory, into
`/home/pi/continuum-bench` on remote workers. Thus files present on disk can be
more extensive than the graph used in a distributed request. This benchmark
packaging is not a security boundary: the example dataset is available in the
release, and the coordinator constructs the fragments from full inputs.
Production private records would require authority-local ingestion and separate
access controls instead of this synthetic/reference-data preparation path.

`python -m continuum_bench.monitoring.comparison run` is a separate experiment:
it replays paired monitoring strategies per host with a small adapter ontology.
It does not deploy these complete modular fragments or measure a federated
six-node decision service merely because all six hosts appear in its results.

## Verified export

The following counts are asserted triples before inference, for 12 synthetic
users plus the reference example. Shared triples appear in several fragments;
adding fragment sizes is not the logical graph size.

| Node | Substrate triples | Total fragment triples |
| --- | ---: | ---: |
| cloud | 2956 | 7422 |
| fog | 2227 | 6390 |
| mist | 2499 | 7602 |
| edge1 | 2499 | 7027 |
| edge2 | 2499 | 7035 |
| edge3 | 2499 | 7015 |

The union contains **9,150 distinct triples**. The complete logical substrate
contains 2,956 triples; 252 resources are marked sensitive by the fragment model.
These counts are configuration-specific and must be regenerated after changes.
The module audit reports 396 owned terms, no duplicate ownership, no unresolved
imports, no profile/placement mismatch and no optional wellbeing/federation
imports in the core closure.

## Deployment freshness

The six-node deployment was synchronized and verified on 13 October 2026;
maintenance evidence is under `outputs/audit/worker-sync-20261013/`. This is a
historical snapshot, not a guarantee after later source edits. Check compatibility
before every campaign, and synchronize/restart after code or semantic changes.
`physical status` validates build, topology and semantic identity, but does not
expose a remote dump of the prepared graph. The local export above checks
configured placement rather than remote memory contents.

## Remaining limitations and completion criteria

- No active IoT worker is configured. Its profile is checked statically only.
- Local fragment closure is implemented; globally complete distributed OWL
  reasoning and arbitrary distributed joins are not implemented.
- Ownership depends on the active authority count and ordering. Adding/removing
  an authority can reassign resources; automatic live migration is not provided.
- Privacy checks constrain selected graph content but do not prove anonymity,
  enforce per-user authorization on returned answers or secure files on disk.
- The coordinator sees the complete benchmark input. Production decentralization
  requires local data ingestion and a policy-controlled response boundary.
- The devices are geographically distributed, but coordinate fields are not
  populated. VPN addresses do not establish distance; fragmentation executes
  no mobility simulation. `network_mbps` is nominal metadata and does not cap
  actual throughput.
- Model-data completeness and traceability are evaluated separately in
  [Ontology review](ONTOLOGY_REVIEW.md).
- Remote deployment freshness must be checked before a new campaign. Do not
  synchronize or restart workers while a campaign is running; release/digest
  mismatches intentionally invalidate mixed-version evidence.

## Reproduce the inspection

From the repository root:

```bash
source .venv/bin/activate
continuum-bench fragments --users 12 --output-dir outputs/audit/ontology-distribution
python tools/audit_ontology_modules.py --output outputs/audit/ontology-distribution/module-audit.json
pytest tests/core/test_partitioning.py tests/core/test_module_boundaries.py tests/infrastructure/test_fragment_transport.py -q
continuum-bench physical status --ssh-user pi
```

The first three commands inspect and test local assets. The last checks physical
worker status; it does not update their code. See [Physical continuum](PHYSICAL_CONTINUUM.md)
for deployment and [Complete execution](COMPLETE_EXECUTION.md) for campaign commands.
