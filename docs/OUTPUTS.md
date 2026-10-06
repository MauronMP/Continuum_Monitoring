# Outputs and Figures

The complete mapping from every test family to its raw files and PNG figures is
available in [Test, experiment and figure reference](TESTS_AND_FIGURES.md).

All generated evidence belongs under `outputs/`. The policy evaluation uses this
layout:

```text
outputs/policy-evaluation/
├── configuration.json
├── manifest.json
├── metadata.json
├── effectiveness/
│   ├── policy_effectiveness.csv
│   └── policy-effectiveness.png
├── dynamic-adaptation/
│   ├── dynamic_adaptation.csv
│   └── dynamic-adaptation.png
├── scalability/
│   ├── policy_scalability.csv
│   └── policy-scalability.png
└── computational-cost/
    ├── computational_cost.csv
    └── computational-cost.png
```

Run measurement and plotting separately:

```bash
continuum-bench policy-evaluation all \
  --evaluation-config configs/policy-evaluation.toml \
  --output-dir outputs/policy-evaluation
continuum-bench policy-evaluation plot \
  --output-dir outputs/policy-evaluation
```

Figures are generated only as 300 dpi PNG files. A missing CSV produces no
figure; it is never replaced with fabricated data. The four CSV files remain the
authoritative evidence and can be processed without Matplotlib.

The shared columns are `experiment_id`, `scenario_id`, `strategy`, `load_size`,
`repetition`, `policy_category`, `seed` and `status`. Experiment-specific fields
retain explicit units in their names, such as `_ms`, `_seconds`, `_mib`,
`_percent` and `_bytes`.

## Long physical runs

Each physical cumulative or scalability directory contains `progress.json`.
The coordinator replaces this file atomically whenever a point starts or ends.
It records the family, current point, total points, percentage, reasoner, load,
repetition, stage and phase. `summary.csv` is also checkpointed after every
finished, timed-out, skipped or failed point. A later worker failure therefore
does not discard the summary evidence already collected by that family.

Console output uses four progress records:

- `[physical-suite-progress]` identifies the cumulative or scalability family;
- `[benchmark-progress]` reports the global point number and percentage;
- `[distributed-batch]` reports the query-batch number and percentage inside
  the current point;
- `[distributed-progress]` is emitted every 15 seconds while HTTP workers are
  still processing a phase, with completed and pending node counts.

`completed`, `timeout`, `skipped_after_timeout`, `failed`,
`unvalidated_results` and `invalid_results` remain distinct outcomes. A native
reasoner crash is recorded as `failed`; it is never rewritten as a timeout or a
successful observation. `unvalidated_results` retains physical timings when the
canonical reference could not finish, while `invalid_results` records an exact
query mismatch. Neither outcome is used in performance curves.

Bounded mode with `--keep-going` is recommended for complete runs. Unlimited
mode is optional and may leave `progress.json` in `running` state indefinitely
when a native reasoner does not return. A stale progress timestamp, saturated
worker processes and nonresponsive health endpoints must be treated as an
incomplete run, never as a long completed measurement.

## Independent policy comparison

`outputs/comparison/<run-id>/` contains isolated paired comparison campaigns.
See [Comparative evaluation](COMPARATIVE_EVALUATION.md) for raw JSON, per-job CSV,
paired statistics, complete outcome coverage and the four per-node PNG families.
These results are separate from the existing policy and placement study contracts.

## Policy-evaluation interpretation

The policy-evaluation reasoning probe is a once-per-batch measurement. Its cost
figure divides it by `decision_iterations` before stacking it with per-decision
policy and plan costs. Historical CSV fields retain their original names;
`detection_latency_ms` measures a supplied-context read, not fault detection.
Observation and traffic volumes are estimates. See [Experiments](EXPERIMENTS.md)
for the decision and memory measurement boundaries. Regenerating PNGs does not
upgrade old runs to the current source identity or make smoke runs publication
evidence.
