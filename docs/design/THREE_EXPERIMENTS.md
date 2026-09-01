# Three controlled architecture experiments

## Why the experiments are separated

One benchmark cannot fairly answer all questions about a continuum ontology.
This project therefore separates three potentially confounded effects:

1. query service scale-out with complete replicas;
2. reasoning scalability across different hardware;
3. a genuinely distributed ontology and ABox.

All three use the RDFS, OWL RL, and RDFS+OWL RL profiles configured in
`configs/benchmark.toml`. Jena, RDF4J, RDFLib/OWL-RL, and Oxigraph belong to the
independent product-engine benchmark. They are not labelled as physical
continuum reasoners unless those products are actually installed and executed
on the physical nodes.

The complete design is in `configs/experiments.toml`; the fast integration
design is in `configs/experiments-smoke.toml`.

## Common preparation

Validate the repository and inspect the resolved elastic topologies:

```bash
.venv/bin/continuum-bench validate
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench topology show --name monolith
.venv/bin/continuum-bench topology show --name docker
.venv/bin/continuum-bench topology show --name physical
```

Rebuild Docker and deploy the identical repository revision to physical nodes:

```bash
.venv/bin/continuum-bench topology down --name docker
.venv/bin/continuum-bench topology up --name docker

.venv/bin/continuum-bench physical stop --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi
```

The coordinator runs on the initiating computer. `configs/topology.toml`
indexes the monolith, Docker, and physical architecture manifests. Each
architecture can contain any supported number of enabled cloud, fog, mist,
edge, and IoT nodes; experiment levels must not request more nodes than the
resolved topology provides.

## Experiment 1: query scale-out with replicas

### Question

How does query throughput and latency change when identical query-serving
replicas are added?

### Method

Every selected node receives a complete, byte-equivalent logical graph. Graph
preparation and materialization are measured but excluded from the primary
query-service metric. A calibration round executes all 115 queries on each
replica. Calibration time is excluded from measured rounds and feeds an
adaptive longest-processing-time scheduler: expensive queries are assigned
first to the endpoint with the smallest predicted load. This avoids assuming
that the PC, containers, and Raspberry Pi devices have equal capacity.

Each query then executes exactly once per measured round. Result equivalence is
checked across replicas.

### Variables and metrics

- Independent variable: active node count from `scale_out.node_counts`.
- Controlled variables: logical dataset, rule count, reasoner, query catalog,
  seed, and measured query rounds.
- Primary metrics: queries/s, round wall time, and p50/p95/p99 engine latency.
- Secondary metrics: query CPU, RSS, assignment per node, replication factor,
  and exact result agreement.

The monolith has only a one-node point. Docker and physical architectures run
every configured level supported by their elastic topology. This experiment
does not measure distributed inference.

### Commands

```bash
.venv/bin/continuum-bench experiment scale-out monolith
.venv/bin/continuum-bench experiment scale-out docker
.venv/bin/continuum-bench experiment scale-out physical
```

Fast integration example:

```bash
.venv/bin/continuum-bench experiment scale-out monolith \
  --experiment-config configs/experiments-smoke.toml \
  --output-dir outputs/experiments-smoke
```

Results are written below
`outputs/experiments/<architecture>/scale-out/` by default.

## Experiment 2: reasoning scalability by hardware

### Question

How long does each individual hardware endpoint take to materialize the same
graph under increasing triples, rules, or users?

### Method

Endpoints are evaluated independently and sequentially. The experiment never
sums the resources of N devices or waits for them as a parallel inference
barrier. It can therefore compare:

- the monolithic process on the coordinator;
- each Docker container;
- the physical cloud endpoint;
- every physical fog, mist, edge, or IoT endpoint.

Profiles vary triples, rules, or users separately. The triple series uses
`padding_mode = "neutral"`, so padding does not create additional
`continuum:User` instances. RDFS may still infer generic axiomatic consequences;
both asserted and materialized triple counts are preserved.

### Metrics

The output includes generation, reasoning, and wall time; asserted, inferred,
and materialized triples; closure-expansion factor; CPU; RSS; disk I/O; and
timeout status. A timeout is right-censored, never converted into a zero.
Endpoint metadata records Python version, platform, processor architecture,
logical CPU count, process width, and Linux memory availability where exposed.

### Commands

```bash
.venv/bin/continuum-bench experiment reasoning-hardware monolith
.venv/bin/continuum-bench experiment reasoning-hardware docker
.venv/bin/continuum-bench experiment reasoning-hardware physical
```

Select named points and one reasoner:

```bash
.venv/bin/continuum-bench experiment reasoning-hardware physical \
  --profile triples-25000 \
  --profile rules-25 \
  --reasoner rdfs
```

Results are written below
`outputs/experiments/<architecture>/reasoning-hardware/`.

## Experiment 3: genuinely distributed ontology

### Question

Can authority-aware ontology and ABox placement reduce critical-path work while
preserving the results of the canonical monolithic graph?

### Method

The logical dataset is identical across architectures:

- monolith: one complete graph and one closure;
- Docker and physical: TBox placement from
  `configs/ontology-placement.toml`, authority-based ABox fragments, local
  materialization, and federated query execution;
- sensitive data remain at their owning edge when policy requires it;
- cloud and fog receive only permitted projections;
- partial results are combined deterministically using binding-bag union or
  logical OR for `ASK`, as declared by `queries/execution-plan.toml`.

After the timed repetitions, every distributed result is checked against the
canonical monolithic oracle. The oracle runs after measurement so that it does
not warm the local cloud endpoint before that endpoint is measured.

### Metrics

- actual storage factor: sum of fragment triples divided by logical graph
  triples;
- largest fragment and per-layer placement;
- preparation time;
- inference sum and critical-path maximum across nodes;
- federated query latency and throughput;
- CPU, memory, and JSON body traffic;
- timeout/censoring status;
- exact result-validation rate against the monolithic oracle.

### Commands

```bash
.venv/bin/continuum-bench experiment distributed-ontology monolith
.venv/bin/continuum-bench experiment distributed-ontology docker
.venv/bin/continuum-bench experiment distributed-ontology physical
```

Results are written below
`outputs/experiments/<architecture>/distributed-ontology/`.

## Run all experiments

Run all three experiments for one architecture:

```bash
.venv/bin/continuum-bench experiment all monolith
.venv/bin/continuum-bench experiment all docker
.venv/bin/continuum-bench experiment all physical
```

Run every available architecture when Docker and physical nodes are already
healthy:

```bash
.venv/bin/continuum-bench experiment all all
```

For controlled measurements, run monolith, Docker, and physical sequentially
and use a documented thermal stabilization period between architectures.

## Figures and hypothesis analysis

Generate figures individually or together:

```bash
.venv/bin/continuum-bench experiment plot scale-out
.venv/bin/continuum-bench experiment plot reasoning-hardware
.venv/bin/continuum-bench experiment plot distributed-ontology
.venv/bin/continuum-bench experiment plot all
.venv/bin/continuum-bench experiment plot all --show
```

Figures are exported as 300 dpi PNG, PDF, and SVG below
`outputs/experiments/figures/`. Complete repetitions are aggregated by median.
Failures and timeouts remain censored and must be read with coverage and timeout
tables.

After all architectures complete, calculate matched comparisons and the formal
claim verdict:

```bash
.venv/bin/continuum-bench experiment analyze
.venv/bin/continuum-bench experiment analyze --show
```

The analysis produces:

- `analysis/scale-out-comparison.csv`: speedup, efficiency, cost, and replica
  equivalence;
- `analysis/hardware-comparison.csv`: endpoint slowdown, CPU, RSS, and graph
  equivalence;
- `analysis/distributed-comparison.csv`: preparation, query, and total speedup;
  CPU/RSS cost; storage factor; censoring; and semantic validation;
- `analysis/claim-verdict.csv`: verdict by architecture and reasoner;
- `analysis/REPORT.md`: a readable explanation of the decision rules.

The analyzer does not assume the continuum wins. A `supported` verdict requires
all of the following at the largest configured level:

1. every required repetition completed;
2. every result matched the oracle;
3. maximum-node throughput exceeded the best observed one-node throughput;
4. maximum-node distributed total time was below the minimum monolithic time,
   or the lower speedup bound exceeded 1x when the monolith timed out.

CPU and RSS remain separate secondary criteria. A shorter wall time does not
imply lower aggregate resource use.

## Correct interpretation

- For scale-out, compare throughput and latency; do not use preparation time to
  claim distributed reasoning.
- For hardware, compare one endpoint with another; do not present the sum of
  device resources as the capacity available to one closure.
- For distributed ontology, compare the same logical dataset, storage factor,
  critical path, and exact result validity.
- Do not compare triples per node as if they were total system triples.
- Confirm `status`, completed repetition coverage, and
  `result_validation_rate = 1` before publishing.
- If the verdict is `not_supported`, report that partitioning overhead or
  hardware limits outweighed the benefit under the measured conditions.
