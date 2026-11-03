# Benchmark outputs

Run directories are generated here and ignored by Git. Each new run contains a manifest, exact configuration/topology, a self-contained semantic-contract snapshot, scenario datasets, reference semantic digests, separate warm-up evidence, independently partitioned measured repetitions, raw logical/physical query records, phase-labelled one-second-target resource samples, summaries, twenty-one PNG figures, and a figure manifest. See `docs/RESULTS.md`.

Independent continuous-monitoring runs use `monitoring-<run-id>/`. They contain deployed-idle and configured demand-level windows, scheduler/task/query evidence, per-host and per-policy summaries, idle-versus-active comparisons, and seven monitoring-specific figures. See `docs/MONITORING_OVERHEAD.md`.
