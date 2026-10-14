# Output layout and evidence

There are two evaluation batteries. Their results remain separate. All generated
evidence belongs under ignored `outputs/`; source configuration and documentation
remain version controlled. Existing historical runs are not moved, merged or
rewritten by this documentation update.

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
