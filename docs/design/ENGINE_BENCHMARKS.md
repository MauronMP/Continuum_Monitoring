# Independent semantic-engine benchmark

## Purpose

This benchmark sends the same canonical v3.0.0 N-Triples graph and the same 115
SPARQL queries to independent implementations. It complements the Python
reasoning profiles:

- RDFS, OWL RL, and RDFS+OWL RL compare entailment regimes in the project;
- Jena, RDF4J, RDFLib/OWL-RL, and Oxigraph compare independently implemented
  products under an explicit semantic contract.

| Service | Version policy | Regime | Role |
| --- | --- | --- | --- |
| Apache Jena | Container version pinned and recorded | RDFS | Independent reasoner |
| Eclipse RDF4J | Container version pinned and recorded | RDFS | Independent reasoner |
| RDFLib + OWL-RL | Runtime version recorded in metadata | RDFS | Python reference |
| Oxigraph | Runtime version recorded in metadata | No inference | SPARQL execution control |

Oxigraph is intentionally not described as a reasoner. It estimates the load
and query cost when no RDFS closure is materialized.

Jena uses `ReasonerRegistry.getRDFSReasoner()`. RDF4J uses
`SchemaCachingRDFSInferencer` over `MemoryStore`. RDFLib uses OWL-RL
`RDFS_Semantics` with the datatype-sensitive literal adapter described below.
The semantic-engine container image uses the Java version required by the most
restrictive pinned product. Consult the current Dockerfile and `/health`
metadata rather than assuming the host Java runtime is used.

## Installation and health checks

On a fresh clone, prepare Docker support and inspect the daemon:

```bash
python3 tools/bootstrap.py --with-docker
.venv/bin/continuum-bench doctor --docker
docker compose version
docker info
```

The automatic suites build and manage the semantic-engine services. If startup
fails, inspect the logs under `outputs/runtime/setup/` and follow the Docker
diagnostics in [Installation guide](INSTALLATION.md).

## Automatic execution

Normal cumulative and scalability commands include every configured product
engine automatically:

```bash
.venv/bin/continuum-smoke-cumulative
.venv/bin/continuum-smoke-scalability
.venv/bin/continuum-bench benchmark cumulative
.venv/bin/continuum-bench benchmark scalability
.venv/bin/continuum-bench benchmark all
```

No engine list or endpoint is required. Use `--python-only` only when the
external-product comparison must be deliberately skipped. Use
`--keep-engine-services` for diagnosis when the services should remain running
after the suite.

The products execute sequentially so that they do not compete for the same CPU
and memory during a measurement. Compose gives them identical declared CPU and
memory limits by default; values are configurable through the documented
environment file. Java heap bounds are explicit in the container configuration
and are not silently adapted to the host.

Each engine and dataset receives one excluded warm-up by default. Override it
on automatic benchmark runs with `--engine-warmups N`;
`--engine-warmups 0` is useful only for a quick functional check. The advanced
standalone `engines` subcommand exposes the equivalent `--warmups N` option.
Terminal progress identifies warm-up, engine, inference regime, repetition,
category or scalability block, and user volume.

## Common service contract

Every service implements:

- `GET /health`: service identity, protocol version, product name, product
  version, and inference regime;
- `POST /prepare`: load canonical N-Triples and prepare or materialize it;
- `POST /queries`: execute a sequential SPARQL batch.

The coordinator records:

- input, output, and inferred triple counts;
- load, reasoning, preparation, and query-batch wall time;
- per-query duration;
- row count or `ASK` value;
- the catalog expectation and observed compliance.

`metadata.json` records the warm-up count, reported engine versions,
`ontology_version=3.0.0`, `query_count=115`, the graph hash, and the reasoning
contract. Figure generation rejects incompatible or incomplete metadata so
that results produced under different closure semantics are not mixed.

RDF4J performs inference while statements are inserted. Its separate `load_ms`
is therefore zero and the combined load-plus-inference interval is reported as
`reasoning_ms`. `prepare_ms` is the comparable preparation metric across all
products.

## Datatype-sensitive RDFS contract and EXT-Q68

OWL-RL 7.6.2 compared some literal values through Python values, where
`True == 1` and `False == 0`. This could substitute integer literals into the
boolean properties `hasNoiseApplied` and `hasAnonymizationApplied`, creating
false EXT-Q68 privacy violations even though the asserted data were valid.

`DatatypeAwareRDFSSemantics` limits equivalence to RDF values with compatible
datatypes and language tags. It preserves valid numeric equivalence and does
not weaken EXT-Q68. The adapter is used by the monolith, RDFLib engine service,
and Docker/physical workers. OWL RL and combined profiles retain their intended
implementations.

The reasoning-contract identifier is exposed by `/health`. Coordinators reject
outdated worker images, so rebuild Docker and redeploy physical nodes after any
contract change. Never make an old result compatible by editing its metadata.

Regression tests cover all 115 queries through the real
N-Triples/prepare/query path for RDFLib and Oxigraph at 0, 5, and 25 users, plus
explicit invalid privacy cases. Repository validation also evaluates all 32
violation queries after materialization.

## Cross-engine validation

Conformance has two levels:

1. Mandatory observable outcome: identical `ASK`, or the same zero/non-zero
   result class, and compliance with the catalog expectation. A mismatch stops
   the suite with a non-zero exit status.
2. Diagnostic exact cardinality: exact row counts are compared and preserved,
   but differing datatype entailment or duplicate-binding behavior does not
   automatically fail the suite when the observable decision is unchanged.

Exact Jena/RDF4J agreement is also reported separately.

## Output layout

```text
outputs/engines/<suite>/
  query-runs.csv
  summary.csv
  metadata.json
  rdfs-equivalence.csv
  rdfs-equivalence-summary.json
outputs/engines/figures/
  engines-cumulative.{png,pdf,svg}
  engines-scalability.{png,pdf,svg}
```

Smoke runs place their `engines` directory inside the configured smoke output
directory.

## Regenerate and display figures

```bash
# Default complete engine result directory
.venv/bin/continuum-bench plot engines
.venv/bin/continuum-bench plot engines --show

# Scalability smoke results in a custom directory
.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  plot engines \
  --engine-dir outputs/smoke-scalability/engines --show

# One available suite only
.venv/bin/continuum-bench plot engines \
  --engine-suite cumulative \
  --engine-dir outputs/smoke-cumulative/engines --show
```

Figures use the median and minimum-maximum range, separate markers, explicit
inference-regime labels, and vector exports. A one-repetition smoke has a zero
range by construction and must not be used as an article's statistical result.

## Correct interpretation

- Compare preparation and query metrics under the same graph hash and contract.
- Do not compare Oxigraph's no-inference time as though it were RDFS reasoning.
- Report failed expectations and equivalence diagnostics with performance.
- Record container image digests, `/health` versions, resource limits, warm-up
  count, and repetition count in a publication artifact.
- The product benchmark does not prove full OWL 2 DL consistency; use the HermiT
  check described in [Protégé and OWL consistency](ONTOLOGY_PROTEGE.md).

## Primary implementation references

- [Apache Jena inference documentation](https://jena.apache.org/documentation/inference/index.html)
- [Apache Jena downloads and runtime requirements](https://jena.apache.org/download/)
- [Eclipse RDF4J downloads](https://rdf4j.org/download/)
- [RDF4J Repository programming guide](https://rdf4j.org/documentation/programming/repository/)
- [RDF4J Server and Workbench](https://rdf4j.org/documentation/tools/server-workbench/)
- [Oxigraph repository](https://github.com/oxigraph/oxigraph)
- [OWL-RL RDFS closure implementation](https://owl-rl.readthedocs.io/en/latest/_modules/owlrl/RDFSClosure.html)
