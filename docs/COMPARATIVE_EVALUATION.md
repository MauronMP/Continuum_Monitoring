# Monitoring-strategy comparison module

This is **Battery 2**, independent of the complete physical architecture suite.
Its scientific questions, four experiment families and literature references are
maintained in [Experiments](EXPERIMENTS.md). Commands are in
[Complete execution](COMPLETE_EXECUTION.md); files and figures are in
[Outputs](OUTPUTS.md). This page specifies implementation and configuration.

## Contract and extension points

`monitoring/comparison/adapters.py` exposes `DecisionAdapter.decide(context)`.
Current adapters are `static`, `procedural` and `semantic`. `workload.py` constructs
deterministic paired inputs and scores them against separately configured plans.
`worker.py` measures one isolated job; `transport.py` transfers a source snapshot
and invokes jobs over SSH; `runner.py` controls the matrix and durable outcomes.
Reporting is separate from measurement.

The semantic adapter consumes RDFS type inference in SPARQL resource selection.
Its RDF projection is not the full modular ontology. Threshold detection and raw
sensor-based context inference are not implemented in this module. A proposed
four-strategy extension would need those mechanisms and an explicit input contract;
it is not enabled by renaming the existing adapters.

## Configuration

`configs/comparison.toml` is strict: missing or unknown fields fail early.

| Fields | Current setting / interpretation |
| --- | --- |
| `policy_config`, `topology` | Paths relative to the comparison TOML. |
| `output` | Unique run directories under `outputs/comparison`. |
| `exclude_nodes`, `exclude_resources` | Both empty: all six workers and logical resources, including Mist. |
| `strategies` | `static`, `procedural`, `semantic`. |
| `experiments` | `effectiveness`, `adaptation`, `scalability`, `cumulative`. |
| `repetitions`, `warmup`, `seed` | 5, 2, 2026. |
| `multipliers` | 1, 4, 16; resources and policies grow together. |
| `events_per_context` | 10 for the non-cumulative families. |
| `cumulative_cycles` | 1, 4, 16 complete ordered context cycles. |
| `timeout_seconds` | 120 seconds for the entire isolated job, including initialization. |
| `connect_timeout_seconds` | 30 seconds for connection. |

There is no smoke or unlimited mode. Small fixtures under `tests/fixtures/`
serve software regression assertions only; they are not research profiles.

## Execution and failure semantics

Jobs are serially scheduled to avoid self-induced contention. Each runs in a fresh
process on its executor; warm-up is excluded from decision timing. Deterministic
strategy randomization and input hashes support paired comparisons. The runner
archives source and effective configuration. It does not overwrite deployed HTTP
workers. A local physical lease prevents overlapping project campaigns started
from this coordinator; it is not a distributed lock across coordinators.

GNU `timeout` bounds remote jobs with a termination grace, including after a lost
SSH connection. A timeout is recorded as censored work, not a completed latency.
Later jobs are attempted; there are no skip-after-timeout triggers. Unavailable
hosts remain in planned outcome counts. Static-plan disagreement is an expected
baseline outcome; adaptive disagreement or execution failures make the command
return nonzero. Ctrl+C preserves completed records and marks interruption.

## Metrics and figures

`setup_ms` includes adapter initialization; semantic setup includes inference and
query preparation. `reasoning_ms` is the materialization component, not an
additional independent sum. `decision_ms` includes selecting and assembling a
plan. Cumulative decision time is the running sum within a job. Loop throughput
excludes setup/warm-up. CPU and RSS are process-scoped and sampling-dependent.

Quality uses resource–metric pairs plus actions and sampling interval. Policy
IDs are metadata, not part of the fairness oracle. Full coverage alone is not
proof of a correct interval or absence of excessive monitoring. Expected plans
are acceptance fixtures, not independently annotated clinical observations.

Figures include per-node and all-node panels for every experiment, paired
strategy comparisons and a cross-node summary. `figure-data.csv`, captions and
`report.json` preserve provenance and coverage. Missing values are not zero;
insufficient repetitions must not be represented as reliable confidence intervals.
These are independent per-host results, not the cost of one six-node transaction.
