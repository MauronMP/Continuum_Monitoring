# Experiments and scientific contracts

## Three batteries, one reusable core

The project currently exposes three evaluation batteries. Their experimental
families are components, not additional standalone research modules. A proposed
separate battery comparing static, threshold/rule-based, context-aware and
ontology-plus-policy-aware monitoring is **not implemented**. No current result
should be presented as that four-strategy comparison.

| Battery | Entry point | Scientific object |
| --- | --- | --- |
| 1. Physical architecture evaluation | `continuum-bench suite` | Cost, capacity and query correctness of configured monitoring workloads across a physical continuum. |
| 3. Container scalability | `continuum-bench container-scale run` | Cost and supported query equivalence as logical participants, users, data and requests grow on fixed physical hosts. |
| 2. Monitoring-strategy comparison | `python -m continuum_bench.monitoring.comparison run` | Paired operational-plan quality and computational cost of three decision implementations. |

See [Complete execution](COMPLETE_EXECUTION.md) for commands and [Outputs](OUTPUTS.md)
for evidence. Ontology and policies are internal mechanisms; neither an OWL
consistency check nor a timing curve validates stress detection clinically.

## Battery 1: physical architecture evaluation

The coordinator orchestrates six physical hosts: Cloud, Fog, Mist and three Edge
nodes. Devices are geographically distributed and connected through Tailscale.
Roles express architectural responsibilities, not controlled hardware classes.
The VPN carries real traffic: `network_mbps` is inventory metadata and no traffic
shaping is applied. Unrecorded coordinates and link capacity must remain unknown.

`monitoring/suite.py` composes independent families and records their outcomes.
Infrastructure discovery, graph construction, reasoner adapters, metrics and
reporting are separate modules. Each point records the configured backend and
workload; errors and timeouts are preserved. Distributed mode uses authority-aware
instance fragments and tier-specific schema; replicated mode gives each worker
the complete workload. See [Ontology distribution](ONTOLOGY_DISTRIBUTION.md).

| Family / implementation | What changes or executes | Main observations | Interpretation boundary |
| --- | --- | --- | --- |
| Scalability: `physical.py`, `distributed_ontology.py` | Increasing synthetic users, repeated across five reasoners and two placements. | Preparation/reasoning cost, query latency, CPU/RSS, throughput, status and reference agreement. | Synthetic user growth is not increasing physical hosts. |
| Cumulative monitoring: same coordinators | Successively includes configured query categories for the prepared workload. | Stage cost, accumulated work and category contribution. | Accumulated categories are not time-varying real patients. |
| Load: `load_benchmark.py` | Configured event rates, users, triples, rule counts and node counts. | Completion, losses/timeouts, query timing, preparation and recovery phases. | Rebuilding worker state is not end-to-end application recovery. |
| Scale-out: `experiments.py` | Selects increasing numbers of real workers from the inventory. | Execution time, throughput and per-node workload. | Real VPN conditions are uncontrolled; shared hardware types confound tier comparisons. |
| Reasoning hardware: `experiments.py` | Varies users, asserted graph size or generated rule count on physical backends. | Materialization time, resources and capacity failures. | Neutral padding and semantic axioms represent different costs. |
| Distributed ontology: `experiments.py` | Executes fragmented and full reference graphs and compares query results. | Placement costs, exact query evidence and worker timings. | Agreement is workload/query-specific, not complete distributed OWL semantics. |
| Distributed reasoning scalability: `distributed_reasoning_scalability.py` | Configured graph sizes, worker counts and RDFS / OWL classification-realization tasks. | Scaling, normalized semantic validation, capacity and resource observations. | Backends expose different reasoning contracts; do not compare unlike tasks as identical. |
| Workload-axis campaign: `campaign.py` | Changes physical nodes, IoT instances, users, requests, policies, individuals, requirements, query complexity/count or concurrency. | End-to-end request work, throughput, CPU/RSS, status and result checks. | Generated workload vocabulary is a controlled workload, not every application ontology module. |
| Policy-plan evaluation: `policy_evaluation/` | Effectiveness, context adaptation, scalability and computational cost of fixed/procedural plans. | Plan conformance, coverage/excess, evaluation cost, sampled resources and estimated observation volume. | Contexts are supplied; the timed reasoning probe does not feed the decision path. |

The local policy evaluator uses `normal → overload → failure → recovery` fixtures.
Its historical `detection_latency_ms` field times reading a supplied context.
`total_adaptation_latency_ms` includes a separate reasoning probe. Neither is
physical fault-detection latency. Observation counts and traffic are model-based
estimates, not emitted events or measured interface bytes. Process sampling does
not automatically include native children; read each field's recorded scope.

A policy belongs to one or more semantic categories. Category-associated queries
may support multiple policies; their shared execution cost must not be counted
as several independent measurements. The 12 policy categories and 16 query groups
are different classifications. The [query guide](../queries/README.md) explains
routing and the compiled query catalogue.

## Battery 2: monitoring-strategy comparison

The module `monitoring/comparison/` defines a `DecisionAdapter` contract:
`decide(context) -> MonitoringPlan`. Adapters receive inputs but never the expected
plan. The runner owns repetitions, deterministic ordering, transport, timing and
outputs. Each strategy/job executes in a fresh process on one selected host;
this is paired per-host evaluation, not collaborative distributed decisions.

| Strategy | Actual mechanism | Purpose |
| --- | --- | --- |
| `static` | A fixed resource/metric/action/interval plan. | Quantify the cost and excess coverage of context-independent monitoring. |
| `procedural` | Existing `PolicyEngine` selects configured rules for a supplied context. | Establish the non-semantic adaptive baseline. |
| `semantic` | RDFS materializes specialized resource types; SPARQL selects policies and inferred tier members. | Measure an executable semantic implementation of equivalent supported policies. |

The semantic adapter uses a small RDF projection of the same inputs. It does not
load the entire modular ontology, use all OWL backends or implement general policy
conflict resolution. RDFS type inference is consumed by resource selection;
removing it changes decisions in the regression fixture. A supplied context label
is not inferred from raw sensors in any current adapter.

| Experiment | Method | Primary evidence |
| --- | --- | --- |
| Effectiveness | Same shuffled contexts and independently configured expected operational plans. | Resource–metric coverage, over/under-monitoring, interval/actions and exact-plan agreement. |
| Adaptation | Ordered normal/overload/failure/recovery transitions. | Decision time after known context, active policies and planned versus required interval. |
| Scalability | Multiply logical resources and policy copies. | Preparation, decision p50/p95, throughput and sampled memory per host. |
| Cumulative | Process longer traces without rebuilding the model inside a job. | Accumulated decision time, amortized throughput and CPU per event. |

Scalability currently increases resources and policies together, so it cannot
isolate their separate causal effects. Each cumulative size is a new isolated job;
it is not a continuously growing ontology. All six executors, including Mist,
are selected by default. The default matrix has 720 jobs and five repetitions.

Correctness compares observable plans, not policy IDs that would unfairly penalize
the static baseline. Coverage uses resource–metric pairs; exact agreement also
checks actions and sampling interval. Expected plans are configured acceptance
criteria, not clinical ground truth. Semantic and procedural agreement validates
functional equivalence on these scenarios, not superior semantic accuracy.

## Fairness, reproducibility and interpretation

Use identical inputs and seeds, archive effective configuration and source, and
pair strategies within node/workload/repetition. Warm-up precedes measurement;
preparation and steady-state decisions are reported separately. Cross-host totals
must not be called one distributed transaction. Native allocation failures are
capacity observations and cannot be repaired by extending timeouts.

Report missing, failed, timed-out and skipped points with denominators. Do not
replace them with zero or hide them from coverage. Confidence intervals require
independent repetitions; successful-only curves can exhibit survivor bias.
Absolute timings vary with CPU scheduling, temperature, background load and VPN
paths even when generated input is deterministic. Scientific claims must name
the dataset, release, hardware and evaluation boundary.

## References and how they are used

These are methodological references, not implemented replicas or imported result
sets. Their numbers must not be pooled with this project's measurements.

| Reference | Relevance to the experiments | What is not reproduced |
| --- | --- | --- |
| Forti, Gaglianese and Brogi, *Lightweight self-organising distributed monitoring of Fog infrastructures*, FGCS 114, 605–618 (2021), [publisher](https://www.sciencedirect.com/science/article/abs/pii/S0167739X19334582). | Physical fog monitoring, resource/network costs and scale-out motivate Battery 1. | FogMon's peer-to-peer overlay, restructuring algorithm and fault resilience. |
| Ghrab et al., *A core IoT ontology for automation support in edge computing*, SOCA 17, 25–37 (2023), [publisher](https://link.springer.com/article/10.1007/s11761-022-00356-2). | Semantic resource matching motivates the explicit inferred resource-selection mechanism in Battery 2. | EdgeOnto's matchmaker and its precision/recall dataset. |
| De Brouwer et al., *Towards a Cascading Reasoning Framework to Support Responsive Ambient-Intelligent Healthcare Interventions*, Sensors 18, 3514 (2018), [publisher](https://www.mdpi.com/1424-8220/18/10/3514). | Hierarchical reasoning cost and healthcare context motivate architectural placement and latency boundaries. | Cascading stream reasoning, deployed interventions or clinical outcomes. |

A direct quantitative comparison with these systems would require their actual
implementations on matched supported workloads and hardware. The current three
adapters are controlled baselines only. The future four-strategy battery must
introduce raw observations, threshold/context mechanisms and an independently
reviewed oracle before claiming those additional comparisons.

## Battery 3: containerized continuum scalability

[Container scalability](CONTAINER_SCALABILITY.md) documents the complete technical
and scientific contract. It reuses the maintained worker, partitioner, reasoner
adapters and query engine under Docker Compose CPU/memory budgets. The coordinator
remains centralized. Users/data/request growth, fixed-load repartitioning and
proportional logical-load growth are distinct scenarios. One participant per host
is the initial profile; more participants do not imply more physical hardware.

Matched distributed and globally replicated placements preserve workload seeds
and resource budgets. Query fan-out counts are retained as operational work;
logical throughput uses completed full-catalog requests per second. Supported
query projections are checked against the replicated reference. This battery
does not evaluate clinical accuracy, decentralization, mobility or live recovery.
The full catalog/policy workload is fixed; cumulative category tests remain in
Battery 1. Fluidity and FogMon motivate the experimentation and overhead analysis,
respectively; their deployment and self-organization algorithms are not reproduced.

## Optional policy-directed recovery extension

[Adaptive monitoring](ADAPTIVE_MONITORING.md) reuses the container battery to evaluate whether policy-constrained additional service/fragment replicas restore successful execution while the original nodes keep processing queries. It separates application failures from service evidence, preserves workload and deadlines, and records abstentions and unsuccessful recoveries. It is an opt-in extension, not part of the three baseline batteries or proof of uninterrupted service recovery.
