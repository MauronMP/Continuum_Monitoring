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
│   ├── distributed-reasoning-scalability/
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
request_timeout_seconds = 300
request_retries = 0
worker_timeout_margin_seconds = 2

[limits]
timeout_mode = "bounded"
phase_timeout_seconds = 300
point_timeout_seconds = 900
consecutive_timeout_threshold = 1
skip_repetitions_after_timeout = false
skip_larger_sizes_after_timeout = false
skip_cumulative_stages_after_timeout = false
stop_scaling_after_timeout = false
```

The values are seconds. The production defaults allow five minutes per worker
request and fifteen minutes per configured point. A timeout is recorded, but
the remaining matrix continues. `request_timeout_seconds` bounds one HTTP
request. `phase_timeout_seconds` bounds a benchmark phase.
`point_timeout_seconds` bounds one configured point. The three `skip_*`
switches can be enabled for exploratory runs where pruning is desired.
Application errors do not activate timeout skip triggers.

Set `timeout_mode = "unlimited"` to record the configured budgets without enforcing them. The equivalent command-line option is `--unlimited`.

## Load, experiment, and campaign budgets

These families have workload-specific budgets:

- [`configs/load-benchmark.toml`](../../configs/load-benchmark.toml), section `[load]`: `request_timeout_seconds`, `point_timeout_seconds`, `recovery_timeout_seconds` and `stop_after_timeout`.
- [`configs/experiments.toml`](../../configs/experiments.toml), section `[experiment]`: `request_timeout_seconds`, `point_timeout_seconds` and `stop_after_timeout`.
- [`configs/distributed-reasoning.toml`](../../configs/distributed-reasoning.toml): dedicated matrix, request/point budgets, semantic-validation sample, timeout pruning, statistics and query concurrency for distributed reasoning scalability.
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

Global timeout overrides are propagated independently to monitoring, load,
campaign and every experiment configuration. `--request-timeout-seconds` does
not overwrite a separately configured phase or point budget; the corresponding
flag changes only that budget. `--timeout-seconds` intentionally sets all
applicable request, phase and point budgets to one value.

The distributed-reasoning family writes schema `distributed-reasoning-v1` rows,
per-node evidence, capacity bounds, query-concurrency observations and sampled
semantic validation. `profile_compatible=false` and
`skipped_profile_incompatible` preserve an unsupported ontology/profile pair;
they are not timeouts and are excluded from performance aggregation.
