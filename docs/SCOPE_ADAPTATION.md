# Scope adaptation of requirements and policies

The 19 October 2026 adaptation preserves all 116 requirements, 79 policies and
115 queries. It revises 14 requirement statements and 10 policy statements to
match observable model contracts or executable software behavior. The ontology
revision is `4.0.0-monitoringcontinuum-v2`; the policy artifact is `POLICIES-REV-02`.
There is no schema/class migration. Prior statements are retained verbatim in
[scope-contracts.toml](../configs/scope-contracts.toml), not silently erased.

Eight adapted items now have directly relevant query references (four requirements
and four policies). Query traceability is **106/116 requirements (91.38%)** and
**73/79 policies (92.41%)**. The remaining ten requirements and six policies concern
software behavior, not SPARQL data inspection; they have explicit software evidence
rather than artificial query references. Neither count proves full operational
compliance of the architecture.

## Current contracts

### RF-07

The reference monitoring model must expose device battery, connection status and data readiness, together with the consent context used to interpret local operation. This requirement covers queryable decision inputs; automatic energy management, preprocessing and offloading on physical devices are outside this release.

- Verification: `model-query`.
- Queries: `BASE-Q10`, `BASE-Q15`.
- Supporting evidence: [tests/monitoring/test_policy_evaluation.py](../tests/monitoring/test_policy_evaluation.py).

### RF-41

Reference semantic contracts must expose their governing policies through governedBy. Evaluation and action records must expose the policy justification checked by the audit queries. This requirement does not impose governedBy on every user, node or zone.

- Verification: `model-query`.
- Queries: `EXT-Q12`, `EXT-Q72`.
- Supporting evidence: [queries/core/policy_governance](../queries/core/policy_governance).

### RF-44

Each reference evaluation that records an adaptation action must identify an applied policy, and each recorded adaptation action must identify its authorizing evaluation. Audit queries must detect missing links; the records do not prove physical execution of migration or degradation.

- Verification: `model-query`.
- Queries: `EXT-Q72`.
- Supporting evidence: [queries/core](../queries/core).

### RF-52

The reference model must expose privacy and other decision weights, the selected model tier and its justification. A recorded Cloud selection without global consent, a permitted zone and granted authorization must be detectable. Automatic privacy-weight optimization is outside this release.

- Verification: `model-query`.
- Queries: `EXT-Q46`, `EXT-Q56`.
- Supporting evidence: [ontology/examples/reference-system.ttl](../ontology/examples/reference-system.ttl).

### RF-69

Physical workers must execute registered query identifiers from the versioned SPARQL catalogue through the project worker protocol. Arbitrary client-supplied SPARQL and a public SPARQL 1.1 HTTP endpoint are outside this release.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/monitoring/test_distributed.py](../tests/monitoring/test_distributed.py).

### RNF-03

Bounded monitoring experiments must record completion, timeout and failure separately. With keep-going enabled, independent later points must remain eligible for execution under the configured skip rules. These measurements do not guarantee service-level acceptance or automatic physical degradation.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/monitoring/test_load_benchmark.py](../tests/monitoring/test_load_benchmark.py).

### RNF-10

The maintained synthetic workload must add supported user and related instance records deterministically, without changing the ontology schema. Module import closure must remain valid. Other instance types or specializations require explicit validation before they enter the baseline.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/core/test_synthetic.py](../tests/core/test_synthetic.py).

### RNF-11

Query catalogue extensions must be introduced as versioned source changes that update the query inventory, routing plan, expectations and reference documentation together. The loader must reject inconsistent metadata; runtime insertion of arbitrary query identifiers is not supported.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/core/test_catalog.py](../tests/core/test_catalog.py).

### RNF-23

The optional wellbeing module must permit a wearable subtype to specialize the existing Wearable class while retaining inherited user-device relations under RDFS reasoning. This is semantic extensibility; physical device drivers and sensor adapters are outside this release.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/core/test_scope_contracts.py](../tests/core/test_scope_contracts.py).

### RNF-24

Maintained ontology files must parse as Turtle/RDF and catalogue queries must execute using the supported SPARQL 1.1 features in RDFLib. OWL axioms are interpreted under each declared reasoner contract; no HTTP endpoint interoperability is claimed.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/core/test_catalog.py](../tests/core/test_catalog.py).

### RNF-26

The supported RDFS, HermiT, Openllet, JFact and Konclude adapters must expose their execution contracts and reject unavailable or unsupported native configurations without silently substituting another reasoner. This requirement concerns these adapters, not arbitrary external SPARQL services.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/core/test_native_reasoners.py](../tests/core/test_native_reasoners.py).

### RNF-31

Every catalogue query must declare its inventory, report, review or violation kind and its interpretation expectation. Catalogue validation must preserve the distinction between warnings, violations and descriptive results.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/core/test_catalog.py](../tests/core/test_catalog.py).

### RNF-37

The schema must provide derivedFrom from State to SOSA Observation so a supplied provenance assertion remains queryable after RDFS materialization. Missing source observations must not be fabricated; automatic provenance capture for every runtime metric is outside this release.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/core/test_scope_contracts.py](../tests/core/test_scope_contracts.py).

### RNF-38

Maintained ontology, policy and query changes must pass the release inventory, query expectations and regression checks. Changed semantic content must produce a different semantic digest and an explicit revision; incompatible schema or query contracts require a major-version migration. This does not certify arbitrary downstream extensions.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/core/test_release.py](../tests/core/test_release.py).

### P-ADAPT-08

Reference ReplicationEvent and SynchronizationEvent records must declare replicationVersion and idempotencyKey; the validation query must identify missing fields. This metadata contract does not guarantee exactly-once physical delivery, durable buffering or duplicate-free migration.

- Verification: `model-query`.
- Queries: `EXT-Q34`.
- Supporting evidence: [src/continuum_bench/monitoring/distributed.py](../src/continuum_bench/monitoring/distributed.py).

### P-CONS-06

Reference federated-learning session reports must expose payload type, required consent range and flags for personal data, individualized gradients and persistent identifiers. Missing fields must remain visible as missing evidence. These records do not authorize a physical model download or extend user consent.

- Verification: `model-query`.
- Queries: `EXT-Q66`.
- Supporting evidence: [ontology/modules/governance.ttl](../ontology/modules/governance.ttl).

### P-GOV-02

Governance evidence in the reference graph must expose governedBy for semantic contracts and appliedPolicy for evaluations with actions. Missing action-evaluation or evaluation-policy links must be reported. Other declared mechanisms are not evidence of runtime enforcement.

- Verification: `model-query`.
- Queries: `EXT-Q12`, `EXT-Q72`.
- Supporting evidence: [queries/core/policy_governance](../queries/core/policy_governance).

### P-MODEL-09

For each supplied context in the controlled monitoring experiment, the policy engine must recompute the active rules and resulting monitoring plan and record its evaluation time. It must not reuse a previous context plan implicitly. Live context detection and model-reselection deadlines are outside this release.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/core/test_scope_contracts.py](../tests/core/test_scope_contracts.py).

### P-NODE-06

If no configured resource tier matches the active monitoring rules, the policy engine must return an empty resource selection rather than silently selecting a higher tier. This is a planning boundary, not an operational trust assessment or a physical retention actuator.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/core/test_scope_contracts.py](../tests/core/test_scope_contracts.py).

### P-OPS-04

A failed or timed-out monitoring point must remain an explicit outcome. Under keep-going, subsequent independent points may execute according to the configured skip rules. This policy does not guarantee continuity of application services or durable synchronization during a physical failure.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/monitoring/test_timeout_skip_policy.py](../tests/monitoring/test_timeout_skip_policy.py).

### P-OPS-06

A supplied recovery context must be evaluated against its configured rules, producing a fresh monitoring plan rather than automatically restoring the largest resource set or shortest sampling interval. Per-item buffer-drain authorization and physical synchronization are outside this release.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/core/test_scope_contracts.py](../tests/core/test_scope_contracts.py).

### P-VAL-02

Each registered query must declare a supported kind and an explicit interpretation expectation before catalogue loading succeeds. Inventory and report queries are descriptive; review queries expose evidence debt; violation queries are interpreted using their configured expectations.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/core/test_catalog.py](../tests/core/test_catalog.py).

### P-VAL-05

Ontology, policy and query changes must preserve the maintained release checks or explicitly revise the contract and migration documentation. Source and semantic fingerprints must distinguish changed versions from earlier measurements; compatibility with all future integrations is not promised.

- Verification: `software-check`.
- Queries: Software verification; no query coverage claimed..
- Supporting evidence: [tests/core/test_release.py](../tests/core/test_release.py).

### P-ZONE-04

For a supplied reference zone assignment, validation must detect a selected external tier or recorded external transfer that violates restricted-zone confinement. This is a graph-validation policy; live mobility detection and automatic invalidation before physical transmission are future work.

- Verification: `model-query`.
- Queries: `EXT-Q37`.
- Supporting evidence: [src/continuum_bench/core/domain.py](../src/continuum_bench/core/domain.py).

## What the checks establish

Counterexample tests introduce missing replication keys, an unjustified action,
a Cloud selection without consent evidence and a restricted-zone violation. The
corresponding queries must detect them. Other tests add a wearable subtype and
supplied observation provenance, and verify that changing a supplied context
recomputes the plan and never invents a resource when no tier matches.

Report queries expose supplied values and missing bindings; they do not authorize
real transfers. Software tests cover supported behavior, not future device drivers,
clinical detection, durable event delivery or arbitrary downstream integration.

## Migration and retained evidence

Historical results retain their original source, policy version and semantic
digests. Never relabel or merge them as measurements of this revision. Before a
new physical campaign, synchronize and restart every worker with the new semantic
assets and verify health. The strict revision/digest check should reject stale
workers rather than run a mixed-version experiment.

```bash
source .venv/bin/activate
python -m pytest tests/core/test_scope_contracts.py tests/core/test_release.py tests/infrastructure/test_validation_debt.py
python tools/review_validation_debt.py
continuum-bench physical deploy --with-dl-reasoners --ssh-user pi
continuum-bench physical start --ssh-user pi
continuum-bench physical status --ssh-user pi
```

The 57 historical-data/acceptance warnings remain. Scope adaptation cannot supply
missing AHP inputs, timestamps or trust windows. See [Ontology review](ONTOLOGY_REVIEW.md).
