# Continuous Policy-Driven Monitoring Overhead

This experiment answers a different question from the ABox scalability benchmark: what recurring operational cost is incurred by keeping the semantic monitoring system deployed and executing policy-defined observations at fixed demand-dependent frequencies?

`continuum-bench run` remains the fixed-infrastructure ABox scalability campaign. `continuum-bench monitor` runs this independent time-window experiment. It does not use or alter the scalability benchmark's 18 rounds, data generation, partitioning, RDFS, query catalogue, timeouts, or reports.

## Experimental contract

Each scenario, layout, condition, and repetition performs reset, fresh partitioning, `/prepare`, RDFS, store construction, semantic readiness, and stabilization. Resource measurement starts only after stabilization. The graph is not reset, repartitioned, or reasoned again during the measured window. Processes remain warm while semantic state is rebuilt for every repetition.

The mandatory `deployed_idle` baseline uses the same workers, dataset, closure, limits, durations and sampler with the scheduler disabled. Active conditions differ only by enabling periodic monitoring. Instrumentation is present in both, so active-minus-idle estimates additional monitoring traffic and compute; it is not packet-level VPN telemetry.

Every repetition has one fixed demand level. This is policy-driven periodic monitoring with predefined demand-dependent schedules. It does not choose levels autonomously, migrate containers, create replicas, redistribute fragments, or implement MAPE-K Analyze/Plan.

## Policies, tasks and scheduling

The ontology provides policy identifiers and traceability, but no uniform executable periodic schedule. [monitoring.toml](../configs/monitoring.toml) therefore references existing `policy_id` values and defines intervals and deadlines without restructuring RDF. The configured workload covers recurring operational, connectivity, topology, wellbeing, data, consent, governance, trust and federation observations. [MONITORING_POLICY_COVERAGE.md](MONITORING_POLICY_COVERAGE.md) records the complete query classification, active policy-query traceability and exact schedule.

A `MonitoringTask` contains a stable task ID, a policy ID declared by an explicit `comon:policyIdentifier` literal, one or more required queries, priority, fixed demand level, interval and optional deadline. A cycle is compliant only when every query completes correctly and on time. Its effective deadline is the minimum of the policy deadline, or interval when absent, and the global logical timeout.

The measurement window starts at `t0`; the first cycle of a task with interval `I` occurs at `t0 + I`, never immediately at `t0`. The scheduler then uses monotonic fixed-rate slots `t0 + n × interval`; logical concurrency remains one. Distributed queries reuse concurrent physical fan-out. Simultaneously due tasks are ordered by descending priority, earliest deadline, scheduled time and stable task ID. Slots passed while busy become `missed_schedule` and are never replayed as a catch-up burst.

Each event separates three independent fields: `execution_status` records whether execution completed or failed, `schedule_status` records whether it completed inside its temporal window or was missed, and `observation_outcome` records the semantic observation. Detecting a condition is a valid observation, not a semantic failure. `semantic_failure` is reserved for an actual query-contract or semantic execution error. Compliance is the number of cycles with `execution_status=completed` and `schedule_status=completed_on_time` divided by all scheduled cycles, including missed slots.

`observation_outcome` follows the query contract. A completed `violation` query produces `condition_detected` only when it returns violations, otherwise `condition_not_detected`. Completed report, inventory, dashboard and review queries produce `observation_available`; returned rows do not imply an anomaly. ASK queries compare their Boolean answer with the manifest's `true` or `false` expectation and produce `expected_boolean_observed` or `unexpected_boolean_observed` (or `boolean_true`/`boolean_false` when no Boolean expectation exists). No query IDs are hardcoded in this interpretation.

After a logical timeout, the runner waits for every participating worker to report `idle=true`, `active_requests=0` and `queue_depth=0`. If a worker does not become idle within `recovery_idle_timeout_seconds`, its container is restarted, its RDF fragment is prepared again, and its dataset and closure identities are checked before scheduling resumes. A failed recovery halts the scheduler and marks the repetition `recovery_failed`; it is never reported as completed. Evidence records `failure_reason`, failed task, query and hosts, `recovery_count`, `recovery_seconds`, `worker_restart_count` and the idle, restart and preparation details.

Monotonic timestamps remain authoritative for deadlines, offsets, lag and durations. Every raw scheduler event also contains `scheduled_at_utc`, `actual_start_utc` and `actual_end_utc` for audit, plus offsets from the measurement-window start. UTC wall-clock values are never used to decide compliance.

## Commands

```bash
source .venv/bin/activate
continuum-bench monitor --config configs/monitoring.toml
```

Select fixed levels when required:

```bash
continuum-bench monitor --config configs/monitoring.toml --demand-level normal
continuum-bench monitor --config configs/monitoring.toml --demand-level high
```

Regenerate its independent report:

```bash
continuum-bench monitor-report outputs/monitoring-<run-id>
```

The example configuration selects `users-1000`, `distributed`, four demand levels, three repetitions, 30 seconds of stabilization and 300 seconds of measurement. Scenarios, layouts, levels, durations, recovery timeouts and tasks are configurable. Task intervals and deadlines are experimental schedule parameters associated with existing policies; they are not temporal requirements asserted by the ontology. `minimum_recommended_cycles_per_task` emits a warning when `measurement_seconds / task_interval` is too small for a configured task; it does not reject short development runs or impose a fixed campaign duration.

## Evidence and metrics

Runs are stored under `outputs/monitoring-<run-id>/`. Every repetition preserves its result, scheduler/task/query JSONL, resource samples, phase events, health before/after and container state. The manifest records source state and configuration, ontology, query, topology and policy digests plus worker build identities. Dataset and closure identities remain in preparation evidence. `measurement_requested_seconds` stores the configured window and `measurement_actual_seconds` stores its monotonic elapsed time. A recovery failure therefore preserves the shorter measured window and all evidence collected before the abort.

`summary/` contains all repetition evidence plus separate `completed_repetitions.csv`, `partial_repetitions.csv` and `failures.csv` tables. Hourly CPU, network, query and physical-request rates use `measurement_actual_seconds`; partial rates are explicitly labelled and retained for diagnosis. Only completed repetitions enter `summary.csv`, medians, idle-versus-active comparisons and figures, so aborted windows cannot silently alter the primary overhead statistics. Task-policy rows separately count available observations, true detected conditions, absent conditions and expected or unexpected Boolean answers.

Per-host rows retain each worker's resource metrics. Repetition and aggregate rows distinguish `worker_memory_*` (the distribution of individual worker samples) from `infrastructure_memory_*`, calculated only when every worker has memory telemetry at the same sampling instant. Missing telemetry remains missing; it is never converted to zero. The report records total and observed host counts for CPU, memory and network, and labels infrastructure-wide CPU and network totals as observed totals when host coverage is incomplete.

Seven monitoring-specific matrix figures remain separate from scalability figures. They cover aggregate overhead, executed workload, per-node CPU, per-node memory, per-node network traffic, temporal quality and cycles by task/policy. Every cell is annotated with its numeric value. `N/A` identifies unavailable or incomplete per-node telemetry. Matrices that combine different units use row-normalized colour only for visual comparison while preserving raw values in the annotations; colour must therefore be interpreted within a row, not between metrics.

Future work may use observations in Analyze and Plan to select a demand regime dynamically before Execute applies it. That autonomous loop is outside this controlled experiment.
