# Output layout and execution controls

All generated evidence is stored below the single `outputs/` root. Commands no longer add redundant `physical` or `current` levels.

```text
outputs/
├── monitoring/
│   ├── distributed/{cumulative,scalability}/
│   └── replicated/{cumulative,scalability}/
├── load/
│   └── analysis/{data,figures}/
├── experiments/
│   ├── scale-out/
│   ├── reasoning-hardware/
│   ├── distributed-ontology/
│   ├── analysis/
│   └── figures/
├── campaign/
├── report/
├── validation/readiness/
├── runtime/{physical,setup}/
└── suites/<run-id>/
```

`outputs/report/` contains the unified scientific PNG report and its source CSV files. `outputs/runtime/` contains process state and logs, not benchmark measurements. A complete suite keeps the same category names inside its unique `outputs/suites/<run-id>/` directory.

## Monitoring timeouts and skip triggers

Edit [`configs/benchmark.toml`](../../configs/benchmark.toml):

```toml
[distributed]
request_timeout_seconds = 60
request_retries = 0
worker_timeout_margin_seconds = 2

[limits]
timeout_mode = "bounded"
phase_timeout_seconds = 60
point_timeout_seconds = 90
consecutive_timeout_threshold = 1
skip_repetitions_after_timeout = true
skip_larger_sizes_after_timeout = true
skip_cumulative_stages_after_timeout = true
stop_scaling_after_timeout = true
```

The values are seconds. `request_timeout_seconds` bounds one HTTP request. `phase_timeout_seconds` bounds a benchmark phase. `point_timeout_seconds` bounds one configured point. The three `skip_*` switches decide which later observations become `skipped_after_timeout` after `consecutive_timeout_threshold` consecutive timeouts. Application errors do not activate timeout skip triggers.

Set `timeout_mode = "unlimited"` to record the configured budgets without enforcing them. The equivalent command-line option is `--unlimited`.

## Load, experiment, and campaign budgets

These families have workload-specific budgets:

- [`configs/load-benchmark.toml`](../../configs/load-benchmark.toml), section `[load]`: `request_timeout_seconds`, `point_timeout_seconds`, `recovery_timeout_seconds` and `stop_after_timeout`.
- [`configs/experiments.toml`](../../configs/experiments.toml), section `[experiment]`: `request_timeout_seconds`, `point_timeout_seconds` and `stop_after_timeout`.
- [`configs/campaign.toml`](../../configs/campaign.toml), section `[campaign]`: `request_timeout_seconds` and `point_timeout_seconds`.

Global command-line overrides must precede the command:

```bash
continuum-bench --request-timeout-seconds 300 \
  --phase-timeout-seconds 600 \
  --point-timeout-seconds 900 \
  --skip-after-timeouts 3 \
  --no-skip-repetitions \
  --no-skip-larger-points \
  --no-skip-cumulative-stages \
  physical all
```

Use `--keep-going` to disable skip pruning while retaining finite timeout budgets. Use `--unlimited` when operations must be allowed to finish without elapsed-time cancellation.

