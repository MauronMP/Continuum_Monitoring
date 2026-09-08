# Command reference

Run these commands from the repository root after activating `.venv`. Commands
are grouped so that each block can be repeated independently.

Target-specific preparation is documented separately in the
[Docker Compose guide](DOCKER_COMPOSE_GUIDE.md) and the
[physical continuum guide](PHYSICAL_CONTINUUM.md).

## A. Repository acceptance block

```bash
continuum-bench doctor --docker --physical --owl
continuum-bench topology validate --name monolith
continuum-bench topology validate --name docker
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

## B. Complete monolith suite

```bash
continuum-smoke-local-cumulative
continuum-smoke-local-scalability
continuum-smoke-local-load
continuum-smoke-local-experiments

continuum-bench local all
continuum-bench load local
continuum-bench experiment all local
continuum-bench study trace --target local \
  --output-dir outputs/study/local
continuum-bench study category-cost \
  --events outputs/load/local/event-runs.csv \
  --output-dir outputs/study/local-cost
```

The monolith provides the native one-node baseline used by architecture
comparisons. See the [monolith guide](MONOLITH_GUIDE.md).

## C. Complete Docker suite

```bash
continuum-bench docker render
continuum-bench docker up
continuum-bench docker status

continuum-smoke-docker-cumulative
continuum-smoke-docker-scalability
continuum-smoke-docker-load
continuum-smoke-docker-experiments

continuum-bench docker all --layout sharded --keep-running
continuum-bench docker all --layout replicated --keep-running
continuum-bench load docker
continuum-bench experiment all docker

continuum-bench study trace --target docker \
  --output-dir outputs/study/docker
continuum-bench study category-cost \
  --events outputs/load/docker/event-runs.csv \
  --output-dir outputs/study/docker-cost

continuum-bench load plot
continuum-bench experiment plot all
continuum-bench experiment analyze
continuum-bench docker down
```

The stack must remain running for load and experiment blocks. `--keep-running`
prevents a benchmark-owned stack from being stopped between blocks.

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

Every engine command runs RDFLib, Jena, RDF4J and Oxigraph automatically. It
is distinct from `owl-validate`, which runs HermiT, Openllet, JFact and
Konclude as OWL consistency validators. `engines plot` refuses partial product
summaries, so all four names are guaranteed to appear in a valid figure.

## F. Individual monitoring blocks

```bash
continuum-bench local cumulative
continuum-bench local scalability
continuum-bench docker cumulative --layout sharded
continuum-bench docker scalability --layout sharded
continuum-bench physical cumulative --layout sharded --ssh-user pi
continuum-bench physical scalability --layout sharded --ssh-user pi
```

Replace `sharded` with `replicated` for the replication baseline.

## G. Individual load dimensions

```bash
continuum-bench load docker --dimension events_per_second
continuum-bench load docker --dimension users
continuum-bench load docker --dimension target_triples
continuum-bench load docker --dimension rule_count
continuum-bench load docker --dimension node_count
```

Replace `docker` with `local` or `physical`, or select one named configuration with
`--profile <profile-name>`.

## H. Individual scientific experiments

```bash
continuum-bench experiment scale-out local
continuum-bench experiment reasoning-hardware local
continuum-bench experiment distributed-ontology local

continuum-bench experiment scale-out docker
continuum-bench experiment reasoning-hardware docker
continuum-bench experiment distributed-ontology docker

continuum-bench experiment scale-out physical
continuum-bench experiment reasoning-hardware physical
continuum-bench experiment distributed-ontology physical
```

## I. Custom configuration files

Global options precede the subcommand:

```bash
continuum-bench --config configs/benchmark.toml validate
continuum-bench --topology-file configs/topologies/docker/topology.toml \
  topology validate --name docker
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

Docker and physical runs are not duplicates: they apply the same workload
contracts to different infrastructures. Sharded and replicated runs are also
distinct experimental treatments and should use different output metadata.
