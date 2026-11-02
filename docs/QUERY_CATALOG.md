# Executable SPARQL Query Catalogue

This document lists every query in `queries/manifest.json`. The manifest is the executable contract and pins order, routing scope, merge strategy, privacy class, file digest, query count, and catalog digest. `ontology/catalog/queries.ttl` mirrors the catalogue as 113 `QuerySpecification` individuals. One benchmark round executes all queries once.

## Catalogue contract

- Queries: **113**
- Catalog digest: `e33627b950063a98b1ab243557d226c67bc022e05b2af350c53e7988fbeaea15`
- `single`: execute on exactly one tier or authority.
- `set_union`: execute on all selected authorities and deduplicate canonical rows.
- `boolean_or`: execute ASK queries on all selected authorities and combine results with logical OR.
- In distributed mode, Cloud receives a minimal consent-count projection; Edge authorities retain disjoint user ABox partitions.

## Categories

| Category | Queries |
|---|---:|
| `adaptation` | 8 |
| `audit_temporal` | 5 |
| `context_zones` | 6 |
| `data_lifecycle` | 8 |
| `decision` | 17 |
| `delegation` | 5 |
| `federation` | 7 |
| `identity_consent` | 18 |
| `observability` | 5 |
| `policy_governance` | 8 |
| `security_identity` | 6 |
| `semantic_schema` | 4 |
| `topology` | 4 |
| `trust` | 6 |
| `validation` | 2 |
| `wellbeing` | 4 |

## Adaptation

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `BASE-Q12` | **Scenario S2: saturation and fog candidates** — Evaluate scenario S2: saturation and fog candidates using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-17, RF-31 | P-ADAPT-01, P-NODE-02 | [base-q12.rq](../queries/core/adaptation/base-q12.rq) |
| `BASE-Q13` | **Scenario S3: edge-to-fog migration** — Evaluate scenario S3: edge-to-fog migration using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-16, RF-17, RF-31 | P-ADAPT-05, P-ADAPT-06 | [base-q13.rq](../queries/core/adaptation/base-q13.rq) |
| `BASE-Q22` | **Models and degradation events** — Evaluate models and degradation events using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-20, RF-24 | P-ADAPT-06, P-FL-08 | [base-q22.rq](../queries/core/adaptation/base-q22.rq) |
| `BASE-Q27` | **ASK: a degradation event exists** — Evaluate aSK: a degradation event exists using the declared query contract. | `ask` | `authorities` | `boolean_or` | `confidential` | RF-20 | P-ADAPT-06 | [base-q27.rq](../queries/core/adaptation/base-q27.rq) |
| `EXT-Q59` | **Adaptive action report** — Evaluate adaptive action report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-16, RF-17, RF-20, RF-66 | P-ADAPT-06, P-AUD-06 | [ext-q59.rq](../queries/core/adaptation/ext-q59.rq) |
| `EXT-Q60` | **Migration report** — Evaluate migration report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-16, RF-17 | P-ADAPT-05 | [ext-q60.rq](../queries/core/adaptation/ext-q60.rq) |
| `EXT-Q61` | **Violation: migration or delegation confused with federated learning** — Evaluate violation: migration or delegation confused with federated learning using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-16, RF-22 | P-ADAPT-05 | [ext-q61.rq](../queries/core/adaptation/ext-q61.rq) |
| `EXT-Q62` | **Degradation report** — Evaluate degradation report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-20 | P-ADAPT-02, P-ADAPT-03, P-ADAPT-06 | [ext-q62.rq](../queries/core/adaptation/ext-q62.rq) |

## Audit Temporal

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `EXT-Q70` | **Complete semantic audit chain** — Evaluate complete semantic audit chain using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-67, RNF-30 | P-AUD-07 | [ext-q70.rq](../queries/core/audit_temporal/ext-q70.rq) |
| `EXT-Q71` | **Violation: incomplete audit ticket** — Evaluate violation: incomplete audit ticket using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-54, RF-66, RNF-28, RNF-29 | P-AUD-06 | [ext-q71.rq](../queries/core/audit_temporal/ext-q71.rq) |
| `EXT-Q72` | **Violation: action without evaluation or policy justification** — Evaluate violation: action without evaluation or policy justification using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-65, RF-66, RF-41, RF-44 | P-AUD-05, P-GOV-02 | [ext-q72.rq](../queries/core/audit_temporal/ext-q72.rq) |
| `EXT-Q73` | **Temporal entity report** — Evaluate temporal entity report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RNF-35, RNF-36 | P-GOV-05, P-AUD-02 | [ext-q73.rq](../queries/core/audit_temporal/ext-q73.rq) |
| `EXT-Q74` | **Violation: missing validFrom or invalid temporal interval** — Evaluate violation: missing validFrom or invalid temporal interval using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RNF-36 | P-GOV-05 | [ext-q74.rq](../queries/core/audit_temporal/ext-q74.rq) |

## Context Zones

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `BASE-Q17` | **Scenario S7: rural areas and retention** — Evaluate scenario S7: rural areas and retention using the declared query contract. | `report` | `authorities` | `set_union` | `restricted` | RF-08, RF-27, RF-31 | P-ZONE-02, P-DATA-07 | [base-q17.rq](../queries/domain/wellbeing/context_zones/base-q17.rq) |
| `BASE-Q18` | **Scenario S8: restricted areas and local confinement** — Evaluate scenario S8: restricted areas and local confinement using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-42, RF-43, RF-60 | P-ZONE-01, P-DATA-01 | [base-q18.rq](../queries/core/context_zones/base-q18.rq) |
| `EXT-Q36` | **Restricted area report** — Evaluate restricted area report using the declared query contract. | `report` | `authority_key:http://example.org/monitoringcontinuum#UserD` | `single` | `confidential` | RF-42, RF-43 | P-ZONE-01 | [ext-q36.rq](../queries/core/context_zones/ext-q36.rq) |
| `EXT-Q37` | **Violation: external processing or transfer in restricted areas** — Evaluate violation: external processing or transfer in restricted areas using the declared query contract. | `violation` | `authorities` | `set_union` | `restricted` | RF-42, RF-43, RF-60 | P-ZONE-01, P-GOV-03, P-ZONE-04 | [ext-q37.rq](../queries/domain/wellbeing/context_zones/ext-q37.rq) |
| `EXT-Q38` | **Rural area and transmission window report** — Evaluate rural area and transmission window report using the declared query contract. | `review` | `authorities` | `set_union` | `restricted` | RF-08, RF-27 | P-ZONE-02, P-DATA-07 | [ext-q38.rq](../queries/domain/wellbeing/context_zones/ext-q38.rq) |
| `EXT-Q39` | **Conditional urban processing report** — Evaluate conditional urban processing report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-42 | P-ZONE-03, P-CONS-04 | [ext-q39.rq](../queries/core/context_zones/ext-q39.rq) |

## Data Lifecycle

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `EXT-Q23` | **External data transfer report** — Evaluate external data transfer report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-09, RF-27, RF-61 | P-DATA-02, P-DATA-03, P-DATA-10 | [ext-q23.rq](../queries/core/data_lifecycle/ext-q23.rq) |
| `EXT-Q24` | **Data context report** — Evaluate data context report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-09, RF-30 | P-DATA-10 | [ext-q24.rq](../queries/core/data_lifecycle/ext-q24.rq) |
| `EXT-Q25` | **Violation: incomplete data context** — Evaluate violation: incomplete data context using the declared query contract. | `violation` | `authorities` | `set_union` | `restricted` | RF-09 | P-DATA-10 | [ext-q25.rq](../queries/domain/wellbeing/data_lifecycle/ext-q25.rq) |
| `EXT-Q31` | **Buffer and retention report** — Evaluate buffer and retention report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-08, RNF-12 | P-DATA-05, P-DATA-07 | [ext-q31.rq](../queries/core/data_lifecycle/ext-q31.rq) |
| `EXT-Q32` | **Violation: sensitive buffer without protection at rest** — Evaluate violation: sensitive buffer without protection at rest using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RNF-15, RNF-12 | P-DATA-03, P-DATA-05 | [ext-q32.rq](../queries/core/data_lifecycle/ext-q32.rq) |
| `EXT-Q33` | **Replication and synchronization report** — Evaluate replication and synchronization report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-19, RNF-13 | P-DATA-08 | [ext-q33.rq](../queries/core/data_lifecycle/ext-q33.rq) |
| `EXT-Q34` | **Violation: replication without versioning or idempotency** — Evaluate violation: replication without versioning or idempotency using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-19, RNF-13 | P-DATA-08, P-ADAPT-08 | [ext-q34.rq](../queries/core/data_lifecycle/ext-q34.rq) |
| `EXT-Q35` | **Data criticality and priority report** — Evaluate data criticality and priority report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-28 | P-DATA-09 | [ext-q35.rq](../queries/core/data_lifecycle/ext-q35.rq) |

## Decision

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `BASE-Q04` | **Models, tiers, versions, hosts and lineage** — Evaluate models, tiers, versions, hosts and lineage using the declared query contract. | `inventory` | `authority_key:http://example.org/monitoringcontinuum#UserB` | `single` | `confidential` | RF-11, RF-12, RF-13, RF-24, RF-70 | P-FL-08, P-MODEL-01 | [base-q04.rq](../queries/core/decision/base-q04.rq) |
| `BASE-Q19` | **Operationally eligible candidates** — Evaluate operationally eligible candidates using the declared query contract. | `report` | `authorities` | `set_union` | `internal` | RF-18, RF-47, RF-48 | P-NODE-02, P-NODE-05 | [base-q19.rq](../queries/core/decision/base-q19.rq) |
| `BASE-Q21` | **Evaluation states and executed actions** — Evaluate evaluation states and executed actions using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-14, RF-15, RF-66 | P-AUD-06, P-MODEL-05 | [base-q21.rq](../queries/core/decision/base-q21.rq) |
| `BASE-Q32` | **Model counts by tier** — Evaluate model counts by tier using the declared query contract. | `dashboard` | `fog` | `single` | `internal` | RF-13, RF-68 | P-MODEL-01 | [base-q32.rq](../queries/core/decision/base-q32.rq) |
| `EXT-Q46` | **Complete model decision report** — Evaluate complete model decision report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-15, RF-51, RF-66, RF-52 | P-MODEL-01, P-MODEL-05, P-AUD-06 | [ext-q46.rq](../queries/core/decision/ext-q46.rq) |
| `EXT-Q47` | **Violation: evaluation without minimum decision fields** — Evaluate violation: evaluation without minimum decision fields using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-54, RF-66, RNF-28 | P-AUD-06 | [ext-q47.rq](../queries/core/decision/ext-q47.rq) |
| `EXT-Q48` | **Violation: unnormalized multicriteria weights** — Evaluate violation: unnormalized multicriteria weights using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-50, RF-55, RNF-34 | P-MODEL-02, P-MODEL-03 | [ext-q48.rq](../queries/core/decision/ext-q48.rq) |
| `EXT-Q49` | **Decision method and consistency report** — Evaluate decision method and consistency report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-55, RNF-33, RNF-34 | P-MODEL-04 | [ext-q49.rq](../queries/core/decision/ext-q49.rq) |
| `EXT-Q50` | **Violation: AHP evaluation without valid consistency** — Evaluate violation: AHP evaluation without valid consistency using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-55, RNF-34 | P-MODEL-04 | [ext-q50.rq](../queries/core/decision/ext-q50.rq) |
| `EXT-Q51` | **Alternatives by evaluation** — Evaluate alternatives by evaluation using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-51, RNF-29 | P-MODEL-05 | [ext-q51.rq](../queries/core/decision/ext-q51.rq) |
| `EXT-Q52` | **Review: alternatives pending recalculation** — Evaluate review: alternatives pending recalculation using the declared query contract. | `review` | `authorities` | `set_union` | `confidential` | RF-51, RNF-29, RNF-33 | P-MODEL-05 | [ext-q52.rq](../queries/core/decision/ext-q52.rq) |
| `EXT-Q53` | **Violation: invalid selected alternative** — Evaluate violation: invalid selected alternative using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-51, RF-54 | P-MODEL-05 | [ext-q53.rq](../queries/core/decision/ext-q53.rq) |
| `EXT-Q54` | **Observed model quality report** — Evaluate observed model quality report using the declared query contract. | `report` | `authorities` | `set_union` | `restricted` | RF-14, RF-29, RNF-27 | P-MODEL-08, P-OPS-05 | [ext-q54.rq](../queries/domain/wellbeing/decision/ext-q54.rq) |
| `EXT-Q55` | **Review: insufficient quality evidence** — Evaluate review: insufficient quality evidence using the declared query contract. | `review` | `authorities` | `set_union` | `confidential` | RF-14, RF-54 | P-MODEL-08 | [ext-q55.rq](../queries/core/decision/ext-q55.rq) |
| `EXT-Q56` | **Violation: cloud selected without sufficient conditions** — Evaluate violation: cloud selected without sufficient conditions using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-53, RF-52 | P-MODEL-07, P-ZONE-01, P-CONS-04 | [ext-q56.rq](../queries/core/decision/ext-q56.rq) |
| `EXT-Q57` | **Model versioning and lineage report** — Evaluate model versioning and lineage report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-24 | P-FL-08 | [ext-q57.rq](../queries/core/decision/ext-q57.rq) |
| `EXT-Q58` | **Review: rollback readiness** — Evaluate review: rollback readiness using the declared query contract. | `review` | `authorities` | `set_union` | `confidential` | RF-24 | P-FL-08 | [ext-q58.rq](../queries/core/decision/ext-q58.rq) |

## Delegation

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `BASE-Q14` | **Scenario S4: failure, delegation and degradation** — Evaluate scenario S4: failure, delegation and degradation using the declared query contract. | `report` | `authority_key:http://example.org/monitoringcontinuum#UserA` | `single` | `confidential` | RF-17, RF-20, RF-62, RF-65 | P-ADAPT-02, P-AUD-01, P-AUD-05 | [base-q14.rq](../queries/core/delegation/base-q14.rq) |
| `BASE-Q35` | **Failure, evaluation and action chain** — Evaluate failure, evaluation and action chain using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-20, RF-65, RF-67 | P-AUD-05, P-AUD-07 | [base-q35.rq](../queries/core/delegation/base-q35.rq) |
| `EXT-Q63` | **Temporary delegation report** — Evaluate temporary delegation report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-62, RF-63, RF-64 | P-AUD-01, P-AUD-02, P-AUD-03 | [ext-q63.rq](../queries/core/delegation/ext-q63.rq) |
| `EXT-Q64` | **Violation: incomplete delegation** — Evaluate violation: incomplete delegation using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-63 | P-AUD-02 | [ext-q64.rq](../queries/core/delegation/ext-q64.rq) |
| `EXT-Q65` | **Violation: delegation depth exceeds the profile** — Evaluate violation: delegation depth exceeds the profile using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RNF-14 | P-AUD-04, P-OPS-01 | [ext-q65.rq](../queries/core/delegation/ext-q65.rq) |

## Federation

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `BASE-Q16` | **Scenario S6: protected federated learning** — Evaluate scenario S6: protected federated learning using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-21, RF-22, RF-25, RF-56, RF-58 | P-FL-01, P-FL-03, P-FL-05, P-FL-07 | [base-q16.rq](../queries/core/federation/base-q16.rq) |
| `BASE-Q24` | **Federated learning chain** — Evaluate federated learning chain using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-21, RF-22, RF-25, RF-59 | P-FL-02, P-FL-04, P-FL-07 | [base-q24.rq](../queries/core/federation/base-q24.rq) |
| `BASE-Q30` | **ASK: a federated learning session includes cloud** — Evaluate aSK: a federated learning session includes cloud using the declared query contract. | `ask` | `authorities` | `boolean_or` | `confidential` | RF-22 | P-FL-01 | [base-q30.rq](../queries/core/federation/base-q30.rq) |
| `EXT-Q66` | **Federated learning session and payload report** — Evaluate federated learning session and payload report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-21, RF-22, RF-23, RF-25 | P-FL-01, P-FL-06, P-FL-07, P-CONS-06 | [ext-q66.rq](../queries/core/federation/ext-q66.rq) |
| `EXT-Q67` | **Violation: unauthorized upstream federated learning session** — Evaluate violation: unauthorized upstream federated learning session using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-21, RF-56 | P-FL-02, P-FL-03 | [ext-q67.rq](../queries/core/federation/ext-q67.rq) |
| `EXT-Q68` | **Violation: gradient without anonymization, noise or privacy mechanism** — Evaluate violation: gradient without anonymization, noise or privacy mechanism using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-57, RF-58, RNF-16, RNF-19 | P-FL-03, P-FL-05 | [ext-q68.rq](../queries/core/federation/ext-q68.rq) |
| `EXT-Q69` | **Differential privacy and epsilon accounting** — Evaluate differential privacy and epsilon accounting using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-56, RF-59, RNF-18 | P-FL-04 | [ext-q69.rq](../queries/core/federation/ext-q69.rq) |

## Identity Consent

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `BASE-Q01` | **Users, active consent and external identifiers** — Evaluate users, active consent and external identifiers using the declared query contract. | `inventory` | `authorities` | `set_union` | `confidential` | RF-01, RF-32, RF-61, RF-70 | P-CONS-01, P-DATA-02 | [base-q01.rq](../queries/core/identity_consent/base-q01.rq) |
| `BASE-Q06` | **RBAC roles and permissions** — Evaluate rBAC roles and permissions using the declared query contract. | `inventory` | `cloud` | `single` | `internal` | RF-37, RF-70 | P-CONS-05 | [base-q06.rq](../queries/core/identity_consent/base-q06.rq) |
| `BASE-Q15` | **Scenario S5: local consent** — Evaluate scenario S5: local consent using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-32, RF-36, RF-38, RF-07 | P-CONS-01, P-CONS-04, P-MODEL-06 | [base-q15.rq](../queries/core/identity_consent/base-q15.rq) |
| `BASE-Q20` | **Complete user semantic profile** — Evaluate complete user semantic profile using the declared query contract. | `report` | `authorities` | `set_union` | `restricted` | RF-02, RF-33, RF-34, RF-70 | P-CONS-02, P-CONS-03 | [base-q20.rq](../queries/domain/wellbeing/identity_consent/base-q20.rq) |
| `BASE-Q25` | **Users authorized for global federated learning** — Evaluate users authorized for global federated learning using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-21, RF-32, RF-36 | P-CONS-04, P-FL-02 | [base-q25.rq](../queries/core/identity_consent/base-q25.rq) |
| `BASE-Q28` | **ASK: an external transfer violates confinement or identity** — Evaluate aSK: an external transfer violates confinement or identity using the declared query contract. | `ask` | `authorities` | `boolean_or` | `restricted` | RF-36, RF-60, RF-61 | P-CONS-04, P-DATA-04 | [base-q28.rq](../queries/domain/wellbeing/identity_consent/base-q28.rq) |
| `BASE-Q31` | **User counts by active consent range** — Evaluate user counts by active consent range using the declared query contract. | `dashboard` | `cloud` | `single` | `internal` | RF-32, RF-68 | P-CONS-01 | [base-q31.rq](../queries/core/identity_consent/base-q31.rq) |
| `EXT-Q11` | **Consent record report** — Evaluate consent record report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-32, RF-35 | P-CONS-01, P-CONS-04 | [ext-q11.rq](../queries/core/identity_consent/ext-q11.rq) |
| `EXT-Q12` | **Semantic contract report** — Evaluate semantic contract report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-33, RF-34, RF-41 | P-CONS-02, P-CONS-03, P-GOV-02 | [ext-q12.rq](../queries/core/identity_consent/ext-q12.rq) |
| `EXT-Q13` | **Violation: incomplete consent records** — Evaluate violation: incomplete consent records using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-32, RF-35 | P-CONS-01 | [ext-q13.rq](../queries/core/identity_consent/ext-q13.rq) |
| `EXT-Q14` | **Violation: incomplete semantic contracts** — Evaluate violation: incomplete semantic contracts using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-33, RF-34 | P-CONS-02, P-CONS-03 | [ext-q14.rq](../queries/core/identity_consent/ext-q14.rq) |
| `EXT-Q15` | **Violation: overlapping contracts for a user and purpose** — Evaluate violation: overlapping contracts for a user and purpose using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-33, RNF-22 | P-CONS-02 | [ext-q15.rq](../queries/core/identity_consent/ext-q15.rq) |
| `EXT-Q16` | **Violation: active consent range without a supporting record** — Evaluate violation: active consent range without a supporting record using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-35 | P-CONS-01, P-CONS-04 | [ext-q16.rq](../queries/core/identity_consent/ext-q16.rq) |
| `EXT-Q17` | **Effective authorization report** — Evaluate effective authorization report using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-35, RF-36, RF-66 | P-CONS-04, P-GOV-03 | [ext-q17.rq](../queries/core/identity_consent/ext-q17.rq) |
| `EXT-Q18` | **Violation: incomplete effective authorization** — Evaluate violation: incomplete effective authorization using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-35, RF-36 | P-CONS-04 | [ext-q18.rq](../queries/core/identity_consent/ext-q18.rq) |
| `EXT-Q19` | **Violation: authorization exceeds consent or contract** — Evaluate violation: authorization exceeds consent or contract using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-35, RF-36 | P-CONS-04, P-GOV-03 | [ext-q19.rq](../queries/core/identity_consent/ext-q19.rq) |
| `EXT-Q20` | **Violation: evaluation without granted authorization** — Evaluate violation: evaluation without granted authorization using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-36, RF-66, RNF-28 | P-CONS-04, P-AUD-06 | [ext-q20.rq](../queries/core/identity_consent/ext-q20.rq) |
| `EXT-Q21` | **Required minimum consent range inventory** — Evaluate required minimum consent range inventory using the declared query contract. | `inventory` | `authorities` | `set_union` | `confidential` | RF-37 | P-CONS-05 | [ext-q21.rq](../queries/core/identity_consent/ext-q21.rq) |

## Observability

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `BASE-Q07` | **Node states and operational metrics** — Evaluate node states and operational metrics using the declared query contract. | `report` | `authorities` | `set_union` | `internal` | RF-05, RF-29, RF-45, RF-70 | P-NODE-01, P-NODE-03, P-OPS-05 | [base-q07.rq](../queries/core/observability/base-q07.rq) |
| `BASE-Q08` | **Saturated, unavailable or disconnected nodes** — Evaluate saturated, unavailable or disconnected nodes using the declared query contract. | `report` | `fog` | `single` | `internal` | RF-17, RF-47, RNF-12 | P-NODE-01, P-NODE-02 | [base-q08.rq](../queries/core/observability/base-q08.rq) |
| `BASE-Q10` | **Device states and transmission eligibility** — Evaluate device states and transmission eligibility using the declared query contract. | `report` | `authorities` | `set_union` | `restricted` | RF-04, RF-26, RF-27, RF-07 | P-DATA-04, P-DATA-06, P-DATA-07 | [base-q10.rq](../queries/domain/wellbeing/observability/base-q10.rq) |
| `BASE-Q26` | **ASK: a saturated node exists** — Evaluate aSK: a saturated node exists using the declared query contract. | `ask` | `fog` | `single` | `internal` | RF-05, RF-29 | P-NODE-01 | [base-q26.rq](../queries/core/observability/base-q26.rq) |
| `BASE-Q33` | **Mean resource usage by node type** — Evaluate mean resource usage by node type using the declared query contract. | `dashboard` | `authority_key:http://example.org/monitoringcontinuum#UserB` | `single` | `confidential` | RF-29, RNF-27 | P-OPS-05 | [base-q33.rq](../queries/core/observability/base-q33.rq) |

## Policy Governance

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `EXT-Q03` | **Complete policy inventory** — Evaluate complete policy inventory using the declared query contract. | `inventory` | `cloud` | `single` | `internal` | RF-39, RF-40, RF-70 | P-GOV-01, P-GOV-04 | [ext-q03.rq](../queries/core/policy_governance/ext-q03.rq) |
| `EXT-Q04` | **Complete mechanism inventory** — Evaluate complete mechanism inventory using the declared query contract. | `inventory` | `cloud` | `single` | `internal` | RV-04 | P-VAL-06 | [ext-q04.rq](../queries/core/policy_governance/ext-q04.rq) |
| `EXT-Q07` | **Relationships between policy categories** — Evaluate relationships between policy categories using the declared query contract. | `report` | `cloud` | `single` | `internal` | RNF-22, RV-04 | P-GOV-03 | [ext-q07.rq](../queries/core/policy_governance/ext-q07.rq) |
| `EXT-Q08` | **Requirement, policy and mechanism traceability** — Evaluate requirement, policy and mechanism traceability using the declared query contract. | `report` | `cloud` | `single` | `internal` | RV-04, RNF-39 | P-VAL-06 | [ext-q08.rq](../queries/core/policy_governance/ext-q08.rq) |
| `EXT-Q09` | **Review: requirements without explicit policies or mechanisms** — Evaluate review: requirements without explicit policies or mechanisms using the declared query contract. | `review` | `cloud` | `single` | `internal` | RV-04 | P-VAL-06 | [ext-q09.rq](../queries/core/policy_governance/ext-q09.rq) |
| `EXT-Q10` | **Violation: incomplete policies or mechanisms** — Evaluate violation: incomplete policies or mechanisms using the declared query contract. | `violation` | `cloud` | `single` | `internal` | RF-39, RF-40, RNF-20 | P-GOV-01, P-GOV-04 | [ext-q10.rq](../queries/core/policy_governance/ext-q10.rq) |
| `EXT-Q78` | **Policy conflict resolution report** — Evaluate policy conflict resolution report using the declared query contract. | `report` | `cloud` | `single` | `internal` | RNF-22 | P-GOV-03 | [ext-q78.rq](../queries/core/policy_governance/ext-q78.rq) |
| `EXT-Q79` | **Violation: conflicting relationship without resolution strategy** — Evaluate violation: conflicting relationship without resolution strategy using the declared query contract. | `violation` | `cloud` | `single` | `internal` | RNF-22 | P-GOV-03 | [ext-q79.rq](../queries/core/policy_governance/ext-q79.rq) |

## Security Identity

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `EXT-Q22` | **Violation: raw physiological observations outside local scope** — Evaluate violation: raw physiological observations outside local scope using the declared query contract. | `violation` | `authorities` | `set_union` | `restricted` | RF-10, RF-60, RNF-17 | P-DATA-01, P-ZONE-01 | [ext-q22.rq](../queries/domain/wellbeing/security_identity/ext-q22.rq) |
| `EXT-Q26` | **Identifier inventory** — Evaluate identifier inventory using the declared query contract. | `inventory` | `authorities` | `set_union` | `confidential` | RF-61, RNF-19 | P-DATA-02 | [ext-q26.rq](../queries/core/security_identity/ext-q26.rq) |
| `EXT-Q27` | **Violation: external transfer without a safe identifier** — Evaluate violation: external transfer without a safe identifier using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-61, RNF-17 | P-DATA-02 | [ext-q27.rq](../queries/core/security_identity/ext-q27.rq) |
| `EXT-Q28` | **Violation: direct identifiers in external flows** — Evaluate violation: direct identifiers in external flows using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-61, RNF-17 | P-DATA-02 | [ext-q28.rq](../queries/core/security_identity/ext-q28.rq) |
| `EXT-Q29` | **Encryption baseline report** — Evaluate encryption baseline report using the declared query contract. | `report` | `cloud` | `single` | `internal` | RNF-15 | P-DATA-03 | [ext-q29.rq](../queries/core/security_identity/ext-q29.rq) |
| `EXT-Q30` | **Violation: sensitive transfer without encryption in transit** — Evaluate violation: sensitive transfer without encryption in transit using the declared query contract. | `violation` | `cloud` | `single` | `internal` | RNF-15 | P-DATA-03 | [ext-q30.rq](../queries/core/security_identity/ext-q30.rq) |

## Semantic Schema

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `EXT-Q01` | **Version and release artifact inventory** — Evaluate version and release artifact inventory using the declared query contract. | `inventory` | `cloud` | `single` | `internal` | RF-68, RNF-39, RV-01, RV-03 | P-VAL-01, P-VAL-04 | [ext-q01.rq](../queries/core/semantic_schema/ext-q01.rq) |
| `EXT-Q02` | **Functional, non-functional and validation requirement coverage** — Evaluate functional, non-functional and validation requirement coverage using the declared query contract. | `dashboard` | `cloud` | `single` | `internal` | RV-04, RF-68 | P-VAL-06 | [ext-q02.rq](../queries/core/semantic_schema/ext-q02.rq) |
| `EXT-Q05` | **Scenario S1-S17 inventory** — Evaluate scenario S1-S17 inventory using the declared query contract. | `inventory` | `cloud` | `single` | `internal` | RF-31, RF-72, RV-03 | P-VAL-07 | [ext-q05.rq](../queries/core/semantic_schema/ext-q05.rq) |
| `EXT-Q06` | **Policy categories** — Evaluate policy categories using the declared query contract. | `inventory` | `cloud` | `single` | `internal` | RF-39, RF-40 | P-GOV-01 | [ext-q06.rq](../queries/core/semantic_schema/ext-q06.rq) |

## Topology

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `BASE-Q02` | **Compute nodes, types and elasticity** — Evaluate compute nodes, types and elasticity using the declared query contract. | `inventory` | `authority_key:http://example.org/monitoringcontinuum#UserB` | `single` | `confidential` | RF-02, RF-05, RF-70 | P-OPS-02, P-OPS-03 | [base-q02.rq](../queries/core/topology/base-q02.rq) |
| `BASE-Q23` | **User-node relationships and distance** — Evaluate user-node relationships and distance using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-02, RF-03, RF-18 | P-NODE-02 | [base-q23.rq](../queries/core/topology/base-q23.rq) |
| `BASE-Q29` | **ASK: fog or cloud elastic capacity exists** — Evaluate aSK: fog or cloud elastic capacity exists using the declared query contract. | `ask` | `fog` | `single` | `internal` | RNF-07 | P-OPS-02 | [base-q29.rq](../queries/core/topology/base-q29.rq) |
| `BASE-Q34` | **Nodes covering restricted areas** — Evaluate nodes covering restricted areas using the declared query contract. | `report` | `fog` | `single` | `internal` | RF-42, RF-43 | P-ZONE-01 | [base-q34.rq](../queries/core/topology/base-q34.rq) |

## Trust

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `EXT-Q40` | **Node state and reproducible trust report** — Evaluate node state and reproducible trust report using the declared query contract. | `report` | `authorities` | `set_union` | `internal` | RF-45, RF-49, RNF-32 | P-NODE-03, P-NODE-04 | [ext-q40.rq](../queries/core/trust/ext-q40.rq) |
| `EXT-Q41` | **Violation: node state without eligibility fields** — Evaluate violation: node state without eligibility fields using the declared query contract. | `violation` | `fog` | `single` | `internal` | RF-05, RF-47 | P-NODE-01, P-NODE-02 | [ext-q41.rq](../queries/core/trust/ext-q41.rq) |
| `EXT-Q42` | **Eligible candidates ranked by trust** — Evaluate eligible candidates ranked by trust using the declared query contract. | `report` | `authorities` | `set_union` | `internal` | RF-47, RF-48 | P-NODE-02, P-NODE-05, P-MODEL-03 | [ext-q42.rq](../queries/core/trust/ext-q42.rq) |
| `EXT-Q43` | **Review: trust assessment is not fully reproducible** — Evaluate review: trust assessment is not fully reproducible using the declared query contract. | `review` | `authorities` | `set_union` | `internal` | RF-49, RNF-32 | P-NODE-03 | [ext-q43.rq](../queries/core/trust/ext-q43.rq) |
| `EXT-Q44` | **External trust used in evaluation** — Evaluate external trust used in evaluation using the declared query contract. | `report` | `authorities` | `set_union` | `confidential` | RF-46, RF-55 | P-MODEL-03, P-NODE-05 | [ext-q44.rq](../queries/core/trust/ext-q44.rq) |
| `EXT-Q45` | **Violation: explicitly ineligible adaptive destination** — Evaluate violation: explicitly ineligible adaptive destination using the declared query contract. | `violation` | `authorities` | `set_union` | `confidential` | RF-18, RF-48 | P-ADAPT-04, P-ADAPT-07 | [ext-q45.rq](../queries/core/trust/ext-q45.rq) |

## Validation

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `EXT-Q76` | **Review: incomplete acceptance profile** — Evaluate review: incomplete acceptance profile using the declared query contract. | `review` | `cloud` | `single` | `internal` | RNF-01, RNF-02, RNF-04, RNF-05, RNF-06, RNF-08, RNF-09, RNF-14, RNF-21, RNF-34 | P-OPS-01, P-VAL-03 | [ext-q76.rq](../queries/core/validation/ext-q76.rq) |
| `EXT-Q77` | **Review: reproducible campaign readiness** — Evaluate review: reproducible campaign readiness using the declared query contract. | `review` | `cloud` | `single` | `internal` | RF-71, RF-72, RNF-39, RV-02, RV-03 | P-VAL-03, P-VAL-04, P-VAL-07 | [ext-q77.rq](../queries/core/validation/ext-q77.rq) |

## Wellbeing

| ID | Title and purpose | Kind | Scope | Merge | Privacy | Requirements | Policies | Source |
|---|---|---|---|---|---|---|---|---|
| `BASE-Q03` | **Wearables associated with users** — Evaluate wearables associated with users using the declared query contract. | `inventory` | `authorities` | `set_union` | `restricted` | RF-01, RF-70 | P-INT-02 | [base-q03.rq](../queries/domain/wellbeing/wellbeing/base-q03.rq) |
| `BASE-Q05` | **Physiological sensors and host devices** — Evaluate physiological sensors and host devices using the declared query contract. | `inventory` | `authorities` | `set_union` | `restricted` | RF-06, RNF-25, RF-70 | P-INT-01 | [base-q05.rq](../queries/domain/wellbeing/wellbeing/base-q05.rq) |
| `BASE-Q09` | **User states, mobility and stress** — Evaluate user states, mobility and stress using the declared query contract. | `report` | `authorities` | `set_union` | `restricted` | RF-03, RF-30, RNF-35 | P-GOV-05, P-OPS-05 | [base-q09.rq](../queries/domain/wellbeing/wellbeing/base-q09.rq) |
| `BASE-Q11` | **Scenario S1: normal operation** — Evaluate scenario S1: normal operation using the declared query contract. | `report` | `authority_key:http://example.org/monitoringcontinuum#UserA` | `single` | `confidential` | RF-31, RF-72 | P-VAL-07 | [base-q11.rq](../queries/core/wellbeing/base-q11.rq) |
