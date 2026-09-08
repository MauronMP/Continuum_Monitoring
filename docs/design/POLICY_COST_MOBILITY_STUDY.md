# Policy-category cost and mobility study

This module extends local and physical monitoring benchmarks with a
configuration-driven study layer. Its purpose is to keep policy-category cost analysis,
query-complexity characterization, ontology placement, mobility and network
conditions explicit and reproducible.

The study layer does not modify ontology classes, SPARQL query definitions or
physical worker services. It generates datasets that can be replayed or joined
with benchmark outputs.

## Separation of concerns

| Concern | Module |
| --- | --- |
| Study configuration | `continuum_bench.monitoring.study.config` |
| Request and mobility records | `continuum_bench.monitoring.study.models` |
| SPARQL structural features | `continuum_bench.monitoring.study.sparql` |
| Mobility strategies | `continuum_bench.monitoring.study.mobility` |
| Distance-aware link estimates | `continuum_bench.monitoring.study.network` |
| Placement and locality estimates | `continuum_bench.monitoring.study.placement` |
| Trace generation | `continuum_bench.monitoring.study.workload` |
| Category/policy/query aggregation | `continuum_bench.monitoring.study.analysis` |

## Configuration

The default study configuration is:

```text
configs/policy-cost-study.toml
```

It declares request count, duration, client count, workload distribution,
arrival model, open/closed-loop mode, concurrency, mobility model, network
model, ontology placement and scheduler strategy. `open_loop` is the default
so offered arrivals do not slow down merely because a previous request is
slow; the generated trace is still a schedule and must be replayed by an
execution adapter for measured request-level timings.

The same seed produces the same request sequence and static positions, so
different placement or scheduling strategies can be compared with equivalent
inputs.

## Generated datasets

```bash
.venv/bin/continuum-bench study trace --target local \
  --output-dir outputs/study/local

.venv/bin/continuum-bench study trace --target physical \
  --output-dir outputs/study/physical

# Generate it against the physical topology
.venv/bin/continuum-bench study trace --target physical \
  --output-dir outputs/study/physical
```

creates:

| Output | Meaning |
| --- | --- |
| `request-trace.csv` | One row per generated request, including category, policy, query, client, placement, routing, estimated network cost and locality. |
| `mobility-trace.csv` | One row per mobility sample, including position, speed, direction, association, connectivity and handover state. |
| `query-features.csv` | One row per SPARQL query with structural features such as triple patterns, basic graph patterns, joins, filters, OPTIONAL, UNION, aggregation and a query-shape label. |
| `connectivity-events.csv` | Reserved connectivity-event format; static traces contain headers and no handovers. |
| `metadata.json` | Study ID, seed, topology, placement, scheduler, mobility and network configuration. |

## Category-cost aggregation

After running a physical load benchmark, aggregate request-level observations:

```bash
.venv/bin/continuum-bench study category-cost \
  --events outputs/load/physical/event-runs.csv
```

Use `outputs/load/local/event-runs.csv` or
`outputs/load/physical/event-runs.csv` for the other targets and write each
analysis to a separate output directory. The trace generator does not execute
the scheduled requests: `execution_mode` and `concurrency` describe a
replayable workload contract, while measured timing and resource values must
come from load/benchmark event rows.

The load event stream rotates through all 115 catalog queries; consequently,
the command can produce category, policy and query summaries for all 16
configured categories. It reports popularity,
completion rate, latency percentiles, mean execution time, structural
complexity and accumulated latency impact.

For a completed microbatch, query CPU, disk and HTTP-body bytes are attributed
in proportion to measured query duration. Batch RSS is an observed stock: the
analysis reports its mean and maximum but never adds memory samples as if they
were consumable work. The attribution method is persisted in each event row.
Queries linked to multiple policies contribute `1/N` request and resource
equivalents to each policy; policy popularity and completion rates therefore
remain normalized instead of double-counting multi-policy queries.

The analysis intentionally preserves independent metrics. It does not collapse
latency, CPU, memory, network and energy into a single scalar score. Composite
scores should only be introduced later with explicit, documented weights.

## Interpretation

The study distinguishes frequently requested categories, expensive categories,
categories with high total impact because they are both frequent and costly,
and categories whose cost is explained by SPARQL structure rather than semantic
theme alone.

Only static positions are implemented. Dynamic mobility models require a future plugin.
