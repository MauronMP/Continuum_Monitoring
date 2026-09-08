# Benchmarks

The monitoring module provides reproducible contracts for
physical continuum targets.

`physical all` runs only the cumulative and scalability suites. Load, separated experiments,
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
Its event stream rotates through the complete 115-query catalog so category,
policy and query costs cover all configured categories. Alert precision,
recall and F1 use only the catalog entries explicitly classified as positive
or negative alert checks; report/inspection queries remain in performance
metrics but are excluded from the confusion matrix.
The deterministic schedule interleaves categories and rotates its start between
repetitions, preventing a short low-rate profile from measuring only the first
catalog category.
The three experiments separately measure replicated query scale-out,
reasoning by physical node hardware and authority-partitioned ontology execution.
Reports include only physical observations and retain incomplete points in
coverage tables. Layout comparisons require matched workloads and node counts.

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
reasoner/layout are skipped after the first timeout. Other reasoners continue;
one expensive profile can no longer suppress the rest of the reasoner matrix.
Configuration loading rejects duplicate or decreasing scale values within a
dimension, preventing a manually edited TOML file from invalidating this
early-stop assumption.

Query batches are interleaved for both replicated and sharded execution so
adjacent costly catalog queries are not concentrated in one HTTP request.

Default full-run ceilings are: monitoring request/phase/point = 60/60/90 s;
load request/point/recovery = 45/60/45 s; experiment request/point = 45/60 s.
Monitoring and experiment smokes use request/point = 30/45 s, while load
smokes use request/point/recovery = 45/90/45 s.

Timeout rows retain the configured budget and completion state. They are not
encoded as zero latency, excluded silently or interpreted as successful fast
runs. Cross-architecture ratios are computed only from matching completed
observations; coverage plots expose failed, skipped and censored points.
