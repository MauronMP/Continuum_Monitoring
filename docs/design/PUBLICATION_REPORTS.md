# Physical publication reports and extended execution

## Rebuild figures from recorded evidence

```bash
. .venv/bin/activate
continuum-bench report
continuum-bench load plot
continuum-bench experiment plot all
```

The report writes 300-DPI PNG figures and CSV source tables under `outputs/paper`.
`report.json` records input hashes, findings and figure paths. `figure-statistics.csv`
records each plotted series, sample count, median and observed range. No PDF or SVG
benchmark figures are generated. Existing equivalents are removed when a figure
is regenerated. Source ontology diagrams are separate semantic documentation.

Figures include completed execution times, CPU and RSS, reasoning by physical
node, cumulative and scalability curves, outcome coverage, category costs,
fractionally attributed policy costs, and communication scenarios. Missing
measurements remain missing. A workload with no completed points gets failure
and loss diagnostics instead of empty performance panels.

The September 9 input audit found no completed points among the 207 load records.
There were 39 attempted timeout points and 168 skipped points. Completed requests
inside these failed runs still carry real observations, but their category/policy
rankings are conditional on survival and on the workload profile. The report selects a shared profile with the greatest
minimum completed coverage across observed reasoners and records that choice. They
are exploratory evidence, not an unbiased estimate of all-policy performance.
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
load, the three separated experiments, the ten-axis campaign and PNG reporting.
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
continuum-bench --unlimited experiment all physical
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

Preserve this evidence separately and add it to the report with:

```bash
continuum-bench report --validation-dir outputs/audit/patient-load/physical
```

The original 207-point dataset remains unchanged. Its incomplete results must
not be relabelled as successful on the strength of this separate rerun.

## Verified unlimited execution

The physical smoke load was executed with nominal six-second budgets and
`--unlimited`. All six points (one and five physical nodes, three reasoners)
completed, processing 12/12 events without loss. On five nodes, combined
RDFS/OWL RL preparation and recovery each took approximately 23 seconds.
These exceeded the recorded budgets without timeout failure or skipped points.
Evidence is under `outputs/audit/unlimited-load/physical`:

```bash
continuum-bench --timeout-seconds 6 --unlimited --repetitions 1 load physical --load-config configs/load-smoke.toml --output-dir outputs/audit/unlimited-load
```

Regression tests also exercise delayed HTTP responses, worker alarm disabling,
local timers, future waits, event-stream draining and campaign completion after
nominal deadlines. This smoke validates timeout behavior, not statistical power.
