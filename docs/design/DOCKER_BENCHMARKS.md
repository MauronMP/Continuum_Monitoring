# Elastic Docker benchmarks

## Configuration model

`configs/topologies/docker/topology.toml` defines image, network, resource and
Compose settings. It composes nodes from:

```text
configs/topologies/docker/nodes/
├── cloud.toml
├── fog.toml
├── mist.toml
├── edge.toml
└── iot.toml
```

The initial topology contains one cloud, one fog and three edge services on
host ports 8191-8195. Node count and tier distribution are not hard-coded.

## Prerequisites

```bash
python3 tools/doctor.py --docker
python3 tools/bootstrap.py --with-docker
.venv/bin/continuum-bench topology validate
```

`docker info`, `docker compose version` and `docker buildx version` must work
for the current user without running the benchmark under `sudo`.

## Start and verify

```bash
.venv/bin/continuum-bench topology up --name docker
.venv/bin/continuum-bench topology status --name docker
```

For the default topology:

```bash
curl --fail http://127.0.0.1:8191/health
curl --fail http://127.0.0.1:8192/health
curl --fail http://127.0.0.1:8193/health
curl --fail http://127.0.0.1:8194/health
curl --fail http://127.0.0.1:8195/health
```

Health responses must identify the expected node, tier, ontology/query
contract and topology fingerprint. A generic `status=ok` response is rejected.

## Two data layouts

| Layout | Data | Scheduling | Use |
|---|---|---|---|
| `replicated` | Complete graph on every node | Each logical query assigned once | Query scale-out baseline |
| `sharded` | Tier profile plus authority-owned ABox | One or more sources per execution plan | Distributed ontology |

The default is `sharded`.

Replicated mode prepares active nodes in parallel, then balances queries. It
does not implement distributed reasoning: each selected node materializes a
complete copy.

Sharded mode loads the tier profile declared in
`configs/ontology-placement.toml`, distributes sensitive resources among
privacy authorities and merges partial query results according to
`queries/execution-plan.toml`.

## Separate smoke tests

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  docker cumulative \
  --layout sharded \
  --topology-only \
  --output-dir outputs/docker-smoke-cumulative

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  docker scalability \
  --layout sharded \
  --topology-only \
  --output-dir outputs/docker-smoke-scalability
```

Replicated equivalents:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  docker cumulative \
  --layout replicated \
  --topology-only \
  --output-dir outputs/docker-smoke-cumulative-replicated

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  docker scalability \
  --layout replicated \
  --topology-only \
  --output-dir outputs/docker-smoke-scalability-replicated
```

`--topology-only` excludes the independent RDFLib/Jena/RDF4J/Oxigraph
comparison. Remove it when product and architecture dimensions are both
required.

## Full tests

```bash
.venv/bin/continuum-bench docker cumulative --layout sharded
.venv/bin/continuum-bench docker scalability --layout sharded
.venv/bin/continuum-bench docker all --layout sharded

.venv/bin/continuum-bench docker cumulative --layout replicated
.venv/bin/continuum-bench docker scalability --layout replicated
.venv/bin/continuum-bench docker all --layout replicated
```

The terminal identifies architecture, layout, node, reasoner, repetition,
category/stage or user block and phase. Do not time the shell command as a
substitute for CSV wall-time fields.

## Authority-sharded aliases and fragments

```bash
.venv/bin/continuum-bench sharded docker cumulative
.venv/bin/continuum-bench sharded docker scalability
.venv/bin/continuum-bench sharded docker all
```

Export fragments for inspection without starting a benchmark:

```bash
.venv/bin/continuum-bench fragments \
  --topology-name docker \
  --users 10 \
  --output-dir outputs/fragments/docker
```

The union of exported fragments must reconstruct the logical source graph.
Non-authority fragments must not contain protected resources.

## EXT-Q68 and stale images

If an old container reports a cross-engine EXT-Q68 failure, rebuild all project
images from the current checkout. The current RDFS contract preserves literal
value spaces and prevents Boolean/integer conflation.

```bash
.venv/bin/continuum-bench topology down --name docker
.venv/bin/continuum-bench topology up --name docker
.venv/bin/continuum-bench topology status --name docker
```

The worker health contract also rejects images with an old ontology revision,
query count or reasoning contract.

## Output and comparison

Default architecture results are separated by layout:

```text
outputs/docker/sharded/{cumulative,scalability}/
outputs/docker/replicated/{cumulative,scalability}/
```

Each suite includes summary, detailed query rows, node rows where applicable,
result validation and metadata. Generate comparisons with:

```bash
.venv/bin/continuum-bench compare all
.venv/bin/continuum-report
```

## Scientific limits

- Container nodes share one kernel, host CPU, memory hierarchy and storage.
- CPU and memory caps are limits, not dedicated hardware reservations.
- Bridge networking is not equivalent to a physical continuum network.
- A five-container run is not five independent computers.
- Replicated storage cost grows approximately with active node count.
- Sharded queries may fan out to several authorities; source execution count
  can exceed logical query count.
- Small workloads may be slower than the monolith because HTTP,
  serialization, scheduling and merge overhead dominate.
- Docker results are valid as a local distributed architecture experiment, not
  as evidence of WAN or Raspberry Pi performance.

## Stop and diagnose

```bash
.venv/bin/continuum-bench topology logs --name docker
.venv/bin/continuum-bench topology down --name docker
```

If startup fails, inspect `outputs/runtime/setup/` and run
`python3 tools/doctor.py --docker --json`. Do not delete unrelated containers,
images or volumes as an automatic recovery action.
