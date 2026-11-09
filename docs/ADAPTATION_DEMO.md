# Controlled Policy-Driven Adaptation Demonstration

This is the third independent experiment in the repository. It connects scalability-induced load, policy-driven monitoring and a controlled capacity-expansion action without changing the ABox scalability benchmark or continuous-monitoring overhead experiment.

> This experiment is a controlled demonstration of how policy-driven monitoring could feed a MAPE-K adaptation loop. Monitor and post-adaptation verification use real measurements. Analyze and Plan are deterministic simulated stages, while Execute is explicitly scripted/manual. The experiment therefore does not claim autonomous self-adaptation.

## Stage contract

| Stage | Mode | Responsibility |
|---|---|---|
| Monitor | `measured` | Prepare the configured ABox, replay the scalability query catalog while periodic policy monitoring observes the same workers, and record semantic, temporal and resource evidence. |
| Trigger evaluation | `measured_threshold_evaluation` | Evaluate configured experimental thresholds over the measured operational cycles. |
| Analyze | `simulated_rule_based` | Convert a satisfied trigger into `additional_capacity_required`. |
| Plan | `simulated_rule_based` | Filter real physical candidates, apply configured governance boundaries and select a target deterministically. |
| Execute | `scripted_manual` | Deploy and prepare one additional read-only semantic worker after an explicit researcher command. |
| Verification | `measured` | Repeat the identical monitoring workload and collect before/after evidence. |

The experiment does not implement autonomous Analyze or Plan, automatic execution, optimization, machine learning, policy synthesis, demand-level transitions, multi-writer replication or general-purpose orchestration.

## Experimental flow

```text
configured scalability point and ABox
  → scalability query-catalog load and policy monitoring in parallel
  → measured degradation trigger
  → simulated rule-based Analyze
  → simulated rule-based Plan
  → explicit scripted replica deployment
  → semantic readiness
  → deterministic read routing
  → real verification with the same workload
```

The default load is `users-10000`, selected because the scalability campaign showed sustained edge pressure at this scale. The application thread executes the same ordered catalog and 18 rounds used by the scalability experiment while the monitoring scheduler runs independently. A run can use any scenario declared by the benchmark. Useful independent checkpoints are `users-1000` (control), `users-4000` (onset), `users-10000` (sustained load) and `users-14000` (high pressure). Change only `scenario` in `configs/adaptation.toml` between campaigns. User count is an input scale and never activates adaptation directly.

## Policies and queries

The application load uses every query in `queries/manifest.json`, in its declared order, with the same distributed selection and merge rules as the scalability experiment. If the baseline reaches a query timeout, it stops at that point as the scalability repetition does. Verification then replays the exact baseline `(round, query)` sequence, including the final timed-out query, so that a successful adaptation cannot receive extra work merely because it no longer times out. The Monitor stage simultaneously uses the periodic workload from [`configs/monitoring.toml`](../configs/monitoring.toml). The trigger is scoped to `operational-node-state`, which executes:

- `BASE-Q07`: node states and operational metrics;
- `BASE-Q08`: saturated, unavailable or disconnected nodes;
- `BASE-Q26`: ASK whether a saturated node exists.

These queries are directly associated with `P-NODE-01`. The trigger uses `P-ADAPT-03`, whose overload-driven statement is the closest existing policy to the measured degradation-to-capacity rule. `BASE-Q12` records scenario context for `P-ADAPT-01`, but the experiment does not claim full enforcement of that policy because it does not yet measure every required cost, energy and continuity dimension. Plan records `BASE-Q19` and `EXT-Q42` as semantic evidence for the hard filters and trust-aware ranking represented by `P-NODE-02` and `P-NODE-05`.

The worker protocol exposes result counts and canonical result digests, not SPARQL bindings. Plan therefore combines this semantic evidence with a real physical candidate inventory obtained from the deployed hosts. Candidate IDs are never inferred from a result digest.

## Trigger definition

Thresholds in [`configs/adaptation.toml`](../configs/adaptation.toml) are **experimental adaptation thresholds**, not temporal or performance requirements asserted by the ontology. The configured conditions are:

- CPU p95 on one of `trigger_resource_hosts` reaches `cpu_p95_percent` and either mean CPU reaches `cpu_mean_percent` or the fraction of saturated samples reaches `cpu_saturation_fraction`;
- trigger-task cycle latency or its p95 reaches `logical_latency_p95_ms`;
- monitoring compliance falls below `monitoring_compliance_min`;
- logical timeouts reach `timeouts`;
- the semantic observation reports saturation.

The trigger compares the configured Edge workers and selects the one with the highest sustained p95, saturation fraction and mean CPU as the possible replica source. CPU from unrelated nodes is excluded. `replica_source` is used only as a deterministic fallback when no candidate Edge has usable telemetry. Each operational cycle records the selected source-node mean, p95, peak, saturated-sample fraction and sample count. CPU persistence is evaluated over the complete source-node sample series: p95, mean or saturated-sample fraction and a minimum sample count must agree. Latency, timeout, semantic and compliance degradation retain the `consecutive_trigger_cycles` requirement. This distinction prevents an isolated CPU spike from activating adaptation without rejecting sustained load merely because periodic query phases contain short CPU troughs. The trigger evidence records the persistence basis, every candidate Edge summary, every evaluated cycle, conditions, measured values, thresholds and policy/query IDs. A non-satisfied trigger produces `no_adaptation_required`; it does not deploy a replica.

## Simulated Analyze and Plan

Analyze implements one deterministic rule:

```text
persistent measured trigger satisfied
  → additional_capacity_required
otherwise
  → no_adaptation_required
```

Plan answers what to deploy and where. The only supported action is `deploy_read_only_replica`. Candidate inspection records:

- baseline worker readiness and idle state;
- physical connectivity;
- node tier and authority;
- available host memory and one-minute load;
- availability of the configured replica port;
- availability of the exact worker image;
- mean, p95 and peak CPU measured on that node during the baseline workload.

`P-NODE-02` is represented by hard eligibility filters, including minimum available memory, maximum one-minute host load per CPU and rejection of nodes that were saturated during the observed workload. `P-NODE-05` is represented by deterministic ranking after those filters. These capacity cutoffs are experimental planning parameters. `allowed_target_tiers` and `excluded_targets` are explicit experimental governance boundaries. The default permits cloud, fog, mist and edge and excludes no host. `preferred_target = "mist"` exercises a nearby continuum tier but can only win when it is connected, semantically ready, sufficiently provisioned and unsaturated. Otherwise Plan selects the eligible node with most residual memory, breaking ties by stable host ID, or returns `planning_failed` when fallback is disabled or no candidate remains.

Plan stores `eligible_candidates`, `selected_target`, rejected candidates with reasons, physical evidence, semantic query evidence and the selection rule. The replica source and physical target are distinct concepts: the source identifies the partition fragment being replicated, while the target identifies the machine hosting the additional container.

## Scripted Execute and replica readiness

Execute occurs only after the researcher explicitly runs the execute command. It starts one additional container on the selected physical target with the configured default limits of 1 CPU and 1536 MiB RAM. The container receives the source participant's exact RDF fragment and builds its own RDFS closure and Oxigraph store.

Before routing, Execute verifies:

- worker protocol and semantic artifact identities;
- idle state;
- dataset digest;
- closure digest;
- semantic readiness.

It records container start, transfer, reasoning, store-load and total replica-ready times. The replica is read-only at the experiment level: routing sends only SPARQL queries after preparation. The underlying worker still retains its administrative `/prepare` and `/reset` endpoints, so this is not an access-control guarantee.

## Post-adaptation routing

The baseline topology remains the source of partition participation. The replica is registered as an equivalent read target for only its source participant. A deterministic round-robin alternates successive source selections between the original participant and its replica. It never adds the replica as another distributed partition and therefore does not change fan-out size or merge semantics. The original source remains active and continues to answer alternating requests. The action expands read capacity across the continuum; it does not migrate all work to Cloud or stop computation at the saturated Edge node.

Physical-query evidence labels every execution as `partition_participant` or `read_only_replica`. Logical deadlines, concurrent distributed fan-out and the existing merge strategies remain unchanged. Replica timeout recovery verifies that the replica returns to the exact prepared dataset and closure; a failed recovery halts verification rather than silently routing stale state.

## Commands

Prepare the normal six baseline workers first using the deployment instructions. Then run each stage independently:

```bash
source .venv/bin/activate

continuum-bench adaptation observe --config configs/adaptation.toml

continuum-bench adaptation analyze \
  --config configs/adaptation.toml \
  outputs/adaptation-<run-id>

continuum-bench adaptation plan \
  --config configs/adaptation.toml \
  outputs/adaptation-<run-id>

# This is the explicit researcher-authorized infrastructure change.
continuum-bench adaptation execute \
  --config configs/adaptation.toml \
  outputs/adaptation-<run-id>

continuum-bench adaptation verify \
  --config configs/adaptation.toml \
  outputs/adaptation-<run-id>

continuum-bench adaptation report outputs/adaptation-<run-id>
```

If Monitor does not satisfy the configured trigger, Analyze and Plan record `no_action`. Execute then records `skipped_no_action` without changing the infrastructure, Verification records that there is no change to verify, and Report produces a decision report containing the baseline measurements and empty after/delta fields. The complete command sequence therefore terminates successfully for both the adaptation and no-action branches. The phases consume the evidence written by the previous phase, so the run can still be inspected or stopped at every boundary.

## Evidence layout

```text
outputs/adaptation-<run-id>/
├── manifest.json
├── configuration.toml
├── benchmark-configuration.toml
├── monitoring-configuration.toml
├── topology.json
├── trigger.json
├── analysis.json
├── plan.json
├── before/
│   ├── dataset.nt
│   ├── fragments/
│   ├── expected-semantics.json
│   ├── workload.json
│   ├── scheduler_events.jsonl
│   ├── application_load.json
│   ├── application_execution_plan.json
│   ├── application_logical_queries.jsonl
│   ├── application_physical_queries.jsonl
│   ├── monitoring_logical_queries.jsonl
│   ├── monitoring_physical_queries.jsonl
│   ├── logical_queries.jsonl
│   ├── physical_queries.jsonl
│   ├── resource_samples.jsonl
│   └── result.json
├── execute/result.json
├── verification/result.json       # no-action branch
├── after/
│   ├── workload.json
│   ├── scheduler_events.jsonl
│   ├── application_load.json
│   ├── application_execution_plan.json
│   ├── application_logical_queries.jsonl
│   ├── application_physical_queries.jsonl
│   ├── monitoring_logical_queries.jsonl
│   ├── monitoring_physical_queries.jsonl
│   ├── logical_queries.jsonl
│   ├── physical_queries.jsonl
│   ├── resource_samples.jsonl
│   └── result.json
└── comparison/
    ├── summary.json
    ├── metrics.csv
    ├── node-metrics.csv
    ├── figures/
    │   ├── 01_trigger_evidence_matrix.png
    │   ├── 02_node_cpu_before_after.png
    │   ├── 03_node_memory_before_after.png
    │   └── 04_application_before_after.png
    └── report.md
```

## Before/after metrics

The report compares application-query latency p50/p95/p99, throughput, duration, completed queries and timeouts, monitoring latency and compliance, schedule lag, CPU mean/p95/peak, memory, network deltas and physical executions. It also reports container start, transfer, reasoning, store-load and replica-ready time. Per-host CPU, memory and network evidence includes the replica separately. Four 300-dpi PNG matrices show the trigger cycles, per-node CPU, per-node memory and application workload before/after; missing telemetry is labelled `N/A` rather than zero. Long trigger matrices use row-normalized colour for readability, while `trigger.json` retains every exact cycle value.

Before and after must have the same scenario, ABox, ontology, layout, task set, demand level, schedule, measurement duration, baseline worker limits and offered application-query sequence. Verification fails when either the serialized workload identities or the ordered `(round, query)` plans differ. Completed query result digests are compared by query ID as a semantic-equivalence check.

A ready replica is an execution success, not proof of a performance improvement. The measured deltas may show improvement, no material change or degradation. A no-action run has no post-adaptation metrics because no adaptation occurred; its baseline data remain valid evidence of the decision. No claim should be made before a physical campaign completes.

## Remaining limitations

- Analyze and Plan are deterministic simulations and require thresholds selected by the researcher.
- Candidate semantics and physical inventory are recorded together, but query bindings are not exposed by the current worker protocol.
- The read-only role is enforced by experiment routing, not by removing administrative worker endpoints.
- `P-ADAPT-01` is retained as semantic scenario context; its complete multi-criteria decision contract is not enforced because cost, energy and service-continuity evidence is incomplete.
- One additional replica and one source participant are supported per run.
- Round-robin is deterministic and reproducible but is not an adaptive load balancer.
- Application catalog replay is concurrent with policy monitoring, but Analyze and Plan do not optimize placement dynamically while the window is running.
- No state synchronization occurs after preparation; the comparison assumes the immutable benchmark ABox.
- The experiment does not remove the replica automatically. Its exact container name is stored in `execute/result.json` for deliberate lifecycle management.
