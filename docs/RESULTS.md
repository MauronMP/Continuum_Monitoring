# Results and Figures

Each run is `outputs/<run-id>/`. It contains campaign and environment manifests, exact configuration, topology, canonical scenario datasets, separate warm-up evidence, and independent layout/repetition directories. Every layout directory contains `cold-start.json`, proving that all workers were restarted and semantically verified before its warm-up. `semantic-contract/` snapshots the canonical base, all Turtle sources, both semantic manifests, and all 113 query files used by the run. Every repetition records worker health before preparation and after the query catalog, phase timings and digests, logical and physical query records, catalog-round totals, container states/image digests, and one-second Docker resource samples. Partial failures are preserved.

`summary/` contains `scalability.csv`, `preparation.csv`, `queries.csv`, `physical_queries.csv`, `resources.csv`, `node_resources.csv`, `phase_resources.csv`, `failures.csv`, `failure_causes.csv`, and `summary.json`. `preparation.csv` preserves per-node partition, serialization, transfer, parse/digest, store-load, RDFS, byte, triple, and digest evidence. Logical rows retain fan-out, selected/successful/failed/pending hosts, logical and merge durations, and partial evidence. Physical rows retain per-worker timing and status. `phase_resources.csv` separates preparation and query CPU/RAM. `figures/` contains the existing nineteen PNGs plus CPU and memory by phase. Timeouts and failures remain categorical and are excluded from completed-query percentiles. Three repetitions support descriptive medians and observed ranges, not strong inferential claims.

- `scalability.csv` is the scenario/layout table: population, actual triples, dataset identity, completion count, timing medians, logical query percentiles/throughput, CPU, memory, network counters, and failures.
- `preparation.csv` is per repetition and node. It is the source for phase-cost and semantic-validation analysis.
- `queries.csv` contains logical-query observations, including logical/merge latency, fan-out and partial-failure evidence.
- `physical_queries.csv` contains every worker request, its effective timeout, worker execution and end-to-end request latency, status, cardinality, and digest. Scalability summaries use end-to-end request latency when available.
- `resources.csv` is the unaggregated phase-labelled Docker/cgroup series. Missing or errored samples and phase transitions remain visible.
- `node_resources.csv` aggregates CPU and memory by physical node only for completed measured repetitions.
- `phase_resources.csv` aggregates CPU and memory separately for `preparation` and `queries`.
- `failures.csv` contains repetition failures and logical query errors without replacing timeouts by numeric values.
- `failure_causes.csv` gives a compact count by normalized transport, timeout, semantic, or memory cause.
- `summary.json` mirrors the main aggregate table for programmatic use.

Figures `01` and `02` verify ABox and materialized-graph growth. `03` reports `T_ready`; `04` retains the preparation components and `05` isolates RDFS. `06` and `07` show completed logical-query latency and throughput. `08` and `09` retain global CPU/RAM. `10`--`19` preserve payload, frontier, layout, node, category, query and compute comparisons. `20` and `21` compare CPU p95 and peak memory between preparation and queries. Every scalability axis includes all configured population levels; a red cross or an empty cell denotes missing valid measurements rather than zero.

Population axes represent the sixteen configured experiment levels as ordered, equally spaced categories. This avoids compressing the high-load frontier from 10000 to 20000 users and makes adjacent campaign outcomes directly readable; the spacing must not be interpreted as a continuous numeric distance. Every figure labels all populations (`1`, `50`, `100`, `500`, `1k`, `2k`, `4k`, `5k`, `6k`, `7k`, `10k`, `12k`, `14k`, `16k`, `18k`, and `20k`); labels are rotated rather than omitted.

Generated campaigns are ignored by Git. `outputs/README.md` remains versioned as the format guide. Before publication, retain one explicitly selected campaign, its manifest, raw evidence, summaries, and figures; do not combine repetitions from different semantic or query fingerprints.
