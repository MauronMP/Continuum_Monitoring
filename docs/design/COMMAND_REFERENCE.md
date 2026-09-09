# Command reference

Run these commands from the repository root after activating `.venv`. Commands
are grouped so that each block can be repeated independently.

Target-specific preparation is documented separately in the
[physical continuum guide](PHYSICAL_CONTINUUM.md).

## A. Repository acceptance block

```bash
continuum-bench doctor --physical --owl
continuum-bench topology validate --name physical
continuum-bench validate
continuum-bench preflight
continuum-bench owl-validate
python -m pytest
python3 tools/check_documentation.py
git diff --check
```

For a release in an environment where all external reasoners are installed,
replace `owl-validate` with `owl-validate --require-all`.


## B. Physical deployment and individual execution

Edit `configs/topologies/physical/nodes/*.toml` first.

```bash
continuum-bench doctor --physical
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
continuum-bench campaign --campaign-config configs/campaign.toml

continuum-bench study trace --target physical \
  --output-dir outputs/study/physical
continuum-bench study category-cost \
  --events outputs/load/physical/event-runs.csv \
  --output-dir outputs/study/physical-cost

continuum-bench report
continuum-bench load plot
continuum-bench experiment plot all
continuum-bench experiment analyze
continuum-bench physical stop --ssh-user pi
```

Category/policy/query cost files are written below
`outputs/study/physical-cost/category-cost/`. This analysis is not included in
`physical all` or `load physical`; it consumes the load event dataset.

## C. Independent semantic-product block

```bash
continuum-smoke-engines
continuum-bench engines cumulative
continuum-bench engines scalability
continuum-bench engines all
continuum-bench engines plot
continuum-bench engines plot --plot-suite cumulative
continuum-bench engines plot --plot-suite scalability
```

Start the native RDFLib, Jena, RDF4J and Oxigraph services first. Each engine
command discovers these services and runs the selected benchmark. It
is distinct from `owl-validate`, which runs HermiT, Openllet, JFact and
Konclude as OWL consistency validators. `engines plot` refuses partial product
summaries, so all four names are guaranteed to appear in a valid figure.

## D. Individual monitoring blocks

```bash
continuum-bench physical cumulative --layout sharded --ssh-user pi
continuum-bench physical scalability --layout sharded --ssh-user pi
```

Replace `sharded` with `replicated` for the replication baseline.

## E. Individual load dimensions

```bash
continuum-bench load physical --dimension events_per_second
continuum-bench load physical --dimension users
continuum-bench load physical --dimension target_triples
continuum-bench load physical --dimension rule_count
continuum-bench load physical --dimension node_count
```

Select one named configuration with
`--profile <profile-name>`.

## F. Individual scientific experiments

```bash


continuum-bench experiment scale-out physical
continuum-bench experiment reasoning-hardware physical
continuum-bench experiment distributed-ontology physical
```

## G. Custom configuration files

Global options precede the subcommand:

```bash
continuum-bench --config configs/benchmark.toml validate
continuum-bench --topology-file configs/topologies/physical/topology.toml \
  topology validate --name physical
```

Subcommand-specific options follow their subcommand. Use `continuum-bench
<command> --help` before starting a long campaign.

## H. Complete physical suite without elapsed-time cutoffs

After deployment and installation of the external OWL validators:

```bash
continuum-bench --unlimited --repetitions 5 suite --dry-run
continuum-bench --unlimited --repetitions 5 suite
```

The first command records the plan without contacting workers. The second runs
software/semantic checks, worker startup, both monitoring layouts, load, all
three experiments, the full ten-axis campaign and PNG reporting sequentially.
Each run gets its own `outputs/suites/<UTC-time>-<id>/` directory and logs.
Native semantic-product benchmarks and study traces remain separate commands.

Select families or retain finite limits:

```bash
continuum-bench --unlimited suite --families monitoring load experiments campaign report
continuum-bench suite --patient
continuum-bench --timeout-seconds 7200 --repetitions 5 suite --patient
```

`--patient` uses finite one-hour budgets and disables timeout pruning.
`--unlimited` disables benchmark elapsed-time cutoffs, including worker alarms
and HTTP waits. Nominal budgets remain in the evidence as unenforced values.
Health/startup and external validator limits remain separate operational checks.
Errors and incomplete results remain visible. See [Tests](TESTS.md) for policies,
regression coverage, cancellation and output contracts.

## I. Individual unlimited runs and smoke configuration

```bash
continuum-bench --unlimited physical all --layout sharded
continuum-bench --unlimited physical all --layout replicated
continuum-bench --unlimited load physical
continuum-bench --unlimited experiment all physical
continuum-bench --unlimited campaign --campaign-config configs/campaign.toml
continuum-bench --unlimited campaign --campaign-config configs/campaign.toml --axis policies --axis query_complexity
continuum-bench --timeout-seconds 6 --unlimited --repetitions 1 load physical --load-config configs/load-smoke.toml --output-dir outputs/audit/unlimited-load
```

`physical all` includes only cumulative/scalability. `campaign` without an
explicit configuration uses the smoke configuration. Global flags precede the
command; family-specific flags follow it.

## J. Publication figures and evidence

```bash
continuum-bench report
continuum-bench report --validation-dir outputs/audit/patient-load/physical
continuum-bench report --input-dir outputs --output-dir outputs/paper
```

Use `--validation-dir` only when that separate measured load dataset exists.
For a saved suite, set `--input-dir` to its actual run directory and choose its
`paper/` directory as output. Reports generate only PNG figures with CSV source
statistics, input hashes and integrity/coverage findings. Missing measurements
are not replaced by successful zeros. Distances in `configs/network-scenarios.toml`
are analytical scenarios, not measured geographic latency. See
[Publication reports](PUBLICATION_REPORTS.md) for interpretation.
