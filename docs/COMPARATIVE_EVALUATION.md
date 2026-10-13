# Comparative evaluation of policy-driven monitoring

This optional module evaluates the policy-decision mechanism on the physical
continuum without replacing the existing experiment suites. Its central question
is: **what decision quality and computational cost do explicit adaptive policies
provide, and what additional cost does semantic resource selection introduce?**

The implementation lives in `src/continuum_bench/monitoring/comparison/`.
Configuration is in `configs/comparison.toml`. All artifacts go under
`outputs/comparison/<UTC timestamp>-<unique ID>/`. Mist is excluded by default
because it is unavailable. Cloud, Fog, Edge1, Edge2 and Edge3 execute identical
paired workloads individually; this is not a distributed query execution study.

## Relationship to published work

These references motivate the evaluation. Built-in adapters are **controlled
baselines**, not reproductions of these papers or their original software.
Published measurements must not be pooled with our measurements or used to claim
speedups: hardware, workloads, semantics and metrics differ.

| Reference | Relevant contribution | Corresponding evidence here | Boundary |
|---|---|---|---|
| Forti, Gaglianese and Brogi, *Lightweight self-organising distributed monitoring of Fog infrastructures*, FGCS, 2021. [DOI](https://doi.org/10.1016/j.future.2020.08.011) | Distributed monitoring and its resource footprint | Measured CPU time and sampled process RSS on each physical host | FogMon gossip, fault tolerance, network monitoring and differential updates are not reproduced |
| Ghrab, Lahyani, Yangui and Jmaiel, *A core IoT ontology for automation support in edge computing*, SOCA 17, 25–37, 2023. [DOI](https://doi.org/10.1007/s11761-022-00356-2) | Semantic resource matching and automation | Configured resource–metric coverage and exact operational plans | EdgeOnto concept-retrieval precision/recall is not the same measure as our monitoring-plan quality |
| De Brouwer, Ongenae, Bonte and De Turck, *Towards a cascading reasoning framework to support responsive ambient-intelligent healthcare interventions*, Sensors 18(10), 3514, 2018. [DOI](https://doi.org/10.3390/s18103514) | Responsive healthcare reasoning across a hierarchy | Context-transition decision latency and preparation cost | This module does not reproduce cascading inference, sensor-to-actuator latency or clinical interventions |
| *Achieving security scalability and flexibility using Fog-Based Context-Aware Access Control*, FGCS 107, 307–323, 2020. [DOI](https://doi.org/10.1016/j.future.2020.02.001) | Context-sensitive semantic policies in Fog | Policy-count scaling and context-specific decision correctness | This module does not reproduce access-control semantics or the authors' system |

For a compact article, use one quality/adaptation figure and one cost/scalability
figure, with a small qualitative related-work table. Keep full per-node evidence
in supplementary artifacts. Actual head-to-head comparison with FogMon or another
published system requires installing its original implementation and defining a
common supported workload; this module does not label a generic baseline as that
system. No superiority over the cited papers is established by a smoke run.

## Strategies and semantic contract

| Adapter | Actual implementation | Interpretation |
|---|---|---|
| `static` | Existing fixed monitoring plan | Context-independent baseline |
| `procedural` | Existing `PolicyEngine`, using the same rule conditions, targets and actions | Equivalent adaptive policies without semantic resource selection |
| `semantic` | An executable RDF projection of the same resource/rule inputs, RDFS materialization, then SPARQL policy and resource selection | Alternative semantic implementation of the decision mechanism |

Each logical device has a specialized class that is a subclass of its continuum
tier. The graph asserts only the specialized type. RDFS infers membership of the
tier class, and SPARQL consumes that membership to select resources. Removing
inferred tier memberships changes the selected plan; a regression test verifies
this causal link. Policies are selected through explicit context membership.
Metrics/actions/intervals are assembled from the selected rule definitions.

The semantic adapter uses the project's common `get_reasoner("rdfs")` port and
its datatype-aware RDFS implementation. This module deliberately fixes RDFS to
isolate the policy mechanism; it does not silently run the other reasoners or
reuse old standalone RDF/OWL comparisons. It does not evaluate all OWL axioms,
policy conflicts, authorization precedence or every module in the full ontology.
The RDF projection is an experimental alternative, not a claim that the current
production decision path already consumes inference.

`DecisionAdapter` in `adapters.py` defines the extension point. Add an adapter to
`ADAPTERS` and `STRATEGIES`, implement `decide(context) -> MonitoringPlan`, and
record its implementation/provenance before interpreting results. An adapter
receives no expected plans. Timing, workload generation, transport, scoring and
reporting remain outside the adapter.

## Experiments

| Experiment | Controlled variable and operation | Output figure |
|---|---|---|
| `effectiveness` | Identical shuffled contexts and explicit acceptance plans, compared across strategies | Per-context coverage, excess pairs, exact plans and decision cost |
| `adaptation` | Ordered normal → overload → failure → recovery cycles | Decision time, activated policies, exact plans and planned vs expected sampling interval |
| `scalability` | Multiply logical resource instances and rule copies, retaining their semantics | Decision latency, preparation cost, decision-loop throughput and sampled peak RSS |
| `cumulative` | Longer ordered event traces over a prepared model, without rebuilding between events | Accumulated decision time, amortized throughput, CPU per event and exact plans |

Every cumulative size is an independent isolated job. The graph is prepared once
per job. Cumulative means accumulated decision work, **not** growing the ontology,
adding physical nodes or accumulating stale state. Previous plans are not carried
into the next context. Size points in scalability jointly increase resources and
policies; they cannot identify each variable's isolated causal effect.

Normal/overload/failure/recovery are supplied synthetic labels, not detected
physical failures. Actions are returned plans; no production offloading, sampling
change or actuator operation is applied. “Adaptation latency” in discussion must
therefore mean **decision time after a known context**, not failure detection,
network recovery or end-to-end clinical response.

## Workloads, oracle and fairness

The rules and explicit expected plans come from the selected
`policy-evaluation.toml`. These fixtures are snapshotted. Expected plans are never
computed by an adapter. They are configured acceptance criteria, not independently
annotated clinical ground truth. Update the scenario expectations separately
when changing a requirement and review them before using results in a paper.

Excluded logical resources are removed from all three inputs and from the oracle.
Rule/resource copies receive stable identifiers. All strategies receive the same
trace, verified by SHA-256 hashes. Strategy order is randomized deterministically
within each node/experiment/size/repetition block. Warm-up is identical. Each job
runs in a fresh process. Executors run serially to reduce self-induced contention.
Other services on a host can still affect timing.

A plan contains resources, metrics, actions and an interval. Coverage is computed
on the Cartesian set of **resource–metric pairs**, consistent with the current
plan model. Policy IDs/categories are explanatory metadata, not correctness
requirements that unfairly penalize the static baseline. Coverage does not check
sampling frequency; exact-plan correctness additionally requires the expected
actions and interval. It is possible to obtain full coverage with over-monitoring
or an incorrect interval. Empty predictions against a nonempty oracle have zero
coverage. Procedural and semantic plans should agree on this supported fragment;
a semantic speed or accuracy advantage is not assumed.

## Installation and execution

Run from the repository root. Follow [Installation](INSTALLATION.md) for the
base environment and native worker setup. This module adds no Python dependency.
The coordinator needs the project environment, matplotlib, SSH and GNU `timeout`.
Remote nodes need the configured Python environment with RDFLib and owlrl, SSH
key access and GNU `timeout`. No service restart or native reasoner installation
is necessary for this RDFS comparison.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'

# Show availability and configured exclusions.
.venv/bin/python -m continuum_bench.monitoring.comparison check

# Automated behavioral and integration-contract tests.
.venv/bin/python -m pytest tests/comparison

# Physical smoke campaign on all available configured nodes.
.venv/bin/python -m continuum_bench.monitoring.comparison run --smoke

# Complete configured campaign; failures are recorded and later jobs continue.
.venv/bin/python -m continuum_bench.monitoring.comparison run

# Select executor hosts without changing logical workload contents.
.venv/bin/python -m continuum_bench.monitoring.comparison run --nodes cloud fog edge1

# Use a separate configuration or output root.
.venv/bin/python -m continuum_bench.monitoring.comparison run --config configs/comparison.toml --output outputs/comparison

# Regenerate CSVs and PNGs from an actual run directory; replace RUN_ID.
.venv/bin/python -m continuum_bench.monitoring.comparison report outputs/comparison/RUN_ID
```

The remote inventory, addresses and Python path are read from the existing
physical topology. The default full campaign contains 720 jobs across six executor hosts; the smoke
campaign contains 108. Runtime depends on host and network conditions.

The coordinator transfers an immutable Python source bundle
over SSH and imports it in a temporary directory; it does not overwrite the
workers' deployment or restart their services. The bundle is saved with the run.
A repository-wide physical campaign lease prevents overlap with existing campaigns
started on this coordinator. There is no cross-coordinator distributed lock.

Mist is included by default as both an executor and a logical resource. Verify
all six nodes with `check` before acquisition. An
unreachable selected host generates `unavailable` job records; it does not reduce
the planned denominator invisibly. Logical Mist exclusion and executor selection
are separate concepts.

## Configuration and bounded execution

All fields are required and unknown keys are rejected.

| Field | Default | Meaning |
|---|---|---|
| `policy_config` | `policy-evaluation.toml` | Rule definitions and explicit scenario oracle; relative to comparison config |
| `topology` | `topologies/physical/topology.toml` | Existing physical inventory; relative to comparison config |
| `output` | `outputs/comparison` | Parent of unique run directories; relative to current repository root |
| `exclude_nodes`, `exclude_resources` | `[]` | Physical executor and logical-resource exclusions |
| `strategies`, `experiments` | All built-in entries | Explicit evaluation scope |
| `repetitions`, `warmup`, `seed` | 5, 2, 2026 | Independent process repetitions, warm-up context cycles, deterministic order |
| `timeout_seconds` | 120 | **120,000 ms per whole job**, including interpreter/bundle initialization, preparation, warm-up and decisions |
| `connect_timeout_seconds` | 30 | SSH connection budget |
| `multipliers` | `[1, 4, 16]` | Logical workload scaling |
| `events_per_context` | 10 | Events per context for non-cumulative experiments |
| `cumulative_cycles` | `[1, 4, 16]` | Complete four-context cycles for cumulative points |

The coordinator transport deadline also permits the connection budget and ten
seconds for transport/termination. GNU `timeout` bounds the remote process even
if the SSH connection breaks, with a three-second forced-termination grace.
There is no unlimited mode in this module. A timeout records a censored job, not
a successful latency equal to the timeout. There are no skip-after-timeout
triggers: subsequent strategies, sizes, repetitions and nodes are still attempted.
Exit code 1 indicates execution failures or non-static oracle mismatches after
the campaign finishes; static mismatch is a reported baseline result. Ctrl+C
marks the run interrupted; completed JSON records remain reportable. A remote
job already submitted may continue until its configured deadline.

## Results and metric boundaries

```text
outputs/comparison/<run-id>/
  metadata.json                  # source/config IDs, topology, scope, final status
  configuration.json             # effective configuration, including smoke overrides
  policy-configuration.toml      # original input for replay
  policy-configuration.json      # expanded configuration description
  source.zip                     # exact Python source shipped to each executor
  preflight.json                 # reachability/dependency evidence
  jobs.jsonl                     # durable job and per-event measurements
  summary.csv                    # one row per job, including failures
  paired-comparisons.csv         # semantic minus baseline, paired repetitions
  outcomes.csv                   # all success/timeout/failure/unavailable counts
  report.json                    # figure/evidence manifest, planned and missing jobs
  report-source.zip               # exact current renderer source, separate from measurement source
  figure-data.csv                # every point: contributing job IDs, values, n and CI
  figure-captions.md              # English captions and interpretation limits
  figures/outcomes.png            # all recorded execution outcomes
  figures/paired-cost.png         # paired semantic-minus-procedural cost by host
  <experiment>/raw/<job-id>.json  # exact input trace, oracle, plans and measurements
  <experiment>/figures/<node>.png
```

CSV summaries never substitute zero for missing failed measurements. Figures are
PNG at 300 dpi, grouped by experiment with separate physical-host panels/files.
Each main figure is 7.2 inches wide with four panels and journal-sized text.
Colors and marker shapes distinguish strategies, including overlapping values.
Memory uses a zero-based linear axis. Positive cost measures use logarithmic axes
only when their range warrants it, with an explicit scale annotation. Numeric
workload spacing is preserved; resource counts and policy counts are both shown.
Missing/failed size points break curves, rather than being joined or imputed.

Every point first aggregates events within one process repetition. Whiskers are
95% percentile bootstrap intervals of the repetition mean, using 5,000 resamples
and a stable seed per group. They are emitted only for at least five completed
process repetitions. Smaller samples display means without confidence bars and
an explicit exploratory label. This threshold is a reporting rule, not proof of
statistical adequacy; five repetitions still provide limited precision. Contexts,
events, and different physical hosts are never counted as independent repetitions.
Constant configured quality outcomes may legitimately have a zero-width interval.

`figure-data.csv` records the exact sample count, failed-job count, contributing
job IDs and repetition values for every plotted point. Figure footers show the
actual range of per-point counts, not the union of available repetition IDs.
`paired-comparisons.csv` uses matched workload/trace hashes; confidence intervals
apply to repetition-level differences, not pooled event timings. The paired-cost
figure selects a common workload multiplier across included hosts and preserves
the sign of additional semantic cost. Hosts without matched runs are absent and
must be checked against outcome coverage. Positive overhead is not an advantage.

`figures/outcomes.png` exposes failed and unavailable jobs. Unattempted work in an
interrupted campaign is reported separately in `report.json`. Do not treat fast
survivors as evidence that timed-out strategies perform well. `figure-captions.md`
provides a caption and limitations for every figure. The four per-node families
are supplementary detail; a compact paper can use a preselected representative
node plus the paired-cost comparison across hosts, explaining the selection.

Before reporting, the module verifies event counts, finite/nonnegative timings,
cumulative sums, stored quality scores, unique repetitions and paired input
identity. It rejects mixed timing-contract versions. Only an unterminated final
JSONL record may be ignored after interruption, and that fact is recorded.
Complete malformed lines fail explicitly. Existing raw measurements are never
rewritten during figure regeneration.

* `setup_ms`: graph/input preparation, inference and query preparation for semantic;
  corresponding adapter initialization for the other strategies.
* `reasoning_ms`: materialization only, within setup. Zero for non-semantic adapters.
* `decision_ms`: one adapter call, including SPARQL selection and plan generation.
* `cumulative_decision_ms`: exact running sum of decision durations.
* `throughput_decisions_per_second`: timed decision loop throughput, excluding warm-up,
  setup and oracle scoring, including common loop bookkeeping and resource sampling.
* `setup_amortized_throughput`: includes adapter setup in the denominator; excludes
  transport, interpreter startup and warm-up.
* CPU: actual process CPU time and mean utilization; 100% means one core.
* RSS: sampled process resident memory, not a system-wide total or exact transient peak.
  Setup and decision phases have separate measurements; sampler interval is 5 ms.
  The plotted peak is the maximum across both phases. All strategies share the
  Python harness and imports; this is not a minimal standalone-agent footprint.
* `transport_wall_ms`: coordinator-observed job round trip, including SSH, source
  transfer and startup; **not application monitoring traffic or network latency**.
* Trace/config/source hashes, host Python/dependency versions and hardware counts
  support reproducibility; timing cannot be deterministic across real machines.

There is no fabricated monitoring-traffic, energy, physical distance, clinical
accuracy, failure-recovery or distributed throughput measurement. Tailscale
connectivity permits execution on the physical hosts; it does not establish
geographic separation or simulate a propagation distance by itself.

## Tests and remaining limits

Automated tests verify equivalent plans, actual dependence on inferred types,
unknown-context deactivation, separation of oracle and adapter, deterministic
paired traces, accumulated-time arithmetic, configuration validation, and failure
continuation. Physical smoke execution additionally checks source transfer and
runtime compatibility on the selected nodes.

This module covers an executable context/tier policy fragment. Cross-category
conflict resolution, real monitoring actuation, consent enforcement, dynamic
resource measurements as inputs and replicated-versus-distributed ontology
placement remain in the scope of separate architecture experiments. The module
cannot validate those capabilities merely by producing a correct plan. Do not
present its results as a full independent validation of the entire proposal.

## Verified implementation run (2026-10-05)

Physical smoke run `20261005T171750Z-b1e5b475` completed 90/90 jobs on Cloud,
Fog and all three Edge hosts, with zero timeouts/failures and zero procedural
or semantic operational-plan mismatches. Mist was excluded. The run produced
20 PNG figures. Seventeen module tests passed, and fourteen existing policy,
documentation and physical-only regression tests also passed. An actual local
process deadline returned GNU timeout status 124 as expected. At that review date, the 600-job
full campaign has not been executed as part of this implementation check.

These observations establish execution and configured-plan correctness only.
They are not independent clinical validation or a head-to-head published-system
comparison. Raw evidence remains in the ignored outputs directory; archive it
separately when preparing a publication.

## Reporting and measurement audit

The publication renderer is separated into `figures.py`; repetition statistics
are in `statistics.py` and evidence checks in `validation.py`. Keep scientific
analysis independent from execution and rendering. Regenerating a report writes
`report-source.zip` and its hash without replacing the original measurement
`source.zip`.

Timing contract `comparison-v2-complete-context-warmup` covers every configured
context during each warm-up cycle and includes input-object construction in
adapter preparation. Earlier runs are explicitly identified as `comparison-v1`;
their measurements are retained as collected, not relabeled or pooled with v2.
Changing the renderer does not retroactively change their timing contract.
The single-repetition smoke data remain exploratory even after publication-quality
formatting. No complete multi-repetition performance campaign is implied.

## Audit validation (publication renderer v2)

- 42 module and adjacent regression tests passed, including repeated-event versus
  repeated-process sample counts, missing-size curve gaps, duplicate evidence,
  non-finite timings, cumulative sums, contradictory scores and interrupted logs.
- Physical v2 smoke run `20261005T173354Z-ac38e4a9` completed 36/36 jobs on Cloud
  and Fog with zero execution failures or adaptive-plan mismatches.
- The earlier five-host smoke campaign was re-rendered from its original 90 jobs;
  its v1 measurement contract is retained. A complete five-host report now contains
  20 per-node figures plus outcome coverage and paired-cost comparison (22 PNGs).
- Raw JSONL hashes were checked before and after regeneration; measurements were
  unchanged. At that review date, the full 600-job campaign remained pending; the later run below supersedes that status.

The checks establish code and reporting behavior. All available smoke results
still have one process repetition per point and must be described as exploratory.

## Physical measurement platform

Physical comparison workers require Linux with `/proc/self/status` available.
Their memory records identify sampled current-process RSS. macOS may run portable
software checks, but its process-lifetime peak memory is not interchangeable with
Linux phase measurements; Linux-only integration tests are explicitly skipped
there. The isolated worker transport also requires GNU `timeout`. Passing portable
CI does not establish physical measurement readiness.

## Cross-node overview figures

Reporting also generates `<experiment>/figures/all-nodes.png` for effectiveness,
adaptation, scalability and cumulative evaluation. Columns show every host
recorded in the run, with identical vertical scales for each metric row. The
plots reuse repetition-level values and confidence intervals from
`figure-data.csv`; hosts are never pooled as experimental repetitions. Excluded
nodes are not imputed. These independent host replays do not measure simultaneous
fleet throughput, total peak RAM, network latency or real service recovery.
Regenerate these figures for an existing run with the `comparison report`
command above; no benchmark rerun is needed.


## Completed five-host campaign and six-host configuration (2026-10-08)

Run `20261007T111333Z-589a4b3c` completed all 600 jobs with five process
repetitions per point and no adaptive-plan mismatches. It contains four tests:
quality against configured expected plans, response to supplied contexts,
joint resource/policy scalability, and accumulated decision work. Static selection
covered every required pair but averaged 62.857% excess monitoring; procedural and
semantic selection both achieved exact agreement with the configured oracle.
This supports equivalent answers with measured semantic overhead, not greater
accuracy than procedural rules or clinical validation.

The default configuration now includes Mist (six executor hosts and six base
logical resources), giving 720 full jobs or 108 smoke jobs. The SSH connection
budget is 30 seconds. Older five-host results retain their acquisition configuration;
do not append six-host observations to them because adding logical Mist resources
changes the workload on every host. Run the complete comparison in a new directory
only after any other physical campaign has finished.

`figures/cross-node-summary.png` provides a compact four-panel overview of all
recorded hosts. Each panel uses a common workload size across hosts. The four
`<experiment>/figures/all-nodes.png` panels provide the detailed metric comparisons.
`cross-node-summary-data.csv` records repetition values, confidence intervals and
job provenance. These figures are generated automatically by both `run` and `report`.
