# Docker Compose user guide

This guide contains only the local elastic Docker continuum workflow. Shared
installation and semantic acceptance are documented in
[Installation](INSTALLATION.md) and [Tests](TESTS.md).

## Topology

The source of truth is `configs/topologies/docker/topology.toml`. Nodes are
split by continuum tier:

```text
configs/topologies/docker/nodes/cloud.toml
configs/topologies/docker/nodes/fog.toml
configs/topologies/docker/nodes/mist.toml
configs/topologies/docker/nodes/edge.toml
configs/topologies/docker/nodes/iot.toml
```

Add or remove `[[nodes]]` entries in those files. Do not edit the generated
`outputs/runtime/docker-compose-docker.yml`.

```bash
continuum-bench topology validate --name docker
continuum-bench docker render
```

## Lifecycle and diagnostics

```bash
continuum-bench doctor --docker
continuum-bench preflight
docker compose version
docker info
continuum-bench docker up
continuum-bench docker status
continuum-bench docker logs
```

The default topology uses five containers with one CPU and 1 GiB per node.
Docker should therefore have at least 5 GiB available.

## Smoke tests

```bash
continuum-smoke-docker-cumulative
continuum-smoke-docker-scalability
continuum-smoke-docker-load
continuum-smoke-docker-experiments
continuum-smoke-docker-cumulative --layout replicated
continuum-smoke-docker-scalability --layout replicated
```

Smokes verify connectivity, deployment, bounded query execution, result
serialization, zero event loss and semantic reference results. They use
isolated `outputs/smoke/` paths and fail on censored/incomplete rows. They are
not used as performance evidence.

## Normal monitoring benchmarks

```bash
continuum-bench docker cumulative --layout sharded --keep-running
continuum-bench docker scalability --layout sharded --keep-running
continuum-bench docker all --layout replicated --keep-running
```

`docker all` runs cumulative and scalability only. `sharded` evaluates
category/authority placement; `replicated` is the full-replica baseline.

## Complete load matrix

```bash
continuum-bench load docker
```

There is no `continuum-bench load all` subcommand. Running `load docker`
without `--dimension` and `--profile` executes every configured Docker load
profile across events/s, users, target triples, rules and active node count.

Run one dimension or profile when iterating:

```bash
continuum-bench load docker --dimension events_per_second
continuum-bench load docker --dimension users
continuum-bench load docker --dimension target_triples
continuum-bench load docker --dimension rule_count
continuum-bench load docker --dimension node_count
continuum-bench load docker --profile <profile-name>
```

## Complete experiment family

```bash
continuum-bench experiment all docker
```

This runs scale-out, reasoning-by-hardware and distributed-ontology
experiments. Run them independently with:

```bash
continuum-bench experiment scale-out docker
continuum-bench experiment reasoning-hardware docker
continuum-bench experiment distributed-ontology docker
```

## Independent semantic products

```bash
continuum-smoke-engines
continuum-bench engines all
continuum-bench engines plot
```

The engine stack is separate from the five-node continuum and automatically
runs RDFLib, Jena, RDF4J and Oxigraph. First-time image construction is bounded
by `CONTINUUM_COMPOSE_BUILD_TIMEOUT` (600 s by default); service startup is
bounded by `CONTINUUM_COMPOSE_TIMEOUT` and benchmark points by the selected
benchmark TOML.

## Study, plots and shutdown

```bash
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

Keep the stack running throughout load and experiment execution. A timeout is
stored as a censored observation rather than an artificial zero-latency result.
