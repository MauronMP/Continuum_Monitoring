# Continuum Monitoring Ontology v3.0.0 reference

> Generated reference for release v3.0.0. Do not edit individual
> entries by hand. Regenerate with
> `.venv/bin/python tools/generate_reference_docs.py`.

Canonical source: `ontology/legacy/smartcity_continuum-v3.0.0.ttl`.

## Scope

The ontology models policy-aware monitoring and adaptation across
IoT, mist, edge, fog and cloud. The reusable core covers topology,
temporal state, consent, contracts, authorization, trust, policy
governance, MAPE-K adaptation, delegation, model selection,
federated learning, audit and validation. The wellbeing domain
adds wearables, physiological observations, stress and sleep.

Hard constraints are evaluated before optimization. Consent,
contract, zone and security remain independent normative sources.
Decisions are reified so their inputs, alternatives, selected tier,
policies, trust evidence and resulting action can be audited.

## Standards and serialization

- RDF 1.1 and Turtle for serialization.
- OWL 2 DL modeling, with an optional HermiT release check.
- SHACL for closed-world structural validation.
- SPARQL 1.1 for inventory, reports, review gates and violations.
- SOSA/SSN, SAREF, FOAF and GeoSPARQL reuse where applicable.

## Runtime modules

| Area | Runtime artefacts |
|---|---|
| Core schema | `ontology/core/schema.ttl` |
| Shared modules | `ontology/modules/*.ttl` |
| Wellbeing extension | `ontology/domains/wellbeing/*.ttl` |
| SHACL constraints | `ontology/shapes/*.ttl` |
| Reference individuals | `ontology/examples/reference-system.ttl` |
| Tier profiles | `ontology/profiles/*.ttl` |
| Protégé source | `ontology/legacy/smartcity_continuum-v3.0.0.ttl` |

## Release inventory

- Ontology declarations: **1**
- OWL classes: **142**
- Object properties: **162**
- Datatype properties: **95**
- Annotation properties: **14**
- Requirements: **116** (`72 RF + 39 RNF + 5 RV`)
- Policies: **79**
- Mechanisms: **55**
- Scenarios: **17**
- SPARQL queries: **115**

## Validation workflow

```bash
.venv/bin/continuum-bench validate
python3 tools/check_owl_consistency.py --require-dl-profile \
  --output outputs/validation/ontology-hermit.json
```

The first command validates parsing, release contracts, query
expectations, SHACL, RDFLib RDFS/OWL RL profiles and distributed
fragment reconstruction. The second is the independent OWL 2 DL
consistency/profile gate and requires Java plus Protégé/HermiT.

## Known limits

- Open-world OWL consistency is not equivalent to SHACL or
  zero-row violation-query compliance.
- Acceptance review queries `EXT-Q76` and `EXT-Q77` identify
  campaign parameters that must be supplied before publication.
- Distributed profiles are materialized locally; the benchmark
  does not implement runtime resolution of remote `owl:imports`.
- The wellbeing vocabulary is a domain extension and is not
  required by continuum deployments in other application domains.

## Complete class catalog

| Term | English label |
|---|---|
| `AccelerometerSensor` | Accelerometer Sensor |
| `AcceptanceProfile` | Acceptance Profile |
| `AdaptabilityLevel` | Adaptability Level |
| `AdaptationAction` | Adaptation Action |
| `AIModel` | AI Model |
| `AnonymousIdentifier` | Anonymous Identifier |
| `Artifact` | Artifact |
| `AuthorizationDecision` | Authorization Decision |
| `AuthorizationOutcome` | Authorization Outcome |
| `AvailabilityLevel` | Availability Level |
| `BatteryLevel` | Battery Level |
| `BufferRecord` | Buffer Record |
| `CityArea` | City Area |
| `CloudNode` | Cloud Node |
| `CommunicationLevel` | Communication Level |
| `Community` | Community |
| `ComplianceMetric` | Compliance Metric |
| `ComputationalNode` | Computational Node |
| `ConflictResolutionStrategy` | Conflict Resolution Strategy |
| `ConsentRange` | Consent Range |
| `ConsentRecord` | Consent Record |
| `DataCategory` | Data Category |
| `DataContext` | Data Context |
| `DataCriticality` | Data Criticality |
| `DataSensitivity` | Data Sensitivity |
| `DecisionAlternative` | Decision Alternative |
| `DecisionMethod` | Decision Method |
| `DegradationEvent` | Degradation Event |
| `DelegationEvent` | Delegation Event |
| `Device` | Device |
| `DeviceConnectionStatus` | Device Connection Status |
| `DeviceState` | Device State |
| `DifferentialPrivacyMechanism` | Differential Privacy Mechanism |
| `DirectIdentifier` | Direct Identifier |
| `DistanceLevel` | Distance Level |
| `EDASensor` | EDA Sensor |
| `EdgeNode` | Edge Node |
| `EncryptionMechanism` | Encryption Mechanism |
| `EnergyLevel` | Energy Level |
| `EvaluationState` | Evaluation State |
| `Feature` | Feature |
| `FederatedLearningSession` | Federated Learning Session |
| `FogNode` | Fog Node |
| `FunctionalRequirement` | Functional Requirement |
| `Geometry` | Geometry |
| `HeartRateSensor` | Heart Rate Sensor |
| `Identifier` | Identifier |
| `MAPESymptom` | MAPE-K Symptom |
| `MechanismSpecification` | Mechanism Specification |
| `MigrationCostLevel` | Migration Cost Level |
| `MigrationEvent` | Migration Event |
| `MigrationTimeLevel` | Migration Time Level |
| `MistNode` | Mist Node |
| `MobileDevice` | Mobile Device |
| `MobilityLevel` | Mobility Level |
| `ModelDegradationCause` | Model Degradation Cause |
| `ModelGradientUpdate` | Model Gradient Update |
| `ModelSelectionAction` | Model Selection Action |
| `ModelTier` | Model Tier |
| `NodeShape` | NodeShape |
| `NodeState` | Node State |
| `NodeUserRelation` | Node-User Relation |
| `NonFunctionalRequirement` | Non-functional Requirement |
| `NonUser` | Non-User |
| `Observation` | Observation |
| `OffloadingEvent` | Offloading Event |
| `OntologyArtifact` | Ontology Artifact |
| `OperationalStatus` | Operational Status |
| `PairwiseComparison` | Pairwise Comparison |
| `ParametrizedData` | Parametrized Data |
| `PayloadType` | Payload Type |
| `PerformanceLevel` | Performance Level |
| `Permission` | Permission |
| `Person` | Person |
| `PersonStatus` | Person Status |
| `PhysiologicalObservation` | Physiological Observation |
| `PhysiologicalParametrizedData` | Physiological Parametrized Data |
| `PhysiologicalSensor` | Physiological Sensor |
| `Platform` | Platform |
| `Policy` | Policy |
| `PolicyArtifact` | Policy Artifact |
| `PolicyCategory` | Policy Category |
| `PolicyCategoryRelation` | Policy Category Relation |
| `PolicyRelationType` | Policy Relation Type |
| `PolicyType` | Policy Type |
| `PopulationDensity` | Population Density |
| `PrivacyBudgetAccount` | Privacy Budget Account |
| `PrivacyMechanism` | Privacy Mechanism |
| `ProcessingLevel` | Processing Level |
| `ProcessingPurpose` | Processing Purpose |
| `ProcessingScope` | Processing Scope |
| `ProfitabilityLevel` | Profitability Level |
| `PseudonymousIdentifier` | Pseudonymous Identifier |
| `QueryCatalog` | Query Catalog |
| `QuerySpecification` | Query Specification |
| `QueryType` | Query Type |
| `RecoveryCondition` | Recovery Condition |
| `ReplicationEvent` | Replication Event |
| `Requirement` | Requirement |
| `RequirementsArtifact` | Requirements Artifact |
| `ResidualCapacity` | Residual Capacity |
| `RestrictedZone` | Restricted Zone |
| `RetentionEvent` | Retention Event |
| `Role` | Access Role |
| `RollbackEvent` | Rollback Event |
| `RuralZone` | Rural Zone |
| `ScalingEvent` | Scaling Event |
| `Scenario` | Scenario |
| `ScenarioArtifact` | Scenario Artifact |
| `SecurityMechanism` | Security Mechanism |
| `SemanticContract` | Semantic Contract |
| `Sensor` | Sensor |
| `Service` | Service |
| `ServiceState` | Service State |
| `SleepObservation` | Sleep Observation |
| `SleepParametrizedData` | Sleep Parametrized Data |
| `SleepSensor` | Sleep Sensor |
| `SmartBand` | Smart Band |
| `SmartRing` | Smart Ring |
| `SmartWatch` | Smart Watch |
| `SpO2Sensor` | SpO2 Sensor |
| `StandardSpecification` | Standard Specification |
| `State` | State |
| `StressLevel` | Stress Level |
| `StressObservation` | Stress Observation |
| `SynchronizationEvent` | Synchronization Event |
| `TemperatureSensor` | Skin Temperature Sensor |
| `TemporalEntity` | Temporal Entity |
| `TrafficWindow` | Traffic Window |
| `TransferEvent` | Transfer Event |
| `TrustAssessment` | Trust Assessment |
| `TrustEvidence` | Trust Evidence |
| `UrbanEnvironment` | Urban Environment |
| `UrbanZone` | Urban Zone |
| `User` | User |
| `UserState` | User State |
| `ValidationCampaign` | Validation Campaign |
| `ValidationRequirement` | Validation / Reproducibility Requirement |
| `ValidationResult` | Validation Result |
| `Wearable` | Wearable |
| `WorkloadLevel` | Workload Level |
| `ZoneType` | Zone type |

## Complete object-property catalog

| Term | English label |
|---|---|
| `actionOriginNode` | action origin node |
| `actionTargetNode` | action target node |
| `affectsModel` | affects model |
| `affectsService` | affects service |
| `aggregatesData` | aggregates data |
| `alternativeModelTier` | alternative model tier |
| `appliedMechanism` | applied mechanism |
| `appliedPolicy` | applied policy |
| `appliedSecurityMechanism` | applied security mechanism |
| `appliesInZone` | applies in zone |
| `appliesPolicy` | applies policy |
| `appliesTo` | applies to |
| `appliesToZoneType` | applies to zone type |
| `auditsContract` | audits contract |
| `authorizedByEvaluation` | authorized by evaluation |
| `basedOnConsentRecord` | based on consent record |
| `basedOnContract` | based on contract |
| `basedOnZone` | based on zone |
| `belongsToCommunity` | belongs to community |
| `belongsToPolicyCategory` | belongs to policy category |
| `belongsToQueryCatalog` | belongs to query catalog |
| `budgetForContract` | budget for contract |
| `budgetForPurpose` | budget for purpose |
| `carriesData` | carries data |
| `connectsTo` | connects to |
| `consentSubject` | consent subject |
| `contextDeviceState` | context device state |
| `contextNodeState` | context node state |
| `contextProcessingLevel` | context processing level |
| `contextPurpose` | context purpose |
| `contextZone` | context zone |
| `contractSubject` | contract subject |
| `coversArea` | covers area |
| `criterionA` | criterion A |
| `criterionB` | criterion B |
| `definedInArtifact` | defined in artifact |
| `delegatedBy` | delegated by |
| `delegatesTo` | delegates requests to |
| `derivedFrom` | derived from |
| `evaluatesNode` | evaluates node |
| `evaluatesService` | evaluates service |
| `evaluationPurpose` | evaluation purpose |
| `evaluationUser` | evaluation user |
| `evaluationZone` | evaluation zone |
| `expiresOnRecoveryOf` | expires on recovery of |
| `generatedBy` | generated by |
| `governedBy` | governed by |
| `hasActiveConsentRange` | has active consent range |
| `hasAdaptability` | has adaptability |
| `hasAuthorizationDecision` | has authorization decision |
| `hasAuthorizationOutcome` | has authorization outcome |
| `hasAuthorizedDataCategory` | authorizes data category |
| `hasAvailability` | has availability |
| `hasBatteryLevel` | has battery level |
| `hasCommunication` | has communication level |
| `hasComplianceMetric` | has compliance metric |
| `hasConnectionStatus` | has connection status |
| `hasConsentRange` | has consent range |
| `hasConsentRecord` | has consent record |
| `hasDataCategory` | has data category |
| `hasDataContext` | has data context |
| `hasDataCriticality` | has data criticality |
| `hasDataSensitivity` | has data sensitivity |
| `hasDecisionAlternative` | has decision alternative |
| `hasDecisionMethod` | has decision method |
| `hasDegradationCause` | has degradation cause |
| `hasDelegation` | has delegation |
| `hasDetectedSymptom` | has detected symptom |
| `hasDeviceState` | has device state |
| `hasDistance` | has distance |
| `hasEffectiveConsentRange` | has effective consent range |
| `hasEnergyLevel` | has energy level |
| `hasFeatureOfInterest` | hasFeatureOfInterest |
| `hasGeometry` | has geometry |
| `hasGeometry` | hasGeometry |
| `hasIdentifier` | has identifier |
| `hasMigrationCost` | has migration cost |
| `hasMigrationTime` | has migration time |
| `hasMobileDevice` | has mobile device |
| `hasMobility` | has mobility |
| `hasModelTier` | has model tier |
| `hasNeighborNode` | has neighbor node |
| `hasNodeState` | has node state |
| `hasOperationalStatus` | has operational status |
| `hasPairwiseComparison` | has pairwise comparison |
| `hasPayloadType` | has payload type |
| `hasPerformance` | has performance |
| `hasPermission` | has permission |
| `hasPersonStatus` | has person status |
| `hasPolicyRelationType` | has policy relation type |
| `hasPolicyType` | has policy type |
| `hasPopulationDensity` | has population density |
| `hasPredictedStressLevel` | has predicted stress level |
| `hasPrivacyBudgetAccount` | has privacy budget account |
| `hasPrivacyMechanism` | has privacy mechanism |
| `hasProcessingLevel` | has processing level |
| `hasProcessingPurpose` | has processing purpose |
| `hasProcessingScope` | has processing scope |
| `hasProfitability` | has profitability |
| `hasQueryType` | has query type |
| `hasRecoveryCondition` | has recovery condition |
| `hasReplicationEvent` | has replication event |
| `hasResidualCapacity` | has residual capacity |
| `hasRole` | has role |
| `hasSemanticContract` | has semantic contract |
| `hasServiceState` | has service state |
| `hasTrustAssessment` | has trust assessment |
| `hasTrustEvidence` | has trust evidence |
| `hasUserState` | has user state |
| `hasValidationResult` | has validation result |
| `hasWearable` | has wearable |
| `hasWorkload` | has workload |
| `hostedOnNode` | hosted on node |
| `hostsModel` | hosts model |
| `hostsService` | hosts service |
| `involvedNode` | involved node |
| `isHostedBy` | isHostedBy |
| `locatedIn` | located in |
| `locatedInZone` | located in zone |
| `madeBySensor` | madeBySensor |
| `observedProperty` | observedProperty |
| `originatesFromDevice` | originates from device |
| `parentDelegation` | parent delegation |
| `partOfScenario` | part of scenario |
| `policyArtifactUsed` | policy artifact used |
| `recommendedMechanism` | recommended mechanism |
| `relatedRequirement` | related requirement |
| `relatesNode` | relates node |
| `relatesUser` | relates user |
| `relationSourceCategory` | relation source category |
| `relationTargetCategory` | relation target category |
| `replicaOf` | replica of |
| `replicationSource` | replication source |
| `replicationTarget` | replication target |
| `requirementsArtifactUsed` | requirements artifact used |
| `requiresConsentRange` | requires consent range |
| `resultedInAction` | resulted in action |
| `rollbackTarget` | rollback target |
| `scenarioMechanism` | scenario mechanism |
| `scenarioPolicy` | scenario policy |
| `selectedAlternative` | selected alternative |
| `selectedModelTier` | selected model tier |
| `sentToNode` | sent to node |
| `supersedesModel` | supersedes model |
| `supportsPolicy` | supports policy |
| `tracedToMechanism` | traced to mechanism |
| `tracedToPolicy` | traced to policy |
| `transferDestination` | transfer destination |
| `transfersData` | transfers data |
| `transferSource` | transfer source |
| `triggeredByState` | triggered by state |
| `trustAssessmentForState` | trust assessment for state |
| `updatesModel` | updates model |
| `usesAcceptanceProfile` | uses acceptance profile |
| `usesIdentifier` | uses identifier |
| `usesModel` | uses model |
| `usesResolutionStrategy` | uses resolution strategy |
| `usesStandard` | uses standard |
| `validationUsesOntology` | validation uses ontology |
| `validationUsesPolicies` | validation uses policies |
| `validationUsesQueries` | validation uses queries |
| `validationUsesScenarios` | validation uses scenarios |

## Complete datatype-property catalog

| Term | English label |
|---|---|
| `AHP_consistency_threshold` | AHP consistency threshold |
| `artifactIdentifier` | artifact identifier |
| `artifactStatus` | artifact status |
| `artifactVersion` | artifact version |
| `authorizationReason` | authorization reason |
| `categoryCode` | category code |
| `conditionExpression` | condition expression |
| `configurationStatus` | configuration status |
| `containsIndividualizedGradients` | contains individualized gradients |
| `containsPersistentIdentifier` | contains persistent identifier |
| `containsPersonalData` | contains personal data |
| `continuumLevel` | continuum level |
| `D_delegation_max` | maximum delegation depth |
| `delegationDepth` | delegation depth |
| `E_device_max` | device energy threshold |
| `eligibilityReason` | eligibility reason |
| `estimatedPredictionError` | estimated prediction error |
| `evaluationOrder` | evaluation order |
| `evidenceContribution` | evidence contribution |
| `evidenceFactor` | evidence factor |
| `hasAHPScore` | has AHP / multicriteria score |
| `hasAnonymizationApplied` | has anonymization applied |
| `hasConsistencyRatio` | has consistency ratio |
| `hasConsistencyThreshold` | has consistency threshold |
| `hasElasticity` | has elasticity |
| `hasEvaluationTicketID` | has evaluation ticket ID |
| `hasLatencyWeight` | has latency weight |
| `hasModelQualityWeight` | has model quality weight |
| `hasNoiseApplied` | has noise applied |
| `hasPolicyAction` | has policy action |
| `hasPolicyStatement` | has policy statement |
| `hasPrivacyBudget` | has privacy budget |
| `hasPrivacyWeight` | has privacy weight |
| `hasSelectionJustification` | has selection justification |
| `hasSimpleResult` | hasSimpleResult |
| `hasTrustScore` | has trust score |
| `hasTrustWeight` | has external trust weight |
| `idempotencyKey` | idempotency key |
| `identifierScope` | identifier scope |
| `identifierValue` | identifier value |
| `isEligible` | is eligible |
| `isPreferredNode` | is preferred node |
| `isRedundant` | is redundant |
| `lastUpdated` | last updated |
| `legacyDecisionScore` | legacy decision score |
| `mechanismDescription` | mechanism description |
| `mechanismIdentifier` | mechanism identifier |
| `migrationNote` | migration note |
| `migrationStatus` | migration status |
| `modelLineageStatus` | model lineage status |
| `modelVersion` | model version |
| `N_agents` | concurrent agent target |
| `name` | name |
| `noiseLevel` | noise level |
| `observedModelQuality` | observed model quality |
| `pairwiseValue` | pairwise comparison value |
| `parametrizedDataReady` | parametrized data ready |
| `plannedExpiry` | planned expiry |
| `policyIdentifier` | policy identifier |
| `policyVersion` | policy version |
| `predictionConfidence` | prediction confidence |
| `privacyBudgetConsumed` | privacy budget consumed |
| `privacyBudgetMaximum` | privacy budget maximum |
| `privacyBudgetRemaining` | privacy budget remaining |
| `protectsAtRest` | protects at rest |
| `protectsInTransit` | protects in transit |
| `queryIdentifier` | query identifier |
| `queryInterpretation` | query interpretation |
| `queryPurpose` | query purpose |
| `queuedRequests` | queued requests |
| `relationCode` | relation code |
| `replicationVersion` | replication version |
| `requirementIdentifier` | requirement identifier |
| `requirementStatement` | requirement statement |
| `requiresRecalculation` | requires recalculation |
| `resourceUsagePercent` | resource usage (%) |
| `resultTime` | resultTime |
| `scenarioIdentifier` | scenario identifier |
| `securityBaselineVersion` | security baseline version |
| `sendTimestamp` | send timestamp |
| `sessionTime` | session time |
| `stateDuration` | state duration |
| `strategyCode` | strategy code |
| `T_decision_max` | decision threshold |
| `T_inference_local` | local inference latency threshold (ms) |
| `T_migration_max` | migration interruption threshold |
| `T_node_join` | node join threshold |
| `T_reselection_max` | reselection threshold |
| `T_sparql_monitor` | SPARQL monitoring threshold |
| `trustRuleVersion` | trust rule version |
| `trustWindowEnd` | trust window end |
| `trustWindowStart` | trust window start |
| `userFeedbackScore` | user feedback score |
| `validFrom` | valid from |
| `validTo` | valid to |

## Complete annotation-property catalog

| Term | English label |
|---|---|
| `class` | class |
| `datatype` | datatype |
| `identifier` | identifier |
| `language` | language |
| `maxCount` | maxCount |
| `message` | message |
| `minCount` | minCount |
| `modified` | modified |
| `or` | or |
| `path` | path |
| `property` | property |
| `replaces` | replaces |
| `severity` | severity |
| `targetClass` | targetClass |
