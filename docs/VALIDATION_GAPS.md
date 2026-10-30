# Ontology warnings, traceability gaps and observed failures

Historical review date: 14 October 2026. Superseded for current statement scope
by [Scope adaptation](SCOPE_ADAPTATION.md) on 19 October 2026. Current query
traceability is 106/116 requirements and 73/79 policies; the tables below preserve
the pre-adaptation gaps and explain why the original broader claims were unsupported. Query references measure traceability, not runtime
compliance. A reviewed warning remains unresolved. This review does not invent
historical observations or turn implementation plans into measured evidence.

## Warning decisions

| Finding | Count | Why it remains | Evidence needed to close it |
| --- | ---: | --- | --- |
| Missing `hasAHPScore` | 32 | Legacy alternatives do not preserve sufficient inputs for a reproducible score. | Recover criteria comparisons, weights and alternative inputs; rerun the documented scoring method with provenance. |
| Missing `lastUpdated` | 2 | Actual model-version timestamps are absent. | Model registry/source version dates, not the audit date. |
| Missing trust-window bounds | 14 | Seven assessments lack start and end times. | Historical telemetry windows for each assessment; do not derive them from unrelated state timestamps. |
| Missing acceptance parameters | 9 | The reference acceptance profile is a draft, not an approved experimental contract. | Prospective, justified values with units and applicability, fixed before acquisition. |

The nine parameters are `T_migration_max`, `T_sparql_monitor`, `T_decision_max`,
`E_device_max`, `N_agents`, `T_node_join`, `D_delegation_max`,
`T_reselection_max` and `AHP_consistency_threshold`. Worker count is not necessarily
agent count. Infrastructure timeouts are execution safeguards, not scientific
acceptance thresholds. Mobility/migration bounds cannot certify an unimplemented
simulation or actuator.

Three source observations additionally lack measurement units. Their unknown-unit
markers are intentional and are not included in the 57 SHACL warnings.

## Coverage decisions

The catalogue references **102/116 requirements (87.93%)** and **69/79 policies
(87.34%)**. The following are all 24 unreferenced items. A software-check status
means there is engineering evidence outside the query catalogue; it does not
increase either percentage. Existing mapped items are not automatically fully
implemented or experimentally validated either.

## Requirements without query references

| ID | Review status | Missing evidence / boundary | Existing evidence |
| --- | --- | --- | --- |
| `RF-07` | deferred | Energy, connectivity and consent must be tested together on a physical device; configured plan scenarios are only partial evidence. | [tests/monitoring/test_policy_evaluation.py](../tests/monitoring/test_policy_evaluation.py) |
| `RF-41` | partial | Governing-policy links are queryable; a complete assertion of governedBy for every governed entity still needs a domain coverage test. | [queries/core/policy_governance](../queries/core/policy_governance) |
| `RF-44` | partial | Evaluation and action reports expose policy links; physical migration and degradation audit trails are not implemented end to end. | [queries/core](../queries/core) |
| `RF-52` | deferred | Privacy-weight dominance requires independently reviewed decision inputs and model-selection evidence. | [ontology/examples/reference-system.ttl](../ontology/examples/reference-system.ttl) |
| `RF-69` | deferred | Workers accept catalog query IDs, not arbitrary SPARQL 1.1 protocol requests. A standards-compliant endpoint is not implemented. | [src/continuum_bench/node.py](../src/continuum_bench/node.py) |
| `RNF-03` | deferred | Load tests exist, but operational acceptance thresholds and physical degradation evidence are missing. | [tests/monitoring/test_load_benchmark.py](../tests/monitoring/test_load_benchmark.py) |
| `RNF-10` | partial | Synthetic instances and modular imports are checked; arbitrary future extensions are not certified. | [tests/core/test_synthetic.py](../tests/core/test_synthetic.py) |
| `RNF-11` | partial | Catalog parsing and baseline expectations are tested; the release inventory is intentionally fixed and requires a versioned update for new IDs. | [tests/core/test_catalog.py](../tests/core/test_catalog.py) |
| `RNF-23` | deferred | Modular schema supports specialization, but a real new wearable adapter has not been validated. | [ontology/domains/wellbeing/schema.ttl](../ontology/domains/wellbeing/schema.ttl) |
| `RNF-24` | software-check | RDF/Turtle parsing and SPARQL execution are exercised; this does not certify a network SPARQL endpoint. | [tests/core/test_catalog.py](../tests/core/test_catalog.py) |
| `RNF-26` | partial | Four native reasoners are tested; external standards-compliant SPARQL endpoint interoperability remains untested. | [tests/core/test_native_reasoners.py](../tests/core/test_native_reasoners.py) |
| `RNF-31` | software-check | Query kinds and interpretation expectations are validated in the catalog contract. | [tests/core/test_catalog.py](../tests/core/test_catalog.py) |
| `RNF-37` | partial | Observation provenance exists in the schema; completeness for all measured runtime states is not established. | [ontology/modules/observability.ttl](../ontology/modules/observability.ttl) |
| `RNF-38` | partial | Baseline and release-contract regressions run; compatibility across arbitrary downstream integrations is outside this evidence. | [tests/core/test_release.py](../tests/core/test_release.py) |

## Policies without query references

| ID | Review status | Missing evidence / boundary | Existing evidence |
| --- | --- | --- | --- |
| `P-ADAPT-08` | deferred | Transport retries do not prove end-to-end critical-event idempotency; fault injection and durable event accounting are required. | [src/continuum_bench/monitoring/distributed.py](../src/continuum_bench/monitoring/distributed.py) |
| `P-CONS-06` | deferred | Generic-model download authorization needs model payload and contract checks beyond catalog queries. | [ontology/modules/governance.ttl](../ontology/modules/governance.ttl) |
| `P-GOV-02` | partial | Policy provenance can be inspected; complete governance of every physical action is not measured. | [queries/core/policy_governance](../queries/core/policy_governance) |
| `P-MODEL-09` | deferred | Context transitions are modeled; physical invalidation and reselection deadline enforcement need a real event source. | [tests/monitoring/test_policy_evaluation.py](../tests/monitoring/test_policy_evaluation.py) |
| `P-NODE-06` | partial | Reference scenarios describe no eligible alternatives; adversarial operational fallback needs execution evidence. | [ontology/examples/reference-system.ttl](../ontology/examples/reference-system.ttl) |
| `P-OPS-04` | deferred | No physical fault-injection campaign has verified critical-function continuity or durable synchronization. | [docs/EXPERIMENTS.md](../docs/EXPERIMENTS.md) |
| `P-OPS-06` | partial | Controlled recovery checks stale policies; per-item physical buffer-drain authorization is not validated. | [tests/monitoring/test_policy_evaluation.py](../tests/monitoring/test_policy_evaluation.py) |
| `P-VAL-02` | software-check | Catalog checks enforce declared query types and interpretation expectations. | [tests/core/test_catalog.py](../tests/core/test_catalog.py) |
| `P-VAL-05` | partial | Versioned release contracts and regression tests protect the maintained baseline, not every possible extension. | [tests/core/test_release.py](../tests/core/test_release.py) |
| `P-ZONE-04` | deferred | Actual mobility-triggered invalidation is not implemented; future mobility interfaces are insufficient evidence. | [src/continuum_bench/core/domain.py](../src/continuum_bench/core/domain.py) |

## Recorded failure diagnosis

The retained 7 October suite predates the current source and ontology. Counts
below are failed observations, not counts of affected processes or hardware
faults. One distributed observation may contain errors from several workers.

| Family | Evidence | Interpretation and next action |
| --- | --- | --- |
| Load | 27 allocation failures: Konclude 12, JFact 6, HermiT 6, Openllet 3 | Explicit `bad_alloc` / Java heap errors. Investigate graph size, peak memory and worker address space; increasing timeout cannot solve allocation exhaustion. |
| Load | One Konclude exit `-11` | Native crash, not proven memory exhaustion or ontology inconsistency. Preserve the exact input and native logs; reproduce in isolation on a compatible runtime. |
| Replicated scalability | Three Konclude failures at 5,000 users: two allocation failures and one exit `-11` | Full worker logs contain allocation evidence for two observations; truncated summary errors alone are insufficient. The crash remains separately classified. |
| Scalability | Distributed: 18 timeouts; replicated: 30 timeouts | Bounded work did not finish; no result should be fabricated or interpreted as zero cost. |
| Load | 105 timeouts: 88 preparation, 13 recovery, 4 workload | Investigate the phase separately. These do not establish successful service recovery. |
| Independent experiments, campaign and original report | Build/fingerprint mismatch in the retained execution | Freeze one revision and synchronize before rerunning. Successful current health checks do not repair historical measurements. |

The recorded reference checks all matched (23,640 comparisons); the current
reference ontology also passes all four native consistency checks. Neither
finding establishes the cause of a native crash on an unfinished larger graph.
There is no evidence here that missing AHP scores caused the observed heap errors.

## Fixes in this review

- The debt checker now rejects release-contract errors, blocking SHACL violations
  and non-missing-value findings even when they concern a familiar property.
  Reports retain the exact severity, constraint, message and coverage counts.
- Regression cases insert an invalid score and a blocking invalid timestamp;
  neither may be accepted under a missing-evidence disposition.
- Generated policy/ontology manuals now distinguish normative hard-constraint
  semantics from demonstrated runtime enforcement.
- The retained suite guide no longer calls all three replicated failures memory
  exhaustion. No experimental row was changed.

## Recheck

```bash
source .venv/bin/activate
python tools/review_validation_debt.py --output outputs/audit/current-review/validation-debt.json
python -m pytest tests/infrastructure/test_validation_debt.py
python tools/check_documentation.py
```

The complete item-level warning inventory is in the JSON report. See
[Ontology review](ONTOLOGY_REVIEW.md) for consistency commands and
[Remediation](REMEDIATION.md) for operational handling. Closing the remaining gaps
requires source evidence, prospective domain decisions or new implementation and
physical validation; changing labels or increasing timeouts is not closure.
