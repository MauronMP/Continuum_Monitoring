# Physical continuum user guide

This guide contains only the workflow for a coordinator and elastic physical
workers. Docker is not required on Raspberry Pi nodes.

## Complete physical suite: copy-and-run order

After editing the topology, the complete workflow is:

```bash
. .venv/bin/activate
continuum-bench doctor --physical
continuum-bench topology validate --name physical
continuum-bench validate
continuum-bench preflight
continuum-bench physical authorize --ssh-user pi
continuum-bench physical stop --ssh-user pi
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

continuum-bench study category-cost \
  --events outputs/load/physical/event-runs.csv \
  --output-dir outputs/study/physical-cost
continuum-bench load plot
continuum-bench experiment plot all
continuum-bench experiment analyze
continuum-bench physical stop --ssh-user pi
```

The two `physical all` commands are different experimental treatments, not
duplicates. Neither includes load, experiments or category-cost analysis.

## Topology

The source of truth is `configs/topologies/physical/topology.toml`. Nodes are
split by continuum tier:

```text
configs/topologies/physical/nodes/cloud.toml
configs/topologies/physical/nodes/fog.toml
configs/topologies/physical/nodes/mist.toml
configs/topologies/physical/nodes/edge.toml
configs/topologies/physical/nodes/iot.toml
```

Each `[[nodes]]` entry defines identity, SSH host, HTTP endpoint, hardware,
network capacity, location, authority and semantic categories. Add or remove
nodes without changing Python code.

The current laboratory inventory is:

| Node | Address | Semantic endpoint |
| --- | --- | --- |
| Cloud coordinator | `127.0.0.1` | `http://127.0.0.1:8391` |
| Fog | `10.151.73.241` | `http://10.151.73.241:8391` |
| Edge 1 | `10.151.73.34` | `http://10.151.73.34:8391` |
| Edge 2 | `10.151.73.143` | `http://10.151.73.143:8391` |
| Edge 3 | `10.151.73.173` | `http://10.151.73.173:8391` |

```bash
continuum-bench topology validate --name physical
continuum-bench doctor --physical
```

## Initial authorization and deployment

Install Python 3.11+, `venv`, `rsync`, `procps` and an SSH server on every
worker. Then run from the coordinator:

```bash
continuum-bench physical authorize --ssh-user pi
continuum-bench physical deploy --ssh-user pi
continuum-bench physical start --ssh-user pi
continuum-bench physical status --ssh-user pi
```

`authorize` installs SSH keys so passwords are neither repeatedly requested nor
stored in configuration. `deploy` creates the lightweight `.venv-node` suited
to 32-bit Raspberry Pi workers and synchronizes the required project files.

## Smoke tests

```bash
continuum-smoke-physical-cumulative --ssh-user pi
continuum-smoke-physical-scalability --ssh-user pi
continuum-smoke-physical-load
continuum-smoke-physical-experiments
continuum-smoke-physical-cumulative --layout replicated --ssh-user pi
continuum-smoke-physical-scalability --layout replicated --ssh-user pi
```

The monitoring smokes accept `--ssh-user` because they load the physical
inventory through the physical command. Load and experiment smokes use the
already-running endpoints from the topology and therefore need no SSH option.
Every smoke fails on timeout, skipped/incomplete result, semantic-reference
failure or event loss. They are not performance evidence.

## Normal monitoring benchmarks

```bash
continuum-bench physical cumulative --layout sharded --ssh-user pi
continuum-bench physical scalability --layout sharded --ssh-user pi
continuum-bench physical all --layout replicated --ssh-user pi
```

`physical all` runs cumulative and scalability only. It does not run load,
experiments, studies or validators.

## Complete load matrix

```bash
continuum-bench load physical
```

There is no literal `load all` action. Running `load physical` without filters
executes every configured physical load profile. A focused run uses:

```bash
continuum-bench load physical --dimension events_per_second
continuum-bench load physical --dimension users
continuum-bench load physical --dimension target_triples
continuum-bench load physical --dimension rule_count
continuum-bench load physical --dimension node_count
continuum-bench load physical --profile <profile-name>
```

## Complete experiment family

```bash
continuum-bench experiment all physical
```

This is equivalent to running these three distinct experiments:

```bash
continuum-bench experiment scale-out physical
continuum-bench experiment reasoning-hardware physical
continuum-bench experiment distributed-ontology physical
```

## Mobility, costs and plots

Static topology coordinates anchor the infrastructure. Deterministic client
mobility is generated independently by the study module.

```bash
continuum-bench study trace --target physical \
  --output-dir outputs/study/physical
continuum-bench study category-cost \
  --events outputs/load/physical/event-runs.csv \
  --output-dir outputs/study/physical-cost
continuum-bench load plot
continuum-bench experiment plot all
continuum-bench experiment analyze
```

The trace command prepares a replayable schedule; it does not claim measured
query or resource values. Category-cost analysis consumes measured event rows.

## Category, policy and query workload cost

This is the analysis that determines which semantic categories, policies and
queries generate the most demand. It must be run after `load physical`:

```bash
continuum-bench study category-cost \
  --events outputs/load/physical/event-runs.csv \
  --output-dir outputs/study/physical-cost
```

The command creates:

```text
outputs/study/physical-cost/category-cost/
├── category-cost-summary.csv
├── policy-cost-summary.csv
└── query-cost-summary.csv
```

The summaries include popularity, attributed request equivalents, completion
rate, p50/p90/p95/p99 latency, mean engine time, structural complexity, total
latency impact and any CPU, memory, disk or network fields present in the load
events. CPU, disk and HTTP bytes are attributed from each batch in proportion
to query duration; RSS is reported as a mean/maximum stock measurement. A
query linked to multiple policies contributes `1/N` to each policy,
preventing duplicated total cost.

## Shutdown and troubleshooting

```bash
continuum-bench physical status --ssh-user pi
continuum-bench physical stop --ssh-user pi
```

On timeout, inspect the affected worker's runtime log, memory pressure and
network connectivity. The coordinator records the point as censored and does
not wait indefinitely. A scalability/cumulative timeout skips only larger
points for the same reasoner; the remaining reasoners continue. Load and
reasoning-hardware profiles also stop monotonically per reasoner/dimension.
Re-run `deploy` after code or dependency changes.

An HTTP 408 whose body says `worker phase exceeded Ns` is a bounded benchmark
observation, not a crashed worker. The worker deliberately interrupts inference
or a query batch just before the coordinator's request deadline. The console
uses `status=timeout`, records the point as right-censored, prints every larger
point as `skipped_after_timeout`, continues with other reasoners, and ends with
counts for completed, timed-out and skipped points.

In replicated placement every node materializes the complete graph. Its
preparation wall time is therefore bounded by the slowest active Raspberry Pi;
adding replicas accelerates parallel query service but cannot accelerate that
duplicated inference. Use `--layout sharded` to evaluate distributed ontology
placement. A repeatable `rdfs_owlrl` preparation timeout at the same user block
is the measured saturation frontier for that hardware/profile combination; it
must not be relabeled as a successful exact timing or hidden by an unbounded
timeout.

Balanced replicated queries use interleaved HTTP batches so the expensive
prefix produced by LPT scheduling is distributed across rounds. After updating
this code, stop, deploy and restart every worker before repeating a campaign.
