# Continuum Monitoring Ontology Benchmark

Reproducible evaluation of a modular, policy-aware monitoring ontology across
an elastic physical continuum. Its nodes use the same ontology, SPARQL catalog, generators,
reasoners, time budgets and scientific result contracts.

## Modular physical campaigns

See [the complete architecture and reproduction guide](docs/design/MODULAR_MONITORING.md)
for the domain ports, ten scalability axes, physical resource model, reasoner
choices, structured evidence and testing boundaries.

```bash
continuum-bench campaign --validate-only
continuum-bench campaign
continuum-bench campaign --campaign-config configs/campaign.toml
```

## Structure

| Path | Responsibility |
| --- | --- |
| `src/continuum_bench/core` | Infrastructure-neutral domain model. |
| `src/continuum_bench/monitoring` | Shared cumulative/scalability orchestration. |
| `src/continuum_bench/monitoring/study` | Workload, mobility and policy-cost studies. |
| `configs/topologies/physical` | Elastic physical nodes split by tier. |
| `ontology`, `queries` | Modular semantic model and categorized SPARQL battery. |

Physical workers share the same benchmark implementation.

## Install

Requires Python 3.11+, Git and OpenSSH/rsync.

```bash
git clone https://github.com/MauronMP/Continuum_Monitoring.git
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

`physical all` covers cumulative and scalability only. See the
command reference for the ordered complete suite.

## Independent semantic products

```bash
continuum-smoke-engines
continuum-bench engines all
continuum-bench engines plot
```

Start the four native engine services before this command. It executes
RDFLib, Jena, RDF4J and Oxigraph; engine
names do not need to be passed manually. HermiT, Openllet, JFact and Konclude
remain separate OWL 2 DL consistency validators invoked by `owl-validate`.
The plot command requires all four products in each selected summary and writes
300-DPI PNG figures.

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
[physical continuum guide](docs/design/PHYSICAL_CONTINUUM.md),
[command reference](docs/design/COMMAND_REFERENCE.md),
[tests](docs/design/TESTS.md) and [architecture](docs/design/ARCHITECTURE.md).

For evidence-led figures and extended full-suite execution, see
[Publication reports](docs/design/PUBLICATION_REPORTS.md).

Run all physical benchmark families without elapsed-time cutoffs (after worker
installation and SSH setup):

```bash
. .venv/bin/activate
continuum-bench --unlimited --repetitions 5 suite
```

Each suite saves a separate directory, logs, execution policy and PNG reports.
Configured budgets remain in the evidence but are not enforced in this mode.
