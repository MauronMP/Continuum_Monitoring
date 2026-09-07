# Benchmarks

The monitoring module provides the same benchmark suites for Docker and
physical continuum targets.

Command scope is deliberately explicit: `docker all` and `physical all` run
only the cumulative and scalability suites. Load, separated experiments,
study artefacts and semantic acceptance are independent blocks documented in
the [command reference](COMMAND_REFERENCE.md).

## Cumulative

The cumulative suite adds categories in the order configured in
`configs/benchmark.toml`. At every stage, the coordinator prepares the ontology
on the selected nodes and executes all queries belonging to the accumulated
category set.

This evaluates how monitoring cost grows when a deployment enables more
policy, requirement and ontology modules.

## Scalability

The scalability suite increases synthetic users and generated individuals.
This evaluates how the target responds as ontology size, query demand and
materialisation cost increase.

## Load and separated experiments

The load suite varies events/s, users, triples, rules and active node count.
The three non-confounded experiments separately measure replicated query
scale-out, reasoning by node hardware and authority-partitioned ontology
execution. Docker and physical targets emit the same schemas.

The reporting layer pairs only rows with identical dimension, profile,
reasoner and node count. It reports p95-latency and inference speedups,
throughput gain, recovery speedup, event-loss difference and scale-out
efficiency in both comparison directions. Incomplete or censored pairs remain
in the coverage table but are excluded from ratio claims.

## Layouts

`sharded` distributes ontology fragments and queries according to authority,
privacy class, tier and category.

`replicated` loads a full replica on every active node and assigns queries using
a bounded calibration sample and heterogeneous longest-processing-time
scheduling.

The LPT assignment is transported in interleaved batches: its expensive-first
ordering is spread across HTTP rounds instead of concentrating the most costly
queries in the first request. This changes only transport packing, not node
assignment, query coverage or result semantics.

## Timeouts

A benchmark point is an acceptance test, not an attempt to wait forever. If a
phase exceeds the configured limit, the row is recorded as a censored timeout.
When monotone early stop is enabled, larger scalability points for the same
reasoner/layout are skipped after the first timeout.

Timeout rows retain the configured budget and completion state. They are not
encoded as zero latency, excluded silently or interpreted as successful fast
runs. Cross-architecture ratios are computed only from matching completed
observations; coverage plots expose failed, skipped and censored points.
