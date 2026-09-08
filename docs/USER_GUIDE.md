# User guide

This page contains the workflow shared by every execution target. Operational
instructions are intentionally separated:

- [Monolith guide](design/MONOLITH_GUIDE.md): native one-process control,
  smokes, benchmarks, load and experiments.
- [Physical continuum guide](design/PHYSICAL_CONTINUUM.md): coordinator,
  Raspberry Pi workers, SSH deployment, smokes and physical campaigns.
- [Command reference](design/COMMAND_REFERENCE.md): copy-and-run commands for
  the complete suites and each independent block.

## Installation

Follow the [complete installation guide](design/INSTALLATION.md), then run:

```bash
git clone https://github.com/MauronMP/Continuum_Monitoring.git
cd Continuum_Monitoring
python3 tools/bootstrap.py --profile coordinator
. .venv/bin/activate
```

Physical deployment requires SSH/rsync on the coordinator and Python 3.11+, `venv`, `rsync`,
`procps` and SSH on every worker.

## Common acceptance checks

```bash
continuum-bench topology validate --name monolith
continuum-bench topology validate --name physical
continuum-bench validate
continuum-bench preflight
continuum-bench owl-validate
python -m pytest
python3 tools/check_documentation.py
```

`validate` covers RDF parsing, SHACL, query contracts and the portable
`rdfs`, `owlrl` and `rdfs_owlrl` materializers. External OWL 2 DL consistency
is separate. After installing HermiT, Openllet, JFact and Konclude, run the
strict gate:

```bash
continuum-bench doctor --owl
continuum-bench owl-validate --require-all
```

## Elastic configuration

Both native targets have independent manifests and tier files:

```text
configs/topologies/monolith/{topology.toml,nodes/*.toml}
configs/topologies/physical/{topology.toml,nodes/*.toml}
```

Add a `[[nodes]]` table to `cloud.toml`, `fog.toml`, `mist.toml`, `edge.toml`
or `iot.toml`. Node IDs and endpoints must be unique. Different hosts may use
the same port. The runner reads the configured nodes without code changes.

## Test-family selection

Choose the smallest family that answers the research question:

- Smoke tests verify that the infrastructure and execution path work.
- Normal cumulative/scalability benchmarks measure category growth and RDF
  volume/user growth under `sharded` or `replicated` placement.
- Load benchmarks stress independent demand dimensions and collect
  request-level latency, throughput, loss, accuracy, recovery and resources.
- Experiments isolate scale-out, hardware reasoning and genuinely distributed
  ontology placement.
- Study commands generate reproducible workload/mobility traces and aggregate
  category, policy and query costs from measured event data.

`local all`, `physical all` run cumulative plus scalability
only. There is no literal `load all` subcommand: unfiltered `load local`,
`load physical` or `load physical` means all configured load profiles.
`experiment all <target>` runs the three
separated scientific experiments, not the normal or load benchmarks.

## Results and interpretation

Results are written under `outputs/` with metadata describing target,
topology, layout, reasoner, profile, repetitions and budgets. Timeouts are
right-censored observations: they remain visible in coverage reporting and are
not converted into zero latency. Architecture ratios use only matched,
completed rows; Physical speedups use the matching monolith row as
their baseline.

RDFLib, Jena, RDF4J and Oxigraph are exercised without naming each engine:

```bash
continuum-smoke-engines
continuum-bench engines all
continuum-bench engines plot
```

```bash
continuum-bench load plot
continuum-bench experiment plot all
continuum-bench experiment analyze
```

Study traces are deterministic schedules, not measured query executions.
Category-cost analysis only reports resource metrics present in the benchmark
event data.

## Troubleshooting entry points

```bash
continuum-bench doctor
continuum-bench doctor --physical
continuum-bench doctor --owl
continuum-bench physical status --ssh-user pi
```

For installation failures, see [Installation](design/INSTALLATION.md). For
methodological limits and scientific interpretation, see
[Scientific validity](design/SCIENTIFIC_VALIDITY.md).
