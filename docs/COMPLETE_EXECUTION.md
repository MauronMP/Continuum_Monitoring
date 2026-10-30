# Complete execution guide

## Index

1. [Scope and prerequisites](#scope-and-prerequisites)
2. [Battery 1: physical architecture evaluation](#battery-1-physical-architecture-evaluation)
3. [Battery 2: monitoring-strategy comparison](#battery-2-monitoring-strategy-comparison)
4. [Battery 3: container scalability](#battery-3-container-scalability)
5. [Validation and maintenance](#validation-and-maintenance)
6. [Timeouts and recovery](#timeouts-and-recovery)

## Scope and prerequisites

There are **three executable evaluation batteries**. The proposed four-strategy
extension is future work and has no command yet. Software regression tests are
engineering checks, not an additional scientific battery.

Complete [Installation](INSTALLATION.md) first. Commands below run from the
repository root. The default topology includes Cloud, Fog, Mist and three Edge
nodes. No five-node fallback profile is maintained.

```bash
source .venv/bin/activate
export CONTINUUM_SSH_PROBE_TIMEOUT_SECONDS=120
export CONTINUUM_HEALTH_TIMEOUT_SECONDS=30
continuum-bench physical status --ssh-user pi
```

Read the [experiment contracts](EXPERIMENTS.md) before interpreting results.
Do not run the batteries concurrently. Freeze source, ontology, queries and
configuration for each campaign; do not redeploy workers during acquisition.
`network_mbps` is descriptive inventory metadata, not a traffic limiter. The
physical experiments use actual VPN links without bandwidth shaping.

## Battery 1: physical architecture evaluation

### Basic command: complete battery

```bash
continuum-bench --timeout-mode bounded --keep-going suite
```

This executes software/documentation checks, semantic validation, workload
preflight, worker startup, distributed and replicated monitoring, load,
physical experiments, configurable campaign axes, local policy evaluation and
reporting. The distributed-reasoning-scalability family is included by the suite.
Every suite has its own `outputs/suites/<run-id>/` directory. The independent
comparison module is not included.

Preview the exact commands without acquiring measurements:

```bash
continuum-bench --timeout-mode bounded --keep-going suite --dry-run
```

The following complementary commands execute individual parts of Battery 1.
Their output paths differ from a complete suite; do not accidentally combine
independent runs into one accepted campaign.

### Physical monitoring: scalability and cumulative categories

```bash
continuum-bench --timeout-mode bounded --keep-going physical all --layout distributed
continuum-bench --timeout-mode bounded --keep-going physical all --layout replicated
continuum-bench --timeout-mode bounded --keep-going physical scalability --layout distributed
continuum-bench --timeout-mode bounded --keep-going physical cumulative --layout distributed
```

Use `--reasoner rdfs`, `--reasoner hermit`, `--reasoner openllet`,
`--reasoner jfact` or `--reasoner konclude` after `physical` to select a backend;
omitting it uses all configured backends. Sizes, categories, seed and repetitions
are in `configs/benchmark.toml`.

### Load

```bash
continuum-bench --timeout-mode bounded --keep-going load physical
continuum-bench --timeout-mode bounded --keep-going load physical --dimension users
continuum-bench load plot --output-dir outputs/load
```

`configs/load-benchmark.toml` defines named profiles. Other `--dimension` values
are `events_per_second`, `target_triples`, `rule_count`, and `node_count`.
`--profile NAME` selects an existing profile, not a newly invented workload.

### Physical experiment families

```bash
continuum-bench --timeout-mode bounded --keep-going experiment all physical --distributed-reasoning-config configs/distributed-reasoning.toml
continuum-bench --timeout-mode bounded --keep-going experiment scale-out physical
continuum-bench --timeout-mode bounded --keep-going experiment reasoning-hardware physical
continuum-bench --timeout-mode bounded --keep-going experiment distributed-ontology physical
continuum-bench --timeout-mode bounded --keep-going experiment distributed-reasoning-scalability physical
continuum-bench experiment plot all --output-dir outputs/experiments
continuum-bench experiment analyze --output-dir outputs/experiments
```

The first three families use `configs/experiments.toml`; distributed reasoning
uses `configs/distributed-reasoning.toml`. For the standalone `experiment all`,
pass the latter explicitly as shown. The complete `suite` already does so.

### Configurable workload axes

```bash
continuum-bench campaign --campaign-config configs/campaign.toml --validate-only
continuum-bench --timeout-mode bounded --keep-going campaign
continuum-bench --timeout-mode bounded --keep-going campaign --axis physical_nodes
```

`configs/campaign.toml` controls resource, user, IoT, policy, requirement, query,
request and concurrency axes. Each campaign creates a unique result directory.

### Local policy-plan evaluation

These are components of Battery 1, not a third battery or a physical recovery test.

```bash
continuum-bench policy-evaluation all
continuum-bench policy-evaluation effectiveness
continuum-bench policy-evaluation dynamic-adaptation
continuum-bench policy-evaluation scalability
continuum-bench policy-evaluation computational-cost
continuum-bench policy-evaluation plot
```

Configuration: `configs/policy-evaluation.toml`. The separate reasoning probe
is not part of the procedural decision path; network volumes here are estimates.

### Reports and optional analysis

Replace `RUN_ID` with an existing directory name; the following commands read
already acquired data and do not create new experimental evidence.

```bash
continuum-bench report --input-dir outputs/suites/RUN_ID --output-dir outputs/suites/RUN_ID/report
python tools/render_suite_diagnostics.py outputs/suites/RUN_ID
continuum-bench study category-cost --events outputs/load/event-runs.csv --output-dir outputs/study
```

The diagnostic renderer uses the suite's archived source and clearly labels
partial results. It does not override publication acceptance. `study trace`
is an optional analytical trace generator, not an additional physical battery:

```bash
continuum-bench study trace --output-dir outputs/study
```

Its distance/link models do not throttle real interfaces and must not be confused
with measured geographical distances. Ontology illustration generation is not
provided; figures supplied by the author are managed separately.

## Battery 2: monitoring-strategy comparison

### Basic commands: availability and complete battery

```bash
python -m continuum_bench.monitoring.comparison check
python -m continuum_bench.monitoring.comparison run
```

All six nodes participate by default. The full configuration schedules 720 jobs:
three strategies, four experiment families with their configured size points,
six hosts and five repetitions. The families are effectiveness, adaptation,
scalability and cumulative processing. See [Experiments](EXPERIMENTS.md).

### Complementary commands

```bash
python -m continuum_bench.monitoring.comparison run --config configs/comparison.toml --output outputs/comparison
python -m continuum_bench.monitoring.comparison report outputs/comparison/RUN_ID
```

For a deliberately different experiment, copy `configs/comparison.toml`, adjust
its `experiments`, `strategies`, repetitions or size lists, and pass the copy with
`--config`. Paths to `policy_config` and `topology` are relative to that config.
The default has no excluded workers or logical resources. Selective `--nodes`
execution remains available for fault diagnosis, not as a five-node recipe.
There is no smoke mode. Whole-job and connection limits are configured separately
in this module; it does not inherit Battery 1's CLI timeout flags.

## Validation and maintenance

These checks validate software/assets and are not scientific campaigns:

```bash
continuum-bench doctor --physical --owl
continuum-bench topology validate
continuum-bench validate
continuum-bench preflight
continuum-bench owl-validate --require-all
python tools/audit_ontology_modules.py
python tools/review_validation_debt.py
python tools/generate_reference_docs.py
python tools/generate_project_indexes.py
python tools/check_documentation.py
python -m pytest
```

Set `CONTINUUM_TEST_NATIVE_OWL=1` when running native integration regressions:

```bash
CONTINUUM_TEST_NATIVE_OWL=1 python -m pytest tests/core/test_native_reasoners.py tests/integration
```

After editing code or semantic assets, and only when no campaign is active:

```bash
continuum-bench physical deploy --with-dl-reasoners --ssh-user pi
continuum-bench physical start --ssh-user pi
continuum-bench physical status --ssh-user pi
```

A slow old process can outlast the five-second shutdown wait. If startup reports
exit 22, inspect the affected worker and retry startup after it has exited;
already compatible services are retained. Do not blindly kill unrelated processes.

## Timeouts and recovery

Battery 1 defaults: request 300 s, phase 300 s, point 900 s. Configuration lives
in `[distributed]` and `[limits]` of `configs/benchmark.toml`, with family-specific
budgets in load, experiment and campaign TOMLs. A longer bounded example is:

```bash
continuum-bench --timeout-mode bounded --request-timeout-seconds 300 --phase-timeout-seconds 600 --point-timeout-seconds 1800 --skip-after-timeouts 2 --no-skip-repetitions --no-skip-larger-points --no-skip-cumulative-stages --keep-going suite
```

`--keep-going` preserves failures and attempts independent later points. Skip
triggers control whether later repetitions, sizes or stages are omitted after
timeouts; they do not turn errors into successful measurements. A complete suite
can finish with a nonzero exit code if some steps fail. Check `suite.json` and
individual logs, not only the progress percentage.

`--unlimited` remains optional for supervised diagnosis; a reasoner that never
returns can block progression indefinitely. It does not fix memory exhaustion.
Battery 2 instead requires finite limits: default 120 s per isolated job and
30 s for SSH connection, plus transport termination allowance.

Use Ctrl+C for controlled interruption. Preserve partial output and start a new
run; do not relabel a partial campaign as complete. Historical results remain
immutable evidence under their original source and semantic fingerprints.

## Battery 3: container scalability

All six physical hosts, including Mist, are enabled in
`configs/container-scale.toml` with `deployment.exclude_hosts = []`.

This is separate from `suite` and the strategy-comparison command. The full run
deploys its Compose workers automatically. Configuration and scenario definitions:
`configs/container-scale.toml`. Detailed methods: [Container scalability](CONTAINER_SCALABILITY.md).

```bash
source .venv/bin/activate
continuum-bench container-scale doctor
continuum-bench --timeout-mode bounded --keep-going container-scale run
```

Complementary commands:

```bash
continuum-bench container-scale render
continuum-bench container-scale run --dry-run
continuum-bench container-scale deploy
continuum-bench container-scale status
continuum-bench --keep-going --repetitions 1 container-scale run --scenario users-1
continuum-bench --keep-going container-scale run --containers-per-host 2
continuum-bench container-scale report --input-dir outputs/container-scale/REPLACE_WITH_RUN_ID
continuum-bench container-scale stop
```

Replace the report directory with the returned `Results:` path. Two participants
per host are optional and still subject to live and declared capacity checks.
Default request/point budgets are 120/600 seconds in this module. `--unlimited` is
optional and may block a reasoner indefinitely; bounded mode is recommended.
The final placement remains running until `stop`; do not overlap with other
physical campaigns. Partial acquisition returns a nonzero exit status while
`--keep-going` preserves subsequent scenarios and their evidence.

### Container battery with an unavailable host

If Mist becomes unavailable, use the explicit exclusion below. The maintained
inventory remains complete; the effective run configuration records the exclusion.
Omit the option when all six hosts are available.

```bash
continuum-bench container-scale doctor --exclude-host mist
continuum-bench --timeout-mode bounded --keep-going container-scale run --exclude-host mist
continuum-bench container-scale status --exclude-host mist
continuum-bench container-scale stop --exclude-host mist
```

This is Battery 3 and is not included in the native `suite` command.

### Container reasoner matrix

Each repeated `--reasoner` adds a backend to the selected matrix, replacing the
TOML list for that invocation. Native backends automatically enable the DL image.
All six hosts, including Mist, are selected by the maintained configuration.

```bash
# Incremental selection:
continuum-bench --timeout-mode bounded --keep-going container-scale run --reasoner rdfs --reasoner jfact
# Validate all installed backends after deployment:
continuum-bench container-scale deploy --reasoner rdfs --reasoner hermit --reasoner openllet --reasoner jfact --reasoner konclude
continuum-bench container-scale validate-reasoners --reasoner rdfs --reasoner hermit --reasoner openllet --reasoner jfact --reasoner konclude
# Full configured workload matrix with all backends:
continuum-bench --timeout-mode bounded --keep-going container-scale run --reasoner rdfs --reasoner hermit --reasoner openllet --reasoner jfact --reasoner konclude
```

The plain `container-scale run` still uses the TOML defaults. Explicit selections
apply only to their invocation; pass them again on subsequent commands or edit
`experiment.reasoners` and `deployment.install_dl` for persistent selection.

### User scalability: 1 to 2000 users

The default container campaign now includes 1, 50, 100, 500, 1000 and 2000
synthetic users. To run only those six scenarios, with both configured layouts,
three measured repetitions and one warm-up:

```bash
source .venv/bin/activate
continuum-bench --timeout-mode bounded --keep-going container-scale run \
  --reasoner rdfs \
  --scenario users-1 --scenario users-50 --scenario users-100 \
  --scenario users-500 --scenario users-1000 --scenario users-2000
```

Omit all `--scenario` options to run all eleven scenarios, including the existing
data-volume, request-concurrency and fixed/proportional-load scenarios. Repeat
`--reasoner` to select additional backends. Append `--dry-run` to inspect the plan
without contacting nodes. Existing results are not changed or extrapolated.

### Cross user counts with configurable request concurrency

Add `--concurrency 1 2 4 N` to a container run, replacing `N` with any positive
integer. For example, the following compares all six user sizes at concurrency
1, 2, 4 and 8, in both configured layouts:

```bash
continuum-bench --timeout-mode bounded --keep-going container-scale run \
  --reasoner rdfs --concurrency 1 2 4 8 \
  --scenario users-1 --scenario users-50 --scenario users-100 \
  --scenario users-500 --scenario users-1000 --scenario users-2000
```

Each concurrency level means simultaneous full-catalog requests, not users or
individual SPARQL queries. Omit the option to retain each scenario's configured
levels. The override applies only to selected scenarios, sorts/deduplicates the
levels, and is archived in `configuration.json` without editing the source TOML.
It also supports repeated flags (`--concurrency 1 2 --concurrency 4 8`). Append
`--dry-run` to inspect the effective configuration without running workloads.
Preparation is measured per user/layout/reasoner/repetition; the query phase then
sweeps concurrency. `query_rounds` remains the per-scenario configured value.

## Optional adaptive monitoring

Plan from an existing container campaign without changing services:

```bash
continuum-bench --timeout-mode bounded adaptive-monitoring plan --input-dir outputs/container-scale/REPLACE_WITH_RUN_ID --scenario users-2000
```

Execute recovery using its archived workload:

```bash
continuum-bench --timeout-mode bounded --keep-going adaptive-monitoring run --input-dir outputs/container-scale/REPLACE_WITH_RUN_ID --scenario users-2000
```

Replace the run ID with an actual campaign. For a new baseline followed by recovery, omit `--input-dir`. Omit `--scenario` for the full configured campaign. See [Adaptive monitoring](ADAPTIVE_MONITORING.md) for resource constraints, bounded actions, result meanings and limitations.

Generate detailed baseline/adaptation figures after an adaptive run:

```bash
python tools/report_adaptive_comparison.py --input-dir outputs/adaptive-monitoring/REPLACE_WITH_RUN_ID
```

Use the returned adaptive run ID. Images are grouped under `figures/`; source comparisons and interpretation are in `analysis/`. This is reporting only and does not rerun or deploy workers.

Run the adaptive extension across all configured user levels and concurrency 1, 2, 4 and 8, creating a new baseline first:

```bash
continuum-bench --timeout-mode bounded --keep-going adaptive-monitoring run \
  --users 1 50 100 500 1000 2000 --concurrency 1 2 4 8
```

For an existing campaign, use `--input-dir` and omit `--concurrency`; the archived levels are preserved. Detailed figures are now generated automatically. Regenerate them using:

```bash
continuum-bench adaptive-monitoring report --input-dir outputs/adaptive-monitoring/REPLACE_WITH_RUN_ID
```

### Adaptive comparison after the trigger/placement update

Use a new baseline to record worker-attributed failures for all layouts. This runs the selected Docker-only workloads first, then assesses each scenario/layout and performs bounded origin-preserving replica expansion when required:

```bash
source .venv/bin/activate
continuum-bench --timeout-mode bounded container-scale deploy
continuum-bench --timeout-mode bounded --keep-going adaptive-monitoring run \
  --users 1 50 100 500 1000 2000 --concurrency 1 2 4 8
```

`configs/adaptive-monitoring.toml` controls the supervisor. Defaults are any observed failure (`minimum_failures=1`, `max_failure_fraction=0.0`), evaluated separately by reasoner/concurrency, and at most six attempts per scenario/layout, retaining original services and accepting useful extra replicas. An unresolved, unattributed or capacity-blocked case remains explicit. This can require substantially more time than the previous single-attempt configuration. It does not raise request timeouts.

To regenerate figures without executing workloads:

```bash
continuum-bench adaptive-monitoring report --input-dir outputs/adaptive-monitoring/RUN_ID
```

Start with `figures/paired-*-availability.png`, `paired-*-concurrency-benefit.png` and `paired-*-intervention-cost.png`. Missing adaptive trials remain missing. See [adaptive monitoring](ADAPTIVE_MONITORING.md) for deployment scope, constraints and interpretation.

### Validate retained-origin replica execution

After deploying the current images, this bounded mechanism validation runs one user with six original workers and one Edge-2 replica on Fog. It checks actual CPU/request work on both copies, semantic digests and unchanged origin container IDs/PIDs before and after replica cleanup:

```bash
python tools/validate_origin_pool.py
```

This is not a scalability campaign and does not replace the full experiment. Historical `outputs/latest` evidence is unchanged and belongs to the previous relocation strategy.

### After the replica-routing correction

Start a new baseline/campaign using the current configuration (18 query rounds).
Do not reuse the one-round October 26 baseline to claim adaptive improvements.
The adaptive supervisor rejects insufficient coverage before deployment and
stops expansions without completion improvement. Request timeouts remain bounded;
the increased number of rounds increases total campaign duration.
