# Policies and enforcement mechanisms

> Generated reference for release v3.0.0. Do not edit individual
> entries by hand. Regenerate with
> `.venv/bin/python tools/generate_reference_docs.py`.

Canonical source: `ontology/legacy/smartcity_continuum-v3.0.0.ttl`.

The release declares 79 policies in 12 categories and 55
enforcement mechanisms. Hard constraints are applied before
optimization: effective authorization is the most restrictive
intersection of consent, semantic contract, zone, security and
resource eligibility.

## Policy categories

| Category | Label |
|---|---|
| `PolicyCategory_CONS` | Consent and semantic contracts |
| `PolicyCategory_DATA` | Data, privacy, identity and transmission |
| `PolicyCategory_FL` | Federated learning and model lifecycle |
| `PolicyCategory_GOV` | Governance, precedence and lifecycle |
| `PolicyCategory_INT` | Interoperability and semantic extensibility |
| `PolicyCategory_ADAPT` | Migration, offloading, degradation and continuity |
| `PolicyCategory_MODEL` | Model selection and AHP |
| `PolicyCategory_NODE` | Nodes and dynamic trust |
| `PolicyCategory_OPS` | Operations, scalability and QoS |
| `PolicyCategory_AUD` | Temporal delegation, MAPE-K and audit |
| `PolicyCategory_VAL` | Validation, reproducibility and maintainability |
| `PolicyCategory_ZONE` | Zones and georestriction |

## Policies

### P-ADAPT-01 — Multi-condition migration decision

Migration or offloading must be decided by jointly considering the adaptation cause, effective authorization, source state, destination eligibility, latency, cost, energy and service continuity. It must not be triggered solely by an isolated metric unless a safety policy makes that metric a hard constraint.

- Type: Obligation
- Category: Migration, offloading, degradation and continuity (`PolicyCategory_ADAPT`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-16`, `RF-17`, `RF-18`, `RNF-03`
- Recommended mechanisms: `M-ADAPT-01`, `M-NODE-02`
- Catalogued queries: `BASE-Q12`

### P-ADAPT-02 — Safe degradation on communication loss or lack of destination

When communication is lost or no eligible destination exists, the system must maintain authorized critical functions locally and degrade processing in a controlled manner before attempting an unauthorized transfer.

- Type: Obligation
- Category: Migration, offloading, degradation and continuity (`PolicyCategory_ADAPT`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-07`, `RF-17`, `RNF-12`
- Recommended mechanisms: `M-ADAPT-02`, `M-BUFFER-01`
- Catalogued queries: `BASE-Q14`, `EXT-Q62`

### P-ADAPT-03 — Overload-driven degradation

Under overload, the system must apply controlled processing degradation, migration or delegation according to eligible alternatives. Scaling to higher tiers is allowed only when consent, zone, capacity and trust policies are satisfied.

- Type: Obligation
- Category: Migration, offloading, degradation and continuity (`PolicyCategory_ADAPT`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-17`, `RF-20`, `RNF-03`
- Recommended mechanisms: `M-ADAPT-01`, `M-ADAPT-02`, `M-OPS-02`
- Catalogued queries: `EXT-Q62`

### P-ADAPT-04 — Destination and migration-cost criteria

A migration must not target an ineligible node or proceed when estimated time/cost exceeds configured limits and a local or degraded alternative better preserves continuity. The reason for abstention must be recorded.

- Type: Abstention
- Category: Migration, offloading, degradation and continuity (`PolicyCategory_ADAPT`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-16`, `RF-17`, `RNF-02`
- Recommended mechanisms: `M-ADAPT-01`, `M-AUD-01`, `M-NODE-02`
- Catalogued queries: `EXT-Q45`

### P-ADAPT-05 — Separation of migration, delegation and federated learning

Migration or delegation must not automatically create a federated-learning session or gradient exchange. FL sessions are created only when the operation actually involves federated learning and satisfies its specific policies.

- Type: Prohibition
- Category: Migration, offloading, degradation and continuity (`PolicyCategory_ADAPT`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-16`, `RF-22`, `RF-25`, `RF-62`
- Recommended mechanisms: `M-ADAPT-03`, `M-FL-01`
- Catalogued queries: `BASE-Q13`, `EXT-Q60`, `EXT-Q61`

### P-ADAPT-06 — Degradation and executed-action recording

Every model or service degradation must record an explicit cause and link to the evaluation that triggered it and the action ultimately executed.

- Type: Obligation
- Category: Migration, offloading, degradation and continuity (`PolicyCategory_ADAPT`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-20`, `RF-44`, `RF-66`
- Recommended mechanisms: `M-ADAPT-02`, `M-AUD-01`
- Catalogued queries: `BASE-Q13`, `BASE-Q22`, `BASE-Q27`, `EXT-Q59`, `EXT-Q62`

### P-ADAPT-07 — Delegation to the highest-trust eligible destination

When delegation is chosen, the preferred destination must be the highest-trust candidate among those already satisfying load, availability, connectivity, residual capacity and active constraints. Its trust score need not exceed the source's if the source degradation has another cause.

- Type: Obligation
- Category: Migration, offloading, degradation and continuity (`PolicyCategory_ADAPT`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-48`, `RF-62`, `RNF-14`
- Recommended mechanisms: `M-DELEG-01`, `M-TRUST-02`
- Catalogued queries: `EXT-Q45`

### P-ADAPT-08 — Recovery continuity and idempotency

Migration, delegation, reconnection and recovery processes must not lose critical events or create accidental duplicates. Retryable operations must have idempotent semantics where applicable.

- Type: Prohibition
- Category: Migration, offloading, degradation and continuity (`PolicyCategory_ADAPT`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-19`, `RF-26`, `RNF-02`, `RNF-13`
- Recommended mechanisms: `M-DELEG-02`, `M-REPL-01`, `M-TX-02`
- Catalogued queries: None declared

### P-AUD-01 — Delegation as a semantic event

Every temporary delegation must be materialized as an explicit event, not merely as a static relationship between nodes.

- Type: Obligation
- Category: Temporal delegation, MAPE-K and audit (`PolicyCategory_AUD`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-62`
- Recommended mechanisms: `M-DELEG-01`
- Catalogued queries: `BASE-Q14`, `EXT-Q63`

### P-AUD-02 — Temporal delegation content

Every delegation must record the source, destination, cause, start of validity and recovery condition. Planned expiration must be stored separately; `validTo` is populated only when the delegation is effectively closed.

- Type: Obligation
- Category: Temporal delegation, MAPE-K and audit (`PolicyCategory_AUD`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-63`, `RNF-36`
- Recommended mechanisms: `M-DELEG-01`, `M-TIME-01`
- Catalogued queries: `EXT-Q63`, `EXT-Q64`, `EXT-Q73`

### P-AUD-03 — Effective delegation closure

A delegation must close when its recovery condition is met or its planned expiration is reached. Closure must record `validTo` with the effective time and stop any new action based on the ended delegation.

- Type: Obligation
- Category: Temporal delegation, MAPE-K and audit (`PolicyCategory_AUD`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-64`, `RNF-36`
- Recommended mechanisms: `M-DELEG-02`
- Catalogued queries: `EXT-Q63`

### P-AUD-04 — Delegation cascade limit

A delegation chain must not exceed `D_delegation_max` or the equivalent stopping condition set in the acceptance profile/active policy.

- Type: Prohibition
- Category: Temporal delegation, MAPE-K and audit (`PolicyCategory_AUD`)
- Version: `POLICIES-REV-01`
- Related requirements: `RNF-14`
- Recommended mechanisms: `M-DELEG-03`
- Catalogued queries: `EXT-Q65`

### P-AUD-05 — Symptom–policy–action coherence

Every relevant adaptive action must be justified by an identifiable MAPE-K symptom or condition and an applicable policy consistent with that symptom. Incompatibilities must be marked as violations or invalid evaluations.

- Type: Obligation
- Category: Temporal delegation, MAPE-K and audit (`PolicyCategory_AUD`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-65`, `RF-66`, `RF-67`
- Recommended mechanisms: `M-AUD-02`
- Catalogued queries: `BASE-Q14`, `BASE-Q35`, `EXT-Q72`

### P-AUD-06 — Complete EvaluationState ticket

Every relevant `EvaluationState` must record, at minimum, the symptom, applied policies, contract, effective consent, evaluated alternatives, AHP scores, external trust criterion, selected tier, justification, decision time and a reference to the executed action.

- Type: Obligation
- Category: Temporal delegation, MAPE-K and audit (`PolicyCategory_AUD`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-51`, `RF-54`, `RF-66`, `RNF-28`, `RNF-29`
- Recommended mechanisms: `M-AUD-01`
- Catalogued queries: `BASE-Q21`, `EXT-Q20`, `EXT-Q46`, `EXT-Q47`, `EXT-Q59`, `EXT-Q71`

### P-AUD-07 — Causal and temporal decision reconstruction

Persisted information must allow retrospective reconstruction of the chain user → contract → effective consent → purpose → zone → policy → node state → alternatives/scores → trust → tier → action, identifying which values were valid at the decision time.

- Type: Obligation
- Category: Temporal delegation, MAPE-K and audit (`PolicyCategory_AUD`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-67`, `RNF-30`, `RNF-32`, `RNF-33`
- Recommended mechanisms: `M-AUD-03`, `M-TIME-01`
- Catalogued queries: `BASE-Q35`, `EXT-Q70`

### P-CONS-01 — Range-based consent and revocation

Consent must be expressed through processing ranges covering at least local scope, community aggregation, global aggregation and denial/revocation. It must be possible to specify data categories, purpose, validity interval and maximum authorized range.

- Type: Obligation
- Category: Consent and semantic contracts (`PolicyCategory_CONS`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-32`
- Recommended mechanisms: `M-CONS-01`
- Catalogued queries: `BASE-Q01`, `BASE-Q15`, `BASE-Q31`, `EXT-Q11`, `EXT-Q13`, `EXT-Q16`

### P-CONS-02 — Unique effective contract per user and purpose

Two effective semantic contracts must not coexist for the same user, purpose and instant. Historical contracts or simultaneous contracts for different purposes are allowed provided their intervals do not create ambiguity for the same purpose.

- Type: Prohibition
- Category: Consent and semantic contracts (`PolicyCategory_CONS`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-33`, `RNF-36`
- Recommended mechanisms: `M-CONS-01`, `M-TIME-01`
- Catalogued queries: `BASE-Q20`, `EXT-Q12`, `EXT-Q14`, `EXT-Q15`

### P-CONS-03 — Minimum contract content

Every effective semantic contract must identify the user, processing purpose, consent range, validity interval and policies governing the processing.

- Type: Obligation
- Category: Consent and semantic contracts (`PolicyCategory_CONS`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-34`, `RF-41`
- Recommended mechanisms: `M-CONS-01`, `M-GOV-02`
- Catalogued queries: `BASE-Q20`, `EXT-Q12`, `EXT-Q14`

### P-CONS-04 — Effective authorization and inconsistencies

When active consent, the contract and zone policy are incompatible, external processing must not exceed their most restrictive intersection. The inconsistency must be recorded and affected processing must remain blocked until effective authorization is unambiguous.

- Type: Prohibition
- Category: Consent and semantic contracts (`PolicyCategory_CONS`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-35`, `RF-36`, `RNF-22`
- Recommended mechanisms: `M-CONS-02`, `M-GOV-03`
- Catalogued queries: `BASE-Q15`, `BASE-Q25`, `BASE-Q28`, `EXT-Q11`, `EXT-Q16`, `EXT-Q17`, `EXT-Q18`, `EXT-Q19`, `EXT-Q20`, `EXT-Q39`, `EXT-Q56`

### P-CONS-05 — Required minimum range declaration

Every consent-dependent resource, permission, model, service, session or action must declare the minimum required range before being considered eligible.

- Type: Obligation
- Category: Consent and semantic contracts (`PolicyCategory_CONS`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-37`
- Recommended mechanisms: `M-CONS-03`
- Catalogued queries: `BASE-Q06`, `EXT-Q21`

### P-CONS-06 — Downstream reception without extending consent

Improved generic models may be received without extending the consent range only when the downstream flow complies with the contract and active policies and contains no personal data, individualized gradients or persistent user-derived identifiers.

- Type: Abstention
- Category: Consent and semantic contracts (`PolicyCategory_CONS`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-23`, `RF-38`
- Recommended mechanisms: `M-CONS-02`, `M-FL-02`
- Catalogued queries: None declared

### P-DATA-01 — Confinement of raw physiological observations

Raw physiological observations must not leave the local scope. They must not be transmitted to Edge, Fog or Cloud. Any external processing must use explicitly authorized parameterized data or model updates.

- Type: Prohibition
- Category: Data, privacy, identity and transmission (`PolicyCategory_DATA`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-10`, `RF-60`, `RNF-17`
- Recommended mechanisms: `M-DATA-01`, `M-TX-01`
- Catalogued queries: `BASE-Q18`, `EXT-Q22`

### P-DATA-02 — External identifier pseudonymization

No direct personal identifier may leave the local scope alongside parameterized data, gradients or federated updates. Every authorized flow must use pseudonymous or anonymized identifiers appropriate to its purpose.

- Type: Prohibition
- Category: Data, privacy, identity and transmission (`PolicyCategory_DATA`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-61`, `RNF-17`, `RNF-19`
- Recommended mechanisms: `M-ID-01`, `M-TX-01`
- Catalogued queries: `BASE-Q01`, `EXT-Q23`, `EXT-Q26`, `EXT-Q27`, `EXT-Q28`

### P-DATA-03 — Sensitive-information encryption

All data classified as sensitive must be protected in transit and at rest according to the deployment's versioned security baseline. This policy also applies to temporary buffers and authorized replicas.

- Type: Obligation
- Category: Data, privacy, identity and transmission (`PolicyCategory_DATA`)
- Version: `POLICIES-REV-01`
- Related requirements: `RNF-15`, `RNF-39`
- Recommended mechanisms: `M-SEC-01`, `M-VAL-04`
- Catalogued queries: `EXT-Q23`, `EXT-Q29`, `EXT-Q30`, `EXT-Q32`

### P-DATA-04 — Data-type-based transmission gate

Parameterized data must not be transmitted until marked as ready for transmission and accompanied by the required contextual metadata. This rule must not be used to block other flow types, such as model downloads, which are governed by their own policies.

- Type: Abstention
- Category: Data, privacy, identity and transmission (`PolicyCategory_DATA`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-04`, `RF-09`, `RF-27`
- Recommended mechanisms: `M-DATA-02`, `M-TX-01`
- Catalogued queries: `BASE-Q10`, `BASE-Q28`

### P-DATA-05 — Retention at the highest authorized tier

When data cannot be transmitted because of connectivity, energy, saturation, zone or authorization constraints, they must be temporarily retained at the highest tier permitted by effective authorization. If external storage is not allowed, they must remain exclusively within the local scope until a safe window or authorized disposal.

- Type: Obligation
- Category: Data, privacy, identity and transmission (`PolicyCategory_DATA`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-08`, `RF-26`, `RNF-12`
- Recommended mechanisms: `M-BUFFER-01`, `M-CONS-02`, `M-ZONE-01`
- Catalogued queries: `EXT-Q31`, `EXT-Q32`

### P-DATA-06 — Energy management for processing and transmission

Low battery requires reduced model complexity and fewer non-critical transmissions. Critical battery requires attempting offloading only to an authorized tier with sufficient connectivity; if no authorized external option exists, local degradation and temporary retention must be applied.

- Type: Obligation
- Category: Data, privacy, identity and transmission (`PolicyCategory_DATA`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-07`, `RF-27`, `RNF-06`
- Recommended mechanisms: `M-ADAPT-02`, `M-BUFFER-01`, `M-DEVICE-01`
- Catalogued queries: `BASE-Q10`

### P-DATA-07 — Safe transmission and reconnection window

Pending flows must not resume merely because connectivity returns. Synchronization or transmission may restart only when sufficient connectivity, effective authorization, an eligible destination and compatible energy conditions hold simultaneously.

- Type: Abstention
- Category: Data, privacy, identity and transmission (`PolicyCategory_DATA`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-26`, `RF-27`, `RNF-12`, `RNF-13`
- Recommended mechanisms: `M-CONS-02`, `M-NODE-02`, `M-TX-02`
- Catalogued queries: `BASE-Q10`, `BASE-Q17`, `EXT-Q31`, `EXT-Q38`

### P-DATA-08 — Redundancy, replication and idempotency

Accidental duplicates or data marked as redundant without a replication purpose must not enter external flows. Controlled replicas are allowed only when explicitly identified, versioned and synchronized idempotently.

- Type: Prohibition
- Category: Data, privacy, identity and transmission (`PolicyCategory_DATA`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-19`, `RF-28`, `RNF-13`
- Recommended mechanisms: `M-REPL-01`, `M-TX-01`
- Catalogued queries: `EXT-Q33`, `EXT-Q34`

### P-DATA-09 — Criticality-based prioritization

Transmission scheduling must prioritize critical data over secondary data using a generic criticality classification. Non-transmissible or redundant data must remain retained under the applicable policy and must not displace critical data from a limited transmission window.

- Type: Obligation
- Category: Data, privacy, identity and transmission (`PolicyCategory_DATA`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-27`, `RF-28`
- Recommended mechanisms: `M-BUFFER-01`, `M-TX-03`
- Catalogued queries: `EXT-Q35`

### P-DATA-10 — Minimum processed-data context

Data used beyond their immediate observation must retain the minimum context needed to interpret their use: time, location or applicable zone, signal quality, device state, node state, processing level and purpose.

- Type: Obligation
- Category: Data, privacy, identity and transmission (`PolicyCategory_DATA`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-09`, `RF-30`, `RNF-27`
- Recommended mechanisms: `M-DATA-02`, `M-TIME-01`
- Catalogued queries: `EXT-Q23`, `EXT-Q24`, `EXT-Q25`

### P-FL-01 — Federated-session eligibility

A federated session must not start while any required participant fails the eligibility, trust or authorization conditions applicable to the flow. If conditions can recover, the session must be deferred to a valid window.

- Type: Abstention
- Category: Federated learning and model lifecycle (`PolicyCategory_FL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-21`, `RF-22`, `RF-25`, `RNF-12`
- Recommended mechanisms: `M-FL-01`, `M-NODE-02`
- Catalogued queries: `BASE-Q16`, `BASE-Q30`, `EXT-Q66`

### P-FL-02 — Upstream federated-flow authorization

No parameter, personalized model or gradient may be sent to higher tiers if effective authorization, the zone or privacy policies do not permit that flow type.

- Type: Prohibition
- Category: Federated learning and model lifecycle (`PolicyCategory_FL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-21`, `RF-35`, `RF-42`
- Recommended mechanisms: `M-CONS-02`, `M-FL-01`, `M-ZONE-01`
- Catalogued queries: `BASE-Q24`, `BASE-Q25`, `EXT-Q67`

### P-FL-03 — Mandatory gradient protection

Every session carrying gradients must declare a privacy budget and noise level. Every gradient leaving a mobile device must be anonymized or pseudonymized as appropriate and have the required differential-privacy noise applied before leaving the device.

- Type: Obligation
- Category: Federated learning and model lifecycle (`PolicyCategory_FL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-56`, `RF-57`, `RNF-16`, `RNF-17`
- Recommended mechanisms: `M-FL-03`, `M-ID-01`
- Catalogued queries: `BASE-Q16`, `EXT-Q67`, `EXT-Q68`

### P-FL-04 — Epsilon budget accounting

The epsilon budget must be controlled per operation or session according to the purpose, contract and active policy and must not exceed the maximum authorized for that context. The applied value and its consumption rule must be auditable.

- Type: Obligation
- Category: Federated learning and model lifecycle (`PolicyCategory_FL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-59`, `RNF-18`
- Recommended mechanisms: `M-AUD-01`, `M-FL-04`
- Catalogued queries: `BASE-Q24`, `EXT-Q69`

### P-FL-05 — Explicit privacy mechanism

Every protected federated session or flow must explicitly link to the privacy, anonymization or pseudonymization mechanism actually applied; an external documentary reference without a verifiable link is insufficient.

- Type: Obligation
- Category: Federated learning and model lifecycle (`PolicyCategory_FL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-58`, `RNF-19`
- Recommended mechanisms: `M-FL-03`, `M-ID-01`
- Catalogued queries: `BASE-Q16`, `EXT-Q68`

### P-FL-06 — Downstream flow of improved models

Improved models distributed to lower tiers must not include personal data, raw observations, individualized gradients or persistent user-derived identifiers. The flow must respect the contract, zone and active policies.

- Type: Prohibition
- Category: Federated learning and model lifecycle (`PolicyCategory_FL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-23`, `RF-38`, `RNF-17`
- Recommended mechanisms: `M-CONS-02`, `M-FL-02`, `M-ZONE-01`
- Catalogued queries: `EXT-Q66`

### P-FL-07 — Minimum HFL session metadata

Every HFL session must record at least the session time, participating nodes, updated model, type of information exchanged and privacy mechanisms where applicable.

- Type: Obligation
- Category: Federated learning and model lifecycle (`PolicyCategory_FL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-25`, `RNF-16`
- Recommended mechanisms: `M-AUD-01`, `M-FL-01`, `M-FL-02`
- Catalogued queries: `BASE-Q16`, `BASE-Q24`, `EXT-Q66`

### P-FL-08 — Model versioning and rollback

Every model update must produce an identifiable version and record its update date. Rollback to a previous version must remain possible in the event of degradation, errors or policy non-compliance.

- Type: Obligation
- Category: Federated learning and model lifecycle (`PolicyCategory_FL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-24`, `RNF-38`, `RNF-39`
- Recommended mechanisms: `M-MODEL-05`, `M-VAL-04`
- Catalogued queries: `BASE-Q04`, `BASE-Q22`, `EXT-Q57`, `EXT-Q58`

### P-GOV-01 — Unique policy typing

Every formal system policy must be represented as an explicit entity and classified under exactly one of obligation, abstention or prohibition. The types must be mutually distinguishable, and no formal policy may be assigned more than one type.

- Type: Obligation
- Category: Governance, precedence and lifecycle (`PolicyCategory_GOV`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-39`, `RF-40`
- Recommended mechanisms: `M-GOV-01`
- Catalogued queries: `EXT-Q03`, `EXT-Q06`, `EXT-Q10`

### P-GOV-02 — Explicit governance links

Every governed entity or decision must maintain an explicit relationship to its governing policy or policy set. Every evaluation, migration, degradation, delegation or model selection must record the specific policy applied.

- Type: Obligation
- Category: Governance, precedence and lifecycle (`PolicyCategory_GOV`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-41`, `RF-44`, `RNF-28`, `RNF-30`
- Recommended mechanisms: `M-AUD-01`, `M-GOV-02`
- Catalogued queries: None declared

### P-GOV-03 — Strictest-constraint precedence

No action may be authorized if it exceeds any current constraint imposed by consent, the semantic contract, zone, security or resource capacity. When rules apply concurrently, final eligibility must correspond to their most restrictive intersection.

- Type: Prohibition
- Category: Governance, precedence and lifecycle (`PolicyCategory_GOV`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-35`, `RF-42`, `RF-43`, `RNF-22`
- Recommended mechanisms: `M-CONS-02`, `M-GOV-03`, `M-ZONE-01`
- Catalogued queries: `EXT-Q07`, `EXT-Q17`, `EXT-Q19`, `EXT-Q37`, `EXT-Q78`, `EXT-Q79`

### P-GOV-04 — Policy determinism and versioning

Adaptation policies must be versioned. Given the same input state, consent, contract, zone and policy version, the system must produce the same eligibility decision and record the applied version. During an acceptance campaign, no policy may change without explicitly changing the artifact version.

- Type: Obligation
- Category: Governance, precedence and lifecycle (`PolicyCategory_GOV`)
- Version: `POLICIES-REV-01`
- Related requirements: `RNF-20`, `RNF-22`, `RNF-38`, `RNF-39`, `RV-04`
- Recommended mechanisms: `M-GOV-02`, `M-GOV-04`, `M-VAL-04`
- Catalogued queries: `EXT-Q03`, `EXT-Q10`

### P-GOV-05 — Temporal state lifecycle

Every state must be modeled as a first-class temporal entity. It must record `validFrom` upon creation and `validTo` only when it ends. A state derived from an observation must retain an explicit link to its source evidence. Planned expiration must not reuse `validTo` before effective closure.

- Type: Obligation
- Category: Governance, precedence and lifecycle (`PolicyCategory_GOV`)
- Version: `POLICIES-REV-01`
- Related requirements: `RNF-35`, `RNF-36`, `RNF-37`
- Recommended mechanisms: `M-TIME-01`
- Catalogued queries: `BASE-Q09`, `EXT-Q73`, `EXT-Q74`

### P-INT-01 — Use of open semantic standards

Semantic representation and querying must use open standards compatible with RDF/OWL/Turtle and SPARQL 1.1. An applicable standard vocabulary, including SOSA/SSN, SAREF, FOAF or GeoSPARQL, must be reused or aligned with; any conceptual duplication must be documented and justified.

- Type: Obligation
- Category: Interoperability and semantic extensibility (`PolicyCategory_INT`)
- Version: `POLICIES-REV-01`
- Related requirements: `RNF-24`, `RNF-25`, `RNF-26`
- Recommended mechanisms: `M-INT-01`, `M-VAL-01`
- Catalogued queries: `BASE-Q05`

### P-INT-02 — Extensibility without breaking the conceptual core

Adding new users, nodes, sensors, models, policies, contracts or wearable types must not require changing central conceptual abstractions already used by reference scenarios, unless an incompatible major-version change is explicitly declared.

- Type: Prohibition
- Category: Interoperability and semantic extensibility (`PolicyCategory_INT`)
- Version: `POLICIES-REV-01`
- Related requirements: `RNF-10`, `RNF-23`, `RNF-38`
- Recommended mechanisms: `M-INT-02`, `M-VAL-05`
- Catalogued queries: `BASE-Q03`

### P-MODEL-01 — Selection by suitability, not highest tier

The system must select the most suitable tier among eligible alternatives, not the highest tier by default. The decision must first apply hard constraints and then optimize among the remaining alternatives.

- Type: Obligation
- Category: Model selection and AHP (`PolicyCategory_MODEL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-15`, `RF-52`, `RF-53`
- Recommended mechanisms: `M-MODEL-01`, `M-NODE-02`
- Catalogued queries: `BASE-Q04`, `BASE-Q32`, `EXT-Q46`

### P-MODEL-02 — AHP criteria and normalization

When AHP is used, normalized weights must correspond to latency, privacy and model quality. Their sum must equal 1 within the configured tolerance. Trust is not part of this normalization.

- Type: Obligation
- Category: Model selection and AHP (`PolicyCategory_MODEL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-50`, `RF-55`, `RNF-34`
- Recommended mechanisms: `M-MODEL-02`
- Catalogued queries: `EXT-Q48`

### P-MODEL-03 — Trust as an external criterion

The trust score or trust weight must not be included as a fourth weight in AHP normalization. It may serve as a filter, ranking criterion or documented external adjustment after eligibility is established.

- Type: Prohibition
- Category: Model selection and AHP (`PolicyCategory_MODEL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-46`, `RF-50`, `RF-55`, `RNF-05`, `RNF-33`
- Recommended mechanisms: `M-MODEL-02`, `M-TRUST-02`
- Catalogued queries: `EXT-Q42`, `EXT-Q44`, `EXT-Q48`

### P-MODEL-04 — AHP method consistency

An evaluation labeled as AHP must not be considered valid if its weights are not normalized or its consistency ratio exceeds the configured threshold. If pairwise comparisons and consistency checking are not used, the decision must be labeled as weighted multicriteria scoring rather than AHP.

- Type: Prohibition
- Category: Model selection and AHP (`PolicyCategory_MODEL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-55`, `RNF-34`
- Recommended mechanisms: `M-MODEL-03`
- Catalogued queries: `EXT-Q49`, `EXT-Q50`

### P-MODEL-05 — Per-alternative scores and explanation

Every selection evaluation must retain the score of each evaluated candidate tier, the final selected tier and a justification explaining why the winning alternative outperformed the others.

- Type: Obligation
- Category: Model selection and AHP (`PolicyCategory_MODEL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-51`, `RF-54`, `RNF-29`, `RNF-33`
- Recommended mechanisms: `M-AUD-01`, `M-MODEL-01`
- Catalogued queries: `BASE-Q21`, `EXT-Q46`, `EXT-Q51`, `EXT-Q52`, `EXT-Q53`

### P-MODEL-06 — Privacy priority

When privacy is the dominant criterion or effective consent limits aggregation, the decision must favor local or Edge tiers only if Edge remains authorized. A hard constraint always takes precedence over a quality score.

- Type: Obligation
- Category: Model selection and AHP (`PolicyCategory_MODEL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-35`, `RF-42`, `RF-52`
- Recommended mechanisms: `M-CONS-02`, `M-MODEL-01`, `M-ZONE-01`
- Catalogued queries: `BASE-Q15`

### P-MODEL-07 — Conditional Cloud selection

Cloud must not be selected until effective consent, the contract, zone, node eligibility and trust have been checked. Differential privacy is additionally required when the operation involves federated learning, gradients or updates subject to that protection, but not as a generic condition for all inference.

- Type: Abstention
- Category: Model selection and AHP (`PolicyCategory_MODEL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-53`, `RF-56`, `RF-59`
- Recommended mechanisms: `M-FL-03`, `M-MODEL-01`
- Catalogued queries: `EXT-Q56`

### P-MODEL-08 — Separation of observed quality and decision weights

Prediction confidence, estimated error, local feedback and observed model quality must be recorded as independent evaluation metrics. AHP weights must not substitute for these metrics.

- Type: Obligation
- Category: Model selection and AHP (`PolicyCategory_MODEL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-14`, `RNF-27`
- Recommended mechanisms: `M-AUD-01`, `M-METRIC-01`
- Catalogued queries: `EXT-Q54`, `EXT-Q55`

### P-MODEL-09 — Reevaluation of the current selection

When context, consent, contract, zone, connectivity, load or trust changes and the current selection becomes invalid, a new evaluation must start and complete within the configured reselection limit.

- Type: Obligation
- Category: Model selection and AHP (`PolicyCategory_MODEL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-15`, `RF-17`, `RNF-21`
- Recommended mechanisms: `M-CTX-01`, `M-MODEL-04`
- Catalogued queries: None declared

### P-NODE-01 — Operational states and eligibility

An `Inoperative` node must not be selected as a processing, migration, HFL or delegation destination. A `ComputeOnly` node may be selected only for operations explicitly compatible with its current capabilities and constraints.

- Type: Prohibition
- Category: Nodes and dynamic trust (`PolicyCategory_NODE`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-05`, `RF-17`, `RNF-12`
- Recommended mechanisms: `M-NODE-01`, `M-NODE-02`
- Catalogued queries: `BASE-Q07`, `BASE-Q08`, `BASE-Q26`, `EXT-Q41`

### P-NODE-02 — Hard candidate filters

No node may enter the optimization phase if it fails minimum availability, necessary connectivity, residual capacity, effective authorization or zone constraints for the evaluated operation.

- Type: Prohibition
- Category: Nodes and dynamic trust (`PolicyCategory_NODE`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-15`, `RF-18`, `RF-47`
- Recommended mechanisms: `M-CONS-02`, `M-NODE-02`, `M-ZONE-01`
- Catalogued queries: `BASE-Q08`, `BASE-Q12`, `BASE-Q19`, `BASE-Q23`, `EXT-Q41`, `EXT-Q42`

### P-NODE-03 — Reproducible trust score

Every node state used in an adaptive decision must have a normalized trust score accompanied by the calculation-rule version and the historical window or evidence period used.

- Type: Obligation
- Category: Nodes and dynamic trust (`PolicyCategory_NODE`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-45`, `RF-49`, `RNF-32`
- Recommended mechanisms: `M-TRUST-01`, `M-VAL-04`
- Catalogued queries: `BASE-Q07`, `EXT-Q40`, `EXT-Q43`

### P-NODE-04 — Trust updates and double counting

The trust-update rule may consider failures, disconnections, saturation and policy violations, but must not cause the same latency or load effect to be counted again as an independent criterion in a subsequent decision without explicit justification.

- Type: Prohibition
- Category: Nodes and dynamic trust (`PolicyCategory_NODE`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-49`, `RNF-32`, `RNF-33`
- Recommended mechanisms: `M-AUD-01`, `M-TRUST-01`
- Catalogued queries: `EXT-Q40`

### P-NODE-05 — Trust-based ranking of eligible candidates

After hard filters are applied, eligible candidates must be ranked or prioritized using trust together with the required operational metrics. Saturated, unstable or historically unreliable nodes must be avoided when a better eligible alternative exists.

- Type: Obligation
- Category: Nodes and dynamic trust (`PolicyCategory_NODE`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-46`, `RF-47`, `RF-48`
- Recommended mechanisms: `M-NODE-02`, `M-TRUST-02`
- Catalogued queries: `BASE-Q19`, `EXT-Q42`, `EXT-Q44`

### P-NODE-06 — Absence of trustworthy alternatives

If no external node meets minimum eligibility and trust requirements, the system must not force a higher tier. It must prefer retention, local degradation or deferral and record the absence of alternatives.

- Type: Abstention
- Category: Nodes and dynamic trust (`PolicyCategory_NODE`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-47`, `RF-48`, `RF-53`
- Recommended mechanisms: `M-ADAPT-02`, `M-AUD-01`, `M-NODE-02`
- Catalogued queries: None declared

### P-OPS-01 — Versioned acceptance profile

Before an acceptance campaign, operational thresholds required by the non-functional requirements must be fixed and versioned, including at least local latency, maximum migration interruption, SPARQL monitoring time, decision time, energy consumption, concurrency, node onboarding, delegation depth and reselection time.

- Type: Obligation
- Category: Operations, scalability and QoS (`PolicyCategory_OPS`)
- Version: `POLICIES-REV-01`
- Related requirements: `RNF-01`, `RNF-02`, `RNF-04`, `RNF-05`, `RNF-06`, `RNF-08`, `RNF-09`, `RNF-14`, `RNF-21`, `RNF-39`
- Recommended mechanisms: `M-OPS-01`, `M-VAL-04`
- Catalogued queries: `EXT-Q65`, `EXT-Q76`

### P-OPS-02 — Horizontal scaling compatible with Fog and Cloud

The scalability policy must allow horizontal scaling in Cloud and, where supporting Fog infrastructure exists, in Fog as well. Cloud must not be assumed to be the only node type capable of elasticity.

- Type: Obligation
- Category: Operations, scalability and QoS (`PolicyCategory_OPS`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-17`, `RNF-07`
- Recommended mechanisms: `M-OPS-02`
- Catalogued queries: `BASE-Q02`, `BASE-Q29`

### P-OPS-03 — Dynamic node onboarding

A new Edge or Fog node must be able to register and enter evaluation without stopping the entire system and within the `T_node_join` limit set in the acceptance profile.

- Type: Obligation
- Category: Operations, scalability and QoS (`PolicyCategory_OPS`)
- Version: `POLICIES-REV-01`
- Related requirements: `RNF-09`, `RNF-10`
- Recommended mechanisms: `M-NODE-01`, `M-OPS-03`
- Catalogued queries: `BASE-Q02`

### P-OPS-04 — Continuity of critical functions

During partial failures, critical functions authorized for local execution must remain operational and pending data/events must retain integrity until synchronization or authorized disposal.

- Type: Obligation
- Category: Operations, scalability and QoS (`PolicyCategory_OPS`)
- Version: `POLICIES-REV-01`
- Related requirements: `RNF-12`, `RNF-13`
- Recommended mechanisms: `M-ADAPT-02`, `M-BUFFER-01`
- Catalogued queries: None declared

### P-OPS-05 — Minimum reproducible instrumentation

Evaluation scenarios must record the metrics needed to measure latency, energy consumption, model quality/accuracy, sleep/stress quality, migration cost, load, residual capacity and node trust.

- Type: Obligation
- Category: Operations, scalability and QoS (`PolicyCategory_OPS`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-29`, `RF-30`, `RNF-27`
- Recommended mechanisms: `M-METRIC-01`, `M-TIME-01`
- Catalogued queries: `BASE-Q07`, `BASE-Q09`, `BASE-Q33`, `EXT-Q54`

### P-OPS-06 — Restoration and safe buffer draining

Recovery from load or connectivity problems does not automatically authorize restoring the maximum processing level or draining all buffers. Restoration and synchronization must occur only while their enabling conditions remain valid for each service or pending data item.

- Type: Abstention
- Category: Operations, scalability and QoS (`PolicyCategory_OPS`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-08`, `RF-15`, `RF-26`, `RNF-12`
- Recommended mechanisms: `M-BUFFER-01`, `M-MODEL-04`, `M-TX-02`
- Catalogued queries: None declared

### P-VAL-01 — Reference endpoint and environment

The ontology must be exposed through SPARQL 1.1. Apache Jena Fuseki is the reference environment for reproducibility; other endpoints are equivalent only if they support the features used and pass the same validation battery.

- Type: Obligation
- Category: Validation, reproducibility and maintainability (`PolicyCategory_VAL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-69`, `RNF-24`, `RNF-26`, `RV-03`
- Recommended mechanisms: `M-VAL-01`
- Catalogued queries: `EXT-Q01`

### P-VAL-02 — Audit-query classification

Every validation query must be explicitly classified as inspection/reporting, warning or violation, and its interpretation criterion must be documented before it enters the baseline.

- Type: Obligation
- Category: Validation, reproducibility and maintainability (`PolicyCategory_VAL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-70`, `RF-71`, `RNF-31`, `RV-01`
- Recommended mechanisms: `M-VAL-02`
- Catalogued queries: None declared

### P-VAL-03 — Preconditions for interpreting zero rows

A zero-row result from a violation query must not be considered evidence of compliance unless correct dataset loading, the expected ontology version, minimum coverage and successful query execution have been checked first.

- Type: Prohibition
- Category: Validation, reproducibility and maintainability (`PolicyCategory_VAL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-71`, `RV-02`
- Recommended mechanisms: `M-VAL-03`
- Catalogued queries: `EXT-Q75`, `EXT-Q76`, `EXT-Q77`

### P-VAL-04 — Unambiguous artifact versioning

Every validation campaign must record unambiguous versions of the ontology, policies, queries, scenarios, acceptance profile and dataset. Generic references that do not identify a specific artifact are not valid for reproducibility.

- Type: Obligation
- Category: Validation, reproducibility and maintainability (`PolicyCategory_VAL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-68`, `RNF-39`, `RV-01`, `RV-03`
- Recommended mechanisms: `M-GOV-04`, `M-VAL-04`
- Catalogued queries: `EXT-Q01`, `EXT-Q77`

### P-VAL-05 — Baseline compatibility and major changes

An ontology, policy or query extension must not silently break declared baseline scenarios or queries. Every incompatible change must trigger a new major version and an explicit traceability update.

- Type: Prohibition
- Category: Validation, reproducibility and maintainability (`PolicyCategory_VAL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RNF-11`, `RNF-38`
- Recommended mechanisms: `M-VAL-04`, `M-VAL-05`
- Catalogued queries: None declared

### P-VAL-06 — Individual requirement traceability

The final documentation must maintain an individual matrix linking every RF, RNF and RV to applicable policies, responsible mechanisms, semantic or standard support, queries/validations and acceptance criteria.

- Type: Obligation
- Category: Validation, reproducibility and maintainability (`PolicyCategory_VAL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RV-04`, `RV-05`
- Recommended mechanisms: `M-VAL-05`
- Catalogued queries: `EXT-Q02`, `EXT-Q04`, `EXT-Q08`, `EXT-Q09`

### P-VAL-07 — Versioned reproducible scenarios

Scenarios S1–S17 must be defined in a versioned artifact or annex and executed against the same dataset, policy and query versions used for the validation campaign.

- Type: Obligation
- Category: Validation, reproducibility and maintainability (`PolicyCategory_VAL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-31`, `RF-72`, `RV-03`
- Recommended mechanisms: `M-VAL-04`, `M-VAL-06`
- Catalogued queries: `BASE-Q11`, `EXT-Q05`, `EXT-Q77`

### P-VAL-08 — Global compliance coverage

The validation campaign must produce coverage and overall compliance metrics for the required minimum areas: consent and contracts, policies and zones, trust, multicriteria decisions, differential privacy, pseudonymization/anonymization, temporary delegation and auditing. Metrics must identify the specific versions of the evaluated artifacts.

- Type: Obligation
- Category: Validation, reproducibility and maintainability (`PolicyCategory_VAL`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-68`, `RNF-39`, `RV-05`
- Recommended mechanisms: `M-VAL-04`, `M-VAL-07`
- Catalogued queries: `EXT-Q80`

### P-ZONE-01 — Restricted zone: local confinement

When processing originates in a restricted zone, user data and associated processing must not leave the local scope: Edge, Fog and Cloud are excluded. Receiving a generic model not derived from the user may be allowed only if an explicit zone policy authorizes inbound traffic and no user information is extracted.

- Type: Prohibition
- Category: Zones and georestriction (`PolicyCategory_ZONE`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-42`, `RF-43`, `RF-53`, `RNF-22`
- Recommended mechanisms: `M-CONS-02`, `M-ZONE-01`
- Catalogued queries: `BASE-Q18`, `BASE-Q34`, `EXT-Q22`, `EXT-Q36`, `EXT-Q37`, `EXT-Q56`

### P-ZONE-02 — Rural zone: retention by default

In a rural zone, pending data must be retained locally by default and transmitted only during a safe window satisfying connectivity, energy, effective authorization and destination eligibility requirements.

- Type: Obligation
- Category: Zones and georestriction (`PolicyCategory_ZONE`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-08`, `RF-26`, `RF-42`
- Recommended mechanisms: `M-BUFFER-01`, `M-TX-02`, `M-ZONE-01`
- Catalogued queries: `BASE-Q17`, `EXT-Q38`

### P-ZONE-03 — Urban zone: conditional aggregation

The presence of urban infrastructure does not itself authorize Edge/Fog aggregation or selection of higher tiers. Aggregation is permitted only when effective consent, the contract, active policy and destination eligibility allow it.

- Type: Abstention
- Category: Zones and georestriction (`PolicyCategory_ZONE`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-15`, `RF-36`, `RF-42`
- Recommended mechanisms: `M-CONS-02`, `M-NODE-02`, `M-ZONE-01`
- Catalogued queries: `EXT-Q39`

### P-ZONE-04 — Zone change and reevaluation

Every zone change that may alter authorization or tier eligibility must invalidate the previous decision and trigger reevaluation before new flows or external processing continue.

- Type: Obligation
- Category: Zones and georestriction (`PolicyCategory_ZONE`)
- Version: `POLICIES-REV-01`
- Related requirements: `RF-03`, `RF-15`, `RF-17`, `RNF-21`
- Recommended mechanisms: `M-CTX-01`, `M-MODEL-04`
- Catalogued queries: None declared

## Enforcement mechanisms

### M-ADAPT-01 — Migration/offloading evaluator

Compare continuity, cost, latency, energy and eligible destinations before triggering migration or offloading.

- Supported policies: `P-ADAPT-01`, `P-ADAPT-03`, `P-ADAPT-04`

### M-ADAPT-02 — Degradation manager

Reduce processing in a controlled manner, record the cause and preserve critical local functions when no valid external alternative exists.

- Supported policies: `P-ADAPT-02`, `P-ADAPT-03`, `P-ADAPT-06`, `P-DATA-06`

### M-ADAPT-03 — Migration executor

Execute migration as an action separate from delegation and federated learning, retaining a reference to the evaluation that authorized it.

- Supported policies: `P-ADAPT-05`

### M-AUD-01 — Semantic evaluation ticket

Persist inputs, alternatives, scores, trust, policies, the decision, time and executed action in EvaluationState.

- Supported policies: `P-ADAPT-04`, `P-ADAPT-06`, `P-AUD-06`, `P-FL-04`, `P-GOV-02`, `P-MODEL-05`, `P-MODEL-08`

### M-AUD-02 — Symptom–policy–action validator

Check that the selected policy and action are consistent with the detected symptom or condition.

- Supported policies: `P-AUD-05`

### M-AUD-03 — Decision-chain reconstruction

Traverse causal and temporal relationships from user/contract to the final action using values valid at the evaluated instant.

- Supported policies: `P-AUD-07`

### M-BUFFER-01 — Authorized retention

Select the highest permitted temporary-storage tier and maintain integrity until synchronization or authorized disposal.

- Supported policies: `P-DATA-05`, `P-OPS-04`, `P-ZONE-02`

### M-CONS-01 — Consent and contract resolution

Determine active consent, the effective contract per purpose, validity, data categories and authorized range.

- Supported policies: `P-CONS-01`, `P-CONS-02`, `P-CONS-03`

### M-CONS-02 — Effective authorization calculation

Calculate effective authorization as the intersection of active consent, the contract, zone and other hard constraints.

- Supported policies: `P-CONS-04`, `P-CONS-06`, `P-DATA-05`, `P-ZONE-03`

### M-CONS-03 — Required-range check

Compare the minimum range required by a resource/action with effective authorization before enabling it.

- Supported policies: `P-CONS-05`

### M-CTX-01 — Context-change detection

Detect mobility, zone changes, connectivity, load, battery and other changes capable of invalidating a decision.

- Supported policies: `P-MODEL-09`, `P-ZONE-04`

### M-DATA-01 — Raw/parameterized data classification

Classify data before any transfer and block raw physiological observations from leaving the local scope.

- Supported policies: `P-DATA-01`

### M-DATA-02 — Contextual tagging

Attach or link the minimum operational context needed to interpret each processed data item.

- Supported policies: `P-DATA-04`, `P-DATA-10`

### M-DELEG-01 — DelegationEvent creation

Create a delegation event with source, destination, cause, validFrom, recovery condition and planned expiration where present, leaving validTo unset while active.

- Supported policies: `P-ADAPT-07`, `P-AUD-01`, `P-AUD-02`

### M-DELEG-02 — Delegation closure

Close the delegation when recovery or expiration occurs and record validTo as the effective closure.

- Supported policies: `P-ADAPT-08`, `P-AUD-03`

### M-DELEG-03 — Delegation depth control

Check the chain's accumulated depth before creating a new delegation.

- Supported policies: `P-AUD-04`

### M-DEVICE-01 — Device-state monitoring

Read battery, connectivity, sensors and data availability to trigger energy and transmission rules.

- Supported policies: `P-DATA-06`

### M-FL-01 — Upstream federated-session manager

Create a federated session only after validating participants, authorization, zone, privacy and update type.

- Supported policies: `P-FL-01`, `P-FL-02`, `P-FL-07`

### M-FL-02 — Downstream distribution manager

Distribute improved generic models after verifying that they contain no individualized information and that the flow complies with active policies.

- Supported policies: `P-CONS-06`, `P-FL-06`

### M-FL-03 — Differential privacy enforcement

Apply noise and record the budget, noise level and privacy mechanism before releasing protected gradients.

- Supported policies: `P-FL-03`, `P-FL-05`, `P-MODEL-07`

### M-FL-04 — Epsilon accounting

Accumulate and validate epsilon-budget consumption by purpose, contract, session and policy.

- Supported policies: `P-FL-04`

### M-GOV-01 — Policy-type classifier

When creating or loading a policy, validate that it has exactly one formal type and that the type is permitted.

- Supported policies: `P-GOV-01`

### M-GOV-02 — Applicable-policy resolution

Resolve policies linked to the user, contract, zone, node, service, session or evaluation and retain their versions.

- Supported policies: `P-GOV-02`, `P-GOV-04`

### M-GOV-03 — Precedence engine

Combine applicable hard constraints and obtain their most restrictive intersection before performing any optimization.

- Supported policies: `P-CONS-04`, `P-GOV-03`

### M-GOV-04 — Policy-version recording

Persist the policy-set version used by each evaluation and validation campaign.

- Supported policies: `P-GOV-04`, `P-VAL-04`

### M-ID-01 — Outgoing-data pseudonymization/anonymization

Replace direct personal identifiers with pseudonymous or anonymous identifiers before authorizing an external flow.

- Supported policies: `P-DATA-02`, `P-FL-03`, `P-FL-05`

### M-INT-01 — Semantic interoperability checker

Check that artifacts use the declared standards and record alignments or justifications for custom concepts relative to existing vocabularies.

- Supported policies: `P-INT-01`

### M-INT-02 — Extensibility validator

Check that adding instances or specializations does not alter central abstractions or break reference scenarios unless an explicit major-version change is made.

- Supported policies: `P-INT-02`

### M-METRIC-01 — Metrics instrumentation

Record model, system and user metrics with common temporal/contextual references.

- Supported policies: `P-MODEL-08`, `P-OPS-05`

### M-MODEL-01 — Tier-alternative evaluation

Calculate the score of each eligible alternative and select the best according to the active policy.

- Supported policies: `P-MODEL-01`, `P-MODEL-05`, `P-MODEL-06`, `P-MODEL-07`

### M-MODEL-02 — AHP normalization

Validate that latency, privacy and quality weights are normalized and that trust is not mixed into them.

- Supported policies: `P-MODEL-02`, `P-MODEL-03`

### M-MODEL-03 — AHP consistency

Calculate and record the consistency metric/ratio and compare it with the configured threshold; label the method correctly if it is not AHP.

- Supported policies: `P-MODEL-04`

### M-MODEL-04 — Adaptive reselection

Invalidate and recalculate the selection when the conditions that made the previous decision valid change.

- Supported policies: `P-MODEL-09`, `P-OPS-06`, `P-ZONE-04`

### M-MODEL-05 — Versioning and rollback

Create identifiable model versions, record updates and allow rollback to an earlier valid version.

- Supported policies: `P-FL-08`

### M-NODE-01 — NodeState monitoring

Read node availability, load, communication, residual capacity, queue, operating status and trust.

- Supported policies: `P-NODE-01`, `P-OPS-03`

### M-NODE-02 — Node-eligibility filter

Exclude candidates that fail applicable operating-state, capacity, connectivity, authorization, zone or minimum-trust requirements.

- Supported policies: `P-NODE-01`, `P-NODE-02`, `P-NODE-06`

### M-OPS-01 — Acceptance-profile manager

Load and freeze the configurable acceptance-campaign thresholds together with their version.

- Supported policies: `P-OPS-01`

### M-OPS-02 — Elasticity and load manager

Apply horizontal scaling wherever compatible capacity exists and record degradation/migration when scaling is impossible or unauthorized.

- Supported policies: `P-ADAPT-03`, `P-OPS-02`

### M-OPS-03 — Dynamic node registration

Onboard a new node, validate its capabilities and make it eligible without stopping the entire system.

- Supported policies: `P-OPS-03`

### M-REPL-01 — Controlled idempotent replication

Identify intentional replicas, version them, detect accidental duplicates and make repeated synchronization executions idempotent.

- Supported policies: `P-ADAPT-08`, `P-DATA-08`

### M-SEC-01 — Cryptographic protection

Apply and verify the in-transit and at-rest encryption baseline for sensitive information and authorized buffers.

- Supported policies: `P-DATA-03`

### M-TIME-01 — Temporal state and contract management

Record validFrom; populate validTo only at effective closure and keep any planned expiration separate.

- Supported policies: `P-AUD-02`, `P-AUD-07`, `P-CONS-02`, `P-DATA-10`

### M-TRUST-01 — Trust calculation and update

Update the trust score from the historical window and versioned rule, retaining evidence of the factors used.

- Supported policies: `P-NODE-03`, `P-NODE-04`

### M-TRUST-02 — External trust-based ranking

Apply trust only to eligible candidates and outside AHP normalization.

- Supported policies: `P-ADAPT-07`, `P-MODEL-03`, `P-NODE-05`

### M-TX-01 — Transmission gate

Check data type, readiness, protected identity, authorization, zone, destination and redundancy rules before every transmission.

- Supported policies: `P-DATA-01`, `P-DATA-02`, `P-DATA-04`, `P-DATA-08`

### M-TX-02 — Reconnection and safe-window manager

Keep blocked flows pending and revalidate all conditions before resuming them after reconnection.

- Supported policies: `P-DATA-07`, `P-OPS-06`

### M-TX-03 — Criticality-based scheduler

Order pending data by criticality, constraints and transmission cost without allowing secondary data to displace critical data.

- Supported policies: `P-DATA-09`

### M-VAL-01 — SPARQL validation environment

Load the dataset and execute the battery on Fuseki as the reference, allowing comparison with equivalent endpoints.

- Supported policies: `P-VAL-01`

### M-VAL-02 — Query catalogue

Record each query's type, purpose, preconditions and interpretation criterion.

- Supported policies: `P-VAL-02`

### M-VAL-03 — Precondition validator

Check the dataset, version, coverage and successful execution before interpreting an empty violation-query result.

- Supported policies: `P-VAL-03`

### M-VAL-04 — Artifact-version recording

Persist unambiguous identifiers for the ontology, policies, queries, scenarios, dataset and acceptance profile used.

- Supported policies: `P-GOV-04`, `P-VAL-04`, `P-VAL-05`, `P-VAL-07`

### M-VAL-05 — Traceability matrix

Maintain the individual links between requirements, policies, mechanisms, semantic support, queries and acceptance criteria.

- Supported policies: `P-VAL-05`, `P-VAL-06`

### M-VAL-06 — Scenario runner

Load and execute the versioned set of scenarios S1–S17 with the selected campaign's artifacts.

- Supported policies: `P-VAL-07`

### M-VAL-07 — Compliance-metric aggregator

Calculate coverage by domain, count violations/warnings and link each result to the artifact versions used in the campaign.

- Supported policies: `P-VAL-08`

### M-ZONE-01 — Zone gate

Resolve the current zone and apply its restrictions before authorizing external storage, processing or transfer.

- Supported policies: `P-ZONE-01`, `P-ZONE-02`, `P-ZONE-03`
