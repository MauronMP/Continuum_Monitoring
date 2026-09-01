# Functional, non-functional and validation requirements

> Generated reference for release v3.0.0. Do not edit individual
> entries by hand. Regenerate with
> `.venv/bin/python tools/generate_reference_docs.py`.

Canonical source: `ontology/legacy/smartcity_continuum-v3.0.0.ttl`.

This manual lists every requirement represented by the executable
ontology. Links are direct RDF traceability assertions; the query
coverage list is derived from `queries/catalog.csv`.

| Family | Expected count |
|---|---:|
| Functional (`RF`) | 72 |
| Non-functional (`RNF`) | 39 |
| Validation (`RV`) | 5 |
| **Total** | **116** |

## Functional requirements

### RF-01 — RF-01

The system must register and manage wearable devices associated with an individual/agent, including at least smartwatches, smart rings and smart bands.

- Direct policies: None declared
- Direct mechanisms: None declared
- Catalogued queries: `BASE-Q01`, `BASE-Q03`

### RF-02 — RF-02

The system must identify the agent's approximate location and the architecture node to which the agent is connected: Mist, Edge, Fog or Cloud.

- Direct policies: None declared
- Direct mechanisms: None declared
- Catalogued queries: `BASE-Q02`, `BASE-Q20`, `BASE-Q23`

### RF-03 — RF-03

The system must detect changes in the agent's context, including movement, loss of connectivity, zone changes, changes in the proximity of nodes and transitions between urban, rural or restricted areas.

- Direct policies: `P-ZONE-04`
- Direct mechanisms: `M-CTX-01`, `M-MODEL-04`
- Catalogued queries: `BASE-Q09`, `BASE-Q23`

### RF-04 — RF-04

The system must monitor device state: battery, connectivity, active sensors, availability of parameterized data and local preprocessing capacity.

- Direct policies: `P-DATA-04`
- Direct mechanisms: `M-DATA-02`, `M-TX-01`
- Catalogued queries: `BASE-Q10`

### RF-05 — RF-05

The system must record the operational state of continuum nodes, including availability, load, communication, residual capacity, resource usage, request queues and operating status. `ComputeOnly` or `Inoperative` states must be explicitly detected so that orchestration can decide whether to delegate, isolate or exclude the node.

- Direct policies: `P-NODE-01`
- Direct mechanisms: `M-NODE-01`, `M-NODE-02`
- Catalogued queries: `BASE-Q02`, `BASE-Q07`, `BASE-Q26`, `EXT-Q41`

### RF-06 — RF-06

The system must capture physiological metrics relevant to stress and sleep, including heart rate, HRV, activity, sleep, movement, SpO2, temperature and electrodermal activity when the sensors are available.

- Direct policies: None declared
- Direct mechanisms: None declared
- Catalogued queries: `BASE-Q05`

### RF-07 — RF-07

The system must manage preprocessing and energy strategy according to context. When connectivity is limited or effective consent restricts processing to the local scope, data must be preprocessed on the device itself or in the Mist tier. When the battery is low, the system must reduce model complexity and non-critical transmissions; when the battery is critical, it must prioritize offloading to the highest authorized tier only if sufficient connectivity exists and consent, the contract and zone policy allow it. If the battery is critical and transfer is not authorized, it must apply local degradation and temporary retention.

- Direct policies: `P-ADAPT-02`, `P-DATA-06`
- Direct mechanisms: `M-ADAPT-02`, `M-BUFFER-01`, `M-DEVICE-01`
- Catalogued queries: None declared

### RF-08 — RF-08

The system must temporarily store data at the highest authorized tier when transmission is prevented by connectivity, energy, saturation, zone restrictions or consent. If effective consent or zone policy does not allow external storage, data must be retained exclusively on the device or within the authorized local scope until a safe transmission window becomes available.

- Direct policies: `P-DATA-05`, `P-OPS-06`, `P-ZONE-02`
- Direct mechanisms: `M-BUFFER-01`, `M-CONS-02`, `M-MODEL-04`, `M-TX-02`, `M-ZONE-01`
- Catalogued queries: `BASE-Q17`, `EXT-Q31`, `EXT-Q38`

### RF-09 — RF-09

The system must tag data with operational context: time, location, signal quality, device state, node state, processing level and purpose of use.

- Direct policies: `P-DATA-04`, `P-DATA-10`
- Direct mechanisms: `M-DATA-02`, `M-TIME-01`, `M-TX-01`
- Catalogued queries: `EXT-Q23`, `EXT-Q24`, `EXT-Q25`

### RF-10 — RF-10

The system must distinguish between raw physiological observations and transmissible parameterized data. For these requirements, the local scope is limited to the mobile/wearable device and, when policy permits, the associated Mist tier; raw physiological observations must not be transmitted to Edge, Fog or Cloud.

- Direct policies: `P-DATA-01`
- Direct mechanisms: `M-DATA-01`, `M-TX-01`
- Catalogued queries: `EXT-Q22`

### RF-11 — RF-11

The system must execute personalized inference models on the device or at nearby tiers to estimate stress and sleep quality.

- Direct policies: None declared
- Direct mechanisms: None declared
- Catalogued queries: `BASE-Q04`

### RF-12 — RF-12

The system must maintain a global general model trained in the Cloud tier, represented through general model and tier concepts rather than a specific instance.

- Direct policies: None declared
- Direct mechanisms: None declared
- Catalogued queries: `BASE-Q04`

### RF-13 — RF-13

The system must allow the general model to be adapted into personalized or degraded models at lower tiers.

- Direct policies: None declared
- Direct mechanisms: None declared
- Catalogued queries: `BASE-Q04`, `BASE-Q32`

### RF-14 — RF-14

The system must evaluate prediction quality and separately record prediction confidence, estimated error, local feedback and the observed quality of the model used. Weights used for multicriteria selection must not substitute for observed quality metrics.

- Direct policies: `P-MODEL-08`
- Direct mechanisms: `M-AUD-01`, `M-METRIC-01`
- Catalogued queries: `BASE-Q21`, `EXT-Q54`, `EXT-Q55`

### RF-15 — RF-15

The system must select the most suitable model tier among `LocalModelTier`, `EdgeModelTier`, `FogModelTier` and `CloudModelTier`, first applying hard constraints on consent, contracts, zones, availability and connectivity and then considering latency, privacy, model quality, load and trust among eligible alternatives. The selection must be reevaluated and replaceable when the conditions that made it valid change.

- Direct policies: `P-MODEL-01`, `P-MODEL-09`, `P-NODE-02`, `P-OPS-06`, `P-ZONE-03`, `P-ZONE-04`
- Direct mechanisms: `M-BUFFER-01`, `M-CONS-02`, `M-CTX-01`, `M-MODEL-01`, `M-MODEL-04`, `M-NODE-02`, `M-TX-02`, `M-ZONE-01`
- Catalogued queries: `BASE-Q21`, `EXT-Q46`

### RF-16 — RF-16

The system must dynamically decide when to migrate inference services between Mist, Edge, Fog and Cloud tiers.

- Direct policies: `P-ADAPT-01`, `P-ADAPT-04`, `P-ADAPT-05`
- Direct mechanisms: `M-ADAPT-01`, `M-ADAPT-03`, `M-AUD-01`, `M-FL-01`, `M-NODE-02`
- Catalogued queries: `BASE-Q13`, `EXT-Q59`, `EXT-Q60`, `EXT-Q61`

### RF-17 — RF-17

The system must migrate data, services or models when it detects low battery, excessive latency, loss of connectivity, saturation, a zone change or low trust in the current node, always within the constraints of RF-07, RF-35 and RF-42. Nodes in the `Inoperative` state must be excluded; `ComputeOnly` nodes may only be used for operations compatible with that state and must otherwise trigger delegation or isolation.

- Direct policies: `P-ADAPT-01`, `P-ADAPT-02`, `P-ADAPT-03`, `P-ADAPT-04`, `P-MODEL-09`, `P-NODE-01`, `P-OPS-02`, `P-ZONE-04`
- Direct mechanisms: `M-ADAPT-01`, `M-ADAPT-02`, `M-AUD-01`, `M-BUFFER-01`, `M-CTX-01`, `M-MODEL-04`, `M-NODE-01`, `M-NODE-02`, `M-OPS-02`
- Catalogued queries: `BASE-Q08`, `BASE-Q12`, `BASE-Q13`, `BASE-Q14`, `EXT-Q59`, `EXT-Q60`

### RF-18 — RF-18

The system must support computation offloading to nearby devices or Edge/Fog nodes when feasible and when it does not violate consent, zone policies or minimum trust requirements.

- Direct policies: `P-ADAPT-01`, `P-NODE-02`
- Direct mechanisms: `M-ADAPT-01`, `M-CONS-02`, `M-NODE-02`, `M-ZONE-01`
- Catalogued queries: `BASE-Q19`, `BASE-Q23`, `EXT-Q45`

### RF-19 — RF-19

The system must support controlled replication and synchronization of critical data, models and federated parameters, distinguishing intentional replicas from accidental duplicates and ensuring synchronization versioning and idempotency.

- Direct policies: `P-ADAPT-08`, `P-DATA-08`
- Direct mechanisms: `M-DELEG-02`, `M-REPL-01`, `M-TX-01`, `M-TX-02`
- Catalogued queries: `EXT-Q33`, `EXT-Q34`

### RF-20 — RF-20

Every model or service degradation must be recorded with an explicit cause.

- Direct policies: `P-ADAPT-03`, `P-ADAPT-06`
- Direct mechanisms: `M-ADAPT-01`, `M-ADAPT-02`, `M-AUD-01`, `M-OPS-02`
- Catalogued queries: `BASE-Q14`, `BASE-Q22`, `BASE-Q27`, `BASE-Q35`, `EXT-Q59`, `EXT-Q62`

### RF-21 — RF-21

The system must allow personalized models, parameters or gradients to be sent to higher tiers for additional training when consent, zone and privacy constraints permit it.

- Direct policies: `P-FL-01`, `P-FL-02`
- Direct mechanisms: `M-CONS-02`, `M-FL-01`, `M-NODE-02`, `M-ZONE-01`
- Catalogued queries: `BASE-Q16`, `BASE-Q24`, `BASE-Q25`, `EXT-Q66`, `EXT-Q67`

### RF-22 — RF-22

The system must support federated or hierarchical learning between devices and Edge, Fog and Cloud nodes.

- Direct policies: `P-ADAPT-05`, `P-FL-01`
- Direct mechanisms: `M-ADAPT-03`, `M-FL-01`, `M-NODE-02`
- Catalogued queries: `BASE-Q16`, `BASE-Q24`, `BASE-Q30`, `EXT-Q61`, `EXT-Q66`

### RF-23 — RF-23

The system must redistribute updated models to lower tiers without extending the current consent range, provided that the downstream flow complies with the semantic contract and active policies and does not carry personal data or individualized gradients.

- Direct policies: `P-CONS-06`, `P-FL-06`
- Direct mechanisms: `M-CONS-02`, `M-FL-02`, `M-ZONE-01`
- Catalogued queries: `EXT-Q66`

### RF-24 — RF-24

The system must version models, record their update dates and support rollback to previous versions in the event of degradation, errors or policy non-compliance.

- Direct policies: `P-FL-08`
- Direct mechanisms: `M-MODEL-05`, `M-VAL-04`
- Catalogued queries: `BASE-Q04`, `BASE-Q22`, `EXT-Q57`, `EXT-Q58`

### RF-25 — RF-25

Every HFL session must record the session time, participating nodes, updated model, type of data exchanged and privacy mechanisms where applicable.

- Direct policies: `P-ADAPT-05`, `P-FL-01`, `P-FL-07`
- Direct mechanisms: `M-ADAPT-03`, `M-AUD-01`, `M-FL-01`, `M-FL-02`, `M-NODE-02`
- Catalogued queries: `BASE-Q16`, `BASE-Q24`, `EXT-Q66`

### RF-26 — RF-26

The system must detect the available connection type or state, including stable, variable, intermittent, no connection, disconnected or airplane mode, and must support automatic reconnection and subsequent synchronization of pending items when an authorized, safe transmission window becomes available again.

- Direct policies: `P-ADAPT-08`, `P-DATA-05`, `P-DATA-07`, `P-OPS-06`, `P-ZONE-02`
- Direct mechanisms: `M-BUFFER-01`, `M-CONS-02`, `M-DELEG-02`, `M-MODEL-04`, `M-NODE-02`, `M-REPL-01`, `M-TX-02`, `M-ZONE-01`
- Catalogued queries: `BASE-Q10`

### RF-27 — RF-27

The system must adapt transmission frequency according to bandwidth, available energy, redundancy, data criticality, zone and consent.

- Direct policies: `P-DATA-04`, `P-DATA-06`, `P-DATA-07`, `P-DATA-09`
- Direct mechanisms: `M-ADAPT-02`, `M-BUFFER-01`, `M-CONS-02`, `M-DATA-02`, `M-DEVICE-01`, `M-NODE-02`, `M-TX-01`, `M-TX-02`, `M-TX-03`
- Catalogued queries: `BASE-Q10`, `BASE-Q17`, `EXT-Q23`, `EXT-Q38`

### RF-28 — RF-28

The system must prioritize critical data over secondary data, retaining redundant or non-transmissible data locally. Criticality must be represented through a generic classification applicable to any data; `StressCritical` may be used for stress but must not be the only prioritization mechanism.

- Direct policies: `P-DATA-08`, `P-DATA-09`
- Direct mechanisms: `M-BUFFER-01`, `M-REPL-01`, `M-TX-01`, `M-TX-03`
- Catalogued queries: `EXT-Q35`

### RF-29 — RF-29

The system must collect system metrics for computational stress studies, including resource usage, load, queues, latency, residual capacity and migration cost.

- Direct policies: `P-OPS-05`
- Direct mechanisms: `M-METRIC-01`, `M-TIME-01`
- Catalogued queries: `BASE-Q07`, `BASE-Q26`, `BASE-Q33`, `EXT-Q54`

### RF-30 — RF-30

The system must correlate physiological metrics with system metrics to study interactions between human stress, computational load, energy and connectivity, using common temporal and contextual references to determine which states and observations coexisted.

- Direct policies: `P-DATA-10`, `P-OPS-05`
- Direct mechanisms: `M-DATA-02`, `M-METRIC-01`, `M-TIME-01`
- Catalogued queries: `BASE-Q09`, `EXT-Q24`

### RF-31 — RF-31

The system must support simulation of urban scenarios with high mobility, high load, loss of connectivity, rural zones, restricted zones, Edge saturation and Edge-to-Fog migration. Scenarios S1–S17 must be defined in an unambiguously referenced, versioned artifact or annex to make this requirement reproducible.

- Direct policies: `P-VAL-07`
- Direct mechanisms: `M-VAL-04`, `M-VAL-06`
- Catalogued queries: `BASE-Q11`, `BASE-Q12`, `BASE-Q13`, `BASE-Q17`, `EXT-Q05`

### RF-32 — RF-32

The system must represent consent through a consent-aware model based on processing ranges, including local consent, community aggregation, global aggregation and explicit denial/revocation. Users must be able to grant or revoke authorization for data categories, purposes, validity intervals and the maximum permitted continuum range.

- Direct policies: `P-CONS-01`
- Direct mechanisms: `M-CONS-01`
- Catalogued queries: `BASE-Q01`, `BASE-Q15`, `BASE-Q25`, `BASE-Q31`, `EXT-Q11`, `EXT-Q13`

### RF-33 — RF-33

Every user must be linked to exactly one effective semantic contract per processing purpose at any given time. Historical contracts and contracts for different purposes are allowed, but their validity intervals must not result in more than one effective contract for the same user and purpose at the same instant.

- Direct policies: `P-CONS-02`
- Direct mechanisms: `M-CONS-01`, `M-TIME-01`
- Catalogued queries: `BASE-Q20`, `EXT-Q12`, `EXT-Q14`, `EXT-Q15`

### RF-34 — RF-34

The semantic contract must link the user, consent range, processing purpose and policies governing the processing.

- Direct policies: `P-CONS-03`
- Direct mechanisms: `M-CONS-01`, `M-GOV-02`
- Catalogued queries: `BASE-Q20`, `EXT-Q12`, `EXT-Q14`

### RF-35 — RF-35

The system must detect inconsistencies between the user's active consent and the range declared in the current semantic contract. Effective authorization must correspond to the most restrictive intersection of active consent, the contract and zone policy; while an inconsistency remains unresolved, external processing that could exceed any of those constraints must be blocked.

- Direct policies: `P-CONS-04`, `P-FL-02`, `P-GOV-03`, `P-MODEL-06`
- Direct mechanisms: `M-CONS-02`, `M-FL-01`, `M-GOV-03`, `M-MODEL-01`, `M-ZONE-01`
- Catalogued queries: `EXT-Q11`, `EXT-Q13`, `EXT-Q16`, `EXT-Q17`, `EXT-Q18`, `EXT-Q19`

### RF-36 — RF-36

The system must prevent selection of models or processing tiers that exceed the user's active consent range.

- Direct policies: `P-CONS-04`, `P-ZONE-03`
- Direct mechanisms: `M-CONS-02`, `M-GOV-03`, `M-NODE-02`, `M-ZONE-01`
- Catalogued queries: `BASE-Q15`, `BASE-Q25`, `BASE-Q28`, `EXT-Q17`, `EXT-Q18`, `EXT-Q19`, `EXT-Q20`

### RF-37 — RF-37

Every resource, policy, permission, model, service or session requiring consent must declare the minimum required range through `requiresConsentRange`.

- Direct policies: `P-CONS-05`
- Direct mechanisms: `M-CONS-03`
- Catalogued queries: `BASE-Q06`, `EXT-Q21`

### RF-38 — RF-38

Denial or revocation of upstream personal-data transmission must not prevent users from receiving improved generic models downstream, provided that the flow contains no personal data or individualized gradients and complies with the contract and active policies. This requirement complements RF-23 and does not authorize any additional upstream transfer.

- Direct policies: `P-CONS-06`, `P-FL-06`
- Direct mechanisms: `M-CONS-02`, `M-FL-02`, `M-ZONE-01`
- Catalogued queries: `BASE-Q15`

### RF-39 — RF-39

The system must represent policies as explicit, queryable semantic entities.

- Direct policies: `P-GOV-01`
- Direct mechanisms: `M-GOV-01`
- Catalogued queries: `EXT-Q03`, `EXT-Q06`, `EXT-Q10`

### RF-40 — RF-40

Every formal policy must be classified under exactly one semantic type: obligation, abstention or prohibition. In this model, an obligation requires an action to be performed; an abstention requires an optional action not to be performed unless explicitly enabled; a prohibition declares an action impermissible. The three types must be distinguishable and disjoint in validation.

- Direct policies: `P-GOV-01`
- Direct mechanisms: `M-GOV-01`
- Catalogued queries: `EXT-Q03`, `EXT-Q06`, `EXT-Q10`

### RF-41 — RF-41

The system must link users, nodes, zones, contracts or evaluations to specific policies through `governedBy`.

- Direct policies: `P-CONS-03`, `P-GOV-02`
- Direct mechanisms: `M-AUD-01`, `M-CONS-01`, `M-GOV-02`
- Catalogued queries: None declared

### RF-42 — RF-42

The system must apply zone-specific policies: local retention in rural zones, blocking external transfers in restricted zones and aggregation in urban zones only when effective consent and the contract authorize it. When zone, consent and contract impose different constraints, the most restrictive condition must always prevail.

- Direct policies: `P-FL-02`, `P-GOV-03`, `P-MODEL-06`, `P-ZONE-01`, `P-ZONE-02`, `P-ZONE-03`
- Direct mechanisms: `M-BUFFER-01`, `M-CONS-02`, `M-FL-01`, `M-GOV-03`, `M-MODEL-01`, `M-NODE-02`, `M-TX-02`, `M-ZONE-01`
- Catalogued queries: `BASE-Q18`, `BASE-Q34`, `EXT-Q36`, `EXT-Q37`, `EXT-Q39`

### RF-43 — RF-43

The system must block all processing or transfer outside the local scope defined in RF-10 when the source is in a `RestrictedZone`, including selection of Edge, Fog or Cloud tiers, unless an explicitly more restrictive policy imposes even less processing.

- Direct policies: `P-GOV-03`, `P-ZONE-01`
- Direct mechanisms: `M-CONS-02`, `M-GOV-03`, `M-ZONE-01`
- Catalogued queries: `BASE-Q18`, `BASE-Q34`, `EXT-Q36`, `EXT-Q37`

### RF-44 — RF-44

The system must record the specific policy applied in every evaluation, degradation, migration, delegation or model-selection decision.

- Direct policies: `P-ADAPT-06`, `P-GOV-02`
- Direct mechanisms: `M-ADAPT-02`, `M-AUD-01`, `M-GOV-02`
- Catalogued queries: None declared

### RF-45 — RF-45

Every `NodeState` used in MAPE-K decisions must record a historical trust value.

- Direct policies: `P-NODE-03`
- Direct mechanisms: `M-TRUST-01`, `M-VAL-04`
- Catalogued queries: `BASE-Q07`, `EXT-Q40`

### RF-46 — RF-46

Every evaluation that compares nodes must record a queryable trust value or weight used as a criterion external to the AHP calculation. Trust must be used to filter or rank eligible alternatives but must not be mixed with the AHP weights defined in RF-50.

- Direct policies: `P-MODEL-03`, `P-NODE-05`
- Direct mechanisms: `M-MODEL-02`, `M-NODE-02`, `M-TRUST-02`
- Catalogued queries: `EXT-Q44`

### RF-47 — RF-47

Node selection must first apply eligibility constraints for availability, connectivity, consent, zone and minimum capacity. Among eligible nodes, the system must prioritize those with higher trust and avoid saturated, unstable or historically unreliable nodes.

- Direct policies: `P-NODE-02`, `P-NODE-05`, `P-NODE-06`
- Direct mechanisms: `M-ADAPT-02`, `M-AUD-01`, `M-CONS-02`, `M-NODE-02`, `M-TRUST-02`, `M-ZONE-01`
- Catalogued queries: `BASE-Q08`, `BASE-Q19`, `EXT-Q41`, `EXT-Q42`

### RF-48 — RF-48

Every delegation must preferentially select, among eligible destinations, the node with the highest trust compatible with load, availability, connectivity, residual capacity and active constraints. The destination is not required to have a higher trust score than the source node when the source degradation has a cause other than trust.

- Direct policies: `P-ADAPT-07`, `P-NODE-05`, `P-NODE-06`
- Direct mechanisms: `M-ADAPT-02`, `M-AUD-01`, `M-DELEG-01`, `M-NODE-02`, `M-TRUST-02`
- Catalogued queries: `BASE-Q19`, `EXT-Q42`, `EXT-Q45`

### RF-49 — RF-49

The system must update a node's trust score from historical behavior, failures, disconnections, saturation and policy violations using a documented normalized scale, time window and update rule. If latency or load contributes to trust calculation, the subsequent decision must avoid counting the same effect twice as an independent criterion without explicit justification.

- Direct policies: `P-NODE-03`, `P-NODE-04`
- Direct mechanisms: `M-AUD-01`, `M-TRUST-01`, `M-VAL-04`
- Catalogued queries: `EXT-Q40`, `EXT-Q43`

### RF-50 — RF-50

Every `EvaluationState` using AHP must record normalized weights for latency, privacy and model quality. Their sum must equal 1 within the configured tolerance. Trust is treated as an external criterion under RF-46 and is not part of this normalization.

- Direct policies: `P-MODEL-02`, `P-MODEL-03`
- Direct mechanisms: `M-MODEL-02`, `M-TRUST-02`
- Catalogued queries: `EXT-Q48`

### RF-51 — RF-51

Every `EvaluationState` must record the AHP score of each evaluated tier alternative, the final selected tier and a justification that makes it possible to reconstruct why the chosen alternative outperformed the others.

- Direct policies: `P-AUD-06`, `P-MODEL-05`
- Direct mechanisms: `M-AUD-01`, `M-MODEL-01`
- Catalogued queries: `EXT-Q46`, `EXT-Q51`, `EXT-Q52`, `EXT-Q53`

### RF-52 — RF-52

The system must favor local or Edge models when the privacy weight is dominant or when consent does not allow global aggregation.

- Direct policies: `P-MODEL-01`, `P-MODEL-06`
- Direct mechanisms: `M-CONS-02`, `M-MODEL-01`, `M-NODE-02`, `M-ZONE-01`
- Catalogued queries: None declared

### RF-53 — RF-53

The system must allow selection of `CloudModelTier` only when effective consent, the contract, zone and trust permit it. Differential privacy is mandatory when the Cloud-bound operation involves federated learning, gradients or updates for which privacy policies require it; it must not be imposed as a generic condition on inference that does not carry such information.

- Direct policies: `P-MODEL-01`, `P-MODEL-07`, `P-NODE-06`, `P-ZONE-01`
- Direct mechanisms: `M-ADAPT-02`, `M-AUD-01`, `M-CONS-02`, `M-FL-03`, `M-MODEL-01`, `M-NODE-02`, `M-ZONE-01`
- Catalogued queries: `EXT-Q56`

### RF-54 — RF-54

The system must detect incomplete evaluations that omit applicable AHP weights, scores of evaluated alternatives, the selected tier, the applied policy, the semantic contract or the justification.

- Direct policies: `P-AUD-06`, `P-MODEL-05`
- Direct mechanisms: `M-AUD-01`, `M-MODEL-01`
- Catalogued queries: `EXT-Q47`, `EXT-Q53`, `EXT-Q55`, `EXT-Q71`

### RF-55 — RF-55

The system must warn about or invalidate an AHP evaluation when weights are not normalized, when the trust weight is included in AHP normalization or when AHP judgment inconsistency exceeds the configured threshold. The ontology must explicitly represent the consistency metric/ratio and the applied threshold; if pairwise comparisons and consistency checking are not used, the mechanism must be documented as weighted multicriteria scoring rather than AHP.

- Direct policies: `P-MODEL-02`, `P-MODEL-03`, `P-MODEL-04`
- Direct mechanisms: `M-MODEL-02`, `M-MODEL-03`, `M-TRUST-02`
- Catalogued queries: `EXT-Q44`, `EXT-Q48`, `EXT-Q49`, `EXT-Q50`

### RF-56 — RF-56

Every federated-learning session carrying gradients must declare a privacy budget and noise level.

- Direct policies: `P-FL-03`, `P-MODEL-07`
- Direct mechanisms: `M-FL-03`, `M-ID-01`, `M-MODEL-01`
- Catalogued queries: `BASE-Q16`, `EXT-Q67`, `EXT-Q69`

### RF-57 — RF-57

Every model gradient leaving a mobile device must have undergone anonymization and noise addition.

- Direct policies: `P-FL-03`
- Direct mechanisms: `M-FL-03`, `M-ID-01`
- Catalogued queries: `EXT-Q68`

### RF-58 — RF-58

Every protected FL session must be linked to an explicit privacy or anonymization mechanism.

- Direct policies: `P-FL-05`
- Direct mechanisms: `M-FL-03`, `M-ID-01`
- Catalogued queries: `BASE-Q16`, `EXT-Q68`

### RF-59 — RF-59

The system must control the differential-privacy epsilon budget according to the processing purpose, semantic contract and active policy.

- Direct policies: `P-FL-04`, `P-MODEL-07`
- Direct mechanisms: `M-AUD-01`, `M-FL-03`, `M-FL-04`, `M-MODEL-01`
- Catalogued queries: `BASE-Q24`, `EXT-Q69`

### RF-60 — RF-60

The system must prevent raw physiological observations from leaving the local scope defined in RF-10; therefore, they must not be transmitted to Edge, Fog or Cloud nodes. Only authorized parameterized data or model updates may leave the local scope.

- Direct policies: `P-DATA-01`
- Direct mechanisms: `M-DATA-01`, `M-TX-01`
- Catalogued queries: `BASE-Q18`, `BASE-Q28`, `EXT-Q22`, `EXT-Q37`

### RF-61 — RF-61

All parameterized data, gradients or updates transmitted outside the local scope must use pseudonymous or anonymized identifiers. Direct personal identifiers must not accompany parameterized data, gradients or federated updates, and a violation query must be available to detect any breach of this rule.

- Direct policies: `P-DATA-02`
- Direct mechanisms: `M-ID-01`, `M-TX-01`
- Catalogued queries: `BASE-Q01`, `BASE-Q28`, `EXT-Q23`, `EXT-Q26`, `EXT-Q27`, `EXT-Q28`

### RF-62 — RF-62

Every temporary delegation must be represented as an explicit semantic event.

- Direct policies: `P-ADAPT-05`, `P-ADAPT-07`, `P-AUD-01`
- Direct mechanisms: `M-ADAPT-03`, `M-DELEG-01`, `M-FL-01`, `M-TRUST-02`
- Catalogued queries: `BASE-Q14`, `EXT-Q63`

### RF-63 — RF-63

The delegation event must record the source, destination, cause, start of validity and recovery condition. `validTo` must represent the effective closure of the delegation and may remain unset while it is active. If a planned expiration differs from the actual closure, it must be represented by an additional explicit temporal limit rather than ambiguously reusing `validTo`.

- Direct policies: `P-AUD-02`
- Direct mechanisms: `M-DELEG-01`, `M-TIME-01`
- Catalogued queries: `EXT-Q63`, `EXT-Q64`

### RF-64 — RF-64

The system must close or invalidate a delegation when the source node's recovery condition is met or its planned expiration is reached. At that point, it must record `validTo` as the effective closure time.

- Direct policies: `P-AUD-03`
- Direct mechanisms: `M-DELEG-02`
- Catalogued queries: `EXT-Q63`

### RF-65 — RF-65

The system must represent detected MAPE-K symptoms and link them to policies and evaluations.

- Direct policies: `P-AUD-05`
- Direct mechanisms: `M-AUD-02`
- Catalogued queries: `BASE-Q14`, `BASE-Q35`, `EXT-Q72`

### RF-66 — RF-66

Every `EvaluationState` must act as a complete semantic audit ticket and record, at minimum, the symptom, applied policy, contract, effective consent, selected tier, justification, decision time and a reference to the action ultimately executed.

- Direct policies: `P-ADAPT-06`, `P-AUD-05`, `P-AUD-06`
- Direct mechanisms: `M-ADAPT-02`, `M-AUD-01`, `M-AUD-02`
- Catalogued queries: `BASE-Q21`, `EXT-Q17`, `EXT-Q20`, `EXT-Q46`, `EXT-Q47`, `EXT-Q59`, `EXT-Q71`, `EXT-Q72`

### RF-67 — RF-67

The system must be able to reconstruct the complete decision chain: user → contract → effective consent → purpose → zone → policy → node state → AHP alternatives and scores → external trust → selected tier → executed action, preserving the causal and temporal relationships needed to identify which information was valid at the decision time.

- Direct policies: `P-AUD-05`, `P-AUD-07`
- Direct mechanisms: `M-AUD-02`, `M-AUD-03`, `M-TIME-01`
- Catalogued queries: `BASE-Q35`, `EXT-Q70`

### RF-68 — RF-68

The system must generate architecture-wide compliance metrics through SPARQL coverage and validation queries. The set of critical classes and properties must be identified by the specific ontology version loaded and recorded in the traceability matrix; it must not depend on an ambiguous reference such as 'v2.1' without identifying the corresponding artifact.

- Direct policies: `P-VAL-04`, `P-VAL-08`
- Direct mechanisms: `M-GOV-04`, `M-VAL-04`, `M-VAL-07`
- Catalogued queries: `BASE-Q31`, `BASE-Q32`, `EXT-Q01`, `EXT-Q02`, `EXT-Q80`

### RF-69 — RF-69

The system must expose the ontology through a SPARQL 1.1 endpoint. Apache Jena Fuseki is the reference environment for reproducibility; equivalent endpoints may be used in operation provided they remain compatible with RDF/OWL/Turtle and SPARQL 1.1 and pass the same validation battery.

- Direct policies: `P-VAL-01`
- Direct mechanisms: `M-VAL-01`
- Catalogued queries: None declared

### RF-70 — RF-70

The system must provide inspection queries to list users, devices, nodes, models, states, policies, contracts, FL sessions and delegations.

- Direct policies: `P-VAL-02`
- Direct mechanisms: `M-VAL-02`
- Catalogued queries: `BASE-Q01`, `BASE-Q02`, `BASE-Q03`, `BASE-Q04`, `BASE-Q05`, `BASE-Q06`, `BASE-Q07`, `BASE-Q20`, `EXT-Q03`

### RF-71 — RF-71

The system must provide violation queries whose zero-row result may be interpreted as compliance only after verifying that the required dataset is loaded, the ontology version is the expected one, minimum coverage data exist and the query executed successfully. An empty result without these preconditions is not sufficient evidence of compliance.

- Direct policies: `P-VAL-02`, `P-VAL-03`
- Direct mechanisms: `M-VAL-02`, `M-VAL-03`
- Catalogued queries: `EXT-Q75`, `EXT-Q77`, `EXT-Q80`

### RF-72 — RF-72

The system must support validation of operational and scientific scenarios through reproducible SPARQL queries, using the versioned scenario artifact required by RF-31 and the reference environment defined in RF-69.

- Direct policies: `P-VAL-07`
- Direct mechanisms: `M-VAL-04`, `M-VAL-06`
- Catalogued queries: `BASE-Q11`, `EXT-Q05`, `EXT-Q77`

## Non-functional requirements

### RNF-01 — RNF-01

Local inference latency on the device or Mist tier must be ≤100 ms at the 95th percentile under the reference hardware/model profile. If a deployment requires a different value, it must explicitly declare `T_inference_local` before validation and must not change it during the acceptance campaign.

- Direct policies: `P-OPS-01`
- Direct mechanisms: `M-OPS-01`, `M-VAL-04`
- Catalogued queries: `EXT-Q76`

### RNF-02 — RNF-02

A service migration or delegation must not cause an interruption longer than `T_migration_max` or the loss of decisions or events marked as critical.

- Direct policies: `P-ADAPT-04`, `P-ADAPT-08`, `P-OPS-01`
- Direct mechanisms: `M-ADAPT-01`, `M-AUD-01`, `M-DELEG-02`, `M-NODE-02`, `M-OPS-01`, `M-REPL-01`, `M-TX-02`, `M-VAL-04`
- Catalogued queries: `EXT-Q76`

### RNF-03 — RNF-03

Peak-load scenarios must maintain service within the limits declared in the acceptance profile and, when degradation, migration, delegation or retention is necessary, degradation must be controlled and auditable.

- Direct policies: `P-ADAPT-01`, `P-ADAPT-03`
- Direct mechanisms: `M-ADAPT-01`, `M-ADAPT-02`, `M-NODE-02`, `M-OPS-02`
- Catalogued queries: None declared

### RNF-04 — RNF-04

Basic monitoring SPARQL queries used by the MAPE-K cycle must complete within `T_sparql_monitor` at the 95th percentile over the reference dataset.

- Direct policies: `P-OPS-01`
- Direct mechanisms: `M-OPS-01`, `M-VAL-04`
- Catalogued queries: `EXT-Q76`

### RNF-05 — RNF-05

AHP multicriteria score calculation and application of the external trust criterion must complete within `T_decision_max` so as not to exceed the adaptation interval defined by the active policy.

- Direct policies: `P-MODEL-03`, `P-OPS-01`
- Direct mechanisms: `M-MODEL-02`, `M-OPS-01`, `M-TRUST-02`, `M-VAL-04`
- Catalogued queries: `EXT-Q76`

### RNF-06 — RNF-06

Device energy consumption under the reference scenario must remain within `E_device_max`, with consumption or its effect on battery life recorded reproducibly. Low-battery strategies must not increase non-critical transmissions relative to normal mode.

- Direct policies: `P-DATA-06`, `P-OPS-01`
- Direct mechanisms: `M-ADAPT-02`, `M-BUFFER-01`, `M-DEVICE-01`, `M-OPS-01`, `M-VAL-04`
- Catalogued queries: `EXT-Q76`

### RNF-07 — RNF-07

The architecture must allow horizontal scaling in Cloud and, when Fog infrastructure is available, in Fog, without modifying the central conceptual model.

- Direct policies: `P-OPS-02`
- Direct mechanisms: `M-OPS-02`
- Catalogued queries: `BASE-Q29`

### RNF-08 — RNF-08

The concurrency target must be expressed through the explicit value `N_agents` rather than ambiguous terms such as 'thousands of agents'; the load campaign must demonstrate concurrent operation with at least that number.

- Direct policies: `P-OPS-01`
- Direct mechanisms: `M-OPS-01`, `M-VAL-04`
- Catalogued queries: `EXT-Q76`

### RNF-09 — RNF-09

Onboarding a new Edge or Fog node must not require stopping the entire system, and the node must become available for evaluation within `T_node_join` after registration and validation are complete.

- Direct policies: `P-OPS-01`, `P-OPS-03`
- Direct mechanisms: `M-NODE-01`, `M-OPS-01`, `M-OPS-03`, `M-VAL-04`
- Catalogued queries: `EXT-Q76`

### RNF-10 — RNF-10

The ontology must support adding new users, nodes, sensors, models, policies and contracts through instance extensions or compatible specializations, without modifying the central conceptual abstractions used by existing scenarios.

- Direct policies: `P-INT-02`, `P-OPS-03`
- Direct mechanisms: `M-INT-02`, `M-NODE-01`, `M-OPS-03`, `M-VAL-05`
- Catalogued queries: None declared

### RNF-11 — RNF-11

The query battery must support new `BASE-Q` or `EXT-Q` blocks without changing the meaning or breaking the execution of existing baseline queries.

- Direct policies: `P-VAL-05`
- Direct mechanisms: `M-VAL-04`, `M-VAL-05`
- Catalogued queries: None declared

### RNF-12 — RNF-12

During partial connectivity failures, critical functions authorized for local execution must remain operational and pending data must retain integrity until synchronization or authorized disposal.

- Direct policies: `P-ADAPT-02`, `P-DATA-05`, `P-DATA-07`, `P-FL-01`, `P-NODE-01`, `P-OPS-04`, `P-OPS-06`
- Direct mechanisms: `M-ADAPT-02`, `M-BUFFER-01`, `M-CONS-02`, `M-FL-01`, `M-MODEL-04`, `M-NODE-01`, `M-NODE-02`, `M-TX-02`, `M-ZONE-01`
- Catalogued queries: `BASE-Q08`, `EXT-Q31`, `EXT-Q32`

### RNF-13 — RNF-13

Reconnection, synchronization, migration and delegation processes must not lose critical events or create accidental duplicates; repeated executions must be idempotent where applicable.

- Direct policies: `P-ADAPT-08`, `P-DATA-07`, `P-DATA-08`, `P-OPS-04`
- Direct mechanisms: `M-ADAPT-02`, `M-BUFFER-01`, `M-CONS-02`, `M-DELEG-02`, `M-NODE-02`, `M-REPL-01`, `M-TX-01`, `M-TX-02`
- Catalogued queries: `EXT-Q33`, `EXT-Q34`

### RNF-14 — RNF-14

Temporary delegation must limit propagation to a maximum depth of `D_delegation_max` or another explicit policy-defined stopping condition, preventing unbounded saturation cascades.

- Direct policies: `P-ADAPT-07`, `P-AUD-04`, `P-OPS-01`
- Direct mechanisms: `M-DELEG-01`, `M-DELEG-03`, `M-OPS-01`, `M-TRUST-02`, `M-VAL-04`
- Catalogued queries: `EXT-Q65`, `EXT-Q76`

### RNF-15 — RNF-15

Sensitive data must be encrypted in transit and at rest according to the deployment's versioned security baseline; the acceptance campaign must verify that no channel or storage classified as sensitive operates outside that baseline.

- Direct policies: `P-DATA-03`
- Direct mechanisms: `M-SEC-01`, `M-VAL-04`
- Catalogued queries: `EXT-Q29`, `EXT-Q30`, `EXT-Q32`

### RNF-16 — RNF-16

All federated sessions for which policies require differential privacy must include a queryable privacy budget, noise level and privacy mechanism.

- Direct policies: `P-FL-03`, `P-FL-07`
- Direct mechanisms: `M-AUD-01`, `M-FL-01`, `M-FL-02`, `M-FL-03`, `M-ID-01`
- Catalogued queries: `EXT-Q68`

### RNF-17 — RNF-17

There must be zero external transmissions of raw physiological observations and zero associations of direct personal identifiers with parameterized data, gradients or federated updates.

- Direct policies: `P-DATA-01`, `P-DATA-02`, `P-FL-03`, `P-FL-06`
- Direct mechanisms: `M-CONS-02`, `M-DATA-01`, `M-FL-02`, `M-FL-03`, `M-ID-01`, `M-TX-01`, `M-ZONE-01`
- Catalogued queries: `EXT-Q22`, `EXT-Q27`, `EXT-Q28`

### RNF-18 — RNF-18

The differential-privacy budget must be explicit and auditable for all applicable operations, including its links to purpose, contract and policy.

- Direct policies: `P-FL-04`
- Direct mechanisms: `M-AUD-01`, `M-FL-04`
- Catalogued queries: `EXT-Q69`

### RNF-19 — RNF-19

Anonymization, pseudonymization and differential-privacy mechanisms used by the system must be represented semantically or verifiably referenced from the corresponding session/flow, and must not depend solely on unlinked external documentation.

- Direct policies: `P-DATA-02`, `P-FL-05`
- Direct mechanisms: `M-FL-03`, `M-ID-01`, `M-TX-01`
- Catalogued queries: `EXT-Q26`, `EXT-Q68`

### RNF-20 — RNF-20

Adaptation policies must be configurable or versionable without modifying the ontology's central conceptual structure.

- Direct policies: `P-GOV-04`
- Direct mechanisms: `M-GOV-02`, `M-GOV-04`, `M-VAL-04`
- Catalogued queries: `EXT-Q10`

### RNF-21 — RNF-21

When context, consent, contract, zone, connectivity or trust changes and the current selection becomes invalid, reevaluation must produce a new decision within `T_reselection_max`.

- Direct policies: `P-MODEL-09`, `P-OPS-01`, `P-ZONE-04`
- Direct mechanisms: `M-CTX-01`, `M-MODEL-04`, `M-OPS-01`, `M-VAL-04`
- Catalogued queries: `EXT-Q76`

### RNF-22 — RNF-22

Constraint precedence must be deterministic: given the same states, contract, consent, zone and policy version, the system must produce the same eligibility decision and record the same applied precedence rule.

- Direct policies: `P-CONS-04`, `P-GOV-03`, `P-GOV-04`, `P-ZONE-01`
- Direct mechanisms: `M-CONS-02`, `M-GOV-02`, `M-GOV-03`, `M-GOV-04`, `M-VAL-04`, `M-ZONE-01`
- Catalogued queries: `EXT-Q07`, `EXT-Q15`, `EXT-Q78`, `EXT-Q79`

### RNF-23 — RNF-23

Adding a new wearable-device type must be possible through the provided interfaces/adapters without modifying the conceptual core of user, device, observation and state.

- Direct policies: `P-INT-02`
- Direct mechanisms: `M-INT-02`, `M-VAL-05`
- Catalogued queries: None declared

### RNF-24 — RNF-24

Semantic representation and querying must use open standards compatible with RDF/OWL/Turtle and SPARQL 1.1.

- Direct policies: `P-INT-01`, `P-VAL-01`
- Direct mechanisms: `M-INT-01`, `M-VAL-01`
- Catalogued queries: None declared

### RNF-25 — RNF-25

The ontology must reuse standard vocabularies where applicable, including SOSA/SSN, SAREF, FOAF and GeoSPARQL, avoiding duplication of equivalent concepts without documented justification.

- Direct policies: `P-INT-01`
- Direct mechanisms: `M-INT-01`, `M-VAL-01`
- Catalogued queries: `BASE-Q05`

### RNF-26 — RNF-26

The RDF/OWL representation must be loadable and queryable by standard reasoners and SPARQL endpoints compatible with the features used by the ontology.

- Direct policies: `P-INT-01`, `P-VAL-01`
- Direct mechanisms: `M-INT-01`, `M-VAL-01`
- Catalogued queries: None declared

### RNF-27 — RNF-27

Instrumentation must measure, at minimum, latency, energy consumption, model accuracy/quality, sleep/stress quality, migration cost, load, residual capacity and node trust during evaluation scenarios.

- Direct policies: `P-DATA-10`, `P-MODEL-08`, `P-OPS-05`
- Direct mechanisms: `M-AUD-01`, `M-DATA-02`, `M-METRIC-01`, `M-TIME-01`
- Catalogued queries: `BASE-Q33`, `EXT-Q54`

### RNF-28 — RNF-28

All MAPE-K decisions classified as relevant to adaptation must be represented by a complete `EvaluationState` as specified in RF-66.

- Direct policies: `P-AUD-06`, `P-GOV-02`
- Direct mechanisms: `M-AUD-01`, `M-GOV-02`
- Catalogued queries: `EXT-Q20`, `EXT-Q47`, `EXT-Q71`

### RNF-29 — RNF-29

Every tier selection must include a readable semantic justification, the evaluated alternatives and their scores, so that the decision can be explained without inferring missing information.

- Direct policies: `P-AUD-06`, `P-MODEL-05`
- Direct mechanisms: `M-AUD-01`, `M-MODEL-01`
- Catalogued queries: `EXT-Q51`, `EXT-Q52`, `EXT-Q71`

### RNF-30 — RNF-30

A decision must be reconstructible retrospectively from persisted semantic information and its temporal relationships, without depending on external logs that are not linked to the model.

- Direct policies: `P-AUD-07`, `P-GOV-02`
- Direct mechanisms: `M-AUD-01`, `M-AUD-03`, `M-GOV-02`, `M-TIME-01`
- Catalogued queries: `EXT-Q70`

### RNF-31 — RNF-31

The audit battery must unambiguously distinguish inspection, warning and violation queries, and each query must document its type and interpretation criterion.

- Direct policies: `P-VAL-02`
- Direct mechanisms: `M-VAL-02`
- Catalogued queries: None declared

### RNF-32 — RNF-32

The trust score used in a decision must be queryable together with the version or historical window that produced it, enabling scientific reproducibility of node selection.

- Direct policies: `P-AUD-07`, `P-NODE-03`, `P-NODE-04`
- Direct mechanisms: `M-AUD-01`, `M-AUD-03`, `M-TIME-01`, `M-TRUST-01`, `M-VAL-04`
- Catalogued queries: `EXT-Q40`, `EXT-Q43`

### RNF-33 — RNF-33

Given the same alternatives, metrics, AHP weights, consistency threshold and external trust criterion, the multicriteria decision result must be reproducible.

- Direct policies: `P-AUD-07`, `P-MODEL-03`, `P-MODEL-05`, `P-NODE-04`
- Direct mechanisms: `M-AUD-01`, `M-AUD-03`, `M-MODEL-01`, `M-MODEL-02`, `M-TIME-01`, `M-TRUST-01`, `M-TRUST-02`
- Catalogued queries: `EXT-Q49`, `EXT-Q52`

### RNF-34 — RNF-34

AHP evaluations must satisfy weight normalization and the configured consistency threshold. If the mechanism does not use pairwise comparisons, the documentation and ontology must call it weighted multicriteria scoring rather than AHP.

- Direct policies: `P-MODEL-02`, `P-MODEL-04`
- Direct mechanisms: `M-MODEL-02`, `M-MODEL-03`
- Catalogued queries: `EXT-Q48`, `EXT-Q49`, `EXT-Q50`, `EXT-Q76`

### RNF-35 — RNF-35

States must be modeled as first-class temporal entities and must be distinguishable from instantaneous observations or static values.

- Direct policies: `P-GOV-05`
- Direct mechanisms: `M-TIME-01`
- Catalogued queries: `BASE-Q09`, `EXT-Q73`

### RNF-36 — RNF-36

Every new state must record `validFrom`; when a state ends, it must record `validTo`, without reusing `validTo` for a planned expiration that differs from effective closure.

- Direct policies: `P-AUD-02`, `P-AUD-03`, `P-CONS-02`, `P-GOV-05`
- Direct mechanisms: `M-CONS-01`, `M-DELEG-01`, `M-DELEG-02`, `M-TIME-01`
- Catalogued queries: `EXT-Q73`, `EXT-Q74`

### RNF-37 — RNF-37

When a state is derived from an observation, an explicit `derivedFrom` or equivalent link must make the source evidence discoverable.

- Direct policies: `P-GOV-05`
- Direct mechanisms: `M-TIME-01`
- Catalogued queries: None declared

### RNF-38 — RNF-38

Extensions to the ontology, policies or queries must not break baseline scenarios or queries; any intentional breaking change must trigger a new major version and an explicit update of the traceability matrix.

- Direct policies: `P-FL-08`, `P-GOV-04`, `P-INT-02`, `P-VAL-05`
- Direct mechanisms: `M-GOV-02`, `M-GOV-04`, `M-INT-02`, `M-MODEL-05`, `M-VAL-04`, `M-VAL-05`
- Catalogued queries: None declared

### RNF-39 — RNF-39

Ontology, policy, query and scenario version identifiers used in a validation campaign must be recorded unambiguously to avoid references such as 'v2.1' without an associated artifact.

- Direct policies: `P-DATA-03`, `P-FL-08`, `P-GOV-04`, `P-OPS-01`, `P-VAL-04`, `P-VAL-08`
- Direct mechanisms: `M-GOV-02`, `M-GOV-04`, `M-MODEL-05`, `M-OPS-01`, `M-SEC-01`, `M-VAL-04`, `M-VAL-07`
- Catalogued queries: `EXT-Q01`, `EXT-Q08`, `EXT-Q77`

## Validation requirements

### RV-01 — RV-01

The architecture must be validated through a documented, versioned and reproducible battery of SPARQL queries.

- Direct policies: `P-VAL-02`, `P-VAL-04`
- Direct mechanisms: `M-GOV-04`, `M-VAL-02`, `M-VAL-04`
- Catalogued queries: `EXT-Q01`, `EXT-Q75`, `EXT-Q80`

### RV-02 — RV-02

For violation queries, zero rows means compliance only after the dataset-loading, ontology-version, minimum-coverage and successful-execution checks defined in RF-71 have passed.

- Direct policies: `P-VAL-03`
- Direct mechanisms: `M-VAL-03`
- Catalogued queries: `EXT-Q77`

### RV-03 — RV-03

Experimental scenarios must be reproducible in Apache Jena Fuseki as the reference environment, loading the same versions of the TTL/dataset, policies, scenarios and queries. Other endpoints may additionally be used if they produce equivalent results for the reference battery.

- Direct policies: `P-VAL-01`, `P-VAL-04`, `P-VAL-07`
- Direct mechanisms: `M-GOV-04`, `M-VAL-01`, `M-VAL-04`, `M-VAL-06`
- Catalogued queries: `EXT-Q01`, `EXT-Q05`, `EXT-Q77`

### RV-04 — RV-04

The documentation must include an individual traceability matrix linking each requirement to the supporting ontology elements or standards, associated policies where present, responsible mechanism or block, queries/validations and acceptance criterion.

- Direct policies: `P-GOV-04`, `P-VAL-06`
- Direct mechanisms: `M-GOV-02`, `M-GOV-04`, `M-VAL-04`, `M-VAL-05`
- Catalogued queries: `EXT-Q02`, `EXT-Q04`, `EXT-Q07`, `EXT-Q08`, `EXT-Q09`

### RV-05 — RV-05

Validation must cover at least consent, contracts, policies and zones, trust, AHP decisions, differential privacy, pseudonymization/anonymization, temporary delegation and semantic auditing.

- Direct policies: `P-VAL-06`, `P-VAL-08`
- Direct mechanisms: `M-VAL-04`, `M-VAL-05`, `M-VAL-07`
- Catalogued queries: `EXT-Q80`
