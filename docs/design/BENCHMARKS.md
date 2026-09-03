# Core benchmark methodology

## Purpose

The core benchmark has two suites that answer different questions:

- cumulative: how query workload grows as monitoring capabilities are added;
- scalability: how the complete workload reacts to larger deterministic ABox
  volumes.

Both use the same ontology, query catalog, seed, reasoner list and output
contract. They are available in monolithic, replicated and authority-sharded
deployments.

## Reasoning profiles

| Profile | Implementation | Meaning |
|---|---|---|
| `rdfs` | RDFLib closure with literal-value guard | RDFS entailment |
| `owlrl` | OWL-RL | OWL 2 RL rule closure |
| `rdfs_owlrl` | RDFS followed by OWL-RL | Combined experimental profile |

These profiles are separate from the product comparison involving RDFLib,
Apache Jena, Eclipse RDF4J and Oxigraph. Oxigraph is the no-entailment SPARQL
control.

## Full and smoke configurations

- `configs/benchmark.toml`: publication-oriented categories, volumes,
  reasoners and repetitions;
- `configs/smoke-cumulative.toml`: one short cumulative repetition;
- `configs/smoke-scalability.toml`: two small user volumes.

The random seed makes generated IRIs and values deterministic. Each measured
repetition rebuilds the relevant graph; mutable closure state is not shared
between reasoners.

## Cumulative experiment

The base graph is materialized once for each reasoner and repetition. Query
categories are then activated in the configured order. At stage N, every query
from stages 1 through N is executed.

Independent variable:

- cumulative category count and corresponding query count.

Measured fields include:

- input, output and inferred triples;
- reasoning time;
- total query time;
- mean and p95 query latency;
- stage total time;
- per-query duration, result count, ASK value and digest.

Reasoning time is displayed with each stage because it is part of end-to-end
deployment cost, but it is not re-executed separately for every category stage.

## Scalability experiment

For every configured `scale_users` value, the runner copies the same base graph
and deterministically adds users, devices, states, observations, contracts and
related resources. Every point is independent: a 1,000-user point does not
contain a previous point plus 1,000 new users.

Independent variable:

- total synthetic user count, with resulting synthetic and input triples.

Measured fields include generation, reasoning and query time, inferred triples,
mean/p95 query latency and queries per second. The full 115-query battery is
executed at every point.

## Monolithic commands

```bash
.venv/bin/continuum-bench benchmark cumulative
.venv/bin/continuum-bench benchmark scalability
.venv/bin/continuum-bench benchmark all
```

The independent product stack runs automatically. Add `--python-only` to
exclude it intentionally.

## Distributed timing

Distributed suites report wall time. Per-node CPU time and work sums are cost
metrics, not latency and must not be substituted for wall time.

Replicated total time contains parallel prepare plus scheduled query wall time.
Sharded total time contains parallel fragment prepare plus federated query wall
time. Monolithic-oracle validation is outside the measured phase and is marked
in metadata.

## Repetitions, warm-ups and statistics

Smoke configurations use one repetition. Publication runs should use the full
configuration, at least one unmeasured warm-up for product engines and enough
measured repetitions to report median and dispersion. Preserve raw rows rather
than only plotted aggregates.

Run architectures in a randomized or counterbalanced order when thermal drift,
background services or network conditions may bias a fixed order.

## Reproducibility metadata

Every result directory records release identity, ontology graph digest,
reasoners, repetitions, seed and architecture-specific information. Distributed
runs also record endpoints and topology fingerprints.

Record external controls that software cannot infer reliably: CPU governor,
cooling, power mode, network, concurrent load and Docker resource settings.

## Interpretation limits

- Cumulative results reflect repeated execution of the growing query set, not
  only the newly added category.
- User count is a workload generator input, not a direct real-world device
  population claim.
- More nodes are not expected to help when fixed overhead dominates.
- Replicated scale-out measures query service, not distributed inference.
- Sharded performance includes semantic placement and federation overhead.
- A timeout is a right-censored observation and must remain in reporting.
- The default acceptance ceiling is 60 seconds per phase/request and 90 seconds
  per complete point (30/45 seconds for smoke). After the first scalability
  timeout, larger points for that engine or topology are recorded as skipped.
- Replicated physical calibration uses a stratified sample capped by
  `calibration_query_limit`; it does not execute the full catalog on every node.
- Comparisons require matched configurations and equivalent query results.

See [LOAD_BENCHMARKS.md](LOAD_BENCHMARKS.md) for event-rate, rule, triple and
node-count dimensions and [THREE_EXPERIMENTS.md](THREE_EXPERIMENTS.md) for the
deconfounded architecture experiments.
