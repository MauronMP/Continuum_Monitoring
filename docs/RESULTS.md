# Results and Figures

Each run is `outputs/<run-id>/`. It contains campaign and environment manifests, exact configuration, topology, canonical scenario datasets, separate warm-up evidence, and independent layout/repetition directories. Every repetition records worker health before preparation and after the query catalog, phase timings and digests, logical and physical query records, catalog-round totals, container states/image digests, and one-second Docker resource samples. Partial failures are preserved.

`summary/` contains `scalability.csv`, `preparation.csv`, `queries.csv`, `resources.csv`, `node_resources.csv`, `failures.csv`, `failure_causes.csv`, and `summary.json`. `preparation.csv` preserves per-node partition, serialization, transfer, remote-load, RDFS, byte, triple, and digest evidence. `figures/` contains fourteen PNGs for ABox/closure growth, preparation, reasoning, query percentiles, logical throughput, CPU, memory, payload bytes, the completion frontier, layout comparison, and per-node CPU and memory. Timeouts and transport failures remain categorical. Three repetitions support descriptive medians and observed ranges, not strong inferential claims.

- `scalability.csv` is the scenario/layout table: population, actual triples, dataset identity, completion count, timing medians, logical query percentiles/throughput, CPU, memory, network counters, and failures.
- `preparation.csv` is per repetition and node. It is the source for phase-cost and semantic-validation analysis.
- `queries.csv` contains logical-query observations. Per-repetition `physical_queries.json` preserves each worker execution separately.
- `resources.csv` is the unaggregated timestamped Docker/cgroup series. Missing or errored samples remain visible.
- `node_resources.csv` aggregates CPU and memory by physical node only for completed measured repetitions.
- `failures.csv` contains repetition failures and logical query errors without replacing timeouts by numeric values.
- `failure_causes.csv` gives a compact count by normalized transport, timeout, semantic, or memory cause.
- `summary.json` mirrors the main aggregate table for programmatic use.

Figures `01` and `02` verify ABox and materialized-graph growth. `03` and `04` show total preparation and its non-reasoning phases. `05` isolates RDFS. `06` and `07` show logical SPARQL latency percentiles and throughput. `08` and `09` show CPU and container-memory distributions from completed repetitions. `10` compares RDF payload volume. `11` identifies the observed completion frontier. `12` separates completed and failed repetitions by layout and population. `13` and `14` expose per-node CPU p95 and peak memory. Every scalability axis includes the configured population levels through 20000; a red cross or an empty heatmap cell denotes missing valid measurements rather than a zero value.
