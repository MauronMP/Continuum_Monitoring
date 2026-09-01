# Project architecture

## Design goals

The repository separates semantic content, experimental workloads,
deployment topology and reporting. A change in node count must not require a
change to ontology classes or query files, and a change in the wellbeing domain
must not modify the continuum core.

## Semantic layers

| Layer | Location | Responsibility |
|---|---|---|
| Canonical release | `ontology/legacy/smartcity_continuum-v3.0.0.ttl` | Complete Protégé-editable v3 graph |
| Core | `ontology/core` | Shared schema and imports |
| Modules | `ontology/modules` | Foundation, topology, observability, governance, orchestration and federation |
| Domain | `ontology/domains/wellbeing` | Wearables, physiological observations, stress and sleep |
| Shapes | `ontology/shapes` | Closed-world structural constraints |
| Examples | `ontology/examples` | Reference ABox and scenarios S1-S17 |
| Profiles | `ontology/profiles` | Tier-specific deployment subsets |

The canonical release is the complete ontology to open in Protégé. Runtime
modules are deterministic derivatives produced by `tools/migrate_assets.py`.
Stable skolem IRIs prevent anonymous OWL/SHACL structures from multiplying when
distributed fragments are merged.

## Query organization

`queries/catalog.csv` is the execution contract. It defines order, ID, core or
domain tier, category, kind, expectation, path and traceability for 115 query
files. `queries/execution-plan.toml` independently defines distributed source
selection and merge strategy.

This distinction is important:

- category controls cumulative activation and preferred placement;
- query kind controls interpretation (`inventory`, `report`, `review`,
  `violation`, `ASK`, `dashboard`);
- execution scope controls which distributed sources are needed;
- merge strategy controls how partial results form one logical result.

Every catalog entry is executed by validation and cannot silently disappear
from a benchmark.

## Python components

| Module | Responsibility |
|---|---|
| `config.py` | Benchmark TOML loading |
| `topology.py` | Composed elastic manifests, validation and Compose rendering |
| `ontology.py` | Graph loading, digest and validation helpers |
| `queries.py` | Catalog loading, execution and expectations |
| `reasoners.py` | RDFS, OWL RL and combined profiles |
| `synthetic.py` | Deterministic ABox generation |
| `benchmark.py` | Monolithic cumulative and scalability suites |
| `partitioning.py` | TBox profile and authority-aware ABox placement |
| `distributed.py` | HTTP coordination for replicated nodes |
| `sharded.py` | Source selection, merge and monolithic-oracle validation |
| `physical.py` | Heterogeneous physical scheduling |
| `physical_cluster.py` | SSH deployment and worker lifecycle |
| `load_benchmark.py` | Rate-controlled multidimensional workload |
| `experiments.py` | Three separated architecture experiments |
| `engines.py` | Independent semantic-product comparison |
| `reporting.py` | Cross-architecture publication report |
| `cli.py` | Stable command-line interface |

## Worker contract

Docker and physical nodes expose the same HTTP protocol. `/health` identifies
the service, protocol, ontology version/revision, reasoning contract, query
count, node ID, tier, privacy authority, categories and topology fingerprint.
The coordinator rejects a mismatch before measurement.

`/prepare` builds a replicated or partitioned graph and materializes the
selected profile. `/queries` executes an explicit ID list and returns timing,
canonical result identity and process telemetry. Recovery endpoints rebuild
application state for the load experiment.

## Architecture configurations

The root `configs/topology.toml` catalogs three independent manifests:

- monolith: one local cloud process;
- Docker: any validated number of local containers;
- physical: a local coordinator and any validated number of SSH-managed hosts.

Each architecture composes separate cloud, fog, mist, edge and IoT node files.
See [ELASTIC_TOPOLOGY.md](ELASTIC_TOPOLOGY.md).

## Data-placement modes

| Mode | Data per node | Primary question |
|---|---|---|
| Monolith | Complete graph | One-node baseline |
| Docker/physical replicated | Complete graph at every selected node | Query scale-out and scheduling |
| Docker/physical sharded | Tier profile plus authority partition | Distributed ontology execution |

Replicated mode does not distribute reasoning: every node materializes a full
copy. Sharded mode replicates the immutable substrate needed for local
reasoning, distributes sensitive resources among authorities and federates
queries according to the execution plan.

## Result equivalence

New runs identify result bags using an order-independent canonical digest plus
cardinality and ASK value. Historical CSVs without a digest fall back to
cardinality/ASK and are marked with the weaker validation level.

Distributed timings exclude monolithic-oracle validation. A passed oracle
demonstrates equivalence for the selected dataset and query battery; it is not
a formal proof of arbitrary SPARQL federation or OWL modularization.

## Generated outputs

Results live under `outputs/` and are not source configuration. Each measured
directory should contain detailed CSV, summary CSV and JSON metadata. Generated
Compose, topology snapshots, figures and setup logs are also outputs and must
not be edited as inputs.
