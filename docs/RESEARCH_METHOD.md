# Research Method and System Guide

## 1. Purpose and scope

The proposal is a policy-driven architecture for deciding what to monitor across
a physical computing continuum. Its knowledge mechanism is a modular ontology.
The intended motivating domain is wellbeing and stress monitoring in the
OnTheEdge context. This repository evaluates software and controlled workloads;
it does not contain a clinical validation of stress detection.

The research question is whether explicit context-sensitive policies can produce
appropriate monitoring plans at an acceptable computational cost across devices
with different capacities. A second question is how placement of the semantic
knowledge and choice of reasoner affect the cost and correctness of querying that
knowledge. These questions require different experiments and must not be merged
into one performance claim.

The general architecture can retain its infrastructure, governance and
observability concepts while replacing a domain module and its policies.
Supporting that extension structurally is different from demonstrating equivalent
performance or correctness in another application domain.

## 2. Architecture and responsibilities

| Component | Responsibility | Why it is separate |
| --- | --- | --- |
| `core` | Node identity, static resources, location, policy/requirement/query concepts and reasoner contracts | Reusable domain concepts must not depend on an experimental runner. |
| Modular ontology | Shared vocabulary, relationships, policy metadata and application instances | Domain-specific concepts can evolve without copying the entire model. |
| Query catalog and execution plan | Query text, purpose, expected results, policy links, source scope and merge strategy | Logical meaning and placement are reviewable independently from timing. |
| Physical workers | Prepare assigned data, invoke a reasoner and execute assigned queries | Real process and machine costs are exercised on the selected hosts. |
| Monitoring runners | Construct controlled workloads, coordinate workers, impose budgets and write evidence | Experiment logic stays outside the ontology and reasoner adapters. |
| Policy comparison adapters | Static, procedural and semantic plan selection | Equivalent inputs can be evaluated without embedding the expected answer in the implementation. |
| Reporting | Validate evidence and generate PNGs from structured results | A graph must not decide whether a failed run counts as a success. |

A conceptual MAPE-K architecture motivates monitoring, analysis, planning,
execution and shared knowledge. The implemented evaluations cover selected
monitoring/decision and reasoning mechanisms. A returned plan does not mean a
physical actuator, migration or sampling-frequency change was executed.

## 3. Ontology modules and policies

Foundation reuses general vocabulary. Topology describes continuum nodes and
relationships. Governance represents policies, requirements, consent and
authorization. Observability describes measured or recorded state. Orchestration
represents decisions and adaptation. Deployment links fragments to nodes.
Federation describes federated-learning concepts. The optional wellbeing module
adds users' devices and physiological/stress-related concepts.

The source of truth is the maintained Turtle model, not a diagram. See the
[ontology reference](reference/ONTOLOGY_REFERENCE.md),
[policy catalog](reference/POLICIES.md) and
[requirements](reference/REQUIREMENTS.md) for exact definitions and identifiers.

Policy categories organize concerns such as consent, data handling, node
eligibility and adaptation. Categories are not ontology modules: one operational
policy may depend on several modules and address several concerns. For example,
a change in processing location requires topology, context and governance evidence
before a new monitoring plan can be authorized. Category labels alone neither
implement a conflict resolver nor demonstrate that a policy was enforced.

A category cost is meaningful only when its workload, queries, input scale,
reasoner and placement are stated. Categories with more queries naturally have
larger aggregate costs; report both total cost and per-query or per-decision cost
when comparing them. Do not infer clinical importance from computational expense.

## 4. Physical continuum and network interpretation

Cloud is the coordinator machine. Fog and Edge are Raspberry Pi workers.
Mist is represented but currently offline; the explicit five-node profile excludes
it. Real workloads run on the actual hosts over Tailscale. Roles express placement
and responsibilities; they do not turn a Raspberry Pi into a commercial cloud.

The VPN supplies connectivity across deployment sites. It is not a calibrated
model of physical distance, latency, bandwidth, jitter or packet loss. Geographic
coordinates and controlled impairment parameters must be recorded before claiming
a distance effect. Logical user/device counts are synthesized in software and are
not additional physical devices.

Node identity and static capacity are separate from dynamic measurements.
Configuration describes CPU, RAM, storage, processing/network capacity, device
type and structured location. Runtime telemetry records observed consumption.
The reachable Raspberry Pis currently use 32-bit user space over a 64-bit kernel;
large native processes may hit address-space limits before exhausting host RAM.

## 5. Knowledge placement and reasoners

| Placement | Implemented behavior | What can be compared |
| --- | --- | --- |
| Replicated | Each selected worker prepares the full logical graph; query work is assigned among replicas. | Duplication, preparation cost, total memory and query balancing. |
| Distributed | Authority-aware instance fragments are assigned to workers, shared schema may be replicated, queries are routed and results merged. | Local graph size, preparation/transport overhead, query cost and equivalence against the full reference. |

A common conceptual vocabulary is sometimes called shared knowledge. There is
no third active `shared` benchmark placement or shared-memory store. The supported
physical layout names are `replicated` and `distributed`.

RDFS is the lightweight entailment baseline. HermiT, Openllet, JFact and Konclude
use native runtimes behind the common abstraction. Their semantics and output
contracts are recorded. Native timings include conversion/startup where applicable;
they are not pure reasoner-kernel benchmarks. A missing backend is a failure or
explicitly unavailable case, never a silent switch to another reasoner.

Consistency asks whether an ontology can have a model. Query equivalence asks
whether a particular distributed execution returns the same answer as its
canonical reference. Neither guarantees the other. Fragment-local OWL reasoning
is not assumed globally complete. Every measured speedup needs valid, equivalent
work, and mismatched results remain excluded.

## 6. Questions and experiment selection

| Question | Appropriate experiment | Required evidence | What it does not establish |
| --- | --- | --- | --- |
| Do policies choose the configured monitoring plan? | Policy effectiveness | Coverage, precision, excess/missing resource–metric pairs and exact plans against explicit expected plans | Clinical correctness or unseen-context generalization. |
| Does a plan change correctly after a known context change? | Controlled adaptation | Ordered contexts, policy changes, chosen interval and decision latency | Physical failure detection or network recovery. |
| What extra cost does semantic selection add? | Paired procedural versus semantic comparison | Same node, inputs, preparation boundaries and operational answers | Superiority over original published systems. |
| How does processing grow with workload? | Physical scalability and comparison scalability | Valid result equivalence, scale, latency, throughput and resources | An isolated causal effect if several variables grow together. |
| How does cost accumulate? | Physical cumulative stages or comparison cumulative events | Explicit definition of what grows and which work is retained | The two cumulative experiments are not interchangeable. |
| Does more physical capacity help? | Scale-out / distributed reasoning strong scaling | Fixed total logical work across node counts | Benefits from merely increasing both work and hardware. |
| Does capacity remain stable as work grows with nodes? | Weak scaling | Fixed work per node and reported total work | Constant end-to-end latency under all workloads. |
| Where does a reasoner reach capacity? | Bounded hardware/load experiments | Completed points, timeouts, failures and largest validated scale | Zero cost for missing points or proof that a timeout means inconsistency. |

For a compact article, prioritize policy-plan quality, paired semantic overhead,
and one scalability/cumulative comparison aligned with the architectural claim.
Keep diagnostic matrices and per-node figures in supplementary material.

## 7. Distinct evaluation paths

### 7.1 Original four-block policy evaluator

`policy-evaluation` runs effectiveness, dynamic adaptation, scalability and
computational cost. The decision engine evaluates procedural context rules.
Ontology identifier validation and a separately timed reasoning probe accompany
it, but the inferred graph is not consumed by that decision engine.

Its conformance score includes policy identifiers as well as operational plan
items. It is useful for regression and controlled cost analysis. It must not be
presented as evidence that semantic inference improved monitoring decisions.
Historical `detection_latency_ms` means supplied-context read time. Estimated
observation counts and bytes are derived from plans, windows and payload sizes;
they are not emitted events or measured interface traffic.

### 7.2 Alternative comparison module

`monitoring/comparison` runs static, procedural and semantic adapters as isolated
jobs on each selected physical host. The semantic adapter materializes RDFS tier
membership and consumes it through SPARQL; removing that inferred membership
changes the decision. The procedural adapter implements the same adaptive rule
semantics. Static monitoring supplies a context-independent baseline.

Expected plans come from the configuration and are not passed to adapters.
Procedural and semantic strategies should agree on operational outputs; a quality
mismatch is investigated before interpreting timing. Five repetitions are the
full default, with explicit warm-up and deterministic workload generation.
Smoke mode reduces work and is always labeled verification evidence.

Each host executes the paired workload independently. This comparison is not
federated query execution. Its cumulative experiment increases the number of
context events over a model prepared once per job. Its scalability experiment
jointly increases logical resources and rule copies. See the
[complete comparison protocol](COMPARATIVE_EVALUATION.md).

### 7.3 Physical reasoning and monitoring suites

These runners prepare replicated or distributed data on HTTP workers. Scalability
increases configured synthetic users and evaluates the query catalog. Cumulative
stages add query categories in the configured order. The coordinator records
preparation, query execution and applicable reference validation separately.

Additional load, scale-out, hardware reasoning, distributed-reasoning and campaign
families explore offered event rate, physical nodes, graph size, rule count,
concurrency and other axes. They are supporting diagnostics, not automatically
all necessary for a paper. The exact file-to-figure mapping is maintained in
[Tests and figures](TESTS_AND_FIGURES.md).

## 8. End-to-end procedure and why each step matters

1. Install the pinned environment and native backends using
   [Complete execution](COMPLETE_EXECUTION.md). Dependency integrity does not
   replace native inference and inconsistency checks.
2. Choose one explicit topology and compatible experiment profiles. A five-node
   run cannot include a six-node scale point.
3. Validate syntax, ontology structure, query expectations, fragmentation and
   privacy placement. Run external OWL consistency checks separately.
4. Deploy identical source/configuration to all selected nodes and verify build,
   protocol, ontology revision and topology identity.
5. Run bounded smoke checks. Investigate semantic mismatches and failed phases
   before investing in a full campaign.
6. Fix the hypotheses, compared configurations and interpretation criteria before
   measuring. Separate system acceptance thresholds from execution deadlines.
7. Execute full repetitions and warm-up on otherwise stable hosts. Record seed,
   node inventory, backend and versions, placement, workload and limits.
8. Inspect statuses and validate results before generating figures. Preserve failed
   and censored points; do not silently replace them or their metadata.
9. Generate PNGs from the recorded structured data. Keep numerical summaries and
   source provenance alongside figures.
10. Report uncertainty, coverage and limits. Archive an immutable run directory
    before changing code or deployment.

The five-node commands and remediation evidence are in
[Audit remediation](REMEDIATION.md). Use `suite --dry-run` to inspect the plan;
this creates a plan, not experimental results.

## 9. Metrics and units

| Metric | Meaning and interpretation |
| --- | --- |
| Decision latency | Time to produce a plan from an already supplied context; report mean and distribution/percentiles separately. |
| Preparation/reasoning | Initialization and materialization costs, reported separately from a decision loop unless explicitly amortized. |
| Throughput | Completed decisions/events per measured interval; state whether preparation and transport are included. |
| CPU | Distinguish process CPU time from CPU percentage and node telemetry. One-core percentages can exceed 100 for parallel work. |
| RSS | Resident memory, with process and sampling scope. Python-process RSS excludes native reasoner child memory unless separately recorded. |
| Network cost | Distinguish observed transport duration/bytes from estimated payload volume and configured network scenarios. |
| Coverage/precision | Agreement with the configured operational oracle, not statistical sensitivity/specificity for patient stress. |
| Timeout | Right-censored execution at a known boundary; not a measured completion latency. |
| Recovery | In current policy comparisons, plan coherence after a recovery label; not a restored physical service. |

Never stack a one-off batch cost and an average per-decision cost directly.
The cost figure divides the separate reasoning probe by `decision_iterations`
before combining it with per-decision policy and plan time. Never equate MiB and
MB without conversion or compare host totals with process-only measurements.

## 10. Figures, uncertainty and result integrity

Figures must identify experiment, node or node population, strategy/backend,
placement, workload axis, units and uncertainty definition. Policy categories
use consistent colors. Include failed/skipped/timeout coverage so that a fast
curve cannot hide missing difficult cases. Use logarithmic axes only for positive
quantities and describe them explicitly.

The comparison reporter validates raw records, retains per-point provenance and
uses its configured repetition-level statistical contract. Events inside a single
process are not independent process repetitions. Smoke figures must not suggest
publication-quality uncertainty. The original evaluator reports scenario-averaged
repetition variability for effectiveness; other panels must state their own
aggregation scope.

Result generation and visualization are separate. CSV/JSON/JSONL evidence is
retained even when no scientifically valid plot can be produced. Empty or invalid
populations should produce a diagnostic, not an invented bar or zero point.
Exact-build gates may reject old results after code changes; that is a provenance
boundary, not permission to rewrite old metadata.

## 11. Relationship to other work

The reference table in [Comparative evaluation](COMPARATIVE_EVALUATION.md#relationship-to-published-work)
explains which published approaches motivate the controlled baselines. A generic
procedural implementation is not FogMon, EdgeOnto or another author's system.
Do not compare published milliseconds directly against our hardware measurements.

A quantitative comparison with an external system requires its actual
implementation, a common supported workload, equivalent outputs, matched hardware,
and the same timing/resource boundaries. Where these cannot be matched, use a
qualitative comparison of architectural features and state the incompatibility.
The current module supports defensible within-project controlled comparisons.

## 12. Limits and acceptance decisions

Structural validation, software tests, benchmark completion, semantic equivalence
and scientific acceptance are separate gates. The query catalog is structurally
validated. Fifty-seven historical/completeness warnings remain because their
source evidence or prospective thresholds are absent. Their exact subjects,
properties and required actions are exported by `tools/review_validation_debt.py`.

The reviewed coverage dispositions distinguish software checks, partial evidence
and deferred functionality. None turns unimplemented mobility, arbitrary SPARQL
endpoint support, real energy management, durable physical recovery or clinical
validation into a completed feature.

A positive result should therefore say precisely which configured workload,
physical nodes, semantic contract and metric support it. The reusable architecture
is the proposal; the measured experiment is its bounded evidence.
