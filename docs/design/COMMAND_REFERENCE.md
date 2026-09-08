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


## D. Complete physical suite

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

continuum-bench study trace --target physical \
  --output-dir outputs/study/physical
continuum-bench study category-cost \
  --events outputs/load/physical/event-runs.csv \
  --output-dir outputs/study/physical-cost

continuum-bench load plot
continuum-bench experiment plot all
continuum-bench experiment analyze
continuum-bench physical stop --ssh-user pi
```

Category/policy/query cost files are written below
`outputs/study/physical-cost/category-cost/`. This analysis is not included in
`physical all` or `load physical`; it consumes the load event dataset.

## E. Independent semantic-product block

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

## F. Individual monitoring blocks

```bash
continuum-bench physical cumulative --layout sharded --ssh-user pi
continuum-bench physical scalability --layout sharded --ssh-user pi
```

Replace `sharded` with `replicated` for the replication baseline.

## G. Individual load dimensions

```bash
continuum-bench load physical --dimension events_per_second
continuum-bench load physical --dimension users
continuum-bench load physical --dimension target_triples
continuum-bench load physical --dimension rule_count
continuum-bench load physical --dimension node_count
```

Select one named configuration with
`--profile <profile-name>`.

## H. Individual scientific experiments

```bash


continuum-bench experiment scale-out physical
continuum-bench experiment reasoning-hardware physical
continuum-bench experiment distributed-ontology physical
```

## I. Custom configuration files

Global options precede the subcommand:

```bash
continuum-bench --config configs/benchmark.toml validate
continuum-bench --topology-file configs/topologies/physical/topology.toml \
  topology validate --name physical
```

Subcommand-specific options follow their subcommand. Use `continuum-bench
<command> --help` before starting a long campaign.

## J. What “complete” means

No single `all` command executes every family. A complete evaluation comprises:

1. repository and semantic acceptance checks;
2. cumulative and scalability in both layouts;
3. multidimensional load;
4. scale-out, reasoning-hardware and distributed-ontology experiments;
5. the RDFLib/Jena/RDF4J/Oxigraph product matrix;
6. trace/cost artefacts and plots.

Sharded and replicated runs are distinct experimental treatments and use
different output metadata.
