# Physical publication reports and extended execution

For the current end-to-end launch procedure, see [Run all physical tests](RUN_ALL_TESTS.md).

## Rebuild figures from recorded evidence

```bash
. .venv/bin/activate
continuum-bench report
continuum-bench load plot
continuum-bench experiment plot all
```

The report writes 300-DPI PNG figures and CSV source tables under `outputs/report`.
`report.json` records input hashes, findings and figure paths. `figure-statistics.csv`
records each plotted series, sample count, median and observed range. No PDF or SVG
benchmark figures are generated. Existing equivalents are removed when a figure
is regenerated. Source ontology diagrams are separate semantic documentation.
`results-audit.json` gives a machine-readable acceptance decision and blockers.
It also records the active software version and topology fingerprint. A report
is rejected when its metadata belongs to another release, uses a different
physical-node count, was reconstructed after a failed run, omits a required
benchmark family or contains no completed observations for that family. Every
stale diagnostic carries a prominent historical-evidence notice. When the
acceptance decision is rejected, performance figures and derived performance
tables are removed from the catalogue and from disk. Only coverage and
integrity diagnostics remain; `report.json` lists every suppressed artifact.
`coverage-and-integrity/png-quality-audit.json` is regenerated from exactly the
retained PNG files and records dimensions, sampled colour count and blankness.

Figures include completed execution times, CPU and RSS, reasoning by physical
node, cumulative and scalability curves, outcome coverage, category costs,
fractionally attributed policy costs, and communication scenarios. Missing
measurements remain missing. A workload with no completed points gets failure
and loss diagnostics instead of empty performance panels. Progression figures
require at least two distinct completed values on their x axis, and placement
comparisons require a completed value shared by both layouts.

The coverage group additionally contains normalized evidence readiness,
semantic-equivalence acceptance, reasoner capacity frontiers and
load-completion matrices. Category panels are
generated only when a backend has completed requests with the required metric;
obsolete empty PNGs are removed during regeneration.

The September 27 review confirmed no completed benchmark points among the 345
load records. There were 65 timeout-class outcomes and 280 skipped points. Completed requests
inside these failed runs still carry real observations, but their category/policy
rankings are conditional on survival and on the workload profile. The report selects a shared profile with the greatest
minimum completed coverage across observed reasoners and records that choice. They
are diagnostic evidence, not an unbiased estimate of all-policy performance,
and are suppressed from a rejected publication catalogue.
CPU is attributed from batch timing; RSS is process memory, not policy allocation.

Curves use only completed observations. Whiskers show observed minimum–maximum,
not confidence intervals. A single surviving scale-out node count cannot establish
scale-out benefit. The coverage figure exposes this limitation. Failed or skipped
observations are never converted into zero-valued successful performance.

## Communication scenarios

The operator confirmed that the physical nodes are in the same room.
`configs/network-scenarios.toml` defines hypothetical distances, bandwidths,
base RTT and propagation speed. Estimated request/response transport is:

```text
transport_ms = base_rtt_ms + 2 * distance_km / propagation_speed_km_s * 1000
               + observed_payload_bytes * 8 / (bandwidth_mbps * 1000)
```

The payload size comes from measured HTTP bodies. The estimate excludes packet
headers, contention, retransmission and routing. It does not emulate a WAN,
move physical nodes or implement mobility trajectories. The accompanying
observed latency-minus-query-time metric includes queueing and serialization;
it is not network RTT. Model outputs and observations are labelled separately.

## Run every physical test family

Inspect the exact plan without contacting workers:

```bash
continuum-bench --unlimited --repetitions 5 suite --dry-run
```

Execute sequentially, preserving prior results:

```bash
continuum-bench --unlimited --repetitions 5 suite
```

This runs software tests, semantic validation, preflight, the four external OWL
validators, physical worker startup, cumulative/scalability in both layouts,
load, the four separated experiments, the ten-axis campaign and PNG reporting.
Every invocation creates a unique directory below `outputs/suites` with a
`suite.json` plan/status record and one log per step. Inspect the logs while a
long step runs. Worker deployment and SSH authorization must already be complete.

`--unlimited` disables elapsed-time cutoffs for preparation, reasoning, queries,
load-stream draining and recovery, including coordinator waits, HTTP sockets and
worker alarms. Later points are not pruned because of an earlier timeout.
Configured budgets remain recorded; `execution_policy.timeout_mode = "unlimited"`
and `configured_budgets_enforced = false` identify their advisory status.
A request may take arbitrarily long. Workload duration still determines how many
events are offered; all accepted requests are drained even after that duration.
Queue overflow, incorrect answers, disconnections and application errors remain
real failures. Health/startup checks and external OWL tool validation retain their
separate operational limits. Cancellation is manual; an unresponsive operation
may require terminating the coordinator and restarting its physical worker.

```bash
continuum-bench --unlimited load physical
continuum-bench --unlimited physical all
continuum-bench --unlimited experiment all physical \
  --distributed-reasoning-config configs/distributed-reasoning.toml
continuum-bench --unlimited campaign --campaign-config configs/campaign.toml
```

For runs where a finite cutoff is desired, `--patient` gives each request/phase/point a 3600-second budget and attempts later
points after timeouts. Recovery retains its own budget. There is no total suite
deadline; the suite can run for many hours. The per-operation budget is finite and
configurable, not an assertion that every workload can finish on any hardware:

```bash
continuum-bench --timeout-seconds 7200 --repetitions 5 suite --patient
continuum-bench --timeout-seconds 300 --keep-going --repetitions 1 load physical --profile eps-50 --output-dir outputs/patient-load
continuum-bench --timeout-seconds 3600 --keep-going physical scalability
```

Use `suite --families load experiments report --patient` for a selected subset.
Global options precede the command. Cancellation remains available with Ctrl+C.
Incomplete result rows make the suite step fail even if the underlying benchmark
process returns zero. Subsequent families still run and retain their evidence.

Increasing time budgets does not increase physical capacity or remove event-queue
loss under saturation. Report both completion coverage and latency/resource
observations; repeat matched workloads before making publication claims.

Replica CPU/RSS telemetry is now preserved in newly written summaries. Older
replica CSVs do not contain these fields and cannot be reconstructed from timing
measurements. The report lists these missing metrics explicitly.


## Verified extended-budget rerun

The `eps-50` profile (500 users, 50,000 triples/node, 25 rules, five physical
nodes) was repeated with 300-second request/point/recovery budgets. RDFS, OWL RL
and combined RDFS/OWL RL each completed 100/100 events without loss. The combined
profile required approximately 174 seconds to prepare and 175 seconds to recover;
its complete pipeline can exceed the point budget because recovery is a separate
phase. This is one validation repetition, not the full extended campaign.

Add a separate measured load dataset to the report with:

```bash
continuum-bench report --validation-dir /path/to/separate/load-results
```

The original 207-point dataset remains unchanged. Its incomplete results must
not be relabelled as successful on the strength of this separate rerun.

## Verified unlimited execution

The physical smoke load was executed with nominal six-second budgets and
`--unlimited`. All six points (one and five physical nodes, three reasoners)
completed, processing 12/12 events without loss. On five nodes, combined
RDFS/OWL RL preparation and recovery each took approximately 23 seconds.
These exceeded the recorded budgets without timeout failure or skipped points.
Write an isolated unlimited smoke run outside the active results root when it must be retained separately:

```bash
continuum-bench --timeout-seconds 6 --unlimited --repetitions 1 load physical --load-config configs/load-smoke.toml --output-dir /path/to/isolated-load-run
```

Regression tests also exercise delayed HTTP responses, worker alarm disabling,
local timers, future waits, event-stream draining and campaign completion after
nominal deadlines. This smoke validates timeout behavior, not statistical power.

## Comparative ontology and policy evaluation

`continuum-bench report` also builds matched physical comparisons. Figures are
organized into `nodes-and-layers/`, `queries/`, `categories-and-policies/`,
`scalability-and-placement/`, `network-scenarios/`, `recovery-and-validation/`
and `coverage-and-integrity/`. The generated `README.md` links every figure;
`report.json` records its path and source hashes. Regenerating a legacy flat PNG
moves that figure into its group; raw benchmark evidence is unchanged.

Node/category and query rankings over archived evidence select the smallest
population with completed summary observations across both layouts and the
available reasoners. Figures generated from the old RDFS/OWL-RL campaign carry a
historical-evidence notice; the active five-reasoner matrix requires a new 0.4.1
six-node run.
Only node measurements belonging to those completed repetitions are included.
Per-node query heatmaps show missing assignments explicitly, not as zero cost.
Expensive-query scatter plots use a stable category colour, one dot per query
and reasoner (median), and a segment to p95; rankings use the maximum median
across reasoners so every panel shows the same query IDs. CSVs retain sample
counts. Tail estimates with few observations are descriptive only.

Historical evidence may use `sharded` for authority-partitioned placement. New
runs use `distributed`; neither term denotes shared memory. Node time is read from actual
worker records. It is never obtained by dividing a federated duration among
nodes. Layer totals sum worker query work within each repetition before taking
the median; Edge combines its physical nodes. Routing and query assignment can
differ, so these totals do not measure hardware speedup in isolation.

The cumulative and scalability panels overlay both placements separately for
the reasoners present in the recorded dataset. They retain completed observations only;
coverage shows why later points may be absent. Category/method comparisons use
summed node query execution per repetition, including actual partition fan-out.
New source tables include `node-category-observations.csv`,
`node-query-observations.csv`, `node-policy-attribution.csv`, `query-ranking.csv`,
`layer-query-work.csv`, `category-method-work.csv` and `placement-comparison.csv`.
Policy attribution divides each query's observed work equally across its linked
policies (1/N); these fractions are not learned policy importance weights.

These observations validate execution costs and semantic result equivalence,
not causal policy overhead. A matched policies-enabled/disabled intervention is
still needed for causal claims. Added cumulative categories change both policy
functionality and the query workload. Historical replica resource omissions,
incomplete high-load runs, analytical distances and separate recovery validation
remain explicitly identified rather than filled with synthetic measurements.

The dedicated distributed-reasoning report adds nine PNG figures for strong and
weak scaling, task-group throughput, speedup, efficiency, coordination overhead,
fragment balance, closure expansion and placement. It reads only
`distributed-reasoning-summary.csv`; until a physical run produces completed
rows, no result from that matrix should be added to a paper as measured evidence.
