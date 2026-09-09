# User guide

This page contains the workflow shared by every execution target. Operational
instructions are intentionally separated:

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

The physical continuum has one manifest and per-tier inventory files:

```text
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

`physical all` runs cumulative and scalability suites. `load physical` runs
all configured load profiles, and `experiment all physical` runs the three
separate scientific experiments.

## Run all physical tests

After authorizing SSH, deploying workers and installing the external OWL validators:

```bash
continuum-bench --unlimited --repetitions 5 suite --dry-run
continuum-bench --unlimited --repetitions 5 suite
```

The suite includes software/semantic checks, both monitoring layouts, load,
three physical experiments, the ten-axis campaign and PNG reporting. It starts
already-installed workers and saves each run in a new directory under
`outputs/suites`. Native engine comparisons and study traces remain separate.

Use `--unlimited` to finish benchmark operations regardless of their configured
elapsed-time budgets. Use `suite --patient` for finite one-hour budgets instead.
Neither mode hides incorrect results, queue loss or infrastructure errors.
Health/startup and external OWL validation retain separate limits. See the
[test catalogue](design/TESTS.md) for all new regressions, filtered runs, output
contracts and a real-node smoke that exceeds its nominal budget.

For individual ten-axis runs:

```bash
continuum-bench campaign --campaign-config configs/campaign.toml --validate-only
continuum-bench --unlimited campaign --campaign-config configs/campaign.toml
```

## Results and interpretation

Results are written under `outputs/` with metadata describing target,
topology, layout, reasoner, profile, repetitions and budgets. Unlimited runs
record their execution policy explicitly. In bounded mode, timeouts are
right-censored observations: they remain visible in coverage reporting and are
not converted into zero latency. Compare completed physical observations with
matching workloads and disclose node counts and placement layouts.

RDFLib, Jena, RDF4J and Oxigraph are exercised without naming each engine:

```bash
continuum-smoke-engines
continuum-bench engines all
continuum-bench engines plot
```

```bash
continuum-bench report
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

[Publication reports](design/PUBLICATION_REPORTS.md) explains PNG figures, category
and policy costs, historical missing measurements and analytical distance scenarios.
