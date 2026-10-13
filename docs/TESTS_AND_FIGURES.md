# Test, Experiment and Figure Reference

This document is the traceability guide for every active test family. It
explains what each test verifies, which files contain the measured evidence,
which PNG figures are derived from those files and what can be concluded from
each result.

## 1. Four different kinds of test

The project uses the word *test* for several activities. They must not be
interpreted as equivalent evidence.

| Kind | Purpose | Persistent scientific data |
| --- | --- | --- |
| Software test | Check contracts, failure handling, parsers and report logic with controlled fixtures. | No. Pytest writes only its optional JUnit report. |
| Validation gate | Check the ontology, queries, policies, topology and installed reasoners before measurement. | Validation summaries only. |
| Physical experiment | Execute a configured workload on the Cloud–Fog–Mist–Edge workers and record observations. | Yes. CSV/JSON files below `outputs/`. |
| Reporting step | Read recorded evidence and create tables and 300 dpi PNG figures. | Yes, but it never changes the raw measurements. |

A passing software test means that the implementation obeys its contract. It
does not demonstrate physical performance. A scientific claim must be based on
completed and semantically validated rows from a physical experiment.

## 2. Software test suite

Run the complete software suite with the installed native OWL backends enabled:

```bash
CONTINUUM_TEST_NATIVE_OWL=1 \
  .venv/bin/python -m pytest \
  -o addopts= \
  -q \
  -ra \
  --junitxml=outputs/software-tests.xml
```

Pytest uses temporary directories for generated fixtures and figures. It does
not place benchmark PNGs in `outputs/`. The persistent file from the command
above is `outputs/software-tests.xml`.

### 2.1 Core contracts

| Test file | What it checks |
| --- | --- |
| `tests/core/test_catalog.py` | Every catalog query has one unique identifier, executes on the reference graph and preserves the expected result bag and RDF value types. |
| `tests/core/test_core_contracts.py` | Geographic-coordinate validation, the dependency boundary between the reusable core and monitoring adapters, and reasoner registration without backend-specific experiment branches. |
| `tests/core/test_native_reasoners.py` | Native reasoner configuration, missing/corrupt runtime failures, classpath precedence, process-tree timeout termination, unlimited execution, real inference, inconsistency detection and graph-equivalence contracts. |
| `tests/core/test_ontology.py` | English/datatype safety, OWL 2 punning, modular imports, legacy-term preservation, SHACL conformance, configured reasoner profiles and contradictions introduced only by inference. |
| `tests/core/test_partitioning.py` | Exact reconstruction of the canonical graph from authority fragments, privacy placement, query-result equivalence, role-specific fragment builds and preservation of aggregate values. |
| `tests/core/test_reasoners.py` | Correct RDFS treatment of distinct and equivalent literal value spaces. |
| `tests/core/test_synthetic.py` | Deterministic monotonic graph growth, streamed/materialized equivalence, exact target sizes, neutral padding and invalid-growth rejection. |
| `tests/core/test_release.py` | Release inventory, traceability, reported acceptance debt and regeneration of the elastic execution plan. |

Additional ontology boundary checks are implemented in
`tests/core/test_module_boundaries.py`: import closure and placement agreement,
consent domains, vocabulary identity, typed observations, safe namespace migration
and preservation of multiple policy categories in validation, queries and docs.

### 2.2 Physical infrastructure

| Test file | What it checks |
| --- | --- |
| `tests/infrastructure/test_cli_physical.py` | CLI routing, distributed default placement, replicated selection, independent timeout overrides, offline preparation and continuation after timeout. |
| `tests/infrastructure/test_environment.py` | Detection of incomplete installations and reporting of physical/OWL prerequisites. |
| `tests/infrastructure/test_fragment_transport.py` | Fragment serialization, checksums, triple counts, worker materialization, exact assignment and rejection of missing or mismatched fragments. |
| `tests/infrastructure/test_installation.py` | Runtime/package dependency consistency, pinned minimal worker requirements, wheel-based bootstrap and rejection of stale or copied virtual environments. |
| `tests/infrastructure/test_node_telemetry.py` | Worker CPU, RSS, child-process, payload and placement telemetry, including phase-timeout cleanup. |
| `tests/infrastructure/test_physical_cluster.py` | Tailscale inventory, SSH authorization, deployment/start/stop lifecycle, PID handling, stale topology detection and native reasoner deployment requirements. |
| `tests/infrastructure/test_physical_only.py` | Removal of retired nonphysical, monolithic, container and historical comparison paths. |
| `tests/infrastructure/test_processes.py` | Streaming and logging of subprocess output, actionable failures, silent-process bounds and timeout validation. |
| `tests/infrastructure/test_topology.py` | Physical layer inventory, node resources, structured locations, topology serialization and memory-capacity parsing. |

`tests/infrastructure/test_semantic_assets.py` verifies path-independent semantic
fingerprints, same-version file changes, missing inputs, stale worker preparation
and health compatibility. `tests/infrastructure/test_remediation_profiles.py`
checks explicit five-node profiles and retained validation debt.

### 2.3 OWL integration

| Test file | What it checks |
| --- | --- |
| `tests/integration/test_owl_checker.py` | Safe dependency extraction, machine-readable consistency results, profile/consistency separation, heap configuration and HermiT execution. |
| `tests/integration/test_owl_runtime_installation.py` | Isolated Java dependency trees and bounded native Konclude consistency execution. |
| `tests/integration/test_owl_validation.py` | Missing-backend failures, modular import resolution, OWLAPI adapters, isolated classpaths and correct timeout/result classification. |

### 2.4 Monitoring and experiment orchestration

| Test file | What it checks |
| --- | --- |
| `tests/monitoring/test_campaign.py` | Production budgets, equivalent distributed/replicated workloads, real axis growth, timeout continuation, structured results, lease exclusion and unlimited execution. |
| `tests/monitoring/test_configuration_contracts.py` | Ordered scales, supported reasoners and valid early-stop dimensions. |
| `tests/monitoring/test_distributed.py` | Query routing, worker discovery, retry behavior, parallel timeout attribution, preserved worker errors and balanced query batches. |
| `tests/monitoring/test_distributed_reasoning_scalability.py` | Five-backend matrix, exact fragment sizes, strong/weak scaling metrics, right-censored capacity, semantic comparison and all nine scalability figures. |
| `tests/monitoring/test_experiment_config.py` | Production/smoke experiment profiles, explicit reasoning profiles and distinct CLI commands. |
| `tests/monitoring/test_experiment_timeouts.py` | A timed-out scale-out point does not prevent independent reasoners from running. |
| `tests/monitoring/test_load_benchmark.py` | Full load axes, category coverage, latency/throughput/loss/accuracy metrics, queue loss, point deadlines and unlimited draining. |
| `tests/monitoring/test_monitoring_timeouts.py` | A distributed scalability timeout does not stop later reasoners. |
| `tests/monitoring/test_patient_load.py` | Later load profiles remain executable after a preparation timeout. |
| `tests/monitoring/test_physical.py` | Current physical addresses and query assignment across available nodes. |
| `tests/monitoring/test_physical_suite.py` | Both cumulative and scalability families run before incomplete evidence is reported, and timeouts remain censored observations. |
| `tests/monitoring/test_policy_evaluation.py` | Policy decisions match configured ground truth and the four evaluations export reproducible CSV and PNG files. |
| `tests/monitoring/test_preflight.py` | Configured graph targets are feasible and cannot accidentally shrink the canonical graph. |
| `tests/monitoring/test_progress.py` | Progress percentages are printed and `progress.json` is replaced atomically. |
| `tests/monitoring/test_smoke_entrypoints.py` | Smoke commands use isolated outputs, pass the requested layout and reject missing or censored evidence. |
| `tests/monitoring/test_study.py` | Reproducible request traces, query characterization, static positions, explicit future mobility plugins and weighted category selection. |
| `tests/monitoring/test_suite_workflow.py` | The complete suite forwards selected configs/topology, enables native reasoner tests and records JUnit output. |
| `tests/monitoring/test_timeout_skip_policy.py` | Timeout classification, streaks, calibration, skip scopes, recovery, keep-going behavior and unlimited-mode semantics. |
| `tests/monitoring/test_unlimited.py` | Unlimited mode disables coordinator, HTTP and worker deadlines and reaches every physical family. |

### 2.5 Reporting contracts

| Test file | What it checks |
| --- | --- |
| `tests/reporting/test_csv_utils.py` | Stable union of CSV columns and atomic preservation of the previous file on write failure. |
| `tests/reporting/test_diagrams.py` | Ontology-diagram completeness, deterministic exports, truthful relation labels, GraphML identity and actionable Graphviz failures. These tests use temporary outputs; they do not create benchmark figures. |
| `tests/reporting/test_documentation.py` | Documentation links and generated ontology/policy/query references are current. |
| `tests/reporting/test_experiment_reporting.py` | Coverage figures retain timeouts and failures instead of hiding censoring. |
| `tests/reporting/test_load_reporting.py` | Load figures use only profiles present in recorded data. |
| `tests/reporting/test_normalize.py` | Canonical JSONL envelopes preserve historical identity and censoring. |
| `tests/reporting/test_publication.py` | Evidence filtering, semantic validation, matched populations, PNG-only output, figure grouping, rejection gates and suppression of unsupported claims. |
| `tests/reporting/test_result_contract.py` | Reports reject obsolete ontology or result-contract releases. |

## 3. Validation gates before physical execution

Run these checks before starting a long experiment:

```bash
continuum-bench doctor --physical --owl
continuum-bench topology validate
continuum-bench validate
continuum-bench preflight
continuum-bench owl-validate --require-all
continuum-bench campaign \
  --campaign-config configs/campaign.toml \
  --validate-only
.venv/bin/python tools/check_documentation.py
```

These gates answer whether the installation and experimental definitions are
valid. They do not measure performance:

- `doctor` checks local and remote prerequisites;
- `topology validate` checks the physical inventory and node contracts;
- `validate` checks ontology imports, SHACL constraints, policies and queries;
- `preflight` checks graph sizes, profiles and capacity assumptions;
- `owl-validate --require-all` checks consistency with HermiT, Openllet, JFact
  and Konclude;
- campaign validation expands the complete experiment matrix without running
  it;
- the documentation checker detects stale generated references and broken
  internal links.

## 4. Physical cumulative and scalability tests

Both families use `configs/benchmark.toml` and the five active backends: RDFS,
HermiT, Openllet, JFact and Konclude.

### 4.1 Cumulative policy-category test

The cumulative test adds query/policy categories in the configured
`category_order`. Stage 1 contains the first category, stage 2 contains the
first two categories, and so on. It measures the accumulated cost of the active
semantic workload: total wall time, critical node reasoning time, query wall
time, CPU, memory, placement and per-query execution.

This test explains how cost grows as the monitoring knowledge and policy scope
become broader. It is observational: a higher cumulative stage contains a
different query mix, so the difference must not be described as the isolated
causal overhead of one policy.

### 4.2 User scalability test

The scalability test keeps the complete query catalog active and increases the
synthetic user population through `10, 100, 500, 1000, 2500, 5000`. It measures
how reasoning, queries, CPU, memory and end-to-end time change as the ontology
and instance population grow.

This test explains capacity and growth trends. A timeout is a right-censored
observation, not a measured latency value.

### 4.3 Distributed and replicated placement

The same logical points are executed in two placement modes:

- **Distributed** sends authority-aware ontology fragments to the physical
  nodes, routes each query to the required authorities and merges the result.
  `result-validation.csv` compares the merged result with the canonical graph.
- **Replicated** places the complete graph on participating workers and balances
  query execution between them. Each replica has the same ontology, so memory
  and transfer costs can grow with the number of nodes.

Cross-layout figures use only matched scale values completed by both layouts.
They compare observed placement behavior; they do not turn heterogeneous
hardware into a controlled hardware-speedup experiment.

### 4.4 Raw files

Each layout/family directory is located at:

```text
outputs/monitoring/<distributed|replicated>/<cumulative|scalability>/
```

| File | Meaning |
| --- | --- |
| `summary.csv` | One row per reasoner, scale/stage and repetition with final status and aggregate timing/resource metrics. |
| `query-runs.csv` | Per-query observations. In replicated mode these are worker executions; in distributed mode they also describe the federated request. |
| `node-query-runs.csv` | Distributed-only execution at each participating node. |
| `assignments.csv` | Replicated-only query-to-worker assignments. |
| `node-runs.csv` | Replicated-only per-node preparation and resource observations. |
| `result-validation.csv` | Distributed-only exact canonical result comparison. |
| `metadata.json` | Software release, topology, reasoner and configuration provenance. |
| `progress.json` | Current point, total points, percentage, reasoner, repetition and phase. |

## 5. Physical load benchmark

The load benchmark uses `configs/load-benchmark.toml`. It changes one variable
at a time while the other values remain at their baseline:

- scheduled events per second: `50, 200, 500, 1000, 2500`;
- ontology target triples: `25k, 50k, 100k, 250k, 500k`;
- rules: `0, 25, 50, 100, 250`;
- active physical nodes: `1, 3, 5, 6`;
- synthetic users: `500, 1000, 2500, 5000, 10000`.

Each scheduled event is one SPARQL alert evaluation. The test measures queueing
and execution latency, processed throughput, event loss, alert accuracy,
inference and pipeline time, CPU, RSS, disk I/O, useful HTTP payload and state
recovery. `event_loss_percent` includes queue rejection, timeout and worker
errors; it is not IP packet loss.

Raw evidence is written to:

| File | Meaning |
| --- | --- |
| `outputs/load/summary.csv` | One row per profile, reasoner and repetition. |
| `outputs/load/event-runs.csv` | Every offered event, query, latency, processing outcome and resource attribution. |
| `outputs/load/node-runs.csv` | Per-node preparation, inference and resource observations. |
| `outputs/load/metadata.json` | Exact profiles, event definitions, topology, reasoners and timeout semantics. |

## 6. Architecture experiments

### 6.1 Scale-out

`scale-out` keeps the logical workload fixed and changes active node count
through `1, 3, 5, 6`. It reports query throughput, p95 latency, reasoning,
resource use and coordination. It explains whether adding physical workers
improves service capacity for the selected workload.

Evidence: `outputs/experiments/scale-out/summary.csv`, `query-runs.csv` and
`metadata.json`.

### 6.2 Reasoning on heterogeneous hardware

`reasoning-hardware` runs the configured triple, rule and user profiles on the
physical roles. It explains how backend cost differs across actual continuum
hardware as ontology size, rule count or population changes. Hardware,
placement and assigned work must all be considered when reading the result.

Evidence: `outputs/experiments/reasoning-hardware/summary.csv` and
`metadata.json`.

### 6.3 Distributed ontology growth

`distributed-ontology` grows synthetic users through
`0, 500, 1000, 2500, 5000, 10000`, builds real authority fragments, executes
federated queries and validates merged results. It explains the end-to-end cost
of partitioning, transfer, reasoning, routing and merge as the distributed
knowledge base grows.

Evidence: `outputs/experiments/distributed-ontology/summary.csv`,
`query-runs.csv`, `result-validation.csv` and `metadata.json`.

### 6.4 Distributed reasoning scalability

This experiment uses `configs/distributed-reasoning.toml` and explicitly
separates reasoning tasks. Its production matrix covers:

- distributed and replicated placement;
- strong and weak scaling;
- `1, 2, 3, 5, 6` physical nodes;
- `50k, 100k, 250k, 500k, 1M, 2M` logical triples;
- RDFS, HermiT, Openllet, JFact and Konclude;
- RDFS closure and OWL DL classification/realization where supported;
- query concurrency `1, 4, 16`.

It explains speedup, parallel efficiency, weak-scaling efficiency,
coordination overhead, fragment imbalance, closure expansion, capacity and the
placement trade-off. Results from different reasoning tasks are never treated
as interchangeable.

Evidence is written under
`outputs/experiments/distributed-reasoning-scalability/`:

| File | Meaning |
| --- | --- |
| `distributed-reasoning-summary.csv` | Aggregate strong/weak scaling observations. |
| `node-runs.csv` | Per-node reasoning, placement and resource data. |
| `query-scalability.csv` | Query latency/throughput at each concurrency level. |
| `semantic-validation.csv` | Sampled logical equivalence checks between layouts. |
| `distributed-reasoning-statistics.csv` | Derived scaling statistics with sample counts. |
| `capacity-summary.csv` | Largest completed point and right-censored capacity. |
| `results.jsonl` | Canonical row envelope for machine processing. |
| `metadata.json` | Complete matrix and provenance. |

## 7. Multi-axis physical campaign

The campaign uses `configs/campaign.toml`. It changes physical nodes, IoT
devices, users, requests, policies, ontology individuals, requirements, query
count, query complexity and concurrency one axis at a time. Each axis is
executed for all configured reasoners, both placements and selected policy
categories.

It tests broad configurability and interaction with real physical execution.
Its output is intentionally data-first:

```text
outputs/campaign/<UTC timestamp>-<run identifier>/
├── campaign.toml
├── manifest.json
├── provenance.json
├── results.csv
└── results.jsonl
```

There is currently no campaign-specific PNG generator. The campaign CSV/JSONL
files are the evidence. Publication figures must not be attributed to the
campaign unless an explicit analysis step is added.

## 8. Four policy-monitoring evaluations

These evaluations use `configs/policy-evaluation.toml`. Decisions use procedural
context rules. Ontology identifier validation and the separately timed reasoning
probe do not supply inferred facts to this decision engine. See
[the interpretation limits](EXPERIMENTS.md#interpretation-limits).

| Evaluation | What it does | Source CSV | PNG |
| --- | --- | --- | --- |
| Policy effectiveness | Compares a static plan with policy-driven plans against explicit scenario ground truth. Reports coverage/recall, precision, over-monitoring and under-monitoring. | `outputs/policy-evaluation/effectiveness/policy_effectiveness.csv` | `outputs/policy-evaluation/effectiveness/policy-effectiveness.png` |
| Dynamic adaptation | Executes normal → overload → failure → recovery and records policy activation, plan changes, context-read time, separate reasoning, evaluation and plan-generation latency on a simulated timeline. | `outputs/policy-evaluation/dynamic-adaptation/dynamic_adaptation.csv` | `outputs/policy-evaluation/dynamic-adaptation/dynamic-adaptation.png` |
| Policy scalability | Increases resources, evaluable policies, active categories and events together. Reports decision latency, throughput, CPU and memory. | `outputs/policy-evaluation/scalability/policy_scalability.csv` | `outputs/policy-evaluation/scalability/policy-scalability.png` |
| Computational cost | Runs static and policy-driven strategies on the same scenarios/resources and separates reasoning, policy evaluation and plan-generation cost. | `outputs/policy-evaluation/computational-cost/computational_cost.csv` | `outputs/policy-evaluation/computational-cost/computational-cost.png` |

The effectiveness PNG contains functional-quality bars and a per-scenario
agreement heatmap. The adaptation PNG shows the context timeline, active
monitoring configuration and latency components. The scalability PNG contains
latency, throughput, CPU and RAM panels. The computational-cost PNG contrasts
CPU, memory, estimated monitoring volume and per-decision costs. The reasoning
probe is amortized over the decision batch before stacking. These are controlled
plan checks, not physical fault-recovery measurements.

## 9. Reproducible policy-cost study

The optional `study` commands generate controlled inputs and aggregate measured
request events. They are not part of the default complete suite.

`continuum-bench study trace` writes `request-trace.csv`, `mobility-trace.csv`,
`query-features.csv`, `connectivity-events.csv` and `metadata.json` under
`outputs/study/`. Current positions are deterministic static inputs. Future
mobility requires an explicit model plugin and is not silently simulated.

`continuum-bench study category-cost --events <event-runs.csv>` joins measured
events with query metadata and writes `category-cost-summary.csv`,
`policy-cost-summary.csv` and `query-cost-summary.csv`. A query linked to
multiple policies contributes a `1/N` attribution fraction to each policy.

This study has no PNG generator. Its CSV summaries are intended for explicit,
reviewable downstream analysis.

## 10. PNG figure provenance

All scientific result figures are 300 dpi PNG files. The plotting commands read
CSV files; they do not rerun workloads or modify raw evidence.

### 10.1 Load figures

Generate them with:

```bash
continuum-bench load plot \
  --output-dir outputs/load
```

The generated directory is `outputs/load/analysis/`.

| PNG pattern | Source | Interpretation |
| --- | --- | --- |
| `figures/load-data-coverage.png` | `summary.csv`, aggregated into `data/load-data-quality.csv` | Completed, timeout, skipped and failed coverage for each reasoner/profile. |
| `figures/load-reference-overview.png` | `summary.csv`, aggregated into `data/load-reference-summary.csv` | Reference and overload p95 latency, peak throughput, loss and RSS. |
| `figures/load-<dimension>-performance.png` | `summary.csv` and `data/load-comparison-summary.csv` | p95 latency with p50–p99 band, throughput, event loss, critical inference, full pipeline and noncompletion rate. |
| `figures/load-<dimension>-resources.png` | Same files | Alert accuracy, CPU/node, RSS, disk I/O, useful HTTP payload and recovery time. |
| `figures/load-<dimension>-outcomes.png` | `summary.csv` | Diagnostic replacement when a dimension has no completed observations. It is not a performance curve. |

`<dimension>` is `events_per_second`, `users`, `target_triples`, `rule_count`
or `node_count` when that dimension exists in the recorded evidence.

### 10.2 Architecture-experiment figures

Generate them with:

```bash
continuum-bench experiment plot all \
  --output-dir outputs/experiments
continuum-bench experiment analyze \
  --output-dir outputs/experiments
```

| PNG | Source CSV | Interpretation |
| --- | --- | --- |
| `figures/architecture-scale-out.png` | `scale-out/summary.csv` | Query throughput and latency as active physical nodes increase. |
| `figures/architecture-hardware-target_triples.png` | `reasoning-hardware/summary.csv` | Reasoning time by node/role/reasoner as ontology size grows. |
| `figures/architecture-hardware-rule_count.png` | Same | Reasoning time as rule count grows. |
| `figures/architecture-hardware-users.png` | Same | Reasoning time as synthetic population grows. |
| `figures/architecture-distributed-ontology.png` | `distributed-ontology/summary.csv` | End-to-end distributed ontology cost as users grow. |
| `figures/distributed-reasoning/reasoning-time-vs-triples.png` | `distributed-reasoning-summary.csv` | Reasoning time under strong scaling. |
| `figures/distributed-reasoning/throughput-vs-triples.png` | Same | Logical triples processed per second. |
| `figures/distributed-reasoning/speedup-vs-nodes.png` | Same | Observed speedup relative to the matched one-node baseline. |
| `figures/distributed-reasoning/parallel-efficiency-vs-nodes.png` | Same | Speedup divided by node count. |
| `figures/distributed-reasoning/weak-scaling-efficiency.png` | Same | Efficiency when work per node is held approximately constant. |
| `figures/distributed-reasoning/coordination-overhead-vs-nodes.png` | Same | Non-reasoning coordination cost as nodes increase. |
| `figures/distributed-reasoning/fragment-imbalance-vs-nodes.png` | Same | Difference between the largest and smallest assigned fragment/work share. |
| `figures/distributed-reasoning/closure-expansion-vs-triples.png` | Same | Ratio between inferred closure size and asserted graph size. |
| `figures/distributed-reasoning/layout-comparison.png` | Same | End-to-end preparation cost for distributed and replicated placement. |
| `figures/experiment-data-coverage.png` | All experiment summaries and `analysis/experiment-data-quality.csv` | Outcome coverage; it exposes censoring and failed points. |

### 10.3 Publication report figures

Generate the evidence audit and matched comparisons with:

```bash
continuum-bench report \
  --input-dir outputs \
  --output-dir outputs/report
```

For a complete-suite run, replace `outputs` with the selected
`outputs/suites/<run>/` directory. `outputs/report/report.json` records every
retained figure, its source hash and every suppressed figure.

| PNG or pattern below `outputs/report/` | Primary source | What it explains |
| --- | --- | --- |
| `coverage-and-integrity/execution-coverage.png` | All result summaries | Counts completed, timeout, skipped and failed observations without treating them as equivalent workloads. |
| `coverage-and-integrity/evidence-readiness.png` | Summaries, metadata and validation files | Whether the complete evidence set satisfies the publication contract. |
| `coverage-and-integrity/semantic-equivalence-coverage.png` | All `result-validation.csv` and semantic-validation files | Coverage and failures of exact logical-result checks. |
| `coverage-and-integrity/load-completion-matrix.png` | `load/summary.csv` | Completed/censored load coverage by reasoner and profile. |
| `coverage-and-integrity/load-failures-and-loss.png` | `load/summary.csv` | Diagnostic outcome counts and unserved events. |
| `coverage-and-integrity/reasoner-capacity-frontier.png` | Monitoring cumulative and scalability summaries | Largest semantically valid completed population and cumulative stage per reasoner/layout. These are tested bounds, not extrapolated limits. |
| `scalability-and-placement/<layout>-<family>-time.png` | Monitoring `summary.csv` | Total, critical-reasoning and query time over cumulative stages or users. |
| `scalability-and-placement/<layout>-<family>-resources.png` | Monitoring `summary.csv` | Aggregate CPU and maximum node RSS over stages or users. |
| `scalability-and-placement/placement-<family>-<reasoner>.png` | Matched distributed and replicated summaries | Placement comparison for total, reasoning and query time. |
| `scalability-and-placement/physical-scale-out.png` | `experiments/scale-out/summary.csv` | Throughput and p95 latency as node count grows. |
| `scalability-and-placement/distributed-ontology-cost.png` | `experiments/distributed-ontology/summary.csv` | Wall time, aggregate RSS and CPU as the distributed ontology grows. |
| `nodes-and-layers/hardware-<dimension>-<reasoner>.png` | `experiments/reasoning-hardware/summary.csv` | Per-role reasoning and resource progression. |
| `nodes-and-layers/node-category-<layout>-<reasoner>.png` | `node-query-runs.csv` or `query-runs.csv` | Median worker query cost by node and policy/query category. |
| `nodes-and-layers/node-expensive-queries-<layout>.png` | Same | Top costly queries for each physical role and reasoner. |
| `nodes-and-layers/continuum-layer-query-work.png` | Same | Total observed worker query work in Edge, Fog and Cloud layers. |
| `queries/expensive-queries-<layout>.png` | Same | Top 20 queries; dot is median, line reaches p95 and color identifies category. |
| `queries/query-complexity-cost-<reasoner>.png` | `load/event-runs.csv` plus `queries/catalog.csv` | Static SPARQL complexity against observed execution cost. It is descriptive, not a causal model. |
| `categories-and-policies/category-evaluation-methods.png` | Matched node query rows | Category work under distributed and replicated evaluation. |
| `categories-and-policies/category-cost-<reasoner>.png` | `load/event-runs.csv` plus catalog | Median query, attributed CPU and process RSS by category. |
| `categories-and-policies/category-tail-and-total-<reasoner>.png` | Same | Median, p95 and frequency-weighted total category cost. |
| `categories-and-policies/policy-total-cost-<reasoner>.png` | Same | Top 15 policy-attributed total query costs using `1/N` attribution. |
| `network-scenarios/network-scenarios-and-observed-overhead.png` | `configs/network-scenarios.toml` plus observed payload/timing | Analytical network scenarios beside observed queue/transport overhead. It is not a geographic-distance measurement. |
| `recovery-and-validation/extended-budget-load-validation.png` | Optional validation-load directory | Preparation, workload, recovery and processed-event fraction for a separate extended-budget check. |

Here `<layout>` is `distributed` or `replicated`, `<family>` is `cumulative`
or `scalability`, and `<dimension>` is one of the recorded hardware axes.

The report also writes the derived CSV files used by these plots, including
`node-category-observations.csv`, `node-query-observations.csv`,
`category-method-work.csv`, `query-ranking.csv`,
`node-policy-attribution.csv`, `layer-query-work.csv`,
`placement-comparison.csv`, `category-cost-by-reasoner.csv`,
`policy-cost-by-reasoner.csv`, `execution-coverage.csv` and
`figure-statistics.csv`.

## 11. When a figure is intentionally absent

A missing PNG is not automatically a plotting defect. The generators suppress
unsupported figures in these cases:

- the required CSV does not exist;
- no row has `status=completed`;
- a progression has fewer than two completed x values;
- distributed results lack successful canonical validation;
- no population/profile is completed in every group required by a comparison;
- the report acceptance gate rejects the evidence release, topology or result
  contract.

When the publication gate rejects a run, only integrity diagnostics are kept:
`evidence-readiness.png`, `execution-coverage.png`,
`load-completion-matrix.png`, `load-failures-and-loss.png` and
`semantic-equivalence-coverage.png`. Raw evidence remains available for
diagnosis, but performance figures are removed to prevent unsupported claims.

## 12. Complete execution and figure generation

The complete physical suite records all families in an isolated directory:

```bash
continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  suite
```

It creates `outputs/suites/<UTC timestamp>-<run identifier>/`, writes one log
per step, records `suite.json`, executes the four policy-evaluation plotters and
generates the publication report. Bounded mode is recommended because a
timeout becomes a right-censored observation and later independent work can
continue. `--unlimited` is optional and can block the matrix indefinitely when
a native reasoner does not return; `--keep-going` only takes effect after the
active call ends. Specialized load and architecture figures can then be
generated from that run without repeating any measurements:

```bash
RUN=outputs/suites/<UTC timestamp>-<run identifier>

continuum-bench load plot \
  --output-dir "$RUN/load"

continuum-bench experiment plot all \
  --output-dir "$RUN/experiments"

continuum-bench experiment analyze \
  --output-dir "$RUN/experiments"

continuum-bench report \
  --input-dir "$RUN" \
  --output-dir "$RUN/report"
```

Always read `suite.json`, `report/report.json`, coverage figures and source CSV
statuses before interpreting a performance curve. Medians and observed ranges
describe the recorded repetitions; they are not confidence intervals unless a
separate statistical analysis explicitly says so.

## Optional comparative policy evaluation

The independent [comparative evaluation module](COMPARATIVE_EVALUATION.md) runs paired static,
procedural and semantic policy strategies on the physical hosts. It provides
its own bounded configuration, four experiments, durable JSON/CSV evidence and
per-node PNG figures. Published systems are methodological references, not
claimed reproductions. Mist is excluded by default.

```bash
.venv/bin/python -m continuum_bench.monitoring.comparison check
.venv/bin/python -m continuum_bench.monitoring.comparison run --smoke
.venv/bin/python -m continuum_bench.monitoring.comparison run
```

The comparative publication renderer also writes `figure-data.csv`, English
captions, outcome coverage and paired semantic-versus-procedural overhead figures.
It uses process repetitions for uncertainty, marks n<5 as exploratory, validates
raw evidence and leaves gaps at failed workload points. See the comparative
module documentation for exact timing boundaries and measurement-contract versions.

## Audit remediation checks

`tests/infrastructure/test_remediation_profiles.py` checks that five-node profiles
never schedule Mist or a six-node point and that every unreferenced policy or
requirement has a current, evidence-linked review disposition. Removing a
reviewed gap must fail the check; documenting it does not increase query coverage.

The native reasoner tests cover expansion of OWL/XML relative and abbreviated
IRIs before constructing OWLlink requests. Worker lifecycle regressions verify
that stopping a managed worker preserves independent native diagnostics.

`tools/check_distributed_semantics.py` is a local correctness diagnostic, not a
physical benchmark or a source of publication timing figures. Its JSON compares
all 115 counts, ASK answers and result digests between canonical and routed
fragment execution. `tools/review_validation_debt.py` produces a per-individual
SHACL debt inventory with actions, while preserving the warnings.

For objectives, interpretation and the relationship between evaluation paths,
see [Research method](RESEARCH_METHOD.md). For actual remediation evidence and
five-node commands, see [Audit remediation](REMEDIATION.md).

### Portable and native validation gates

The default pytest run requires only the Python environment. Native inference
and canonical-ontology checks are explicitly skipped unless enabled, so the clean
installation CI does not accidentally require a local Java reasoner installation.
After installing all native backends, run the mandatory physical deployment gate:

```bash
CONTINUUM_TEST_NATIVE_OWL=1 .venv/bin/pytest -q   tests/core/test_native_reasoners.py   tests/core/test_ontology.py::test_configured_reasoner_profiles_have_no_explicit_contradictions
```

This executes all four native backends, including canonical violation queries.
An enabled gate fails if a backend is unavailable; it does not silently fall back.
