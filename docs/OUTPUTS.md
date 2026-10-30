# Output layout and evidence

There are three evaluation batteries. Their results remain separate. All generated
evidence belongs under ignored `outputs/`; source configuration and documentation
remain version controlled. The cleanup on 14 October 2026 retained only the latest acquired run of each
battery. Older runs, dry-run plans, standalone results and maintenance outputs
were deleted. Retained acquisition files were verified unchanged using SHA-256.

## Start here: retained results

| Battery | Retained directory | What to open first | Recorded outcome |
| --- | --- | --- | --- |
| Physical architecture | `outputs/suites/20261007T120755Z-11ab3e5f/` | `review.md`, then `suite.json`; `diagnostic-figures/` for partial-data plots. | Partial: distributed monitoring timed out; replicated monitoring, load, experiments, campaign and report failed. |
| Monitoring comparison | `outputs/comparison/20261009T162702Z-0df2fd02/` | `figure-captions.md`, `figures/`, then `outcomes.csv` and `summary.csv`. | Completed: 720 jobs, six hosts, zero failed jobs recorded. |

These acquisitions predate the latest code cleanup. They are not results of the
current revision. The physical suite's `report-recovered/` and diagnostic figures
must not be presented as evidence that its failed steps succeeded. Preserve the
raw data, source snapshots, configurations and logs inside these two run roots.
Later figure rendering dates do not constitute a new experimental acquisition.

`outputs/README.md` provides direct links to these results. `outputs/audit/current-review/` contains the latest requested maintenance checks,
not an experimental battery. `outputs/runtime/`
contains operational state for active services, not scientific results, and was
preserved to avoid disrupting workers. Other output families described below are
created by future commands; their presence is not required after this cleanup.

## Battery 1: complete physical suites

```text
outputs/suites/<run-id>/
  suite.json                         # planned steps, outcomes and command logs
  source.tar.gz                      # source snapshot for provenance/recovery
  software-tests.xml                 # engineering regressions
  validation/                        # native ontology consistency evidence
  monitoring/
    distributed/
      scalability/                   # growing synthetic workload
      cumulative/                    # cumulative category workload
    replicated/
      scalability/
      cumulative/
  load/                              # offered event/load profiles
  experiments/
    scale-out/                       # physical node-count experiment
    reasoning-hardware/              # graph/rule/user sizes by backend/node
    distributed-ontology/            # fragmentation/reference comparison
    distributed-reasoning-scalability/
  campaign/<run-id>/                 # configurable independent workload axes
  policy-evaluation/
    effectiveness/
    dynamic-adaptation/
    scalability/
    computational-cost/
  report/                            # accepted plots/tables and coverage audit
  *.log                              # separate logs for executed suite steps
```

The actual step inventory is in `suite.json`; absent folders can mean a family
was not selected, was blocked or never started. A directory alone is not evidence
of successful completion. Reports may reject performance figures when required
families or semantic acceptance are missing.

| Family | Authoritative evidence | Derived material |
| --- | --- | --- |
| Monitoring | `summary.csv`, query/node observations, result validation, `metadata.json`, `progress.json` where emitted. | Node, category, query, reasoner and placement PNGs. |
| Load | `summary.csv`, `event-runs.csv`, node-level timing/resource records and metadata. | Completion, timeout/loss, latency, throughput and capacity figures. |
| Physical experiments | Per-family `summary.csv`; `query-runs.csv` / `result-validation.csv` where applicable; metadata. | Scale-out, hardware, placement and semantic-validation summaries. |
| Campaign | `manifest.json`, `results.jsonl`, `results.csv`. | Axis-based comparisons from recorded jobs. |
| Policy effectiveness | `effectiveness/policy_effectiveness.csv`. | `policy-effectiveness.png`. |
| Dynamic adaptation | `dynamic-adaptation/dynamic_adaptation.csv`. | `dynamic-adaptation.png`. |
| Policy scalability | `scalability/policy_scalability.csv`. | `policy-scalability.png`. |
| Computational cost | `computational-cost/computational_cost.csv`. | `computational-cost.png`. |

Standalone commands use `outputs/monitoring/`, `outputs/load/`,
`outputs/experiments/`, `outputs/campaign/` and `outputs/policy-evaluation/`
respectively, preserving the same family subfolders. Repeated standalone runs
can target the same directory; supply a distinct `--output-dir` when retaining
multiple acquisitions. Complete suites create unique run roots automatically.

## Battery 2: isolated monitoring-strategy comparison

```text
outputs/comparison/<run-id>/
  metadata.json                      # source/config/topology and run status
  configuration.json                 # effective comparison configuration
  policy-configuration.toml          # acceptance plans and rules
  source.zip                         # acquisition code bundle
  jobs.jsonl                         # durable job outcomes
  summary.csv                        # one row per job
  outcomes.csv                       # completion/failure denominators
  paired-comparisons.csv              # available matched strategy statistics
  figure-data.csv                    # source points, repetitions and coverage
  figure-captions.md                  # definitions and interpretation
  report.json                        # report provenance and figure list
  report-source.zip                  # code used for rendering
  effectiveness/raw/                 # individual job JSON evidence
  adaptation/raw/
  scalability/raw/
  cumulative/raw/
  figures/                           # general comparison panels
```

Each experiment also receives its per-node and all-node PNGs as listed in
`report.json`. Do not infer filenames or success from a fixed figure count;
the manifest describes what was generated from that run. Mist must appear in a
complete six-host run. An unavailable host is a recorded outcome, not silently
removed from the planned denominator.

## Supporting outputs, not additional batteries

- `outputs/validation/`: semantic and preflight checks run outside suites.
- `outputs/audit/`: module/file inspections and worker-maintenance evidence.
- `outputs/fragments/`: exported asserted per-node Turtle and manifests.
- `outputs/runtime/`: process logs, PID files, setup state and physical leases.
- `outputs/study/`: analytical traces or category attribution derived from actual
  event files; analytical distance estimates are not physical measurements.
- `diagnostic-figures/` inside a historical suite: explicitly partial plots made
  from archived source. They never override the publication acceptance gate.

No ontology-diagram generator is maintained. Author-supplied ontology images
are independent of benchmark outputs and are not regenerated by these commands.

## Status, units and metric scope

Retain `completed`, `timeout`, `failed`, `skipped_after_timeout`,
`unvalidated_results` and `invalid_results` as distinct outcomes. Unknown metrics
stay missing. `unvalidated_results` means physical work exists but reference
validation did not finish; `invalid_results` means recorded answers differ.
Neither belongs in accepted performance comparisons.

Units are explicit (`_ms`, `_seconds`, `_bytes`, `_mib`, `_kib`, `_percent`).
CPU process time, sampled RSS and child-process peak resources have different
scopes. Read the recorded scope fields. Monitoring throughput is not necessarily
sensor throughput; decision-loop throughput excludes initialization unless stated.

Policy-plan traffic estimates are not network-interface measurements. VPN overhead
in coordinator timing includes serialization, scheduling and protocol work; it
is not pure propagation delay. Nominal `network_mbps` neither caps traffic nor
establishes measured bandwidth.

## Figures and recovery

Figures use measured/recorded input and PNG output. No missing series is fabricated.
Use [Complete execution](COMPLETE_EXECUTION.md) for each battery's report commands.
Regeneration changes presentation, not acquisition identity or scientific validity.
Preserve source/configuration snapshots, exact outcome counts and raw evidence.
Historical reduced acquisitions remain historical; they are not full campaigns.

## Battery 3: container scalability

Each run is isolated under `outputs/container-scale/<run-id>/`. Open `campaign.json`
first, then `figures/manifest.json`. `configuration.json` records effective options;
`placement-*/placement.json` distinguishes physical hosts from logical participants.
Each scenario separates `warmup/` from `measured/`. Docker snapshots and preflight
records are evidence about deployment/resources, not additional scientific runs.

The measured directory contains preparation summaries, node rows, query load,
logical client throughput and semantic validation. PNG figures cover costs, all
participants, physical-host aggregation, concurrency and completion states. Do not
use internal fan-out query counts as cross-layout throughput. See the complete
[output contract](CONTAINER_SCALABILITY.md#results-and-figures). Historical retained
results above predate this battery and cannot validate its deployment.

## Adaptive recovery evidence

`outputs/adaptive-monitoring/<run-id>/` contains policy/configuration snapshots, decisions, per-attempt recovery measurements and service samples, plus CSV/PNG before-after outcomes. Planning runs retain missing after-values as NA. See [Adaptive monitoring](ADAPTIVE_MONITORING.md) for states and interpretation.

For detailed adaptive comparisons, `tools/report_adaptive_comparison.py` creates `figures/manifest.json`, completion/concurrency/node-cost PNGs, physical-host telemetry plots and `analysis/COMPARISON.md` with the associated CSV tables. The original root-level `recovery-outcomes.png` remains available for compatibility and is copied into the figure collection.

Adaptive paired comparisons additionally export `analysis/paired-service-outcomes.csv` and `analysis/intervention-trajectory.csv`. `figures/paired-*-availability.png` separates preparation completion from request completion; `paired-*-concurrency-benefit.png` compares matched user/concurrency cells; `paired-*-intervention-cost.png` reports every measured intervention's effectiveness and deployment/verification time. Only the intervention's target layout contributes adaptive measurements. No trial is not a zero-cost or successful trial.

## Latest publishable campaign

`outputs/latest/` is the Git-visible snapshot of the most recently exported adaptive campaign, including its nested baseline. Earlier local campaigns were removed after verified export. `outputs/runtime/` remains local operational state. Use [the publication guide](LATEST_RESULTS.md) to refresh the snapshot, regenerate figures and upload it without staging unrelated code changes. `.gitignore` continues to exclude all other output directories.

For origin-preserving runs, `replica-routing.csv` records actual request destinations and successful-request CPU/RSS; `*-origin-work.png` and `analysis/replica-workshare.csv` distinguish originals from copies. `outputs/validation/origin-pool-*` holds bounded mechanism validation evidence and is ignored by Git. It does not replace the last scientific campaign.
