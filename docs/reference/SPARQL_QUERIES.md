# SPARQL query battery

> Generated reference for release v3.0.0. Do not edit individual
> entries by hand. Regenerate with
> `.venv/bin/python tools/generate_reference_docs.py`.

Canonical source: `queries/catalog.csv and queries/**/*.rq`.

The battery contains 35 BASE queries and 80 EXT queries. Every
entry below is executed by the validation gate and by cumulative
and scalability benchmarks unless a scientific experiment
explicitly selects a subset.

## Interpretation

- `inventory`: Returns the resources that make up the declared inventory.
- `report`: Returns explanatory evidence; rows are not violations by themselves.
- `review`: Returns configuration gaps or evidence that requires human review.
- `violation`: Must return zero rows after all validation preconditions pass.
- `ASK`: Returns a Boolean operational assertion defined by the query.
- `dashboard`: Returns aggregate coverage or migration-debt indicators.

A zero-row violation result is evidence only after `EXT-Q01`,
`EXT-Q02`, `EXT-Q05`, `EXT-Q76` and `EXT-Q77` establish release
identity, coverage, scenarios, acceptance parameters and campaign
readiness. `EXT-Q76` and `EXT-Q77` are review gates and may
legitimately report pending configuration.

## Run the battery

```bash
.venv/bin/continuum-bench validate
.venv/bin/continuum-bench benchmark cumulative --python-only
.venv/bin/continuum-bench benchmark scalability --python-only
```

## Complete catalog

### BASE-Q01 — identity_consent / inventory

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/base-q01.rq`](../../queries/core/identity_consent/base-q01.rq).

- Order: `1`
- Tier: `core`
- Category: `identity_consent`
- Kind: `inventory`
- Expectation: non_empty; reference count `4`
- Requirements: `RF-01`, `RF-32`, `RF-61`, `RF-70`
- Policies: `P-CONS-01`, `P-DATA-02`

### BASE-Q02 — topology / inventory

Evaluates continuum node, location and connectivity structure using the executable query in [`queries/core/topology/base-q02.rq`](../../queries/core/topology/base-q02.rq).

- Order: `2`
- Tier: `core`
- Category: `topology`
- Kind: `inventory`
- Expectation: non_empty; reference count `8`
- Requirements: `RF-02`, `RF-05`, `RF-70`
- Policies: `P-OPS-02`, `P-OPS-03`

### BASE-Q03 — wellbeing / inventory

Evaluates wearable, physiological, stress and sleep concepts using the executable query in [`queries/domain/wellbeing/wellbeing/base-q03.rq`](../../queries/domain/wellbeing/wellbeing/base-q03.rq).

- Order: `3`
- Tier: `domain`
- Category: `wellbeing`
- Kind: `inventory`
- Expectation: non_empty; reference count `4`
- Requirements: `RF-01`, `RF-70`
- Policies: `P-INT-02`

### BASE-Q04 — decision / inventory

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/base-q04.rq`](../../queries/core/decision/base-q04.rq).

- Order: `4`
- Tier: `core`
- Category: `decision`
- Kind: `inventory`
- Expectation: non_empty; reference count `7`
- Requirements: `RF-11`, `RF-12`, `RF-13`, `RF-24`, `RF-70`
- Policies: `P-FL-08`, `P-MODEL-01`

### BASE-Q05 — wellbeing / inventory

Evaluates wearable, physiological, stress and sleep concepts using the executable query in [`queries/domain/wellbeing/wellbeing/base-q05.rq`](../../queries/domain/wellbeing/wellbeing/base-q05.rq).

- Order: `5`
- Tier: `domain`
- Category: `wellbeing`
- Kind: `inventory`
- Expectation: non_empty; reference count `5`
- Requirements: `RF-06`, `RNF-25`, `RF-70`
- Policies: `P-INT-01`

### BASE-Q06 — identity_consent / inventory

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/base-q06.rq`](../../queries/core/identity_consent/base-q06.rq).

- Order: `6`
- Tier: `core`
- Category: `identity_consent`
- Kind: `inventory`
- Expectation: non_empty; reference count `10`
- Requirements: `RF-37`, `RF-70`
- Policies: `P-CONS-05`

### BASE-Q07 — observability / report

Evaluates device, user and node operational state using the executable query in [`queries/core/observability/base-q07.rq`](../../queries/core/observability/base-q07.rq).

- Order: `7`
- Tier: `core`
- Category: `observability`
- Kind: `report`
- Expectation: non_empty; reference count `7`
- Requirements: `RF-05`, `RF-29`, `RF-45`, `RF-70`
- Policies: `P-NODE-01`, `P-NODE-03`, `P-OPS-05`

### BASE-Q08 — observability / report

Evaluates device, user and node operational state using the executable query in [`queries/core/observability/base-q08.rq`](../../queries/core/observability/base-q08.rq).

- Order: `8`
- Tier: `core`
- Category: `observability`
- Kind: `report`
- Expectation: non_empty; reference count `2`
- Requirements: `RF-17`, `RF-47`, `RNF-12`
- Policies: `P-NODE-01`, `P-NODE-02`

### BASE-Q09 — wellbeing / report

Evaluates wearable, physiological, stress and sleep concepts using the executable query in [`queries/domain/wellbeing/wellbeing/base-q09.rq`](../../queries/domain/wellbeing/wellbeing/base-q09.rq).

- Order: `9`
- Tier: `domain`
- Category: `wellbeing`
- Kind: `report`
- Expectation: non_empty; reference count `6`
- Requirements: `RF-03`, `RF-30`, `RNF-35`
- Policies: `P-GOV-05`, `P-OPS-05`

### BASE-Q10 — observability / report

Evaluates device, user and node operational state using the executable query in [`queries/domain/wellbeing/observability/base-q10.rq`](../../queries/domain/wellbeing/observability/base-q10.rq).

- Order: `10`
- Tier: `domain`
- Category: `observability`
- Kind: `report`
- Expectation: non_empty; reference count `4`
- Requirements: `RF-04`, `RF-26`, `RF-27`
- Policies: `P-DATA-04`, `P-DATA-06`, `P-DATA-07`

### BASE-Q11 — wellbeing / report

Evaluates wearable, physiological, stress and sleep concepts using the executable query in [`queries/core/wellbeing/base-q11.rq`](../../queries/core/wellbeing/base-q11.rq).

- Order: `11`
- Tier: `core`
- Category: `wellbeing`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RF-31`, `RF-72`
- Policies: `P-VAL-07`

### BASE-Q12 — adaptation / report

Evaluates migration, degradation and adaptive actions using the executable query in [`queries/core/adaptation/base-q12.rq`](../../queries/core/adaptation/base-q12.rq).

- Order: `12`
- Tier: `core`
- Category: `adaptation`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RF-17`, `RF-31`
- Policies: `P-ADAPT-01`, `P-NODE-02`

### BASE-Q13 — adaptation / report

Evaluates migration, degradation and adaptive actions using the executable query in [`queries/core/adaptation/base-q13.rq`](../../queries/core/adaptation/base-q13.rq).

- Order: `13`
- Tier: `core`
- Category: `adaptation`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RF-16`, `RF-17`, `RF-31`
- Policies: `P-ADAPT-05`, `P-ADAPT-06`

### BASE-Q14 — delegation / report

Evaluates temporary delegation and recovery using the executable query in [`queries/core/delegation/base-q14.rq`](../../queries/core/delegation/base-q14.rq).

- Order: `14`
- Tier: `core`
- Category: `delegation`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RF-17`, `RF-20`, `RF-62`, `RF-65`
- Policies: `P-ADAPT-02`, `P-AUD-01`, `P-AUD-05`

### BASE-Q15 — identity_consent / report

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/base-q15.rq`](../../queries/core/identity_consent/base-q15.rq).

- Order: `15`
- Tier: `core`
- Category: `identity_consent`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RF-32`, `RF-36`, `RF-38`
- Policies: `P-CONS-01`, `P-CONS-04`, `P-MODEL-06`

### BASE-Q16 — federation / report

Evaluates federated learning and differential privacy using the executable query in [`queries/core/federation/base-q16.rq`](../../queries/core/federation/base-q16.rq).

- Order: `16`
- Tier: `core`
- Category: `federation`
- Kind: `report`
- Expectation: non_empty; reference count `3`
- Requirements: `RF-21`, `RF-22`, `RF-25`, `RF-56`, `RF-58`
- Policies: `P-FL-01`, `P-FL-03`, `P-FL-05`, `P-FL-07`

### BASE-Q17 — context_zones / report

Evaluates zone-aware and georestricted processing using the executable query in [`queries/domain/wellbeing/context_zones/base-q17.rq`](../../queries/domain/wellbeing/context_zones/base-q17.rq).

- Order: `17`
- Tier: `domain`
- Category: `context_zones`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RF-08`, `RF-27`, `RF-31`
- Policies: `P-ZONE-02`, `P-DATA-07`

### BASE-Q18 — context_zones / report

Evaluates zone-aware and georestricted processing using the executable query in [`queries/core/context_zones/base-q18.rq`](../../queries/core/context_zones/base-q18.rq).

- Order: `18`
- Tier: `core`
- Category: `context_zones`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RF-42`, `RF-43`, `RF-60`
- Policies: `P-ZONE-01`, `P-DATA-01`

### BASE-Q19 — decision / report

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/base-q19.rq`](../../queries/core/decision/base-q19.rq).

- Order: `19`
- Tier: `core`
- Category: `decision`
- Kind: `report`
- Expectation: non_empty; reference count `4`
- Requirements: `RF-18`, `RF-47`, `RF-48`
- Policies: `P-NODE-02`, `P-NODE-05`

### BASE-Q20 — identity_consent / report

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/domain/wellbeing/identity_consent/base-q20.rq`](../../queries/domain/wellbeing/identity_consent/base-q20.rq).

- Order: `20`
- Tier: `domain`
- Category: `identity_consent`
- Kind: `report`
- Expectation: non_empty; reference count `4`
- Requirements: `RF-02`, `RF-33`, `RF-34`, `RF-70`
- Policies: `P-CONS-02`, `P-CONS-03`

### BASE-Q21 — decision / report

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/base-q21.rq`](../../queries/core/decision/base-q21.rq).

- Order: `21`
- Tier: `core`
- Category: `decision`
- Kind: `report`
- Expectation: non_empty; reference count `11`
- Requirements: `RF-14`, `RF-15`, `RF-66`
- Policies: `P-AUD-06`, `P-MODEL-05`

### BASE-Q22 — adaptation / report

Evaluates migration, degradation and adaptive actions using the executable query in [`queries/core/adaptation/base-q22.rq`](../../queries/core/adaptation/base-q22.rq).

- Order: `22`
- Tier: `core`
- Category: `adaptation`
- Kind: `report`
- Expectation: non_empty; reference count `3`
- Requirements: `RF-20`, `RF-24`
- Policies: `P-ADAPT-06`, `P-FL-08`

### BASE-Q23 — topology / report

Evaluates continuum node, location and connectivity structure using the executable query in [`queries/core/topology/base-q23.rq`](../../queries/core/topology/base-q23.rq).

- Order: `23`
- Tier: `core`
- Category: `topology`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RF-02`, `RF-03`, `RF-18`
- Policies: `P-NODE-02`

### BASE-Q24 — federation / report

Evaluates federated learning and differential privacy using the executable query in [`queries/core/federation/base-q24.rq`](../../queries/core/federation/base-q24.rq).

- Order: `24`
- Tier: `core`
- Category: `federation`
- Kind: `report`
- Expectation: non_empty; reference count `5`
- Requirements: `RF-21`, `RF-22`, `RF-25`, `RF-59`
- Policies: `P-FL-02`, `P-FL-04`, `P-FL-07`

### BASE-Q25 — identity_consent / report

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/base-q25.rq`](../../queries/core/identity_consent/base-q25.rq).

- Order: `25`
- Tier: `core`
- Category: `identity_consent`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RF-21`, `RF-32`, `RF-36`
- Policies: `P-CONS-04`, `P-FL-02`

### BASE-Q26 — observability / ask

Evaluates device, user and node operational state using the executable query in [`queries/core/observability/base-q26.rq`](../../queries/core/observability/base-q26.rq).

- Order: `26`
- Tier: `core`
- Category: `observability`
- Kind: `ask`
- Expectation: true; reference count `1`; reference ASK `true`
- Requirements: `RF-05`, `RF-29`
- Policies: `P-NODE-01`

### BASE-Q27 — adaptation / ask

Evaluates migration, degradation and adaptive actions using the executable query in [`queries/core/adaptation/base-q27.rq`](../../queries/core/adaptation/base-q27.rq).

- Order: `27`
- Tier: `core`
- Category: `adaptation`
- Kind: `ask`
- Expectation: true; reference count `1`; reference ASK `true`
- Requirements: `RF-20`
- Policies: `P-ADAPT-06`

### BASE-Q28 — identity_consent / ask

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/domain/wellbeing/identity_consent/base-q28.rq`](../../queries/domain/wellbeing/identity_consent/base-q28.rq).

- Order: `28`
- Tier: `domain`
- Category: `identity_consent`
- Kind: `ask`
- Expectation: false; reference count `0`; reference ASK `false`
- Requirements: `RF-36`, `RF-60`, `RF-61`
- Policies: `P-CONS-04`, `P-DATA-04`

### BASE-Q29 — topology / ask

Evaluates continuum node, location and connectivity structure using the executable query in [`queries/core/topology/base-q29.rq`](../../queries/core/topology/base-q29.rq).

- Order: `29`
- Tier: `core`
- Category: `topology`
- Kind: `ask`
- Expectation: true; reference count `1`; reference ASK `true`
- Requirements: `RNF-07`
- Policies: `P-OPS-02`

### BASE-Q30 — federation / ask

Evaluates federated learning and differential privacy using the executable query in [`queries/core/federation/base-q30.rq`](../../queries/core/federation/base-q30.rq).

- Order: `30`
- Tier: `core`
- Category: `federation`
- Kind: `ask`
- Expectation: true; reference count `1`; reference ASK `true`
- Requirements: `RF-22`
- Policies: `P-FL-01`

### BASE-Q31 — identity_consent / dashboard

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/base-q31.rq`](../../queries/core/identity_consent/base-q31.rq).

- Order: `31`
- Tier: `core`
- Category: `identity_consent`
- Kind: `dashboard`
- Expectation: non_empty; reference count `3`
- Requirements: `RF-32`, `RF-68`
- Policies: `P-CONS-01`

### BASE-Q32 — decision / dashboard

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/base-q32.rq`](../../queries/core/decision/base-q32.rq).

- Order: `32`
- Tier: `core`
- Category: `decision`
- Kind: `dashboard`
- Expectation: non_empty; reference count `4`
- Requirements: `RF-13`, `RF-68`
- Policies: `P-MODEL-01`

### BASE-Q33 — observability / dashboard

Evaluates device, user and node operational state using the executable query in [`queries/core/observability/base-q33.rq`](../../queries/core/observability/base-q33.rq).

- Order: `33`
- Tier: `core`
- Category: `observability`
- Kind: `dashboard`
- Expectation: non_empty; reference count `5`
- Requirements: `RF-29`, `RNF-27`
- Policies: `P-OPS-05`

### BASE-Q34 — topology / report

Evaluates continuum node, location and connectivity structure using the executable query in [`queries/core/topology/base-q34.rq`](../../queries/core/topology/base-q34.rq).

- Order: `34`
- Tier: `core`
- Category: `topology`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RF-42`, `RF-43`
- Policies: `P-ZONE-01`

### BASE-Q35 — delegation / report

Evaluates temporary delegation and recovery using the executable query in [`queries/core/delegation/base-q35.rq`](../../queries/core/delegation/base-q35.rq).

- Order: `35`
- Tier: `core`
- Category: `delegation`
- Kind: `report`
- Expectation: non_empty; reference count `86`
- Requirements: `RF-20`, `RF-65`, `RF-67`
- Policies: `P-AUD-05`, `P-AUD-07`

### EXT-Q01 — semantic_schema / inventory

Evaluates release artefacts and semantic schema coverage using the executable query in [`queries/core/semantic_schema/ext-q01.rq`](../../queries/core/semantic_schema/ext-q01.rq).

- Order: `36`
- Tier: `core`
- Category: `semantic_schema`
- Kind: `inventory`
- Expectation: non_empty; reference count `6`
- Requirements: `RF-68`, `RNF-39`, `RV-01`, `RV-03`
- Policies: `P-VAL-01`, `P-VAL-04`

### EXT-Q02 — semantic_schema / dashboard

Evaluates release artefacts and semantic schema coverage using the executable query in [`queries/core/semantic_schema/ext-q02.rq`](../../queries/core/semantic_schema/ext-q02.rq).

- Order: `37`
- Tier: `core`
- Category: `semantic_schema`
- Kind: `dashboard`
- Expectation: non_empty; reference count `3`
- Requirements: `RV-04`, `RF-68`
- Policies: `P-VAL-06`

### EXT-Q03 — policy_governance / inventory

Evaluates policy inventory, precedence and traceability using the executable query in [`queries/core/policy_governance/ext-q03.rq`](../../queries/core/policy_governance/ext-q03.rq).

- Order: `38`
- Tier: `core`
- Category: `policy_governance`
- Kind: `inventory`
- Expectation: non_empty; reference count `79`
- Requirements: `RF-39`, `RF-40`, `RF-70`
- Policies: `P-GOV-01`, `P-GOV-04`

### EXT-Q04 — policy_governance / inventory

Evaluates policy inventory, precedence and traceability using the executable query in [`queries/core/policy_governance/ext-q04.rq`](../../queries/core/policy_governance/ext-q04.rq).

- Order: `39`
- Tier: `core`
- Category: `policy_governance`
- Kind: `inventory`
- Expectation: non_empty; reference count `55`
- Requirements: `RV-04`
- Policies: `P-VAL-06`

### EXT-Q05 — semantic_schema / inventory

Evaluates release artefacts and semantic schema coverage using the executable query in [`queries/core/semantic_schema/ext-q05.rq`](../../queries/core/semantic_schema/ext-q05.rq).

- Order: `40`
- Tier: `core`
- Category: `semantic_schema`
- Kind: `inventory`
- Expectation: non_empty; reference count `17`
- Requirements: `RF-31`, `RF-72`, `RV-03`
- Policies: `P-VAL-07`

### EXT-Q06 — semantic_schema / inventory

Evaluates release artefacts and semantic schema coverage using the executable query in [`queries/core/semantic_schema/ext-q06.rq`](../../queries/core/semantic_schema/ext-q06.rq).

- Order: `41`
- Tier: `core`
- Category: `semantic_schema`
- Kind: `inventory`
- Expectation: non_empty; reference count `12`
- Requirements: `RF-39`, `RF-40`
- Policies: `P-GOV-01`

### EXT-Q07 — policy_governance / report

Evaluates policy inventory, precedence and traceability using the executable query in [`queries/core/policy_governance/ext-q07.rq`](../../queries/core/policy_governance/ext-q07.rq).

- Order: `42`
- Tier: `core`
- Category: `policy_governance`
- Kind: `report`
- Expectation: non_empty; reference count `67`
- Requirements: `RNF-22`, `RV-04`
- Policies: `P-GOV-03`

### EXT-Q08 — policy_governance / report

Evaluates policy inventory, precedence and traceability using the executable query in [`queries/core/policy_governance/ext-q08.rq`](../../queries/core/policy_governance/ext-q08.rq).

- Order: `43`
- Tier: `core`
- Category: `policy_governance`
- Kind: `report`
- Expectation: non_empty; reference count `1089`
- Requirements: `RV-04`, `RNF-39`
- Policies: `P-VAL-06`

### EXT-Q09 — policy_governance / review

Evaluates policy inventory, precedence and traceability using the executable query in [`queries/core/policy_governance/ext-q09.rq`](../../queries/core/policy_governance/ext-q09.rq).

- Order: `44`
- Tier: `core`
- Category: `policy_governance`
- Kind: `review`
- Expectation: any; reference count `6`
- Requirements: `RV-04`
- Policies: `P-VAL-06`

### EXT-Q10 — policy_governance / violation

Evaluates policy inventory, precedence and traceability using the executable query in [`queries/core/policy_governance/ext-q10.rq`](../../queries/core/policy_governance/ext-q10.rq).

- Order: `45`
- Tier: `core`
- Category: `policy_governance`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-39`, `RF-40`, `RNF-20`
- Policies: `P-GOV-01`, `P-GOV-04`

### EXT-Q11 — identity_consent / report

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/ext-q11.rq`](../../queries/core/identity_consent/ext-q11.rq).

- Order: `46`
- Tier: `core`
- Category: `identity_consent`
- Kind: `report`
- Expectation: non_empty; reference count `25`
- Requirements: `RF-32`, `RF-35`
- Policies: `P-CONS-01`, `P-CONS-04`

### EXT-Q12 — identity_consent / report

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/ext-q12.rq`](../../queries/core/identity_consent/ext-q12.rq).

- Order: `47`
- Tier: `core`
- Category: `identity_consent`
- Kind: `report`
- Expectation: non_empty; reference count `28`
- Requirements: `RF-33`, `RF-34`
- Policies: `P-CONS-02`, `P-CONS-03`

### EXT-Q13 — identity_consent / violation

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/ext-q13.rq`](../../queries/core/identity_consent/ext-q13.rq).

- Order: `48`
- Tier: `core`
- Category: `identity_consent`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-32`, `RF-35`
- Policies: `P-CONS-01`

### EXT-Q14 — identity_consent / violation

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/ext-q14.rq`](../../queries/core/identity_consent/ext-q14.rq).

- Order: `49`
- Tier: `core`
- Category: `identity_consent`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-33`, `RF-34`
- Policies: `P-CONS-02`, `P-CONS-03`

### EXT-Q15 — identity_consent / violation

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/ext-q15.rq`](../../queries/core/identity_consent/ext-q15.rq).

- Order: `50`
- Tier: `core`
- Category: `identity_consent`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-33`, `RNF-22`
- Policies: `P-CONS-02`

### EXT-Q16 — identity_consent / violation

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/ext-q16.rq`](../../queries/core/identity_consent/ext-q16.rq).

- Order: `51`
- Tier: `core`
- Category: `identity_consent`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-35`
- Policies: `P-CONS-01`, `P-CONS-04`

### EXT-Q17 — identity_consent / report

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/ext-q17.rq`](../../queries/core/identity_consent/ext-q17.rq).

- Order: `52`
- Tier: `core`
- Category: `identity_consent`
- Kind: `report`
- Expectation: non_empty; reference count `8`
- Requirements: `RF-35`, `RF-36`, `RF-66`
- Policies: `P-CONS-04`, `P-GOV-03`

### EXT-Q18 — identity_consent / violation

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/ext-q18.rq`](../../queries/core/identity_consent/ext-q18.rq).

- Order: `53`
- Tier: `core`
- Category: `identity_consent`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-35`, `RF-36`
- Policies: `P-CONS-04`

### EXT-Q19 — identity_consent / violation

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/ext-q19.rq`](../../queries/core/identity_consent/ext-q19.rq).

- Order: `54`
- Tier: `core`
- Category: `identity_consent`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-35`, `RF-36`
- Policies: `P-CONS-04`, `P-GOV-03`

### EXT-Q20 — identity_consent / violation

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/ext-q20.rq`](../../queries/core/identity_consent/ext-q20.rq).

- Order: `55`
- Tier: `core`
- Category: `identity_consent`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-36`, `RF-66`, `RNF-28`
- Policies: `P-CONS-04`, `P-AUD-06`

### EXT-Q21 — identity_consent / inventory

Evaluates identity, consent, contracts and authorization using the executable query in [`queries/core/identity_consent/ext-q21.rq`](../../queries/core/identity_consent/ext-q21.rq).

- Order: `56`
- Tier: `core`
- Category: `identity_consent`
- Kind: `inventory`
- Expectation: non_empty; reference count `11`
- Requirements: `RF-37`
- Policies: `P-CONS-05`

### EXT-Q22 — security_identity / violation

Evaluates identifiers, encryption and protected transfer using the executable query in [`queries/domain/wellbeing/security_identity/ext-q22.rq`](../../queries/domain/wellbeing/security_identity/ext-q22.rq).

- Order: `57`
- Tier: `domain`
- Category: `security_identity`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-10`, `RF-60`, `RNF-17`
- Policies: `P-DATA-01`, `P-ZONE-01`

### EXT-Q23 — data_lifecycle / report

Evaluates data context, buffering, replication and transmission using the executable query in [`queries/core/data_lifecycle/ext-q23.rq`](../../queries/core/data_lifecycle/ext-q23.rq).

- Order: `58`
- Tier: `core`
- Category: `data_lifecycle`
- Kind: `report`
- Expectation: non_empty; reference count `3`
- Requirements: `RF-09`, `RF-27`, `RF-61`
- Policies: `P-DATA-02`, `P-DATA-03`, `P-DATA-10`

### EXT-Q24 — data_lifecycle / report

Evaluates data context, buffering, replication and transmission using the executable query in [`queries/core/data_lifecycle/ext-q24.rq`](../../queries/core/data_lifecycle/ext-q24.rq).

- Order: `59`
- Tier: `core`
- Category: `data_lifecycle`
- Kind: `report`
- Expectation: non_empty; reference count `2`
- Requirements: `RF-09`, `RF-30`
- Policies: `P-DATA-10`

### EXT-Q25 — data_lifecycle / violation

Evaluates data context, buffering, replication and transmission using the executable query in [`queries/domain/wellbeing/data_lifecycle/ext-q25.rq`](../../queries/domain/wellbeing/data_lifecycle/ext-q25.rq).

- Order: `60`
- Tier: `domain`
- Category: `data_lifecycle`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-09`
- Policies: `P-DATA-10`

### EXT-Q26 — security_identity / inventory

Evaluates identifiers, encryption and protected transfer using the executable query in [`queries/core/security_identity/ext-q26.rq`](../../queries/core/security_identity/ext-q26.rq).

- Order: `61`
- Tier: `core`
- Category: `security_identity`
- Kind: `inventory`
- Expectation: non_empty; reference count `4`
- Requirements: `RF-61`, `RNF-19`
- Policies: `P-DATA-02`

### EXT-Q27 — security_identity / violation

Evaluates identifiers, encryption and protected transfer using the executable query in [`queries/core/security_identity/ext-q27.rq`](../../queries/core/security_identity/ext-q27.rq).

- Order: `62`
- Tier: `core`
- Category: `security_identity`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-61`, `RNF-17`
- Policies: `P-DATA-02`

### EXT-Q28 — security_identity / violation

Evaluates identifiers, encryption and protected transfer using the executable query in [`queries/core/security_identity/ext-q28.rq`](../../queries/core/security_identity/ext-q28.rq).

- Order: `63`
- Tier: `core`
- Category: `security_identity`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-61`, `RNF-17`
- Policies: `P-DATA-02`

### EXT-Q29 — security_identity / report

Evaluates identifiers, encryption and protected transfer using the executable query in [`queries/core/security_identity/ext-q29.rq`](../../queries/core/security_identity/ext-q29.rq).

- Order: `64`
- Tier: `core`
- Category: `security_identity`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RNF-15`
- Policies: `P-DATA-03`

### EXT-Q30 — security_identity / violation

Evaluates identifiers, encryption and protected transfer using the executable query in [`queries/core/security_identity/ext-q30.rq`](../../queries/core/security_identity/ext-q30.rq).

- Order: `65`
- Tier: `core`
- Category: `security_identity`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RNF-15`
- Policies: `P-DATA-03`

### EXT-Q31 — data_lifecycle / report

Evaluates data context, buffering, replication and transmission using the executable query in [`queries/core/data_lifecycle/ext-q31.rq`](../../queries/core/data_lifecycle/ext-q31.rq).

- Order: `66`
- Tier: `core`
- Category: `data_lifecycle`
- Kind: `report`
- Expectation: any; reference count `0`
- Requirements: `RF-08`, `RNF-12`
- Policies: `P-DATA-05`, `P-DATA-07`

### EXT-Q32 — data_lifecycle / violation

Evaluates data context, buffering, replication and transmission using the executable query in [`queries/core/data_lifecycle/ext-q32.rq`](../../queries/core/data_lifecycle/ext-q32.rq).

- Order: `67`
- Tier: `core`
- Category: `data_lifecycle`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RNF-15`, `RNF-12`
- Policies: `P-DATA-03`, `P-DATA-05`

### EXT-Q33 — data_lifecycle / report

Evaluates data context, buffering, replication and transmission using the executable query in [`queries/core/data_lifecycle/ext-q33.rq`](../../queries/core/data_lifecycle/ext-q33.rq).

- Order: `68`
- Tier: `core`
- Category: `data_lifecycle`
- Kind: `report`
- Expectation: any; reference count `0`
- Requirements: `RF-19`, `RNF-13`
- Policies: `P-DATA-08`

### EXT-Q34 — data_lifecycle / violation

Evaluates data context, buffering, replication and transmission using the executable query in [`queries/core/data_lifecycle/ext-q34.rq`](../../queries/core/data_lifecycle/ext-q34.rq).

- Order: `69`
- Tier: `core`
- Category: `data_lifecycle`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-19`, `RNF-13`
- Policies: `P-DATA-08`

### EXT-Q35 — data_lifecycle / report

Evaluates data context, buffering, replication and transmission using the executable query in [`queries/core/data_lifecycle/ext-q35.rq`](../../queries/core/data_lifecycle/ext-q35.rq).

- Order: `70`
- Tier: `core`
- Category: `data_lifecycle`
- Kind: `report`
- Expectation: non_empty; reference count `6`
- Requirements: `RF-28`
- Policies: `P-DATA-09`

### EXT-Q36 — context_zones / report

Evaluates zone-aware and georestricted processing using the executable query in [`queries/core/context_zones/ext-q36.rq`](../../queries/core/context_zones/ext-q36.rq).

- Order: `71`
- Tier: `core`
- Category: `context_zones`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RF-42`, `RF-43`
- Policies: `P-ZONE-01`

### EXT-Q37 — context_zones / violation

Evaluates zone-aware and georestricted processing using the executable query in [`queries/domain/wellbeing/context_zones/ext-q37.rq`](../../queries/domain/wellbeing/context_zones/ext-q37.rq).

- Order: `72`
- Tier: `domain`
- Category: `context_zones`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-42`, `RF-43`, `RF-60`
- Policies: `P-ZONE-01`, `P-GOV-03`

### EXT-Q38 — context_zones / review

Evaluates zone-aware and georestricted processing using the executable query in [`queries/domain/wellbeing/context_zones/ext-q38.rq`](../../queries/domain/wellbeing/context_zones/ext-q38.rq).

- Order: `73`
- Tier: `domain`
- Category: `context_zones`
- Kind: `review`
- Expectation: any; reference count `1`
- Requirements: `RF-08`, `RF-27`
- Policies: `P-ZONE-02`, `P-DATA-07`

### EXT-Q39 — context_zones / report

Evaluates zone-aware and georestricted processing using the executable query in [`queries/core/context_zones/ext-q39.rq`](../../queries/core/context_zones/ext-q39.rq).

- Order: `74`
- Tier: `core`
- Category: `context_zones`
- Kind: `report`
- Expectation: non_empty; reference count `5`
- Requirements: `RF-42`
- Policies: `P-ZONE-03`, `P-CONS-04`

### EXT-Q40 — trust / report

Evaluates reproducible trust evidence and eligibility using the executable query in [`queries/core/trust/ext-q40.rq`](../../queries/core/trust/ext-q40.rq).

- Order: `75`
- Tier: `core`
- Category: `trust`
- Kind: `report`
- Expectation: non_empty; reference count `7`
- Requirements: `RF-45`, `RF-49`, `RNF-32`
- Policies: `P-NODE-03`, `P-NODE-04`

### EXT-Q41 — trust / violation

Evaluates reproducible trust evidence and eligibility using the executable query in [`queries/core/trust/ext-q41.rq`](../../queries/core/trust/ext-q41.rq).

- Order: `76`
- Tier: `core`
- Category: `trust`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-05`, `RF-47`
- Policies: `P-NODE-01`, `P-NODE-02`

### EXT-Q42 — trust / report

Evaluates reproducible trust evidence and eligibility using the executable query in [`queries/core/trust/ext-q42.rq`](../../queries/core/trust/ext-q42.rq).

- Order: `77`
- Tier: `core`
- Category: `trust`
- Kind: `report`
- Expectation: non_empty; reference count `4`
- Requirements: `RF-47`, `RF-48`
- Policies: `P-NODE-02`, `P-NODE-05`, `P-MODEL-03`

### EXT-Q43 — trust / review

Evaluates reproducible trust evidence and eligibility using the executable query in [`queries/core/trust/ext-q43.rq`](../../queries/core/trust/ext-q43.rq).

- Order: `78`
- Tier: `core`
- Category: `trust`
- Kind: `review`
- Expectation: any; reference count `7`
- Requirements: `RF-49`, `RNF-32`
- Policies: `P-NODE-03`

### EXT-Q44 — trust / report

Evaluates reproducible trust evidence and eligibility using the executable query in [`queries/core/trust/ext-q44.rq`](../../queries/core/trust/ext-q44.rq).

- Order: `79`
- Tier: `core`
- Category: `trust`
- Kind: `report`
- Expectation: non_empty; reference count `10`
- Requirements: `RF-46`, `RF-55`
- Policies: `P-MODEL-03`, `P-NODE-05`

### EXT-Q45 — trust / violation

Evaluates reproducible trust evidence and eligibility using the executable query in [`queries/core/trust/ext-q45.rq`](../../queries/core/trust/ext-q45.rq).

- Order: `80`
- Tier: `core`
- Category: `trust`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-18`, `RF-48`
- Policies: `P-ADAPT-04`, `P-ADAPT-07`

### EXT-Q46 — decision / report

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/ext-q46.rq`](../../queries/core/decision/ext-q46.rq).

- Order: `81`
- Tier: `core`
- Category: `decision`
- Kind: `report`
- Expectation: non_empty; reference count `11`
- Requirements: `RF-15`, `RF-51`, `RF-66`
- Policies: `P-MODEL-01`, `P-MODEL-05`, `P-AUD-06`

### EXT-Q47 — decision / violation

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/ext-q47.rq`](../../queries/core/decision/ext-q47.rq).

- Order: `82`
- Tier: `core`
- Category: `decision`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-54`, `RF-66`, `RNF-28`
- Policies: `P-AUD-06`

### EXT-Q48 — decision / violation

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/ext-q48.rq`](../../queries/core/decision/ext-q48.rq).

- Order: `83`
- Tier: `core`
- Category: `decision`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-50`, `RF-55`, `RNF-34`
- Policies: `P-MODEL-02`, `P-MODEL-03`

### EXT-Q49 — decision / report

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/ext-q49.rq`](../../queries/core/decision/ext-q49.rq).

- Order: `84`
- Tier: `core`
- Category: `decision`
- Kind: `report`
- Expectation: non_empty; reference count `8`
- Requirements: `RF-55`, `RNF-33`, `RNF-34`
- Policies: `P-MODEL-04`

### EXT-Q50 — decision / violation

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/ext-q50.rq`](../../queries/core/decision/ext-q50.rq).

- Order: `85`
- Tier: `core`
- Category: `decision`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-55`, `RNF-34`
- Policies: `P-MODEL-04`

### EXT-Q51 — decision / report

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/ext-q51.rq`](../../queries/core/decision/ext-q51.rq).

- Order: `86`
- Tier: `core`
- Category: `decision`
- Kind: `report`
- Expectation: non_empty; reference count `32`
- Requirements: `RF-51`, `RNF-29`
- Policies: `P-MODEL-05`

### EXT-Q52 — decision / review

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/ext-q52.rq`](../../queries/core/decision/ext-q52.rq).

- Order: `87`
- Tier: `core`
- Category: `decision`
- Kind: `review`
- Expectation: any; reference count `32`
- Requirements: `RF-51`, `RNF-29`, `RNF-33`
- Policies: `P-MODEL-05`

### EXT-Q53 — decision / violation

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/ext-q53.rq`](../../queries/core/decision/ext-q53.rq).

- Order: `88`
- Tier: `core`
- Category: `decision`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-51`, `RF-54`
- Policies: `P-MODEL-05`

### EXT-Q54 — decision / report

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/domain/wellbeing/decision/ext-q54.rq`](../../queries/domain/wellbeing/decision/ext-q54.rq).

- Order: `89`
- Tier: `domain`
- Category: `decision`
- Kind: `report`
- Expectation: any; reference count `0`
- Requirements: `RF-14`, `RF-29`, `RNF-27`
- Policies: `P-MODEL-08`, `P-OPS-05`

### EXT-Q55 — decision / review

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/ext-q55.rq`](../../queries/core/decision/ext-q55.rq).

- Order: `90`
- Tier: `core`
- Category: `decision`
- Kind: `review`
- Expectation: any; reference count `8`
- Requirements: `RF-14`, `RF-54`
- Policies: `P-MODEL-08`

### EXT-Q56 — decision / violation

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/ext-q56.rq`](../../queries/core/decision/ext-q56.rq).

- Order: `91`
- Tier: `core`
- Category: `decision`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-53`
- Policies: `P-MODEL-07`, `P-ZONE-01`, `P-CONS-04`

### EXT-Q57 — decision / report

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/ext-q57.rq`](../../queries/core/decision/ext-q57.rq).

- Order: `92`
- Tier: `core`
- Category: `decision`
- Kind: `report`
- Expectation: non_empty; reference count `7`
- Requirements: `RF-24`
- Policies: `P-FL-08`

### EXT-Q58 — decision / review

Evaluates model-tier selection, AHP and model lifecycle using the executable query in [`queries/core/decision/ext-q58.rq`](../../queries/core/decision/ext-q58.rq).

- Order: `93`
- Tier: `core`
- Category: `decision`
- Kind: `review`
- Expectation: any; reference count `7`
- Requirements: `RF-24`
- Policies: `P-FL-08`

### EXT-Q59 — adaptation / report

Evaluates migration, degradation and adaptive actions using the executable query in [`queries/core/adaptation/ext-q59.rq`](../../queries/core/adaptation/ext-q59.rq).

- Order: `94`
- Tier: `core`
- Category: `adaptation`
- Kind: `report`
- Expectation: non_empty; reference count `11`
- Requirements: `RF-16`, `RF-17`, `RF-20`, `RF-66`
- Policies: `P-ADAPT-06`, `P-AUD-06`

### EXT-Q60 — adaptation / report

Evaluates migration, degradation and adaptive actions using the executable query in [`queries/core/adaptation/ext-q60.rq`](../../queries/core/adaptation/ext-q60.rq).

- Order: `95`
- Tier: `core`
- Category: `adaptation`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RF-16`, `RF-17`
- Policies: `P-ADAPT-05`

### EXT-Q61 — adaptation / violation

Evaluates migration, degradation and adaptive actions using the executable query in [`queries/core/adaptation/ext-q61.rq`](../../queries/core/adaptation/ext-q61.rq).

- Order: `96`
- Tier: `core`
- Category: `adaptation`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-16`, `RF-22`
- Policies: `P-ADAPT-05`

### EXT-Q62 — adaptation / report

Evaluates migration, degradation and adaptive actions using the executable query in [`queries/core/adaptation/ext-q62.rq`](../../queries/core/adaptation/ext-q62.rq).

- Order: `97`
- Tier: `core`
- Category: `adaptation`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RF-20`
- Policies: `P-ADAPT-02`, `P-ADAPT-03`, `P-ADAPT-06`

### EXT-Q63 — delegation / report

Evaluates temporary delegation and recovery using the executable query in [`queries/core/delegation/ext-q63.rq`](../../queries/core/delegation/ext-q63.rq).

- Order: `98`
- Tier: `core`
- Category: `delegation`
- Kind: `report`
- Expectation: non_empty; reference count `1`
- Requirements: `RF-62`, `RF-63`, `RF-64`
- Policies: `P-AUD-01`, `P-AUD-02`, `P-AUD-03`

### EXT-Q64 — delegation / violation

Evaluates temporary delegation and recovery using the executable query in [`queries/core/delegation/ext-q64.rq`](../../queries/core/delegation/ext-q64.rq).

- Order: `99`
- Tier: `core`
- Category: `delegation`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-63`
- Policies: `P-AUD-02`

### EXT-Q65 — delegation / violation

Evaluates temporary delegation and recovery using the executable query in [`queries/core/delegation/ext-q65.rq`](../../queries/core/delegation/ext-q65.rq).

- Order: `100`
- Tier: `core`
- Category: `delegation`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RNF-14`
- Policies: `P-AUD-04`, `P-OPS-01`

### EXT-Q66 — federation / report

Evaluates federated learning and differential privacy using the executable query in [`queries/core/federation/ext-q66.rq`](../../queries/core/federation/ext-q66.rq).

- Order: `101`
- Tier: `core`
- Category: `federation`
- Kind: `report`
- Expectation: non_empty; reference count `2`
- Requirements: `RF-21`, `RF-22`, `RF-23`, `RF-25`
- Policies: `P-FL-01`, `P-FL-06`, `P-FL-07`

### EXT-Q67 — federation / violation

Evaluates federated learning and differential privacy using the executable query in [`queries/core/federation/ext-q67.rq`](../../queries/core/federation/ext-q67.rq).

- Order: `102`
- Tier: `core`
- Category: `federation`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-21`, `RF-56`
- Policies: `P-FL-02`, `P-FL-03`

### EXT-Q68 — federation / violation

Evaluates federated learning and differential privacy using the executable query in [`queries/core/federation/ext-q68.rq`](../../queries/core/federation/ext-q68.rq).

- Order: `103`
- Tier: `core`
- Category: `federation`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-57`, `RF-58`, `RNF-16`, `RNF-19`
- Policies: `P-FL-03`, `P-FL-05`

### EXT-Q69 — federation / report

Evaluates federated learning and differential privacy using the executable query in [`queries/core/federation/ext-q69.rq`](../../queries/core/federation/ext-q69.rq).

- Order: `104`
- Tier: `core`
- Category: `federation`
- Kind: `report`
- Expectation: non_empty; reference count `2`
- Requirements: `RF-56`, `RF-59`, `RNF-18`
- Policies: `P-FL-04`

### EXT-Q70 — audit_temporal / report

Evaluates audit chains and temporal validity using the executable query in [`queries/core/audit_temporal/ext-q70.rq`](../../queries/core/audit_temporal/ext-q70.rq).

- Order: `105`
- Tier: `core`
- Category: `audit_temporal`
- Kind: `report`
- Expectation: non_empty; reference count `204`
- Requirements: `RF-67`, `RNF-30`
- Policies: `P-AUD-07`

### EXT-Q71 — audit_temporal / violation

Evaluates audit chains and temporal validity using the executable query in [`queries/core/audit_temporal/ext-q71.rq`](../../queries/core/audit_temporal/ext-q71.rq).

- Order: `106`
- Tier: `core`
- Category: `audit_temporal`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-54`, `RF-66`, `RNF-28`, `RNF-29`
- Policies: `P-AUD-06`

### EXT-Q72 — audit_temporal / violation

Evaluates audit chains and temporal validity using the executable query in [`queries/core/audit_temporal/ext-q72.rq`](../../queries/core/audit_temporal/ext-q72.rq).

- Order: `107`
- Tier: `core`
- Category: `audit_temporal`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RF-65`, `RF-66`
- Policies: `P-AUD-05`

### EXT-Q73 — audit_temporal / report

Evaluates audit chains and temporal validity using the executable query in [`queries/core/audit_temporal/ext-q73.rq`](../../queries/core/audit_temporal/ext-q73.rq).

- Order: `108`
- Tier: `core`
- Category: `audit_temporal`
- Kind: `report`
- Expectation: non_empty; reference count `79`
- Requirements: `RNF-35`, `RNF-36`
- Policies: `P-GOV-05`, `P-AUD-02`

### EXT-Q74 — audit_temporal / violation

Evaluates audit chains and temporal validity using the executable query in [`queries/core/audit_temporal/ext-q74.rq`](../../queries/core/audit_temporal/ext-q74.rq).

- Order: `109`
- Tier: `core`
- Category: `audit_temporal`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RNF-36`
- Policies: `P-GOV-05`

### EXT-Q75 — validation / inventory

Evaluates acceptance, SHACL and campaign readiness using the executable query in [`queries/core/validation/ext-q75.rq`](../../queries/core/validation/ext-q75.rq).

- Order: `110`
- Tier: `core`
- Category: `validation`
- Kind: `inventory`
- Expectation: non_empty; reference count `74`
- Requirements: `RF-71`, `RV-01`
- Policies: `P-VAL-03`

### EXT-Q76 — validation / review

Evaluates acceptance, SHACL and campaign readiness using the executable query in [`queries/core/validation/ext-q76.rq`](../../queries/core/validation/ext-q76.rq).

- Order: `111`
- Tier: `core`
- Category: `validation`
- Kind: `review`
- Expectation: any; reference count `9`
- Requirements: `RNF-01`, `RNF-02`, `RNF-04`, `RNF-05`, `RNF-06`, `RNF-08`, `RNF-09`, `RNF-14`, `RNF-21`, `RNF-34`
- Policies: `P-OPS-01`, `P-VAL-03`

### EXT-Q77 — validation / review

Evaluates acceptance, SHACL and campaign readiness using the executable query in [`queries/core/validation/ext-q77.rq`](../../queries/core/validation/ext-q77.rq).

- Order: `112`
- Tier: `core`
- Category: `validation`
- Kind: `review`
- Expectation: any; reference count `6`
- Requirements: `RF-71`, `RF-72`, `RNF-39`, `RV-02`, `RV-03`
- Policies: `P-VAL-03`, `P-VAL-04`, `P-VAL-07`

### EXT-Q78 — policy_governance / report

Evaluates policy inventory, precedence and traceability using the executable query in [`queries/core/policy_governance/ext-q78.rq`](../../queries/core/policy_governance/ext-q78.rq).

- Order: `113`
- Tier: `core`
- Category: `policy_governance`
- Kind: `report`
- Expectation: non_empty; reference count `37`
- Requirements: `RNF-22`
- Policies: `P-GOV-03`

### EXT-Q79 — policy_governance / violation

Evaluates policy inventory, precedence and traceability using the executable query in [`queries/core/policy_governance/ext-q79.rq`](../../queries/core/policy_governance/ext-q79.rq).

- Order: `114`
- Tier: `core`
- Category: `policy_governance`
- Kind: `violation`
- Expectation: zero_rows; reference count `0`
- Requirements: `RNF-22`
- Policies: `P-GOV-03`

### EXT-Q80 — validation / dashboard

Evaluates acceptance, SHACL and campaign readiness using the executable query in [`queries/core/validation/ext-q80.rq`](../../queries/core/validation/ext-q80.rq).

- Order: `115`
- Tier: `core`
- Category: `validation`
- Kind: `dashboard`
- Expectation: non_empty; reference count `13`
- Requirements: `RF-68`, `RF-71`, `RV-01`, `RV-05`
- Policies: `P-VAL-08`
