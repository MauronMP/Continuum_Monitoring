# Cross-architecture comparative report

## Purpose

The comparative report turns compatible monolith, Docker, and physical result
tables into publication-oriented figures and machine-readable summaries. It
does not execute benchmarks and it does not infer that one architecture is
better when required data are missing or semantically incompatible.

## Prerequisites

Before generating the report:

1. run matching cumulative and scalability suites in each architecture;
2. keep the same ontology revision, query catalog, reasoner profiles, synthetic
   seed, levels, and repetition count;
3. confirm that result-validation checks pass;
4. retain all CSV and metadata files at their default or explicitly supplied
   roots.

The default input roots are:

```text
outputs/
outputs/docker/replicated/
outputs/docker/sharded/
outputs/physical/replicated/
outputs/physical/sharded/
```

## Commands

Generate the report with default locations:

```bash
.venv/bin/python tools/generate_comparative_figures.py
```

Equivalent module and installed-entry-point commands are:

```bash
.venv/bin/python -m continuum_bench.reporting
.venv/bin/continuum-report
```

Select every input and display generated PNG files:

```bash
.venv/bin/continuum-report \
  --monolith-dir outputs \
  --docker-dir outputs/docker/replicated \
  --physical-dir outputs/physical/replicated \
  --docker-sharded-dir outputs/docker/sharded \
  --physical-sharded-dir outputs/physical/sharded \
  --output-dir outputs/analysis \
  --show
```

Missing optional physical or sharded inputs are reported and omitted; they are
not fabricated from another architecture.

## Figure families

The base report exports each figure as 300 dpi PNG, PDF, and SVG:

1. `monolith-cumulative`: total time, reasoning/SPARQL decomposition, p95, and
   materialization expansion.
2. `monolith-scalability`: total time, throughput, maximum-volume phase
   decomposition, and inferred triples.
3. `docker-cumulative`: wall time, preparation/query time, per-layer query work,
   and aggregate work per wall second.
4. `docker-scalability`: the corresponding metrics by synthetic volume.
5. `deployment-cumulative`: monolith/Docker times, speedup, parallel efficiency,
   and percentage change.
6. `deployment-scalability`: matched architecture comparisons across configured
   user volumes.
7. `monolith-products-cumulative`: Jena, RDF4J, RDFLib/OWL-RL, and Oxigraph.
8. `monolith-products-scalability`: the four products by volume.
9. `docker-products-cumulative`: product-engine results from the Docker flow.
10. `docker-products-scalability`: the corresponding product volume series.

Oxigraph is labelled as the no-inference SPARQL control. Product figures remain
separate from RDFS, OWL RL, and combined reasoning-profile figures.

When compatible physical and sharded data exist, the report also creates:

- `physical-cumulative` and `physical-scalability`, including per-node cost;
- `architecture-cumulative` and `architecture-scalability` for all three
  architectures;
- `article-cumulative-summary` and `article-scalability-summary` with medians,
  minimum-maximum ranges, speedup, preparation percentage, and effective SPARQL
  throughput;
- `architecture-all-cumulative` and `architecture-all-scalability` covering all
  available placement variants;
- `multi-architecture-*.csv` source tables for independent analysis.

Ranges are descriptive minimum-maximum ranges, not confidence intervals.

## Cost definitions

`docker-node-costs.csv` and `physical-node-costs.csv` aggregate:

- assigned query count;
- sum of SPARQL durations;
- mean latency;
- p95 latency;
- process CPU where available;
- maximum process RSS;
- HTTP JSON body bytes.

The sum of SPARQL duration is a workload proxy that helps reveal imbalance. It
is not monetary cost or energy consumption. RSS is a process high-water mark,
and network bytes exclude HTTP headers and TCP/IP/link overhead.

The report also computes aggregate work intensity:

```text
(sum of node reasoning time + sum of node query time) / wall time
```

This value indicates how much concurrent measured work was sustained per wall
second. It must not be labelled energy efficiency.

## Generated tables

`outputs/analysis/data/` can contain:

- `monolith-reasoner-summary.csv`;
- `docker-reasoner-summary.csv`;
- `physical-reasoner-summary.csv`;
- `docker-node-costs.csv` and `physical-node-costs.csv`;
- `deployment-summary.csv`;
- `product-engine-summary.csv`;
- cumulative and scalability matched comparisons;
- query-by-query architecture validation;
- `three-way-cumulative.csv` and `three-way-scalability.csv`;
- `article-cumulative-summary.csv` and `article-scalability-summary.csv`.

`deployment-summary.csv` identifies the fastest architecture at the largest
matched load point. New validation compares binding-bag digest, cardinality,
and `ASK`. Historical files without a digest are explicitly marked
`validation_level=cardinality_ask` and should not be mixed with exact-digest
claims.

## Publication checklist

- Verify that every plotted series has the intended repetition coverage.
- Keep timeout rate and failure tables with latency figures.
- Confirm result equivalence before discussing speedup.
- Report replicated and authority-sharded layouts as different treatments.
- State that Docker nodes share one host and therefore do not provide the same
  failure or network isolation as physical nodes.
- Publish the CSV source table and metadata for every final figure.
- Use vector PDF or SVG for manuscript figures and retain PNG only as a preview.

For causal claims about scale-out and partitioning, use the stricter analyzer
in [Three controlled architecture experiments](THREE_EXPERIMENTS.md).
