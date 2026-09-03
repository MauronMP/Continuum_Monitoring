# Continuum Monitoring Ontology Benchmark v3.0.0

This repository provides a reproducible benchmark and validation framework for
a policy-aware monitoring ontology spanning IoT, mist, edge, fog and cloud.
It includes the complete English ontology, 115 SPARQL queries, SHACL shapes,
synthetic workloads, three Python reasoning profiles, four independent semantic
products, elastic Docker deployment and an SSH-managed physical continuum.

The reusable ontology core is domain-independent. Wearable, stress and sleep
concepts are isolated in an optional wellbeing extension.

## Documentation

Start with the [complete user guide](docs/USER_GUIDE.md). The documentation
index in [docs/README.md](docs/README.md) links installation, test execution,
methodology, architecture, topology configuration and scientific limitations.

Primary operational guides:

- [installation from a clean clone](docs/design/INSTALLATION.md);
- [all tests and commands](docs/design/TESTS.md);
- [elastic topology configuration](docs/design/ELASTIC_TOPOLOGY.md);
- [Docker benchmarks](docs/design/DOCKER_BENCHMARKS.md);
- [physical continuum deployment](docs/design/PHYSICAL_CONTINUUM.md);
- [benchmark methodology](docs/design/BENCHMARKS.md);
- [scientific validity and limits](docs/design/SCIENTIFIC_VALIDITY.md).

The English requirement, policy, query and ontology references under
`docs/reference` are generated from the executable v3 artefacts:

```bash
.venv/bin/python tools/generate_reference_docs.py
.venv/bin/python tools/check_documentation.py
```

## Repository layout

| Path | Purpose |
|---|---|
| `ontology/legacy/smartcity_continuum-v3.0.0.ttl` | Complete canonical ontology for Protégé |
| `ontology/core`, `ontology/modules` | Reusable continuum schema and modules |
| `ontology/domains/wellbeing` | Optional domain extension |
| `ontology/shapes` | SHACL validation constraints |
| `ontology/examples` | Reproducible reference individuals and scenarios |
| `ontology/profiles` | Cloud, fog, mist, edge and IoT placement profiles |
| `queries/catalog.csv` | Ordered 115-query execution catalog |
| `queries/core`, `queries/domain` | One SPARQL 1.1 query per file |
| `queries/execution-plan.toml` | Distributed source and merge plan |
| `configs/topology.toml` | Catalog of monolithic, Docker and physical architectures |
| `configs/topologies/*/nodes` | Per-architecture, per-tier elastic node files |
| `src/continuum_bench` | Validation, workloads, runners and reports |
| `engine-service` | Apache Jena and Eclipse RDF4J adapters |
| `docs` | User, design, method and generated reference manuals |

## Supported hosts

- Coordinator: 64-bit Linux, macOS or WSL2 with CPython 3.11-3.13.
- Docker experiments: Docker Engine/Desktop, Compose v2 and Buildx.
- Physical workers: Linux or Raspberry Pi OS with Python 3.11+, including
  lightweight 32-bit Raspberry Pi workers.
- Native Windows Python is not supported; use WSL2.

Jena, RDF4J and Maven run in containers. They do not need to be installed on
the host. Physical 32-bit workers intentionally use the portable RDFLib/OWL-RL
profiles and do not run the independent Java/PyOxigraph product stack.

## Clean installation

```bash
git clone https://github.com/MauronMP/Continuum_Monitoring.git
cd Continuum_Monitoring

python3 tools/doctor.py
python3 tools/bootstrap.py

.venv/bin/python -m pip check
.venv/bin/continuum-bench --help
```

To prepare Docker as part of bootstrap:

```bash
python3 tools/doctor.py --docker
python3 tools/bootstrap.py --with-docker
```

The bootstrap creates a repository-local `.venv`, installs pinned
dependencies, performs consistency checks and writes setup logs below
`outputs/runtime/setup/`. Do not copy a virtual environment from another host.

See [INSTALLATION.md](docs/design/INSTALLATION.md) for Ubuntu, macOS, WSL2,
Docker permissions, Raspberry Pi prerequisites and troubleshooting.

## Validate the release

```bash
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench validate
.venv/bin/python tools/check_documentation.py
.venv/bin/python -m pytest
```

The validation gate checks Turtle parsing, the v3 release contract, all 115
query expectations, SHACL, RDFS/OWL-RL materialization, datatype safety,
absence of asserted/inferred contradictions, privacy-aware fragment
reconstruction and topology consistency.

Optional OWL 2 DL profile and HermiT consistency check:

```bash
python3 tools/check_owl_consistency.py --require-dl-profile \
  --output outputs/validation/ontology-hermit.json
```

This optional command requires Java 11+ and Protégé with HermiT. It is kept
outside timed benchmarks.

## Fast smoke tests

Python-only pytest contracts, requiring no Docker:

```bash
.venv/bin/python -m pytest -m smoke_cumulative
.venv/bin/python -m pytest -m smoke_scalability
```

Measurable local smokes with the three reasoning profiles and automatic
RDFLib/Jena/RDF4J/Oxigraph product runs:

```bash
.venv/bin/continuum-smoke-cumulative
.venv/bin/continuum-smoke-scalability
```

If Docker is unavailable, validate only the local pipeline:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  benchmark cumulative --python-only

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  benchmark scalability --python-only
```

Smoke results prove that the workflow executes; they are not publication
measurements.

## Monolithic benchmarks

```bash
.venv/bin/continuum-bench benchmark cumulative
.venv/bin/continuum-bench benchmark scalability
.venv/bin/continuum-bench benchmark all
```

These commands run the configured Python reasoning profiles and automatically
run the independent product stack. Add `--python-only` to exclude the product
comparison deliberately.

The cumulative suite adds all 16 categories in a fixed order. The scalability
suite rebuilds an independent deterministic graph for every configured user
volume and executes all 115 queries. Publication runs cap a phase at 60 seconds
and a complete measurement point at 90 seconds. An exceeded limit is written as
a right-censored row; larger scalability points for the affected engine or
topology are skipped instead of being timed to completion. Configure these
thresholds under `[limits]` and `[distributed]` in `configs/benchmark.toml`.

## Elastic Docker topology

Inspect and start every node declared under `configs/topologies/docker`:

```bash
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench topology show --name docker
.venv/bin/continuum-bench topology up --name docker
.venv/bin/continuum-bench topology status --name docker
```

Run authority-partitioned and replicated layouts:

```bash
.venv/bin/continuum-bench docker all --layout sharded
.venv/bin/continuum-bench docker all --layout replicated
```

Stop only this generated topology:

```bash
.venv/bin/continuum-bench topology down --name docker
```

The generated Compose file is an output artefact. Add or remove nodes only in
the per-tier TOML files; no Python or static Compose edit is required.

## Physical continuum

The default physical topology uses this coordinator as cloud, one Raspberry Pi
as fog and three Raspberry Pi devices as edge nodes. Edit
`configs/topologies/physical/nodes/*.toml` to match the actual hosts.

```bash
python3 tools/doctor.py --physical

.venv/bin/continuum-bench physical authorize --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi

.venv/bin/continuum-bench physical all --layout sharded --ssh-user pi
.venv/bin/continuum-bench physical all --layout replicated --ssh-user pi

.venv/bin/continuum-bench physical stop --ssh-user pi
```

Passwordless SSH keys are required after `authorize`; passwords are never
stored in the repository. Deployment creates a minimal `.venv-node` on each
remote host and sends a flattened, fingerprinted topology snapshot.

Physical sharded queries use bounded batches and worker-side deadlines from the
`[distributed]` table in the selected benchmark TOML. Long POSTs are not
retried by default, avoiding duplicate work on single-threaded Raspberry Pi
workers. After changing code or timeout settings, stop, deploy, start and check
the cluster before rerunning. See
[PHYSICAL_CONTINUUM.md](docs/design/PHYSICAL_CONTINUUM.md#bounded-query-batches-and-timeouts).

## Multidimensional load benchmark

The load suite independently varies event rate, users, target triples, rules
and active node count. It measures p50/p95/p99 latency, processed and lost
events, throughput, inference, alert accuracy, CPU, RSS, disk, HTTP payload
bytes and application-state recovery.

```bash
.venv/bin/continuum-bench load monolith
.venv/bin/continuum-bench load docker
.venv/bin/continuum-bench load physical
.venv/bin/continuum-bench load all
.venv/bin/continuum-bench load plot --show
```

## Three separated architecture experiments

The project avoids conflating three different questions:

1. `scale-out`: query throughput using full replicas; prepare time excluded
   from the primary query metric.
2. `reasoning-hardware`: materialization of the same graph on each endpoint
   independently.
3. `distributed-ontology`: authority-aware TBox/ABox placement and federated
   query execution, checked against a monolithic oracle.

```bash
.venv/bin/continuum-bench experiment scale-out all
.venv/bin/continuum-bench experiment reasoning-hardware all
.venv/bin/continuum-bench experiment distributed-ontology all
.venv/bin/continuum-bench experiment all all

.venv/bin/continuum-bench experiment plot all --show
.venv/bin/continuum-bench experiment analyze --show
```

## Figures and comparisons

```bash
.venv/bin/continuum-bench plot all
.venv/bin/continuum-bench plot publication
.venv/bin/continuum-bench plot engines --engine-suite all
.venv/bin/continuum-bench compare all
.venv/bin/continuum-report
```

Publication figures are generated as 300-dpi PNG and vector PDF/SVG where the
report supports them. Always preserve the accompanying CSV and JSON metadata;
figures alone are not sufficient experimental evidence.

## Elastic node configuration

```text
configs/topologies/
├── monolith/{topology.toml,nodes/*.toml}
├── docker/{topology.toml,nodes/*.toml}
└── physical/{topology.toml,nodes/*.toml}
```

Every architecture has separate `cloud.toml`, `fog.toml`, `mist.toml`,
`edge.toml` and `iot.toml` files. Distributed architectures accept any positive
number of nodes subject to validation. The monolithic baseline intentionally
contains exactly one local cloud node.

After any topology edit:

```bash
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench topology show --name monolith
.venv/bin/continuum-bench topology show --name docker
.venv/bin/continuum-bench topology show --name physical
```

See [ELASTIC_TOPOLOGY.md](docs/design/ELASTIC_TOPOLOGY.md) for every field,
validation rule and resizing procedure.

## Reproducibility rules

- Do not run unrelated heavy workloads during measured campaigns.
- Keep reasoners, ontology revision, query catalog, seeds and resource limits
  fixed across compared architectures.
- Use at least one warm-up and multiple measured repetitions for publication.
- Treat timeouts and failures as observations; never drop them silently.
- Compare matched profiles and verify result digests before interpreting
  speedup.
- Record host model, OS, Python, Docker, network, cooling and power mode.
- Do not claim that a continuum must outperform a monolith. The experiments
  identify the workload and scale at which distribution helps or hurts.

## License and citation

Add the repository URL, release/commit identifier, ontology revision, complete
configuration files and generated metadata to any published experimental
artefact. See [SCIENTIFIC_VALIDITY.md](docs/design/SCIENTIFIC_VALIDITY.md) for
the evidence required before making performance or ontology-validity claims.
