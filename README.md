# Continuum Monitoring Ontology Benchmark

Reproducible evaluation of a modular, policy-aware monitoring ontology across
a native monolith, an elastic local Docker continuum and a real physical
continuum. All targets use the same ontology, SPARQL catalog, generators,
reasoners, time budgets and scientific result contracts.

## Structure

| Path | Responsibility |
| --- | --- |
| `src/continuum_bench/core` | Infrastructure-neutral domain model. |
| `src/continuum_bench/monitoring` | Shared cumulative/scalability orchestration. |
| `src/continuum_bench/study` | Workload, mobility and policy-cost studies. |
| `configs/topologies/monolith` | Single-process reference split by tier. |
| `configs/topologies/docker` | Elastic Docker nodes split by tier. |
| `configs/topologies/physical` | Elastic physical nodes split by tier. |
| `ontology`, `queries` | Modular semantic model and categorized SPARQL battery. |

Local, Docker and physical deployments are infrastructure adapters, not separate
benchmark implementations. Docker is therefore a reproducible staging target
for the physical campaign.

## Install

Requires Python 3.11+, Git and either Docker with Compose v2 or OpenSSH/rsync.

```bash
git clone <repository-url> Continuum_Monitoring
cd Continuum_Monitoring
python3 tools/bootstrap.py --profile coordinator
. .venv/bin/activate
continuum-bench validate
continuum-bench preflight
continuum-bench owl-validate
```

`owl-validate` runs all available external validators. After installing HermiT,
Openllet, JFact and Konclude, use `continuum-bench owl-validate --require-all`
as the strict release gate.

Install their pinned validation runtime automatically with:

```bash
python3 tools/install_owl_reasoners.py
```

## Native monolith

```bash
continuum-smoke-local-cumulative
continuum-smoke-local-scalability
continuum-smoke-local-load
continuum-smoke-local-experiments
continuum-bench local all
continuum-bench load local
continuum-bench experiment all local
```

## Local Docker continuum

The default topology is one cloud, one fog and three edge containers. Add or
remove `[[nodes]]` in `configs/topologies/docker/nodes/*.toml`; Compose is
generated from those files.

```bash
continuum-bench doctor --docker
continuum-bench docker render
continuum-bench docker up
continuum-bench docker status

continuum-bench docker all --layout sharded --keep-running
continuum-bench docker all --layout replicated --keep-running
continuum-bench load docker
continuum-bench experiment all docker

continuum-bench load plot
continuum-bench experiment analyze
continuum-bench docker down
```

Smoke tests:

```bash
continuum-smoke-docker-cumulative
continuum-smoke-docker-scalability
continuum-smoke-docker-load
continuum-smoke-docker-experiments
```

`docker all` covers cumulative and scalability only. The load, experiment,
study and acceptance blocks are separate by design.

## Physical continuum

```bash
continuum-bench physical authorize --ssh-user pi
continuum-bench physical deploy --ssh-user pi
continuum-bench physical start --ssh-user pi
continuum-bench physical status --ssh-user pi
continuum-smoke-physical-cumulative --ssh-user pi
continuum-smoke-physical-scalability --ssh-user pi
continuum-smoke-physical-load
continuum-smoke-physical-experiments
continuum-bench physical all --layout sharded --ssh-user pi
continuum-bench physical all --layout replicated --ssh-user pi
continuum-bench load physical
continuum-bench experiment all physical
continuum-bench physical stop --ssh-user pi
```

`physical all` likewise covers cumulative and scalability only. See the
command reference for the ordered complete suite.

## Independent semantic products

```bash
continuum-smoke-engines
continuum-bench engines all
continuum-bench engines plot
```

This command automatically executes RDFLib, Jena, RDF4J and Oxigraph; engine
names do not need to be passed manually. HermiT, Openllet, JFact and Konclude
remain separate OWL 2 DL consistency validators invoked by `owl-validate`.
The plot command requires all four products in each selected summary and writes
300-DPI PNG plus vector PDF/SVG figures.

## Evaluation families

- Cumulative: progressively activates every policy/query category.
- Scalability: increases synthetic users and RDF volume.
- Load: varies events/s, users, triples, rules and node count; records latency,
  throughput, loss, accuracy, recovery and resource metrics.
- Experiments: replicated query scale-out, reasoning by hardware and
  authority-partitioned distributed ontology execution.
- Study: reproducible workload/mobility traces and category/policy/query cost.

Timeouts are stored as right-censored observations. Results go to `outputs/`.
See [the user guide](docs/USER_GUIDE.md),
[installation](docs/design/INSTALLATION.md),
[monolith guide](docs/design/MONOLITH_GUIDE.md),
[Docker Compose guide](docs/design/DOCKER_COMPOSE_GUIDE.md),
[physical continuum guide](docs/design/PHYSICAL_CONTINUUM.md),
[command reference](docs/design/COMMAND_REFERENCE.md),
[tests](docs/design/TESTS.md) and [architecture](docs/design/ARCHITECTURE.md).
