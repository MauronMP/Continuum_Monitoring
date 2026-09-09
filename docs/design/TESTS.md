# Test and validation catalogue

The project separates software checks, semantic validation, smoke tests and
measurement campaigns. A command returning zero only certifies the contract of
that command; it does not imply scientific acceptance of every requirement.

## Difference between benchmark families

| Family | Main question | What changes | Principal outputs |
| --- | --- | --- | --- |
| Normal cumulative | What is the cost of enabling more semantic/policy functionality? | Categories and all queries accumulated stage by stage | Per-stage/query execution and inference timings |
| Normal scalability | How does the monitoring ontology react to larger synthetic graphs and user populations? | Synthetic users and RDF individuals/volume | Per-block/query timings, inferred triples and timeout state |
| Load, one dimension | Where is the saturation point for one controlled factor? | One of events/s, users, triples, rules or active nodes | Event, node and summary rows with percentiles, throughput, loss and resources |
| Load, complete matrix | How does the system respond across all configured demand axes? | Every enabled load profile and dimension | The union of all load observations and coverage data |
| Experiments all | Which architectural mechanism explains performance? | Replicas/node count, reasoning hardware, then ontology partitioning | Three experiment datasets and architecture-specific comparisons |

“Normal” tests execute the ontology/query catalogue under two broad progression
models. Load tests model sustained request pressure and resource saturation.
Experiments deliberately isolate architectural hypotheses so that a speedup is
not attributed to distribution when it actually comes from replication,
different hardware or a smaller ontology fragment.

There is no literal `continuum-bench load all` command. The complete matrix is
selected by omitting filters:

```bash
continuum-bench load physical
```

The aggregate command `continuum-bench experiment all physical` executes the
three experiment families sequentially. `continuum-bench suite` additionally
orchestrates all physical benchmark families and acceptance checks.

## Software and documentation checks

```bash
python -m pytest
continuum-bench preflight
python3 tools/check_documentation.py
git diff --check
```

`pytest` covers configuration loading, topology elasticity, ontology/query
contracts, mobility, placement, orchestration, timeout censoring and analysis.
The documentation checker validates internal links and documented paths.

## Semantic checks

```bash
continuum-bench validate
continuum-bench owl-validate
continuum-bench owl-validate --require-all
```

The first command runs the internal RDF/SHACL/query battery and the three
portable materialization profiles. The second invokes every available external
OWL validator. The strict form requires HermiT, Openllet, JFact and Konclude.
An unavailable reasoner is reported as unavailable, never as a success.

Scientific acceptance is stricter than process success. Known unmet external
query expectations, including EXT-Q76/EXT-Q77 when present in the current
reference set, remain explicit limitations and must not be hidden by a green
structural validation.

## Smoke tests



Physical:

```bash
continuum-smoke-physical-cumulative --ssh-user pi
continuum-smoke-physical-scalability --ssh-user pi
continuum-smoke-physical-load
continuum-smoke-physical-experiments
continuum-smoke-physical-cumulative --layout replicated --ssh-user pi
continuum-smoke-physical-scalability --layout replicated --ssh-user pi
```

Smokes use bounded profiles and one repetition to verify deployment,
partitioning, query execution, result transport and CSV generation. They now
inspect the generated summaries and exit non-zero for timeout, early skip,
event loss or incomplete semantic validation. They are not performance
evidence.

The unit suite also injects simulated HTTP 408/timeout failures into both
replicated and sharded scalability runners. It verifies that later points for
the affected reasoner become `skipped_after_timeout` while the other reasoners
still execute. This checks the failure policy without waiting for a real
deadline.

The independent semantic-product smoke is:

```bash
continuum-smoke-engines
continuum-bench engines plot
```

It checks already-running native RDFLib, Jena, RDF4J and Oxigraph services.

## Monitoring benchmarks

Run cumulative and scalability independently:

```bash
continuum-bench physical cumulative --layout sharded --ssh-user pi
continuum-bench physical scalability --layout sharded --ssh-user pi
```

Or run both with `all`:

```bash
continuum-bench physical all --layout sharded --ssh-user pi
continuum-bench physical all --layout replicated --ssh-user pi
```

`physical all` means cumulative plus scalability only. It does
not include load, experiments, studies, unit tests or OWL validation.

## Load campaign

```bash
continuum-bench load physical
```

The campaign varies events/s, users, target triples, rules and active nodes. It
records latency percentiles, throughput, loss, inference time, alert accuracy,
CPU, memory, disk, network and recovery observations. Timeouts are recorded as
right-censored outcomes in bounded mode. Use `--unlimited` before `load` to
finish accepted work without elapsed-time cutoffs.

## Three separated experiments

```bash
continuum-bench experiment scale-out physical
continuum-bench experiment reasoning-hardware physical
continuum-bench experiment distributed-ontology physical
continuum-bench experiment all physical
```

- `scale-out` evaluates replicated query service while varying workers.
- `reasoning-hardware` isolates materialization cost by node hardware.
- `distributed-ontology` evaluates authority/category fragments, local
  reasoning and federated result merge against a canonical result bag.

## Study and figures

```bash
continuum-bench study trace --target physical --output-dir outputs/study/physical
continuum-bench study category-cost --events outputs/load/physical/event-runs.csv --output-dir outputs/study/physical-cost
continuum-bench report
continuum-bench load plot
continuum-bench experiment plot all
continuum-bench experiment analyze
continuum-bench engines plot
```

Trace generation is deterministic workload preparation, not live semantic
replay. Cost analysis consumes measured event rows; it does not invent missing
resource metrics. Benchmark figures are generated only as 300-DPI PNG. Experiment plotting also writes `experiment-data-quality.csv` and a
stacked coverage figure, keeping completed, censored and failed observations
visible.

The exact end-to-end command order is maintained in
[Command reference](COMMAND_REFERENCE.md).

## Complete physical suite and execution policies

After the deployment described in [Physical continuum](PHYSICAL_CONTINUUM.md):

```bash
continuum-bench --unlimited --repetitions 5 suite --dry-run
continuum-bench --unlimited --repetitions 5 suite
continuum-bench --unlimited --repetitions 5 suite --families load experiments campaign report
```

The default order is software tests, semantic validation/preflight/strict external
OWL validation, worker startup, sharded monitoring, replicated monitoring, load,
all three experiments, the full ten-axis campaign and publication reporting.
The separate native semantic-product matrix and study traces are not included.
The suite starts existing deployments; it does not install workers or authorize SSH.

| Policy | Command example | Behavior |
| --- | --- | --- |
| Configured limits | `continuum-bench load physical` | Enforce configured budgets and configured timeout pruning. |
| Extended limits | `continuum-bench suite --patient` | One-hour budgets; attempt later points after timeout. |
| Custom finite limits | `continuum-bench --timeout-seconds 7200 --keep-going load physical` | Enforce the selected limit without timeout pruning. |
| Unlimited | `continuum-bench --unlimited load physical` | Disable benchmark elapsed-time cutoffs and timeout pruning. |

Global options precede the command. `--timeout-seconds` must be finite and greater
than five; `--repetitions` must be positive. Unlimited mode preserves nominal
budgets in metadata with `execution_policy.timeout_mode = "unlimited"` and
`configured_budgets_enforced = false`. Preparation, query/point waits, local
reasoning, HTTP requests, worker alarms and recovery follow that policy.
Load duration still controls offered events; accepted work is drained afterward.
Health/startup checks and external OWL validator limits remain operational checks.
Errors, incorrect results, queue loss and disconnections are not hidden.

Each suite creates `outputs/suites/<UTC-time>-<id>/` containing `suite.json`,
per-step logs, source/dependency provenance, physical/load/experiment/campaign
results and a `paper/` report. Inspect logs while it runs. A non-zero child exit
or incomplete monitoring/load/experiment summary makes that step fail; later
families still execute. Cancellation is manual; a blocked operation may require
terminating the coordinator and restarting the affected worker. Previous suite
results are retained. Individual commands using the same output directory can
replace earlier results, so select a new `--output-dir` for comparisons.

## Modular ten-axis physical campaign

```bash
continuum-bench campaign --campaign-config configs/campaign.toml --validate-only
continuum-bench --unlimited --repetitions 5 campaign --campaign-config configs/campaign.toml
continuum-bench --unlimited campaign --campaign-config configs/campaign.toml --axis physical_nodes --axis concurrency
```

`campaign` alone selects `configs/campaign-smoke.toml`; the full suite explicitly
selects `configs/campaign.toml`. The full configuration varies `physical_nodes`,
`iot_devices`, `users`, `requests`, `policies`, `individuals`, `requirements`,
`query_count`, `query_complexity` and `concurrency`. It compares the configured
replicated and distributed modes with common workloads and result validation.
Reasoners, categories, warm-up, repetitions and seed are configured in TOML.
Outputs include a manifest, configuration, provenance and versioned JSONL/CSV
with per-request evidence. See [Modular monitoring](MODULAR_MONITORING.md).

## New regression coverage and physical verification

| Test file | Contract verified |
| --- | --- |
| `tests/monitoring/test_unlimited.py` | Delayed HTTP completes beyond its nominal limit; worker alarms are disabled; local/future waits are unbounded; HTTP failures remain failures; suite propagates the policy. |
| `tests/monitoring/test_load_benchmark.py` | Event conservation, queue loss, bounded deadlines and unlimited draining after an expired point budget. |
| `tests/monitoring/test_patient_load.py` | Later profiles execute when timeout pruning is disabled. |
| `tests/monitoring/test_campaign.py` | Equivalent placements, workload axes, result evidence and campaign completion past nominal deadlines. |
| `tests/reporting/test_publication.py` | PNG output, preservation of genuine zero values, missing-data handling, skipped/timeout distinction, suite failure detection and replica resource aggregation. |
| `tests/reporting/test_experiment_reporting.py` | Physical experiment reports and outcome coverage. |

Run these regressions without running a long physical campaign:

```bash
python -m pytest -q tests/monitoring/test_unlimited.py tests/monitoring/test_load_benchmark.py tests/monitoring/test_patient_load.py tests/monitoring/test_campaign.py tests/reporting/test_publication.py tests/reporting/test_experiment_reporting.py
```

The HTTP regression opens a localhost socket. Unit tests use controlled workers
or infrastructure doubles; they do not establish physical performance.
For the real-node unlimited smoke, with workers already running:

```bash
continuum-bench --timeout-seconds 6 --unlimited --repetitions 1 load physical --load-config configs/load-smoke.toml --output-dir outputs/audit/unlimited-load
```

The recorded verification completed six points and 12/12 events without loss,
including five-node preparation/recovery phases of about 23 seconds despite the
nominal six-second budget. This verifies timeout behavior, not statistical power.
[Publication reports](PUBLICATION_REPORTS.md) documents the separate extended-load
validation, PNG figures, missing historical telemetry and analytical distances.
