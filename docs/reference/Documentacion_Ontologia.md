# Documentación de la Ontología SmartCity Continuum — v3.0.0

**Ontología:** `smartcity_continuum_v3.0.0.ttl`  
**Versión OWL:** `3.0.0`  
**Namespace principal:** `http://example.org/smartcity#`  
**Formato:** OWL / RDF / Turtle  
**Fecha de alineación documental:** 2026-08-26  
**Requisitos:** `RF-01–RF-72`, `RNF-01–RNF-39`, `RV-01–RV-05`  
**Políticas:** `POLICIES-REV-01` — 79 políticas y 55 mecanismos  
**Batería SPARQL externa:** `sparql_battery_v3.0.0.sparql` — `BASE-Q01–BASE-Q35` y `EXT-Q01–EXT-Q80` (115 consultas)

> Esta documentación sustituye la documentación v2.1. Describe el modelo realmente serializado en la TTL v3.0.0 y lo contextualiza con los artefactos de requisitos, políticas/mecanismos y consultas SPARQL actualmente vigentes.

---

## Índice

1. [Visión general](#1-visión-general)
2. [Cambios principales respecto a v2.1](#2-cambios-principales-respecto-a-v21)
3. [Principios de diseño](#3-principios-de-diseño)
4. [Namespaces y estándares](#4-namespaces-y-estándares)
5. [Arquitectura del continuum y ámbitos de procesamiento](#5-arquitectura-del-continuum-y-ámbitos-de-procesamiento)
6. [Mapa modular de la ontología](#6-mapa-modular-de-la-ontología)
7. [Catálogo completo de clases](#7-catálogo-completo-de-clases)
8. [Catálogo completo de propiedades de objeto](#8-catálogo-completo-de-propiedades-de-objeto)
9. [Catálogo completo de propiedades de datos](#9-catálogo-completo-de-propiedades-de-datos)
10. [Vocabularios controlados e individuos clave](#10-vocabularios-controlados-e-individuos-clave)
11. [Modelo de requisitos y trazabilidad](#11-modelo-de-requisitos-y-trazabilidad)
12. [Modelo de políticas, mecanismos y conflictos](#12-modelo-de-políticas-mecanismos-y-conflictos)
13. [Consentimiento, contratos y autorización efectiva](#13-consentimiento-contratos-y-autorización-efectiva)
14. [Datos, identidad, seguridad y transmisión](#14-datos-identidad-seguridad-y-transmisión)
15. [Confianza dinámica y selección de nodos](#15-confianza-dinámica-y-selección-de-nodos)
16. [Decisión multicriterio y AHP](#16-decisión-multicriterio-y-ahp)
17. [Adaptación, migración, delegación y continuidad](#17-adaptación-migración-delegación-y-continuidad)
18. [Aprendizaje federado, privacidad diferencial y ciclo de vida de modelos](#18-aprendizaje-federado-privacidad-diferencial-y-ciclo-de-vida-de-modelos)
19. [Modelo temporal](#19-modelo-temporal)
20. [Auditoría semántica y MAPE-K](#20-auditoría-semántica-y-mape-k)
21. [Escenarios S1–S17](#21-escenarios-s1s17)
22. [Validación SPARQL y catálogo de consultas](#22-validación-sparql-y-catálogo-de-consultas)
23. [Validación SHACL](#23-validación-shacl)
24. [Artefactos, versionado y reproducibilidad](#24-artefactos-versionado-y-reproducibilidad)
25. [Estadísticas de la ontología](#25-estadísticas-de-la-ontología)
26. [Estado de validación](#26-estado-de-validación)
27. [Datos pendientes y limitaciones conocidas](#27-datos-pendientes-y-limitaciones-conocidas)
28. [Referencias cruzadas de artefactos](#28-referencias-cruzadas-de-artefactos)

---

## 1. Visión general

La ontología v3.0.0 modela un **continuum computacional inteligente, gobernado por políticas, consentimiento, contexto y confianza**, orientado a predicción de estrés/sueño, adaptación MAPE-K y aprendizaje federado jerárquico. La v3 convierte decisiones que antes eran parcialmente implícitas en entidades semánticas auditables y versionables.

El modelo integra:

- wearables, dispositivos móviles y nodos Mist/Edge/Fog/Cloud;
- sensores y observaciones fisiológicas mediante SOSA/SSN y dispositivos mediante SAREF;
- estados temporales de usuario, dispositivo, nodo y servicio;
- consentimiento independiente del contrato y una `AuthorizationDecision` efectiva;
- políticas tipadas, categorías de políticas, mecanismos y relaciones de conflicto/anomalía;
- confianza histórica reproducible mediante `TrustAssessment`;
- selección de modelos mediante alternativas explícitas, AHP o puntuación multicriterio ponderada;
- acciones adaptativas explícitas: migración, offloading, degradación, retención, sincronización, rollback, selección y escalado;
- aprendizaje federado con tipos de payload, privacidad diferencial y contabilidad epsilon;
- identidad pseudónima/anónima, cifrado, eventos de transferencia y contexto de datos;
- auditoría causal mediante `EvaluationState`;
- requisitos, políticas, mecanismos, escenarios y artefactos versionados;
- 15 shapes SHACL y una batería externa de 115 consultas SPARQL de validación.

## 2. Cambios principales respecto a v2.1

| Área | v2.1 | v3.0.0 |
|---|---|---|
| Consentimiento | Modelo binario heredado + rangos | Se elimina `ConsentStatus/ConsentGiven/ConsentDenied`; se introducen `ConsentRecord`, `RangeDenied` y autorización efectiva. |
| Contrato | Contrato y consentimiento parcialmente acoplados | Consentimiento y contrato son fuentes independientes; la autorización se calcula como intersección restrictiva. |
| Ámbito local | Edge podía interpretarse como local en zonas internas | Local = wearable/móvil/Mist autorizado; Edge/Fog/Cloud son externos para datos fisiológicos crudos. |
| Políticas | 7 políticas individuales | 79 políticas, 12 categorías, 55 mecanismos y taxonomía formal de relaciones/conflictos. |
| Trust | Score/peso mezclado con decisión | `TrustAssessment` versionado; trust es filtro/criterio externo y no un cuarto peso AHP. |
| AHP | Un score global y cuatro pesos | Tres pesos AHP (latencia/privacidad/calidad), alternativas por tier, comparaciones por pares y ratio de consistencia. |
| Adaptación | Migración/delegación/FL parcialmente acoplados | Jerarquía `AdaptationAction`; migración, delegación y FL se separan explícitamente. |
| FL | `dataType` textual y DP parcialmente en sesión | `PayloadType`, DP en gradientes, cuentas epsilon y diferenciación uplink/downlink. |
| Identidad/seguridad | `anonymizedID` literal | Jerarquía de identificadores, `TransferEvent`, pseudonimización y línea base de cifrado. |
| Temporalidad | `validFrom/validTo` ligados principalmente a `State` | `TemporalEntity` general; `plannedExpiry` separado de `validTo`. |
| Auditoría | Ticket con campos parciales | `EvaluationState` enlaza usuario, propósito, zona, políticas, alternativas, trust, tier y acción. |
| Reproducibilidad | 8 escenarios y validación limitada | S1–S17, `AcceptanceProfile`, artefactos versionados y campaña de validación. |
| SHACL | Validación mínima de FL | 15 `NodeShape` estructurales para los módulos críticos. |
| SPARQL | 69 consultas v2.1 | 115 consultas externas v3 (`35 BASE + 80 EXT`). |

## 3. Principios de diseño

### 3.1 Reutilización de estándares

SOSA/SSN, SAREF, FOAF y GeoSPARQL se reutilizan donde corresponde; RDF/OWL/Turtle y SPARQL 1.1 constituyen la base interoperable.

### 3.2 Estados y eventos como entidades temporales

Los cambios de contexto se reifican para permitir validez temporal, trazabilidad y auditoría.

### 3.3 Restricciones antes de optimización

Consentimiento, contrato, zona, seguridad y elegibilidad filtran alternativas antes de AHP, trust o QoS.

### 3.4 Separación de fuentes normativas

Consentimiento del usuario, contrato y política de zona no se colapsan en un único atributo.

### 3.5 Explicabilidad por construcción

Una decisión debe poder reconstruirse desde el contexto hasta la acción final.

### 3.6 No invención de evidencia

Valores históricos no disponibles (scores por alternativa, ventanas de trust o umbrales) se marcan como pendientes en lugar de fabricarse.

### 3.7 Versionado de artefactos

Ontología, requisitos, políticas, escenarios, consultas y perfil de aceptación deben quedar identificados inequívocamente.

### 3.8 Validación multicapa

OWL/RDF proporciona el modelo, SHACL valida estructura y SPARQL aporta inspección, auditoría, incumplimiento y métricas.

## 4. Namespaces y estándares

| Prefijo | URI | Uso |
|---|---|---|
| `ex:` | `http://example.org/smartcity#` | Namespace principal del proyecto. |
| `dcterms:` | `http://purl.org/dc/terms/` | Metadatos de artefactos/ontología. |
| `foaf:` | `http://xmlns.com/foaf/0.1/` | Personas. |
| `saref:` | `https://saref.etsi.org/core/` | Dispositivos IoT. |
| `sosa:` | `http://www.w3.org/ns/sosa/` | Sensores y observaciones. |
| `geo:` | `http://www.opengis.net/ont/geosparql#` | Geometría y zonas. |
| `sh:` | `http://www.w3.org/ns/shacl#` | Shapes y validación SHACL. |
| `owl:` | `http://www.w3.org/2002/07/owl#` | Constructos OWL. |
| `rdf:` | `http://www.w3.org/1999/02/22-rdf-syntax-ns#` | Núcleo RDF. |
| `rdfs:` | `http://www.w3.org/2000/01/rdf-schema#` | Esquema y anotaciones. |
| `xsd:` | `http://www.w3.org/2001/XMLSchema#` | Tipos de datos. |

### 4.1 Especificaciones representadas como individuos

- `ex:Standard_ApacheJenaFuseki` — Apache Jena Fuseki reference endpoint.
- `ex:Standard_FOAF` — FOAF.
- `ex:Standard_GeoSPARQL` — GeoSPARQL.
- `ex:Standard_OWL` — OWL.
- `ex:Standard_RDF` — RDF.
- `ex:Standard_SAREF` — SAREF.
- `ex:Standard_SOSA_SSN` — SOSA/SSN.
- `ex:Standard_SPARQL11` — SPARQL 1.1.
- `ex:Standard_Turtle` — Turtle.

## 5. Arquitectura del continuum y ámbitos de procesamiento

```text
Ámbito local/autorizado
  Wearable / MobileDevice / MistNode personal
  ├─ observaciones fisiológicas crudas
  ├─ preprocesamiento
  └─ LocalModelTier

Ámbito externo
  EdgeNode  → EdgeModelTier
  FogNode   → FogModelTier
  CloudNode → CloudModelTier
```

La arquitectura no interpreta los tiers como una escala de calidad obligatoriamente ascendente. `ModelTier` indica ubicación/capacidad de ejecución; la selección efectiva depende de autorización, zona, estado del nodo, trust y criterio multicriterio.

### 5.1 Regla de confinamiento

Las `PhysiologicalObservation` crudas no pueden transmitirse a Edge, Fog ni Cloud. Para procesamiento externo solo pueden utilizarse `ParametrizedData` o actualizaciones de modelo expresamente autorizadas y protegidas. En `RestrictedZone`, la política vigente puede reducir incluso un contrato comunitario a `RangeLocalOnly`.

## 6. Mapa modular de la ontología

| Módulo | Elementos principales |
|---|---|
| Infraestructura e IoT | `ComputationalNode`, `MistNode`, `EdgeNode`, `FogNode`, `CloudNode`, `Wearable`, `MobileDevice`, sensores y observaciones. |
| Temporalidad y contexto | `TemporalEntity`, `State`, `NodeState`, `DeviceState`, `UserState`, `ServiceState`, `NodeUserRelation`, `DataContext`. |
| Consentimiento y autorización | `ConsentRecord`, `SemanticContract`, `AuthorizationDecision`, `ConsentRange`, `ProcessingPurpose`, `DataCategory`. |
| Datos, identidad y seguridad | `ParametrizedData`, `TransferEvent`, `BufferRecord`, `ReplicationEvent`, `Identifier`, `SecurityMechanism`. |
| Políticas y mecanismos | `Policy`, `PolicyCategory`, `PolicyType`, `MechanismSpecification`, `PolicyCategoryRelation`, `PolicyRelationType`. |
| Trust y decisión | `TrustAssessment`, `TrustEvidence`, `DecisionMethod`, `DecisionAlternative`, `PairwiseComparison`, `EvaluationState`. |
| Adaptación | `AdaptationAction` y subclases de migración, offloading, degradación, retención, sincronización, rollback, selección y escalado. |
| Aprendizaje federado | `FederatedLearningSession`, `PayloadType`, `ModelGradientUpdate`, `PrivacyMechanism`, `PrivacyBudgetAccount`. |
| Requisitos y reproducibilidad | `Requirement`, `Artifact`, `Scenario`, `AcceptanceProfile`, `ValidationCampaign`, `QueryCatalog`, `StandardSpecification`. |
| Validación | 15 `sh:NodeShape` y batería SPARQL externa v3. |

## 7. Catálogo completo de clases

La serialización contiene **151 recursos tipados como `owl:Class`**. De ellos, **133 son clases nombradas del namespace `ex:`**; el resto corresponde a clases externas reutilizadas y expresiones anónimas empleadas en uniones de dominio/rango.

### 7.1 Clases nombradas `ex:`

| Clase | Superclase(s) | Etiqueta / función |
|---|---|---|
| `ex:AccelerometerSensor` | `ex:PhysiologicalSensor` | Determines user mobility and physical activity. |
| `ex:AcceptanceProfile` | `ex:Artifact` | Acceptance Profile |
| `ex:AdaptabilityLevel` | — | Adaptability Level |
| `ex:AdaptationAction` | `ex:TemporalEntity` | Auditable action produced by an EvaluationState. |
| `ex:AIModel` | — | Stress prediction model. Exists at different quality levels per continuum layer. |
| `ex:AnonymousIdentifier` | `ex:Identifier` | Anonymous Identifier |
| `ex:Artifact` | — | Versionable project artifact. |
| `ex:AuthorizationDecision` | `ex:TemporalEntity` | Effective authorization obtained from the intersection of consent record, contract, zone and hard restrictions. |
| `ex:AuthorizationOutcome` | — | Authorization Outcome |
| `ex:AvailabilityLevel` | — | Availability Level |
| `ex:BatteryLevel` | — | Battery Level |
| `ex:BufferRecord` | `ex:TemporalEntity` | Temporary retained data record governed by authorization and storage policies. |
| `ex:CityArea` | `ex:UrbanEnvironment` | City Area |
| `ex:CloudNode` | `ex:ComputationalNode` | Cloud continuum node for global processing. Selection is conditional on authorization and policies; it is not intrinsically preferred. |
| `ex:CommunicationLevel` | — | Communication Level |
| `ex:Community` | — | Group of users with similar mobility patterns and routines (neighbourhood, floor, hospital ward). |
| `ex:ComplianceMetric` | — | Compliance Metric |
| `ex:ComputationalNode` | `saref:Device` | Continuum architecture node capable of hosting models and processing data. |
| `ex:ConflictResolutionStrategy` | — | Conflict Resolution Strategy |
| `ex:ConsentRange` | — | Maximum processing scope declared by consent/contract. Includes LocalOnly, CommunityAgg, GlobalAgg and Denied/Revoked. Effective authorization is computed independently. |
| `ex:ConsentRecord` | `ex:TemporalEntity` | User-declared consent decision independent from the semantic contract. |
| `ex:DataCategory` | — | Semantic category of information governed by consent, privacy and transmission policies. |
| `ex:DataContext` | `ex:TemporalEntity` | Operational context associated with data or a processing/transfer event. |
| `ex:DataCriticality` | — | Data Criticality |
| `ex:DataSensitivity` | — | Data Sensitivity |
| `ex:DecisionAlternative` | — | Decision Alternative |
| `ex:DecisionMethod` | — | Decision Method |
| `ex:DegradationEvent` | `ex:AdaptationAction` | Degradation Event |
| `ex:DelegationEvent` | `ex:AdaptationAction`, `ex:TemporalEntity` | Reified temporal delegation that records delegator node, delegate node, cause, validity interval and recovery condition. |
| `ex:DeviceConnectionStatus` | — | Device Connection Status |
| `ex:DeviceState` | `ex:State` | Device State |
| `ex:DifferentialPrivacyMechanism` | `ex:PrivacyMechanism` | Differential Privacy Mechanism |
| `ex:DirectIdentifier` | `ex:Identifier` | Direct Identifier |
| `ex:DistanceLevel` | — | Distance Level |
| `ex:EDASensor` | `ex:PhysiologicalSensor` | Electrodermal activity sensor. |
| `ex:EdgeNode` | `ex:ComputationalNode` | Edge continuum node. It is external to the local scope defined for raw physiological observations. Elasticity is a node capability, not a class invariant. |
| `ex:EncryptionMechanism` | `ex:SecurityMechanism` | Encryption Mechanism |
| `ex:EnergyLevel` | — | Energy Level |
| `ex:EvaluationState` | `ex:State` | Derived by reasoning over NodeState + UserState + NodeUserRelation. |
| `ex:FederatedLearningSession` | — | Event of parameter/model transfer between continuum layers (HFL). |
| `ex:FogNode` | `ex:ComputationalNode` | Fog continuum node for community/zone processing. Elasticity depends on deployment capability and is not fixed by the class. |
| `ex:FunctionalRequirement` | `ex:Requirement` | Functional Requirement |
| `ex:HeartRateSensor` | `ex:PhysiologicalSensor` | Heart Rate Sensor |
| `ex:Identifier` | — | Identifier that may be direct, pseudonymous or anonymous. |
| `ex:MAPESymptom` | — | Symptom detected in the MAPE-K Monitor/Analyse phases and recorded for auditability. |
| `ex:MechanismSpecification` | — | Mechanism Specification |
| `ex:MigrationCostLevel` | — | Migration Cost Level |
| `ex:MigrationEvent` | `ex:AdaptationAction` | Migration Event |
| `ex:MigrationTimeLevel` | — | Migration Time Level |
| `ex:MistNode` | `ex:ComputationalNode` | Closest node to the user. Minimal capacity, very low latency. |
| `ex:MobileDevice` | `ex:MistNode` | User smartphone acting as a personal Mist node. It belongs to the local processing scope when associated with the user. |
| `ex:MobilityLevel` | — | Mobility Level |
| `ex:ModelDegradationCause` | — | Model Degradation Cause |
| `ex:ModelGradientUpdate` | `ex:ParametrizedData` | Federated learning update that may leave a mobile device only after anonymization and noise addition. |
| `ex:ModelSelectionAction` | `ex:AdaptationAction` | Model Selection Action |
| `ex:ModelTier` | — | Model Tier |
| `ex:NodeState` | `ex:State` | Node State |
| `ex:NodeUserRelation` | `ex:TemporalEntity` | Captures distance and connectivity between a node and a user at a given instant. |
| `ex:NonFunctionalRequirement` | `ex:Requirement` | Non-functional Requirement |
| `ex:NonUser` | `foaf:Person` | Person in the environment without a wearable or active participation. |
| `ex:OffloadingEvent` | `ex:AdaptationAction` | Offloading Event |
| `ex:OntologyArtifact` | `ex:Artifact` | Ontology Artifact |
| `ex:OperationalStatus` | — | Operational Status |
| `ex:PairwiseComparison` | — | Pairwise Comparison |
| `ex:ParametrizedData` | — | Pre-computed and aggregated data. Raw physiological data never leaves the device. |
| `ex:PayloadType` | — | Payload Type |
| `ex:PerformanceLevel` | — | Performance Level |
| `ex:Permission` | — | Permission |
| `ex:PersonStatus` | — | Person Status |
| `ex:PhysiologicalObservation` | `sosa:Observation` | Physiological Observation |
| `ex:PhysiologicalParametrizedData` | `ex:ParametrizedData` | EDA, HR, SpO2, etc. Sent during the day or at night when conditions allow. |
| `ex:PhysiologicalSensor` | `sosa:Sensor` | Physiological Sensor |
| `ex:Policy` | — | Normative governance rule from POLICIES-REV-01. Policies are specifications, not execution mechanisms. |
| `ex:PolicyArtifact` | `ex:Artifact` | Policy Artifact |
| `ex:PolicyCategory` | — | Policy Category |
| `ex:PolicyCategoryRelation` | — | Policy Category Relation |
| `ex:PolicyRelationType` | — | Policy Relation Type |
| `ex:PolicyType` | — | Policy Type |
| `ex:PopulationDensity` | — | Population Density |
| `ex:PrivacyBudgetAccount` | — | Privacy Budget Account |
| `ex:PrivacyMechanism` | — | Privacy Mechanism |
| `ex:ProcessingLevel` | — | Processing Level |
| `ex:ProcessingPurpose` | — | Purpose for which data, model parameters or predictions are processed. |
| `ex:ProcessingScope` | — | Processing Scope |
| `ex:ProfitabilityLevel` | — | Profitability Level |
| `ex:PseudonymousIdentifier` | `ex:Identifier` | Pseudonymous Identifier |
| `ex:QueryCatalog` | `ex:Artifact` | Query Catalog |
| `ex:QuerySpecification` | — | Query Specification |
| `ex:QueryType` | — | Query Type |
| `ex:RecoveryCondition` | — | Recovery Condition |
| `ex:ReplicationEvent` | `ex:TemporalEntity` | Controlled and idempotent replication or synchronization event. |
| `ex:Requirement` | — | Requirement |
| `ex:RequirementsArtifact` | `ex:Artifact` | Requirements Artifact |
| `ex:ResidualCapacity` | — | Residual Capacity |
| `ex:RestrictedZone` | `ex:CityArea` | Geographic zone with hard restrictions on external processing/transfer. Raw physiological observations remain on wearable/mobile or authorised personal Mist; Edge, Fog and Cloud are external to local scope. |
| `ex:RetentionEvent` | `ex:AdaptationAction` | Retention Event |
| `ex:Role` | — | Access Role |
| `ex:RollbackEvent` | `ex:AdaptationAction` | Rollback Event |
| `ex:RuralZone` | `ex:CityArea` | Few nodes. Predominance of local retention and controlled transmission. |
| `ex:ScalingEvent` | `ex:AdaptationAction` | Scaling Event |
| `ex:Scenario` | — | Scenario |
| `ex:ScenarioArtifact` | `ex:Artifact` | Scenario Artifact |
| `ex:SecurityMechanism` | — | Security Mechanism |
| `ex:SemanticContract` | `ex:TemporalEntity` | Temporal agreement binding user, processing purpose(s), consent range and governing policies. It is independent from the user-declared ConsentRecord. |
| `ex:Service` | — | Stress prediction or any other continuum service. |
| `ex:ServiceState` | `ex:State` | Service State |
| `ex:SleepObservation` | `sosa:Observation` | Sleep Observation |
| `ex:SleepParametrizedData` | `ex:ParametrizedData` | Sleep quality and phase durations. Generated when the user wakes up. |
| `ex:SleepSensor` | `ex:PhysiologicalSensor` | Captures total duration, phases (REM, deep, light) and sleep quality. |
| `ex:SmartBand` | `ex:Wearable` | Smart Band |
| `ex:SmartRing` | `ex:Wearable` | Smart Ring |
| `ex:SmartWatch` | `ex:Wearable` | Smart Watch |
| `ex:SpO2Sensor` | `ex:PhysiologicalSensor` | Blood oxygen saturation sensor. |
| `ex:StandardSpecification` | — | Standard Specification |
| `ex:State` | `ex:TemporalEntity` | Dynamic state of an entity; temporal and distinguishable from instantaneous observations. |
| `ex:StressLevel` | — | Stress Level |
| `ex:StressObservation` | `sosa:Observation` | Output of the stress prediction model. |
| `ex:SynchronizationEvent` | `ex:AdaptationAction` | Synchronization Event |
| `ex:TemperatureSensor` | `ex:PhysiologicalSensor` | Skin temperature — used as stress indicator. |
| `ex:TemporalEntity` | — | Entity with an explicit validity interval. validTo denotes effective closure, never merely planned expiry. |
| `ex:TrafficWindow` | — | Time interval with high demand (morning: wake-up; night: physiological data upload). |
| `ex:TransferEvent` | `ex:TemporalEntity` | Auditable transfer of data, model updates or other payloads. |
| `ex:TrustAssessment` | `ex:TemporalEntity` | Versioned assessment explaining a trust score. |
| `ex:TrustEvidence` | — | Trust Evidence |
| `ex:UrbanEnvironment` | — | Geographic and density context that conditions system connectivity and behaviour. |
| `ex:UrbanZone` | `ex:CityArea` | High node and user density. More communication options. |
| `ex:User` | `foaf:Person` | System participant with a wearable device. |
| `ex:UserState` | `ex:State` | User State |
| `ex:ValidationCampaign` | `ex:Artifact` | Validation Campaign |
| `ex:ValidationRequirement` | `ex:Requirement` | Validation / Reproducibility Requirement |
| `ex:ValidationResult` | — | Validation Result |
| `ex:Wearable` | `saref:Device` | Personal IoT device (smartwatch, smart ring, smart band). |
| `ex:WorkloadLevel` | — | Workload Level |

### 7.2 Clases externas reutilizadas

- `geo:Feature`
- `geo:Geometry`
- `sosa:Observation`
- `sosa:Platform`
- `sosa:Sensor`
- `foaf:Person`
- `saref:Device`

## 8. Catálogo completo de propiedades de objeto

La ontología declara **162 propiedades de objeto**: **157 propias (`ex:`)** y 5 reutilizadas de vocabularios externos.

### 8.1 Propiedades `ex:`

| Propiedad | Dominio | Rango | Función |
|---|---|---|---|
| `ex:actionOriginNode` | `ex:AdaptationAction` | `ex:ComputationalNode` | action origin node |
| `ex:actionTargetNode` | `ex:AdaptationAction` | `ex:ComputationalNode` | action target node |
| `ex:affectsModel` | `ex:AdaptationAction` | `ex:AIModel` | affects model |
| `ex:affectsService` | `ex:AdaptationAction` | `ex:Service` | affects service |
| `ex:aggregatesData` | `ex:ComputationalNode` | `ex:ParametrizedData` | aggregates data |
| `ex:alternativeModelTier` | `ex:DecisionAlternative` | `ex:ModelTier` | alternative model tier |
| `ex:appliedMechanism` | `ex:EvaluationState` | `ex:MechanismSpecification` | applied mechanism |
| `ex:appliedPolicy` | `ex:EvaluationState` | `ex:Policy` | applied policy |
| `ex:appliedSecurityMechanism` | — | `ex:SecurityMechanism` | applied security mechanism |
| `ex:appliesInZone` | `ex:Policy` | `ex:CityArea` | applies in zone |
| `ex:appliesPolicy` | `ex:EvaluationState` | `ex:Policy` | Deprecated in v3.0.0; use ex:appliedPolicy. Use appliedPolicy |
| `ex:appliesTo` | `ex:Permission` | — | applies to |
| `ex:appliesToZoneType` | `ex:Policy` | `owl:Class` | applies to zone type |
| `ex:auditsContract` | `ex:EvaluationState` | `ex:SemanticContract` | audits contract |
| `ex:authorizedByEvaluation` | `ex:AdaptationAction` | `ex:EvaluationState` | authorized by evaluation |
| `ex:basedOnConsentRecord` | `ex:AuthorizationDecision` | `ex:ConsentRecord` | based on consent record |
| `ex:basedOnContract` | `ex:AuthorizationDecision` | `ex:SemanticContract` | based on contract |
| `ex:basedOnZone` | `ex:AuthorizationDecision` | `ex:CityArea` | based on zone |
| `ex:belongsToCommunity` | `ex:User` | `ex:Community` | belongs to community |
| `ex:belongsToPolicyCategory` | `ex:Policy` | `ex:PolicyCategory` | belongs to policy category |
| `ex:belongsToQueryCatalog` | `ex:QuerySpecification` | `ex:QueryCatalog` | belongs to query catalog |
| `ex:budgetForContract` | `ex:PrivacyBudgetAccount` | `ex:SemanticContract` | budget for contract |
| `ex:budgetForPurpose` | `ex:PrivacyBudgetAccount` | `ex:ProcessingPurpose` | budget for purpose |
| `ex:carriesData` | `ex:TransferEvent` | — | carries data |
| `ex:connectsTo` | `saref:Device` | `ex:ComputationalNode` | connects to |
| `ex:consentSubject` | `ex:ConsentRecord` | `ex:User` | consent subject |
| `ex:contextDeviceState` | `ex:DataContext` | `ex:DeviceState` | context device state |
| `ex:contextNodeState` | `ex:DataContext` | `ex:NodeState` | context node state |
| `ex:contextProcessingLevel` | `ex:DataContext` | `ex:ProcessingLevel` | context processing level |
| `ex:contextPurpose` | `ex:DataContext` | `ex:ProcessingPurpose` | context purpose |
| `ex:contextZone` | `ex:DataContext` | `ex:CityArea` | context zone |
| `ex:contractSubject` | `ex:SemanticContract` | `ex:User` | contract subject |
| `ex:coversArea` | `ex:ComputationalNode` | `ex:CityArea` | covers area |
| `ex:criterionA` | `ex:PairwiseComparison` | — | criterion A |
| `ex:criterionB` | `ex:PairwiseComparison` | — | criterion B |
| `ex:definedInArtifact` | — | `ex:Artifact` | defined in artifact |
| `ex:delegatedBy` | `ex:DelegationEvent` | `ex:ComputationalNode` | delegated by |
| `ex:delegatesTo` | `ex:ComputationalNode ∪ ex:DelegationEvent` | `ex:ComputationalNode` | Used when a node is saturated or disconnected. For temporal delegation, use an ex:DelegationEvent with ex:validFrom/ex:validTo and ex:delegatedBy. |
| `ex:derivedFrom` | `ex:State` | `sosa:Observation` | SOSA observation that originated this state and provides its timestamp. |
| `ex:evaluatesNode` | `ex:EvaluationState` | `ex:ComputationalNode` | evaluates node |
| `ex:evaluatesService` | `ex:EvaluationState` | `ex:Service` | evaluates service |
| `ex:evaluationPurpose` | `ex:EvaluationState` | `ex:ProcessingPurpose` | evaluation purpose |
| `ex:evaluationUser` | `ex:EvaluationState` | `ex:User` | evaluation user |
| `ex:evaluationZone` | `ex:EvaluationState` | `ex:CityArea` | evaluation zone |
| `ex:expiresOnRecoveryOf` | `ex:DelegationEvent` | `ex:ComputationalNode` | Use semantic RecoveryCondition together with validTo/plannedExpiry. |
| `ex:generatedBy` | `ex:ParametrizedData` | `ex:Wearable` | generated by |
| `ex:governedBy` | — | `ex:Policy` | Links users, nodes, services, zones or sessions to the applicable policy according to location and processing context. |
| `ex:hasActiveConsentRange` | `ex:User` | `ex:ConsentRange` | Current user-declared range resolved from the active ConsentRecord. It is intentionally independent from the SemanticContract so inconsistencies can be detected. |
| `ex:hasAdaptability` | `ex:ServiceState` | `ex:AdaptabilityLevel` | has adaptability |
| `ex:hasAuthorizationDecision` | — | `ex:AuthorizationDecision` | has authorization decision |
| `ex:hasAuthorizationOutcome` | `ex:AuthorizationDecision` | `ex:AuthorizationOutcome` | has authorization outcome |
| `ex:hasAuthorizedDataCategory` | `ex:ConsentRecord` | `ex:DataCategory` | authorizes data category |
| `ex:hasAvailability` | `ex:NodeState` | `ex:AvailabilityLevel` | has availability |
| `ex:hasBatteryLevel` | `ex:DeviceState` | `ex:BatteryLevel` | has battery level |
| `ex:hasCommunication` | `ex:NodeState` | `ex:CommunicationLevel` | has communication level |
| `ex:hasComplianceMetric` | `ex:ValidationCampaign` | `ex:ComplianceMetric` | has compliance metric |
| `ex:hasConnectionStatus` | `ex:DeviceState` | `ex:DeviceConnectionStatus` | has connection status |
| `ex:hasConsentRange` | `ex:User ∪ ex:SemanticContract ∪ ex:Policy ∪ ex:FederatedLearningSession ∪ ex:EvaluationState` | `ex:ConsentRange` | has consent range |
| `ex:hasConsentRecord` | `ex:User` | `ex:ConsentRecord` | has consent record |
| `ex:hasDataCategory` | — | `ex:DataCategory` | has data category |
| `ex:hasDataContext` | — | `ex:DataContext` | has data context |
| `ex:hasDataCriticality` | — | `ex:DataCriticality` | has data criticality |
| `ex:hasDataSensitivity` | — | `ex:DataSensitivity` | has data sensitivity |
| `ex:hasDecisionAlternative` | `ex:EvaluationState` | `ex:DecisionAlternative` | has decision alternative |
| `ex:hasDecisionMethod` | `ex:EvaluationState` | `ex:DecisionMethod` | has decision method |
| `ex:hasDegradationCause` | — | `ex:ModelDegradationCause` | has degradation cause |
| `ex:hasDelegation` | `ex:ComputationalNode` | `ex:DelegationEvent` | has delegation |
| `ex:hasDetectedSymptom` | `ex:EvaluationState` | `ex:MAPESymptom` | has detected symptom |
| `ex:hasDeviceState` | `ex:Wearable` | `ex:DeviceState` | has device state |
| `ex:hasDistance` | `ex:NodeUserRelation` | `ex:DistanceLevel` | has distance |
| `ex:hasEffectiveConsentRange` | `ex:AuthorizationDecision` | `ex:ConsentRange` | has effective consent range |
| `ex:hasEnergyLevel` | `ex:NodeState` | `ex:EnergyLevel` | has energy level |
| `ex:hasGeometry` | `ex:CityArea` | `geo:Geometry` | has geometry |
| `ex:hasIdentifier` | `ex:User` | `ex:Identifier` | has identifier |
| `ex:hasMigrationCost` | `ex:EvaluationState` | `ex:MigrationCostLevel` | has migration cost |
| `ex:hasMigrationTime` | `ex:EvaluationState` | `ex:MigrationTimeLevel` | has migration time |
| `ex:hasMobileDevice` | `ex:User` | `ex:MobileDevice` | has mobile device |
| `ex:hasMobility` | `ex:UserState` | `ex:MobilityLevel` | has mobility |
| `ex:hasModelTier` | `ex:AIModel` | `ex:ModelTier` | has model tier |
| `ex:hasNeighborNode` | `ex:ComputationalNode` | `ex:ComputationalNode` | Adjacent node to which requests can be delegated. |
| `ex:hasNodeState` | `ex:ComputationalNode` | `ex:NodeState` | has node state |
| `ex:hasOperationalStatus` | `ex:NodeState` | `ex:OperationalStatus` | has operational status |
| `ex:hasPairwiseComparison` | `ex:EvaluationState` | `ex:PairwiseComparison` | has pairwise comparison |
| `ex:hasPayloadType` | `ex:FederatedLearningSession` | `ex:PayloadType` | has payload type |
| `ex:hasPerformance` | `ex:NodeState` | `ex:PerformanceLevel` | has performance |
| `ex:hasPermission` | `ex:Role` | `ex:Permission` | has permission |
| `ex:hasPersonStatus` | `ex:UserState` | `ex:PersonStatus` | has person status |
| `ex:hasPolicyRelationType` | `ex:PolicyCategoryRelation` | `ex:PolicyRelationType` | has policy relation type |
| `ex:hasPolicyType` | `ex:Policy` | `ex:PolicyType` | has policy type |
| `ex:hasPopulationDensity` | `ex:CityArea` | `ex:PopulationDensity` | has population density |
| `ex:hasPredictedStressLevel` | `ex:UserState` | `ex:StressLevel` | has predicted stress level |
| `ex:hasPrivacyBudgetAccount` | `ex:FederatedLearningSession` | `ex:PrivacyBudgetAccount` | has privacy budget account |
| `ex:hasPrivacyMechanism` | `ex:FederatedLearningSession ∪ ex:ParametrizedData` | `ex:PrivacyMechanism` | has privacy mechanism |
| `ex:hasProcessingLevel` | `ex:ServiceState` | `ex:ProcessingLevel` | has processing level |
| `ex:hasProcessingPurpose` | `ex:SemanticContract ∪ ex:Policy ∪ ex:FederatedLearningSession ∪ ex:EvaluationState ∪ ex:Permission` | `ex:ProcessingPurpose` | has processing purpose |
| `ex:hasProcessingScope` | `ex:ModelTier` | `ex:ProcessingScope` | has processing scope |
| `ex:hasProfitability` | `ex:EvaluationState` | `ex:ProfitabilityLevel` | has profitability |
| `ex:hasQueryType` | `ex:QuerySpecification` | `ex:QueryType` | has query type |
| `ex:hasRecoveryCondition` | `ex:DelegationEvent` | `ex:RecoveryCondition` | has recovery condition |
| `ex:hasReplicationEvent` | — | `ex:ReplicationEvent` | has replication event |
| `ex:hasResidualCapacity` | `ex:NodeState` | `ex:ResidualCapacity` | has residual capacity |
| `ex:hasRole` | `foaf:Person` | `ex:Role` | has role |
| `ex:hasSemanticContract` | `ex:User` | `ex:SemanticContract` | has semantic contract |
| `ex:hasServiceState` | `ex:Service` | `ex:ServiceState` | has service state |
| `ex:hasTrustAssessment` | `ex:NodeState` | `ex:TrustAssessment` | has trust assessment |
| `ex:hasTrustEvidence` | `ex:TrustAssessment` | `ex:TrustEvidence` | has trust evidence |
| `ex:hasUserState` | `ex:User` | `ex:UserState` | has user state |
| `ex:hasValidationResult` | `ex:ValidationCampaign` | `ex:ValidationResult` | has validation result |
| `ex:hasWearable` | `ex:User` | `ex:Wearable` | has wearable |
| `ex:hasWorkload` | `ex:NodeState` | `ex:WorkloadLevel` | has workload |
| `ex:hostedOnNode` | `ex:AIModel` | `ex:ComputationalNode` | hosted on node |
| `ex:hostsModel` | `ex:ComputationalNode` | `ex:AIModel` | hosts model |
| `ex:hostsService` | `ex:ComputationalNode` | `ex:Service` | hosts service |
| `ex:involvedNode` | `ex:FederatedLearningSession` | `ex:ComputationalNode` | involved node |
| `ex:locatedIn` | — | — | located in |
| `ex:locatedInZone` | `ex:User` | `ex:CityArea` | located in zone |
| `ex:originatesFromDevice` | `ex:ParametrizedData` | `ex:MobileDevice` | originates from device |
| `ex:parentDelegation` | `ex:DelegationEvent` | `ex:DelegationEvent` | parent delegation |
| `ex:partOfScenario` | — | `ex:Scenario` | part of scenario |
| `ex:policyArtifactUsed` | `ex:EvaluationState` | `ex:PolicyArtifact` | policy artifact used |
| `ex:recommendedMechanism` | `ex:Policy` | `ex:MechanismSpecification` | recommended mechanism |
| `ex:relatedRequirement` | `ex:Policy` | `ex:Requirement` | related requirement |
| `ex:relatesNode` | `ex:NodeUserRelation` | `ex:ComputationalNode` | relates node |
| `ex:relatesUser` | `ex:NodeUserRelation` | `ex:User` | relates user |
| `ex:relationSourceCategory` | `ex:PolicyCategoryRelation` | `ex:PolicyCategory` | relation source category |
| `ex:relationTargetCategory` | `ex:PolicyCategoryRelation` | `ex:PolicyCategory` | relation target category |
| `ex:replicaOf` | — | — | replica of |
| `ex:replicationSource` | `ex:ReplicationEvent` | — | replication source |
| `ex:replicationTarget` | `ex:ReplicationEvent` | — | replication target |
| `ex:requirementsArtifactUsed` | `ex:EvaluationState` | `ex:RequirementsArtifact` | requirements artifact used |
| `ex:requiresConsentRange` | `ex:Permission ∪ ex:Policy ∪ ex:Service ∪ ex:ServiceState ∪ ex:AIModel ∪ ex:FederatedLearningSession ∪ ex:EvaluationState` | `ex:ConsentRange` | Minimum consent-aware processing scope required for an action, policy, model tier or FL session. |
| `ex:resultedInAction` | `ex:EvaluationState` | `ex:AdaptationAction` | resulted in action |
| `ex:rollbackTarget` | `ex:RollbackEvent` | `ex:AIModel` | rollback target |
| `ex:scenarioMechanism` | `ex:Scenario` | `ex:MechanismSpecification` | scenario mechanism |
| `ex:scenarioPolicy` | `ex:Scenario` | `ex:Policy` | scenario policy |
| `ex:selectedAlternative` | `ex:EvaluationState` | `ex:DecisionAlternative` | selected alternative |
| `ex:selectedModelTier` | `ex:EvaluationState` | `ex:ModelTier` | Model tier selected by the AHP-style decision balance. |
| `ex:sentToNode` | `ex:ParametrizedData` | `ex:ComputationalNode` | sent to node |
| `ex:supersedesModel` | `ex:AIModel` | `ex:AIModel` | supersedes model |
| `ex:supportsPolicy` | `ex:MechanismSpecification` | `ex:Policy` | supports policy |
| `ex:tracedToMechanism` | `ex:Requirement` | `ex:MechanismSpecification` | traced to mechanism |
| `ex:tracedToPolicy` | `ex:Requirement` | `ex:Policy` | traced to policy |
| `ex:transferDestination` | `ex:TransferEvent` | — | transfer destination |
| `ex:transfersData` | `ex:FederatedLearningSession` | `ex:ParametrizedData` | transfers data |
| `ex:transferSource` | `ex:TransferEvent` | — | transfer source |
| `ex:triggeredByState` | `ex:DelegationEvent ∪ ex:EvaluationState` | `ex:State` | triggered by state |
| `ex:trustAssessmentForState` | `ex:TrustAssessment` | `ex:NodeState` | trust assessment for state |
| `ex:updatesModel` | `ex:FederatedLearningSession` | `ex:AIModel` | updates model |
| `ex:usesAcceptanceProfile` | `ex:ValidationCampaign` | `ex:AcceptanceProfile` | uses acceptance profile |
| `ex:usesIdentifier` | `ex:TransferEvent` | `ex:Identifier` | uses identifier |
| `ex:usesModel` | `ex:Service` | `ex:AIModel` | Model used by a service. Distinct from hostsModel, whose subject is a ComputationalNode. |
| `ex:usesResolutionStrategy` | `ex:PolicyCategoryRelation` | `ex:ConflictResolutionStrategy` | uses resolution strategy |
| `ex:usesStandard` | `ex:Artifact` | `ex:StandardSpecification` | uses standard |
| `ex:validationUsesOntology` | `ex:ValidationCampaign` | `ex:OntologyArtifact` | validation uses ontology |
| `ex:validationUsesPolicies` | `ex:ValidationCampaign` | `ex:PolicyArtifact` | validation uses policies |
| `ex:validationUsesQueries` | `ex:ValidationCampaign` | `ex:QueryCatalog` | validation uses queries |
| `ex:validationUsesScenarios` | `ex:ValidationCampaign` | `ex:ScenarioArtifact` | validation uses scenarios |

### 8.2 Propiedades externas declaradas/reutilizadas

- `geo:hasGeometry`
- `sosa:hasFeatureOfInterest`
- `sosa:isHostedBy`
- `sosa:madeBySensor`
- `sosa:observedProperty`

## 9. Catálogo completo de propiedades de datos

La ontología declara **94 propiedades de datos**: **92 propias (`ex:`)** y 2 reutilizadas de SOSA.

### 9.1 Propiedades `ex:`

| Propiedad | Dominio | Rango | Función |
|---|---|---|---|
| `ex:AHP_consistency_threshold` | `ex:AcceptanceProfile` | `xsd:decimal` | AHP consistency threshold |
| `ex:artifactIdentifier` | `ex:Artifact` | `xsd:string` | artifact identifier |
| `ex:artifactStatus` | `ex:Artifact` | `xsd:string` | artifact status |
| `ex:artifactVersion` | `ex:Artifact` | `xsd:string` | artifact version |
| `ex:authorizationReason` | `ex:AuthorizationDecision` | `xsd:string` | authorization reason |
| `ex:categoryCode` | `ex:PolicyCategory` | `xsd:string` | category code |
| `ex:conditionExpression` | `ex:RecoveryCondition` | `xsd:string` | condition expression |
| `ex:configurationStatus` | — | `xsd:string` | configuration status |
| `ex:containsIndividualizedGradients` | `ex:FederatedLearningSession` | `xsd:boolean` | contains individualized gradients |
| `ex:containsPersistentIdentifier` | `ex:FederatedLearningSession` | `xsd:boolean` | contains persistent identifier |
| `ex:containsPersonalData` | `ex:FederatedLearningSession` | `xsd:boolean` | contains personal data |
| `ex:continuumLevel` | `ex:ModelTier` | `xsd:integer` | Physical/logical continuum level only; not a preference or quality ranking. |
| `ex:D_delegation_max` | `ex:AcceptanceProfile` | `xsd:integer` | maximum delegation depth |
| `ex:delegationDepth` | `ex:DelegationEvent` | `xsd:integer` | delegation depth |
| `ex:E_device_max` | `ex:AcceptanceProfile` | `xsd:decimal` | device energy threshold |
| `ex:eligibilityReason` | `ex:DecisionAlternative` | `xsd:string` | eligibility reason |
| `ex:estimatedPredictionError` | `ex:EvaluationState` | `xsd:decimal` | estimated prediction error |
| `ex:evaluationOrder` | `ex:PolicyCategory` | `xsd:integer` | evaluation order |
| `ex:evidenceContribution` | `ex:TrustEvidence` | `xsd:decimal` | evidence contribution |
| `ex:evidenceFactor` | `ex:TrustEvidence` | `xsd:string` | evidence factor |
| `ex:hasAHPScore` | `ex:DecisionAlternative` | `xsd:decimal` | Score of a specific candidate alternative. For AHP it is the AHP result; for other methods the DecisionMethod identifies the scoring semantics. |
| `ex:hasAnonymizationApplied` | `ex:ParametrizedData` | `xsd:boolean` | has anonymization applied |
| `ex:hasConsistencyRatio` | `ex:EvaluationState` | `xsd:decimal` | has consistency ratio |
| `ex:hasConsistencyThreshold` | `ex:EvaluationState` | `xsd:decimal` | has consistency threshold |
| `ex:hasElasticity` | `ex:ComputationalNode` | `xsd:boolean` | has elasticity |
| `ex:hasEvaluationTicketID` | `ex:EvaluationState` | `xsd:string` | has evaluation ticket ID |
| `ex:hasLatencyWeight` | `ex:EvaluationState` | `xsd:decimal` | has latency weight |
| `ex:hasModelQualityWeight` | `ex:EvaluationState` | `xsd:decimal` | has model quality weight |
| `ex:hasNoiseApplied` | `ex:ParametrizedData` | `xsd:boolean` | has noise applied |
| `ex:hasPolicyAction` | `ex:Policy` | `xsd:string` | Policy action is now described by the normative policy statement and linked mechanisms/actions; retained only for compatibility. |
| `ex:hasPolicyStatement` | `ex:Policy` | `xsd:string` | has policy statement |
| `ex:hasPrivacyBudget` | `ex:FederatedLearningSession` | `xsd:decimal` | Differential privacy epsilon value for the FL session. |
| `ex:hasPrivacyWeight` | `ex:EvaluationState` | `xsd:decimal` | has privacy weight |
| `ex:hasSelectionJustification` | `ex:EvaluationState` | `xsd:string` | has selection justification |
| `ex:hasTrustScore` | — | `xsd:decimal` | Normalized historical reliability score [0,1]. A v3-compliant scientific use should also reference TrustAssessment with rule version and historical window. |
| `ex:hasTrustWeight` | `ex:EvaluationState` | `xsd:decimal` | External trust criterion used to filter/order already eligible alternatives. It is not part of AHP weight normalization. |
| `ex:idempotencyKey` | — | `xsd:string` | idempotency key |
| `ex:identifierScope` | `ex:Identifier` | `xsd:string` | identifier scope |
| `ex:identifierValue` | `ex:Identifier` | `xsd:string` | identifier value |
| `ex:isEligible` | `ex:DecisionAlternative` | `xsd:boolean` | is eligible |
| `ex:isPreferredNode` | `ex:NodeUserRelation` | `xsd:boolean` | Historical preferred node for this user based on zone and load. |
| `ex:isRedundant` | `ex:ParametrizedData` | `xsd:boolean` | Redundant or repetitive data — candidate for elimination to reduce traffic. |
| `ex:lastUpdated` | `ex:AIModel` | `xsd:dateTime` | last updated |
| `ex:legacyDecisionScore` | `ex:EvaluationState` | `xsd:decimal` | Legacy single winning score retained for provenance. It is not equivalent to v3 per-alternative scores. |
| `ex:mechanismDescription` | `ex:MechanismSpecification` | `xsd:string` | mechanism description |
| `ex:mechanismIdentifier` | `ex:MechanismSpecification` | `xsd:string` | mechanism identifier |
| `ex:migrationNote` | — | `xsd:string` | migration note |
| `ex:migrationStatus` | — | `xsd:string` | migration status |
| `ex:modelLineageStatus` | `ex:AIModel` | `xsd:string` | model lineage status |
| `ex:modelVersion` | `ex:AIModel` | `xsd:string` | model version |
| `ex:N_agents` | `ex:AcceptanceProfile` | `xsd:integer` | concurrent agent target |
| `ex:noiseLevel` | `ex:FederatedLearningSession` | `xsd:decimal` | Magnitude of noise injected into gradients or model parameters before transfer. |
| `ex:observedModelQuality` | `ex:EvaluationState` | `xsd:decimal` | observed model quality |
| `ex:pairwiseValue` | `ex:PairwiseComparison` | `xsd:decimal` | pairwise comparison value |
| `ex:parametrizedDataReady` | `ex:DeviceState` | `xsd:boolean` | parametrized data ready |
| `ex:plannedExpiry` | `ex:TemporalEntity` | `xsd:dateTime` | Planned deadline distinct from effective closure validTo. |
| `ex:policyIdentifier` | `ex:Policy` | `xsd:string` | policy identifier |
| `ex:policyVersion` | `ex:Policy` | `xsd:string` | policy version |
| `ex:predictionConfidence` | `ex:EvaluationState` | `xsd:decimal` | prediction confidence |
| `ex:privacyBudgetConsumed` | `ex:PrivacyBudgetAccount` | `xsd:decimal` | privacy budget consumed |
| `ex:privacyBudgetMaximum` | `ex:PrivacyBudgetAccount` | `xsd:decimal` | privacy budget maximum |
| `ex:privacyBudgetRemaining` | `ex:PrivacyBudgetAccount` | `xsd:decimal` | privacy budget remaining |
| `ex:protectsAtRest` | `ex:SecurityMechanism` | `xsd:boolean` | protects at rest |
| `ex:protectsInTransit` | `ex:SecurityMechanism` | `xsd:boolean` | protects in transit |
| `ex:queryIdentifier` | `ex:QuerySpecification` | `xsd:string` | query identifier |
| `ex:queryInterpretation` | `ex:QuerySpecification` | `xsd:string` | query interpretation |
| `ex:queryPurpose` | `ex:QuerySpecification` | `xsd:string` | query purpose |
| `ex:queuedRequests` | `ex:NodeState` | `xsd:integer` | queued requests |
| `ex:relationCode` | `ex:PolicyRelationType` | `xsd:string` | relation code |
| `ex:replicationVersion` | — | `xsd:string` | replication version |
| `ex:requirementIdentifier` | `ex:Requirement` | `xsd:string` | requirement identifier |
| `ex:requirementStatement` | `ex:Requirement` | `xsd:string` | requirement statement |
| `ex:requiresRecalculation` | `ex:EvaluationState` | `xsd:boolean` | requires recalculation |
| `ex:resourceUsagePercent` | `ex:NodeState` | `xsd:decimal` | resource usage (%) |
| `ex:scenarioIdentifier` | `ex:Scenario` | `xsd:string` | scenario identifier |
| `ex:securityBaselineVersion` | `ex:SecurityMechanism` | `xsd:string` | security baseline version |
| `ex:sendTimestamp` | `ex:ParametrizedData` | `xsd:dateTime` | send timestamp |
| `ex:sessionTime` | `ex:FederatedLearningSession` | `xsd:dateTime` | session time |
| `ex:stateDuration` | `ex:State` | `xsd:duration` | Computed as validTo - validFrom. |
| `ex:strategyCode` | `ex:ConflictResolutionStrategy` | `xsd:string` | strategy code |
| `ex:T_decision_max` | `ex:AcceptanceProfile` | `xsd:decimal` | decision threshold |
| `ex:T_inference_local` | `ex:AcceptanceProfile` | `xsd:decimal` | local inference latency threshold (ms) |
| `ex:T_migration_max` | `ex:AcceptanceProfile` | `xsd:decimal` | migration interruption threshold |
| `ex:T_node_join` | `ex:AcceptanceProfile` | `xsd:decimal` | node join threshold |
| `ex:T_reselection_max` | `ex:AcceptanceProfile` | `xsd:decimal` | reselection threshold |
| `ex:T_sparql_monitor` | `ex:AcceptanceProfile` | `xsd:decimal` | SPARQL monitoring threshold |
| `ex:trustRuleVersion` | `ex:TrustAssessment` | `xsd:string` | trust rule version |
| `ex:trustWindowEnd` | `ex:TrustAssessment` | `xsd:dateTime` | trust window end |
| `ex:trustWindowStart` | `ex:TrustAssessment` | `xsd:dateTime` | trust window start |
| `ex:userFeedbackScore` | `ex:UserState` | `xsd:integer` | User rating of the previous day's prediction (local model without consent). |
| `ex:validFrom` | `ex:TemporalEntity` | `xsd:dateTime` | Effective start timestamp of a temporal entity. |
| `ex:validTo` | `ex:TemporalEntity` | `xsd:dateTime` | Effective closure timestamp. It must not be used for a planned expiration before actual closure. |

### 9.2 Propiedades externas de datos

- `sosa:hasSimpleResult`
- `sosa:resultTime`

## 10. Vocabularios controlados e individuos clave

| Clase de vocabulario | Individuos |
|---|---|
| `ex:EnergyLevel` | `ex:HighEnergy`, `ex:LowEnergy`, `ex:MediumEnergy`, `ex:VeryLowEnergy` |
| `ex:AvailabilityLevel` | `ex:Available`, `ex:NotAvailable`, `ex:Partial` |
| `ex:PerformanceLevel` | `ex:Acceptable`, `ex:Deficient`, `ex:Optimal` |
| `ex:WorkloadLevel` | `ex:HighWorkload`, `ex:LowWorkload`, `ex:MediumWorkload`, `ex:NoWorkload`, `ex:SaturatedWorkload` |
| `ex:CommunicationLevel` | `ex:IntermittentComm`, `ex:NoConnectionComm`, `ex:StableComm`, `ex:VariableComm` |
| `ex:ResidualCapacity` | `ex:CriticalResidual`, `ex:HighResidual`, `ex:LowResidual`, `ex:MediumResidual` |
| `ex:OperationalStatus` | `ex:ComputeOnly`, `ex:Inoperative`, `ex:Operational` |
| `ex:MobilityLevel` | `ex:InTransport`, `ex:Running`, `ex:Still`, `ex:Walking` |
| `ex:PersonStatus` | `ex:Agitated`, `ex:Asleep`, `ex:Calm` |
| `ex:StressLevel` | `ex:StressCritical`, `ex:StressHigh`, `ex:StressLow`, `ex:StressMedium` |
| `ex:BatteryLevel` | `ex:BatteryHigh`, `ex:BatteryLow`, `ex:BatteryMedium`, `ex:BatteryVeryLow` |
| `ex:DeviceConnectionStatus` | `ex:AirplaneMode`, `ex:Connected`, `ex:Disconnected` |
| `ex:ProcessingLevel` | `ex:FullProcessing`, `ex:MinimalProcessing`, `ex:ReducedProcessing` |
| `ex:AdaptabilityLevel` | `ex:Migratable`, `ex:MigratableAndScalable`, `ex:NotAdaptable`, `ex:Scalable` |
| `ex:ProfitabilityLevel` | `ex:Adequate`, `ex:NotAdequate` |
| `ex:MigrationTimeLevel` | `ex:TimingHigh`, `ex:TimingLow`, `ex:TimingMedium`, `ex:TimingVeryHigh`, `ex:TimingVeryLow` |
| `ex:MigrationCostLevel` | `ex:CostHigh`, `ex:CostLow`, `ex:CostMedium`, `ex:CostVeryHigh`, `ex:CostVeryLow` |
| `ex:DistanceLevel` | `ex:Close`, `ex:Far`, `ex:Near`, `ex:VeryClose`, `ex:VeryFar` |
| `ex:PopulationDensity` | `ex:HighDensity`, `ex:LowDensity`, `ex:MediumDensity` |
| `ex:ConsentRange` | `ex:RangeCommunityAgg`, `ex:RangeDenied`, `ex:RangeGlobalAgg`, `ex:RangeLocalOnly` |
| `ex:PolicyType` | `ex:AbstentionPolicyType`, `ex:ObligationPolicyType`, `ex:ProhibitionPolicyType` |
| `ex:ProcessingPurpose` | `ex:PurposeClinicalMonitoring`, `ex:PurposeCommunityFederatedLearning`, `ex:PurposeGlobalFederatedLearning`, `ex:PurposeInfrastructureAdaptation`, `ex:PurposeLocalPrediction` |
| `ex:ModelTier` | `ex:CloudModelTier`, `ex:EdgeModelTier`, `ex:FogModelTier`, `ex:LocalModelTier` |
| `ex:ModelDegradationCause` | `ex:CommunicationLoss`, `ex:InfrastructureOverload`, `ex:LowBattery`, `ex:NoNearbyNodes` |
| `ex:MAPESymptom` | `ex:SymptomCommunicationLoss`, `ex:SymptomConsentLocalOnly`, `ex:SymptomNodeRecoveryPending`, `ex:SymptomNone`, `ex:SymptomRestrictedZoneBoundary`, `ex:SymptomRuralLowConnectivity`, `ex:SymptomSaturatedWorkload` |
| `ex:AuthorizationOutcome` | `ex:AuthorizationBlocked`, `ex:AuthorizationGranted`, `ex:AuthorizationInconsistent`, `ex:PendingRecalculation` |
| `ex:ProcessingScope` | `ex:ExternalProcessingScope`, `ex:LocalProcessingScope` |
| `ex:PayloadType` | `ex:GlobalModelParametersPayload`, `ex:ImprovedModelParametersPayload`, `ex:ModelGradientsPayload`, `ex:ParametrizedDataPayload` |
| `ex:DataCategory` | `ex:ModelGradientCategory`, `ex:ModelParametersCategory`, `ex:PhysiologicalParametrizedCategory`, `ex:PredictionCategory`, `ex:RawPhysiologicalDataCategory`, `ex:RawSleepDataCategory`, `ex:SleepParametrizedCategory` |
| `ex:DataCriticality` | `ex:CriticalData`, `ex:HighPriorityData`, `ex:LowPriorityData`, `ex:NormalPriorityData` |
| `ex:DataSensitivity` | `ex:NonSensitiveData`, `ex:SensitiveData` |
| `ex:DecisionMethod` | `ex:AHPDecisionMethod`, `ex:WeightedMulticriteriaMethod` |
| `ex:PolicyRelationType` | `ex:PolicyRelationType_CO`, `ex:PolicyRelationType_CON`, `ex:PolicyRelationType_COR`, `ex:PolicyRelationType_DEP`, `ex:PolicyRelationType_GEN`, `ex:PolicyRelationType_IND`, `ex:PolicyRelationType_IRR`, `ex:PolicyRelationType_RED`, `ex:PolicyRelationType_SHD`, `ex:PolicyRelationType_SUB` |
| `ex:ConflictResolutionStrategy` | `ex:Resolution_CONSTRAINT_BEFORE_OPT`, `ex:Resolution_DEFER_REEVALUATE`, `ex:Resolution_DENY_OVERRIDES`, `ex:Resolution_EXPLICIT_REJECT`, `ex:Resolution_MOST_SPECIFIC`, `ex:Resolution_PRIORITY_ORDERED` |
| `ex:QueryType` | `ex:InspectionQueryType`, `ex:ViolationQueryType`, `ex:WarningQueryType` |

### 10.1 Rangos de consentimiento

| Rango | Semántica operativa |
|---|---|
| `ex:RangeDenied` | No autoriza procesamiento/transferencia dependiente del consentimiento. |
| `ex:RangeLocalOnly` | Procesamiento limitado al ámbito personal/local autorizado. |
| `ex:RangeCommunityAgg` | Permite agregación comunitaria solo si contrato, zona y políticas lo mantienen autorizado. |
| `ex:RangeGlobalAgg` | Puede habilitar agregación global/Cloud, siempre tras el resto de restricciones duras. |

### 10.2 Instancias operativas principales

Las tablas siguientes resumen los individuos de escenario más relevantes. No sustituyen el catálogo RDF completo de 669 individuos, pero documentan las entidades operativas que articulan S1–S8 y los módulos nuevos de v3.

#### Usuarios y dispositivos personales

| Usuario | Wearable(s) | Móvil/Mist | Rango activo | Zona actual |
|---|---|---|---|---|
| `ex:UserA` | `ex:WatchA` | `ex:MobileA` | `ex:RangeGlobalAgg` | `ex:CityCentreZone` |
| `ex:UserB` | `ex:RingB` | — | `ex:RangeLocalOnly` | `ex:UnknownZone` (en `Eval_S5`; zona histórica no conocida) |
| `ex:UserC` | `ex:BandC` | `ex:MobileC` | `ex:RangeCommunityAgg` | `ex:NorthRuralZone` |
| `ex:UserD` | `ex:WatchD` | — | `ex:RangeCommunityAgg` | `ex:CareFacility1` |

#### Nodos del continuum

| Nodo | Tipo(s) | Elasticidad | Zonas cubiertas |
|---|---|---|---|
| `ex:CloudNode1` | `ex:CloudNode` | true | — |
| `ex:EdgeNode1` | `ex:EdgeNode` | false | `ex:CityCentreZone` |
| `ex:EdgeNode2` | `ex:EdgeNode` | false | — |
| `ex:FogNode1` | `ex:FogNode` | false | `ex:CityCentreZone` |
| `ex:InternalEdgeFacility` | `ex:MistNode` | false | `ex:CareFacility1` |
| `ex:RingB` | `ex:MistNode` | — | — |

#### Modelos de IA

| Modelo | Tier | Host | Versión | Linaje |
|---|---|---|---|---|
| `ex:ModelCloud1` | `ex:CloudModelTier` | `ex:CloudNode1` | `2.1.0` | legacy-version-string-migrated; predecessor relation unavailable unless explicitly stated in source |
| `ex:ModelEdge1` | `ex:EdgeModelTier` | `ex:EdgeNode1` | `1.2.0` | legacy-version-string-migrated; predecessor relation unavailable unless explicitly stated in source |
| `ex:ModelFog1` | `ex:FogModelTier` | `ex:FogNode1` | `1.8.0` | legacy-version-string-migrated; predecessor relation unavailable unless explicitly stated in source |
| `ex:ModelLocal1` | `ex:LocalModelTier` | `ex:MobileA` | `0.9.0` | legacy-version-string-migrated; predecessor relation unavailable unless explicitly stated in source |
| `ex:ModelLocalB` | `ex:LocalModelTier` | `ex:RingB` | `0.8.0` | legacy-version-string-migrated; predecessor relation unavailable unless explicitly stated in source |
| `ex:ModelLocalD` | `ex:LocalModelTier` | `ex:InternalEdgeFacility` | `migrated-local-v3` | legacy-version-string-migrated; predecessor relation unavailable unless explicitly stated in source |
| `ex:ModelLocal_C` | `ex:LocalModelTier` | `ex:MobileC` | `1.0.0` | legacy-version-string-migrated; predecessor relation unavailable unless explicitly stated in source |

#### Consentimiento, contratos y autorización efectiva

| Usuario | ConsentRecord | Rango declarado | Contrato | Resultado/rango efectivo por evaluación |
|---|---|---|---|---|
| `ex:UserA` | `ex:ConsentRecord_UserA_Global` | `ex:RangeGlobalAgg` | `ex:Contract_UserA_Global` | `Eval_S1`→`AuthorizationGranted/RangeGlobalAgg`; `Eval_S2`→`AuthorizationGranted/RangeGlobalAgg`; `Eval_S6`→`AuthorizationGranted/RangeGlobalAgg`; `Eval_S3`→`AuthorizationGranted/RangeGlobalAgg`; `Eval_S4`→`AuthorizationGranted/RangeGlobalAgg` |
| `ex:UserB` | `ex:ConsentRecord_UserB_Local` | `ex:RangeLocalOnly` | `ex:Contract_UserB_LocalOnly` | `Eval_S5`→`AuthorizationGranted/RangeLocalOnly` |
| `ex:UserC` | `ex:ConsentRecord_UserC_Community` | `ex:RangeCommunityAgg` | `ex:Contract_UserC_Community` | `Eval_S7`→`AuthorizationGranted/RangeCommunityAgg` |
| `ex:UserD` | `ex:ConsentRecord_UserD_Restricted` | `ex:RangeCommunityAgg` | `ex:Contract_UserD_RestrictedFacility` | `Eval_S8`→`AuthorizationGranted/RangeLocalOnly` |

#### Evaluaciones y acciones de S1–S8

| Evaluación | Método | Síntoma | Tier seleccionado | Acción resultante |
|---|---|---|---|---|
| `ex:Eval_S1` | `ex:WeightedMulticriteriaMethod` | `ex:SymptomNone` | `ex:EdgeModelTier` | `ex:ModelSelection_Eval_S1` |
| `ex:Eval_S2` | `ex:WeightedMulticriteriaMethod` | `ex:SymptomSaturatedWorkload` | `ex:FogModelTier` | `ex:ModelSelection_Eval_S2` |
| `ex:Eval_S3` | `ex:WeightedMulticriteriaMethod` | `ex:SymptomSaturatedWorkload` | `ex:FogModelTier` | `ex:Migration_S3_Edge1_To_Fog1` |
| `ex:Eval_S4` | `ex:WeightedMulticriteriaMethod` | `ex:SymptomCommunicationLoss` | `ex:EdgeModelTier` | `ex:Degradation_S4_LocalFallback` |
| `ex:Eval_S5` | `ex:WeightedMulticriteriaMethod` | `ex:SymptomConsentLocalOnly` | `ex:LocalModelTier` | `ex:ModelSelection_Eval_S5` |
| `ex:Eval_S6` | `ex:WeightedMulticriteriaMethod` | `ex:SymptomNone` | `ex:CloudModelTier` | `ex:ModelSelection_Eval_S6` |
| `ex:Eval_S7` | `ex:WeightedMulticriteriaMethod` | `ex:SymptomRuralLowConnectivity` | `ex:LocalModelTier` | `ex:ModelSelection_Eval_S7` |
| `ex:Eval_S8` | `ex:WeightedMulticriteriaMethod` | `ex:SymptomRestrictedZoneBoundary` | `ex:LocalModelTier` | `ex:ModelSelection_S8_Local` |

#### Sesiones federadas y transferencias protegidas

| Recurso | Tipo | Payload/dato | Nodos/origen-destino | Privacidad/seguridad |
|---|---|---|---|---|
| `ex:FL_S6_DownloadToEdge` | `FederatedLearningSession` | `ex:ImprovedModelParametersPayload` | `ex:CloudNode1`, `ex:EdgeNode1` | — |
| `ex:FL_S6_EdgeToCloud` | `FederatedLearningSession` | `ex:ModelGradientsPayload` | `ex:CloudNode1`, `ex:EdgeNode1`, `ex:FogNode1` | `ex:DifferentialPrivacy`, `ex:GaussianNoiseMechanism`; ε=1.50 |
| `ex:Transfer_Gradient_S6_A` | `TransferEvent` | `ex:GradientUpdate_S6_A` | `ex:MobileA` → `ex:CloudNode1` | seguridad: `ex:DeploymentEncryptionBaseline_v3`; ID: `ex:Pseudonym_UserA_v3` |
| `ex:Transfer_PhysioDataA1` | `TransferEvent` | `ex:PhysioDataA1` | `ex:WatchA` → `ex:EdgeNode1` | seguridad: `ex:DeploymentEncryptionBaseline_v3`; ID: `ex:Pseudonym_UserA_v3` |
| `ex:Transfer_SleepDataA1` | `TransferEvent` | `ex:SleepDataA1` | `ex:WatchA` → `ex:EdgeNode1` | seguridad: `ex:DeploymentEncryptionBaseline_v3`; ID: `ex:Pseudonym_UserA_v3` |


## 11. Modelo de requisitos y trazabilidad

Los requisitos son entidades semánticas de primera clase para permitir trazabilidad reproducible hacia políticas y mecanismos.

```text
Requirement
 ├─ FunctionalRequirement      (RF-01 … RF-72)
 ├─ NonFunctionalRequirement   (RNF-01 … RNF-39)
 └─ ValidationRequirement      (RV-01 … RV-05)
      ├─ tracedToPolicy → Policy
      └─ tracedToMechanism → MechanismSpecification
```

| Tipo | Cantidad | Rango de IDs |
|---|---:|---|
| Funcionales | 72 | `RF-01–RF-72` |
| No funcionales | 39 | `RNF-01–RNF-39` |
| Validación/reproducibilidad | 5 | `RV-01–RV-05` |

La trazabilidad completa requisito → ontología → política → mecanismo → consulta se mantiene en `RN_RNF_revisado_requisitos_trazabilidad_v3.0.0.md`. La TTL contiene enlaces directos `tracedToPolicy` y `tracedToMechanism` cuando son aplicables; algunos requisitos puramente estructurales se documentan con cobertura indirecta en la matriz externa.

### 11.1 Matriz resumida de trazabilidad por módulo

| Módulo ontológico | Requisitos principales | Categorías/políticas | Consultas SPARQL principales |
|---|---|---|---|
| Dispositivos, nodos y contexto | `RF-01–RF-05` | `INT`, `OPS`, `NODE`, `ZONE` | `BASE-Q01–BASE-Q10`, `BASE-Q20`, `BASE-Q23`, `EXT-Q40–EXT-Q42` |
| Datos y transmisión | `RF-06–RF-10`, `RF-26–RF-30`, `RF-60–RF-61` | `DATA`, `CONS`, `ZONE` | `BASE-Q10`, `BASE-Q28`, `EXT-Q22–EXT-Q35` |
| Modelos y decisión | `RF-11–RF-15`, `RF-50–RF-55` | `MODEL`, `NODE`, `GOV` | `BASE-Q04`, `BASE-Q21`, `EXT-Q46–EXT-Q58` |
| Adaptación y continuidad | `RF-16–RF-20` | `ADAPT`, `NODE`, `OPS` | `BASE-Q12–BASE-Q14`, `BASE-Q35`, `EXT-Q59–EXT-Q65` |
| Aprendizaje federado | `RF-21–RF-25`, `RF-56–RF-59` | `FL`, `DATA`, `CONS` | `BASE-Q16`, `BASE-Q24`, `EXT-Q66–EXT-Q69` |
| Consentimiento y contratos | `RF-32–RF-38` | `CONS`, `GOV` | `BASE-Q15`, `BASE-Q20`, `BASE-Q25`, `EXT-Q11–EXT-Q21` |
| Gobernanza y zonas | `RF-39–RF-44` | `GOV`, `ZONE` | `EXT-Q03`, `EXT-Q06–EXT-Q10`, `EXT-Q36–EXT-Q39`, `EXT-Q78–EXT-Q79` |
| Trust y elegibilidad | `RF-45–RF-49` | `NODE`, `MODEL` | `BASE-Q07`, `BASE-Q19`, `EXT-Q40–EXT-Q45` |
| Delegación y auditoría | `RF-62–RF-68` | `AUD`, `GOV` | `BASE-Q35`, `EXT-Q63–EXT-Q74`, `EXT-Q80` |
| Validación y reproducibilidad | `RF-69–RF-72`, `RV-01–RV-05`, RNF asociados | `VAL`, `INT`, `OPS` | `EXT-Q01–EXT-Q10`, `EXT-Q75–EXT-Q80` |

La matriz individual y los criterios de aceptación se mantienen en el documento de requisitos; esta tabla resume únicamente los módulos de la ontología.

## 12. Modelo de políticas, mecanismos y conflictos

### 12.1 Políticas como recursos semánticos

Cada `Policy` conserva ID, título, statement normativo, tipo, categoría, versión, requisitos relacionados y mecanismos recomendados. Una política debe tener exactamente un `PolicyType`.

| Tipo | Nº de políticas |
|---|---:|
| Abstención | 9 |
| Obligación | 50 |
| Prohibición | 20 |

### 12.2 Categorías de políticas

| Código | Categoría | Orden | Nº políticas | IDs |
|---|---|---:|---:|---|
| `INT` | Interoperability and semantic extensibility | 0 | 2 | `P-INT-01`, `P-INT-02` |
| `GOV` | Governance, precedence and lifecycle | 1 | 5 | `P-GOV-01`, `P-GOV-02`, `P-GOV-03`, `P-GOV-04`, `P-GOV-05` |
| `CONS` | Consent and semantic contracts | 2 | 6 | `P-CONS-01`, `P-CONS-02`, `P-CONS-03`, `P-CONS-04`, `P-CONS-05`, `P-CONS-06` |
| `DATA` | Data, privacy, identity and transmission | 2 | 10 | `P-DATA-01`, `P-DATA-02`, `P-DATA-03`, `P-DATA-04`, `P-DATA-05`, `P-DATA-06`, `P-DATA-07`, `P-DATA-08`, `P-DATA-09`, `P-DATA-10` |
| `ZONE` | Zones and georestriction | 2 | 4 | `P-ZONE-01`, `P-ZONE-02`, `P-ZONE-03`, `P-ZONE-04` |
| `NODE` | Nodes and dynamic trust | 3 | 6 | `P-NODE-01`, `P-NODE-02`, `P-NODE-03`, `P-NODE-04`, `P-NODE-05`, `P-NODE-06` |
| `OPS` | Operations, scalability and QoS | 3 | 6 | `P-OPS-01`, `P-OPS-02`, `P-OPS-03`, `P-OPS-04`, `P-OPS-05`, `P-OPS-06` |
| `MODEL` | Model selection and AHP | 4 | 9 | `P-MODEL-01`, `P-MODEL-02`, `P-MODEL-03`, `P-MODEL-04`, `P-MODEL-05`, `P-MODEL-06`, `P-MODEL-07`, `P-MODEL-08`, `P-MODEL-09` |
| `ADAPT` | Migration, offloading, degradation and continuity | 5 | 8 | `P-ADAPT-01`, `P-ADAPT-02`, `P-ADAPT-03`, `P-ADAPT-04`, `P-ADAPT-05`, `P-ADAPT-06`, `P-ADAPT-07`, `P-ADAPT-08` |
| `FL` | Federated learning and model lifecycle | 5 | 8 | `P-FL-01`, `P-FL-02`, `P-FL-03`, `P-FL-04`, `P-FL-05`, `P-FL-06`, `P-FL-07`, `P-FL-08` |
| `AUD` | Temporal delegation, MAPE-K and audit | 6 | 7 | `P-AUD-01`, `P-AUD-02`, `P-AUD-03`, `P-AUD-04`, `P-AUD-05`, `P-AUD-06`, `P-AUD-07` |
| `VAL` | Validation, reproducibility and maintainability | 7 | 8 | `P-VAL-01`, `P-VAL-02`, `P-VAL-03`, `P-VAL-04`, `P-VAL-05`, `P-VAL-06`, `P-VAL-07`, `P-VAL-08` |

### 12.3 Registro completo de políticas

| ID | Título | Categoría | Tipo | Requisitos | Mecanismos | Consultas v3 |
|---|---|---|---|---|---|---|
| `P-ADAPT-01` | Decisión de migración multicondición | `ADAPT` | Obligación | `RF-16`, `RF-17`, `RF-18`, `RNF-03` | `M-ADAPT-01`, `M-NODE-02` | `BASE-Q12` |
| `P-ADAPT-02` | Degradación segura ante pérdida de comunicación o falta de destino | `ADAPT` | Obligación | `RF-07`, `RF-17`, `RNF-12` | `M-ADAPT-02`, `M-BUFFER-01` | `BASE-Q14`, `EXT-Q62` |
| `P-ADAPT-03` | Degradación por sobrecarga | `ADAPT` | Obligación | `RF-17`, `RF-20`, `RNF-03` | `M-ADAPT-01`, `M-ADAPT-02`, `M-OPS-02` | `EXT-Q62` |
| `P-ADAPT-04` | Criterios de destino y coste de migración | `ADAPT` | Abstención | `RF-16`, `RF-17`, `RNF-02` | `M-ADAPT-01`, `M-AUD-01`, `M-NODE-02` | `EXT-Q45` |
| `P-ADAPT-05` | Separación de migración, delegación y aprendizaje federado | `ADAPT` | Prohibición | `RF-16`, `RF-22`, `RF-25`, `RF-62` | `M-ADAPT-03`, `M-FL-01` | `BASE-Q13`, `EXT-Q60`, `EXT-Q61` |
| `P-ADAPT-06` | Registro de degradación y acción ejecutada | `ADAPT` | Obligación | `RF-20`, `RF-44`, `RF-66` | `M-ADAPT-02`, `M-AUD-01` | `BASE-Q13`, `BASE-Q22`, `BASE-Q27`, `EXT-Q59`, `EXT-Q62` |
| `P-ADAPT-07` | Delegación a destino elegible de mayor confianza | `ADAPT` | Obligación | `RF-48`, `RF-62`, `RNF-14` | `M-DELEG-01`, `M-TRUST-02` | `EXT-Q45` |
| `P-ADAPT-08` | Continuidad e idempotencia de recuperación | `ADAPT` | Prohibición | `RF-19`, `RF-26`, `RNF-02`, `RNF-13` | `M-DELEG-02`, `M-REPL-01`, `M-TX-02` | `BASE-Q10`, `EXT-Q33`, `EXT-Q34` |
| `P-AUD-01` | Delegación como evento semántico | `AUD` | Obligación | `RF-62` | `M-DELEG-01` | `BASE-Q14`, `EXT-Q63` |
| `P-AUD-02` | Contenido temporal de la delegación | `AUD` | Obligación | `RF-63`, `RNF-36` | `M-DELEG-01`, `M-TIME-01` | `EXT-Q63`, `EXT-Q64`, `EXT-Q73` |
| `P-AUD-03` | Cierre efectivo de delegaciones | `AUD` | Obligación | `RF-64`, `RNF-36` | `M-DELEG-02` | `EXT-Q63` |
| `P-AUD-04` | Límite de cascada de delegación | `AUD` | Prohibición | `RNF-14` | `M-DELEG-03` | `EXT-Q65` |
| `P-AUD-05` | Coherencia síntoma–política–acción | `AUD` | Obligación | `RF-65`, `RF-66`, `RF-67` | `M-AUD-02` | `BASE-Q14`, `BASE-Q35`, `EXT-Q72` |
| `P-AUD-06` | Ticket completo de EvaluationState | `AUD` | Obligación | `RF-51`, `RF-54`, `RF-66`, `RNF-28`, `RNF-29` | `M-AUD-01` | `BASE-Q21`, `EXT-Q20`, `EXT-Q46`, `EXT-Q47`, `EXT-Q59`, `EXT-Q71` |
| `P-AUD-07` | Reconstrucción causal y temporal de decisiones | `AUD` | Obligación | `RF-67`, `RNF-30`, `RNF-32`, `RNF-33` | `M-AUD-03`, `M-TIME-01` | `BASE-Q35`, `EXT-Q70` |
| `P-CONS-01` | Consentimiento por rangos y revocación | `CONS` | Obligación | `RF-32` | `M-CONS-01` | `BASE-Q01`, `BASE-Q15`, `BASE-Q31`, `EXT-Q11`, `EXT-Q13`, `EXT-Q16` |
| `P-CONS-02` | Contrato efectivo único por usuario y propósito | `CONS` | Prohibición | `RF-33`, `RNF-36` | `M-CONS-01`, `M-TIME-01` | `BASE-Q20`, `EXT-Q12`, `EXT-Q14`, `EXT-Q15` |
| `P-CONS-03` | Contenido mínimo del contrato | `CONS` | Obligación | `RF-34`, `RF-41` | `M-CONS-01`, `M-GOV-02` | `BASE-Q20`, `EXT-Q12`, `EXT-Q14` |
| `P-CONS-04` | Autorización efectiva e inconsistencias | `CONS` | Prohibición | `RF-35`, `RF-36`, `RNF-22` | `M-CONS-02`, `M-GOV-03` | `BASE-Q15`, `BASE-Q25`, `BASE-Q28`, `EXT-Q11`, `EXT-Q16`, `EXT-Q17`, `EXT-Q18`, `EXT-Q19`, `EXT-Q20`, `EXT-Q39`, `EXT-Q56` |
| `P-CONS-05` | Declaración del rango mínimo requerido | `CONS` | Obligación | `RF-37` | `M-CONS-03` | `BASE-Q06`, `EXT-Q21` |
| `P-CONS-06` | Recepción descendente sin ampliación de consentimiento | `CONS` | Abstención | `RF-23`, `RF-38` | `M-CONS-02`, `M-FL-02` | `BASE-Q15`, `EXT-Q66` |
| `P-DATA-01` | Confinamiento de observaciones fisiológicas crudas | `DATA` | Prohibición | `RF-10`, `RF-60`, `RNF-17` | `M-DATA-01`, `M-TX-01` | `BASE-Q18`, `EXT-Q22` |
| `P-DATA-02` | Pseudonimización de identificadores externos | `DATA` | Prohibición | `RF-61`, `RNF-17`, `RNF-19` | `M-ID-01`, `M-TX-01` | `BASE-Q01`, `EXT-Q23`, `EXT-Q26`, `EXT-Q27`, `EXT-Q28` |
| `P-DATA-03` | Cifrado de información sensible | `DATA` | Obligación | `RNF-15`, `RNF-39` | `M-SEC-01`, `M-VAL-04` | `EXT-Q23`, `EXT-Q29`, `EXT-Q30`, `EXT-Q32` |
| `P-DATA-04` | Puerta de transmisión por tipo de dato | `DATA` | Abstención | `RF-04`, `RF-09`, `RF-27` | `M-DATA-02`, `M-TX-01` | `BASE-Q10`, `BASE-Q28` |
| `P-DATA-05` | Retención en la capa más alta autorizada | `DATA` | Obligación | `RF-08`, `RF-26`, `RNF-12` | `M-BUFFER-01`, `M-CONS-02`, `M-ZONE-01` | `EXT-Q31`, `EXT-Q32` |
| `P-DATA-06` | Gestión energética de procesamiento y transmisión | `DATA` | Obligación | `RF-07`, `RF-27`, `RNF-06` | `M-ADAPT-02`, `M-BUFFER-01`, `M-DEVICE-01` | `BASE-Q10` |
| `P-DATA-07` | Ventana segura de transmisión y reconexión | `DATA` | Abstención | `RF-26`, `RF-27`, `RNF-12`, `RNF-13` | `M-CONS-02`, `M-NODE-02`, `M-TX-02` | `BASE-Q10`, `BASE-Q17`, `EXT-Q31`, `EXT-Q38` |
| `P-DATA-08` | Redundancia, replicación e idempotencia | `DATA` | Prohibición | `RF-19`, `RF-28`, `RNF-13` | `M-REPL-01`, `M-TX-01` | `EXT-Q33`, `EXT-Q34` |
| `P-DATA-09` | Priorización por criticidad | `DATA` | Obligación | `RF-27`, `RF-28` | `M-BUFFER-01`, `M-TX-03` | `EXT-Q35` |
| `P-DATA-10` | Contexto mínimo de datos procesados | `DATA` | Obligación | `RF-09`, `RF-30`, `RNF-27` | `M-DATA-02`, `M-TIME-01` | `EXT-Q23`, `EXT-Q24`, `EXT-Q25` |
| `P-FL-01` | Elegibilidad de sesiones federadas | `FL` | Abstención | `RF-21`, `RF-22`, `RF-25`, `RNF-12` | `M-FL-01`, `M-NODE-02` | `BASE-Q16`, `BASE-Q30`, `EXT-Q66` |
| `P-FL-02` | Autorización del flujo federado ascendente | `FL` | Prohibición | `RF-21`, `RF-35`, `RF-42` | `M-CONS-02`, `M-FL-01`, `M-ZONE-01` | `BASE-Q24`, `BASE-Q25`, `EXT-Q67` |
| `P-FL-03` | Protección obligatoria de gradientes | `FL` | Obligación | `RF-56`, `RF-57`, `RNF-16`, `RNF-17` | `M-FL-03`, `M-ID-01` | `BASE-Q16`, `EXT-Q67`, `EXT-Q68` |
| `P-FL-04` | Contabilidad del presupuesto epsilon | `FL` | Obligación | `RF-59`, `RNF-18` | `M-AUD-01`, `M-FL-04` | `BASE-Q24`, `EXT-Q69` |
| `P-FL-05` | Mecanismo de privacidad explícito | `FL` | Obligación | `RF-58`, `RNF-19` | `M-FL-03`, `M-ID-01` | `BASE-Q16`, `EXT-Q68` |
| `P-FL-06` | Flujo descendente de modelos mejorados | `FL` | Prohibición | `RF-23`, `RF-38`, `RNF-17` | `M-CONS-02`, `M-FL-02`, `M-ZONE-01` | `EXT-Q66` |
| `P-FL-07` | Metadatos mínimos de sesión HFL | `FL` | Obligación | `RF-25`, `RNF-16` | `M-AUD-01`, `M-FL-01`, `M-FL-02` | `BASE-Q16`, `BASE-Q24`, `EXT-Q66` |
| `P-FL-08` | Versionado y rollback de modelos | `FL` | Obligación | `RF-24`, `RNF-38`, `RNF-39` | `M-MODEL-05`, `M-VAL-04` | `BASE-Q04`, `BASE-Q22`, `EXT-Q57`, `EXT-Q58` |
| `P-GOV-01` | Tipado único de políticas | `GOV` | Obligación | `RF-39`, `RF-40` | `M-GOV-01` | `EXT-Q03`, `EXT-Q06`, `EXT-Q10` |
| `P-GOV-02` | Vinculación explícita de gobernanza | `GOV` | Obligación | `RF-41`, `RF-44`, `RNF-28`, `RNF-30` | `M-AUD-01`, `M-GOV-02` | `EXT-Q08`, `EXT-Q70`, `EXT-Q72` |
| `P-GOV-03` | Precedencia de la restricción más estricta | `GOV` | Prohibición | `RF-35`, `RF-42`, `RF-43`, `RNF-22` | `M-CONS-02`, `M-GOV-03`, `M-ZONE-01` | `EXT-Q07`, `EXT-Q17`, `EXT-Q19`, `EXT-Q37`, `EXT-Q78`, `EXT-Q79` |
| `P-GOV-04` | Determinismo y versionado de políticas | `GOV` | Obligación | `RNF-20`, `RNF-22`, `RNF-38`, `RNF-39`, `RV-04` | `M-GOV-02`, `M-GOV-04`, `M-VAL-04` | `EXT-Q03`, `EXT-Q10` |
| `P-GOV-05` | Ciclo temporal de estados | `GOV` | Obligación | `RNF-35`, `RNF-36`, `RNF-37` | `M-TIME-01` | `BASE-Q09`, `EXT-Q73`, `EXT-Q74` |
| `P-INT-01` | Uso de estándares semánticos abiertos | `INT` | Obligación | `RNF-24`, `RNF-25`, `RNF-26` | `M-INT-01`, `M-VAL-01` | `BASE-Q05` |
| `P-INT-02` | Extensibilidad sin ruptura del núcleo conceptual | `INT` | Prohibición | `RNF-10`, `RNF-23`, `RNF-38` | `M-INT-02`, `M-VAL-05` | `BASE-Q03` |
| `P-MODEL-01` | Selección por adecuación, no por tier máximo | `MODEL` | Obligación | `RF-15`, `RF-52`, `RF-53` | `M-MODEL-01`, `M-NODE-02` | `BASE-Q04`, `BASE-Q32`, `EXT-Q46` |
| `P-MODEL-02` | Criterios y normalización AHP | `MODEL` | Obligación | `RF-50`, `RF-55`, `RNF-34` | `M-MODEL-02` | `EXT-Q48` |
| `P-MODEL-03` | Confianza como criterio externo | `MODEL` | Prohibición | `RF-46`, `RF-50`, `RF-55`, `RNF-05`, `RNF-33` | `M-MODEL-02`, `M-TRUST-02` | `EXT-Q42`, `EXT-Q44`, `EXT-Q48` |
| `P-MODEL-04` | Consistencia del método AHP | `MODEL` | Prohibición | `RF-55`, `RNF-34` | `M-MODEL-03` | `EXT-Q49`, `EXT-Q50` |
| `P-MODEL-05` | Puntuación por alternativa y explicación | `MODEL` | Obligación | `RF-51`, `RF-54`, `RNF-29`, `RNF-33` | `M-AUD-01`, `M-MODEL-01` | `BASE-Q21`, `EXT-Q46`, `EXT-Q51`, `EXT-Q52`, `EXT-Q53` |
| `P-MODEL-06` | Prioridad de privacidad | `MODEL` | Obligación | `RF-35`, `RF-42`, `RF-52` | `M-CONS-02`, `M-MODEL-01`, `M-ZONE-01` | `BASE-Q15` |
| `P-MODEL-07` | Selección de Cloud condicionada | `MODEL` | Abstención | `RF-53`, `RF-56`, `RF-59` | `M-FL-03`, `M-MODEL-01` | `EXT-Q56` |
| `P-MODEL-08` | Separación entre calidad observada y pesos de decisión | `MODEL` | Obligación | `RF-14`, `RNF-27` | `M-AUD-01`, `M-METRIC-01` | `EXT-Q54`, `EXT-Q55` |
| `P-MODEL-09` | Reevaluación de selección vigente | `MODEL` | Obligación | `RF-15`, `RF-17`, `RNF-21` | `M-CTX-01`, `M-MODEL-04` | `BASE-Q21`, `EXT-Q46`, `EXT-Q59`, `EXT-Q76` |
| `P-NODE-01` | Estados operativos y elegibilidad | `NODE` | Prohibición | `RF-05`, `RF-17`, `RNF-12` | `M-NODE-01`, `M-NODE-02` | `BASE-Q07`, `BASE-Q08`, `BASE-Q26`, `EXT-Q41` |
| `P-NODE-02` | Filtros duros de candidatos | `NODE` | Prohibición | `RF-15`, `RF-18`, `RF-47` | `M-CONS-02`, `M-NODE-02`, `M-ZONE-01` | `BASE-Q08`, `BASE-Q12`, `BASE-Q19`, `BASE-Q23`, `EXT-Q41`, `EXT-Q42` |
| `P-NODE-03` | Trust score reproducible | `NODE` | Obligación | `RF-45`, `RF-49`, `RNF-32` | `M-TRUST-01`, `M-VAL-04` | `BASE-Q07`, `EXT-Q40`, `EXT-Q43` |
| `P-NODE-04` | Actualización del trust y doble contabilización | `NODE` | Prohibición | `RF-49`, `RNF-32`, `RNF-33` | `M-AUD-01`, `M-TRUST-01` | `EXT-Q40` |
| `P-NODE-05` | Ordenación por confianza entre candidatos elegibles | `NODE` | Obligación | `RF-46`, `RF-47`, `RF-48` | `M-NODE-02`, `M-TRUST-02` | `BASE-Q19`, `EXT-Q42`, `EXT-Q44` |
| `P-NODE-06` | Ausencia de alternativas confiables | `NODE` | Abstención | `RF-47`, `RF-48`, `RF-53` | `M-ADAPT-02`, `M-AUD-01`, `M-NODE-02` | `BASE-Q19`, `EXT-Q42`, `EXT-Q45`, `EXT-Q56` |
| `P-OPS-01` | Perfil de aceptación versionado | `OPS` | Obligación | `RNF-01`, `RNF-02`, `RNF-04`, `RNF-05`, `RNF-06`, `RNF-08`, `RNF-09`, `RNF-14`, `RNF-21`, `RNF-39` | `M-OPS-01`, `M-VAL-04` | `EXT-Q65`, `EXT-Q76` |
| `P-OPS-02` | Escalado horizontal compatible con Fog y Cloud | `OPS` | Obligación | `RF-17`, `RNF-07` | `M-OPS-02` | `BASE-Q02`, `BASE-Q29` |
| `P-OPS-03` | Incorporación dinámica de nodos | `OPS` | Obligación | `RNF-09`, `RNF-10` | `M-NODE-01`, `M-OPS-03` | `BASE-Q02` |
| `P-OPS-04` | Continuidad de funciones críticas | `OPS` | Obligación | `RNF-12`, `RNF-13` | `M-ADAPT-02`, `M-BUFFER-01` | `BASE-Q08`, `EXT-Q31`, `EXT-Q32`, `EXT-Q33`, `EXT-Q34` |
| `P-OPS-05` | Instrumentación mínima reproducible | `OPS` | Obligación | `RF-29`, `RF-30`, `RNF-27` | `M-METRIC-01`, `M-TIME-01` | `BASE-Q07`, `BASE-Q09`, `BASE-Q33`, `EXT-Q54` |
| `P-OPS-06` | Restauración y vaciado seguro de buffers | `OPS` | Abstención | `RF-08`, `RF-15`, `RF-26`, `RNF-12` | `M-BUFFER-01`, `M-MODEL-04`, `M-TX-02` | `BASE-Q10`, `BASE-Q17`, `EXT-Q31`, `EXT-Q38`, `EXT-Q46` |
| `P-VAL-01` | Endpoint y entorno de referencia | `VAL` | Obligación | `RF-69`, `RNF-24`, `RNF-26`, `RV-03` | `M-VAL-01` | `EXT-Q01` |
| `P-VAL-02` | Clasificación de consultas de auditoría | `VAL` | Obligación | `RF-70`, `RF-71`, `RNF-31`, `RV-01` | `M-VAL-02` | `EXT-Q01`, `EXT-Q75`, `EXT-Q77`, `EXT-Q80` |
| `P-VAL-03` | Precondiciones para interpretar cero filas | `VAL` | Prohibición | `RF-71`, `RV-02` | `M-VAL-03` | `EXT-Q75`, `EXT-Q76`, `EXT-Q77` |
| `P-VAL-04` | Versionado inequívoco de artefactos | `VAL` | Obligación | `RF-68`, `RNF-39`, `RV-01`, `RV-03` | `M-GOV-04`, `M-VAL-04` | `EXT-Q01`, `EXT-Q77` |
| `P-VAL-05` | Compatibilidad de línea base y cambios mayores | `VAL` | Prohibición | `RNF-11`, `RNF-38` | `M-VAL-04`, `M-VAL-05` | `EXT-Q01`, `EXT-Q02`, `EXT-Q05`, `EXT-Q77`, `EXT-Q80` |
| `P-VAL-06` | Trazabilidad individual de requisitos | `VAL` | Obligación | `RV-04`, `RV-05` | `M-VAL-05` | `EXT-Q02`, `EXT-Q04`, `EXT-Q08`, `EXT-Q09` |
| `P-VAL-07` | Escenarios versionados y reproducibles | `VAL` | Obligación | `RF-31`, `RF-72`, `RV-03` | `M-VAL-04`, `M-VAL-06` | `BASE-Q11`, `EXT-Q05`, `EXT-Q77` |
| `P-VAL-08` | Cobertura global de cumplimiento | `VAL` | Obligación | `RF-68`, `RNF-39`, `RV-05` | `M-VAL-04`, `M-VAL-07` | `EXT-Q80` |
| `P-ZONE-01` | Zona restringida: confinamiento local | `ZONE` | Prohibición | `RF-42`, `RF-43`, `RF-53`, `RNF-22` | `M-CONS-02`, `M-ZONE-01` | `BASE-Q18`, `BASE-Q34`, `EXT-Q22`, `EXT-Q36`, `EXT-Q37`, `EXT-Q56` |
| `P-ZONE-02` | Zona rural: retención por defecto | `ZONE` | Obligación | `RF-08`, `RF-26`, `RF-42` | `M-BUFFER-01`, `M-TX-02`, `M-ZONE-01` | `BASE-Q17`, `EXT-Q38` |
| `P-ZONE-03` | Zona urbana: agregación condicionada | `ZONE` | Abstención | `RF-15`, `RF-36`, `RF-42` | `M-CONS-02`, `M-NODE-02`, `M-ZONE-01` | `EXT-Q39` |
| `P-ZONE-04` | Cambio de zona y reevaluación | `ZONE` | Obligación | `RF-03`, `RF-15`, `RF-17`, `RNF-21` | `M-CTX-01`, `M-MODEL-04` | `BASE-Q09`, `BASE-Q23`, `EXT-Q46`, `EXT-Q59` |

### 12.4 Mecanismos

La ontología contiene **55 `MechanismSpecification`**. Los mecanismos describen cómo se materializan las políticas; no conceden autorización por sí mismos.

| ID | Descripción | Políticas soportadas |
|---|---|---|
| `M-ADAPT-01` | Comparar continuidad, coste, latencia, energía y destinos elegibles antes de activar migración u offloading. | `P-ADAPT-01`, `P-ADAPT-03`, `P-ADAPT-04` |
| `M-ADAPT-02` | Reducir procesamiento de forma controlada, registrar causa y conservar funciones críticas locales cuando no exista una alternativa externa válida. | `P-ADAPT-02`, `P-ADAPT-03`, `P-ADAPT-06`, `P-DATA-06` |
| `M-ADAPT-03` | Ejecutar la migración como una acción independiente de delegación y de aprendizaje federado, conservando referencia a la evaluación que la autorizó. | `P-ADAPT-05` |
| `M-AUD-01` | Persistir en EvaluationState las entradas, alternativas, puntuaciones, confianza, políticas, decisión, tiempo y acción ejecutada. | `P-ADAPT-04`, `P-ADAPT-06`, `P-AUD-06`, `P-FL-04`, `P-GOV-02`, `P-MODEL-05`, `P-MODEL-08` |
| `M-AUD-02` | Comprobar que la política y la acción elegidas sean coherentes con el síntoma o condición detectada. | `P-AUD-05` |
| `M-AUD-03` | Recorrer relaciones causales y temporales desde usuario/contrato hasta la acción final utilizando los valores vigentes en el instante evaluado. | `P-AUD-07` |
| `M-BUFFER-01` | Seleccionar la capa de almacenamiento temporal más alta permitida y mantener integridad hasta sincronización o descarte autorizado. | `P-DATA-05`, `P-OPS-04`, `P-ZONE-02` |
| `M-CONS-01` | Determinar consentimiento activo, contrato efectivo por propósito, vigencia, categorías de datos y rango autorizado. | `P-CONS-01`, `P-CONS-02`, `P-CONS-03` |
| `M-CONS-02` | Calcular la autorización efectiva como intersección de consentimiento activo, contrato, zona y demás restricciones duras. | `P-CONS-04`, `P-CONS-06`, `P-DATA-05`, `P-ZONE-03` |
| `M-CONS-03` | Comparar el rango mínimo requerido por recurso/acción con la autorización efectiva antes de habilitarlo. | `P-CONS-05` |
| `M-CTX-01` | Detectar movilidad, cambio de zona, conectividad, carga, batería y otras variaciones capaces de invalidar una decisión. | `P-MODEL-09`, `P-ZONE-04` |
| `M-DATA-01` | Clasificar el dato antes de cualquier transferencia y bloquear observaciones fisiológicas crudas fuera del ámbito local. | `P-DATA-01` |
| `M-DATA-02` | Adjuntar o relacionar el contexto operativo mínimo necesario para interpretar cada dato procesado. | `P-DATA-04`, `P-DATA-10` |
| `M-DELEG-01` | Crear el evento de delegación con origen, destino, causa, validFrom, recuperación y expiración planificada cuando exista, dejando validTo vacío mientras esté activo. | `P-ADAPT-07`, `P-AUD-01`, `P-AUD-02` |
| `M-DELEG-02` | Cerrar la delegación al cumplirse recuperación o expiración y registrar validTo como cierre efectivo. | `P-ADAPT-08`, `P-AUD-03` |
| `M-DELEG-03` | Comprobar la profundidad acumulada de la cadena antes de crear una nueva delegación. | `P-AUD-04` |
| `M-DEVICE-01` | Leer batería, conectividad, sensores y disponibilidad de datos para disparar reglas energéticas y de transmisión. | `P-DATA-06` |
| `M-FL-01` | Crear una sesión federada únicamente tras validar participantes, autorización, zona, privacidad y tipo de actualización. | `P-FL-01`, `P-FL-02`, `P-FL-07` |
| `M-FL-02` | Distribuir modelos genéricos mejorados verificando que no contienen información individualizada y que el flujo cumple las políticas activas. | `P-CONS-06`, `P-FL-06` |
| `M-FL-03` | Aplicar ruido y registrar presupuesto, nivel de ruido y mecanismo de privacidad antes de liberar gradientes protegidos. | `P-FL-03`, `P-FL-05`, `P-MODEL-07` |
| `M-FL-04` | Acumular y validar el consumo del presupuesto epsilon por propósito, contrato, sesión y política. | `P-FL-04` |
| `M-GOV-01` | Validar al crear o cargar una política que tenga exactamente un tipo formal y que dicho tipo sea uno de los permitidos. | `P-GOV-01` |
| `M-GOV-02` | Resolver las políticas vinculadas a usuario, contrato, zona, nodo, servicio, sesión o evaluación y conservar su versión. | `P-GOV-02`, `P-GOV-04` |
| `M-GOV-03` | Combinar las restricciones duras aplicables y obtener la intersección más restrictiva antes de calcular cualquier optimización. | `P-CONS-04`, `P-GOV-03` |
| `M-GOV-04` | Persistir la versión del conjunto de políticas usada por cada evaluación y campaña de validación. | `P-GOV-04`, `P-VAL-04` |
| `M-ID-01` | Sustituir identificadores personales directos por identificadores pseudónimos o anónimos antes de autorizar un flujo externo. | `P-DATA-02`, `P-FL-03`, `P-FL-05` |
| `M-INT-01` | Comprobar que los artefactos utilizan los estándares declarados y registrar las alineaciones o justificaciones de conceptos propios frente a vocabularios existentes. | `P-INT-01` |
| `M-INT-02` | Comprobar que la incorporación de nuevas instancias o especializaciones no altera las abstracciones centrales ni rompe los escenarios de referencia salvo cambio mayor explícito. | `P-INT-02` |
| `M-METRIC-01` | Registrar métricas de modelo, sistema y usuario con referencias temporales/contextuales comunes. | `P-MODEL-08`, `P-OPS-05` |
| `M-MODEL-01` | Calcular la puntuación de cada alternativa elegible y seleccionar la mejor según la política activa. | `P-MODEL-01`, `P-MODEL-05`, `P-MODEL-06`, `P-MODEL-07` |
| `M-MODEL-02` | Validar que los pesos de latencia, privacidad y calidad estén normalizados y que trust no se mezcle en ellos. | `P-MODEL-02`, `P-MODEL-03` |
| `M-MODEL-03` | Calcular y registrar la métrica/ratio de consistencia y compararla con el umbral configurado; si el método no es AHP, etiquetarlo correctamente. | `P-MODEL-04` |
| `M-MODEL-04` | Invalidar y recalcular la selección cuando cambien las condiciones que hacían válida la decisión anterior. | `P-MODEL-09`, `P-OPS-06`, `P-ZONE-04` |
| `M-MODEL-05` | Crear versiones de modelo identificables, registrar actualización y permitir volver a una versión válida anterior. | `P-FL-08` |
| `M-NODE-01` | Leer disponibilidad, carga, comunicación, capacidad residual, cola, estado operativo y trust de los nodos. | `P-NODE-01`, `P-OPS-03` |
| `M-NODE-02` | Excluir candidatos que incumplan estado operativo, capacidad, conectividad, autorización, zona o mínimos de confianza aplicables. | `P-NODE-01`, `P-NODE-02`, `P-NODE-06` |
| `M-OPS-01` | Cargar y congelar los umbrales configurables de una campaña de aceptación junto con su versión. | `P-OPS-01` |
| `M-OPS-02` | Aplicar escalado horizontal donde exista capacidad compatible y registrar degradación/migración cuando el escalado no sea posible o no esté autorizado. | `P-ADAPT-03`, `P-OPS-02` |
| `M-OPS-03` | Incorporar un nodo nuevo, validar sus capacidades y hacerlo elegible sin detener el sistema completo. | `P-OPS-03` |
| `M-REPL-01` | Identificar réplicas intencionadas, versionarlas, detectar duplicados accidentales y hacer idempotentes las reejecuciones de sincronización. | `P-ADAPT-08`, `P-DATA-08` |
| `M-SEC-01` | Aplicar y verificar la línea base de cifrado en tránsito y en reposo para información sensible y buffers autorizados. | `P-DATA-03` |
| `M-TIME-01` | Registrar validFrom; completar validTo únicamente al cierre efectivo y mantener separada cualquier expiración planificada. | `P-AUD-02`, `P-AUD-07`, `P-CONS-02`, `P-DATA-10` |
| `M-TRUST-01` | Actualizar el trust score a partir de la ventana histórica y regla versionada, conservando evidencias de los factores utilizados. | `P-NODE-03`, `P-NODE-04` |
| `M-TRUST-02` | Aplicar trust únicamente sobre candidatos elegibles y fuera de la normalización AHP. | `P-ADAPT-07`, `P-MODEL-03`, `P-NODE-05` |
| `M-TX-01` | Comprobar tipo de dato, preparación, identidad protegida, autorización, zona, destino y reglas de redundancia antes de cada envío. | `P-DATA-01`, `P-DATA-02`, `P-DATA-04`, `P-DATA-08` |
| `M-TX-02` | Mantener pendientes los flujos bloqueados y revalidar todas las condiciones antes de reanudarlos tras una reconexión. | `P-DATA-07`, `P-OPS-06` |
| `M-TX-03` | Ordenar datos pendientes por criticidad, restricciones y coste de transmisión sin permitir que datos secundarios desplacen a los críticos. | `P-DATA-09` |
| `M-VAL-01` | Cargar el dataset y ejecutar la batería sobre Fuseki como referencia, permitiendo comparar endpoints equivalentes. | `P-VAL-01` |
| `M-VAL-02` | Registrar para cada consulta su tipo, finalidad, precondiciones y criterio de interpretación. | `P-VAL-02` |
| `M-VAL-03` | Comprobar dataset, versión, cobertura y ejecución correcta antes de interpretar una consulta de incumplimiento vacía. | `P-VAL-03` |
| `M-VAL-04` | Persistir identificadores inequívocos de ontología, políticas, consultas, escenarios, dataset y perfil de aceptación utilizados. | `P-GOV-04`, `P-VAL-04`, `P-VAL-05`, `P-VAL-07` |
| `M-VAL-05` | Mantener la relación individual entre requisitos, políticas, mecanismos, soporte semántico, consultas y criterios de aceptación. | `P-VAL-05`, `P-VAL-06` |
| `M-VAL-06` | Cargar y ejecutar el conjunto versionado de escenarios S1–S17 con los artefactos de la campaña seleccionada. | `P-VAL-07` |
| `M-VAL-07` | Calcular cobertura por dominio, contar incumplimientos/advertencias y vincular cada resultado con las versiones de artefactos utilizadas en la campaña. | `P-VAL-08` |
| `M-ZONE-01` | Resolver la zona vigente y aplicar sus restricciones antes de autorizar almacenamiento, procesamiento o transferencia externa. | `P-ZONE-01`, `P-ZONE-02`, `P-ZONE-03` |

### 12.5 Taxonomía de relaciones/conflictos

| Código | Relación | Interpretación |
|---|---|---|
| `IND` | Independent / Disjoint | Sin intersección normativa relevante. |
| `CO` | Consistent Overlap | Solapamiento compatible; ambas reglas pueden cumplirse. |
| `SUB` | Subsumption / Specialization | Una política/categoría especializa a otra sin contradicción. |
| `RED` | Redundancy | Cobertura duplicada; anomalía de mantenibilidad. |
| `DEP` | Policy/Order Dependency | La aplicación depende del resultado/orden de otra política. |
| `GEN` | Generalization / Exception Conflict | Regla general y excepción específica con efectos diferentes. |
| `COR` | Correlation / Partial Conflict | Intersección parcial con efectos distintos. |
| `CON` | Contradiction | Efectos incompatibles en el mismo ámbito. |
| `SHD` | Shadowing / Override | Una política prioritaria hace inefectiva otra en el subámbito. |
| `IRR` | Irrelevance | Política inalcanzable/no aplicable en estados válidos. |

### 12.6 Estrategias de resolución

- `CONSTRAINT_BEFORE_OPT` — Constraint-before-optimization.
- `DEFER_REEVALUATE` — Defer-and-reevaluate.
- `DENY_OVERRIDES` — Deny-overrides / Most-restrictive.
- `EXPLICIT_REJECT` — Explicit conflict rejection.
- `MOST_SPECIFIC` — Most-specific-policy.
- `PRIORITY_ORDERED` — Priority-ordered.

### 12.7 Matriz predominante entre categorías

|  | GOV | CONS | DATA | ZONE | NODE | MODEL | ADAPT | FL | AUD | OPS | INT | VAL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **GOV** | — | `DEP` | `DEP` | `DEP` | `DEP` | `DEP` | `DEP` | `DEP` | `DEP` | `DEP` | `DEP` | `DEP` |
| **CONS** | `DEP` | — | `DEP` | `GEN` | `DEP` | `SHD` | `SHD` | `GEN` | `CO` | `DEP` | `CO` | `CO` |
| **DATA** | `DEP` | `DEP` | — | `SUB` | `DEP` | `SHD` | `DEP` | `GEN` | `CO` | `DEP` | `CO` | `CO` |
| **ZONE** | `DEP` | `GEN` | `SUB` | — | `SUB` | `SHD` | `SHD` | `SHD` | `CO` | `SUB` | `CO` | `CO` |
| **NODE** | `DEP` | `DEP` | `DEP` | `SUB` | — | `DEP` | `DEP` | `DEP` | `CO` | `DEP` | `CO` | `CO` |
| **MODEL** | `DEP` | `SHD` | `SHD` | `SHD` | `DEP` | — | `DEP` | `DEP` | `CO` | `DEP` | `CO` | `CO` |
| **ADAPT** | `DEP` | `SHD` | `DEP` | `SHD` | `DEP` | `DEP` | — | `IND` | `CO` | `DEP` | `CO` | `CO` |
| **FL** | `DEP` | `GEN` | `GEN` | `SHD` | `DEP` | `DEP` | `IND` | — | `CO` | `DEP` | `CO` | `CO` |
| **AUD** | `DEP` | `CO` | `CO` | `CO` | `CO` | `CO` | `CO` | `CO` | — | `CO` | `CO` | `DEP` |
| **OPS** | `DEP` | `DEP` | `DEP` | `SUB` | `DEP` | `DEP` | `DEP` | `DEP` | `CO` | — | `CO` | `CO` |
| **INT** | `DEP` | `CO` | `CO` | `CO` | `CO` | `CO` | `CO` | `CO` | `CO` | `CO` | — | `CO` |
| **VAL** | `DEP` | `CO` | `CO` | `CO` | `CO` | `CO` | `CO` | `CO` | `DEP` | `CO` | `CO` | — |

Orden normativo: `GOV → CONS/DATA/ZONE → NODE/OPS → MODEL → ADAPT/FL → AUD → VAL`, con `INT` transversal. Una optimización nunca puede ampliar un permiso restringido por consentimiento, dato, privacidad o zona.

## 13. Consentimiento, contratos y autorización efectiva

La v3 separa tres niveles que no deben confundirse:

```text
ConsentRecord (decisión del usuario)
     +
SemanticContract (acuerdo por propósito)
     +
Zona / políticas duras
     ↓
AuthorizationDecision
     ├─ hasAuthorizationOutcome
     ├─ hasEffectiveConsentRange
     └─ authorizationReason
```

`hasActiveConsentRange` se obtiene del consentimiento activo, no del contrato. Esto permite detectar divergencias reales entre ambos. La autorización efectiva debe ser la intersección más restrictiva y puede producir `AuthorizationGranted`, `AuthorizationBlocked`, `AuthorizationInconsistent` o `PendingRecalculation`.

Un `ConsentRecord` puede declarar sujeto, rango, propósito, categorías de datos y vigencia. Un `SemanticContract` debe identificar usuario, propósito, rango contractual, vigencia y políticas aplicables. La coexistencia de contratos efectivos para el mismo usuario+propósito+instante se considera una inconsistencia.

## 14. Datos, identidad, seguridad y transmisión

### 14.1 Clasificación de datos

La v3 distingue `DataCategory`, `DataCriticality` y `DataSensitivity`. `DataContext` conserva zona, propósito, `DeviceState`, `NodeState` y `ProcessingLevel` vigentes para interpretar el dato en el mismo contexto temporal.

### 14.2 Identidad

`Identifier` se especializa en `DirectIdentifier`, `PseudonymousIdentifier` y `AnonymousIdentifier`. Los flujos externos se modelan mediante `TransferEvent` y pueden registrar `usesIdentifier`; un identificador directo no debe acompañar datos parametrizados o gradientes fuera del ámbito local.

### 14.3 Seguridad

`SecurityMechanism` y `EncryptionMechanism` permiten representar una línea base criptográfica con `protectsInTransit`, `protectsAtRest` y `securityBaselineVersion`. La ontología representa `DeploymentEncryptionBaseline_v3` sin imponer algoritmos concretos no fijados por los requisitos.

### 14.4 Replicación y buffers

`ReplicationEvent`, `replicaOf`, `replicationVersion` e `idempotencyKey` distinguen una réplica controlada de un duplicado accidental. `BufferRecord` y los eventos de retención/sincronización permiten mantener información local hasta una ventana segura.

## 15. Confianza dinámica y selección de nodos

`hasTrustScore` expresa la confianza numérica; la evidencia reproducible se encapsula en `TrustAssessment`.

```text
NodeState → hasTrustAssessment → TrustAssessment
TrustAssessment
 ├─ trustRuleVersion
 ├─ trustWindowStart / trustWindowEnd
 ├─ hasTrustEvidence → TrustEvidence
 └─ hasTrustScore
```

La elegibilidad de un nodo se decide primero por restricciones duras: estado operativo, disponibilidad, comunicación, capacidad, consentimiento y zona. Solo después trust y métricas operativas ordenan candidatos válidos. La v3 evita tratar trust como sustituto de latencia/carga o contabilizar dos veces la misma señal sin justificación.

## 16. Decisión multicriterio y AHP

### 16.1 Métodos de decisión

- `AHPDecisionMethod`: exige comparaciones por pares, normalización y control de consistencia.
- `WeightedMulticriteriaMethod`: puntuación ponderada cuando no existe evidencia suficiente para afirmar que se ejecutó AHP estricto.

### 16.2 Separación de criterios

Los tres pesos normalizados son: `hasLatencyWeight`, `hasPrivacyWeight` y `hasModelQualityWeight`. **Trust no forma parte de la suma AHP**; `hasTrustWeight` permanece como criterio externo documentado en la evaluación.

```text
1. Resolver restricciones duras
2. Construir DecisionAlternative por tier
3. Marcar isEligible / eligibilityReason
4. Calcular hasAHPScore en cada alternativa elegible
5. Aplicar trust externo si la política lo exige
6. selectedAlternative → selectedModelTier
7. Persistir hasSelectionJustification y resultedInAction
```

Para AHP estricto, `EvaluationState` puede registrar `PairwiseComparison`, `hasConsistencyRatio` y `hasConsistencyThreshold`. Si falta esa evidencia, la evaluación debe etiquetarse como `WeightedMulticriteriaMethod`. Los `Eval_S1–Eval_S8` heredados siguen esta segunda opción porque la fuente v2.1 no contenía matrices por pares ni scores de todas las alternativas.

## 17. Adaptación, migración, delegación y continuidad

`AdaptationAction` es una superclase temporal para las acciones ejecutadas como consecuencia de una evaluación.

| Subclase | Uso |
|---|---|
| `ex:MigrationEvent` | Migration Event |
| `ex:OffloadingEvent` | Offloading Event |
| `ex:DegradationEvent` | Degradation Event |
| `ex:RetentionEvent` | Retention Event |
| `ex:SynchronizationEvent` | Synchronization Event |
| `ex:RollbackEvent` | Rollback Event |
| `ex:ModelSelectionAction` | Model Selection Action |
| `ex:ScalingEvent` | Scaling Event |
| `ex:DelegationEvent` | Delegation Event |

Toda acción puede vincularse con `authorizedByEvaluation`, `actionOriginNode`, `actionTargetNode`, `affectsModel`, `affectsService` y `partOfScenario`. Esto permite que `EvaluationState → resultedInAction` registre el resultado real y no solo la intención del planificador.

### 17.1 Separación entre migración, delegación y FL

La v3 elimina la implicación automática entre estas operaciones. S3 se representa como `MigrationEvent`; una `DelegationEvent` solo existe si el origen transfiere temporalmente responsabilidad; una `FederatedLearningSession` solo existe si realmente hay aprendizaje federado.

### 17.2 Delegación temporal

Una delegación registra origen, destino, causa/estado disparador, `validFrom`, `plannedExpiry`, `RecoveryCondition`, profundidad y `validTo` únicamente al cierre efectivo. `parentDelegation` soporta el control de cascadas frente a `D_delegation_max`.

## 18. Aprendizaje federado, privacidad diferencial y ciclo de vida de modelos

### 18.1 Sesiones y payloads

`FederatedLearningSession` utiliza `hasPayloadType` en lugar del antiguo `dataType` textual. Los payloads controlados son `ModelGradientsPayload`, `GlobalModelParametersPayload`, `ImprovedModelParametersPayload` y `ParametrizedDataPayload`.

### 18.2 Privacidad diferencial

Los metadatos de ruido y anonimización se aplican al `ModelGradientUpdate`. Las sesiones que transportan gradientes pueden registrar `hasPrivacyBudget`, `noiseLevel`, `hasPrivacyMechanism` y una `PrivacyBudgetAccount` asociada a contrato/propósito.

La cuenta epsilon distingue `privacyBudgetMaximum`, `privacyBudgetConsumed` y `privacyBudgetRemaining`. El máximo no se inventa si el perfil o la política no lo han fijado.

### 18.3 Flujo descendente

Una descarga de modelo mejorado no se modela como gradiente individualizado. Puede declarar `containsPersonalData=false`, `containsIndividualizedGradients=false` y `containsPersistentIdentifier=false`, y no necesita un presupuesto DP artificial cuando solo transporta parámetros genéricos.

### 18.4 Versionado y rollback

`AIModel` conserva `modelVersion`, `lastUpdated`, `supersedesModel` y `modelLineageStatus`. `RollbackEvent` enlaza `rollbackTarget` para volver a una versión anterior válida ante degradación o incumplimiento.

## 19. Modelo temporal

`TemporalEntity` centraliza `validFrom`, `validTo` y `plannedExpiry`.

```text
TemporalEntity
 ├─ State
 │   ├─ NodeState
 │   ├─ DeviceState
 │   ├─ UserState
 │   ├─ ServiceState
 │   └─ EvaluationState
 ├─ SemanticContract
 ├─ ConsentRecord
 ├─ AuthorizationDecision
 ├─ NodeUserRelation
 ├─ DataContext
 ├─ TrustAssessment
 ├─ TransferEvent / BufferRecord / ReplicationEvent
 └─ AdaptationAction y subclases
```

`validTo` representa siempre cierre efectivo. Una fecha de expiración prevista se expresa mediante `plannedExpiry`. Los estados derivados de observaciones usan `derivedFrom` solo cuando existe una evidencia temporal coherente.

## 20. Auditoría semántica y MAPE-K

`EvaluationState` funciona como ticket de auditoría. Puede enlazar:

- usuario (`evaluationUser`), propósito (`evaluationPurpose`) y zona (`evaluationZone`);
- contrato (`auditsContract`) y autorización efectiva (`hasAuthorizationDecision`);
- síntoma (`hasDetectedSymptom`) y estados evaluados;
- políticas (`appliedPolicy`) y mecanismos (`appliedMechanism`);
- método, pesos, alternativas, scores y trust externo;
- alternativa/tier seleccionado y justificación;
- versiones de requisitos/políticas usadas;
- acción ejecutada mediante `resultedInAction`.

### 20.1 Correspondencia MAPE-K

| Fase | Soporte semántico v3 |
|---|---|
| Monitor | `NodeState`, `DeviceState`, `UserState`, `ServiceState`, observaciones SOSA, `DataContext`. |
| Analyse | `MAPESymptom`, `AuthorizationDecision`, `TrustAssessment`, elegibilidad de nodos, cuentas de privacidad. |
| Plan | `EvaluationState`, `Policy`, `DecisionAlternative`, `DecisionMethod`, `PairwiseComparison`. |
| Execute | `AdaptationAction`, `DelegationEvent`, `MigrationEvent`, `FederatedLearningSession`, `TransferEvent`. |
| Knowledge | Grafo RDF completo, artefactos versionados, requisitos, políticas, mecanismos, escenarios y resultados de validación. |

## 21. Escenarios S1–S17

La v3 representa **17 `Scenario`**. S1–S8 reutilizan y corrigen evidencia histórica identificable; S9–S17 son especificaciones formales preparadas para ser pobladas sin inventar resultados experimentales.

| ID | Nombre | Políticas principales | Mecanismos principales | Consultas principales | Estado de datos |
|---|---|---|---|---|---|
| `S1` | Estado normal equilibrado | `P-GOV-03`, `P-MODEL-01`, `P-MODEL-05`, `P-NODE-02` | `M-AUD-01`, `M-GOV-03`, `M-MODEL-01`, `M-NODE-02` | `BASE-Q11`, `BASE-Q21`, `EXT-Q46`, `EXT-Q51` | Instancias heredadas/corregidas |
| `S2` | Saturación urbana por evento masivo | `P-ADAPT-01`, `P-ADAPT-03`, `P-OPS-02`, `P-ZONE-03` | `M-ADAPT-01`, `M-ADAPT-02`, `M-OPS-02`, `M-ZONE-01` | `BASE-Q12`, `BASE-Q19`, `EXT-Q41`, `EXT-Q42`, `EXT-Q62` | Instancias heredadas/corregidas |
| `S3` | Migración Edge → Fog | `P-ADAPT-01`, `P-ADAPT-04`, `P-ADAPT-05`, `P-ADAPT-06` | `M-ADAPT-01`, `M-ADAPT-03`, `M-AUD-01` | `BASE-Q13`, `EXT-Q59`, `EXT-Q60`, `EXT-Q61` | Instancias heredadas/corregidas |
| `S4` | Fallo de comunicación y degradación | `P-ADAPT-02`, `P-DATA-07`, `P-NODE-01`, `P-OPS-04` | `M-ADAPT-02`, `M-NODE-01`, `M-TX-02` | `BASE-Q14`, `BASE-Q35`, `EXT-Q62`, `EXT-Q63`, `EXT-Q72` | Instancias heredadas/corregidas |
| `S5` | Usuario con consentimiento denegado o solo local | `P-CONS-01`, `P-CONS-04`, `P-CONS-06`, `P-DATA-01` | `M-CONS-01`, `M-CONS-02`, `M-DATA-01`, `M-FL-02` | `BASE-Q15`, `EXT-Q11`, `EXT-Q17`, `EXT-Q19`, `EXT-Q22` | Instancias heredadas/corregidas |
| `S6` | Sesión HFL global autorizada | `P-FL-01`, `P-FL-02`, `P-FL-03`, `P-FL-04`, `P-FL-07` | `M-AUD-01`, `M-FL-01`, `M-FL-03`, `M-FL-04` | `BASE-Q16`, `BASE-Q24`, `EXT-Q66`, `EXT-Q67`, `EXT-Q68`, `EXT-Q69` | Instancias heredadas/corregidas |
| `S7` | Zona rural con retención local | `P-DATA-05`, `P-DATA-07`, `P-ZONE-02` | `M-BUFFER-01`, `M-TX-02`, `M-ZONE-01` | `BASE-Q17`, `EXT-Q31`, `EXT-Q38` | Instancias heredadas/corregidas |
| `S8` | Zona restringida | `P-DATA-01`, `P-GOV-03`, `P-ZONE-01` | `M-DATA-01`, `M-GOV-03`, `M-ZONE-01` | `BASE-Q18`, `BASE-Q34`, `EXT-Q36`, `EXT-Q37` | Instancias heredadas/corregidas |
| `S9` | Escalabilidad bajo crecimiento | `P-OPS-01`, `P-OPS-02`, `P-OPS-03`, `P-OPS-05` | `M-METRIC-01`, `M-OPS-01`, `M-OPS-02`, `M-OPS-03` | `BASE-Q02`, `BASE-Q07`, `BASE-Q29`, `BASE-Q33`, `EXT-Q76` | Especificación formal; datos experimentales por poblar |
| `S10` | Propagación descendente de modelo | `P-CONS-06`, `P-FL-06`, `P-FL-08` | `M-FL-02`, `M-MODEL-05` | `BASE-Q04`, `BASE-Q16`, `EXT-Q57`, `EXT-Q58`, `EXT-Q66` | Especificación formal; datos experimentales por poblar |
| `S11` | Contrato semántico consent-aware | `P-CONS-01`, `P-CONS-02`, `P-CONS-03`, `P-CONS-04`, `P-CONS-05` | `M-CONS-01`, `M-CONS-02`, `M-CONS-03` | `BASE-Q20`, `EXT-Q11`, `EXT-Q12`, `EXT-Q14`, `EXT-Q15`, `EXT-Q17`, `EXT-Q19`, `EXT-Q21` | Especificación formal; datos experimentales por poblar |
| `S12` | Selección limitada por autorización efectiva | `P-CONS-04`, `P-GOV-03`, `P-MODEL-01`, `P-NODE-02` | `M-CONS-02`, `M-GOV-03`, `M-MODEL-01`, `M-NODE-02` | `BASE-Q21`, `BASE-Q25`, `EXT-Q17`, `EXT-Q19`, `EXT-Q20`, `EXT-Q42`, `EXT-Q46`, `EXT-Q56` | Especificación formal; datos experimentales por poblar |
| `S13` | Delegación trust-based | `P-ADAPT-07`, `P-AUD-01`, `P-AUD-04`, `P-NODE-03`, `P-NODE-05` | `M-DELEG-01`, `M-DELEG-03`, `M-TRUST-01`, `M-TRUST-02` | `BASE-Q19`, `EXT-Q40`, `EXT-Q42`, `EXT-Q43`, `EXT-Q45`, `EXT-Q63`, `EXT-Q65` | Especificación formal; datos experimentales por poblar |
| `S14` | Decisión AHP explicable | `P-MODEL-02`, `P-MODEL-03`, `P-MODEL-04`, `P-MODEL-05` | `M-AUD-01`, `M-MODEL-01`, `M-MODEL-02`, `M-MODEL-03` | `BASE-Q21`, `EXT-Q46`, `EXT-Q48`, `EXT-Q49`, `EXT-Q50`, `EXT-Q51`, `EXT-Q53` | Especificación formal; datos experimentales por poblar |
| `S15` | Privacidad diferencial en gradientes FL | `P-DATA-02`, `P-FL-03`, `P-FL-04`, `P-FL-05` | `M-FL-03`, `M-FL-04`, `M-ID-01` | `BASE-Q24`, `EXT-Q23`, `EXT-Q26`, `EXT-Q27`, `EXT-Q29`, `EXT-Q30`, `EXT-Q66`, `EXT-Q68`, `EXT-Q69` | Especificación formal; datos experimentales por poblar |
| `S16` | Gobernanza por obligación, abstención y prohibición | `P-GOV-01`, `P-GOV-02`, `P-GOV-03`, `P-GOV-04` | `M-GOV-01`, `M-GOV-02`, `M-GOV-03`, `M-GOV-04` | `EXT-Q03`, `EXT-Q06`, `EXT-Q07`, `EXT-Q10`, `EXT-Q78`, `EXT-Q79` | Especificación formal; datos experimentales por poblar |
| `S17` | Auditoría semántica completa | `P-AUD-05`, `P-AUD-06`, `P-AUD-07`, `P-VAL-04` | `M-AUD-01`, `M-AUD-02`, `M-AUD-03`, `M-VAL-04` | `BASE-Q35`, `EXT-Q46`, `EXT-Q59`, `EXT-Q70`, `EXT-Q71`, `EXT-Q72`, `EXT-Q73`, `EXT-Q77`, `EXT-Q80` | Especificación formal; datos experimentales por poblar |

Correcciones destacadas: S3 es una migración explícita y no genera FL automáticamente; S5 opera con consentimiento local/denegable por rango; S8 selecciona `LocalModelTier` sobre Mist autorizado y bloquea Edge/Fog/Cloud para el procesamiento protegido.

## 22. Validación SPARQL y catálogo de consultas

La batería ejecutable vigente es externa a la TTL: `sparql_battery_v3.0.0.sparql`. Contiene **115 consultas SPARQL 1.1** documentadas en `Consultas_Sparql_v3.0.0.md`.

| Familia | Rango | Nº | Finalidad |
|---|---|---:|---|
| BASE | `BASE-Q01–BASE-Q35` | 35 | Estructura, operación, escenarios S1–S8, ASK y agregados. |
| EXT v3 | `EXT-Q01–EXT-Q80` | 80 | Gobernanza, privacidad, decisión, auditoría, temporalidad, aceptación y reproducibilidad. |

Tipos documentales de consulta: `inventory`, `report`, `review`, `violation`, `ASK` y `dashboard`. Una consulta `violation` con 0 filas solo acredita cumplimiento después de validar versión, dataset, cobertura, escenarios y perfil de aceptación.

### 22.1 Estado del `QueryCatalog` dentro de la TTL

La TTL conserva actualmente `ex:QueryCatalog_Pending` con estado `pending-definition` y **0 individuos `QuerySpecification`**. Esto no significa que la batería SPARQL esté ausente: el catálogo ejecutable externo ya está completo. Significa que las 115 especificaciones todavía no se han materializado como individuos dentro del grafo. Si se desea trazabilidad totalmente autocontenida en RDF, una siguiente revisión deberá sustituir/actualizar `QueryCatalog_Pending` y crear las `QuerySpecification` correspondientes.

## 23. Validación SHACL

La ontología incluye **15 `sh:NodeShape`** de estructura. No sustituyen las consultas SPARQL; validan cardinalidades y tipos básicos de los elementos críticos.

| Shape | Target | Finalidad |
|---|---|---|
| `ex:AIModelShape_v3` | `ex:AIModel` | Every deployable model version should have lastUpdated for reproducibility.; Every deployable model version should have a modelVersion. |
| `ex:AcceptanceProfileShape_v3` | `ex:AcceptanceProfile` | Acceptance threshold must be configured before a validation campaign.; Acceptance threshold must be configured before a validation campaign. |
| `ex:AuthorizationDecisionShape_v3` | `ex:AuthorizationDecision` | Effective authorization completeness |
| `ex:ConsentRecordShape_v3` | `ex:ConsentRecord` | Consent record completeness |
| `ex:DataContextShape_v3` | `ex:DataContext` | Data context minimum fields |
| `ex:DecisionAlternativeShape_v3` | `ex:DecisionAlternative` | A v3 decision alternative should contain a score; migrated legacy alternatives are pending recalculation. |
| `ex:DelegationEventShape_v3` | `ex:DelegationEvent` | Delegation lifecycle |
| `ex:EvaluationStateShape_v3` | `ex:EvaluationState` | Evaluation audit ticket completeness |
| `ex:FederatedLearningSessionShape_v3` | `ex:FederatedLearningSession` | Federated learning session structure |
| `ex:MechanismShape_v3` | `ex:MechanismSpecification` | Mechanism specification completeness |
| `ex:ModelGradientUpdateShape_v3` | `ex:ModelGradientUpdate` | Gradient privacy structure |
| `ex:PolicyShape_v3` | `ex:Policy` | Policy specification completeness |
| `ex:SemanticContractShape_v3` | `ex:SemanticContract` | Semantic contract completeness |
| `ex:StateShape_v3` | `ex:State` | Every State must have exactly one validFrom. |
| `ex:TrustAssessmentShape_v3` | `ex:TrustAssessment` | Historical trust window start is required for reproducible v3 trust.; Historical trust window end is required for reproducible v3 trust. |

## 24. Artefactos, versionado y reproducibilidad

La v3 introduce `Artifact` y especializaciones para enlazar versiones concretas de los componentes de una campaña.

| Artefacto en TTL | Clase | Identificador | Versión/estado |
|---|---|---|---|
| `ex:RequirementsArtifact_Revised` | `ex:RequirementsArtifact` | `RN_RNF_revisado_requisitos.md` | revised |
| `ex:PolicyArtifact_POLICIES_REV_01` | `ex:PolicyArtifact` | `POLICIES-REV-01` | 2026-08-26 / revised |
| `ex:ScenarioArtifact_S1_S17_v3` | `ex:ScenarioArtifact` | `S1-S17` | 3.0.0 / revised-specification |
| `ex:OntologyArtifact_3_0_0` | `ex:OntologyArtifact` | `smartcity_continuum_v3.0.0.ttl` | 3.0.0 / generated |
| `ex:QueryCatalog_Pending` | `ex:QueryCatalog` | `QUERY-CATALOG-PENDING` | pending-definition |
| `ex:AcceptanceProfile_v3_Draft` | `ex:AcceptanceProfile` | `ACCEPTANCE-PROFILE-V3-DRAFT` | draft-incomplete |

`ValidationCampaign` puede enlazar ontología, políticas, consultas, escenarios y `AcceptanceProfile`, y almacenar `ValidationResult`/`ComplianceMetric`. El perfil de aceptación actual es deliberadamente incompleto: solo fija el umbral local explícitamente respaldado por los requisitos y deja el resto pendiente.

## 25. Estadísticas de la ontología

| Elemento | Cantidad actual |
|---|---:|
| Triples RDF | 7827 |
| Recursos `owl:Class` | 151 |
| Clases nombradas `ex:` | 133 |
| Propiedades de objeto | 162 |
| Propiedades de objeto `ex:` | 157 |
| Propiedades de datos | 94 |
| Propiedades de datos `ex:` | 92 |
| Individuos `owl:NamedIndividual` | 669 |
| Requisitos funcionales | 72 |
| Requisitos no funcionales | 39 |
| Requisitos de validación | 5 |
| Políticas | 79 |
| Mecanismos | 55 |
| Categorías de políticas | 12 |
| Relaciones entre categorías | 66 |
| Escenarios | 17 |
| Shapes SHACL | 15 |
| QuerySpecification materializadas en TTL | 0 |
| Consultas externas documentadas | 115 |

## 26. Estado de validación

La versión actual se reparsea correctamente con RDFLib y las comprobaciones estructurales realizadas sobre la TTL v3 superan los controles duros establecidos durante la migración:

- versión OWL `3.0.0`;
- eliminación del consentimiento binario y de `hasConsent`;
- 79 políticas, 55 mecanismos y 116 requisitos representados;
- S1–S17 presentes;
- S3 modelado como migración explícita sin FL heredado;
- S8 confinado a Local/Mist;
- trust fuera de los pesos AHP de `NodeState`;
- pesos heredados normalizados sin trust;
- estados heredados con `validFrom`;
- ausencia de transferencia externa modelada de observaciones fisiológicas crudas;
- 0 incompatibilidades heurísticas de dominio/rango en propiedades de objeto y de dominio en propiedades de datos;
- 66 relaciones entre categorías de políticas representadas.

La batería SPARQL v3 fue diseñada y ejecutada separadamente sobre esta TTL. Las consultas de tipo `violation` no presentan falsos positivos estructurales en el estado documentado; las de tipo `review` mantienen visibles las deudas de datos heredados/configuración.

## 27. Datos pendientes y limitaciones conocidas

La ontología modela los siguientes campos, pero no fabrica valores que los artefactos fuente no proporcionan:

- puntuaciones de todas las alternativas de `Eval_S1–Eval_S8` (32 alternativas estructurales pendientes de recalcular);
- ventanas históricas/evidencias completas de los trust scores heredados;
- `T_migration_max`, `T_sparql_monitor`, `T_decision_max`, `E_device_max`, `N_agents`, `T_node_join`, `D_delegation_max` y `T_reselection_max`;
- `AHP_consistency_threshold` del perfil de aceptación;
- presupuesto epsilon máximo autorizado para la cuenta global histórica de UserA;
- zona histórica exacta de UserB en S5, representada como `UnknownZone` hasta disponer de evidencia;
- métricas observadas específicas de latencia/energía en aquellos escenarios donde la fuente antigua no las almacenaba;
- materialización RDF de las 115 consultas como `QuerySpecification` (la batería externa sí está completa).

Estos elementos deben considerarse **deuda de datos/configuración**, no fallos del esquema. Las consultas `review` de la batería v3 los distinguen de los incumplimientos normativos.

## 28. Referencias cruzadas de artefactos

| Artefacto | Función |
|---|---|
| `smartcity_continuum_v3.0.0.ttl` | Ontología ejecutable descrita por este documento. |
| `RN_RNF_revisado_requisitos_trazabilidad_v3.0.0.md` | Requisitos RF/RNF/RV y matriz completa requisito→ontología→política→mecanismo→consulta. |
| `Politicas_revisadas_trazabilidad_v3.0.0.md` | 79 políticas, 55 mecanismos, conflictos, escenarios y consultas asociadas. |
| `sparql_battery_v3.0.0.sparql` | Catálogo ejecutable de 115 consultas SPARQL independientes. |
| `Consultas_Sparql_v3.0.0.md` | Documentación de cada consulta, tipo, finalidad, trazabilidad y resultado de referencia. |
| `ONTOLOGY_V3_MIGRATION_REPORT.md` | Registro de decisiones y correcciones realizadas al migrar desde v2.1.1. |

---

## Nota de mantenimiento

Esta documentación debe versionarse conjuntamente con la TTL. Si se materializan las consultas SPARQL como `QuerySpecification`, se completan los umbrales del `AcceptanceProfile`, se recalculan alternativas AHP/trust o se pueblan experimentalmente S9–S17, deberá actualizarse esta documentación y la trazabilidad de artefactos sin reutilizar silenciosamente la versión `3.0.0`.
