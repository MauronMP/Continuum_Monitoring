# Monitoring Policy Coverage

This document defines the configured **broad policy-driven periodic monitoring workload**. It is compiled from the maintained query catalog, the ontology policy identifiers and `configs/monitoring.toml`. The counts stored in experiment manifests describe this workload; they are not a formal percentage of semantic coverage.

## Table A — Query classification

Every catalog query is classified by its execution purpose. A query classified as `periodic_monitoring` can still be excluded when another selected query set already observes the same requirement or when adding it would broaden load without adding a distinct control.

| Policy | Domain | Query | Classification | Included | Reason |
|---|---|---|---|---|---|
| P-CONS-01, P-DATA-02 | Identity and consent | `BASE-Q01` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-OPS-02, P-OPS-03 | Topology | `BASE-Q02` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-INT-02 | Wellbeing | `BASE-Q03` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-FL-08, P-MODEL-01 | Decision | `BASE-Q04` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-INT-01 | Wellbeing | `BASE-Q05` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-CONS-05 | Identity and consent | `BASE-Q06` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-NODE-01, P-NODE-03, P-OPS-05 | Observability | `BASE-Q07` | `periodic_monitoring` | yes | Recurring node health, saturation, availability and connectivity control. |
| P-NODE-01, P-NODE-02 | Observability | `BASE-Q08` | `periodic_monitoring` | yes | Recurring node health, saturation, availability and connectivity control. |
| P-GOV-05, P-OPS-05 | Wellbeing | `BASE-Q09` | `periodic_monitoring` | yes | Recurring temporal integrity check for wellbeing observations. |
| P-DATA-04, P-DATA-06, P-DATA-07 | Observability | `BASE-Q10` | `periodic_monitoring` | yes | Recurring device-state and transmission-eligibility control. |
| P-VAL-07 | Wellbeing | `BASE-Q11` | `benchmark_only` | no | Scenario or validation evidence; executed by benchmark/validation workflows. |
| P-ADAPT-01, P-NODE-02 | Adaptation | `BASE-Q12` | `benchmark_only` | no | Scenario or validation evidence; executed by benchmark/validation workflows. |
| P-ADAPT-05, P-ADAPT-06 | Adaptation | `BASE-Q13` | `benchmark_only` | no | Scenario or validation evidence; executed by benchmark/validation workflows. |
| P-ADAPT-02, P-AUD-01, P-AUD-05 | Delegation | `BASE-Q14` | `benchmark_only` | no | Scenario or validation evidence; executed by benchmark/validation workflows. |
| P-CONS-01, P-CONS-04, P-MODEL-06 | Identity and consent | `BASE-Q15` | `benchmark_only` | no | Scenario or validation evidence; executed by benchmark/validation workflows. |
| P-FL-01, P-FL-03, P-FL-05, P-FL-07 | Federation | `BASE-Q16` | `benchmark_only` | no | Scenario or validation evidence; executed by benchmark/validation workflows. |
| P-ZONE-02, P-DATA-07 | Context and zones | `BASE-Q17` | `benchmark_only` | no | Scenario or validation evidence; executed by benchmark/validation workflows. |
| P-ZONE-01, P-DATA-01 | Context and zones | `BASE-Q18` | `benchmark_only` | no | Scenario or validation evidence; executed by benchmark/validation workflows. |
| P-NODE-02, P-NODE-05 | Decision | `BASE-Q19` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-CONS-02, P-CONS-03 | Identity and consent | `BASE-Q20` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-AUD-06, P-MODEL-05 | Decision | `BASE-Q21` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-ADAPT-06, P-FL-08 | Adaptation | `BASE-Q22` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-NODE-02 | Topology | `BASE-Q23` | `periodic_monitoring` | yes | Recurring proximity signal used to observe topology risk without executing adaptation. |
| P-FL-02, P-FL-04, P-FL-07 | Federation | `BASE-Q24` | `event_or_on_demand` | no | Evaluated when delegation or federation activity occurs; no general periodic requirement selected. |
| P-CONS-04, P-FL-02 | Identity and consent | `BASE-Q25` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-NODE-01 | Observability | `BASE-Q26` | `periodic_monitoring` | yes | Recurring node health, saturation, availability and connectivity control. |
| P-ADAPT-06 | Adaptation | `BASE-Q27` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-CONS-04, P-DATA-04 | Identity and consent | `BASE-Q28` | `periodic_monitoring` | no | Valid periodic candidate, omitted to avoid overlapping controls in the bounded workload. |
| P-OPS-02 | Topology | `BASE-Q29` | `periodic_monitoring` | no | Valid periodic candidate, omitted to avoid overlapping controls in the bounded workload. |
| P-FL-01 | Federation | `BASE-Q30` | `event_or_on_demand` | no | Evaluated when delegation or federation activity occurs; no general periodic requirement selected. |
| P-CONS-01 | Identity and consent | `BASE-Q31` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-MODEL-01 | Decision | `BASE-Q32` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-OPS-05 | Observability | `BASE-Q33` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-ZONE-01 | Topology | `BASE-Q34` | `inventory_or_administration` | no | Topology inventory/report used for administration; recurring proximity has a dedicated task. |
| P-AUD-05, P-AUD-07 | Delegation | `BASE-Q35` | `event_or_on_demand` | no | Evaluated when delegation or federation activity occurs; no general periodic requirement selected. |
| P-VAL-01, P-VAL-04 | Semantic schema | `EXT-Q01` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-VAL-06 | Semantic schema | `EXT-Q02` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-GOV-01, P-GOV-04 | Policy governance | `EXT-Q03` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-VAL-06 | Policy governance | `EXT-Q04` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-VAL-07 | Semantic schema | `EXT-Q05` | `benchmark_only` | no | Scenario or validation evidence; executed by benchmark/validation workflows. |
| P-GOV-01 | Semantic schema | `EXT-Q06` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-GOV-03 | Policy governance | `EXT-Q07` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-VAL-06 | Policy governance | `EXT-Q08` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-VAL-06 | Policy governance | `EXT-Q09` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-GOV-01, P-GOV-04 | Policy governance | `EXT-Q10` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-CONS-01, P-CONS-04 | Identity and consent | `EXT-Q11` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-CONS-02, P-CONS-03, P-GOV-02 | Identity and consent | `EXT-Q12` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-CONS-01 | Identity and consent | `EXT-Q13` | `periodic_monitoring` | yes | Recurring consent completeness and active-range integrity control. |
| P-CONS-02, P-CONS-03 | Identity and consent | `EXT-Q14` | `periodic_monitoring` | no | Valid periodic candidate, omitted to avoid overlapping controls in the bounded workload. |
| P-CONS-02 | Identity and consent | `EXT-Q15` | `periodic_monitoring` | no | Valid periodic candidate, omitted to avoid overlapping controls in the bounded workload. |
| P-CONS-01, P-CONS-04 | Identity and consent | `EXT-Q16` | `periodic_monitoring` | yes | Recurring consent completeness and active-range integrity control. |
| P-CONS-04, P-GOV-03 | Identity and consent | `EXT-Q17` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-CONS-04 | Identity and consent | `EXT-Q18` | `periodic_monitoring` | no | Valid periodic candidate, omitted to avoid overlapping controls in the bounded workload. |
| P-CONS-04, P-GOV-03 | Identity and consent | `EXT-Q19` | `periodic_monitoring` | no | Valid periodic candidate, omitted to avoid overlapping controls in the bounded workload. |
| P-CONS-04, P-AUD-06 | Identity and consent | `EXT-Q20` | `periodic_monitoring` | no | Valid periodic candidate, omitted to avoid overlapping controls in the bounded workload. |
| P-CONS-05 | Identity and consent | `EXT-Q21` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-DATA-01, P-ZONE-01 | Security and identity | `EXT-Q22` | `periodic_monitoring` | no | Valid periodic candidate, omitted to avoid overlapping controls in the bounded workload. |
| P-DATA-02, P-DATA-03, P-DATA-10 | Data lifecycle | `EXT-Q23` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-DATA-10 | Data lifecycle | `EXT-Q24` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-DATA-10 | Data lifecycle | `EXT-Q25` | `periodic_monitoring` | no | Valid periodic candidate, omitted to avoid overlapping controls in the bounded workload. |
| P-DATA-02 | Security and identity | `EXT-Q26` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-DATA-02 | Security and identity | `EXT-Q27` | `periodic_monitoring` | no | Valid periodic candidate, omitted to avoid overlapping controls in the bounded workload. |
| P-DATA-02 | Security and identity | `EXT-Q28` | `periodic_monitoring` | no | Valid periodic candidate, omitted to avoid overlapping controls in the bounded workload. |
| P-DATA-03 | Security and identity | `EXT-Q29` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-DATA-03 | Security and identity | `EXT-Q30` | `periodic_monitoring` | no | Valid periodic candidate, omitted to avoid overlapping controls in the bounded workload. |
| P-DATA-05, P-DATA-07 | Data lifecycle | `EXT-Q31` | `periodic_monitoring` | yes | Recurring buffer capacity and retention compliance control. |
| P-DATA-03, P-DATA-05 | Data lifecycle | `EXT-Q32` | `periodic_monitoring` | yes | Recurring buffer capacity and retention compliance control. |
| P-DATA-08 | Data lifecycle | `EXT-Q33` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-DATA-08, P-ADAPT-08 | Data lifecycle | `EXT-Q34` | `periodic_monitoring` | no | Valid periodic candidate, omitted to avoid overlapping controls in the bounded workload. |
| P-DATA-09 | Data lifecycle | `EXT-Q35` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-ZONE-01 | Context and zones | `EXT-Q36` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-ZONE-01, P-GOV-03, P-ZONE-04 | Context and zones | `EXT-Q37` | `periodic_monitoring` | yes | Recurring restricted-data confinement control. |
| P-ZONE-02, P-DATA-07 | Context and zones | `EXT-Q38` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-ZONE-03, P-CONS-04 | Context and zones | `EXT-Q39` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-NODE-03, P-NODE-04 | Trust | `EXT-Q40` | `periodic_monitoring` | yes | Recurring trust-evidence freshness and completeness control. |
| P-NODE-01, P-NODE-02 | Trust | `EXT-Q41` | `adaptation_or_planning` | no | Trust analysis is consumed by decisions; the selected recurring evidence checks cover Monitor. |
| P-NODE-02, P-NODE-05, P-MODEL-03 | Trust | `EXT-Q42` | `adaptation_or_planning` | no | Trust analysis is consumed by decisions; the selected recurring evidence checks cover Monitor. |
| P-NODE-03 | Trust | `EXT-Q43` | `periodic_monitoring` | yes | Recurring trust-evidence freshness and completeness control. |
| P-MODEL-03, P-NODE-05 | Trust | `EXT-Q44` | `adaptation_or_planning` | no | Trust analysis is consumed by decisions; the selected recurring evidence checks cover Monitor. |
| P-ADAPT-04, P-ADAPT-07 | Trust | `EXT-Q45` | `adaptation_or_planning` | no | Trust analysis is consumed by decisions; the selected recurring evidence checks cover Monitor. |
| P-MODEL-01, P-MODEL-05, P-AUD-06 | Decision | `EXT-Q46` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-AUD-06 | Decision | `EXT-Q47` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-MODEL-02, P-MODEL-03 | Decision | `EXT-Q48` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-MODEL-04 | Decision | `EXT-Q49` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-MODEL-04 | Decision | `EXT-Q50` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-MODEL-05 | Decision | `EXT-Q51` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-MODEL-05 | Decision | `EXT-Q52` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-MODEL-05 | Decision | `EXT-Q53` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-MODEL-08, P-OPS-05 | Decision | `EXT-Q54` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-MODEL-08 | Decision | `EXT-Q55` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-MODEL-07, P-ZONE-01, P-CONS-04 | Decision | `EXT-Q56` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-FL-08 | Decision | `EXT-Q57` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-FL-08 | Decision | `EXT-Q58` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-ADAPT-06, P-AUD-06 | Adaptation | `EXT-Q59` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-ADAPT-05 | Adaptation | `EXT-Q60` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-ADAPT-05 | Adaptation | `EXT-Q61` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-ADAPT-02, P-ADAPT-03, P-ADAPT-06 | Adaptation | `EXT-Q62` | `adaptation_or_planning` | no | Supports Analyze/Plan or action selection rather than recurring Monitor execution. |
| P-AUD-01, P-AUD-02, P-AUD-03 | Delegation | `EXT-Q63` | `event_or_on_demand` | no | Evaluated when delegation or federation activity occurs; no general periodic requirement selected. |
| P-AUD-02 | Delegation | `EXT-Q64` | `event_or_on_demand` | no | Evaluated when delegation or federation activity occurs; no general periodic requirement selected. |
| P-AUD-04, P-OPS-01 | Delegation | `EXT-Q65` | `event_or_on_demand` | no | Evaluated when delegation or federation activity occurs; no general periodic requirement selected. |
| P-FL-01, P-FL-06, P-FL-07, P-CONS-06 | Federation | `EXT-Q66` | `event_or_on_demand` | no | Evaluated when delegation or federation activity occurs; no general periodic requirement selected. |
| P-FL-02, P-FL-03 | Federation | `EXT-Q67` | `periodic_monitoring` | yes | Recurring authorization and privacy safeguards for federated exchanges. |
| P-FL-03, P-FL-05 | Federation | `EXT-Q68` | `periodic_monitoring` | yes | Recurring authorization and privacy safeguards for federated exchanges. |
| P-FL-04 | Federation | `EXT-Q69` | `event_or_on_demand` | no | Evaluated when delegation or federation activity occurs; no general periodic requirement selected. |
| P-AUD-07 | Audit and temporal | `EXT-Q70` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-AUD-06 | Audit and temporal | `EXT-Q71` | `periodic_monitoring` | no | Valid periodic candidate, omitted to avoid overlapping controls in the bounded workload. |
| P-AUD-05, P-GOV-02 | Audit and temporal | `EXT-Q72` | `periodic_monitoring` | yes | Recurring audit accountability and traceability control. |
| P-GOV-05, P-AUD-02 | Audit and temporal | `EXT-Q73` | `event_or_on_demand` | no | Report or review query run when its triggering event or investigation requires it. |
| P-GOV-05 | Audit and temporal | `EXT-Q74` | `periodic_monitoring` | yes | Recurring temporal integrity check for wellbeing observations. |
| P-OPS-01, P-VAL-03 | Validation | `EXT-Q76` | `benchmark_only` | no | Scenario or validation evidence; executed by benchmark/validation workflows. |
| P-VAL-03, P-VAL-04, P-VAL-07 | Validation | `EXT-Q77` | `benchmark_only` | no | Scenario or validation evidence; executed by benchmark/validation workflows. |
| P-GOV-03 | Policy governance | `EXT-Q78` | `inventory_or_administration` | no | Static inventory, schema, dashboard or governance administration check. |
| P-GOV-03 | Policy governance | `EXT-Q79` | `periodic_monitoring` | yes | Low-frequency governance consistency control. |

### Policies without a direct query contract

Seven ontology policies are absent from every query's `# Policies` declaration. They are not assigned to a periodic task because doing so would invent the policy-query traceability that this workload requires.

| Policy | Domain | Classification | Included | Reason |
|---|---|---|---|---|
| `P-MODEL-09` | Decision | `adaptation_or_planning` | no | Recomputes a monitoring plan for a supplied context; live reselection is outside Monitor. |
| `P-NODE-06` | Decision | `adaptation_or_planning` | no | Defines the empty-selection planning boundary when no resource tier is eligible. |
| `P-OPS-04` | Experiment execution | `benchmark_only` | no | Defines explicit failure outcomes and keep-going behavior rather than a query observation. |
| `P-OPS-06` | Recovery | `adaptation_or_planning` | no | Evaluates a supplied recovery context and produces a new plan; physical synchronization is outside this release. |
| `P-VAL-02` | Validation | `benchmark_only` | no | Validates query kinds and interpretation expectations during catalogue loading. |
| `P-VAL-05` | Validation | `benchmark_only` | no | Governs release checks, fingerprints and migration compatibility. |
| `P-VAL-08` | Validation | `benchmark_only` | no | Governs validation-campaign coverage and artifact-version evidence. |

## Table B — Active periodic workload

Intervals and deadlines are expressed in seconds in LOW / NORMAL / HIGH / CRITICAL order. The values are experimental monitoring schedule parameters associated with existing policies; the ontology does not assert them as normative temporal requirements.

| MonitoringTask | Policy | Domain | Queries | Intervals (L/N/H/C) | Deadlines (L/N/H/C) |
|---|---|---|---|---:|---:|
| `operational-node-state` | `P-NODE-01` | Observability | `BASE-Q07`, `BASE-Q08`, `BASE-Q26` | 60/30/10/5 | 45/20/8/5 |
| `device-transmission-state` | `P-DATA-06` | Observability | `BASE-Q10` | 120/60/30/15 | 60/30/20/10 |
| `wellbeing-temporal-state` | `P-GOV-05` | Wellbeing, Audit and temporal | `BASE-Q09`, `EXT-Q74` | 180/90/45/20 | 90/45/30/15 |
| `topology-proximity-signal` | `P-NODE-02` | Topology | `BASE-Q23` | 240/120/60/30 | 120/60/30/20 |
| `buffer-retention-state` | `P-DATA-05` | Data lifecycle | `EXT-Q31`, `EXT-Q32` | 180/120/60/30 | 90/60/30/20 |
| `consent-integrity` | `P-CONS-01` | Identity and consent | `EXT-Q13`, `EXT-Q16` | 240/180/90/45 | 120/90/45/30 |
| `restricted-zone-confinement` | `P-ZONE-01` | Context and zones | `EXT-Q37` | 180/120/60/30 | 90/60/30/20 |
| `audit-accountability` | `P-GOV-02` | Audit and temporal | `EXT-Q72` | 240/180/90/45 | 120/90/45/30 |
| `trust-evidence` | `P-NODE-03` | Trust | `EXT-Q40`, `EXT-Q43` | 240/120/60/30 | 120/60/30/20 |
| `federation-safeguards` | `P-FL-03` | Federation | `EXT-Q67`, `EXT-Q68` | 240/180/90/45 | 120/90/45/30 |
| `policy-conflict-integrity` | `P-GOV-03` | Policy governance | `EXT-Q79` | 240/180/90/45 | 120/90/45/30 |

## Selection rationale

- **Operational and connectivity state:** node saturation, availability, connectivity and device transmission eligibility form the highest-frequency controls.
- **Topology and user context:** proximity and temporal wellbeing checks observe changing context without executing placement or adaptation actions.
- **Data and privacy:** buffer retention, restricted-zone confinement and consent integrity cover recurring data-handling constraints.
- **Governance and trust:** audit accountability, trust evidence and policy-conflict integrity provide slower controls over evidence and configuration consistency.
- **Federation:** recurring safeguards detect unauthorized upstream sessions and missing privacy mechanisms when federated state is present.

The workload intentionally excludes full inventories, dashboards, benchmark scenarios, broad decision reports and action-selection queries. Those queries remain available to their dedicated workflows. The scheduler performs only Monitor activities: it does not deploy, replicate, migrate, plan placement or change the configured demand level.

## Temporal and synchronization notes

All tasks define positive intervals and deadlines for every demand level, each deadline is no longer than its interval, and intervals satisfy LOW ≥ NORMAL ≥ HIGH ≥ CRITICAL. Heterogeneous intervals reduce repeated alignment after the initial release. No arbitrary initial offsets are used because the ontology and policy artifacts do not define them. The existing short-cycle warning remains authoritative when a measurement window produces too few observations for a task.

## Traceability and limits

Policy-query associations come from `docs/QUERY_CATALOG.md`, whose requirements and policies are derived from the repository query contracts. Each active task selects one policy that directly appears in the catalog mapping of every query assigned to that task. Some catalog queries map to several policies; selection of one task policy does not remove the other documented relationships.

This classification is an experiment workload taxonomy, not an ontology entailment or a proof that excluded policies are unmonitored in every deployment. Schedules are experimental parameters. The current experiment fixes one demand level per repetition and does not implement Analyze, Plan, automatic demand transitions or horizontal scaling.
