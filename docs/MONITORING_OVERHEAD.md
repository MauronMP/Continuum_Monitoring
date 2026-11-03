# Continuous Policy-Driven Monitoring Overhead

This experiment answers a different question from the ABox scalability benchmark: what recurring operational cost is incurred by keeping the semantic monitoring system deployed and executing policy-defined observations at fixed demand-dependent frequencies?

`continuum-bench run` remains the fixed-infrastructure ABox scalability campaign. `continuum-bench monitor` runs this independent time-window experiment. It does not use or alter the scalability benchmark's 18 rounds, data generation, partitioning, RDFS, query catalogue, timeouts, or reports.

## Experimental contract

Each scenario, layout, condition, and repetition performs reset, fresh partitioning, `/prepare`, RDFS, store construction, semantic readiness, and stabilization. Resource measurement starts only after stabilization. The graph is not reset, repartitioned, or reasoned again during the measured window. Processes remain warm while semantic state is rebuilt for every repetition.

The mandatory `deployed_idle` baseline uses the same workers, dataset, closure, limits, durations and sampler with the scheduler disabled. Active conditions differ only by enabling periodic monitoring. Instrumentation is present in both, so active-minus-idle estimates additional monitoring traffic and compute; it is not packet-level VPN telemetry.

Every repetition has one fixed demand level. This is policy-driven periodic monitoring with predefined demand-dependent schedules. It does not choose levels autonomously, migrate containers, create replicas, redistribute fragments, or implement MAPE-K Analyze/Plan.

## Policies, tasks and scheduling

The ontology provides policy identifiers and traceability, but no uniform executable periodic schedule. [monitoring.toml](../configs/monitoring.toml) therefore references existing `policy_id` values and defines intervals and deadlines without restructuring RDF.

A `MonitoringTask` contains a stable task ID, policy ID, one or more required queries, priority, fixed demand level, interval and optional deadline. A cycle is compliant only when every query completes correctly and on time. Its effective deadline is the minimum of the policy deadline, or interval when absent, and the global logical timeout.

The scheduler uses monotonic fixed-rate slots `t0 + n × interval`; logical concurrency remains one. Distributed queries reuse concurrent physical fan-out. Simultaneously due tasks are ordered by descending priority, earliest deadline, scheduled time and stable task ID. Slots passed while busy become `missed_schedule` and are never replayed as a catch-up burst.

Compliance is on-time cycles divided by all scheduled cycles, including missed slots. Evidence distinguishes `completed_on_time`, `completed_late`, `logical_timeout`, `physical_failure`, `semantic_failure` and `missed_schedule`, and records schedule lag, utilization and maximum pending tasks.

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

The example configuration selects `users-1000`, `distributed`, four demand levels, three repetitions, 30 seconds of stabilization and 300 seconds of measurement. Scenarios, layouts, levels, durations and tasks are configurable.

## Evidence and metrics

Runs are stored under `outputs/monitoring-<run-id>/`. Every repetition preserves its result, scheduler/task/query JSONL, resource samples, phase events, health before/after and container state. The manifest records source state and configuration, ontology, query, topology and policy digests plus worker build identities. Dataset and closure identities remain in preparation evidence.

`summary/` contains repetition, host, task/policy and idle-versus-active CSV files. It reports compliance, scheduled/on-time/late/missed cycles, failures, lag, scheduler utilization, pending tasks, logical latency, CPU, RAM, network and hourly cycle/query/request rates. Seven monitoring-specific figures remain separate from scalability figures.

Future work may use observations in Analyze and Plan to select a demand regime dynamically before Execute applies it. That autonomous loop is outside this controlled experiment.
