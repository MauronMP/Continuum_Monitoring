# Complete SPARQL query catalogue

Generated reading/export bundle, not one executable SPARQL statement.
The worker loads `catalog.csv` and the individual `.rq` files. Edit those
sources and regenerate this file; do not execute this document as a query.

Contains all 115 queries in catalogue order.

## BASE-Q01: Users, active consent and external identifiers

Category: `identity_consent`. Scope: `authorities`.

Source: [core/identity_consent/base-q01.rq](../queries/core/identity_consent/base-q01.rq).

Evaluate users, active consent and external identifiers using the declared query contract.

```sparql
# Type: inventory
# Purpose: Evaluate users, active consent and external identifiers using the declared query contract.
# Requirements: RF-01, RF-32, RF-61, RF-70
# Policies: P-CONS-01, P-DATA-02
# Current v4.0.0 result: 4 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?user ?name ?activeRange ?identifier ?identifierType WHERE {
  ?user a comon:User .
  OPTIONAL { ?user foaf:name ?name }
  OPTIONAL { ?user comon:hasActiveConsentRange ?activeRange }
  OPTIONAL {
    ?user comon:hasIdentifier ?identifier .
    ?identifier a ?identifierType .
    FILTER(?identifierType IN (comon:PseudonymousIdentifier, comon:AnonymousIdentifier, comon:DirectIdentifier))
  }
}
ORDER BY ?user
```

## BASE-Q02: Compute nodes, types and elasticity

Category: `topology`. Scope: `authority_key:http://example.org/monitoringcontinuum#UserB`.

Source: [core/topology/base-q02.rq](../queries/core/topology/base-q02.rq).

Evaluate compute nodes, types and elasticity using the declared query contract.

```sparql
# Type: inventory
# Purpose: Evaluate compute nodes, types and elasticity using the declared query contract.
# Requirements: RF-02, RF-05, RF-70
# Policies: P-OPS-02, P-OPS-03
# Current v4.0.0 result: 8 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?node ?nodeType ?elasticity WHERE {
  ?node a ?nodeType .
  ?nodeType rdfs:subClassOf* comon:ComputationalNode .
  FILTER(?nodeType != comon:ComputationalNode)
  OPTIONAL { ?node comon:hasElasticity ?elasticity }
}
ORDER BY ?node ?nodeType
```

## BASE-Q03: Wearables associated with users

Category: `wellbeing`. Scope: `authorities`.

Source: [domain/wellbeing/wellbeing/base-q03.rq](../queries/domain/wellbeing/wellbeing/base-q03.rq).

Evaluate wearables associated with users using the declared query contract.

```sparql
# Type: inventory
# Purpose: Evaluate wearables associated with users using the declared query contract.
# Requirements: RF-01, RF-70
# Policies: P-INT-02
# Current v4.0.0 result: 4 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?user ?wearable ?wearableType WHERE {
  ?user a comon:User ; comon:hasWearable ?wearable .
  ?wearable a ?wearableType .
  ?wearableType rdfs:subClassOf* comon:Wearable .
  FILTER(?wearableType != comon:Wearable)
}
ORDER BY ?user ?wearable
```

## BASE-Q04: Models, tiers, versions, hosts and lineage

Category: `decision`. Scope: `authority_key:http://example.org/monitoringcontinuum#UserB`.

Source: [core/decision/base-q04.rq](../queries/core/decision/base-q04.rq).

Evaluate models, tiers, versions, hosts and lineage using the declared query contract.

```sparql
# Type: inventory
# Purpose: Evaluate models, tiers, versions, hosts and lineage using the declared query contract.
# Requirements: RF-11, RF-12, RF-13, RF-24, RF-70
# Policies: P-FL-08, P-MODEL-01
# Current v4.0.0 result: 7 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?model ?tier ?version ?updated ?host ?supersedes WHERE {
  ?model a comon:AIModel .
  OPTIONAL { ?model comon:hasModelTier ?tier }
  OPTIONAL { ?model comon:modelVersion ?version }
  OPTIONAL { ?model comon:lastUpdated ?updated }
  OPTIONAL { ?model comon:hostedOnNode ?host }
  OPTIONAL { ?model comon:supersedesModel ?supersedes }
}
ORDER BY ?model
```

## BASE-Q05: Physiological sensors and host devices

Category: `wellbeing`. Scope: `authorities`.

Source: [domain/wellbeing/wellbeing/base-q05.rq](../queries/domain/wellbeing/wellbeing/base-q05.rq).

Evaluate physiological sensors and host devices using the declared query contract.

```sparql
# Type: inventory
# Purpose: Evaluate physiological sensors and host devices using the declared query contract.
# Requirements: RF-06, RNF-25, RF-70
# Policies: P-INT-01
# Current v4.0.0 result: 5 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?sensor ?sensorType ?device WHERE {
  ?sensor a ?sensorType .
  ?sensorType rdfs:subClassOf* comon:PhysiologicalSensor .
  FILTER(?sensorType != comon:PhysiologicalSensor)
  OPTIONAL { ?device saref:consistsOf ?sensor }
}
ORDER BY ?device ?sensor
```

## BASE-Q06: RBAC roles and permissions

Category: `identity_consent`. Scope: `cloud`.

Source: [core/identity_consent/base-q06.rq](../queries/core/identity_consent/base-q06.rq).

Evaluate rBAC roles and permissions using the declared query contract.

```sparql
# Type: inventory
# Purpose: Evaluate rBAC roles and permissions using the declared query contract.
# Requirements: RF-37, RF-70
# Policies: P-CONS-05
# Current v4.0.0 result: 10 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?role ?permission ?requiredRange WHERE {
  ?role a comon:Role .
  OPTIONAL { ?role comon:hasPermission ?permission }
  OPTIONAL { ?permission comon:requiresConsentRange ?requiredRange }
}
ORDER BY ?role ?permission
```

## BASE-Q07: Node states and operational metrics

Category: `observability`. Scope: `fog`.

Source: [core/observability/base-q07.rq](../queries/core/observability/base-q07.rq).

Evaluate node states and operational metrics using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate node states and operational metrics using the declared query contract.
# Requirements: RF-05, RF-29, RF-45, RF-70
# Policies: P-NODE-01, P-NODE-03, P-OPS-05
# Current v4.0.0 result: 7 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?node ?state ?workload ?availability ?communication ?residual ?resourceUsage ?queued ?operational ?trust WHERE {
  ?node comon:hasNodeState ?state .
  ?state a comon:NodeState .
  OPTIONAL { ?state comon:hasWorkload ?workload }
  OPTIONAL { ?state comon:hasAvailability ?availability }
  OPTIONAL { ?state comon:hasCommunication ?communication }
  OPTIONAL { ?state comon:hasResidualCapacity ?residual }
  OPTIONAL { ?state comon:resourceUsagePercent ?resourceUsage }
  OPTIONAL { ?state comon:queuedRequests ?queued }
  OPTIONAL { ?state comon:hasOperationalStatus ?operational }
  OPTIONAL { ?state comon:hasTrustAssessment/comon:hasTrustScore ?trust }
}
ORDER BY ?node ?state
```

## BASE-Q08: Saturated, unavailable or disconnected nodes

Category: `observability`. Scope: `fog`.

Source: [core/observability/base-q08.rq](../queries/core/observability/base-q08.rq).

Evaluate saturated, unavailable or disconnected nodes using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate saturated, unavailable or disconnected nodes using the declared query contract.
# Requirements: RF-17, RF-47, RNF-12
# Policies: P-NODE-01, P-NODE-02
# Current v4.0.0 result: 2 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?node ?state ?workload ?availability ?communication ?operational WHERE {
  ?node comon:hasNodeState ?state .
  ?state a comon:NodeState .
  OPTIONAL { ?state comon:hasWorkload ?workload }
  OPTIONAL { ?state comon:hasAvailability ?availability }
  OPTIONAL { ?state comon:hasCommunication ?communication }
  OPTIONAL { ?state comon:hasOperationalStatus ?operational }
  FILTER(
    ?workload = comon:SaturatedWorkload ||
    ?availability = comon:NotAvailable ||
    ?communication = comon:NoConnectionComm ||
    ?operational = comon:Inoperative
  )
}
ORDER BY ?node
```

## BASE-Q09: User states, mobility and stress

Category: `wellbeing`. Scope: `authorities`.

Source: [domain/wellbeing/wellbeing/base-q09.rq](../queries/domain/wellbeing/wellbeing/base-q09.rq).

Evaluate user states, mobility and stress using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate user states, mobility and stress using the declared query contract.
# Requirements: RF-03, RF-30, RNF-35
# Policies: P-GOV-05, P-OPS-05
# Current v4.0.0 result: 6 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?user ?state ?mobility ?stress ?personStatus ?from ?to WHERE {
  ?user comon:hasUserState ?state .
  ?state a comon:UserState .
  OPTIONAL { ?state comon:hasMobility ?mobility }
  OPTIONAL { ?state comon:hasPredictedStressLevel ?stress }
  OPTIONAL { ?state comon:hasPersonStatus ?personStatus }
  OPTIONAL { ?state comon:validFrom ?from }
  OPTIONAL { ?state comon:validTo ?to }
}
ORDER BY ?user ?from
```

## BASE-Q10: Device states and transmission eligibility

Category: `observability`. Scope: `authorities`.

Source: [domain/wellbeing/observability/base-q10.rq](../queries/domain/wellbeing/observability/base-q10.rq).

Evaluate device states and transmission eligibility using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate device states and transmission eligibility using the declared query contract.
# Requirements: RF-04, RF-26, RF-27, RF-07
# Policies: P-DATA-04, P-DATA-06, P-DATA-07
# Current v4.0.0 result: 4 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?user ?device ?state ?battery ?connection ?dataReady ?from ?to WHERE {
  ?user a comon:User .
  { ?user comon:hasWearable ?device } UNION { ?user comon:hasMobileDevice ?device }
  ?device comon:hasDeviceState ?state .
  OPTIONAL { ?state comon:hasBatteryLevel ?battery }
  OPTIONAL { ?state comon:hasConnectionStatus ?connection }
  OPTIONAL { ?state comon:parametrizedDataReady ?dataReady }
  OPTIONAL { ?state comon:validFrom ?from }
  OPTIONAL { ?state comon:validTo ?to }
}
ORDER BY ?user ?device ?from
```

## BASE-Q11: Scenario S1: normal operation

Category: `wellbeing`. Scope: `authority_key:http://example.org/monitoringcontinuum#UserA`.

Source: [core/wellbeing/base-q11.rq](../queries/core/wellbeing/base-q11.rq).

Evaluate scenario S1: normal operation using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate scenario S1: normal operation using the declared query contract.
# Requirements: RF-31, RF-72
# Policies: P-VAL-07
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?node ?tier ?action ?profitability WHERE {
  ?evaluation a comon:EvaluationState ; comon:partOfScenario comon:S1 .
  OPTIONAL { ?evaluation comon:evaluatesNode ?node }
  OPTIONAL { ?evaluation comon:selectedModelTier ?tier }
  OPTIONAL { ?evaluation comon:resultedInAction ?action }
  OPTIONAL { ?evaluation comon:hasProfitability ?profitability }
}
```

## BASE-Q12: Scenario S2: saturation and fog candidates

Category: `adaptation`. Scope: `authorities`.

Source: [core/adaptation/base-q12.rq](../queries/core/adaptation/base-q12.rq).

Evaluate scenario S2: saturation and fog candidates using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate scenario S2: saturation and fog candidates using the declared query contract.
# Requirements: RF-17, RF-31
# Policies: P-ADAPT-01, P-NODE-02
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?edgeState ?edgeTrust ?fogState ?fogTrust WHERE {
  ?edgeState a comon:NodeState ; comon:partOfScenario comon:S2 ; comon:hasWorkload comon:SaturatedWorkload .
  OPTIONAL { ?edgeState comon:hasTrustAssessment/comon:hasTrustScore ?edgeTrust }
  ?fogState a comon:NodeState ; comon:partOfScenario comon:S2 ; comon:hasAvailability comon:Available .
  OPTIONAL { ?fogState comon:hasTrustAssessment/comon:hasTrustScore ?fogTrust }
}
```

## BASE-Q13: Scenario S3: edge-to-fog migration

Category: `adaptation`. Scope: `authorities`.

Source: [core/adaptation/base-q13.rq](../queries/core/adaptation/base-q13.rq).

Evaluate scenario S3: edge-to-fog migration using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate scenario S3: edge-to-fog migration using the declared query contract.
# Requirements: RF-16, RF-17, RF-31
# Policies: P-ADAPT-05, P-ADAPT-06
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?migration ?origin ?target ?service ?evaluation ?from ?to WHERE {
  ?migration a comon:MigrationEvent ; comon:partOfScenario comon:S3 .
  OPTIONAL { ?migration comon:actionOriginNode ?origin }
  OPTIONAL { ?migration comon:actionTargetNode ?target }
  OPTIONAL { ?migration comon:affectsService ?service }
  OPTIONAL { ?migration comon:authorizedByEvaluation ?evaluation }
  OPTIONAL { ?migration comon:validFrom ?from }
  OPTIONAL { ?migration comon:validTo ?to }
}
```

## BASE-Q14: Scenario S4: failure, delegation and degradation

Category: `delegation`. Scope: `authority_key:http://example.org/monitoringcontinuum#UserA`.

Source: [core/delegation/base-q14.rq](../queries/core/delegation/base-q14.rq).

Evaluate scenario S4: failure, delegation and degradation using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate scenario S4: failure, delegation and degradation using the declared query contract.
# Requirements: RF-17, RF-20, RF-62, RF-65
# Policies: P-ADAPT-02, P-AUD-01, P-AUD-05
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?failedState ?symptom ?delegation ?target ?degradation ?evaluation WHERE {
  ?failedState a comon:NodeState ; comon:partOfScenario comon:S4 .
  OPTIONAL { ?evaluation a comon:EvaluationState ; comon:partOfScenario comon:S4 ; comon:hasDetectedSymptom ?symptom }
  OPTIONAL { ?delegation a comon:DelegationEvent ; comon:partOfScenario comon:S4 ; comon:actionTargetNode ?target }
  OPTIONAL { ?degradation a comon:DegradationEvent ; comon:partOfScenario comon:S4 }
}
```

## BASE-Q15: Scenario S5: local consent

Category: `identity_consent`. Scope: `authorities`.

Source: [core/identity_consent/base-q15.rq](../queries/core/identity_consent/base-q15.rq).

Evaluate scenario S5: local consent using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate scenario S5: local consent using the declared query contract.
# Requirements: RF-32, RF-36, RF-38, RF-07
# Policies: P-CONS-01, P-CONS-04, P-MODEL-06
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?user ?activeRange ?authorization ?effectiveRange ?tier ?action WHERE {
  ?evaluation a comon:EvaluationState ; comon:partOfScenario comon:S5 ; comon:evaluationUser ?user ; comon:hasAuthorizationDecision ?authorization ; comon:selectedModelTier ?tier .
  ?user comon:hasActiveConsentRange ?activeRange .
  ?authorization comon:hasEffectiveConsentRange ?effectiveRange .
  OPTIONAL { ?evaluation comon:resultedInAction ?action }
}
```

## BASE-Q16: Scenario S6: protected federated learning

Category: `federation`. Scope: `authorities`.

Source: [core/federation/base-q16.rq](../queries/core/federation/base-q16.rq).

Evaluate scenario S6: protected federated learning using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate scenario S6: protected federated learning using the declared query contract.
# Requirements: RF-21, RF-22, RF-25, RF-56, RF-58
# Policies: P-FL-01, P-FL-03, P-FL-05, P-FL-07
# Current v4.0.0 result: 3 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?session ?payload ?model ?budget ?noise ?privacy ?personal ?individualized WHERE {
  ?session a comon:FederatedLearningSession ; comon:partOfScenario comon:S6 .
  OPTIONAL { ?session comon:hasPayloadType ?payload }
  OPTIONAL { ?session comon:updatesModel ?model }
  OPTIONAL { ?session comon:hasPrivacyBudget ?budget }
  OPTIONAL { ?session comon:noiseLevel ?noise }
  OPTIONAL { ?session comon:hasPrivacyMechanism ?privacy }
  OPTIONAL { ?session comon:containsPersonalData ?personal }
  OPTIONAL { ?session comon:containsIndividualizedGradients ?individualized }
}
ORDER BY ?session ?privacy
```

## BASE-Q17: Scenario S7: rural areas and retention

Category: `context_zones`. Scope: `authorities`.

Source: [domain/wellbeing/context_zones/base-q17.rq](../queries/domain/wellbeing/context_zones/base-q17.rq).

Evaluate scenario S7: rural areas and retention using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate scenario S7: rural areas and retention using the declared query contract.
# Requirements: RF-08, RF-27, RF-31
# Policies: P-ZONE-02, P-DATA-07
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?user ?zone ?deviceState ?connection ?retention ?sync WHERE {
  ?user a comon:User ; comon:locatedInZone ?zone .
  ?zone a comon:RuralZone .
  OPTIONAL { ?user (comon:hasWearable|comon:hasMobileDevice)/comon:hasDeviceState ?deviceState . ?deviceState comon:hasConnectionStatus ?connection }
  OPTIONAL { ?retention a comon:RetentionEvent ; comon:partOfScenario comon:S7 }
  OPTIONAL { ?sync a comon:SynchronizationEvent ; comon:partOfScenario comon:S7 }
}
```

## BASE-Q18: Scenario S8: restricted areas and local confinement

Category: `context_zones`. Scope: `authorities`.

Source: [core/context_zones/base-q18.rq](../queries/core/context_zones/base-q18.rq).

Evaluate scenario S8: restricted areas and local confinement using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate scenario S8: restricted areas and local confinement using the declared query contract.
# Requirements: RF-42, RF-43, RF-60
# Policies: P-ZONE-01, P-DATA-01
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?user ?zone ?evaluation ?tier ?action WHERE {
  ?evaluation a comon:EvaluationState ; comon:partOfScenario comon:S8 ; comon:evaluationUser ?user ; comon:evaluationZone ?zone ; comon:selectedModelTier ?tier .
  OPTIONAL { ?evaluation comon:resultedInAction ?action }
}
```

## BASE-Q19: Operationally eligible candidates

Category: `decision`. Scope: `fog`.

Source: [core/decision/base-q19.rq](../queries/core/decision/base-q19.rq).

Evaluate operationally eligible candidates using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate operationally eligible candidates using the declared query contract.
# Requirements: RF-18, RF-47, RF-48
# Policies: P-NODE-02, P-NODE-05
# Current v4.0.0 result: 4 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?node ?state ?workload ?availability ?communication ?residual ?trust WHERE {
  ?node comon:hasNodeState ?state .
  ?state comon:hasAvailability comon:Available ; comon:hasCommunication comon:StableComm ; comon:hasWorkload ?workload ; comon:hasResidualCapacity ?residual .
  FILTER(?workload IN (comon:LowWorkload, comon:MediumWorkload))
  FILTER(?residual IN (comon:MediumResidual, comon:HighResidual))
  OPTIONAL { ?state comon:hasTrustAssessment/comon:hasTrustScore ?trust }
}
ORDER BY DESC(?trust) ?node
```

## BASE-Q20: Complete user semantic profile

Category: `identity_consent`. Scope: `authorities`.

Source: [domain/wellbeing/identity_consent/base-q20.rq](../queries/domain/wellbeing/identity_consent/base-q20.rq).

Evaluate complete user semantic profile using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate complete user semantic profile using the declared query contract.
# Requirements: RF-02, RF-33, RF-34, RF-70
# Policies: P-CONS-02, P-CONS-03
# Current v4.0.0 result: 4 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?user ?name ?zone ?wearable ?mobile ?activeRange ?consentRecord ?contract WHERE {
  ?user a comon:User .
  OPTIONAL { ?user foaf:name ?name }
  OPTIONAL { ?user comon:locatedInZone ?zone }
  OPTIONAL { ?user comon:hasWearable ?wearable }
  OPTIONAL { ?user comon:hasMobileDevice ?mobile }
  OPTIONAL { ?user comon:hasActiveConsentRange ?activeRange }
  OPTIONAL { ?user comon:hasConsentRecord ?consentRecord }
  OPTIONAL { ?user comon:hasSemanticContract ?contract }
}
ORDER BY ?user
```

## BASE-Q21: Evaluation states and executed actions

Category: `decision`. Scope: `authorities`.

Source: [core/decision/base-q21.rq](../queries/core/decision/base-q21.rq).

Evaluate evaluation states and executed actions using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate evaluation states and executed actions using the declared query contract.
# Requirements: RF-14, RF-15, RF-66
# Policies: P-AUD-06, P-MODEL-05
# Current v4.0.0 result: 11 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?scenario ?user ?node ?method ?tier ?profitability ?action ?from WHERE {
  ?evaluation a comon:EvaluationState .
  OPTIONAL { ?evaluation comon:partOfScenario ?scenario }
  OPTIONAL { ?evaluation comon:evaluationUser ?user }
  OPTIONAL { ?evaluation comon:evaluatesNode ?node }
  OPTIONAL { ?evaluation comon:hasDecisionMethod ?method }
  OPTIONAL { ?evaluation comon:selectedModelTier ?tier }
  OPTIONAL { ?evaluation comon:hasProfitability ?profitability }
  OPTIONAL { ?evaluation comon:resultedInAction ?action }
  OPTIONAL { ?evaluation comon:validFrom ?from }
}
ORDER BY ?from ?evaluation
```

## BASE-Q22: Models and degradation events

Category: `adaptation`. Scope: `authorities`.

Source: [core/adaptation/base-q22.rq](../queries/core/adaptation/base-q22.rq).

Evaluate models and degradation events using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate models and degradation events using the declared query contract.
# Requirements: RF-20, RF-24
# Policies: P-ADAPT-06, P-FL-08
# Current v4.0.0 result: 3 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?model ?cause ?event ?service ?scenario WHERE {
  { ?model a comon:AIModel ; comon:hasDegradationCause ?cause }
  UNION
  { ?event a comon:DegradationEvent . OPTIONAL { ?event comon:affectsModel ?model } OPTIONAL { ?event comon:affectsService ?service } OPTIONAL { ?event comon:hasDegradationCause ?cause } OPTIONAL { ?event comon:partOfScenario ?scenario } }
}
ORDER BY ?scenario ?model ?event
```

## BASE-Q23: User-node relationships and distance

Category: `topology`. Scope: `authorities`.

Source: [core/topology/base-q23.rq](../queries/core/topology/base-q23.rq).

Evaluate user-node relationships and distance using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate user-node relationships and distance using the declared query contract.
# Requirements: RF-02, RF-03, RF-18
# Policies: P-NODE-02
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?relation ?user ?node ?distance ?preferred ?from ?to WHERE {
  ?relation a comon:NodeUserRelation ; comon:relatesUser ?user ; comon:relatesNode ?node .
  OPTIONAL { ?relation comon:hasDistance ?distance }
  OPTIONAL { ?relation comon:isPreferredNode ?preferred }
  OPTIONAL { ?relation comon:validFrom ?from }
  OPTIONAL { ?relation comon:validTo ?to }
}
ORDER BY ?user ?from
```

## BASE-Q24: Federated learning chain

Category: `federation`. Scope: `authorities`.

Source: [core/federation/base-q24.rq](../queries/core/federation/base-q24.rq).

Evaluate federated learning chain using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate federated learning chain using the declared query contract.
# Requirements: RF-21, RF-22, RF-25, RF-59
# Policies: P-FL-02, P-FL-04, P-FL-07
# Current v4.0.0 result: 5 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?session ?scenario ?node ?payload ?model ?data ?budgetAccount ?budget ?noise WHERE {
  ?session a comon:FederatedLearningSession .
  OPTIONAL { ?session comon:partOfScenario ?scenario }
  OPTIONAL { ?session comon:involvedNode ?node }
  OPTIONAL { ?session comon:hasPayloadType ?payload }
  OPTIONAL { ?session comon:updatesModel ?model }
  OPTIONAL { ?session comon:transfersData ?data }
  OPTIONAL { ?session comon:hasPrivacyBudgetAccount ?budgetAccount }
  OPTIONAL { ?session comon:hasPrivacyBudget ?budget }
  OPTIONAL { ?session comon:noiseLevel ?noise }
}
ORDER BY ?session ?node
```

## BASE-Q25: Users authorized for global federated learning

Category: `identity_consent`. Scope: `authorities`.

Source: [core/identity_consent/base-q25.rq](../queries/core/identity_consent/base-q25.rq).

Evaluate users authorized for global federated learning using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate users authorized for global federated learning using the declared query contract.
# Requirements: RF-21, RF-32, RF-36
# Policies: P-CONS-04, P-FL-02
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?user ?authorization ?effectiveRange ?contract WHERE {
  ?authorization a comon:AuthorizationDecision ; comon:hasEffectiveConsentRange comon:RangeGlobalAgg ; comon:basedOnContract ?contract .
  ?evaluation a comon:EvaluationState ; comon:hasAuthorizationDecision ?authorization ; comon:evaluationUser ?user ; comon:evaluationPurpose comon:PurposeGlobalFederatedLearning .
}
ORDER BY ?user
```

## BASE-Q26: ASK: a saturated node exists

Category: `observability`. Scope: `fog`.

Source: [core/observability/base-q26.rq](../queries/core/observability/base-q26.rq).

Evaluate aSK: a saturated node exists using the declared query contract.

```sparql
# Type: ASK
# Purpose: Evaluate aSK: a saturated node exists using the declared query contract.
# Requirements: RF-05, RF-29
# Policies: P-NODE-01
# Current v4.0.0 result: true
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

ASK { ?state a comon:NodeState ; comon:hasWorkload comon:SaturatedWorkload . }
```

## BASE-Q27: ASK: a degradation event exists

Category: `adaptation`. Scope: `authorities`.

Source: [core/adaptation/base-q27.rq](../queries/core/adaptation/base-q27.rq).

Evaluate aSK: a degradation event exists using the declared query contract.

```sparql
# Type: ASK
# Purpose: Evaluate aSK: a degradation event exists using the declared query contract.
# Requirements: RF-20
# Policies: P-ADAPT-06
# Current v4.0.0 result: true
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

ASK { { ?event a comon:DegradationEvent } UNION { ?model a comon:AIModel ; comon:hasDegradationCause ?cause } }
```

## BASE-Q28: ASK: an external transfer violates confinement or identity

Category: `identity_consent`. Scope: `authorities`.

Source: [domain/wellbeing/identity_consent/base-q28.rq](../queries/domain/wellbeing/identity_consent/base-q28.rq).

Evaluate aSK: an external transfer violates confinement or identity using the declared query contract.

```sparql
# Type: ASK
# Purpose: Evaluate aSK: an external transfer violates confinement or identity using the declared query contract.
# Requirements: RF-36, RF-60, RF-61
# Policies: P-CONS-04, P-DATA-04
# Current v4.0.0 result: false
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

ASK {
  ?transfer a comon:TransferEvent ; comon:transferDestination ?dest ; comon:carriesData ?data .
  ?dest a ?destType .
  FILTER(?destType IN (comon:EdgeNode,comon:FogNode,comon:CloudNode))
  { ?data a ?rawType . FILTER(?rawType IN (comon:PhysiologicalObservation,comon:SleepObservation)) }
  UNION
  { ?transfer comon:usesIdentifier ?id . ?id a comon:DirectIdentifier }
  UNION
  { FILTER NOT EXISTS { ?transfer comon:usesIdentifier ?safe . ?safe a ?safeType . FILTER(?safeType IN (comon:PseudonymousIdentifier,comon:AnonymousIdentifier)) } }
}
```

## BASE-Q29: ASK: fog or cloud elastic capacity exists

Category: `topology`. Scope: `fog`.

Source: [core/topology/base-q29.rq](../queries/core/topology/base-q29.rq).

Evaluate aSK: fog or cloud elastic capacity exists using the declared query contract.

```sparql
# Type: ASK
# Purpose: Evaluate aSK: fog or cloud elastic capacity exists using the declared query contract.
# Requirements: RNF-07
# Policies: P-OPS-02
# Current v4.0.0 result: true
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

ASK {
  ?node comon:hasElasticity true ; a ?type .
  FILTER(?type IN (comon:FogNode, comon:CloudNode))
}
```

## BASE-Q30: ASK: a federated learning session includes cloud

Category: `federation`. Scope: `authorities`.

Source: [core/federation/base-q30.rq](../queries/core/federation/base-q30.rq).

Evaluate aSK: a federated learning session includes cloud using the declared query contract.

```sparql
# Type: ASK
# Purpose: Evaluate aSK: a federated learning session includes cloud using the declared query contract.
# Requirements: RF-22
# Policies: P-FL-01
# Current v4.0.0 result: true
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

ASK { ?session a comon:FederatedLearningSession ; comon:involvedNode ?cloud . ?cloud a comon:CloudNode . }
```

## BASE-Q31: User counts by active consent range

Category: `identity_consent`. Scope: `cloud`.

Source: [core/identity_consent/base-q31.rq](../queries/core/identity_consent/base-q31.rq).

Evaluate user counts by active consent range using the declared query contract.

```sparql
# Type: dashboard
# Purpose: Evaluate user counts by active consent range using the declared query contract.
# Requirements: RF-32, RF-68
# Policies: P-CONS-01
# Current v4.0.0 result: 3 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?range (COUNT(DISTINCT ?user) AS ?users) WHERE {
  ?user a comon:User ; comon:hasActiveConsentRange ?range .
}
GROUP BY ?range
ORDER BY ?range
```

## BASE-Q32: Model counts by tier

Category: `decision`. Scope: `fog`.

Source: [core/decision/base-q32.rq](../queries/core/decision/base-q32.rq).

Evaluate model counts by tier using the declared query contract.

```sparql
# Type: dashboard
# Purpose: Evaluate model counts by tier using the declared query contract.
# Requirements: RF-13, RF-68
# Policies: P-MODEL-01
# Current v4.0.0 result: 4 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?tier (COUNT(DISTINCT ?model) AS ?models) WHERE {
  ?model a comon:AIModel ; comon:hasModelTier ?tier .
}
GROUP BY ?tier
ORDER BY ?tier
```

## BASE-Q33: Mean resource usage by node type

Category: `observability`. Scope: `authority_key:http://example.org/monitoringcontinuum#UserB`.

Source: [core/observability/base-q33.rq](../queries/core/observability/base-q33.rq).

Evaluate mean resource usage by node type using the declared query contract.

```sparql
# Type: dashboard
# Purpose: Evaluate mean resource usage by node type using the declared query contract.
# Requirements: RF-29, RNF-27
# Policies: P-OPS-05
# Current v4.0.0 result: 5 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?nodeType (AVG(?usage) AS ?avgUsage) (COUNT(?state) AS ?samples) WHERE {
  ?node comon:hasNodeState ?state ; a ?nodeType .
  ?state comon:resourceUsagePercent ?usage .
  ?nodeType rdfs:subClassOf* comon:ComputationalNode .
}
GROUP BY ?nodeType
ORDER BY ?nodeType
```

## BASE-Q34: Nodes covering restricted areas

Category: `topology`. Scope: `fog`.

Source: [core/topology/base-q34.rq](../queries/core/topology/base-q34.rq).

Evaluate nodes covering restricted areas using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate nodes covering restricted areas using the declared query contract.
# Requirements: RF-42, RF-43
# Policies: P-ZONE-01
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?node ?zone WHERE {
  ?zone a comon:RestrictedZone .
  ?node comon:coversArea ?zone .
}
ORDER BY ?zone ?node
```

## BASE-Q35: Failure, evaluation and action chain

Category: `delegation`. Scope: `authorities`.

Source: [core/delegation/base-q35.rq](../queries/core/delegation/base-q35.rq).

Evaluate failure, evaluation and action chain using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate failure, evaluation and action chain using the declared query contract.
# Requirements: RF-20, RF-65, RF-67
# Policies: P-AUD-05, P-AUD-07
# Current v4.0.0 result: 86 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?scenario ?symptom ?node ?policy ?action ?actionType WHERE {
  ?evaluation a comon:EvaluationState ; comon:hasDetectedSymptom ?symptom ; comon:resultedInAction ?action .
  OPTIONAL { ?evaluation comon:partOfScenario ?scenario }
  OPTIONAL { ?evaluation comon:evaluatesNode ?node }
  OPTIONAL { ?evaluation comon:appliedPolicy ?policy }
  OPTIONAL { ?action a ?actionType . FILTER(?actionType != owl:NamedIndividual) }
}
ORDER BY ?scenario ?evaluation ?policy
```

## EXT-Q01: Version and release artifact inventory

Category: `semantic_schema`. Scope: `cloud`.

Source: [core/semantic_schema/ext-q01.rq](../queries/core/semantic_schema/ext-q01.rq).

Evaluate version and release artifact inventory using the declared query contract.

```sparql
# Type: inventory
# Purpose: Evaluate version and release artifact inventory using the declared query contract.
# Requirements: RF-68, RNF-39, RV-01, RV-03
# Policies: P-VAL-01, P-VAL-04
# Current v4.0.0 result: 6 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?ontology ?versionInfo ?versionIRI ?artifact ?artifactType ?identifier ?artifactVersion ?status WHERE {
  VALUES ?ontology { <http://example.org/monitoringcontinuum> }
  OPTIONAL { ?ontology owl:versionInfo ?versionInfo }
  OPTIONAL { ?ontology owl:versionIRI ?versionIRI }
  OPTIONAL {
    VALUES ?artifactType {
      comon:OntologyArtifact comon:RequirementsArtifact comon:PolicyArtifact
      comon:ScenarioArtifact comon:QueryCatalog comon:AcceptanceProfile
    }
    ?artifact a ?artifactType .
    OPTIONAL { ?artifact comon:artifactIdentifier ?identifier }
    OPTIONAL { ?artifact comon:artifactVersion ?artifactVersion }
    OPTIONAL { ?artifact comon:artifactStatus ?status }
  }
}
ORDER BY ?artifactType ?artifact
```

## EXT-Q02: Functional, non-functional and validation requirement coverage

Category: `semantic_schema`. Scope: `cloud`.

Source: [core/semantic_schema/ext-q02.rq](../queries/core/semantic_schema/ext-q02.rq).

Evaluate functional, non-functional and validation requirement coverage using the declared query contract.

```sparql
# Type: dashboard
# Purpose: Evaluate functional, non-functional and validation requirement coverage using the declared query contract.
# Requirements: RV-04, RF-68
# Policies: P-VAL-06
# Current v4.0.0 result: 3 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?requirementType (COUNT(DISTINCT ?r) AS ?count) WHERE {
  VALUES ?requirementType {
    comon:FunctionalRequirement comon:NonFunctionalRequirement comon:ValidationRequirement
  }
  ?r a ?requirementType .
}
GROUP BY ?requirementType
ORDER BY ?requirementType
```

## EXT-Q03: Complete policy inventory

Category: `policy_governance`. Scope: `cloud`.

Source: [core/policy_governance/ext-q03.rq](../queries/core/policy_governance/ext-q03.rq).

Evaluate complete policy inventory using the declared query contract.

```sparql
# Type: inventory
# Purpose: Evaluate complete policy inventory using the declared query contract.
# Requirements: RF-39, RF-40, RF-70
# Policies: P-GOV-01, P-GOV-04
# Current v4.0.0 result: 79 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?policy ?id ?category ?type ?version ?statement WHERE {
  ?policy a comon:Policy ; comon:policyIdentifier ?id .
  OPTIONAL { ?policy comon:belongsToPolicyCategory ?category }
  OPTIONAL { ?policy comon:hasPolicyType ?type }
  OPTIONAL { ?policy comon:policyVersion ?version }
  OPTIONAL { ?policy comon:hasPolicyStatement ?statement }
}
ORDER BY ?id
```

## EXT-Q04: Complete mechanism inventory

Category: `policy_governance`. Scope: `cloud`.

Source: [core/policy_governance/ext-q04.rq](../queries/core/policy_governance/ext-q04.rq).

Evaluate complete mechanism inventory using the declared query contract.

```sparql
# Type: inventory
# Purpose: Evaluate complete mechanism inventory using the declared query contract.
# Requirements: RV-04
# Policies: P-VAL-06
# Current v4.0.0 result: 55 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?mechanism ?id ?description (GROUP_CONCAT(DISTINCT STR(?policy); separator=", ") AS ?policies) WHERE {
  ?mechanism a comon:MechanismSpecification ; comon:mechanismIdentifier ?id .
  OPTIONAL { ?mechanism comon:mechanismDescription ?description }
  OPTIONAL { ?mechanism comon:supportsPolicy ?policy }
}
GROUP BY ?mechanism ?id ?description
ORDER BY ?id
```

## EXT-Q05: Scenario S1-S17 inventory

Category: `semantic_schema`. Scope: `cloud`.

Source: [core/semantic_schema/ext-q05.rq](../queries/core/semantic_schema/ext-q05.rq).

Evaluate scenario S1-S17 inventory using the declared query contract.

```sparql
# Type: inventory
# Purpose: Evaluate scenario S1-S17 inventory using the declared query contract.
# Requirements: RF-31, RF-72, RV-03
# Policies: P-VAL-07
# Current v4.0.0 result: 17 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?scenario ?id ?artifact
       (GROUP_CONCAT(DISTINCT STR(?policy); separator=", ") AS ?policies)
       (GROUP_CONCAT(DISTINCT STR(?mechanism); separator=", ") AS ?mechanisms) WHERE {
  ?scenario a comon:Scenario ; comon:scenarioIdentifier ?id .
  OPTIONAL { ?scenario comon:definedInArtifact ?artifact }
  OPTIONAL { ?scenario comon:scenarioPolicy ?policy }
  OPTIONAL { ?scenario comon:scenarioMechanism ?mechanism }
}
GROUP BY ?scenario ?id ?artifact
ORDER BY ?id
```

## EXT-Q06: Policy categories

Category: `semantic_schema`. Scope: `cloud`.

Source: [core/semantic_schema/ext-q06.rq](../queries/core/semantic_schema/ext-q06.rq).

Evaluate policy categories using the declared query contract.

```sparql
# Type: inventory
# Purpose: Evaluate policy categories using the declared query contract.
# Requirements: RF-39, RF-40
# Policies: P-GOV-01
# Current v4.0.0 result: 12 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?category ?code ?label WHERE {
  ?category a comon:PolicyCategory .
  OPTIONAL { ?category comon:categoryCode ?code }
  OPTIONAL { ?category rdfs:label ?label }
}
ORDER BY ?code
```

## EXT-Q07: Relationships between policy categories

Category: `policy_governance`. Scope: `cloud`.

Source: [core/policy_governance/ext-q07.rq](../queries/core/policy_governance/ext-q07.rq).

Evaluate relationships between policy categories using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate relationships between policy categories using the declared query contract.
# Requirements: RNF-22, RV-04
# Policies: P-GOV-03
# Current v4.0.0 result: 67 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?relation ?source ?target ?relationType ?code ?strategy WHERE {
  ?relation a comon:PolicyCategoryRelation ; comon:relationSourceCategory ?source ; comon:relationTargetCategory ?target ; comon:hasPolicyRelationType ?relationType .
  OPTIONAL { ?relationType comon:relationCode ?code }
  OPTIONAL { ?relation comon:usesResolutionStrategy ?strategy }
}
ORDER BY ?source ?target
```

## EXT-Q08: Requirement, policy and mechanism traceability

Category: `policy_governance`. Scope: `cloud`.

Source: [core/policy_governance/ext-q08.rq](../queries/core/policy_governance/ext-q08.rq).

Evaluate requirement, policy and mechanism traceability using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate requirement, policy and mechanism traceability using the declared query contract.
# Requirements: RV-04, RNF-39
# Policies: P-VAL-06
# Current v4.0.0 result: 1089 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?requirement ?rid ?rtype ?policy ?mechanism WHERE {
  VALUES ?rtype {
    comon:FunctionalRequirement comon:NonFunctionalRequirement comon:ValidationRequirement
  }
  ?requirement a ?rtype ; comon:requirementIdentifier ?rid .
  OPTIONAL { ?requirement comon:tracedToPolicy ?policy }
  OPTIONAL { ?requirement comon:tracedToMechanism ?mechanism }
}
ORDER BY ?rid ?policy ?mechanism
```

## EXT-Q09: Review: requirements without explicit policies or mechanisms

Category: `policy_governance`. Scope: `cloud`.

Source: [core/policy_governance/ext-q09.rq](../queries/core/policy_governance/ext-q09.rq).

Evaluate review: requirements without explicit policies or mechanisms using the declared query contract.

```sparql
# Type: review
# Purpose: Evaluate review: requirements without explicit policies or mechanisms using the declared query contract.
# Requirements: RV-04
# Policies: P-VAL-06
# Current v4.0.0 result: 6 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?requirement ?rid WHERE {
  ?requirement a comon:Requirement ; comon:requirementIdentifier ?rid .
  FILTER NOT EXISTS { ?requirement comon:tracedToPolicy ?p }
  FILTER NOT EXISTS { ?requirement comon:tracedToMechanism ?m }
}
ORDER BY ?rid
```

## EXT-Q10: Violation: incomplete policies or mechanisms

Category: `policy_governance`. Scope: `cloud`.

Source: [core/policy_governance/ext-q10.rq](../queries/core/policy_governance/ext-q10.rq).

Evaluate violation: incomplete policies or mechanisms using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: incomplete policies or mechanisms using the declared query contract.
# Requirements: RF-39, RF-40, RNF-20
# Policies: P-GOV-01, P-GOV-04
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?resource ?kind ?missing WHERE {
  {
    ?resource a comon:Policy . BIND("Policy" AS ?kind)
    VALUES (?prop ?missing) {
      (comon:policyIdentifier "policyIdentifier")
      (comon:belongsToPolicyCategory "belongsToPolicyCategory")
      (comon:hasPolicyType "hasPolicyType")
      (comon:policyVersion "policyVersion")
      (comon:hasPolicyStatement "hasPolicyStatement")
      (comon:recommendedMechanism "recommendedMechanism")
    }
    FILTER NOT EXISTS { ?resource ?prop ?v }
  }
  UNION
  {
    ?resource a comon:MechanismSpecification . BIND("Mechanism" AS ?kind)
    VALUES (?prop ?missing) {
      (comon:mechanismIdentifier "mechanismIdentifier")
      (comon:mechanismDescription "mechanismDescription")
      (comon:supportsPolicy "supportsPolicy")
    }
    FILTER NOT EXISTS { ?resource ?prop ?v }
  }
}
ORDER BY ?kind ?resource ?missing
```

## EXT-Q11: Consent record report

Category: `identity_consent`. Scope: `authorities`.

Source: [core/identity_consent/ext-q11.rq](../queries/core/identity_consent/ext-q11.rq).

Evaluate consent record report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate consent record report using the declared query contract.
# Requirements: RF-32, RF-35
# Policies: P-CONS-01, P-CONS-04
# Current v4.0.0 result: 25 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?record ?user ?range ?purpose ?dataCategory ?from ?to WHERE {
  ?record a comon:ConsentRecord ; comon:consentSubject ?user ; comon:hasConsentRange ?range .
  OPTIONAL { ?record comon:hasProcessingPurpose ?purpose }
  OPTIONAL { ?record comon:hasAuthorizedDataCategory ?dataCategory }
  OPTIONAL { ?record comon:validFrom ?from }
  OPTIONAL { ?record comon:validTo ?to }
}
ORDER BY ?user ?record ?purpose ?dataCategory
```

## EXT-Q12: Semantic contract report

Category: `identity_consent`. Scope: `authorities`.

Source: [core/identity_consent/ext-q12.rq](../queries/core/identity_consent/ext-q12.rq).

Evaluate semantic contract report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate semantic contract report using the declared query contract.
# Requirements: RF-33, RF-34, RF-41
# Policies: P-CONS-02, P-CONS-03, P-GOV-02
# Current v4.0.0 result: 28 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?contract ?user ?range ?purpose ?policy ?from ?to WHERE {
  ?contract a comon:SemanticContract ; comon:contractSubject ?user ; comon:hasConsentRange ?range .
  OPTIONAL { ?contract comon:hasProcessingPurpose ?purpose }
  OPTIONAL { ?contract comon:governedBy ?policy }
  OPTIONAL { ?contract comon:validFrom ?from }
  OPTIONAL { ?contract comon:validTo ?to }
}
ORDER BY ?user ?contract ?purpose ?policy
```

## EXT-Q13: Violation: incomplete consent records

Category: `identity_consent`. Scope: `authorities`.

Source: [core/identity_consent/ext-q13.rq](../queries/core/identity_consent/ext-q13.rq).

Evaluate violation: incomplete consent records using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: incomplete consent records using the declared query contract.
# Requirements: RF-32, RF-35
# Policies: P-CONS-01
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?record ?missing WHERE {
  ?record a comon:ConsentRecord .
  VALUES (?prop ?missing) {
    (comon:consentSubject "consentSubject")
    (comon:hasConsentRange "hasConsentRange")
    (comon:hasProcessingPurpose "hasProcessingPurpose")
    (comon:hasAuthorizedDataCategory "hasAuthorizedDataCategory")
    (comon:validFrom "validFrom")
  }
  FILTER NOT EXISTS { ?record ?prop ?v }
}
ORDER BY ?record ?missing
```

## EXT-Q14: Violation: incomplete semantic contracts

Category: `identity_consent`. Scope: `authorities`.

Source: [core/identity_consent/ext-q14.rq](../queries/core/identity_consent/ext-q14.rq).

Evaluate violation: incomplete semantic contracts using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: incomplete semantic contracts using the declared query contract.
# Requirements: RF-33, RF-34
# Policies: P-CONS-02, P-CONS-03
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?contract ?missing WHERE {
  ?contract a comon:SemanticContract .
  VALUES (?prop ?missing) {
    (comon:contractSubject "contractSubject")
    (comon:hasConsentRange "hasConsentRange")
    (comon:hasProcessingPurpose "hasProcessingPurpose")
    (comon:governedBy "governedBy")
    (comon:validFrom "validFrom")
  }
  FILTER NOT EXISTS { ?contract ?prop ?v }
}
ORDER BY ?contract ?missing
```

## EXT-Q15: Violation: overlapping contracts for a user and purpose

Category: `identity_consent`. Scope: `authorities`.

Source: [core/identity_consent/ext-q15.rq](../queries/core/identity_consent/ext-q15.rq).

Evaluate violation: overlapping contracts for a user and purpose using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: overlapping contracts for a user and purpose using the declared query contract.
# Requirements: RF-33, RNF-22
# Policies: P-CONS-02
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?user ?purpose ?c1 ?c2 WHERE {
  ?c1 a comon:SemanticContract ; comon:contractSubject ?user ; comon:hasProcessingPurpose ?purpose ; comon:validFrom ?f1 .
  ?c2 a comon:SemanticContract ; comon:contractSubject ?user ; comon:hasProcessingPurpose ?purpose ; comon:validFrom ?f2 .
  FILTER(STR(?c1) < STR(?c2))
  OPTIONAL { ?c1 comon:validTo ?t1 }
  OPTIONAL { ?c2 comon:validTo ?t2 }
  FILTER((!BOUND(?t1) || ?f2 < ?t1) && (!BOUND(?t2) || ?f1 < ?t2))
}
ORDER BY ?user ?purpose
```

## EXT-Q16: Violation: active consent range without a supporting record

Category: `identity_consent`. Scope: `authorities`.

Source: [core/identity_consent/ext-q16.rq](../queries/core/identity_consent/ext-q16.rq).

Evaluate violation: active consent range without a supporting record using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: active consent range without a supporting record using the declared query contract.
# Requirements: RF-35
# Policies: P-CONS-01, P-CONS-04
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?user ?activeRange WHERE {
  ?user a comon:User ; comon:hasActiveConsentRange ?activeRange .
  FILTER NOT EXISTS {
    ?user comon:hasConsentRecord ?record .
    ?record comon:hasConsentRange ?activeRange .
  }
}
ORDER BY ?user
```

## EXT-Q17: Effective authorization report

Category: `identity_consent`. Scope: `authorities`.

Source: [core/identity_consent/ext-q17.rq](../queries/core/identity_consent/ext-q17.rq).

Evaluate effective authorization report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate effective authorization report using the declared query contract.
# Requirements: RF-35, RF-36, RF-66
# Policies: P-CONS-04, P-GOV-03
# Current v4.0.0 result: 8 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?authorization ?outcome ?effectiveRange ?record ?contract ?zone ?from WHERE {
  ?evaluation a comon:EvaluationState ; comon:hasAuthorizationDecision ?authorization .
  ?authorization a comon:AuthorizationDecision .
  OPTIONAL { ?authorization comon:hasAuthorizationOutcome ?outcome }
  OPTIONAL { ?authorization comon:hasEffectiveConsentRange ?effectiveRange }
  OPTIONAL { ?authorization comon:basedOnConsentRecord ?record }
  OPTIONAL { ?authorization comon:basedOnContract ?contract }
  OPTIONAL { ?authorization comon:basedOnZone ?zone }
  OPTIONAL { ?authorization comon:validFrom ?from }
}
ORDER BY ?evaluation
```

## EXT-Q18: Violation: incomplete effective authorization

Category: `identity_consent`. Scope: `authorities`.

Source: [core/identity_consent/ext-q18.rq](../queries/core/identity_consent/ext-q18.rq).

Evaluate violation: incomplete effective authorization using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: incomplete effective authorization using the declared query contract.
# Requirements: RF-35, RF-36
# Policies: P-CONS-04
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?authorization ?missing WHERE {
  ?authorization a comon:AuthorizationDecision .
  VALUES (?prop ?missing) {
    (comon:hasAuthorizationOutcome "hasAuthorizationOutcome")
    (comon:hasEffectiveConsentRange "hasEffectiveConsentRange")
    (comon:basedOnConsentRecord "basedOnConsentRecord")
    (comon:basedOnContract "basedOnContract")
    (comon:basedOnZone "basedOnZone")
    (comon:validFrom "validFrom")
  }
  FILTER NOT EXISTS { ?authorization ?prop ?v }
}
ORDER BY ?authorization ?missing
```

## EXT-Q19: Violation: authorization exceeds consent or contract

Category: `identity_consent`. Scope: `authorities`.

Source: [core/identity_consent/ext-q19.rq](../queries/core/identity_consent/ext-q19.rq).

Evaluate violation: authorization exceeds consent or contract using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: authorization exceeds consent or contract using the declared query contract.
# Requirements: RF-35, RF-36
# Policies: P-CONS-04, P-GOV-03
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?authorization ?effective ?consentRange ?contractRange WHERE {
  VALUES (?effective ?eLevel) { (comon:RangeDenied 0) (comon:RangeLocalOnly 1) (comon:RangeCommunityAgg 2) (comon:RangeGlobalAgg 3) }
  VALUES (?consentRange ?cLevel) { (comon:RangeDenied 0) (comon:RangeLocalOnly 1) (comon:RangeCommunityAgg 2) (comon:RangeGlobalAgg 3) }
  VALUES (?contractRange ?kLevel) { (comon:RangeDenied 0) (comon:RangeLocalOnly 1) (comon:RangeCommunityAgg 2) (comon:RangeGlobalAgg 3) }
  ?authorization a comon:AuthorizationDecision ; comon:hasEffectiveConsentRange ?effective ; comon:basedOnConsentRecord/comon:hasConsentRange ?consentRange ; comon:basedOnContract/comon:hasConsentRange ?contractRange .
  FILTER(?eLevel > ?cLevel || ?eLevel > ?kLevel)
}
```

## EXT-Q20: Violation: evaluation without granted authorization

Category: `identity_consent`. Scope: `authorities`.

Source: [core/identity_consent/ext-q20.rq](../queries/core/identity_consent/ext-q20.rq).

Evaluate violation: evaluation without granted authorization using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: evaluation without granted authorization using the declared query contract.
# Requirements: RF-36, RF-66, RNF-28
# Policies: P-CONS-04, P-AUD-06
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation WHERE {
  ?evaluation a comon:EvaluationState .
  FILTER NOT EXISTS { ?evaluation comon:hasAuthorizationDecision/comon:hasAuthorizationOutcome comon:AuthorizationGranted }
}
ORDER BY ?evaluation
```

## EXT-Q21: Required minimum consent range inventory

Category: `identity_consent`. Scope: `authorities`.

Source: [core/identity_consent/ext-q21.rq](../queries/core/identity_consent/ext-q21.rq).

Evaluate required minimum consent range inventory using the declared query contract.

```sparql
# Type: inventory
# Purpose: Evaluate required minimum consent range inventory using the declared query contract.
# Requirements: RF-37
# Policies: P-CONS-05
# Current v4.0.0 result: 11 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?resource ?type ?requiredRange WHERE {
  ?resource comon:requiresConsentRange ?requiredRange .
  OPTIONAL { ?resource a ?type . FILTER(?type != owl:NamedIndividual) }
}
ORDER BY ?resource ?type
```

## EXT-Q22: Violation: raw physiological observations outside local scope

Category: `security_identity`. Scope: `authorities`.

Source: [domain/wellbeing/security_identity/ext-q22.rq](../queries/domain/wellbeing/security_identity/ext-q22.rq).

Evaluate violation: raw physiological observations outside local scope using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: raw physiological observations outside local scope using the declared query contract.
# Requirements: RF-10, RF-60, RNF-17
# Policies: P-DATA-01, P-ZONE-01
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?raw ?destination ?via WHERE {
  VALUES ?rawType { comon:PhysiologicalObservation comon:SleepObservation }
  ?raw a ?rawType .
  {
    ?raw comon:sentToNode ?destination . BIND("sentToNode" AS ?via)
  }
  UNION
  {
    ?transfer a comon:TransferEvent ; comon:carriesData ?raw ; comon:transferDestination ?destination . BIND("TransferEvent" AS ?via)
  }
  VALUES ?destType { comon:EdgeNode comon:FogNode comon:CloudNode }
  ?destination a ?destType .
}
ORDER BY ?raw
```

## EXT-Q23: External data transfer report

Category: `data_lifecycle`. Scope: `authorities`.

Source: [core/data_lifecycle/ext-q23.rq](../queries/core/data_lifecycle/ext-q23.rq).

Evaluate external data transfer report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate external data transfer report using the declared query contract.
# Requirements: RF-09, RF-27, RF-61
# Policies: P-DATA-02, P-DATA-03, P-DATA-10
# Current v4.0.0 result: 3 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?transfer ?data ?category ?sensitivity ?criticality ?source ?destination ?identifier ?security ?from WHERE {
  ?transfer a comon:TransferEvent ; comon:carriesData ?data ; comon:transferSource ?source ; comon:transferDestination ?destination .
  OPTIONAL { ?data comon:hasDataCategory ?category }
  OPTIONAL { ?data comon:hasDataSensitivity ?sensitivity }
  OPTIONAL { ?data comon:hasDataCriticality ?criticality }
  OPTIONAL { ?transfer comon:usesIdentifier ?identifier }
  OPTIONAL { ?transfer comon:appliedSecurityMechanism ?security }
  OPTIONAL { ?transfer comon:validFrom ?from }
}
ORDER BY ?from ?transfer
```

## EXT-Q24: Data context report

Category: `data_lifecycle`. Scope: `authorities`.

Source: [core/data_lifecycle/ext-q24.rq](../queries/core/data_lifecycle/ext-q24.rq).

Evaluate data context report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate data context report using the declared query contract.
# Requirements: RF-09, RF-30
# Policies: P-DATA-10
# Current v4.0.0 result: 2 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?data ?context ?deviceState ?nodeState ?processingLevel ?purpose ?zone ?from ?note WHERE {
  ?data comon:hasDataContext ?context .
  ?context a comon:DataContext .
  OPTIONAL { ?context comon:contextDeviceState ?deviceState }
  OPTIONAL { ?context comon:contextNodeState ?nodeState }
  OPTIONAL { ?context comon:contextProcessingLevel ?processingLevel }
  OPTIONAL { ?context comon:contextPurpose ?purpose }
  OPTIONAL { ?context comon:contextZone ?zone }
  OPTIONAL { ?context comon:validFrom ?from }
  OPTIONAL { ?context comon:migrationNote ?note }
}
ORDER BY ?data
```

## EXT-Q25: Violation: incomplete data context

Category: `data_lifecycle`. Scope: `authorities`.

Source: [domain/wellbeing/data_lifecycle/ext-q25.rq](../queries/domain/wellbeing/data_lifecycle/ext-q25.rq).

Evaluate violation: incomplete data context using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: incomplete data context using the declared query contract.
# Requirements: RF-09
# Policies: P-DATA-10
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?data ?context ?missing WHERE {
  VALUES ?dataType { comon:PhysiologicalParametrizedData comon:SleepParametrizedData }
  ?data a ?dataType .
  {
    FILTER NOT EXISTS { ?data comon:hasDataContext ?anyContext }
    VALUES (?prop ?missing) {
      (comon:contextDeviceState "contextDeviceState")
      (comon:contextNodeState "contextNodeState")
      (comon:contextProcessingLevel "contextProcessingLevel")
      (comon:contextPurpose "contextPurpose")
      (comon:contextZone "contextZone")
      (comon:validFrom "validFrom")
    }
  }
  UNION
  {
    ?data comon:hasDataContext ?context .
    VALUES (?prop ?missing) {
      (comon:contextDeviceState "contextDeviceState")
      (comon:contextNodeState "contextNodeState")
      (comon:contextProcessingLevel "contextProcessingLevel")
      (comon:contextPurpose "contextPurpose")
      (comon:contextZone "contextZone")
      (comon:validFrom "validFrom")
    }
    FILTER NOT EXISTS { ?context ?prop ?v }
  }
}
ORDER BY ?data ?missing
```

## EXT-Q26: Identifier inventory

Category: `security_identity`. Scope: `authorities`.

Source: [core/security_identity/ext-q26.rq](../queries/core/security_identity/ext-q26.rq).

Evaluate identifier inventory using the declared query contract.

```sparql
# Type: inventory
# Purpose: Evaluate identifier inventory using the declared query contract.
# Requirements: RF-61, RNF-19
# Policies: P-DATA-02
# Current v4.0.0 result: 4 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?user ?identifier ?identifierType ?scope ?value WHERE {
  VALUES ?identifierType {
    comon:PseudonymousIdentifier comon:AnonymousIdentifier comon:DirectIdentifier
  }
  ?user a comon:User ; comon:hasIdentifier ?identifier .
  ?identifier a ?identifierType .
  OPTIONAL { ?identifier comon:identifierScope ?scope }
  OPTIONAL { ?identifier comon:identifierValue ?value }
}
ORDER BY ?user ?identifier
```

## EXT-Q27: Violation: external transfer without a safe identifier

Category: `security_identity`. Scope: `authorities`.

Source: [core/security_identity/ext-q27.rq](../queries/core/security_identity/ext-q27.rq).

Evaluate violation: external transfer without a safe identifier using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: external transfer without a safe identifier using the declared query contract.
# Requirements: RF-61, RNF-17
# Policies: P-DATA-02
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?transfer ?destination ?identifier WHERE {
  ?transfer a comon:TransferEvent ; comon:transferDestination ?destination .
  ?destination a ?destType .
  FILTER(?destType IN (comon:EdgeNode,comon:FogNode,comon:CloudNode))
  OPTIONAL { ?transfer comon:usesIdentifier ?identifier }
  FILTER(!BOUND(?identifier) || NOT EXISTS { ?identifier a ?safeType . FILTER(?safeType IN (comon:PseudonymousIdentifier,comon:AnonymousIdentifier)) })
}
ORDER BY ?transfer
```

## EXT-Q28: Violation: direct identifiers in external flows

Category: `security_identity`. Scope: `authorities`.

Source: [core/security_identity/ext-q28.rq](../queries/core/security_identity/ext-q28.rq).

Evaluate violation: direct identifiers in external flows using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: direct identifiers in external flows using the declared query contract.
# Requirements: RF-61, RNF-17
# Policies: P-DATA-02
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?transfer ?identifier ?destination WHERE {
  ?transfer a comon:TransferEvent ; comon:usesIdentifier ?identifier ; comon:transferDestination ?destination .
  ?identifier a comon:DirectIdentifier .
  ?destination a ?destType .
  FILTER(?destType IN (comon:EdgeNode,comon:FogNode,comon:CloudNode))
}
```

## EXT-Q29: Encryption baseline report

Category: `security_identity`. Scope: `cloud`.

Source: [core/security_identity/ext-q29.rq](../queries/core/security_identity/ext-q29.rq).

Evaluate encryption baseline report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate encryption baseline report using the declared query contract.
# Requirements: RNF-15
# Policies: P-DATA-03
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?mechanism ?version ?inTransit ?atRest WHERE {
  ?mechanism a comon:EncryptionMechanism .
  OPTIONAL { ?mechanism comon:securityBaselineVersion ?version }
  OPTIONAL { ?mechanism comon:protectsInTransit ?inTransit }
  OPTIONAL { ?mechanism comon:protectsAtRest ?atRest }
}
ORDER BY ?mechanism
```

## EXT-Q30: Violation: sensitive transfer without encryption in transit

Category: `security_identity`. Scope: `cloud`.

Source: [core/security_identity/ext-q30.rq](../queries/core/security_identity/ext-q30.rq).

Evaluate violation: sensitive transfer without encryption in transit using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: sensitive transfer without encryption in transit using the declared query contract.
# Requirements: RNF-15
# Policies: P-DATA-03
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?transfer ?data WHERE {
  ?transfer a comon:TransferEvent ; comon:carriesData ?data .
  ?data comon:hasDataSensitivity comon:SensitiveData .
  FILTER NOT EXISTS { ?transfer comon:appliedSecurityMechanism ?m . ?m comon:protectsInTransit true }
}
```

## EXT-Q31: Buffer and retention report

Category: `data_lifecycle`. Scope: `authorities`.

Source: [core/data_lifecycle/ext-q31.rq](../queries/core/data_lifecycle/ext-q31.rq).

Evaluate buffer and retention report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate buffer and retention report using the declared query contract.
# Requirements: RF-08, RNF-12
# Policies: P-DATA-05, P-DATA-07
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?record ?type ?data ?from ?to ?security WHERE {
  VALUES ?type { comon:BufferRecord comon:RetentionEvent }
  ?record a ?type .
  OPTIONAL { ?record comon:carriesData ?data }
  OPTIONAL { ?record comon:validFrom ?from }
  OPTIONAL { ?record comon:validTo ?to }
  OPTIONAL { ?record comon:appliedSecurityMechanism ?security }
}
ORDER BY ?record
```

## EXT-Q32: Violation: sensitive buffer without protection at rest

Category: `data_lifecycle`. Scope: `authorities`.

Source: [core/data_lifecycle/ext-q32.rq](../queries/core/data_lifecycle/ext-q32.rq).

Evaluate violation: sensitive buffer without protection at rest using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: sensitive buffer without protection at rest using the declared query contract.
# Requirements: RNF-15, RNF-12
# Policies: P-DATA-03, P-DATA-05
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?buffer ?data WHERE {
  ?buffer a comon:BufferRecord ; comon:carriesData ?data .
  ?data comon:hasDataSensitivity comon:SensitiveData .
  FILTER NOT EXISTS { ?buffer comon:appliedSecurityMechanism ?m . ?m comon:protectsAtRest true }
}
```

## EXT-Q33: Replication and synchronization report

Category: `data_lifecycle`. Scope: `authorities`.

Source: [core/data_lifecycle/ext-q33.rq](../queries/core/data_lifecycle/ext-q33.rq).

Evaluate replication and synchronization report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate replication and synchronization report using the declared query contract.
# Requirements: RF-19, RNF-13
# Policies: P-DATA-08
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?event ?type ?source ?target ?replica ?version ?idempotencyKey ?from WHERE {
  VALUES ?type { comon:ReplicationEvent comon:SynchronizationEvent }
  ?event a ?type .
  OPTIONAL { ?event comon:replicationSource ?source }
  OPTIONAL { ?event comon:replicationTarget ?target }
  OPTIONAL { ?event comon:replicaOf ?replica }
  OPTIONAL { ?event comon:replicationVersion ?version }
  OPTIONAL { ?event comon:idempotencyKey ?idempotencyKey }
  OPTIONAL { ?event comon:validFrom ?from }
}
ORDER BY ?event
```

## EXT-Q34: Violation: replication without versioning or idempotency

Category: `data_lifecycle`. Scope: `authorities`.

Source: [core/data_lifecycle/ext-q34.rq](../queries/core/data_lifecycle/ext-q34.rq).

Evaluate violation: replication without versioning or idempotency using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: replication without versioning or idempotency using the declared query contract.
# Requirements: RF-19, RNF-13
# Policies: P-DATA-08, P-ADAPT-08
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?event ?missing WHERE {
  VALUES ?type { comon:ReplicationEvent comon:SynchronizationEvent }
  ?event a ?type .
  VALUES (?prop ?missing) { (comon:replicationVersion "replicationVersion") (comon:idempotencyKey "idempotencyKey") }
  FILTER NOT EXISTS { ?event ?prop ?v }
}
ORDER BY ?event ?missing
```

## EXT-Q35: Data criticality and priority report

Category: `data_lifecycle`. Scope: `authorities`.

Source: [core/data_lifecycle/ext-q35.rq](../queries/core/data_lifecycle/ext-q35.rq).

Evaluate data criticality and priority report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate data criticality and priority report using the declared query contract.
# Requirements: RF-28
# Policies: P-DATA-09
# Current v4.0.0 result: 6 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?data ?category ?criticality ?redundant WHERE {
  ?data comon:hasDataCategory ?category .
  OPTIONAL { ?data comon:hasDataCriticality ?criticality }
  OPTIONAL { ?data comon:isRedundant ?redundant }
}
ORDER BY ?criticality ?data
```

## EXT-Q36: Restricted area report

Category: `context_zones`. Scope: `authority_key:http://example.org/monitoringcontinuum#UserD`.

Source: [core/context_zones/ext-q36.rq](../queries/core/context_zones/ext-q36.rq).

Evaluate restricted area report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate restricted area report using the declared query contract.
# Requirements: RF-42, RF-43
# Policies: P-ZONE-01
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?zone ?user ?evaluation ?tier ?action WHERE {
  ?zone a comon:RestrictedZone .
  OPTIONAL { ?user a comon:User ; comon:locatedInZone ?zone }
  OPTIONAL { ?evaluation a comon:EvaluationState ; comon:evaluationZone ?zone ; comon:selectedModelTier ?tier . OPTIONAL { ?evaluation comon:resultedInAction ?action } }
}
ORDER BY ?zone ?user ?evaluation
```

## EXT-Q37: Violation: external processing or transfer in restricted areas

Category: `context_zones`. Scope: `authorities`.

Source: [domain/wellbeing/context_zones/ext-q37.rq](../queries/domain/wellbeing/context_zones/ext-q37.rq).

Evaluate violation: external processing or transfer in restricted areas using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: external processing or transfer in restricted areas using the declared query contract.
# Requirements: RF-42, RF-43, RF-60
# Policies: P-ZONE-01, P-GOV-03, P-ZONE-04
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?subject ?violationType ?destinationOrTier WHERE {
  {
    ?evaluation a comon:EvaluationState ; comon:evaluationZone ?zone ; comon:selectedModelTier ?tier .
    ?zone a comon:RestrictedZone .
    FILTER(?tier IN (comon:EdgeModelTier,comon:FogModelTier,comon:CloudModelTier))
    BIND(?evaluation AS ?subject) BIND("external-tier" AS ?violationType) BIND(?tier AS ?destinationOrTier)
  }
  UNION
  {
    ?user a comon:User ; comon:locatedInZone ?zone . ?zone a comon:RestrictedZone .
    ?user (comon:hasWearable|comon:hasMobileDevice) ?device .
    ?transfer a comon:TransferEvent ; comon:transferSource ?device ; comon:transferDestination ?dest .
    ?dest a ?destType . FILTER(?destType IN (comon:EdgeNode,comon:FogNode,comon:CloudNode))
    BIND(?transfer AS ?subject) BIND("external-transfer" AS ?violationType) BIND(?dest AS ?destinationOrTier)
  }
}
ORDER BY ?subject
```

## EXT-Q38: Rural area and transmission window report

Category: `context_zones`. Scope: `authorities`.

Source: [domain/wellbeing/context_zones/ext-q38.rq](../queries/domain/wellbeing/context_zones/ext-q38.rq).

Evaluate rural area and transmission window report using the declared query contract.

```sparql
# Type: review
# Purpose: Evaluate rural area and transmission window report using the declared query contract.
# Requirements: RF-08, RF-27
# Policies: P-ZONE-02, P-DATA-07
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?user ?zone ?device ?state ?connection ?retention ?sync WHERE {
  ?user a comon:User ; comon:locatedInZone ?zone . ?zone a comon:RuralZone .
  OPTIONAL { ?user (comon:hasWearable|comon:hasMobileDevice) ?device . ?device comon:hasDeviceState ?state . OPTIONAL { ?state comon:hasConnectionStatus ?connection } }
  OPTIONAL { ?retention a comon:RetentionEvent ; comon:partOfScenario ?scenario . FILTER(?scenario = comon:S7) }
  OPTIONAL { ?sync a comon:SynchronizationEvent ; comon:partOfScenario ?scenario2 . FILTER(?scenario2 = comon:S7) }
}
ORDER BY ?user ?device
```

## EXT-Q39: Conditional urban processing report

Category: `context_zones`. Scope: `authorities`.

Source: [core/context_zones/ext-q39.rq](../queries/core/context_zones/ext-q39.rq).

Evaluate conditional urban processing report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate conditional urban processing report using the declared query contract.
# Requirements: RF-42
# Policies: P-ZONE-03, P-CONS-04
# Current v4.0.0 result: 5 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?zone ?authorization ?effectiveRange ?tier ?node WHERE {
  ?evaluation a comon:EvaluationState ; comon:evaluationZone ?zone ; comon:hasAuthorizationDecision ?authorization ; comon:selectedModelTier ?tier .
  ?zone a comon:UrbanZone .
  ?authorization comon:hasEffectiveConsentRange ?effectiveRange .
  OPTIONAL { ?evaluation comon:evaluatesNode ?node }
}
ORDER BY ?evaluation
```

## EXT-Q40: Node state and reproducible trust report

Category: `trust`. Scope: `fog`.

Source: [core/trust/ext-q40.rq](../queries/core/trust/ext-q40.rq).

Evaluate node state and reproducible trust report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate node state and reproducible trust report using the declared query contract.
# Requirements: RF-45, RF-49, RNF-32
# Policies: P-NODE-03, P-NODE-04
# Current v4.0.0 result: 7 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?node ?state ?trustAssessment ?score ?ruleVersion ?windowStart ?windowEnd ?configStatus WHERE {
  ?node comon:hasNodeState ?state . ?state a comon:NodeState .
  OPTIONAL {
    ?state comon:hasTrustAssessment ?trustAssessment .
    OPTIONAL { ?trustAssessment comon:hasTrustScore ?score }
    OPTIONAL { ?trustAssessment comon:trustRuleVersion ?ruleVersion }
    OPTIONAL { ?trustAssessment comon:trustWindowStart ?windowStart }
    OPTIONAL { ?trustAssessment comon:trustWindowEnd ?windowEnd }
    OPTIONAL { ?trustAssessment comon:configurationStatus ?configStatus }
  }
}
ORDER BY ?node ?state
```

## EXT-Q41: Violation: node state without eligibility fields

Category: `trust`. Scope: `fog`.

Source: [core/trust/ext-q41.rq](../queries/core/trust/ext-q41.rq).

Evaluate violation: node state without eligibility fields using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: node state without eligibility fields using the declared query contract.
# Requirements: RF-05, RF-47
# Policies: P-NODE-01, P-NODE-02
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?state ?missing WHERE {
  ?state a comon:NodeState .
  VALUES (?prop ?missing) {
    (comon:hasAvailability "hasAvailability")
    (comon:hasWorkload "hasWorkload")
    (comon:hasCommunication "hasCommunication")
    (comon:hasResidualCapacity "hasResidualCapacity")
    (comon:hasOperationalStatus "hasOperationalStatus")
  }
  FILTER NOT EXISTS { ?state ?prop ?v }
}
ORDER BY ?state ?missing
```

## EXT-Q42: Eligible candidates ranked by trust

Category: `trust`. Scope: `fog`.

Source: [core/trust/ext-q42.rq](../queries/core/trust/ext-q42.rq).

Evaluate eligible candidates ranked by trust using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate eligible candidates ranked by trust using the declared query contract.
# Requirements: RF-47, RF-48
# Policies: P-NODE-02, P-NODE-05, P-MODEL-03
# Current v4.0.0 result: 4 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?node ?state ?trust WHERE {
  VALUES ?workload { comon:LowWorkload comon:MediumWorkload }
  VALUES ?residual { comon:MediumResidual comon:HighResidual }
  ?node comon:hasNodeState ?state .
  ?state comon:hasAvailability comon:Available ; comon:hasCommunication comon:StableComm ; comon:hasWorkload ?workload ; comon:hasResidualCapacity ?residual ; comon:hasOperationalStatus comon:Operational .
  ?state comon:hasTrustAssessment/comon:hasTrustScore ?trust .
}
ORDER BY DESC(?trust) ?node
```

## EXT-Q43: Review: trust assessment is not fully reproducible

Category: `trust`. Scope: `fog`.

Source: [core/trust/ext-q43.rq](../queries/core/trust/ext-q43.rq).

Evaluate review: trust assessment is not fully reproducible using the declared query contract.

```sparql
# Type: review
# Purpose: Evaluate review: trust assessment is not fully reproducible using the declared query contract.
# Requirements: RF-49, RNF-32
# Policies: P-NODE-03
# Current v4.0.0 result: 7 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?assessment ?state ?score ?ruleVersion ?windowStart ?windowEnd ?evidence ?configStatus WHERE {
  ?assessment a comon:TrustAssessment ; comon:trustAssessmentForState ?state .
  OPTIONAL { ?assessment comon:hasTrustScore ?score }
  OPTIONAL { ?assessment comon:trustRuleVersion ?ruleVersion }
  OPTIONAL { ?assessment comon:trustWindowStart ?windowStart }
  OPTIONAL { ?assessment comon:trustWindowEnd ?windowEnd }
  OPTIONAL { ?assessment comon:hasTrustEvidence ?evidence }
  OPTIONAL { ?assessment comon:configurationStatus ?configStatus }
  FILTER(!BOUND(?score) || !BOUND(?ruleVersion) || !BOUND(?windowStart) || !BOUND(?windowEnd) || !BOUND(?evidence))
}
ORDER BY ?assessment
```

## EXT-Q44: External trust used in evaluation

Category: `trust`. Scope: `authorities`.

Source: [core/trust/ext-q44.rq](../queries/core/trust/ext-q44.rq).

Evaluate external trust used in evaluation using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate external trust used in evaluation using the declared query contract.
# Requirements: RF-46, RF-55
# Policies: P-MODEL-03, P-NODE-05
# Current v4.0.0 result: 10 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?latencyWeight ?privacyWeight ?qualityWeight ?externalTrustWeight ?nodeTrust WHERE {
  ?evaluation a comon:EvaluationState .
  OPTIONAL { ?evaluation comon:hasLatencyWeight ?latencyWeight }
  OPTIONAL { ?evaluation comon:hasPrivacyWeight ?privacyWeight }
  OPTIONAL { ?evaluation comon:hasModelQualityWeight ?qualityWeight }
  OPTIONAL { ?evaluation comon:hasTrustWeight ?externalTrustWeight }
  OPTIONAL { ?evaluation comon:evaluatesNode/comon:hasNodeState/comon:hasTrustAssessment/comon:hasTrustScore ?nodeTrust }
}
ORDER BY ?evaluation
```

## EXT-Q45: Violation: explicitly ineligible adaptive destination

Category: `trust`. Scope: `authorities`.

Source: [core/trust/ext-q45.rq](../queries/core/trust/ext-q45.rq).

Evaluate violation: explicitly ineligible adaptive destination using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: explicitly ineligible adaptive destination using the declared query contract.
# Requirements: RF-18, RF-48
# Policies: P-ADAPT-04, P-ADAPT-07
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?action ?scenario ?origin ?target ?reason WHERE {
  VALUES ?actionType { comon:MigrationEvent comon:DelegationEvent comon:OffloadingEvent }
  ?action a ?actionType ; comon:actionOriginNode ?origin ; comon:actionTargetNode ?target ; comon:partOfScenario ?scenario .
  ?target comon:hasNodeState ?ts . ?ts comon:partOfScenario ?scenario .
  {
    { ?ts comon:hasAvailability comon:NotAvailable } UNION { ?ts comon:hasCommunication comon:NoConnectionComm } UNION { ?ts comon:hasWorkload comon:SaturatedWorkload } UNION { ?ts comon:hasOperationalStatus comon:Inoperative }
    BIND("target-hard-ineligible" AS ?reason)
  }
  UNION
  {
    ?origin comon:hasNodeState ?os . ?os comon:partOfScenario ?scenario ; comon:hasTrustAssessment/comon:hasTrustScore ?originTrust .
    ?ts comon:hasTrustAssessment/comon:hasTrustScore ?targetTrust .
    FILTER(?targetTrust < ?originTrust)
    BIND("target-lower-trust" AS ?reason)
  }
}
ORDER BY ?action ?reason
```

## EXT-Q46: Complete model decision report

Category: `decision`. Scope: `authorities`.

Source: [core/decision/ext-q46.rq](../queries/core/decision/ext-q46.rq).

Evaluate complete model decision report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate complete model decision report using the declared query contract.
# Requirements: RF-15, RF-51, RF-66, RF-52
# Policies: P-MODEL-01, P-MODEL-05, P-AUD-06
# Current v4.0.0 result: 11 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?user ?method ?latency ?privacy ?quality ?trustExternal ?tier ?justification ?action WHERE {
  ?evaluation a comon:EvaluationState .
  OPTIONAL { ?evaluation comon:evaluationUser ?user }
  OPTIONAL { ?evaluation comon:hasDecisionMethod ?method }
  OPTIONAL { ?evaluation comon:hasLatencyWeight ?latency }
  OPTIONAL { ?evaluation comon:hasPrivacyWeight ?privacy }
  OPTIONAL { ?evaluation comon:hasModelQualityWeight ?quality }
  OPTIONAL { ?evaluation comon:hasTrustWeight ?trustExternal }
  OPTIONAL { ?evaluation comon:selectedModelTier ?tier }
  OPTIONAL { ?evaluation comon:hasSelectionJustification ?justification }
  OPTIONAL { ?evaluation comon:resultedInAction ?action }
}
ORDER BY ?evaluation
```

## EXT-Q47: Violation: evaluation without minimum decision fields

Category: `decision`. Scope: `authorities`.

Source: [core/decision/ext-q47.rq](../queries/core/decision/ext-q47.rq).

Evaluate violation: evaluation without minimum decision fields using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: evaluation without minimum decision fields using the declared query contract.
# Requirements: RF-54, RF-66, RNF-28
# Policies: P-AUD-06
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?missing WHERE {
  ?evaluation a comon:EvaluationState .
  VALUES (?prop ?missing) {
    (comon:evaluationUser "evaluationUser")
    (comon:evaluationPurpose "evaluationPurpose")
    (comon:evaluationZone "evaluationZone")
    (comon:auditsContract "auditsContract")
    (comon:hasAuthorizationDecision "hasAuthorizationDecision")
    (comon:hasDecisionMethod "hasDecisionMethod")
    (comon:hasLatencyWeight "hasLatencyWeight")
    (comon:hasPrivacyWeight "hasPrivacyWeight")
    (comon:hasModelQualityWeight "hasModelQualityWeight")
    (comon:selectedModelTier "selectedModelTier")
    (comon:hasSelectionJustification "hasSelectionJustification")
    (comon:validFrom "validFrom")
    (comon:resultedInAction "resultedInAction")
  }
  FILTER NOT EXISTS { ?evaluation ?prop ?v }
}
ORDER BY ?evaluation ?missing
```

## EXT-Q48: Violation: unnormalized multicriteria weights

Category: `decision`. Scope: `authorities`.

Source: [core/decision/ext-q48.rq](../queries/core/decision/ext-q48.rq).

Evaluate violation: unnormalized multicriteria weights using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: unnormalized multicriteria weights using the declared query contract.
# Requirements: RF-50, RF-55, RNF-34
# Policies: P-MODEL-02, P-MODEL-03
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?latency ?privacy ?quality ((?latency + ?privacy + ?quality) AS ?sum) WHERE {
  ?evaluation a comon:EvaluationState ; comon:hasLatencyWeight ?latency ; comon:hasPrivacyWeight ?privacy ; comon:hasModelQualityWeight ?quality .
  FILTER(ABS((?latency + ?privacy + ?quality) - 1.0) > 0.000001)
}
ORDER BY ?evaluation
```

## EXT-Q49: Decision method and consistency report

Category: `decision`. Scope: `authorities`.

Source: [core/decision/ext-q49.rq](../queries/core/decision/ext-q49.rq).

Evaluate decision method and consistency report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate decision method and consistency report using the declared query contract.
# Requirements: RF-55, RNF-33, RNF-34
# Policies: P-MODEL-04
# Current v4.0.0 result: 8 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?method ?ratio ?threshold ?pairwiseCount WHERE {
  ?evaluation a comon:EvaluationState ; comon:hasDecisionMethod ?method .
  OPTIONAL { ?evaluation comon:hasConsistencyRatio ?ratio }
  OPTIONAL { ?evaluation comon:hasConsistencyThreshold ?threshold }
  {
    SELECT ?evaluation (COUNT(?pc) AS ?pairwiseCount) WHERE {
      ?evaluation a comon:EvaluationState . OPTIONAL { ?evaluation comon:hasPairwiseComparison ?pc }
    } GROUP BY ?evaluation
  }
}
ORDER BY ?evaluation
```

## EXT-Q50: Violation: AHP evaluation without valid consistency

Category: `decision`. Scope: `authorities`.

Source: [core/decision/ext-q50.rq](../queries/core/decision/ext-q50.rq).

Evaluate violation: AHP evaluation without valid consistency using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: AHP evaluation without valid consistency using the declared query contract.
# Requirements: RF-55, RNF-34
# Policies: P-MODEL-04
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?ratio ?threshold ?pairwiseCount WHERE {
  ?evaluation a comon:EvaluationState ; comon:hasDecisionMethod comon:AHPDecisionMethod .
  OPTIONAL { ?evaluation comon:hasConsistencyRatio ?ratio }
  OPTIONAL { ?evaluation comon:hasConsistencyThreshold ?threshold }
  {
    SELECT ?evaluation (COUNT(?pc) AS ?pairwiseCount) WHERE {
      ?evaluation a comon:EvaluationState . OPTIONAL { ?evaluation comon:hasPairwiseComparison ?pc }
    } GROUP BY ?evaluation
  }
  FILTER(!BOUND(?ratio) || !BOUND(?threshold) || ?pairwiseCount = 0 || ?ratio > ?threshold)
}
```

## EXT-Q51: Alternatives by evaluation

Category: `decision`. Scope: `authorities`.

Source: [core/decision/ext-q51.rq](../queries/core/decision/ext-q51.rq).

Evaluate alternatives by evaluation using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate alternatives by evaluation using the declared query contract.
# Requirements: RF-51, RNF-29
# Policies: P-MODEL-05
# Current v4.0.0 result: 32 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?alternative ?tier ?eligible ?score ?reason ?selected WHERE {
  ?evaluation a comon:EvaluationState ; comon:hasDecisionAlternative ?alternative .
  ?alternative comon:alternativeModelTier ?tier .
  OPTIONAL { ?alternative comon:isEligible ?eligible }
  OPTIONAL { ?alternative comon:hasAHPScore ?score }
  OPTIONAL { ?alternative comon:eligibilityReason ?reason }
  BIND(EXISTS { ?evaluation comon:selectedAlternative ?alternative } AS ?selected)
}
ORDER BY ?evaluation ?tier
```

## EXT-Q52: Review: alternatives pending recalculation

Category: `decision`. Scope: `authorities`.

Source: [core/decision/ext-q52.rq](../queries/core/decision/ext-q52.rq).

Evaluate review: alternatives pending recalculation using the declared query contract.

```sparql
# Type: review
# Purpose: Evaluate review: alternatives pending recalculation using the declared query contract.
# Requirements: RF-51, RNF-29, RNF-33
# Policies: P-MODEL-05
# Current v4.0.0 result: 32 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?alternative ?tier ?eligible ?score ?reason WHERE {
  ?evaluation a comon:EvaluationState ; comon:hasDecisionAlternative ?alternative .
  ?alternative comon:alternativeModelTier ?tier .
  OPTIONAL { ?alternative comon:isEligible ?eligible }
  OPTIONAL { ?alternative comon:hasAHPScore ?score }
  OPTIONAL { ?alternative comon:eligibilityReason ?reason }
  FILTER(!BOUND(?eligible) || !BOUND(?score))
}
ORDER BY ?evaluation ?tier
```

## EXT-Q53: Violation: invalid selected alternative

Category: `decision`. Scope: `authorities`.

Source: [core/decision/ext-q53.rq](../queries/core/decision/ext-q53.rq).

Evaluate violation: invalid selected alternative using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: invalid selected alternative using the declared query contract.
# Requirements: RF-51, RF-54
# Policies: P-MODEL-05
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?selected ?selectedTier ?alternativeTier ?eligible ?reason WHERE {
  ?evaluation a comon:EvaluationState ; comon:selectedModelTier ?selectedTier .
  OPTIONAL { ?evaluation comon:selectedAlternative ?selected . OPTIONAL { ?selected comon:alternativeModelTier ?alternativeTier } OPTIONAL { ?selected comon:isEligible ?eligible } }
  BIND(IF(!BOUND(?selected), "missing-selectedAlternative", IF(BOUND(?eligible) && ?eligible = false, "selected-not-eligible", IF(BOUND(?alternativeTier) && ?alternativeTier != ?selectedTier, "tier-mismatch", ""))) AS ?reason)
  FILTER(?reason != "")
}
ORDER BY ?evaluation
```

## EXT-Q54: Observed model quality report

Category: `decision`. Scope: `authorities`.

Source: [domain/wellbeing/decision/ext-q54.rq](../queries/domain/wellbeing/decision/ext-q54.rq).

Evaluate observed model quality report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate observed model quality report using the declared query contract.
# Requirements: RF-14, RF-29, RNF-27
# Policies: P-MODEL-08, P-OPS-05
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?subject ?observedQuality ?predictionConfidence ?estimatedError ?feedback WHERE {
  VALUES ?type {
    comon:EvaluationState comon:AIModel comon:StressObservation comon:SleepObservation
  }
  ?subject a ?type .
  OPTIONAL { ?subject comon:observedModelQuality ?observedQuality }
  OPTIONAL { ?subject comon:predictionConfidence ?predictionConfidence }
  OPTIONAL { ?subject comon:estimatedPredictionError ?estimatedError }
  OPTIONAL { ?subject comon:userFeedbackScore ?feedback }
  FILTER(BOUND(?observedQuality) || BOUND(?predictionConfidence) || BOUND(?estimatedError) || BOUND(?feedback))
}
ORDER BY ?subject
```

## EXT-Q55: Review: insufficient quality evidence

Category: `decision`. Scope: `authorities`.

Source: [core/decision/ext-q55.rq](../queries/core/decision/ext-q55.rq).

Evaluate review: insufficient quality evidence using the declared query contract.

```sparql
# Type: review
# Purpose: Evaluate review: insufficient quality evidence using the declared query contract.
# Requirements: RF-14, RF-54
# Policies: P-MODEL-08
# Current v4.0.0 result: 8 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?qualityWeight WHERE {
  ?evaluation a comon:EvaluationState ; comon:hasModelQualityWeight ?qualityWeight .
  FILTER NOT EXISTS { ?evaluation comon:observedModelQuality ?q }
  FILTER NOT EXISTS { ?evaluation comon:predictionConfidence ?c }
  FILTER NOT EXISTS { ?evaluation comon:estimatedPredictionError ?e }
}
ORDER BY ?evaluation
```

## EXT-Q56: Violation: cloud selected without sufficient conditions

Category: `decision`. Scope: `authorities`.

Source: [core/decision/ext-q56.rq](../queries/core/decision/ext-q56.rq).

Evaluate violation: cloud selected without sufficient conditions using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: cloud selected without sufficient conditions using the declared query contract.
# Requirements: RF-53, RF-52
# Policies: P-MODEL-07, P-ZONE-01, P-CONS-04
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?effectiveRange ?zone ?outcome ?reason WHERE {
  ?evaluation a comon:EvaluationState ; comon:selectedModelTier comon:CloudModelTier ; comon:evaluationZone ?zone ; comon:hasAuthorizationDecision ?authorization .
  OPTIONAL { ?authorization comon:hasEffectiveConsentRange ?effectiveRange }
  OPTIONAL { ?authorization comon:hasAuthorizationOutcome ?outcome }
  BIND(IF(!BOUND(?effectiveRange) || ?effectiveRange != comon:RangeGlobalAgg, "range-not-global", IF(EXISTS { ?zone a comon:RestrictedZone }, "restricted-zone", IF(!BOUND(?outcome) || ?outcome != comon:AuthorizationGranted, "authorization-not-granted", ""))) AS ?reason)
  FILTER(?reason != "")
}
ORDER BY ?evaluation
```

## EXT-Q57: Model versioning and lineage report

Category: `decision`. Scope: `authorities`.

Source: [core/decision/ext-q57.rq](../queries/core/decision/ext-q57.rq).

Evaluate model versioning and lineage report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate model versioning and lineage report using the declared query contract.
# Requirements: RF-24
# Policies: P-FL-08
# Current v4.0.0 result: 7 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?model ?version ?updated ?supersedes ?lineageStatus WHERE {
  ?model a comon:AIModel .
  OPTIONAL { ?model comon:modelVersion ?version }
  OPTIONAL { ?model comon:lastUpdated ?updated }
  OPTIONAL { ?model comon:supersedesModel ?supersedes }
  OPTIONAL { ?model comon:modelLineageStatus ?lineageStatus }
}
ORDER BY ?model
```

## EXT-Q58: Review: rollback readiness

Category: `decision`. Scope: `authorities`.

Source: [core/decision/ext-q58.rq](../queries/core/decision/ext-q58.rq).

Evaluate review: rollback readiness using the declared query contract.

```sparql
# Type: review
# Purpose: Evaluate review: rollback readiness using the declared query contract.
# Requirements: RF-24
# Policies: P-FL-08
# Current v4.0.0 result: 7 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?subject ?kind ?target ?status WHERE {
  { ?subject a comon:RollbackEvent . BIND("rollback-event" AS ?kind) OPTIONAL { ?subject comon:rollbackTarget ?target } }
  UNION
  { ?subject a comon:AIModel . FILTER NOT EXISTS { ?subject comon:supersedesModel ?prev } BIND("model-without-predecessor" AS ?kind) OPTIONAL { ?subject comon:modelLineageStatus ?status } }
}
ORDER BY ?kind ?subject
```

## EXT-Q59: Adaptive action report

Category: `adaptation`. Scope: `authorities`.

Source: [core/adaptation/ext-q59.rq](../queries/core/adaptation/ext-q59.rq).

Evaluate adaptive action report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate adaptive action report using the declared query contract.
# Requirements: RF-16, RF-17, RF-20, RF-66
# Policies: P-ADAPT-06, P-AUD-06
# Current v4.0.0 result: 11 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?action ?actionType ?scenario ?evaluation ?origin ?target ?service ?model ?from ?to WHERE {
  ?action a comon:AdaptationAction ; a ?actionType .
  FILTER(?actionType != comon:AdaptationAction && ?actionType != owl:NamedIndividual)
  OPTIONAL { ?action comon:partOfScenario ?scenario }
  OPTIONAL { ?action comon:authorizedByEvaluation ?evaluation }
  OPTIONAL { ?action comon:actionOriginNode ?origin }
  OPTIONAL { ?action comon:actionTargetNode ?target }
  OPTIONAL { ?action comon:affectsService ?service }
  OPTIONAL { ?action comon:affectsModel ?model }
  OPTIONAL { ?action comon:validFrom ?from }
  OPTIONAL { ?action comon:validTo ?to }
}
ORDER BY ?scenario ?action
```

## EXT-Q60: Migration report

Category: `adaptation`. Scope: `authorities`.

Source: [core/adaptation/ext-q60.rq](../queries/core/adaptation/ext-q60.rq).

Evaluate migration report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate migration report using the declared query contract.
# Requirements: RF-16, RF-17
# Policies: P-ADAPT-05
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?migration ?scenario ?origin ?target ?evaluation ?service ?cost ?time ?from ?to WHERE {
  ?migration a comon:MigrationEvent .
  OPTIONAL { ?migration comon:partOfScenario ?scenario }
  OPTIONAL { ?migration comon:actionOriginNode ?origin }
  OPTIONAL { ?migration comon:actionTargetNode ?target }
  OPTIONAL { ?migration comon:authorizedByEvaluation ?evaluation }
  OPTIONAL { ?migration comon:affectsService ?service }
  OPTIONAL { ?evaluation comon:hasMigrationCost ?cost }
  OPTIONAL { ?evaluation comon:hasMigrationTime ?time }
  OPTIONAL { ?migration comon:validFrom ?from }
  OPTIONAL { ?migration comon:validTo ?to }
}
ORDER BY ?migration
```

## EXT-Q61: Violation: migration or delegation confused with federated learning

Category: `adaptation`. Scope: `authorities`.

Source: [core/adaptation/ext-q61.rq](../queries/core/adaptation/ext-q61.rq).

Evaluate violation: migration or delegation confused with federated learning using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: migration or delegation confused with federated learning using the declared query contract.
# Requirements: RF-16, RF-22
# Policies: P-ADAPT-05
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?resource WHERE {
  VALUES ?adaptType { comon:MigrationEvent comon:DelegationEvent comon:OffloadingEvent }
  ?resource a comon:FederatedLearningSession ; a ?adaptType .
}
```

## EXT-Q62: Degradation report

Category: `adaptation`. Scope: `authorities`.

Source: [core/adaptation/ext-q62.rq](../queries/core/adaptation/ext-q62.rq).

Evaluate degradation report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate degradation report using the declared query contract.
# Requirements: RF-20
# Policies: P-ADAPT-02, P-ADAPT-03, P-ADAPT-06
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?event ?scenario ?cause ?service ?model ?evaluation ?from ?to WHERE {
  ?event a comon:DegradationEvent .
  OPTIONAL { ?event comon:partOfScenario ?scenario }
  OPTIONAL { ?event comon:hasDegradationCause ?cause }
  OPTIONAL { ?event comon:affectsService ?service }
  OPTIONAL { ?event comon:affectsModel ?model }
  OPTIONAL { ?event comon:authorizedByEvaluation ?evaluation }
  OPTIONAL { ?event comon:validFrom ?from }
  OPTIONAL { ?event comon:validTo ?to }
}
ORDER BY ?event
```

## EXT-Q63: Temporary delegation report

Category: `delegation`. Scope: `authorities`.

Source: [core/delegation/ext-q63.rq](../queries/core/delegation/ext-q63.rq).

Evaluate temporary delegation report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate temporary delegation report using the declared query contract.
# Requirements: RF-62, RF-63, RF-64
# Policies: P-AUD-01, P-AUD-02, P-AUD-03
# Current v4.0.0 result: 1 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?delegation ?origin ?target ?triggerState ?recovery ?depth ?plannedExpiry ?from ?to WHERE {
  ?delegation a comon:DelegationEvent .
  OPTIONAL { ?delegation comon:actionOriginNode ?origin }
  OPTIONAL { ?delegation comon:actionTargetNode ?target }
  OPTIONAL { ?delegation comon:triggeredByState ?triggerState }
  OPTIONAL { ?delegation comon:hasRecoveryCondition ?recovery }
  OPTIONAL { ?delegation comon:delegationDepth ?depth }
  OPTIONAL { ?delegation comon:plannedExpiry ?plannedExpiry }
  OPTIONAL { ?delegation comon:validFrom ?from }
  OPTIONAL { ?delegation comon:validTo ?to }
}
ORDER BY ?delegation
```

## EXT-Q64: Violation: incomplete delegation

Category: `delegation`. Scope: `authorities`.

Source: [core/delegation/ext-q64.rq](../queries/core/delegation/ext-q64.rq).

Evaluate violation: incomplete delegation using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: incomplete delegation using the declared query contract.
# Requirements: RF-63
# Policies: P-AUD-02
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?delegation ?missing WHERE {
  ?delegation a comon:DelegationEvent .
  VALUES (?prop ?missing) {
    (comon:actionOriginNode "actionOriginNode")
    (comon:actionTargetNode "actionTargetNode")
    (comon:triggeredByState "triggeredByState")
    (comon:validFrom "validFrom")
    (comon:hasRecoveryCondition "hasRecoveryCondition")
    (comon:delegationDepth "delegationDepth")
  }
  FILTER NOT EXISTS { ?delegation ?prop ?v }
}
ORDER BY ?delegation ?missing
```

## EXT-Q65: Violation: delegation depth exceeds the profile

Category: `delegation`. Scope: `authorities`.

Source: [core/delegation/ext-q65.rq](../queries/core/delegation/ext-q65.rq).

Evaluate violation: delegation depth exceeds the profile using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: delegation depth exceeds the profile using the declared query contract.
# Requirements: RNF-14
# Policies: P-AUD-04, P-OPS-01
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?delegation ?depth ?maxDepth ?profile WHERE {
  ?delegation a comon:DelegationEvent ; comon:delegationDepth ?depth .
  ?profile a comon:AcceptanceProfile ; comon:D_delegation_max ?maxDepth .
  FILTER(?depth > ?maxDepth)
}
```

## EXT-Q66: Federated learning session and payload report

Category: `federation`. Scope: `authorities`.

Source: [core/federation/ext-q66.rq](../queries/core/federation/ext-q66.rq).

Evaluate federated learning session and payload report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate federated learning session and payload report using the declared query contract.
# Requirements: RF-21, RF-22, RF-23, RF-25
# Policies: P-FL-01, P-FL-06, P-FL-07, P-CONS-06
# Current v4.0.0 result: 2 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?session ?payload ?purpose ?requiredRange ?model ?data ?personal ?individualized ?persistent WHERE {
  ?session a comon:FederatedLearningSession .
  OPTIONAL { ?session comon:hasPayloadType ?payload }
  OPTIONAL { ?session comon:hasProcessingPurpose ?purpose }
  OPTIONAL { ?session comon:requiresConsentRange ?requiredRange }
  OPTIONAL { ?session comon:updatesModel ?model }
  OPTIONAL { ?session comon:transfersData ?data }
  OPTIONAL { ?session comon:containsPersonalData ?personal }
  OPTIONAL { ?session comon:containsIndividualizedGradients ?individualized }
  OPTIONAL { ?session comon:containsPersistentIdentifier ?persistent }
}
ORDER BY ?session
```

## EXT-Q67: Violation: unauthorized upstream federated learning session

Category: `federation`. Scope: `authorities`.

Source: [core/federation/ext-q67.rq](../queries/core/federation/ext-q67.rq).

Evaluate violation: unauthorized upstream federated learning session using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: unauthorized upstream federated learning session using the declared query contract.
# Requirements: RF-21, RF-56
# Policies: P-FL-02, P-FL-03
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?session ?range ?purpose ?personal ?persistent WHERE {
  ?session a comon:FederatedLearningSession ; comon:hasPayloadType comon:ModelGradientsPayload .
  OPTIONAL { ?session comon:hasConsentRange ?range }
  OPTIONAL { ?session comon:hasProcessingPurpose ?purpose }
  OPTIONAL { ?session comon:containsPersonalData ?personal }
  OPTIONAL { ?session comon:containsPersistentIdentifier ?persistent }
  FILTER(!BOUND(?range) || ?range != comon:RangeGlobalAgg || !BOUND(?purpose) || ?purpose != comon:PurposeGlobalFederatedLearning || (BOUND(?personal) && ?personal = true) || (BOUND(?persistent) && ?persistent = true))
}
```

## EXT-Q68: Violation: gradient without anonymization, noise or privacy mechanism

Category: `federation`. Scope: `authorities`.

Source: [core/federation/ext-q68.rq](../queries/core/federation/ext-q68.rq).

Evaluate violation: gradient without anonymization, noise or privacy mechanism using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: gradient without anonymization, noise or privacy mechanism using the declared query contract.
# Requirements: RF-57, RF-58, RNF-16, RNF-19
# Policies: P-FL-03, P-FL-05
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?gradient ?noiseApplied ?anonApplied WHERE {
  ?gradient a comon:ModelGradientUpdate ; comon:originatesFromDevice ?device ; comon:sentToNode ?dest .
  OPTIONAL { ?gradient comon:hasNoiseApplied ?noiseApplied }
  OPTIONAL { ?gradient comon:hasAnonymizationApplied ?anonApplied }
  FILTER(!BOUND(?noiseApplied) || ?noiseApplied != true || !BOUND(?anonApplied) || ?anonApplied != true || NOT EXISTS { ?gradient comon:hasPrivacyMechanism ?m })
}
```

## EXT-Q69: Differential privacy and epsilon accounting

Category: `federation`. Scope: `authorities`.

Source: [core/federation/ext-q69.rq](../queries/core/federation/ext-q69.rq).

Evaluate differential privacy and epsilon accounting using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate differential privacy and epsilon accounting using the declared query contract.
# Requirements: RF-56, RF-59, RNF-18
# Policies: P-FL-04
# Current v4.0.0 result: 2 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?session ?budget ?noise ?account ?contract ?purpose ?maximum ?consumed ?remaining ?status WHERE {
  ?session a comon:FederatedLearningSession .
  OPTIONAL { ?session comon:hasPrivacyBudget ?budget }
  OPTIONAL { ?session comon:noiseLevel ?noise }
  OPTIONAL { ?session comon:hasPrivacyBudgetAccount ?account .
    OPTIONAL { ?account comon:budgetForContract ?contract }
    OPTIONAL { ?account comon:budgetForPurpose ?purpose }
    OPTIONAL { ?account comon:privacyBudgetMaximum ?maximum }
    OPTIONAL { ?account comon:privacyBudgetConsumed ?consumed }
    OPTIONAL { ?account comon:privacyBudgetRemaining ?remaining }
    OPTIONAL { ?account comon:configurationStatus ?status }
  }
}
ORDER BY ?session
```

## EXT-Q70: Complete semantic audit chain

Category: `audit_temporal`. Scope: `authorities`.

Source: [core/audit_temporal/ext-q70.rq](../queries/core/audit_temporal/ext-q70.rq).

Evaluate complete semantic audit chain using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate complete semantic audit chain using the declared query contract.
# Requirements: RF-67, RNF-30
# Policies: P-AUD-07
# Current v4.0.0 result: 204 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?user ?contract ?effectiveRange ?purpose ?zone ?policy ?node ?alternative ?altTier ?altScore ?trust ?selectedTier ?action ?from WHERE {
  ?evaluation a comon:EvaluationState ; comon:evaluationUser ?user ; comon:auditsContract ?contract ; comon:hasAuthorizationDecision/comon:hasEffectiveConsentRange ?effectiveRange ; comon:evaluationPurpose ?purpose ; comon:evaluationZone ?zone ; comon:selectedModelTier ?selectedTier ; comon:resultedInAction ?action ; comon:validFrom ?from .
  OPTIONAL { ?evaluation comon:appliedPolicy ?policy }
  OPTIONAL { ?evaluation comon:evaluatesNode ?node . OPTIONAL { ?node comon:hasNodeState/comon:hasTrustAssessment/comon:hasTrustScore ?trust } }
  OPTIONAL { ?evaluation comon:hasDecisionAlternative ?alternative . ?alternative comon:alternativeModelTier ?altTier . OPTIONAL { ?alternative comon:hasAHPScore ?altScore } }
}
ORDER BY ?evaluation ?policy ?altTier
```

## EXT-Q71: Violation: incomplete audit ticket

Category: `audit_temporal`. Scope: `authorities`.

Source: [core/audit_temporal/ext-q71.rq](../queries/core/audit_temporal/ext-q71.rq).

Evaluate violation: incomplete audit ticket using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: incomplete audit ticket using the declared query contract.
# Requirements: RF-54, RF-66, RNF-28, RNF-29
# Policies: P-AUD-06
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?evaluation ?missing WHERE {
  ?evaluation a comon:EvaluationState .
  {
    VALUES (?prop ?missing) {
      (comon:hasDetectedSymptom "hasDetectedSymptom")
      (comon:appliedPolicy "appliedPolicy")
      (comon:auditsContract "auditsContract")
      (comon:hasAuthorizationDecision "hasAuthorizationDecision")
      (comon:hasDecisionAlternative "hasDecisionAlternative")
      (comon:selectedModelTier "selectedModelTier")
      (comon:hasSelectionJustification "hasSelectionJustification")
      (comon:validFrom "validFrom")
      (comon:resultedInAction "resultedInAction")
    }
    FILTER NOT EXISTS { ?evaluation ?prop ?v }
  }
  UNION
  {
    FILTER NOT EXISTS { ?evaluation comon:hasAuthorizationDecision/comon:hasEffectiveConsentRange ?r }
    BIND("effectiveConsentRange" AS ?missing)
  }
}
ORDER BY ?evaluation ?missing
```

## EXT-Q72: Violation: action without evaluation or policy justification

Category: `audit_temporal`. Scope: `authorities`.

Source: [core/audit_temporal/ext-q72.rq](../queries/core/audit_temporal/ext-q72.rq).

Evaluate violation: action without evaluation or policy justification using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: action without evaluation or policy justification using the declared query contract.
# Requirements: RF-65, RF-66, RF-41, RF-44
# Policies: P-AUD-05, P-GOV-02
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?subject ?reason WHERE {
  {
    ?subject a comon:AdaptationAction .
    FILTER NOT EXISTS { ?subject comon:authorizedByEvaluation ?evaluation }
    BIND("action-without-evaluation" AS ?reason)
  }
  UNION
  {
    ?subject a comon:EvaluationState ; comon:resultedInAction ?action .
    FILTER NOT EXISTS { ?subject comon:appliedPolicy ?policy }
    BIND("evaluation-without-policy" AS ?reason)
  }
}
ORDER BY ?subject
```

## EXT-Q73: Temporal entity report

Category: `audit_temporal`. Scope: `authorities`.

Source: [core/audit_temporal/ext-q73.rq](../queries/core/audit_temporal/ext-q73.rq).

Evaluate temporal entity report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate temporal entity report using the declared query contract.
# Requirements: RNF-35, RNF-36
# Policies: P-GOV-05, P-AUD-02
# Current v4.0.0 result: 79 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?entity ?type ?from ?to ?plannedExpiry WHERE {
  ?entity a ?type .
  ?type rdfs:subClassOf* comon:TemporalEntity .
  FILTER(?type != comon:TemporalEntity)
  OPTIONAL { ?entity comon:validFrom ?from }
  OPTIONAL { ?entity comon:validTo ?to }
  OPTIONAL { ?entity comon:plannedExpiry ?plannedExpiry }
}
ORDER BY ?entity ?type
```

## EXT-Q74: Violation: missing validFrom or invalid temporal interval

Category: `audit_temporal`. Scope: `authorities`.

Source: [core/audit_temporal/ext-q74.rq](../queries/core/audit_temporal/ext-q74.rq).

Evaluate violation: missing validFrom or invalid temporal interval using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: missing validFrom or invalid temporal interval using the declared query contract.
# Requirements: RNF-36
# Policies: P-GOV-05
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?entity ?from ?to ?reason WHERE {
  ?entity a ?type . ?type rdfs:subClassOf* comon:TemporalEntity . FILTER(?type != comon:TemporalEntity && ?type != comon:TrustAssessment)
  OPTIONAL { ?entity comon:validFrom ?from }
  OPTIONAL { ?entity comon:validTo ?to }
  BIND(IF(!BOUND(?from), "missing-validFrom", IF(BOUND(?to) && ?to < ?from, "validTo-before-validFrom", "")) AS ?reason)
  FILTER(?reason != "")
}
ORDER BY ?entity
```

## EXT-Q75: SHACL shape inventory

Category: `validation`. Scope: `cloud`.

Source: [core/validation/ext-q75.rq](../queries/core/validation/ext-q75.rq).

Evaluate sHACL shape inventory using the declared query contract.

```sparql
# Type: inventory
# Purpose: Evaluate sHACL shape inventory using the declared query contract.
# Requirements: RF-71, RV-01
# Policies: P-VAL-03
# Current v4.0.0 result: 74 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?shape ?targetClass ?path ?minCount ?maxCount ?severity ?message WHERE {
  ?shape a sh:NodeShape .
  OPTIONAL { ?shape sh:targetClass ?targetClass }
  OPTIONAL { ?shape sh:property ?ps . OPTIONAL { ?ps sh:path ?path } OPTIONAL { ?ps sh:minCount ?minCount } OPTIONAL { ?ps sh:maxCount ?maxCount } OPTIONAL { ?ps sh:severity ?severity } OPTIONAL { ?ps sh:message ?message } }
}
ORDER BY ?shape ?path
```

## EXT-Q76: Review: incomplete acceptance profile

Category: `validation`. Scope: `cloud`.

Source: [core/validation/ext-q76.rq](../queries/core/validation/ext-q76.rq).

Evaluate review: incomplete acceptance profile using the declared query contract.

```sparql
# Type: review
# Purpose: Evaluate review: incomplete acceptance profile using the declared query contract.
# Requirements: RNF-01, RNF-02, RNF-04, RNF-05, RNF-06, RNF-08, RNF-09, RNF-14, RNF-21, RNF-34
# Policies: P-OPS-01, P-VAL-03
# Current v4.0.0 result: 9 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?profile ?missing WHERE {
  ?profile a comon:AcceptanceProfile .
  VALUES (?prop ?missing) {
    (comon:T_inference_local "T_inference_local")
    (comon:T_migration_max "T_migration_max")
    (comon:T_sparql_monitor "T_sparql_monitor")
    (comon:T_decision_max "T_decision_max")
    (comon:E_device_max "E_device_max")
    (comon:N_agents "N_agents")
    (comon:T_node_join "T_node_join")
    (comon:D_delegation_max "D_delegation_max")
    (comon:T_reselection_max "T_reselection_max")
    (comon:AHP_consistency_threshold "AHP_consistency_threshold")
  }
  FILTER NOT EXISTS { ?profile ?prop ?v }
}
ORDER BY ?missing
```

## EXT-Q77: Review: reproducible campaign readiness

Category: `validation`. Scope: `cloud`.

Source: [core/validation/ext-q77.rq](../queries/core/validation/ext-q77.rq).

Evaluate review: reproducible campaign readiness using the declared query contract.

```sparql
# Type: review
# Purpose: Evaluate review: reproducible campaign readiness using the declared query contract.
# Requirements: RF-71, RF-72, RNF-39, RV-02, RV-03
# Policies: P-VAL-03, P-VAL-04, P-VAL-07
# Current v4.0.0 result: 6 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?check ?value WHERE {
  {
    BIND("ontology-version" AS ?check) <http://example.org/monitoringcontinuum> owl:versionInfo ?value
  }
  UNION { BIND("ontology-artifact" AS ?check) ?a a comon:OntologyArtifact ; comon:artifactIdentifier ?value }
  UNION { BIND("requirements-artifact" AS ?check) ?a a comon:RequirementsArtifact ; comon:artifactIdentifier ?value }
  UNION { BIND("policy-artifact" AS ?check) ?a a comon:PolicyArtifact ; comon:artifactIdentifier ?value }
  UNION { BIND("scenario-artifact" AS ?check) ?a a comon:ScenarioArtifact ; comon:artifactIdentifier ?value }
  UNION { BIND("query-catalog-status" AS ?check) ?a a comon:QueryCatalog ; comon:artifactStatus ?value }
  UNION { BIND("validation-campaign" AS ?check) ?a a comon:ValidationCampaign . BIND(STR(?a) AS ?value) }
}
ORDER BY ?check
```

## EXT-Q78: Policy conflict resolution report

Category: `policy_governance`. Scope: `cloud`.

Source: [core/policy_governance/ext-q78.rq](../queries/core/policy_governance/ext-q78.rq).

Evaluate policy conflict resolution report using the declared query contract.

```sparql
# Type: report
# Purpose: Evaluate policy conflict resolution report using the declared query contract.
# Requirements: RNF-22
# Policies: P-GOV-03
# Current v4.0.0 result: 37 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?relation ?source ?target ?type ?code ?strategy WHERE {
  ?relation a comon:PolicyCategoryRelation ; comon:relationSourceCategory ?source ; comon:relationTargetCategory ?target ; comon:hasPolicyRelationType ?type .
  OPTIONAL { ?type comon:relationCode ?code }
  OPTIONAL { ?relation comon:usesResolutionStrategy ?strategy }
  FILTER(?code IN ("GEN","COR","CON","SHD","DEP"))
}
ORDER BY ?code ?source ?target
```

## EXT-Q79: Violation: conflicting relationship without resolution strategy

Category: `policy_governance`. Scope: `cloud`.

Source: [core/policy_governance/ext-q79.rq](../queries/core/policy_governance/ext-q79.rq).

Evaluate violation: conflicting relationship without resolution strategy using the declared query contract.

```sparql
# Type: violation
# Purpose: Evaluate violation: conflicting relationship without resolution strategy using the declared query contract.
# Requirements: RNF-22
# Policies: P-GOV-03
# Current v4.0.0 result: 0 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?relation ?source ?target ?code WHERE {
  ?relation a comon:PolicyCategoryRelation ; comon:relationSourceCategory ?source ; comon:relationTargetCategory ?target ; comon:hasPolicyRelationType ?type .
  ?type comon:relationCode ?code .
  FILTER(?code IN ("GEN","COR","CON","SHD"))
  FILTER NOT EXISTS { ?relation comon:usesResolutionStrategy ?strategy }
}
ORDER BY ?code ?source ?target
```

## EXT-Q80: Global coverage and migration debt dashboard

Category: `validation`. Scope: `cloud`.

Source: [core/validation/ext-q80.rq](../queries/core/validation/ext-q80.rq).

Evaluate global coverage and migration debt dashboard using the declared query contract.

```sparql
# Type: dashboard
# Purpose: Evaluate global coverage and migration debt dashboard using the declared query contract.
# Requirements: RF-68, RF-71, RV-01, RV-05
# Policies: P-VAL-08
# Current v4.0.0 result: 13 rows
PREFIX comon: <http://example.org/monitoringcontinuum#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?metric ?value WHERE {
  { BIND("functional_requirements" AS ?metric) { SELECT (COUNT(DISTINCT ?x) AS ?value) WHERE { ?x a comon:FunctionalRequirement } } }
  UNION { BIND("nonfunctional_requirements" AS ?metric) { SELECT (COUNT(DISTINCT ?x) AS ?value) WHERE { ?x a comon:NonFunctionalRequirement } } }
  UNION { BIND("validation_requirements" AS ?metric) { SELECT (COUNT(DISTINCT ?x) AS ?value) WHERE { ?x a comon:ValidationRequirement } } }
  UNION { BIND("policies" AS ?metric) { SELECT (COUNT(DISTINCT ?x) AS ?value) WHERE { ?x a comon:Policy } } }
  UNION { BIND("mechanisms" AS ?metric) { SELECT (COUNT(DISTINCT ?x) AS ?value) WHERE { ?x a comon:MechanismSpecification } } }
  UNION { BIND("scenarios" AS ?metric) { SELECT (COUNT(DISTINCT ?x) AS ?value) WHERE { ?x a comon:Scenario } } }
  UNION { BIND("policy_category_relations" AS ?metric) { SELECT (COUNT(DISTINCT ?x) AS ?value) WHERE { ?x a comon:PolicyCategoryRelation } } }
  UNION { BIND("shacl_shapes" AS ?metric) { SELECT (COUNT(DISTINCT ?x) AS ?value) WHERE { ?x a sh:NodeShape } } }
  UNION { BIND("evaluations" AS ?metric) { SELECT (COUNT(DISTINCT ?x) AS ?value) WHERE { ?x a comon:EvaluationState } } }
  UNION { BIND("alternatives_pending_recalculation" AS ?metric) { SELECT (COUNT(DISTINCT ?x) AS ?value) WHERE { ?e comon:hasDecisionAlternative ?x . FILTER NOT EXISTS { ?x comon:hasAHPScore ?score } } } }
  UNION { BIND("trust_assessments_incomplete" AS ?metric) { SELECT (COUNT(DISTINCT ?x) AS ?value) WHERE { ?x a comon:TrustAssessment . FILTER(!EXISTS { ?x comon:trustWindowStart ?ws } || !EXISTS { ?x comon:trustWindowEnd ?we } || !EXISTS { ?x comon:hasTrustEvidence ?ev }) } } }
  UNION { BIND("acceptance_parameters_missing" AS ?metric) { SELECT (COUNT(?prop) AS ?value) WHERE { VALUES ?prop { comon:T_inference_local comon:T_migration_max comon:T_sparql_monitor comon:T_decision_max comon:E_device_max comon:N_agents comon:T_node_join comon:D_delegation_max comon:T_reselection_max comon:AHP_consistency_threshold } FILTER NOT EXISTS { ?p a comon:AcceptanceProfile ; ?prop ?v } } } }
  UNION { BIND("query_specs_in_ontology" AS ?metric) { SELECT (COUNT(DISTINCT ?x) AS ?value) WHERE { ?x a comon:QuerySpecification } } }
}
ORDER BY ?metric
```
