# Multidimensional load and scalability benchmark

## Purpose and scope

This benchmark measures how the same semantic alert workload behaves under
increasing load in three deployment architectures:

1. a monolithic process on one computer;
2. an elastic local Docker topology;
3. an elastic physical continuum topology.

The test complements the cumulative and ABox-size suites. Distributed runs use
replicated logical graphs so that query scale-out can be measured independently
from ontology partitioning. The distributed-ontology experiment described in
[Three controlled architecture experiments](THREE_EXPERIMENTS.md) evaluates
authority-based partitioning separately.

The active architecture is loaded from `configs/topology.toml`. For a profile
with `node_count = N`, the coordinator selects the first N enabled nodes in the
deterministic order declared by the architecture's layer manifests. The run
fails before measurement if fewer than N nodes are available.

## Event and workload model

One event is one SPARQL alert evaluation. The workload cycles deterministically
through 26 queries with known outcomes:

- five `ASK` queries expected to return `true`;
- 21 violation queries expected to return zero rows.

Events are scheduled at a constant arrival rate and accepted events are grouped
up to `batch_size`. No event runs before its scheduled arrival time. A bounded
central queue holds at most `queue_capacity_events`; excess, timed-out, or
failed events are recorded as lost instead of being silently discarded.
Accepted batches are assigned round-robin to the active nodes.

Each measurement point performs these phases in order:

1. rebuild the v3.0.0 reference graph;
2. generate deterministic users, devices, states, and contracts;
3. add a deterministic synthetic `rdfs:subClassOf` rule chain;
4. pad the graph to the exact requested triple count;
5. materialize RDFS, OWL RL, or RDFS+OWL RL closure;
6. execute the timed event stream;
7. discard application state and rebuild it to measure recovery.

Recovery means reconstructing the semantic application state. It does not
include rebooting the operating system, Docker daemon, container, or physical
device.

## Independent variables

`configs/load-benchmark.toml` defines a one-factor-at-a-time design. Only the
named dimension changes within a series; the other factors remain at that
series' baseline.

| Dimension | Default levels |
| --- | --- |
| Events per second | 50, 200, 500, 1,000, 2,500 |
| Synthetic users | 500, 1,000, 2,500, 5,000, 10,000 |
| Target triples per node | 25,000, 50,000, 100,000, 250,000, 500,000 |
| Synthetic rules | 0, 25, 50, 100, 250 |
| Active nodes | 1, 3, 5 |

The full configuration uses three repetitions per point and runs every
reasoning profile enabled in `configs/benchmark.toml`. The smoke configuration
in `configs/load-smoke.toml` preserves the protocol with small volumes and one
repetition. A smoke result verifies integration only; it is not a statistically
meaningful performance sample.

## Measured variables

| Metric | Definition |
| --- | --- |
| `latency_p50_ms`, `latency_p95_ms`, `latency_p99_ms` | Time from scheduled arrival to response, including queueing, transport, and SPARQL execution. |
| `events_processed_per_second` | Completed events divided by the measured event-phase wall time. |
| `events_lost`, `event_loss_percent` | Events rejected because of queue capacity, timeout, or execution error. |
| `inference_wall_ms` | Critical-path materialization time: the maximum across nodes prepared in parallel. |
| `alert_precision` | `TP / (TP + FP)`. |
| `alert_accuracy` | `(TP + TN) / processed`; recall and F1 are also stored. |
| `process_cpu_time_ms` | Aggregate process CPU time observed during the run. |
| `cpu_percent_per_node_one_core` | CPU time normalized by wall time, node count, and one logical core. |
| `max_current_rss_kib` | Largest current RSS sampled at phase or batch boundaries. |
| `max_peak_rss_kib` | Maximum process high-water mark reported by the platform. |
| `disk_read_bytes`, `disk_write_bytes`, `disk_io_bytes` | Process I/O counters from `/proc/self/io`; zero when the platform cannot expose them. |
| `network_body_bytes` | JSON request and response body bytes; excludes HTTP headers and lower network layers. |
| `recovery_wall_ms` | Critical-path time to reconstruct application state. |

The output also records the timeout phase, confusion matrix, complete phase
timings, and per-node metrics.

## Timeout semantics

Three independent limits are configured in the load TOML file:

- `request_timeout_seconds`: one prepare or HTTP request;
- `point_timeout_seconds`: the complete event phase for one point;
- `recovery_timeout_seconds`: state reconstruction.

A timeout remains an observation. The row records its status, phase, and limit,
and unfinished events count as lost. The local coordinator enforces the point
deadline. Distributed workers also arm an internal timeout one second before
the HTTP deadline so that interrupted Python reasoning releases its lock and
the worker remains usable for the next profile.

## Prerequisites

Complete the common installation and validation first:

```bash
python3 tools/bootstrap.py --with-docker
.venv/bin/continuum-bench doctor --docker
.venv/bin/continuum-bench validate
```

For Docker, start or rebuild the configured topology:

```bash
.venv/bin/continuum-bench topology down --name docker
.venv/bin/continuum-bench topology up --name docker
.venv/bin/continuum-bench topology status --name docker
```

For physical nodes, deploy the same revision and verify every endpoint:

```bash
.venv/bin/continuum-bench physical stop --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi
```

Passwordless SSH is strongly recommended. See
[Physical continuum deployment](PHYSICAL_CONTINUUM.md).

## Smoke runs

Run each architecture independently:

```bash
.venv/bin/continuum-bench load monolith \
  --load-config configs/load-smoke.toml \
  --output-dir outputs/load-smoke

.venv/bin/continuum-bench load docker \
  --load-config configs/load-smoke.toml \
  --output-dir outputs/load-smoke

.venv/bin/continuum-bench load physical \
  --load-config configs/load-smoke.toml \
  --output-dir outputs/load-smoke
```

## Full runs

Run one architecture at a time to avoid resource contention:

```bash
.venv/bin/continuum-bench load monolith
.venv/bin/continuum-bench load docker
.venv/bin/continuum-bench load physical
```

If the Docker and physical topologies are already healthy, the following
command executes all three in coordinator-defined order:

```bash
.venv/bin/continuum-bench load all
```

Filter a full design without editing TOML:

```bash
# One complete independent-variable series
.venv/bin/continuum-bench load monolith --dimension target_triples
.venv/bin/continuum-bench load docker --dimension events_per_second

# One or more named points
.venv/bin/continuum-bench load physical --profile nodes-5
.venv/bin/continuum-bench load physical \
  --profile triples-100000 --profile triples-250000
```

`--dimension` and `--profile` are repeatable. When both are supplied, only
profiles in their intersection run.

## Output files

Each architecture directory contains:

- `summary.csv`: one row per profile, reasoner, and repetition;
- `event-runs.csv`: event-level status, latency, and correctness;
- `node-runs.csv`: node-level phase timing and resource metrics;
- metadata and generated figures where applicable.

Keep all CSV and metadata files with any published figure. The node table is
required to distinguish cloud, fog, mist, edge, and IoT costs.

## Generate figures

```bash
.venv/bin/continuum-bench load plot
.venv/bin/continuum-bench load plot --show
```

The report exports 300 dpi PNG plus vector PDF and SVG for every dimension. It
includes:

- p95 latency with a p50-p99 band, throughput, loss, inference time, total
  time, and timeout rate;
- alert correctness, CPU, RSS, disk, network, and recovery;
- latency, throughput, inference, and recovery ratios against the monolith;
- scale-out efficiency and event-loss differences;
- data-coverage matrices by architecture, reasoner, profile, and repetition;
- a reference overview at 200 events/s and at peak offered load.

Complete points show the median and minimum-maximum range. Hollow markers
identify incomplete points. Zeros caused by failed preparation are excluded
from inference, recovery, and resource aggregates. These ranges are descriptive,
not confidence intervals.

## Interpretation and publication limits

- Compare only matching ontology revision, query catalog, seed, reasoner,
  profile, and completed repetition count.
- Read latency and throughput together with event loss and timeout coverage.
- A distributed system may finish faster while consuming more aggregate CPU,
  memory, and network capacity.
- The replicated test evaluates query distribution, not semantic authority
  partitioning.
- Increase repetitions and predefine a statistical analysis before using the
  results to support a scientific claim.
- Record hardware, operating system, container limits, background load,
  thermal state, and dependency versions with the final dataset.

See [Scientific validity and limitations](SCIENTIFIC_VALIDITY.md) for the
claim boundary.
