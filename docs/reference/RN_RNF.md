# Listado de requisitos funcionales, no funcionales y de validación

> **Versión de trazabilidad:** v3.0.0. Este documento se alinea con `smartcity_continuum_v3.0.0.ttl`, el artefacto de políticas `POLICIES-REV-01` y la batería `sparql_battery_v3.0.0.sparql` (`BASE-Q01`–`BASE-Q35`, `EXT-Q01`–`EXT-Q80`). En este documento, `ex:` representa `http://example.org/smartcity#`.
>
> **Convenciones:** `†` indica una asociación temática/documental derivada para un requisito estructural que no posee actualmente un enlace directo `ex:tracedToPolicy`/`ex:tracedToMechanism` en la TTL. `‡` indica una consulta existente cuya cobertura es pertinente para el requisito, pero cuyo metadato `Requirements:` no incluye todavía ese ID de requisito. Estas marcas permiten mantener la matriz fiel a los artefactos actuales sin confundir trazabilidad directa con cobertura indirecta.


## 1. Requisitos Funcionales (RF)

Se mantienen los requisitos base y se añaden requisitos específicos para acreditar la ampliación ontológica: consentimiento semántico, contratos, políticas tipadas, confianza dinámica, decisión multicriterio AHP, privacidad diferencial, delegación temporal y auditoría completa. En caso de conflicto entre consentimiento, contrato semántico y política de zona, debe aplicarse siempre la restricción más estricta.

---

### 1.1 Gestión de dispositivos, agentes y nodos del continuum

**RF-01** El sistema debe registrar y gestionar dispositivos vestibles asociados a un individuo/agente, incluyendo al menos relojes inteligentes, anillos inteligentes y bandas inteligentes.
**Soporte ontológico:** `ex:Wearable`, `ex:SmartWatch`, `ex:SmartRing`, `ex:SmartBand`, `ex:hasWearable`  
**Políticas asociadas:** `P-INT-02`†  
**Mecanismos asociados:** `M-INT-02`†, `M-VAL-05`†  
**Consultas asociadas:** `BASE-Q01`, `BASE-Q03`

**RF-02** El sistema debe identificar la localización aproximada del agente y el nodo de la arquitectura al que está conectado: mist, edge, fog o cloud.
**Soporte ontológico:** `ex:locatedInZone`, `ex:connectsTo`, `ex:ComputationalNode`, `ex:MistNode`, `ex:EdgeNode`, `ex:FogNode`, `ex:CloudNode`  
**Políticas asociadas:** `P-OPS-02`†, `P-OPS-03`†  
**Mecanismos asociados:** `M-NODE-01`†, `M-OPS-02`†, `M-OPS-03`†  
**Consultas asociadas:** `BASE-Q02`, `BASE-Q20`, `BASE-Q23`

**RF-03** El sistema debe detectar cambios de contexto del agente, incluyendo movimiento, pérdida de conectividad, cambio de zona, variación de nodo cercano/lejos y transición entre áreas urbanas, rurales o restringidas.
**Soporte ontológico:** `ex:UserState`, `ex:hasMobility`, `ex:NodeUserRelation`, `ex:hasDistance`, `ex:locatedInZone`  
**Políticas asociadas:** `P-ZONE-04`  
**Mecanismos asociados:** `M-CTX-01`, `M-MODEL-04`  
**Consultas asociadas:** `BASE-Q09`, `BASE-Q23`

**RF-04** El sistema debe monitorizar el estado del dispositivo: batería, conectividad, sensores activos, disponibilidad de datos parametrizados y capacidad de preprocesamiento local.
**Soporte ontológico:** `ex:DeviceState`, `ex:hasBatteryLevel`, `ex:hasConnectionStatus`, `ex:parametrizedDataReady`  
**Políticas asociadas:** `P-DATA-04`  
**Mecanismos asociados:** `M-DATA-02`, `M-TX-01`  
**Consultas asociadas:** `BASE-Q10`

**RF-05** El sistema debe registrar el estado operacional de los nodos del continuum, incluyendo disponibilidad, carga, comunicación, capacidad residual, uso de recursos, cola de peticiones y estado operativo. Cuando existan estados `ComputeOnly` o `Inoperative`, deben detectarse explícitamente para que la orquestación pueda decidir delegación, aislamiento o exclusión del nodo.
**Soporte ontológico:** `ex:NodeState`, `ex:hasAvailability`, `ex:hasWorkload`, `ex:hasCommunication`, `ex:hasResidualCapacity`, `ex:resourceUsagePercent`, `ex:queuedRequests`, `ex:hasOperationalStatus`, `ex:ComputeOnly`, `ex:Inoperative`  
**Políticas asociadas:** `P-NODE-01`  
**Mecanismos asociados:** `M-NODE-01`, `M-NODE-02`  
**Consultas asociadas:** `BASE-Q02`, `BASE-Q07`, `BASE-Q26`, `EXT-Q41`

---

### 1.2 Captura, preprocesamiento y gestión contextual de datos


**RF-06** El sistema debe capturar métricas fisiológicas relevantes para estrés y sueño, incluyendo frecuencia cardíaca, HRV, actividad, sueño, movimiento, SpO2, temperatura y actividad electrodérmica cuando los sensores estén disponibles.
**Soporte ontológico:** `ex:PhysiologicalSensor`, `ex:HeartRateSensor`, `ex:EDASensor`, `ex:SleepSensor`, `ex:AccelerometerSensor`, `ex:SpO2Sensor`, `ex:TemperatureSensor`, `ex:PhysiologicalObservation`, `ex:SleepObservation`, `sosa:Sensor`, `sosa:Observation`, `saref:Device`  
**Políticas asociadas:** `P-INT-01`†  
**Mecanismos asociados:** `M-INT-01`†, `M-VAL-01`†  
**Consultas asociadas:** `BASE-Q05`

**RF-07** El sistema debe gestionar el preprocesamiento y la estrategia energética según el contexto. Cuando la conectividad sea limitada o el consentimiento efectivo restrinja el procesamiento al ámbito local, los datos deben preprocesarse en el propio dispositivo o capa mist. Ante batería baja, el sistema debe reducir complejidad de modelo y transmisiones no críticas; ante batería crítica, debe priorizar offloading hacia la capa más alta autorizada únicamente si existe conectividad suficiente y consentimiento, contrato y política de zona lo permiten. Si la batería es crítica y la transferencia no está autorizada, debe aplicar degradación local y retención temporal.
**Soporte ontológico:** `ex:DeviceState`, `ex:hasBatteryLevel`, `ex:BufferRecord`, `ex:AuthorizationDecision`, `ex:hasEffectiveConsentRange`, `ex:MistNode`  
**Políticas asociadas:** `P-ADAPT-02`, `P-DATA-06`  
**Mecanismos asociados:** `M-ADAPT-02`, `M-BUFFER-01`, `M-DEVICE-01`  
**Consultas asociadas:** `BASE-Q10`‡, `BASE-Q17`‡, `EXT-Q31`‡, `EXT-Q62`‡

**RF-08** El sistema debe almacenar temporalmente los datos en la capa más alta autorizada cuando no sea posible transmitirlos por conectividad, energía, saturación, zona o consentimiento. Si el consentimiento efectivo o la política de zona no permiten almacenamiento externo, los datos deben conservarse exclusivamente en el dispositivo o ámbito local autorizado hasta que exista una ventana segura de transmisión.
**Soporte ontológico:** `ex:BufferRecord`, `ex:TransferEvent`, `ex:AuthorizationDecision`, `ex:hasEffectiveConsentRange`, `ex:contextZone`  
**Políticas asociadas:** `P-DATA-05`, `P-OPS-06`, `P-ZONE-02`  
**Mecanismos asociados:** `M-BUFFER-01`, `M-CONS-02`, `M-MODEL-04`, `M-TX-02`, `M-ZONE-01`  
**Consultas asociadas:** `BASE-Q17`, `EXT-Q31`, `EXT-Q38`

**RF-09** El sistema debe etiquetar los datos con contexto operativo: hora, localización, calidad de señal, estado del dispositivo, estado del nodo, nivel de procesamiento y propósito de uso.
**Soporte ontológico:** `ex:locatedInZone`, `ex:hasCommunication`, `ex:DeviceState`, `ex:NodeState`, `ex:ProcessingPurpose`, `ex:DataContext`, `ex:hasDataContext`, `ex:contextDeviceState`, `ex:contextNodeState`, `ex:contextProcessingLevel`, `ex:contextPurpose`, `ex:contextZone`  
**Políticas asociadas:** `P-DATA-04`, `P-DATA-10`  
**Mecanismos asociados:** `M-DATA-02`, `M-TIME-01`, `M-TX-01`  
**Consultas asociadas:** `EXT-Q23`, `EXT-Q24`, `EXT-Q25`

**RF-10** El sistema debe distinguir entre observaciones fisiológicas crudas y datos parametrizados transmisibles. A efectos de estos requisitos, el ámbito local se limita al dispositivo móvil/vestible y, cuando la política lo permita, a la capa mist asociada; las observaciones fisiológicas crudas no deben transmitirse a Edge, Fog ni Cloud.
**Soporte ontológico:** `ex:PhysiologicalObservation`, `ex:SleepObservation`, `ex:ParametrizedData`, `ex:TransferEvent`, `ex:EdgeNode`, `ex:FogNode`, `ex:CloudNode`  
**Políticas asociadas:** `P-DATA-01`  
**Mecanismos asociados:** `M-DATA-01`, `M-TX-01`  
**Consultas asociadas:** `EXT-Q22`

---

### 1.3 Modelos de estrés, sueño y selección de tier


**RF-11** El sistema debe ejecutar modelos de inferencia personalizados en el dispositivo o en capas cercanas para estimar estrés y calidad del sueño.
**Soporte ontológico:** `ex:AIModel`, `ex:LocalModelTier`, `ex:EdgeModelTier`, `ex:StressObservation`  
**Políticas asociadas:** `P-MODEL-01`†  
**Mecanismos asociados:** `M-MODEL-01`†, `M-NODE-02`†  
**Consultas asociadas:** `BASE-Q04`

**RF-12** El sistema debe mantener un modelo general global entrenado en la capa cloud, representado mediante conceptos generales de modelo y tier y no mediante una instancia concreta.
**Soporte ontológico:** `ex:AIModel`, `ex:CloudNode`, `ex:CloudModelTier`, `ex:hasModelTier`, `ex:modelVersion`, `ex:lastUpdated`  
**Políticas asociadas:** `P-MODEL-01`†, `P-FL-08`†  
**Mecanismos asociados:** `M-MODEL-01`†, `M-MODEL-05`†, `M-NODE-02`†, `M-VAL-04`†  
**Consultas asociadas:** `BASE-Q04`

**RF-13** El sistema debe permitir la adaptación del modelo general a modelos personalizados o degradados en capas inferiores.
**Soporte ontológico:** `ex:AIModel`, `ex:hasModelTier`, `ex:modelVersion`, `ex:lastUpdated`, `ex:hasDegradationCause`  
**Políticas asociadas:** `P-MODEL-01`†, `P-FL-08`†  
**Mecanismos asociados:** `M-MODEL-01`†, `M-MODEL-05`†, `M-NODE-02`†, `M-VAL-04`†  
**Consultas asociadas:** `BASE-Q04`, `BASE-Q32`

**RF-14** El sistema debe evaluar la calidad de las predicciones y registrar por separado la confianza de predicción, el error estimado, el feedback local y la calidad observada del modelo utilizado. Los pesos empleados para la selección multicriterio no deben utilizarse como sustituto de métricas observadas de calidad.
**Soporte ontológico:** `ex:predictionConfidence`, `ex:estimatedPredictionError`, `ex:userFeedbackScore`, `ex:observedModelQuality`  
**Políticas asociadas:** `P-MODEL-08`  
**Mecanismos asociados:** `M-AUD-01`, `M-METRIC-01`  
**Consultas asociadas:** `BASE-Q21`, `EXT-Q54`, `EXT-Q55`

**RF-15** El sistema debe seleccionar el tier de modelo más adecuado entre `LocalModelTier`, `EdgeModelTier`, `FogModelTier` y `CloudModelTier`, aplicando primero las restricciones duras de consentimiento, contrato, zona, disponibilidad y conectividad y, sobre las alternativas elegibles, considerando latencia, privacidad, calidad del modelo, carga y confianza. La selección debe reevaluarse y poder sustituirse cuando cambien las condiciones que la hicieron válida.
**Soporte ontológico:** `ex:EvaluationState`, `ex:DecisionAlternative`, `ex:hasDecisionAlternative`, `ex:selectedAlternative`, `ex:selectedModelTier`, `ex:hasLatencyWeight`, `ex:hasPrivacyWeight`, `ex:hasModelQualityWeight`, `ex:hasTrustAssessment`, `ex:LocalModelTier`, `ex:EdgeModelTier`, `ex:FogModelTier`  
**Políticas asociadas:** `P-MODEL-01`, `P-MODEL-09`, `P-NODE-02`, `P-OPS-06`, `P-ZONE-03`, `P-ZONE-04`  
**Mecanismos asociados:** `M-BUFFER-01`, `M-CONS-02`, `M-CTX-01`, `M-MODEL-01`, `M-MODEL-04`, `M-NODE-02`, `M-TX-02`, `M-ZONE-01`  
**Consultas asociadas:** `BASE-Q21`, `EXT-Q46`

---

### 1.4 Migración, offloading, degradación y continuidad de servicio


**RF-16** El sistema debe decidir dinámicamente cuándo migrar servicios de inferencia entre capas mist, edge, fog y cloud.
**Soporte ontológico:** `ex:Service`, `ex:ServiceState`, `ex:EvaluationState`, `ex:evaluatesService`, `ex:evaluatesNode`  
**Políticas asociadas:** `P-ADAPT-01`, `P-ADAPT-04`, `P-ADAPT-05`  
**Mecanismos asociados:** `M-ADAPT-01`, `M-ADAPT-03`, `M-AUD-01`, `M-FL-01`, `M-NODE-02`  
**Consultas asociadas:** `BASE-Q13`, `EXT-Q59`, `EXT-Q60`, `EXT-Q61`

**RF-17** El sistema debe migrar datos, servicios o modelos cuando se detecte batería baja, latencia excesiva, pérdida de conectividad, saturación, cambio de zona o bajo nivel de confianza del nodo actual, siempre dentro de las restricciones de RF-07, RF-35 y RF-42. Los nodos en estado `Inoperative` deben excluirse; los nodos `ComputeOnly` solo podrán utilizarse para operaciones compatibles con ese estado y, en caso contrario, deberán provocar delegación o aislamiento.
**Soporte ontológico:** `ex:DeviceState`, `ex:NodeState`, `ex:hasBatteryLevel`, `ex:hasCommunication`, `ex:hasWorkload`, `ex:hasTrustScore`, `ex:MAPESymptom`, `ex:ComputeOnly`, `ex:Inoperative`, `ex:MigrationEvent`, `ex:AdaptationAction`  
**Políticas asociadas:** `P-ADAPT-01`, `P-ADAPT-02`, `P-ADAPT-03`, `P-ADAPT-04`, `P-MODEL-09`, `P-NODE-01`, `P-OPS-02`, `P-ZONE-04`  
**Mecanismos asociados:** `M-ADAPT-01`, `M-ADAPT-02`, `M-AUD-01`, `M-BUFFER-01`, `M-CTX-01`, `M-MODEL-04`, `M-NODE-01`, `M-NODE-02`, `M-OPS-02`  
**Consultas asociadas:** `BASE-Q08`, `BASE-Q12`, `BASE-Q13`, `BASE-Q14`, `EXT-Q59`, `EXT-Q60`

**RF-18** El sistema debe permitir offloading de cómputo a dispositivos cercanos o nodos Edge/Fog cuando sea viable y no vulnere consentimiento, políticas de zona ni confianza mínima.
**Soporte ontológico:** `ex:hasNeighborNode`, `ex:delegatesTo`, `ex:DelegationEvent`, `ex:ConsentRange`, `ex:Policy`  
**Políticas asociadas:** `P-ADAPT-01`, `P-NODE-02`  
**Mecanismos asociados:** `M-ADAPT-01`, `M-CONS-02`, `M-NODE-02`, `M-ZONE-01`  
**Consultas asociadas:** `BASE-Q19`, `BASE-Q23`, `EXT-Q45`

**RF-19** El sistema debe soportar replicación controlada y sincronización de datos críticos, modelos y parámetros federados, distinguiendo las réplicas intencionadas de los duplicados accidentales y garantizando versionado e idempotencia de la sincronización.
**Soporte ontológico:** `ex:ParametrizedData`, `ex:isRedundant`, `ex:FederatedLearningSession`, `ex:updatesModel`, `ex:ReplicationEvent`, `ex:SynchronizationEvent`, `ex:replicaOf`, `ex:replicationVersion`, `ex:idempotencyKey`  
**Políticas asociadas:** `P-ADAPT-08`, `P-DATA-08`  
**Mecanismos asociados:** `M-DELEG-02`, `M-REPL-01`, `M-TX-01`, `M-TX-02`  
**Consultas asociadas:** `EXT-Q33`, `EXT-Q34`

**RF-20** Toda degradación de modelo o servicio debe quedar registrada con causa explícita.
**Soporte ontológico:** `ex:hasDegradationCause`, `ex:ModelDegradationCause`, `ex:CommunicationLoss`, `ex:LowBattery`, `ex:NoNearbyNodes`, `ex:InfrastructureOverload`  
**Políticas asociadas:** `P-ADAPT-03`, `P-ADAPT-06`  
**Mecanismos asociados:** `M-ADAPT-01`, `M-ADAPT-02`, `M-AUD-01`, `M-OPS-02`  
**Consultas asociadas:** `BASE-Q14`, `BASE-Q22`, `BASE-Q27`, `BASE-Q35`, `EXT-Q59`, `EXT-Q62`

---

### 1.5 Aprendizaje federado jerárquico y versionado de modelos


**RF-21** El sistema debe permitir enviar modelos personalizados, parámetros o gradientes a capas superiores para entrenamiento adicional cuando el consentimiento, la zona y la privacidad lo permitan.
**Soporte ontológico:** `ex:FederatedLearningSession`, `ex:hasPayloadType`, `ex:ModelGradientUpdate`, `ex:ConsentRange`, `ex:Policy`, `ex:ModelGradientsPayload`, `ex:AuthorizationDecision`  
**Políticas asociadas:** `P-FL-01`, `P-FL-02`  
**Mecanismos asociados:** `M-CONS-02`, `M-FL-01`, `M-NODE-02`, `M-ZONE-01`  
**Consultas asociadas:** `BASE-Q16`, `BASE-Q24`, `BASE-Q25`, `EXT-Q66`, `EXT-Q67`

**RF-22** El sistema debe soportar aprendizaje federado o jerárquico entre dispositivos y nodos Edge, Fog y Cloud.
**Soporte ontológico:** `ex:FederatedLearningSession`, `ex:involvedNode`, `ex:updatesModel`, `ex:EdgeNode`, `ex:FogNode`, `ex:CloudNode`  
**Políticas asociadas:** `P-ADAPT-05`, `P-FL-01`  
**Mecanismos asociados:** `M-ADAPT-03`, `M-FL-01`, `M-NODE-02`  
**Consultas asociadas:** `BASE-Q16`, `BASE-Q24`, `BASE-Q30`, `EXT-Q61`, `EXT-Q66`

**RF-23** El sistema debe redistribuir modelos actualizados hacia capas inferiores sin ampliar el rango de consentimiento vigente, siempre que el flujo descendente cumpla el contrato semántico y las políticas activas y no transporte datos personales ni gradientes individualizados.
**Soporte ontológico:** `ex:FederatedLearningSession`, `ex:hasPayloadType`, `ex:ImprovedModelParametersPayload`, `ex:updatesModel`  
**Políticas asociadas:** `P-CONS-06`, `P-FL-06`  
**Mecanismos asociados:** `M-CONS-02`, `M-FL-02`, `M-ZONE-01`  
**Consultas asociadas:** `EXT-Q66`

**RF-24** El sistema debe versionar modelos, registrar fecha de actualización y permitir rollback a versiones anteriores ante degradación, error o incumplimiento de política.
**Soporte ontológico:** `ex:modelVersion`, `ex:lastUpdated`, `ex:AIModel`, `ex:hasDegradationCause`, `ex:RollbackEvent`, `ex:rollbackTarget`, `ex:supersedesModel`, `ex:modelLineageStatus`  
**Políticas asociadas:** `P-FL-08`  
**Mecanismos asociados:** `M-MODEL-05`, `M-VAL-04`  
**Consultas asociadas:** `BASE-Q04`, `BASE-Q22`, `EXT-Q57`, `EXT-Q58`

**RF-25** Toda sesión HFL debe registrar tiempo de sesión, nodos involucrados, modelo actualizado, tipo de dato intercambiado y mecanismos de privacidad cuando aplique.
**Soporte ontológico:** `ex:FederatedLearningSession`, `ex:sessionTime`, `ex:involvedNode`, `ex:updatesModel`, `ex:hasPayloadType`, `ex:hasPrivacyBudget`, `ex:noiseLevel`, `ex:hasPrivacyMechanism`  
**Políticas asociadas:** `P-ADAPT-05`, `P-FL-01`, `P-FL-07`  
**Mecanismos asociados:** `M-ADAPT-03`, `M-AUD-01`, `M-FL-01`, `M-FL-02`, `M-NODE-02`  
**Consultas asociadas:** `BASE-Q16`, `BASE-Q24`, `EXT-Q66`

---

### 1.6 Gestión de conectividad y priorización de transmisión


**RF-26** El sistema debe detectar el tipo o estado de conexión disponible, incluyendo conexión estable, variable, intermitente, sin conexión, desconectado o modo avión, y debe soportar reconexión automática y sincronización posterior de los elementos pendientes cuando vuelva a existir una ventana autorizada y segura de transmisión.
**Soporte ontológico:** `ex:CommunicationLevel`, `ex:DeviceConnectionStatus`, `ex:StableComm`, `ex:IntermittentComm`, `ex:NoConnectionComm`, `ex:Connected`, `ex:Disconnected`, `ex:AirplaneMode`, `ex:SynchronizationEvent`  
**Políticas asociadas:** `P-ADAPT-08`, `P-DATA-05`, `P-DATA-07`, `P-OPS-06`, `P-ZONE-02`  
**Mecanismos asociados:** `M-BUFFER-01`, `M-CONS-02`, `M-DELEG-02`, `M-MODEL-04`, `M-NODE-02`, `M-REPL-01`, `M-TX-02`, `M-ZONE-01`  
**Consultas asociadas:** `BASE-Q10`

**RF-27** El sistema debe adaptar la frecuencia de transmisión según ancho de banda, energía disponible, redundancia, criticidad del dato, zona y consentimiento.
**Soporte ontológico:** `ex:hasBatteryLevel`, `ex:hasCommunication`, `ex:isRedundant`, `ex:ConsentRange`, `ex:CityArea`, `ex:DataCriticality`, `ex:hasDataCriticality`  
**Políticas asociadas:** `P-DATA-04`, `P-DATA-06`, `P-DATA-07`, `P-DATA-09`  
**Mecanismos asociados:** `M-ADAPT-02`, `M-BUFFER-01`, `M-CONS-02`, `M-DATA-02`, `M-DEVICE-01`, `M-NODE-02`, `M-TX-01`, `M-TX-02`, `M-TX-03`  
**Consultas asociadas:** `BASE-Q10`, `BASE-Q17`, `EXT-Q23`, `EXT-Q38`

**RF-28** El sistema debe priorizar datos críticos frente a datos secundarios, manteniendo localmente los datos redundantes o no transmisibles. La criticidad debe representarse mediante una clasificación genérica aplicable a cualquier dato; `StressCritical` puede utilizarse para estrés, pero no debe ser el único mecanismo de prioridad.
**Soporte ontológico:** `ex:ParametrizedData`, `ex:isRedundant`, `ex:DataCriticality`, `ex:CriticalData`, `ex:hasDataCriticality`  
**Políticas asociadas:** `P-DATA-08`, `P-DATA-09`  
**Mecanismos asociados:** `M-BUFFER-01`, `M-REPL-01`, `M-TX-01`, `M-TX-03`  
**Consultas asociadas:** `EXT-Q35`

---

### 1.7 Estudio de estrés, simulación y evaluación del sistema


**RF-29** El sistema debe recolectar métricas del sistema para estudios de estrés computacional, incluyendo uso de recursos, carga, colas, latencia, capacidad residual y coste de migración.
**Soporte ontológico:** `ex:resourceUsagePercent`, `ex:queuedRequests`, `ex:hasWorkload`, `ex:hasResidualCapacity`, `ex:hasMigrationTime`, `ex:hasMigrationCost`  
**Políticas asociadas:** `P-OPS-05`  
**Mecanismos asociados:** `M-METRIC-01`, `M-TIME-01`  
**Consultas asociadas:** `BASE-Q07`, `BASE-Q26`, `BASE-Q33`, `EXT-Q54`

**RF-30** El sistema debe correlacionar métricas fisiológicas con métricas del sistema para estudiar interacciones entre estrés humano, carga computacional, energía y conectividad, utilizando referencias temporales y contextuales comunes que permitan determinar qué estados y observaciones coexistían.
**Soporte ontológico:** `ex:UserState`, `ex:NodeState`, `ex:DeviceState`, `ex:StressObservation`, `ex:DataContext`, `ex:contextDeviceState`, `ex:contextNodeState`, `ex:validFrom`  
**Políticas asociadas:** `P-DATA-10`, `P-OPS-05`  
**Mecanismos asociados:** `M-DATA-02`, `M-METRIC-01`, `M-TIME-01`  
**Consultas asociadas:** `BASE-Q09`, `EXT-Q24`

**RF-31** El sistema debe permitir la simulación de escenarios urbanos con alta movilidad, alta carga, pérdida de conectividad, zona rural, zona restringida, saturación Edge y migración Edge→Fog. Los escenarios S1–S17 deben estar definidos en un artefacto o anexo versionado y referenciado de forma inequívoca para que este requisito sea reproducible.
**Soporte ontológico:** `ex:UrbanZone`, `ex:RuralZone`, `ex:RestrictedZone`, `ex:DelegationEvent`, `ex:EvaluationState`, `ex:Scenario`, `ex:ScenarioArtifact`, `ex:scenarioIdentifier`, `ex:partOfScenario`  
**Políticas asociadas:** `P-VAL-07`  
**Mecanismos asociados:** `M-VAL-04`, `M-VAL-06`  
**Consultas asociadas:** `BASE-Q11`, `BASE-Q12`, `BASE-Q13`, `BASE-Q17`, `EXT-Q05`

---

### 1.8 Consentimiento semántico y contratos consent-aware


**RF-32** El sistema debe representar el consentimiento mediante un modelo consent-aware basado en rangos de procesamiento, incluyendo consentimiento local, agregación comunitaria, agregación global y denegación/revocación explícita. El usuario debe poder establecer o revocar qué categorías de datos autoriza, con qué propósito, durante qué intervalo de validez y hasta qué rango del continuum.
**Soporte ontológico:** `ex:ConsentRecord`, `ex:ConsentRange`, `ex:RangeDenied`, `ex:RangeLocalOnly`, `ex:RangeCommunityAgg`, `ex:RangeGlobalAgg`  
**Políticas asociadas:** `P-CONS-01`  
**Mecanismos asociados:** `M-CONS-01`  
**Consultas asociadas:** `BASE-Q01`, `BASE-Q15`, `BASE-Q25`, `BASE-Q31`, `EXT-Q11`, `EXT-Q13`

**RF-33** Todo usuario debe estar vinculado a exactamente un contrato semántico efectivo por propósito de procesamiento en cada instante. Se permiten contratos históricos o para propósitos diferentes, pero sus intervalos de validez no deben producir más de un contrato efectivo para el mismo usuario y propósito en el mismo instante.
**Soporte ontológico:** `ex:SemanticContract`, `ex:contractSubject`, `ex:validFrom`, `ex:validTo`  
**Políticas asociadas:** `P-CONS-02`  
**Mecanismos asociados:** `M-CONS-01`, `M-TIME-01`  
**Consultas asociadas:** `BASE-Q20`, `EXT-Q12`, `EXT-Q14`, `EXT-Q15`

**RF-34** El contrato semántico debe vincular al usuario, el rango de consentimiento, el propósito de procesamiento y las políticas que gobiernan el tratamiento.
**Soporte ontológico:** `ex:contractSubject`, `ex:hasConsentRange`, `ex:hasProcessingPurpose`, `ex:governedBy`  
**Políticas asociadas:** `P-CONS-03`  
**Mecanismos asociados:** `M-CONS-01`, `M-GOV-02`  
**Consultas asociadas:** `BASE-Q20`, `EXT-Q12`, `EXT-Q14`

**RF-35** El sistema debe detectar inconsistencias entre el consentimiento activo del usuario y el rango declarado en su contrato semántico vigente. La autorización efectiva debe corresponder a la intersección más restrictiva entre consentimiento activo, contrato y política de zona; ante una inconsistencia no resuelta, debe bloquearse el procesamiento externo que pueda exceder cualquiera de esas restricciones.
**Soporte ontológico:** `ex:hasActiveConsentRange`, `ex:hasConsentRange`, `ex:SemanticContract`, `ex:ConsentRecord`, `ex:AuthorizationDecision`, `ex:hasEffectiveConsentRange`  
**Políticas asociadas:** `P-CONS-04`, `P-FL-02`, `P-GOV-03`, `P-MODEL-06`  
**Mecanismos asociados:** `M-CONS-02`, `M-FL-01`, `M-GOV-03`, `M-MODEL-01`, `M-ZONE-01`  
**Consultas asociadas:** `EXT-Q11`, `EXT-Q13`, `EXT-Q16`, `EXT-Q17`, `EXT-Q18`, `EXT-Q19`

**RF-36** El sistema debe impedir la selección de modelos o capas de procesamiento que excedan el rango de consentimiento activo del usuario.
**Soporte ontológico:** `ex:selectedModelTier`, `ex:hasActiveConsentRange`, `ex:requiresConsentRange`, `ex:ConsentRange`, `ex:AuthorizationDecision`, `ex:hasEffectiveConsentRange`  
**Políticas asociadas:** `P-CONS-04`, `P-ZONE-03`  
**Mecanismos asociados:** `M-CONS-02`, `M-GOV-03`, `M-NODE-02`, `M-ZONE-01`  
**Consultas asociadas:** `BASE-Q15`, `BASE-Q25`, `BASE-Q28`, `EXT-Q17`, `EXT-Q18`, `EXT-Q19`, `EXT-Q20`

**RF-37** Todo recurso, política, permiso, modelo, servicio o sesión que requiera consentimiento debe declarar el rango mínimo requerido mediante `requiresConsentRange`.
**Soporte ontológico:** `ex:requiresConsentRange`, `ex:ConsentRange`, `ex:Policy`, `ex:Permission`, `ex:AIModel`, `ex:Service`, `ex:FederatedLearningSession`  
**Políticas asociadas:** `P-CONS-05`  
**Mecanismos asociados:** `M-CONS-03`  
**Consultas asociadas:** `BASE-Q06`, `EXT-Q21`

**RF-38** La denegación o revocación del envío ascendente de datos personales no debe impedir que el usuario reciba modelos genéricos mejorados en flujo descendente, siempre que dicho flujo no contenga datos personales ni gradientes individualizados y cumpla el contrato y las políticas activas. Este requisito complementa RF-23 y no autoriza ninguna transferencia ascendente adicional.
**Soporte ontológico:** `ex:ConsentRecord`, `ex:RangeDenied`, `ex:RangeLocalOnly`, `ex:ImprovedModelParametersPayload`, `ex:hasPayloadType`, `ex:AIModel`  
**Políticas asociadas:** `P-CONS-06`, `P-FL-06`  
**Mecanismos asociados:** `M-CONS-02`, `M-FL-02`, `M-ZONE-01`  
**Consultas asociadas:** `BASE-Q15`

---

### 1.9 Gobernanza por políticas, tipos de política y zonas


**RF-39** El sistema debe representar las políticas como entidades semánticas explícitas y consultables.
**Soporte ontológico:** `ex:Policy`, `ex:PolicyCategory`, `ex:hasPolicyType`, `ex:belongsToPolicyCategory`  
**Políticas asociadas:** `P-GOV-01`  
**Mecanismos asociados:** `M-GOV-01`  
**Consultas asociadas:** `EXT-Q03`, `EXT-Q06`, `EXT-Q10`

**RF-40** Toda política formal debe estar clasificada en un único tipo semántico entre obligación, abstención o prohibición. A efectos del modelo: una obligación exige ejecutar una acción; una abstención exige no ejecutar una acción opcional salvo habilitación explícita; una prohibición declara una acción no permitida. Los tres tipos deben ser distinguibles y disjuntos en la validación.
**Soporte ontológico:** `ex:PolicyType`, `ex:ObligationPolicyType`, `ex:AbstentionPolicyType`, `ex:ProhibitionPolicyType`  
**Políticas asociadas:** `P-GOV-01`  
**Mecanismos asociados:** `M-GOV-01`  
**Consultas asociadas:** `EXT-Q03`, `EXT-Q06`, `EXT-Q10`

**RF-41** El sistema debe vincular usuarios, nodos, zonas, contratos o evaluaciones con políticas específicas mediante `governedBy`.
**Soporte ontológico:** `ex:governedBy`, `ex:Policy`, `ex:SemanticContract`, `ex:EvaluationState`  
**Políticas asociadas:** `P-CONS-03`, `P-GOV-02`  
**Mecanismos asociados:** `M-AUD-01`, `M-CONS-01`, `M-GOV-02`  
**Consultas asociadas:** `EXT-Q03`‡, `EXT-Q08`‡, `EXT-Q12`‡, `EXT-Q70`‡

**RF-42** El sistema debe aplicar políticas específicas por zona: retención local en zona rural, bloqueo de transferencia externa en zona restringida y agregación en zona urbana únicamente cuando el consentimiento efectivo y el contrato la autoricen. Cuando zona, consentimiento y contrato impongan restricciones diferentes, debe prevalecer siempre la condición más restrictiva.
**Soporte ontológico:** `ex:RuralZone`, `ex:RestrictedZone`, `ex:UrbanZone`, `ex:Policy`  
**Políticas asociadas:** `P-FL-02`, `P-GOV-03`, `P-MODEL-06`, `P-ZONE-01`, `P-ZONE-02`, `P-ZONE-03`  
**Mecanismos asociados:** `M-BUFFER-01`, `M-CONS-02`, `M-FL-01`, `M-GOV-03`, `M-MODEL-01`, `M-NODE-02`, `M-TX-02`, `M-ZONE-01`  
**Consultas asociadas:** `BASE-Q18`, `BASE-Q34`, `EXT-Q36`, `EXT-Q37`, `EXT-Q39`

**RF-43** El sistema debe bloquear cualquier procesamiento o transferencia fuera del ámbito local definido en RF-10 cuando el origen se encuentre en una `RestrictedZone`, incluyendo la selección de tiers Edge, Fog o Cloud, salvo que una política explícita más restrictiva establezca todavía menos procesamiento.
**Soporte ontológico:** `ex:RestrictedZone`, `ex:LocalModelTier`, `ex:EdgeModelTier`, `ex:FogModelTier`, `ex:CloudModelTier`  
**Políticas asociadas:** `P-GOV-03`, `P-ZONE-01`  
**Mecanismos asociados:** `M-CONS-02`, `M-GOV-03`, `M-ZONE-01`  
**Consultas asociadas:** `BASE-Q18`, `BASE-Q34`, `EXT-Q36`, `EXT-Q37`

**RF-44** El sistema debe registrar qué política concreta se aplicó en cada evaluación, degradación, migración, delegación o decisión de selección de modelo.
**Soporte ontológico:** `ex:EvaluationState`, `ex:appliedPolicy`, `ex:governedBy`, `ex:AdaptationAction`  
**Políticas asociadas:** `P-ADAPT-06`, `P-GOV-02`  
**Mecanismos asociados:** `M-ADAPT-02`, `M-AUD-01`, `M-GOV-02`  
**Consultas asociadas:** `EXT-Q59`‡, `EXT-Q63`‡, `EXT-Q70`‡, `EXT-Q72`‡

---

### 1.10 Confianza dinámica y orquestación trust-based


**RF-45** Todo `NodeState` usado en decisiones MAPE-K debe registrar un valor de confianza histórica.
**Soporte ontológico:** `ex:hasTrustScore`, `ex:TrustAssessment`, `ex:trustAssessmentForState`, `ex:NodeState`  
**Políticas asociadas:** `P-NODE-03`  
**Mecanismos asociados:** `M-TRUST-01`, `M-VAL-04`  
**Consultas asociadas:** `BASE-Q07`, `EXT-Q40`

**RF-46** Toda evaluación que compare nodos debe registrar un valor o peso de confianza consultable utilizado como criterio externo al cálculo AHP. La confianza debe aplicarse para filtrar u ordenar alternativas elegibles, pero no debe mezclarse con los pesos AHP definidos en RF-50.
**Soporte ontológico:** `ex:TrustAssessment`, `ex:hasTrustWeight`, `ex:hasTrustScore`, `ex:EvaluationState`, `ex:evaluatesNode`  
**Políticas asociadas:** `P-MODEL-03`, `P-NODE-05`  
**Mecanismos asociados:** `M-MODEL-02`, `M-NODE-02`, `M-TRUST-02`  
**Consultas asociadas:** `EXT-Q44`

**RF-47** La selección de nodos debe aplicar primero restricciones de elegibilidad por disponibilidad, conectividad, consentimiento, zona y capacidad mínima. Entre los nodos elegibles, el sistema debe priorizar los de mayor confianza y evitar nodos saturados, inestables o históricamente poco fiables.
**Soporte ontológico:** `ex:TrustAssessment`, `ex:hasTrustScore`, `ex:NodeState`, `ex:hasAvailability`, `ex:hasCommunication`, `ex:hasWorkload`, `ex:hasResidualCapacity`  
**Políticas asociadas:** `P-NODE-02`, `P-NODE-05`, `P-NODE-06`  
**Mecanismos asociados:** `M-ADAPT-02`, `M-AUD-01`, `M-CONS-02`, `M-NODE-02`, `M-TRUST-02`, `M-ZONE-01`  
**Consultas asociadas:** `BASE-Q08`, `BASE-Q19`, `EXT-Q41`, `EXT-Q42`

**RF-48** Toda delegación debe seleccionar preferentemente, entre los destinos elegibles, el nodo con mayor confianza compatible con la carga, disponibilidad, conectividad, capacidad residual y restricciones activas. No se exige que el destino tenga mayor trust score que el nodo origen cuando la degradación del origen se deba a una causa distinta de la confianza.
**Soporte ontológico:** `ex:DelegationEvent`, `ex:delegatedBy`, `ex:delegatesTo`, `ex:TrustAssessment`, `ex:hasTrustScore`  
**Políticas asociadas:** `P-ADAPT-07`, `P-NODE-05`, `P-NODE-06`  
**Mecanismos asociados:** `M-ADAPT-02`, `M-AUD-01`, `M-DELEG-01`, `M-NODE-02`, `M-TRUST-02`  
**Consultas asociadas:** `BASE-Q19`, `EXT-Q42`, `EXT-Q45`

**RF-49** El sistema debe actualizar el trust score de un nodo a partir de comportamiento histórico, fallos, desconexiones, saturación e incumplimientos de políticas mediante una escala normalizada, una ventana temporal y una regla de actualización documentadas. Si latencia o carga participan en el cálculo de confianza, la decisión posterior debe evitar contabilizar dos veces el mismo efecto como criterio independiente sin justificación explícita.
**Soporte ontológico:** `ex:TrustAssessment`, `ex:hasTrustEvidence`, `ex:trustRuleVersion`, `ex:trustWindowStart`, `ex:trustWindowEnd`  
**Políticas asociadas:** `P-NODE-03`, `P-NODE-04`  
**Mecanismos asociados:** `M-AUD-01`, `M-TRUST-01`, `M-VAL-04`  
**Consultas asociadas:** `EXT-Q40`, `EXT-Q43`

---

### 1.11 Decisión multicriterio AHP y explicación de selección


**RF-50** Toda `EvaluationState` que utilice AHP debe registrar pesos normalizados para latencia, privacidad y calidad del modelo. La suma de esos pesos debe ser 1 dentro de la tolerancia configurada. La confianza se trata como criterio externo según RF-46 y no forma parte de esta normalización.
**Soporte ontológico:** `ex:hasLatencyWeight`, `ex:hasPrivacyWeight`, `ex:hasModelQualityWeight`, `ex:EvaluationState`  
**Políticas asociadas:** `P-MODEL-02`, `P-MODEL-03`  
**Mecanismos asociados:** `M-MODEL-02`, `M-TRUST-02`  
**Consultas asociadas:** `EXT-Q48`

**RF-51** Toda `EvaluationState` debe registrar la puntuación AHP de cada alternativa de tier evaluada, el tier finalmente seleccionado y una justificación que permita reconstruir por qué la alternativa elegida superó a las demás.
**Soporte ontológico:** `ex:hasAHPScore`, `ex:selectedModelTier`, `ex:hasSelectionJustification`, `ex:DecisionAlternative`, `ex:hasDecisionAlternative`, `ex:selectedAlternative`, `ex:EvaluationState`  
**Políticas asociadas:** `P-AUD-06`, `P-MODEL-05`  
**Mecanismos asociados:** `M-AUD-01`, `M-MODEL-01`  
**Consultas asociadas:** `EXT-Q46`, `EXT-Q51`, `EXT-Q52`, `EXT-Q53`

**RF-52** El sistema debe favorecer modelos locales o Edge cuando el peso de privacidad sea dominante o cuando el consentimiento no permita agregación global.
**Soporte ontológico:** `ex:hasPrivacyWeight`, `ex:RangeLocalOnly`, `ex:RangeCommunityAgg`, `ex:LocalModelTier`, `ex:EdgeModelTier`, `ex:AuthorizationDecision`  
**Políticas asociadas:** `P-MODEL-01`, `P-MODEL-06`  
**Mecanismos asociados:** `M-CONS-02`, `M-MODEL-01`, `M-NODE-02`, `M-ZONE-01`  
**Consultas asociadas:** `BASE-Q15`‡, `EXT-Q46`‡, `EXT-Q51`‡, `EXT-Q56`‡

**RF-53** El sistema debe permitir seleccionar `CloudModelTier` únicamente cuando consentimiento efectivo, contrato, zona y confianza lo permitan. La privacidad diferencial será obligatoria cuando la operación hacia Cloud implique aprendizaje federado, gradientes o actualizaciones para las que las políticas de privacidad la exijan; no debe imponerse como condición genérica a una inferencia que no transporte ese tipo de información.
**Soporte ontológico:** `ex:CloudModelTier`, `ex:AuthorizationDecision`, `ex:hasTrustAssessment`, `ex:hasPrivacyBudgetAccount`  
**Políticas asociadas:** `P-MODEL-01`, `P-MODEL-07`, `P-NODE-06`, `P-ZONE-01`  
**Mecanismos asociados:** `M-ADAPT-02`, `M-AUD-01`, `M-CONS-02`, `M-FL-03`, `M-MODEL-01`, `M-NODE-02`, `M-ZONE-01`  
**Consultas asociadas:** `EXT-Q56`

**RF-54** El sistema debe detectar evaluaciones incompletas que no incluyan los pesos AHP aplicables, las puntuaciones de las alternativas evaluadas, el tier seleccionado, la política aplicada, el contrato semántico y la justificación.
**Soporte ontológico:** `ex:EvaluationState`, `ex:hasLatencyWeight`, `ex:hasPrivacyWeight`, `ex:hasModelQualityWeight`, `ex:selectedModelTier`, `ex:hasSelectionJustification`, `ex:appliedPolicy`, `ex:hasDecisionAlternative`, `ex:auditsContract`, `ex:resultedInAction`  
**Políticas asociadas:** `P-AUD-06`, `P-MODEL-05`  
**Mecanismos asociados:** `M-AUD-01`, `M-MODEL-01`  
**Consultas asociadas:** `EXT-Q47`, `EXT-Q53`, `EXT-Q55`, `EXT-Q71`

**RF-55** El sistema debe advertir o marcar como inválida una evaluación AHP cuando los pesos no estén normalizados, cuando se mezcle el peso de confianza dentro de la normalización AHP o cuando la consistencia de los juicios AHP supere el umbral configurado. La ontología debe representar explícitamente la métrica/ratio de consistencia y el umbral aplicado; si no se emplean comparaciones por pares ni control de consistencia, el mecanismo debe documentarse como puntuación multicriterio ponderada y no como AHP.
**Soporte ontológico:** `ex:hasConsistencyRatio`, `ex:hasConsistencyThreshold`, `ex:AHPDecisionMethod`, `ex:WeightedMulticriteriaMethod`  
**Políticas asociadas:** `P-MODEL-02`, `P-MODEL-03`, `P-MODEL-04`  
**Mecanismos asociados:** `M-MODEL-02`, `M-MODEL-03`, `M-TRUST-02`  
**Consultas asociadas:** `EXT-Q44`, `EXT-Q48`, `EXT-Q49`, `EXT-Q50`

---

### 1.12 Privacidad diferencial y seguridad de flujos federados


**RF-56** Toda sesión de aprendizaje federado que transporte gradientes debe declarar presupuesto de privacidad y nivel de ruido.
**Soporte ontológico:** `ex:FederatedLearningSession`, `ex:hasPrivacyBudget`, `ex:noiseLevel`, `ex:hasPayloadType`  
**Políticas asociadas:** `P-FL-03`, `P-MODEL-07`  
**Mecanismos asociados:** `M-FL-03`, `M-ID-01`, `M-MODEL-01`  
**Consultas asociadas:** `BASE-Q16`, `EXT-Q67`, `EXT-Q69`

**RF-57** Todo gradiente de modelo que salga de un dispositivo móvil debe haber pasado por anonimización y adición de ruido.
**Soporte ontológico:** `ex:ModelGradientUpdate`, `ex:hasNoiseApplied`, `ex:hasAnonymizationApplied`, `ex:MobileDevice`, `ex:hasPrivacyMechanism`  
**Políticas asociadas:** `P-FL-03`  
**Mecanismos asociados:** `M-FL-03`, `M-ID-01`  
**Consultas asociadas:** `EXT-Q68`

**RF-58** Toda sesión FL protegida debe estar vinculada a un mecanismo explícito de privacidad o anonimización.
**Soporte ontológico:** `ex:PrivacyMechanism`, `ex:DifferentialPrivacyMechanism`, `ex:hasPrivacyMechanism`, `ex:FederatedLearningSession`  
**Políticas asociadas:** `P-FL-05`  
**Mecanismos asociados:** `M-FL-03`, `M-ID-01`  
**Consultas asociadas:** `BASE-Q16`, `EXT-Q68`

**RF-59** El sistema debe controlar el presupuesto epsilon de privacidad diferencial de acuerdo con el propósito de procesamiento, el contrato semántico y la política activa.
**Soporte ontológico:** `ex:hasPrivacyBudget`, `ex:ProcessingPurpose`, `ex:SemanticContract`, `ex:Policy`, `ex:PrivacyBudgetAccount`, `ex:privacyBudgetMaximum`, `ex:privacyBudgetConsumed`, `ex:privacyBudgetRemaining`, `ex:budgetForContract`  
**Políticas asociadas:** `P-FL-04`, `P-MODEL-07`  
**Mecanismos asociados:** `M-AUD-01`, `M-FL-03`, `M-FL-04`, `M-MODEL-01`  
**Consultas asociadas:** `BASE-Q24`, `EXT-Q69`

**RF-60** El sistema debe impedir que observaciones fisiológicas crudas abandonen el ámbito local definido en RF-10; por tanto, no deben transmitirse a nodos Edge, Fog ni Cloud. Solo datos parametrizados o actualizaciones de modelo autorizadas pueden salir del ámbito local.
**Soporte ontológico:** `ex:TransferEvent`, `ex:PhysiologicalObservation`, `ex:SleepObservation`, `ex:ParametrizedData`, `ex:EdgeNode`, `ex:FogNode`, `ex:CloudNode`  
**Políticas asociadas:** `P-DATA-01`  
**Mecanismos asociados:** `M-DATA-01`, `M-TX-01`  
**Consultas asociadas:** `BASE-Q18`, `BASE-Q28`, `EXT-Q22`, `EXT-Q37`

---

### 1.13 Pseudonimización y protección de identificadores


**RF-61** Todo dato parametrizado, gradiente o actualización transmitida fuera del ámbito local debe utilizar identificadores pseudónimos o anonimizados. Los identificadores personales directos no deben viajar junto con datos parametrizados, gradientes ni actualizaciones federadas, y debe existir una consulta de incumplimiento que permita detectar cualquier violación de esta regla.
**Soporte ontológico:** `ex:Identifier`, `ex:PseudonymousIdentifier`, `ex:AnonymousIdentifier`, `ex:DirectIdentifier`, `ex:usesIdentifier`, `ex:TransferEvent`  
**Políticas asociadas:** `P-DATA-02`  
**Mecanismos asociados:** `M-ID-01`, `M-TX-01`  
**Consultas asociadas:** `BASE-Q01`, `BASE-Q28`, `EXT-Q23`, `EXT-Q26`, `EXT-Q27`, `EXT-Q28`

---

### 1.14 Delegación temporal, eventos MAPE-K y auditoría semántica


**RF-62** Toda delegación temporal debe representarse como un evento semántico explícito.
**Soporte ontológico:** `ex:DelegationEvent`, `ex:delegatedBy`, `ex:delegatesTo`, `ex:triggeredByState`, `ex:validFrom`, `ex:hasRecoveryCondition`  
**Políticas asociadas:** `P-ADAPT-05`, `P-ADAPT-07`, `P-AUD-01`  
**Mecanismos asociados:** `M-ADAPT-03`, `M-DELEG-01`, `M-FL-01`, `M-TRUST-02`  
**Consultas asociadas:** `BASE-Q14`, `EXT-Q63`

**RF-63** El evento de delegación debe registrar origen, destino, causa, inicio de validez y condición de recuperación. `validTo` debe representar el cierre efectivo de la delegación y puede permanecer sin valor mientras esté activa. Si existe una expiración planificada distinta del cierre real, debe representarse mediante un límite temporal explícito adicional y no reutilizando ambiguamente `validTo`.
**Soporte ontológico:** `ex:DelegationEvent`, `ex:delegatedBy`, `ex:delegatesTo`, `ex:hasRecoveryCondition`, `ex:plannedExpiry`, `ex:validFrom`, `ex:validTo`  
**Políticas asociadas:** `P-AUD-02`  
**Mecanismos asociados:** `M-DELEG-01`, `M-TIME-01`  
**Consultas asociadas:** `EXT-Q63`, `EXT-Q64`

**RF-64** El sistema debe cerrar o invalidar una delegación cuando se cumpla la condición de recuperación del nodo origen o se alcance su expiración planificada. En ese momento debe registrar `validTo` como instante de cierre efectivo.
**Soporte ontológico:** `ex:DelegationEvent`, `ex:hasRecoveryCondition`, `ex:plannedExpiry`, `ex:validTo`  
**Políticas asociadas:** `P-AUD-03`  
**Mecanismos asociados:** `M-DELEG-02`  
**Consultas asociadas:** `EXT-Q63`

**RF-65** El sistema debe representar síntomas MAPE-K detectados y vincularlos con políticas y evaluaciones.
**Soporte ontológico:** `ex:MAPESymptom`, `ex:hasDetectedSymptom`, `ex:appliedPolicy`, `ex:EvaluationState`  
**Políticas asociadas:** `P-AUD-05`  
**Mecanismos asociados:** `M-AUD-02`  
**Consultas asociadas:** `BASE-Q14`, `BASE-Q35`, `EXT-Q72`

**RF-66** Cada `EvaluationState` debe actuar como ticket de auditoría semántica completo y registrar, como mínimo, síntoma, política aplicada, contrato, consentimiento efectivo, tier seleccionado, justificación, instante de decisión y referencia a la acción finalmente ejecutada.
**Soporte ontológico:** `ex:EvaluationState`, `ex:hasDetectedSymptom`, `ex:appliedPolicy`, `ex:auditsContract`, `ex:hasAuthorizationDecision`, `ex:selectedModelTier`, `ex:hasSelectionJustification`, `ex:resultedInAction`  
**Políticas asociadas:** `P-ADAPT-06`, `P-AUD-05`, `P-AUD-06`  
**Mecanismos asociados:** `M-ADAPT-02`, `M-AUD-01`, `M-AUD-02`  
**Consultas asociadas:** `BASE-Q21`, `EXT-Q17`, `EXT-Q20`, `EXT-Q46`, `EXT-Q47`, `EXT-Q59`, `EXT-Q71`, `EXT-Q72`

**RF-67** El sistema debe poder reconstruir la cadena completa de decisión: usuario → contrato → consentimiento efectivo → propósito → zona → política → estado de nodo → alternativas y puntuaciones AHP → confianza externa → tier seleccionado → acción ejecutada, conservando las relaciones causales y temporales necesarias para identificar qué información estaba vigente en el instante de la decisión.
**Soporte ontológico:** `ex:evaluationUser`, `ex:auditsContract`, `ex:hasEffectiveConsentRange`, `ex:evaluationPurpose`, `ex:evaluationZone`, `ex:hasDecisionAlternative`, `ex:hasTrustAssessment`, `ex:resultedInAction`  
**Políticas asociadas:** `P-AUD-05`, `P-AUD-07`  
**Mecanismos asociados:** `M-AUD-02`, `M-AUD-03`, `M-TIME-01`  
**Consultas asociadas:** `BASE-Q35`, `EXT-Q70`

**RF-68** El sistema debe generar métricas de cumplimiento global de la arquitectura mediante consultas SPARQL de cobertura y validación. El conjunto de clases y propiedades críticas debe identificarse mediante la versión concreta de la ontología cargada y registrada en la matriz de trazabilidad; no debe depender de una referencia ambigua como “v2.1” sin identificar el artefacto correspondiente.
**Soporte ontológico:** `ex:OntologyArtifact`, `ex:PolicyArtifact`, `ex:RequirementsArtifact`, `ex:ScenarioArtifact`, `ex:QuerySpecification`, `ex:QueryType`  
**Políticas asociadas:** `P-VAL-04`, `P-VAL-08`  
**Mecanismos asociados:** `M-GOV-04`, `M-VAL-04`, `M-VAL-07`  
**Consultas asociadas:** `BASE-Q31`, `BASE-Q32`, `EXT-Q01`, `EXT-Q02`, `EXT-Q80`

---

### 1.15 Validación SPARQL, consistencia y operación sobre Fuseki


**RF-69** El sistema debe exponer la ontología en un endpoint SPARQL 1.1. Apache Jena Fuseki será el entorno de referencia para reproducibilidad; podrán utilizarse endpoints equivalentes en operación siempre que mantengan compatibilidad con RDF/OWL/Turtle y SPARQL 1.1 y superen la misma batería de validación.
**Soporte ontológico:** `ex:OntologyArtifact`, `ex:QuerySpecification`, `SPARQL 1.1`, `RDF/OWL/Turtle`  
**Políticas asociadas:** `P-VAL-01`  
**Mecanismos asociados:** `M-VAL-01`  
**Consultas asociadas:** `EXT-Q01`‡, `EXT-Q75`‡, `EXT-Q77`‡; además, la conformidad se comprueba ejecutando la batería v3 completa en el endpoint de referencia

**RF-70** El sistema debe disponer de consultas de inspección para listar usuarios, dispositivos, nodos, modelos, estados, políticas, contratos, sesiones FL y delegaciones.
**Soporte ontológico:** `ex:QuerySpecification`, `ex:InspectionQueryType`, `ex:User`, `ex:Wearable`, `ex:ComputationalNode`, `ex:AIModel`, `ex:State`, `ex:Policy`, `ex:SemanticContract`, `ex:FederatedLearningSession`, `ex:DelegationEvent`  
**Políticas asociadas:** `P-VAL-02`  
**Mecanismos asociados:** `M-VAL-02`  
**Consultas asociadas:** `BASE-Q01`, `BASE-Q02`, `BASE-Q03`, `BASE-Q04`, `BASE-Q05`, `BASE-Q06`, `BASE-Q07`, `BASE-Q20`, `EXT-Q03`

**RF-71** El sistema debe disponer de consultas de incumplimiento cuyo resultado de cero filas pueda interpretarse como cumplimiento únicamente después de comprobar que el dataset requerido está cargado, que la versión de ontología es la esperada, que los datos mínimos de cobertura existen y que la consulta se ejecutó correctamente. Un resultado vacío sin esas precondiciones no constituye evidencia suficiente de cumplimiento.
**Soporte ontológico:** `ex:ViolationQueryType`, `ex:ValidationCampaign`, `ex:AcceptanceProfile`, `ex:OntologyArtifact`, `ex:ScenarioArtifact`  
**Políticas asociadas:** `P-VAL-02`, `P-VAL-03`  
**Mecanismos asociados:** `M-VAL-02`, `M-VAL-03`  
**Consultas asociadas:** `EXT-Q75`, `EXT-Q77`, `EXT-Q80`

**RF-72** El sistema debe permitir la validación de escenarios operativos y científicos mediante consultas SPARQL reproducibles, utilizando el artefacto versionado de escenarios exigido por RF-31 y el entorno de referencia definido en RF-69.
**Soporte ontológico:** `ex:Scenario`, `ex:ScenarioArtifact`, `ex:ValidationCampaign`, `ex:QuerySpecification`  
**Políticas asociadas:** `P-VAL-07`  
**Mecanismos asociados:** `M-VAL-04`, `M-VAL-06`  
**Consultas asociadas:** `BASE-Q11`, `EXT-Q05`, `EXT-Q77`

---

## 2. Requisitos No Funcionales (RNF)

Los requisitos no funcionales definen propiedades de calidad y criterios de aceptación. Las reglas que describían comportamiento funcional han sido integradas en los RF correspondientes para evitar duplicidad. Los umbrales configurables usados en esta sección deben quedar fijados antes de una campaña de aceptación en un **perfil de aceptación versionado**. Como mínimo dicho perfil debe declarar `T_inference_local`, `T_migration_max`, `T_sparql_monitor`, `T_decision_max`, `E_device_max`, `N_agents`, `T_node_join`, `D_delegation_max` y `T_reselection_max`.

---

### 2.1 Rendimiento

**RNF-01** La latencia de inferencia local en dispositivo o mist debe ser ≤100 ms en el percentil 95 bajo el perfil hardware/modelo de referencia. Si un despliegue requiere otro valor, deberá declararse explícitamente como `T_inference_local` antes de la validación y no podrá modificarse durante la campaña de aceptación.
**Soporte ontológico:** `ex:AcceptanceProfile`, `ex:T_inference_local`  
**Políticas asociadas:** `P-OPS-01`  
**Mecanismos asociados:** `M-OPS-01`, `M-VAL-04`  
**Consultas asociadas:** `EXT-Q76`

**RNF-02** Una migración o delegación de servicio no debe producir una interrupción superior a `T_migration_max` ni pérdida de decisiones o eventos marcados como críticos.
**Soporte ontológico:** `ex:AcceptanceProfile`, `ex:T_migration_max`, `ex:MigrationEvent`, `ex:DelegationEvent`, `ex:DataCriticality`  
**Políticas asociadas:** `P-ADAPT-04`, `P-ADAPT-08`, `P-OPS-01`  
**Mecanismos asociados:** `M-ADAPT-01`, `M-AUD-01`, `M-DELEG-02`, `M-NODE-02`, `M-OPS-01`, `M-REPL-01`, `M-TX-02`, `M-VAL-04`  
**Consultas asociadas:** `EXT-Q76`

**RNF-03** Los escenarios de pico de carga deben mantener el servicio dentro de los límites declarados en el perfil de aceptación y, cuando sea necesario degradar, migrar, delegar o retener, la degradación debe ser controlada y auditable.
**Soporte ontológico:** `ex:AcceptanceProfile`, `ex:AdaptationAction`, `ex:DegradationEvent`, `ex:MigrationEvent`, `ex:DelegationEvent`, `ex:BufferRecord`  
**Políticas asociadas:** `P-ADAPT-01`, `P-ADAPT-03`  
**Mecanismos asociados:** `M-ADAPT-01`, `M-ADAPT-02`, `M-NODE-02`, `M-OPS-02`  
**Consultas asociadas:** `BASE-Q12`‡, `EXT-Q59`‡, `EXT-Q62`‡, `EXT-Q76`‡

**RNF-04** Las consultas SPARQL de monitorización básica utilizadas por el ciclo MAPE-K deben completar su ejecución dentro de `T_sparql_monitor` en el percentil 95 sobre el dataset de referencia.
**Soporte ontológico:** `ex:AcceptanceProfile`, `ex:T_sparql_monitor`, `ex:QuerySpecification`  
**Políticas asociadas:** `P-OPS-01`  
**Mecanismos asociados:** `M-OPS-01`, `M-VAL-04`  
**Consultas asociadas:** `EXT-Q76`

**RNF-05** El cálculo de la puntuación multicriterio AHP y la aplicación del criterio externo de confianza deben completarse dentro de `T_decision_max` para no exceder el intervalo de adaptación definido por la política activa.
**Soporte ontológico:** `ex:AcceptanceProfile`, `ex:T_decision_max`, `ex:EvaluationState`, `ex:TrustAssessment`  
**Políticas asociadas:** `P-MODEL-03`, `P-OPS-01`  
**Mecanismos asociados:** `M-MODEL-02`, `M-OPS-01`, `M-TRUST-02`, `M-VAL-04`  
**Consultas asociadas:** `EXT-Q76`

---

### 2.2 Eficiencia energética

**RNF-06** El consumo energético del dispositivo bajo el escenario de referencia debe mantenerse dentro de `E_device_max`, registrando consumo o impacto sobre autonomía de forma reproducible. Las estrategias de batería baja no deben incrementar transmisiones no críticas respecto al modo normal.
**Soporte ontológico:** `ex:AcceptanceProfile`, `ex:E_device_max`, `ex:DeviceState`, `ex:hasBatteryLevel`  
**Políticas asociadas:** `P-DATA-06`, `P-OPS-01`  
**Mecanismos asociados:** `M-ADAPT-02`, `M-BUFFER-01`, `M-DEVICE-01`, `M-OPS-01`, `M-VAL-04`  
**Consultas asociadas:** `EXT-Q76`

---

### 2.3 Escalabilidad

**RNF-07** La arquitectura debe permitir escalado horizontal en Cloud y, cuando exista infraestructura Fog disponible, en Fog, sin modificar el modelo conceptual central.
**Soporte ontológico:** `ex:CloudNode`, `ex:FogNode`, `ex:hasElasticity`  
**Políticas asociadas:** `P-OPS-02`  
**Mecanismos asociados:** `M-OPS-02`  
**Consultas asociadas:** `BASE-Q29`

**RNF-08** El objetivo de concurrencia debe expresarse mediante el valor explícito `N_agents` en lugar de términos ambiguos como “miles de agentes”; la campaña de carga debe demostrar operación concurrente con al menos ese valor.
**Soporte ontológico:** `ex:AcceptanceProfile`, `ex:N_agents`, `ex:User`  
**Políticas asociadas:** `P-OPS-01`  
**Mecanismos asociados:** `M-OPS-01`, `M-VAL-04`  
**Consultas asociadas:** `EXT-Q76`

**RNF-09** La incorporación de un nuevo nodo Edge o Fog no debe requerir detener el sistema completo y debe quedar disponible para evaluación dentro de `T_node_join` tras completar su registro y validación.
**Soporte ontológico:** `ex:AcceptanceProfile`, `ex:T_node_join`, `ex:EdgeNode`, `ex:FogNode`  
**Políticas asociadas:** `P-OPS-01`, `P-OPS-03`  
**Mecanismos asociados:** `M-NODE-01`, `M-OPS-01`, `M-OPS-03`, `M-VAL-04`  
**Consultas asociadas:** `EXT-Q76`

**RNF-10** La ontología debe permitir añadir nuevos usuarios, nodos, sensores, modelos, políticas y contratos mediante extensión de instancias o especializaciones compatibles, sin modificar las abstracciones conceptuales centrales utilizadas por los escenarios existentes.
**Soporte ontológico:** `ex:User`, `ex:ComputationalNode`, `ex:PhysiologicalSensor`, `ex:AIModel`, `ex:Policy`, `ex:SemanticContract`  
**Políticas asociadas:** `P-INT-02`, `P-OPS-03`  
**Mecanismos asociados:** `M-INT-02`, `M-NODE-01`, `M-OPS-03`, `M-VAL-05`  
**Consultas asociadas:** `EXT-Q01`‡, `EXT-Q02`‡, `EXT-Q03`‡, `EXT-Q04`‡, `EXT-Q05`‡

**RNF-11** La batería de consultas debe admitir nuevos bloques `BASE-Q` o `EXT-Q` sin cambiar el significado ni romper la ejecución de las consultas existentes que formen parte de la línea base.
**Soporte ontológico:** `ex:QuerySpecification`, `ex:QueryCatalog`  
**Políticas asociadas:** `P-VAL-05`  
**Mecanismos asociados:** `M-VAL-04`, `M-VAL-05`  
**Consultas asociadas:** `EXT-Q01`‡, `EXT-Q77`‡, `EXT-Q80`‡

---

### 2.4 Fiabilidad y tolerancia a fallos

**RNF-12** Ante fallos parciales de conectividad, las funciones críticas autorizadas para ejecución local deben continuar operativas y los datos pendientes deben conservar integridad hasta su sincronización o descarte autorizado.
**Soporte ontológico:** `ex:DeviceConnectionStatus`, `ex:BufferRecord`, `ex:SynchronizationEvent`, `ex:DataCriticality`  
**Políticas asociadas:** `P-ADAPT-02`, `P-DATA-05`, `P-DATA-07`, `P-FL-01`, `P-NODE-01`, `P-OPS-04`, `P-OPS-06`  
**Mecanismos asociados:** `M-ADAPT-02`, `M-BUFFER-01`, `M-CONS-02`, `M-FL-01`, `M-MODEL-04`, `M-NODE-01`, `M-NODE-02`, `M-TX-02`, `M-ZONE-01`  
**Consultas asociadas:** `BASE-Q08`, `EXT-Q31`, `EXT-Q32`

**RNF-13** Los procesos de reconexión, sincronización, migración y delegación no deben provocar pérdida de eventos críticos ni crear duplicados accidentales; las reejecuciones deben ser idempotentes cuando corresponda.
**Soporte ontológico:** `ex:SynchronizationEvent`, `ex:ReplicationEvent`, `ex:idempotencyKey`, `ex:DataCriticality`  
**Políticas asociadas:** `P-ADAPT-08`, `P-DATA-07`, `P-DATA-08`, `P-OPS-04`  
**Mecanismos asociados:** `M-ADAPT-02`, `M-BUFFER-01`, `M-CONS-02`, `M-DELEG-02`, `M-NODE-02`, `M-REPL-01`, `M-TX-01`, `M-TX-02`  
**Consultas asociadas:** `EXT-Q33`, `EXT-Q34`

**RNF-14** La delegación temporal debe limitar la propagación de delegaciones a una profundidad máxima `D_delegation_max` o a otra condición de corte explícita definida por política, evitando cascadas no acotadas de saturación.
**Soporte ontológico:** `ex:DelegationEvent`, `ex:delegationDepth`, `ex:parentDelegation`, `ex:D_delegation_max`  
**Políticas asociadas:** `P-ADAPT-07`, `P-AUD-04`, `P-OPS-01`  
**Mecanismos asociados:** `M-DELEG-01`, `M-DELEG-03`, `M-OPS-01`, `M-TRUST-02`, `M-VAL-04`  
**Consultas asociadas:** `EXT-Q65`, `EXT-Q76`

---

### 2.5 Seguridad, privacidad y control de la información

**RNF-15** Los datos sensibles deben cifrarse en tránsito y en reposo conforme a la línea base de seguridad versionada del despliegue; la campaña de aceptación debe verificar que ningún canal o almacenamiento clasificado como sensible opera fuera de dicha línea base.
**Soporte ontológico:** `ex:EncryptionMechanism`, `ex:SecurityMechanism`, `ex:protectsInTransit`, `ex:protectsAtRest`, `ex:securityBaselineVersion`  
**Políticas asociadas:** `P-DATA-03`  
**Mecanismos asociados:** `M-SEC-01`, `M-VAL-04`  
**Consultas asociadas:** `EXT-Q29`, `EXT-Q30`, `EXT-Q32`

**RNF-16** El 100 % de las sesiones federadas para las que las políticas exijan privacidad diferencial debe incluir presupuesto de privacidad, nivel de ruido y mecanismo de privacidad consultables.
**Soporte ontológico:** `ex:FederatedLearningSession`, `ex:hasPrivacyBudget`, `ex:noiseLevel`, `ex:hasPrivacyMechanism`  
**Políticas asociadas:** `P-FL-03`, `P-FL-07`  
**Mecanismos asociados:** `M-AUD-01`, `M-FL-01`, `M-FL-02`, `M-FL-03`, `M-ID-01`  
**Consultas asociadas:** `EXT-Q68`

**RNF-17** Debe haber cero transmisiones externas de observaciones fisiológicas crudas y cero asociaciones de identificadores personales directos con datos parametrizados, gradientes o actualizaciones federadas.
**Soporte ontológico:** `ex:TransferEvent`, `ex:PhysiologicalObservation`, `ex:DirectIdentifier`, `ex:PseudonymousIdentifier`, `ex:AnonymousIdentifier`  
**Políticas asociadas:** `P-DATA-01`, `P-DATA-02`, `P-FL-03`, `P-FL-06`  
**Mecanismos asociados:** `M-CONS-02`, `M-DATA-01`, `M-FL-02`, `M-FL-03`, `M-ID-01`, `M-TX-01`, `M-ZONE-01`  
**Consultas asociadas:** `EXT-Q22`, `EXT-Q27`, `EXT-Q28`

**RNF-18** El presupuesto de privacidad diferencial debe ser explícito y auditable para el 100 % de las operaciones a las que aplique, incluyendo su vínculo con propósito, contrato y política.
**Soporte ontológico:** `ex:PrivacyBudgetAccount`, `ex:budgetForContract`, `ex:privacyBudgetMaximum`, `ex:privacyBudgetConsumed`, `ex:privacyBudgetRemaining`  
**Políticas asociadas:** `P-FL-04`  
**Mecanismos asociados:** `M-AUD-01`, `M-FL-04`  
**Consultas asociadas:** `EXT-Q69`

**RNF-19** Los mecanismos de anonimización, pseudonimización y privacidad diferencial utilizados por el sistema deben estar representados semánticamente o referenciados de forma verificable desde la sesión/flujo correspondiente, y no depender exclusivamente de documentación externa no enlazada.
**Soporte ontológico:** `ex:PrivacyMechanism`, `ex:SecurityMechanism`, `ex:hasPrivacyMechanism`, `ex:appliedSecurityMechanism`  
**Políticas asociadas:** `P-DATA-02`, `P-FL-05`  
**Mecanismos asociados:** `M-FL-03`, `M-ID-01`, `M-TX-01`  
**Consultas asociadas:** `EXT-Q26`, `EXT-Q68`

---

### 2.6 Adaptabilidad y configurabilidad

**RNF-20** Las políticas de adaptación deben poder configurarse o versionarse sin modificar la estructura conceptual central de la ontología.
**Soporte ontológico:** `ex:Policy`, `ex:policyVersion`, `ex:PolicyArtifact`  
**Políticas asociadas:** `P-GOV-04`  
**Mecanismos asociados:** `M-GOV-02`, `M-GOV-04`, `M-VAL-04`  
**Consultas asociadas:** `EXT-Q10`

**RNF-21** Cuando cambie contexto, consentimiento, contrato, zona, conectividad o confianza y la selección vigente deje de ser válida, la reevaluación debe completar una nueva decisión dentro de `T_reselection_max`.
**Soporte ontológico:** `ex:EvaluationState`, `ex:T_reselection_max`, `ex:AuthorizationDecision`, `ex:TrustAssessment`  
**Políticas asociadas:** `P-MODEL-09`, `P-OPS-01`, `P-ZONE-04`  
**Mecanismos asociados:** `M-CTX-01`, `M-MODEL-04`, `M-OPS-01`, `M-VAL-04`  
**Consultas asociadas:** `EXT-Q76`

**RNF-22** La precedencia entre restricciones debe ser determinista: ante los mismos estados, contrato, consentimiento, zona y versión de políticas, el sistema debe producir la misma decisión de elegibilidad y dejar registrada la misma regla de precedencia aplicada.
**Soporte ontológico:** `ex:PolicyCategoryRelation`, `ex:ConflictResolutionStrategy`, `ex:usesResolutionStrategy`  
**Políticas asociadas:** `P-CONS-04`, `P-GOV-03`, `P-GOV-04`, `P-ZONE-01`  
**Mecanismos asociados:** `M-CONS-02`, `M-GOV-02`, `M-GOV-03`, `M-GOV-04`, `M-VAL-04`, `M-ZONE-01`  
**Consultas asociadas:** `EXT-Q07`, `EXT-Q15`, `EXT-Q78`, `EXT-Q79`

---

### 2.7 Interoperabilidad

**RNF-23** La incorporación de un nuevo tipo de dispositivo vestible debe poder realizarse mediante las interfaces/adaptadores previstos sin modificar el núcleo conceptual de usuario, dispositivo, observación y estado.
**Soporte ontológico:** `ex:Wearable`, `ex:PhysiologicalSensor`, `ex:State`, `ex:User`  
**Políticas asociadas:** `P-INT-02`  
**Mecanismos asociados:** `M-INT-02`, `M-VAL-05`  
**Consultas asociadas:** `BASE-Q03`‡, `BASE-Q05`‡, `EXT-Q01`‡

**RNF-24** La representación y consulta semántica debe basarse en estándares abiertos compatibles con RDF/OWL/Turtle y SPARQL 1.1.
**Soporte ontológico:** `ex:OntologyArtifact`, `ex:QuerySpecification`, `rdf:RDF`, `owl:Ontology`, `SPARQL 1.1`  
**Políticas asociadas:** `P-INT-01`, `P-VAL-01`  
**Mecanismos asociados:** `M-INT-01`, `M-VAL-01`  
**Consultas asociadas:** `EXT-Q01`‡, `EXT-Q75`‡, `EXT-Q77`‡; además, la conformidad se comprueba ejecutando la batería v3 completa en el endpoint de referencia

**RNF-25** La ontología debe reutilizar vocabularios estándar cuando sean aplicables, incluyendo SOSA/SSN, SAREF, FOAF y GeoSPARQL, evitando duplicar conceptos equivalentes sin justificación documental.
**Soporte ontológico:** `ex:PhysiologicalSensor`, `sosa:Sensor`, `sosa:Observation`, `saref:Device`, `foaf:Person`, `geo:Feature`  
**Políticas asociadas:** `P-INT-01`  
**Mecanismos asociados:** `M-INT-01`, `M-VAL-01`  
**Consultas asociadas:** `BASE-Q05`

**RNF-26** La representación RDF/OWL debe poder cargarse y consultarse en razonadores y endpoints SPARQL estándar compatibles con las características utilizadas por la ontología.
**Soporte ontológico:** `ex:OntologyArtifact`, `ex:QuerySpecification`, `owl:Ontology`, `SPARQL 1.1`  
**Políticas asociadas:** `P-INT-01`, `P-VAL-01`  
**Mecanismos asociados:** `M-INT-01`, `M-VAL-01`  
**Consultas asociadas:** `EXT-Q01`‡, `EXT-Q75`‡, `EXT-Q77`‡; además, la conformidad se comprueba ejecutando la batería v3 completa en el endpoint de referencia

---

### 2.8 Observabilidad, explicabilidad y auditabilidad

**RNF-27** La instrumentación debe permitir medir, como mínimo, latencia, consumo energético, precisión/calidad del modelo, calidad de sueño/estrés, coste de migración, carga, capacidad residual y confianza del nodo durante los escenarios de evaluación.
**Soporte ontológico:** `ex:EvaluationState`, `ex:MigrationEvent`, `ex:NodeState`, `ex:TrustAssessment`, `ex:observedModelQuality`  
**Políticas asociadas:** `P-DATA-10`, `P-MODEL-08`, `P-OPS-05`  
**Mecanismos asociados:** `M-AUD-01`, `M-DATA-02`, `M-METRIC-01`, `M-TIME-01`  
**Consultas asociadas:** `BASE-Q33`, `EXT-Q54`

**RNF-28** El 100 % de las decisiones MAPE-K clasificadas como relevantes para adaptación debe quedar representado por un `EvaluationState` completo según RF-66.
**Soporte ontológico:** `ex:EvaluationState`, `ex:hasDetectedSymptom`, `ex:appliedPolicy`, `ex:hasAuthorizationDecision`, `ex:selectedModelTier`, `ex:resultedInAction`  
**Políticas asociadas:** `P-AUD-06`, `P-GOV-02`  
**Mecanismos asociados:** `M-AUD-01`, `M-GOV-02`  
**Consultas asociadas:** `EXT-Q20`, `EXT-Q47`, `EXT-Q71`

**RNF-29** El 100 % de las selecciones de tier debe incluir una justificación semántica legible, las alternativas evaluadas y sus puntuaciones, de modo que la decisión pueda explicarse sin inferir información ausente.
**Soporte ontológico:** `ex:DecisionAlternative`, `ex:hasDecisionAlternative`, `ex:hasAHPScore`, `ex:hasSelectionJustification`  
**Políticas asociadas:** `P-AUD-06`, `P-MODEL-05`  
**Mecanismos asociados:** `M-AUD-01`, `M-MODEL-01`  
**Consultas asociadas:** `EXT-Q51`, `EXT-Q52`, `EXT-Q71`

**RNF-30** Una decisión debe poder reconstruirse a posteriori utilizando la información semántica persistida y sus relaciones temporales, sin depender de logs externos no enlazados al modelo.
**Soporte ontológico:** `ex:EvaluationState`, `ex:validFrom`, `ex:resultedInAction`, `ex:hasAuthorizationDecision`, `ex:appliedPolicy`  
**Políticas asociadas:** `P-AUD-07`, `P-GOV-02`  
**Mecanismos asociados:** `M-AUD-01`, `M-AUD-03`, `M-GOV-02`, `M-TIME-01`  
**Consultas asociadas:** `EXT-Q70`

**RNF-31** La batería de auditoría debe distinguir de forma inequívoca consultas de inspección, advertencias e incumplimientos, y cada consulta debe documentar su tipo y criterio de interpretación.
**Soporte ontológico:** `ex:QuerySpecification`, `ex:InspectionQueryType`, `ex:WarningQueryType`, `ex:ViolationQueryType`  
**Políticas asociadas:** `P-VAL-02`  
**Mecanismos asociados:** `M-VAL-02`  
**Consultas asociadas:** `EXT-Q80`‡; la clasificación `inventory/report/review/warning/violation/ASK/dashboard` se documenta en el catálogo completo

**RNF-32** El trust score utilizado en una decisión debe ser consultable junto con la versión o ventana histórica que produjo ese valor, permitiendo reproducir científicamente la selección de nodos.
**Soporte ontológico:** `ex:TrustAssessment`, `ex:trustRuleVersion`, `ex:trustWindowStart`, `ex:trustWindowEnd`, `ex:hasTrustEvidence`  
**Políticas asociadas:** `P-AUD-07`, `P-NODE-03`, `P-NODE-04`  
**Mecanismos asociados:** `M-AUD-01`, `M-AUD-03`, `M-TIME-01`, `M-TRUST-01`, `M-VAL-04`  
**Consultas asociadas:** `EXT-Q40`, `EXT-Q43`

**RNF-33** Dado el mismo conjunto de alternativas, métricas, pesos AHP, umbral de consistencia y criterio externo de confianza, el resultado de la decisión multicriterio debe ser reproducible.
**Soporte ontológico:** `ex:EvaluationState`, `ex:DecisionAlternative`, `ex:hasConsistencyThreshold`, `ex:hasTrustAssessment`  
**Políticas asociadas:** `P-AUD-07`, `P-MODEL-03`, `P-MODEL-05`, `P-NODE-04`  
**Mecanismos asociados:** `M-AUD-01`, `M-AUD-03`, `M-MODEL-01`, `M-MODEL-02`, `M-TIME-01`, `M-TRUST-01`, `M-TRUST-02`  
**Consultas asociadas:** `EXT-Q49`, `EXT-Q52`

**RNF-34** Las evaluaciones AHP deben cumplir la normalización de pesos y el umbral de consistencia configurado. Si el mecanismo no utiliza comparaciones por pares, la documentación y la ontología deben denominarlo puntuación multicriterio ponderada y no AHP.
**Soporte ontológico:** `ex:AHPDecisionMethod`, `ex:WeightedMulticriteriaMethod`, `ex:hasConsistencyRatio`, `ex:hasConsistencyThreshold`  
**Políticas asociadas:** `P-MODEL-02`, `P-MODEL-04`  
**Mecanismos asociados:** `M-MODEL-02`, `M-MODEL-03`  
**Consultas asociadas:** `EXT-Q48`, `EXT-Q49`, `EXT-Q50`, `EXT-Q76`

---

### 2.9 Calidad semántica, consistencia temporal y mantenibilidad

**RNF-35** Los estados deben modelarse como entidades temporales de primera clase y poder distinguirse de observaciones instantáneas o valores estáticos.
**Soporte ontológico:** `ex:State`, `ex:TemporalEntity`, `ex:validFrom`, `ex:validTo`  
**Políticas asociadas:** `P-GOV-05`  
**Mecanismos asociados:** `M-TIME-01`  
**Consultas asociadas:** `BASE-Q09`, `EXT-Q73`

**RNF-36** El 100 % de los estados nuevos debe registrar `validFrom`; cuando un estado finalice, debe registrar `validTo`, sin reutilizar `validTo` para una expiración planificada distinta del cierre efectivo.
**Soporte ontológico:** `ex:State`, `ex:validFrom`, `ex:validTo`, `ex:plannedExpiry`  
**Políticas asociadas:** `P-AUD-02`, `P-AUD-03`, `P-CONS-02`, `P-GOV-05`  
**Mecanismos asociados:** `M-CONS-01`, `M-DELEG-01`, `M-DELEG-02`, `M-TIME-01`  
**Consultas asociadas:** `EXT-Q73`, `EXT-Q74`

**RNF-37** Cuando un estado derive de una observación, debe existir un enlace `derivedFrom` o equivalente explícito que permita localizar la evidencia de origen.
**Soporte ontológico:** `ex:State`, `ex:derivedFrom`, `ex:TemporalEntity`  
**Políticas asociadas:** `P-GOV-05`  
**Mecanismos asociados:** `M-TIME-01`  
**Consultas asociadas:** `EXT-Q73`‡, `EXT-Q74`‡; cobertura temporal indirecta: no existe todavía una consulta dedicada exclusivamente a `derivedFrom`

**RNF-38** Las ampliaciones de ontología, políticas o consultas no deben romper los escenarios base ni las consultas declaradas como línea base; cualquier ruptura intencionada debe implicar una nueva versión mayor y una actualización explícita de la matriz de trazabilidad.
**Soporte ontológico:** `ex:OntologyArtifact`, `ex:PolicyArtifact`, `ex:QueryCatalog`, `ex:ScenarioArtifact`, `ex:artifactVersion`  
**Políticas asociadas:** `P-FL-08`, `P-GOV-04`, `P-INT-02`, `P-VAL-05`  
**Mecanismos asociados:** `M-GOV-02`, `M-GOV-04`, `M-INT-02`, `M-MODEL-05`, `M-VAL-04`, `M-VAL-05`  
**Consultas asociadas:** `EXT-Q01`‡, `EXT-Q02`‡, `EXT-Q05`‡, `EXT-Q77`‡, `EXT-Q80`‡

**RNF-39** Los identificadores de versiones de ontología, políticas, consultas y escenarios utilizados en una campaña de validación deben quedar registrados de forma inequívoca para evitar referencias ambiguas como “v2.1” sin artefacto asociado.
**Soporte ontológico:** `ex:OntologyArtifact`, `ex:PolicyArtifact`, `ex:RequirementsArtifact`, `ex:ScenarioArtifact`, `ex:ValidationCampaign`, `ex:artifactVersion`  
**Políticas asociadas:** `P-DATA-03`, `P-FL-08`, `P-GOV-04`, `P-OPS-01`, `P-VAL-04`, `P-VAL-08`  
**Mecanismos asociados:** `M-GOV-02`, `M-GOV-04`, `M-MODEL-05`, `M-OPS-01`, `M-SEC-01`, `M-VAL-04`, `M-VAL-07`  
**Consultas asociadas:** `EXT-Q01`, `EXT-Q08`, `EXT-Q77`

---

## 3. Requisitos de Validación y Reproducibilidad (RV)

Estos requisitos se separan de los RNF porque describen el proceso de verificación y aceptación de la arquitectura, no una propiedad de calidad de ejecución.

**RV-01** La arquitectura debe validarse mediante una batería de consultas SPARQL documentada, versionada y reproducible.
**Soporte ontológico:** `ex:QuerySpecification`, `ex:QueryCatalog`, `ex:ValidationCampaign`, `ex:OntologyArtifact`  
**Políticas asociadas:** `P-VAL-02`, `P-VAL-04`  
**Mecanismos asociados:** `M-GOV-04`, `M-VAL-02`, `M-VAL-04`  
**Consultas asociadas:** `EXT-Q01`, `EXT-Q75`, `EXT-Q80`

**RV-02** En las consultas de incumplimiento, cero filas equivale a cumplimiento únicamente si se han superado previamente las comprobaciones de carga del dataset, versión de ontología, cobertura mínima y ejecución correcta definidas en RF-71.
**Soporte ontológico:** `ex:ViolationQueryType`, `ex:ValidationCampaign`, `ex:AcceptanceProfile`, `ex:OntologyArtifact`  
**Políticas asociadas:** `P-VAL-03`  
**Mecanismos asociados:** `M-VAL-03`  
**Consultas asociadas:** `EXT-Q77`

**RV-03** Los escenarios experimentales deben poder reproducirse en Apache Jena Fuseki como entorno de referencia, cargando la misma versión de TTL/dataset, políticas, escenarios y consultas. Otros endpoints podrán utilizarse adicionalmente si producen resultados equivalentes para la batería de referencia.
**Soporte ontológico:** `ex:ValidationCampaign`, `ex:OntologyArtifact`, `ex:PolicyArtifact`, `ex:ScenarioArtifact`, `ex:QueryCatalog`, `Apache Jena Fuseki`, `SPARQL 1.1`  
**Políticas asociadas:** `P-VAL-01`, `P-VAL-04`, `P-VAL-07`  
**Mecanismos asociados:** `M-GOV-04`, `M-VAL-01`, `M-VAL-04`, `M-VAL-06`  
**Consultas asociadas:** `EXT-Q01`, `EXT-Q05`, `EXT-Q77`

**RV-04** La documentación debe incluir una matriz de trazabilidad individual entre cada requisito, los elementos ontológicos o estándares que lo soportan, las políticas asociadas cuando existan, el mecanismo o bloque responsable, las consultas/validaciones y el criterio de aceptación.
**Soporte ontológico:** `ex:Requirement`, `ex:tracedToPolicy`, `ex:tracedToMechanism`, `ex:Policy`, `ex:MechanismSpecification`, `ex:QuerySpecification`  
**Políticas asociadas:** `P-GOV-04`, `P-VAL-06`  
**Mecanismos asociados:** `M-GOV-02`, `M-GOV-04`, `M-VAL-04`, `M-VAL-05`  
**Consultas asociadas:** `EXT-Q02`, `EXT-Q04`, `EXT-Q07`, `EXT-Q08`, `EXT-Q09`

**RV-05** La validación debe cubrir al menos consentimiento, contratos, políticas y zonas, confianza, decisión AHP, privacidad diferencial, pseudonimización/anonimización, delegación temporal y auditoría semántica.
**Soporte ontológico:** `ex:ConsentRecord`, `ex:SemanticContract`, `ex:Policy`, `ex:RestrictedZone`, `ex:TrustAssessment`, `ex:EvaluationState`, `ex:PrivacyBudgetAccount`, `ex:DelegationEvent`  
**Políticas asociadas:** `P-VAL-06`, `P-VAL-08`  
**Mecanismos asociados:** `M-VAL-04`, `M-VAL-05`, `M-VAL-07`  
**Consultas asociadas:** `EXT-Q80`

---

---
## 4. Matriz de trazabilidad individual v3.0.0

La matriz siguiente implementa RV-04 a nivel de requisito individual. Las asociaciones se han obtenido de la trazabilidad explícita de la ontología v3, de `POLICIES-REV-01` y de los metadatos `Requirements:`/`Policies:` de la batería SPARQL v3. Las marcas `†` y `‡` se explican al inicio del documento.

### 4.1 Requisitos funcionales

| Requisito | Elementos ontológicos / estándares | Políticas | Mecanismos | Consultas | Cobertura | Criterio de aceptación |
|---|---|---|---|---|---|---|
| **RF-01** | `ex:Wearable`, `ex:SmartWatch`, `ex:SmartRing`, `ex:SmartBand`, `ex:hasWearable` | `P-INT-02` | `M-INT-02`, `M-VAL-05` | `BASE-Q01`, `BASE-Q03` | Mixta: política/mecanismo derivado | Cobertura/resultado esperado verificable en `BASE-Q01`, `BASE-Q03` conforme al artefacto y escenario versionados. |
| **RF-02** | `ex:locatedInZone`, `ex:connectsTo`, `ex:ComputationalNode`, `ex:MistNode`, `ex:EdgeNode`, `ex:FogNode`, `ex:CloudNode` | `P-OPS-02`, `P-OPS-03` | `M-NODE-01`, `M-OPS-02`, `M-OPS-03` | `BASE-Q02`, `BASE-Q20`, `BASE-Q23` | Mixta: política/mecanismo derivado | Cobertura/resultado esperado verificable en `BASE-Q02`, `BASE-Q20`, `BASE-Q23` conforme al artefacto y escenario versionados. |
| **RF-03** | `ex:UserState`, `ex:hasMobility`, `ex:NodeUserRelation`, `ex:hasDistance`, `ex:locatedInZone` | `P-ZONE-04` | `M-CTX-01`, `M-MODEL-04` | `BASE-Q09`, `BASE-Q23` | Directa | Cobertura/resultado esperado verificable en `BASE-Q09`, `BASE-Q23` conforme al artefacto y escenario versionados. |
| **RF-04** | `ex:DeviceState`, `ex:hasBatteryLevel`, `ex:hasConnectionStatus`, `ex:parametrizedDataReady` | `P-DATA-04` | `M-DATA-02`, `M-TX-01` | `BASE-Q10` | Directa | Cobertura/resultado esperado verificable en `BASE-Q10` conforme al artefacto y escenario versionados. |
| **RF-05** | `ex:NodeState`, `ex:hasAvailability`, `ex:hasWorkload`, `ex:hasCommunication`, `ex:hasResidualCapacity`, `ex:resourceUsagePercent`, `ex:queuedRequests`, `ex:hasOperationalStatus`, `ex:ComputeOnly`, `ex:Inoperative` | `P-NODE-01` | `M-NODE-01`, `M-NODE-02` | `BASE-Q02`, `BASE-Q07`, `BASE-Q26`, `EXT-Q41` | Directa | 0 filas en `EXT-Q41`, tras las precondiciones de RF-71/RV-02. |
| **RF-06** | `ex:PhysiologicalSensor`, `ex:HeartRateSensor`, `ex:EDASensor`, `ex:SleepSensor`, `ex:AccelerometerSensor`, `ex:SpO2Sensor`, `ex:TemperatureSensor`, `ex:PhysiologicalObservation`, `ex:SleepObservation`, `sosa:Sensor`, `sosa:Observation`, `saref:Device` | `P-INT-01` | `M-INT-01`, `M-VAL-01` | `BASE-Q05` | Mixta: política/mecanismo derivado | Cobertura/resultado esperado verificable en `BASE-Q05` conforme al artefacto y escenario versionados. |
| **RF-07** | `ex:DeviceState`, `ex:hasBatteryLevel`, `ex:BufferRecord`, `ex:AuthorizationDecision`, `ex:hasEffectiveConsentRange`, `ex:MistNode` | `P-ADAPT-02`, `P-DATA-06` | `M-ADAPT-02`, `M-BUFFER-01`, `M-DEVICE-01` | `BASE-Q10`, `BASE-Q17`, `EXT-Q31`, `EXT-Q62` | Mixta: consulta indirecta | Cobertura/resultado esperado verificable en `BASE-Q10`, `BASE-Q17`, `EXT-Q31` conforme al artefacto y escenario versionados. |
| **RF-08** | `ex:BufferRecord`, `ex:TransferEvent`, `ex:AuthorizationDecision`, `ex:hasEffectiveConsentRange`, `ex:contextZone` | `P-DATA-05`, `P-OPS-06`, `P-ZONE-02` | `M-BUFFER-01`, `M-CONS-02`, `M-MODEL-04`, `M-TX-02`, `M-ZONE-01` | `BASE-Q17`, `EXT-Q31`, `EXT-Q38` | Directa | Revisión explícita de `EXT-Q38`; cualquier pendiente debe quedar justificado o resuelto antes de aceptación. |
| **RF-09** | `ex:locatedInZone`, `ex:hasCommunication`, `ex:DeviceState`, `ex:NodeState`, `ex:ProcessingPurpose`, `ex:DataContext`, `ex:hasDataContext`, `ex:contextDeviceState`, `ex:contextNodeState`, `ex:contextProcessingLevel`, `ex:contextPurpose`, `ex:contextZone` | `P-DATA-04`, `P-DATA-10` | `M-DATA-02`, `M-TIME-01`, `M-TX-01` | `EXT-Q23`, `EXT-Q24`, `EXT-Q25` | Directa | 0 filas en `EXT-Q25`, tras las precondiciones de RF-71/RV-02. |
| **RF-10** | `ex:PhysiologicalObservation`, `ex:SleepObservation`, `ex:ParametrizedData`, `ex:TransferEvent`, `ex:EdgeNode`, `ex:FogNode`, `ex:CloudNode` | `P-DATA-01` | `M-DATA-01`, `M-TX-01` | `EXT-Q22` | Directa | 0 filas en `EXT-Q22`, tras las precondiciones de RF-71/RV-02. |
| **RF-11** | `ex:AIModel`, `ex:LocalModelTier`, `ex:EdgeModelTier`, `ex:StressObservation` | `P-MODEL-01` | `M-MODEL-01`, `M-NODE-02` | `BASE-Q04` | Mixta: política/mecanismo derivado | Cobertura/resultado esperado verificable en `BASE-Q04` conforme al artefacto y escenario versionados. |
| **RF-12** | `ex:AIModel`, `ex:CloudNode`, `ex:CloudModelTier`, `ex:hasModelTier`, `ex:modelVersion`, `ex:lastUpdated` | `P-MODEL-01`, `P-FL-08` | `M-MODEL-01`, `M-MODEL-05`, `M-NODE-02`, `M-VAL-04` | `BASE-Q04` | Mixta: política/mecanismo derivado | Cobertura/resultado esperado verificable en `BASE-Q04` conforme al artefacto y escenario versionados. |
| **RF-13** | `ex:AIModel`, `ex:hasModelTier`, `ex:modelVersion`, `ex:lastUpdated`, `ex:hasDegradationCause` | `P-MODEL-01`, `P-FL-08` | `M-MODEL-01`, `M-MODEL-05`, `M-NODE-02`, `M-VAL-04` | `BASE-Q04`, `BASE-Q32` | Mixta: política/mecanismo derivado | Cobertura/resultado esperado verificable en `BASE-Q04`, `BASE-Q32` conforme al artefacto y escenario versionados. |
| **RF-14** | `ex:predictionConfidence`, `ex:estimatedPredictionError`, `ex:userFeedbackScore`, `ex:observedModelQuality` | `P-MODEL-08` | `M-AUD-01`, `M-METRIC-01` | `BASE-Q21`, `EXT-Q54`, `EXT-Q55` | Directa | Revisión explícita de `EXT-Q55`; cualquier pendiente debe quedar justificado o resuelto antes de aceptación. |
| **RF-15** | `ex:EvaluationState`, `ex:DecisionAlternative`, `ex:hasDecisionAlternative`, `ex:selectedAlternative`, `ex:selectedModelTier`, `ex:hasLatencyWeight`, `ex:hasPrivacyWeight`, `ex:hasModelQualityWeight`, `ex:hasTrustAssessment`, `ex:LocalModelTier`, `ex:EdgeModelTier`, `ex:FogModelTier` | `P-MODEL-01`, `P-MODEL-09`, `P-NODE-02`, `P-OPS-06`, `P-ZONE-03`, `P-ZONE-04` | `M-BUFFER-01`, `M-CONS-02`, `M-CTX-01`, `M-MODEL-01`, `M-MODEL-04`, `M-NODE-02`, `M-TX-02`, `M-ZONE-01` | `BASE-Q21`, `EXT-Q46` | Directa | Cobertura/resultado esperado verificable en `BASE-Q21`, `EXT-Q46` conforme al artefacto y escenario versionados. |
| **RF-16** | `ex:Service`, `ex:ServiceState`, `ex:EvaluationState`, `ex:evaluatesService`, `ex:evaluatesNode` | `P-ADAPT-01`, `P-ADAPT-04`, `P-ADAPT-05` | `M-ADAPT-01`, `M-ADAPT-03`, `M-AUD-01`, `M-FL-01`, `M-NODE-02` | `BASE-Q13`, `EXT-Q59`, `EXT-Q60`, `EXT-Q61` | Directa | 0 filas en `EXT-Q61`, tras las precondiciones de RF-71/RV-02. |
| **RF-17** | `ex:DeviceState`, `ex:NodeState`, `ex:hasBatteryLevel`, `ex:hasCommunication`, `ex:hasWorkload`, `ex:hasTrustScore`, `ex:MAPESymptom`, `ex:ComputeOnly`, `ex:Inoperative`, `ex:MigrationEvent`, `ex:AdaptationAction` | `P-ADAPT-01`, `P-ADAPT-02`, `P-ADAPT-03`, `P-ADAPT-04`, `P-MODEL-09`, `P-NODE-01`, `P-OPS-02`, `P-ZONE-04` | `M-ADAPT-01`, `M-ADAPT-02`, `M-AUD-01`, `M-BUFFER-01`, `M-CTX-01`, `M-MODEL-04`, `M-NODE-01`, `M-NODE-02`, `M-OPS-02` | `BASE-Q08`, `BASE-Q12`, `BASE-Q13`, `BASE-Q14`, `EXT-Q59`, `EXT-Q60` | Directa | Cobertura/resultado esperado verificable en `BASE-Q08`, `BASE-Q12`, `BASE-Q13` conforme al artefacto y escenario versionados. |
| **RF-18** | `ex:hasNeighborNode`, `ex:delegatesTo`, `ex:DelegationEvent`, `ex:ConsentRange`, `ex:Policy` | `P-ADAPT-01`, `P-NODE-02` | `M-ADAPT-01`, `M-CONS-02`, `M-NODE-02`, `M-ZONE-01` | `BASE-Q19`, `BASE-Q23`, `EXT-Q45` | Directa | 0 filas en `EXT-Q45`, tras las precondiciones de RF-71/RV-02. |
| **RF-19** | `ex:ParametrizedData`, `ex:isRedundant`, `ex:FederatedLearningSession`, `ex:updatesModel`, `ex:ReplicationEvent`, `ex:SynchronizationEvent`, `ex:replicaOf`, `ex:replicationVersion`, `ex:idempotencyKey` | `P-ADAPT-08`, `P-DATA-08` | `M-DELEG-02`, `M-REPL-01`, `M-TX-01`, `M-TX-02` | `EXT-Q33`, `EXT-Q34` | Directa | 0 filas en `EXT-Q34`, tras las precondiciones de RF-71/RV-02. |
| **RF-20** | `ex:hasDegradationCause`, `ex:ModelDegradationCause`, `ex:CommunicationLoss`, `ex:LowBattery`, `ex:NoNearbyNodes`, `ex:InfrastructureOverload` | `P-ADAPT-03`, `P-ADAPT-06` | `M-ADAPT-01`, `M-ADAPT-02`, `M-AUD-01`, `M-OPS-02` | `BASE-Q14`, `BASE-Q22`, `BASE-Q27`, `BASE-Q35`, `EXT-Q59`, `EXT-Q62` | Directa | Cobertura/resultado esperado verificable en `BASE-Q14`, `BASE-Q22`, `BASE-Q27` conforme al artefacto y escenario versionados. |
| **RF-21** | `ex:FederatedLearningSession`, `ex:hasPayloadType`, `ex:ModelGradientUpdate`, `ex:ConsentRange`, `ex:Policy`, `ex:ModelGradientsPayload`, `ex:AuthorizationDecision` | `P-FL-01`, `P-FL-02` | `M-CONS-02`, `M-FL-01`, `M-NODE-02`, `M-ZONE-01` | `BASE-Q16`, `BASE-Q24`, `BASE-Q25`, `EXT-Q66`, `EXT-Q67` | Directa | 0 filas en `EXT-Q67`, tras las precondiciones de RF-71/RV-02. |
| **RF-22** | `ex:FederatedLearningSession`, `ex:involvedNode`, `ex:updatesModel`, `ex:EdgeNode`, `ex:FogNode`, `ex:CloudNode` | `P-ADAPT-05`, `P-FL-01` | `M-ADAPT-03`, `M-FL-01`, `M-NODE-02` | `BASE-Q16`, `BASE-Q24`, `BASE-Q30`, `EXT-Q61`, `EXT-Q66` | Directa | 0 filas en `EXT-Q61`, tras las precondiciones de RF-71/RV-02. |
| **RF-23** | `ex:FederatedLearningSession`, `ex:hasPayloadType`, `ex:ImprovedModelParametersPayload`, `ex:updatesModel` | `P-CONS-06`, `P-FL-06` | `M-CONS-02`, `M-FL-02`, `M-ZONE-01` | `EXT-Q66` | Directa | Cobertura/resultado esperado verificable en `EXT-Q66` conforme al artefacto y escenario versionados. |
| **RF-24** | `ex:modelVersion`, `ex:lastUpdated`, `ex:AIModel`, `ex:hasDegradationCause`, `ex:RollbackEvent`, `ex:rollbackTarget`, `ex:supersedesModel`, `ex:modelLineageStatus` | `P-FL-08` | `M-MODEL-05`, `M-VAL-04` | `BASE-Q04`, `BASE-Q22`, `EXT-Q57`, `EXT-Q58` | Directa | Revisión explícita de `EXT-Q58`; cualquier pendiente debe quedar justificado o resuelto antes de aceptación. |
| **RF-25** | `ex:FederatedLearningSession`, `ex:sessionTime`, `ex:involvedNode`, `ex:updatesModel`, `ex:hasPayloadType`, `ex:hasPrivacyBudget`, `ex:noiseLevel`, `ex:hasPrivacyMechanism` | `P-ADAPT-05`, `P-FL-01`, `P-FL-07` | `M-ADAPT-03`, `M-AUD-01`, `M-FL-01`, `M-FL-02`, `M-NODE-02` | `BASE-Q16`, `BASE-Q24`, `EXT-Q66` | Directa | Cobertura/resultado esperado verificable en `BASE-Q16`, `BASE-Q24`, `EXT-Q66` conforme al artefacto y escenario versionados. |
| **RF-26** | `ex:CommunicationLevel`, `ex:DeviceConnectionStatus`, `ex:StableComm`, `ex:IntermittentComm`, `ex:NoConnectionComm`, `ex:Connected`, `ex:Disconnected`, `ex:AirplaneMode`, `ex:SynchronizationEvent` | `P-ADAPT-08`, `P-DATA-05`, `P-DATA-07`, `P-OPS-06`, `P-ZONE-02` | `M-BUFFER-01`, `M-CONS-02`, `M-DELEG-02`, `M-MODEL-04`, `M-NODE-02`, `M-REPL-01`, `M-TX-02`, `M-ZONE-01` | `BASE-Q10` | Directa | Cobertura/resultado esperado verificable en `BASE-Q10` conforme al artefacto y escenario versionados. |
| **RF-27** | `ex:hasBatteryLevel`, `ex:hasCommunication`, `ex:isRedundant`, `ex:ConsentRange`, `ex:CityArea`, `ex:DataCriticality`, `ex:hasDataCriticality` | `P-DATA-04`, `P-DATA-06`, `P-DATA-07`, `P-DATA-09` | `M-ADAPT-02`, `M-BUFFER-01`, `M-CONS-02`, `M-DATA-02`, `M-DEVICE-01`, `M-NODE-02`, `M-TX-01`, `M-TX-02`, `M-TX-03` | `BASE-Q10`, `BASE-Q17`, `EXT-Q23`, `EXT-Q38` | Directa | Revisión explícita de `EXT-Q38`; cualquier pendiente debe quedar justificado o resuelto antes de aceptación. |
| **RF-28** | `ex:ParametrizedData`, `ex:isRedundant`, `ex:DataCriticality`, `ex:CriticalData`, `ex:hasDataCriticality` | `P-DATA-08`, `P-DATA-09` | `M-BUFFER-01`, `M-REPL-01`, `M-TX-01`, `M-TX-03` | `EXT-Q35` | Directa | Cobertura/resultado esperado verificable en `EXT-Q35` conforme al artefacto y escenario versionados. |
| **RF-29** | `ex:resourceUsagePercent`, `ex:queuedRequests`, `ex:hasWorkload`, `ex:hasResidualCapacity`, `ex:hasMigrationTime`, `ex:hasMigrationCost` | `P-OPS-05` | `M-METRIC-01`, `M-TIME-01` | `BASE-Q07`, `BASE-Q26`, `BASE-Q33`, `EXT-Q54` | Directa | Las métricas de carga/capacidad/cola y coste/tiempo de migración deben ser consultables. La v3 no define todavía una propiedad genérica específica para latencia observada, por lo que esa parte requiere completar el modelo si se desea persistencia semántica del valor. |
| **RF-30** | `ex:UserState`, `ex:NodeState`, `ex:DeviceState`, `ex:StressObservation`, `ex:DataContext`, `ex:contextDeviceState`, `ex:contextNodeState`, `ex:validFrom` | `P-DATA-10`, `P-OPS-05` | `M-DATA-02`, `M-METRIC-01`, `M-TIME-01` | `BASE-Q09`, `EXT-Q24` | Directa | Cobertura/resultado esperado verificable en `BASE-Q09`, `EXT-Q24` conforme al artefacto y escenario versionados. |
| **RF-31** | `ex:UrbanZone`, `ex:RuralZone`, `ex:RestrictedZone`, `ex:DelegationEvent`, `ex:EvaluationState`, `ex:Scenario`, `ex:ScenarioArtifact`, `ex:scenarioIdentifier`, `ex:partOfScenario` | `P-VAL-07` | `M-VAL-04`, `M-VAL-06` | `BASE-Q11`, `BASE-Q12`, `BASE-Q13`, `BASE-Q17`, `EXT-Q05` | Directa | Cobertura/resultado esperado verificable en `BASE-Q11`, `BASE-Q12`, `BASE-Q13` conforme al artefacto y escenario versionados. |
| **RF-32** | `ex:ConsentRecord`, `ex:ConsentRange`, `ex:RangeDenied`, `ex:RangeLocalOnly`, `ex:RangeCommunityAgg`, `ex:RangeGlobalAgg` | `P-CONS-01` | `M-CONS-01` | `BASE-Q01`, `BASE-Q15`, `BASE-Q25`, `BASE-Q31`, `EXT-Q11`, `EXT-Q13` | Directa | 0 filas en `EXT-Q13`, tras las precondiciones de RF-71/RV-02. |
| **RF-33** | `ex:SemanticContract`, `ex:contractSubject`, `ex:validFrom`, `ex:validTo` | `P-CONS-02` | `M-CONS-01`, `M-TIME-01` | `BASE-Q20`, `EXT-Q12`, `EXT-Q14`, `EXT-Q15` | Directa | 0 filas en `EXT-Q14`, `EXT-Q15`, tras las precondiciones de RF-71/RV-02. |
| **RF-34** | `ex:contractSubject`, `ex:hasConsentRange`, `ex:hasProcessingPurpose`, `ex:governedBy` | `P-CONS-03` | `M-CONS-01`, `M-GOV-02` | `BASE-Q20`, `EXT-Q12`, `EXT-Q14` | Directa | 0 filas en `EXT-Q14`, tras las precondiciones de RF-71/RV-02. |
| **RF-35** | `ex:hasActiveConsentRange`, `ex:hasConsentRange`, `ex:SemanticContract`, `ex:ConsentRecord`, `ex:AuthorizationDecision`, `ex:hasEffectiveConsentRange` | `P-CONS-04`, `P-FL-02`, `P-GOV-03`, `P-MODEL-06` | `M-CONS-02`, `M-FL-01`, `M-GOV-03`, `M-MODEL-01`, `M-ZONE-01` | `EXT-Q11`, `EXT-Q13`, `EXT-Q16`, `EXT-Q17`, `EXT-Q18`, `EXT-Q19` | Directa | 0 filas en `EXT-Q13`, `EXT-Q16`, `EXT-Q18`, `EXT-Q19`, tras las precondiciones de RF-71/RV-02. |
| **RF-36** | `ex:selectedModelTier`, `ex:hasActiveConsentRange`, `ex:requiresConsentRange`, `ex:ConsentRange`, `ex:AuthorizationDecision`, `ex:hasEffectiveConsentRange` | `P-CONS-04`, `P-ZONE-03` | `M-CONS-02`, `M-GOV-03`, `M-NODE-02`, `M-ZONE-01` | `BASE-Q15`, `BASE-Q25`, `BASE-Q28`, `EXT-Q17`, `EXT-Q18`, `EXT-Q19`, `EXT-Q20` | Directa | 0 filas en `EXT-Q18`, `EXT-Q19`, `EXT-Q20`, tras las precondiciones de RF-71/RV-02. |
| **RF-37** | `ex:requiresConsentRange`, `ex:ConsentRange`, `ex:Policy`, `ex:Permission`, `ex:AIModel`, `ex:Service`, `ex:FederatedLearningSession` | `P-CONS-05` | `M-CONS-03` | `BASE-Q06`, `EXT-Q21` | Directa | Cobertura/resultado esperado verificable en `BASE-Q06`, `EXT-Q21` conforme al artefacto y escenario versionados. |
| **RF-38** | `ex:ConsentRecord`, `ex:RangeDenied`, `ex:RangeLocalOnly`, `ex:ImprovedModelParametersPayload`, `ex:hasPayloadType`, `ex:AIModel` | `P-CONS-06`, `P-FL-06` | `M-CONS-02`, `M-FL-02`, `M-ZONE-01` | `BASE-Q15` | Directa | Cobertura/resultado esperado verificable en `BASE-Q15` conforme al artefacto y escenario versionados. |
| **RF-39** | `ex:Policy`, `ex:PolicyCategory`, `ex:hasPolicyType`, `ex:belongsToPolicyCategory` | `P-GOV-01` | `M-GOV-01` | `EXT-Q03`, `EXT-Q06`, `EXT-Q10` | Directa | 0 filas en `EXT-Q10`, tras las precondiciones de RF-71/RV-02. |
| **RF-40** | `ex:PolicyType`, `ex:ObligationPolicyType`, `ex:AbstentionPolicyType`, `ex:ProhibitionPolicyType` | `P-GOV-01` | `M-GOV-01` | `EXT-Q03`, `EXT-Q06`, `EXT-Q10` | Directa | 0 filas en `EXT-Q10`, tras las precondiciones de RF-71/RV-02. |
| **RF-41** | `ex:governedBy`, `ex:Policy`, `ex:SemanticContract`, `ex:EvaluationState` | `P-CONS-03`, `P-GOV-02` | `M-AUD-01`, `M-CONS-01`, `M-GOV-02` | `EXT-Q03`, `EXT-Q08`, `EXT-Q12`, `EXT-Q70` | Mixta: consulta indirecta | Cobertura/resultado esperado verificable en `EXT-Q03`, `EXT-Q08`, `EXT-Q12` conforme al artefacto y escenario versionados. |
| **RF-42** | `ex:RuralZone`, `ex:RestrictedZone`, `ex:UrbanZone`, `ex:Policy` | `P-FL-02`, `P-GOV-03`, `P-MODEL-06`, `P-ZONE-01`, `P-ZONE-02`, `P-ZONE-03` | `M-BUFFER-01`, `M-CONS-02`, `M-FL-01`, `M-GOV-03`, `M-MODEL-01`, `M-NODE-02`, `M-TX-02`, `M-ZONE-01` | `BASE-Q18`, `BASE-Q34`, `EXT-Q36`, `EXT-Q37`, `EXT-Q39` | Directa | 0 filas en `EXT-Q37`, tras las precondiciones de RF-71/RV-02. |
| **RF-43** | `ex:RestrictedZone`, `ex:LocalModelTier`, `ex:EdgeModelTier`, `ex:FogModelTier`, `ex:CloudModelTier` | `P-GOV-03`, `P-ZONE-01` | `M-CONS-02`, `M-GOV-03`, `M-ZONE-01` | `BASE-Q18`, `BASE-Q34`, `EXT-Q36`, `EXT-Q37` | Directa | 0 filas en `EXT-Q37`, tras las precondiciones de RF-71/RV-02. |
| **RF-44** | `ex:EvaluationState`, `ex:appliedPolicy`, `ex:governedBy`, `ex:AdaptationAction` | `P-ADAPT-06`, `P-GOV-02` | `M-ADAPT-02`, `M-AUD-01`, `M-GOV-02` | `EXT-Q59`, `EXT-Q63`, `EXT-Q70`, `EXT-Q72` | Mixta: consulta indirecta | 0 filas en `EXT-Q72`, tras las precondiciones de RF-71/RV-02. |
| **RF-45** | `ex:hasTrustScore`, `ex:TrustAssessment`, `ex:trustAssessmentForState`, `ex:NodeState` | `P-NODE-03` | `M-TRUST-01`, `M-VAL-04` | `BASE-Q07`, `EXT-Q40` | Directa | Cobertura/resultado esperado verificable en `BASE-Q07`, `EXT-Q40` conforme al artefacto y escenario versionados. |
| **RF-46** | `ex:TrustAssessment`, `ex:hasTrustWeight`, `ex:hasTrustScore`, `ex:EvaluationState`, `ex:evaluatesNode` | `P-MODEL-03`, `P-NODE-05` | `M-MODEL-02`, `M-NODE-02`, `M-TRUST-02` | `EXT-Q44` | Directa | Cobertura/resultado esperado verificable en `EXT-Q44` conforme al artefacto y escenario versionados. |
| **RF-47** | `ex:TrustAssessment`, `ex:hasTrustScore`, `ex:NodeState`, `ex:hasAvailability`, `ex:hasCommunication`, `ex:hasWorkload`, `ex:hasResidualCapacity` | `P-NODE-02`, `P-NODE-05`, `P-NODE-06` | `M-ADAPT-02`, `M-AUD-01`, `M-CONS-02`, `M-NODE-02`, `M-TRUST-02`, `M-ZONE-01` | `BASE-Q08`, `BASE-Q19`, `EXT-Q41`, `EXT-Q42` | Directa | 0 filas en `EXT-Q41`, tras las precondiciones de RF-71/RV-02. |
| **RF-48** | `ex:DelegationEvent`, `ex:delegatedBy`, `ex:delegatesTo`, `ex:TrustAssessment`, `ex:hasTrustScore` | `P-ADAPT-07`, `P-NODE-05`, `P-NODE-06` | `M-ADAPT-02`, `M-AUD-01`, `M-DELEG-01`, `M-NODE-02`, `M-TRUST-02` | `BASE-Q19`, `EXT-Q42`, `EXT-Q45` | Directa | 0 filas en `EXT-Q45`, tras las precondiciones de RF-71/RV-02. |
| **RF-49** | `ex:TrustAssessment`, `ex:hasTrustEvidence`, `ex:trustRuleVersion`, `ex:trustWindowStart`, `ex:trustWindowEnd` | `P-NODE-03`, `P-NODE-04` | `M-AUD-01`, `M-TRUST-01`, `M-VAL-04` | `EXT-Q40`, `EXT-Q43` | Directa | Revisión explícita de `EXT-Q43`; cualquier pendiente debe quedar justificado o resuelto antes de aceptación. |
| **RF-50** | `ex:hasLatencyWeight`, `ex:hasPrivacyWeight`, `ex:hasModelQualityWeight`, `ex:EvaluationState` | `P-MODEL-02`, `P-MODEL-03` | `M-MODEL-02`, `M-TRUST-02` | `EXT-Q48` | Directa | 0 filas en `EXT-Q48`, tras las precondiciones de RF-71/RV-02. |
| **RF-51** | `ex:hasAHPScore`, `ex:selectedModelTier`, `ex:hasSelectionJustification`, `ex:DecisionAlternative`, `ex:hasDecisionAlternative`, `ex:selectedAlternative`, `ex:EvaluationState` | `P-AUD-06`, `P-MODEL-05` | `M-AUD-01`, `M-MODEL-01` | `EXT-Q46`, `EXT-Q51`, `EXT-Q52`, `EXT-Q53` | Directa | 0 filas en `EXT-Q53`, tras las precondiciones de RF-71/RV-02. |
| **RF-52** | `ex:hasPrivacyWeight`, `ex:RangeLocalOnly`, `ex:RangeCommunityAgg`, `ex:LocalModelTier`, `ex:EdgeModelTier`, `ex:AuthorizationDecision` | `P-MODEL-01`, `P-MODEL-06` | `M-CONS-02`, `M-MODEL-01`, `M-NODE-02`, `M-ZONE-01` | `BASE-Q15`, `EXT-Q46`, `EXT-Q51`, `EXT-Q56` | Mixta: consulta indirecta | 0 filas en `EXT-Q56`, tras las precondiciones de RF-71/RV-02. |
| **RF-53** | `ex:CloudModelTier`, `ex:AuthorizationDecision`, `ex:hasTrustAssessment`, `ex:hasPrivacyBudgetAccount` | `P-MODEL-01`, `P-MODEL-07`, `P-NODE-06`, `P-ZONE-01` | `M-ADAPT-02`, `M-AUD-01`, `M-CONS-02`, `M-FL-03`, `M-MODEL-01`, `M-NODE-02`, `M-ZONE-01` | `EXT-Q56` | Directa | 0 filas en `EXT-Q56`, tras las precondiciones de RF-71/RV-02. |
| **RF-54** | `ex:EvaluationState`, `ex:hasLatencyWeight`, `ex:hasPrivacyWeight`, `ex:hasModelQualityWeight`, `ex:selectedModelTier`, `ex:hasSelectionJustification`, `ex:appliedPolicy`, `ex:hasDecisionAlternative`, `ex:auditsContract`, `ex:resultedInAction` | `P-AUD-06`, `P-MODEL-05` | `M-AUD-01`, `M-MODEL-01` | `EXT-Q47`, `EXT-Q53`, `EXT-Q55`, `EXT-Q71` | Directa | 0 filas en `EXT-Q47`, `EXT-Q53`, `EXT-Q71`, tras las precondiciones de RF-71/RV-02. |
| **RF-55** | `ex:hasConsistencyRatio`, `ex:hasConsistencyThreshold`, `ex:AHPDecisionMethod`, `ex:WeightedMulticriteriaMethod` | `P-MODEL-02`, `P-MODEL-03`, `P-MODEL-04` | `M-MODEL-02`, `M-MODEL-03`, `M-TRUST-02` | `EXT-Q44`, `EXT-Q48`, `EXT-Q49`, `EXT-Q50` | Directa | 0 filas en `EXT-Q48`, `EXT-Q50`, tras las precondiciones de RF-71/RV-02. |
| **RF-56** | `ex:FederatedLearningSession`, `ex:hasPrivacyBudget`, `ex:noiseLevel`, `ex:hasPayloadType` | `P-FL-03`, `P-MODEL-07` | `M-FL-03`, `M-ID-01`, `M-MODEL-01` | `BASE-Q16`, `EXT-Q67`, `EXT-Q69` | Directa | 0 filas en `EXT-Q67`, tras las precondiciones de RF-71/RV-02. |
| **RF-57** | `ex:ModelGradientUpdate`, `ex:hasNoiseApplied`, `ex:hasAnonymizationApplied`, `ex:MobileDevice`, `ex:hasPrivacyMechanism` | `P-FL-03` | `M-FL-03`, `M-ID-01` | `EXT-Q68` | Directa | 0 filas en `EXT-Q68`, tras las precondiciones de RF-71/RV-02. |
| **RF-58** | `ex:PrivacyMechanism`, `ex:DifferentialPrivacyMechanism`, `ex:hasPrivacyMechanism`, `ex:FederatedLearningSession` | `P-FL-05` | `M-FL-03`, `M-ID-01` | `BASE-Q16`, `EXT-Q68` | Directa | 0 filas en `EXT-Q68`, tras las precondiciones de RF-71/RV-02. |
| **RF-59** | `ex:hasPrivacyBudget`, `ex:ProcessingPurpose`, `ex:SemanticContract`, `ex:Policy`, `ex:PrivacyBudgetAccount`, `ex:privacyBudgetMaximum`, `ex:privacyBudgetConsumed`, `ex:privacyBudgetRemaining`, `ex:budgetForContract` | `P-FL-04`, `P-MODEL-07` | `M-AUD-01`, `M-FL-03`, `M-FL-04`, `M-MODEL-01` | `BASE-Q24`, `EXT-Q69` | Directa | Cobertura/resultado esperado verificable en `BASE-Q24`, `EXT-Q69` conforme al artefacto y escenario versionados. |
| **RF-60** | `ex:TransferEvent`, `ex:PhysiologicalObservation`, `ex:SleepObservation`, `ex:ParametrizedData`, `ex:EdgeNode`, `ex:FogNode`, `ex:CloudNode` | `P-DATA-01` | `M-DATA-01`, `M-TX-01` | `BASE-Q18`, `BASE-Q28`, `EXT-Q22`, `EXT-Q37` | Directa | 0 filas en `EXT-Q22`, `EXT-Q37`, tras las precondiciones de RF-71/RV-02. |
| **RF-61** | `ex:Identifier`, `ex:PseudonymousIdentifier`, `ex:AnonymousIdentifier`, `ex:DirectIdentifier`, `ex:usesIdentifier`, `ex:TransferEvent` | `P-DATA-02` | `M-ID-01`, `M-TX-01` | `BASE-Q01`, `BASE-Q28`, `EXT-Q23`, `EXT-Q26`, `EXT-Q27`, `EXT-Q28` | Directa | 0 filas en `EXT-Q27`, `EXT-Q28`, tras las precondiciones de RF-71/RV-02. |
| **RF-62** | `ex:DelegationEvent`, `ex:delegatedBy`, `ex:delegatesTo`, `ex:triggeredByState`, `ex:validFrom`, `ex:hasRecoveryCondition` | `P-ADAPT-05`, `P-ADAPT-07`, `P-AUD-01` | `M-ADAPT-03`, `M-DELEG-01`, `M-FL-01`, `M-TRUST-02` | `BASE-Q14`, `EXT-Q63` | Directa | Cobertura/resultado esperado verificable en `BASE-Q14`, `EXT-Q63` conforme al artefacto y escenario versionados. |
| **RF-63** | `ex:DelegationEvent`, `ex:delegatedBy`, `ex:delegatesTo`, `ex:hasRecoveryCondition`, `ex:plannedExpiry`, `ex:validFrom`, `ex:validTo` | `P-AUD-02` | `M-DELEG-01`, `M-TIME-01` | `EXT-Q63`, `EXT-Q64` | Directa | 0 filas en `EXT-Q64`, tras las precondiciones de RF-71/RV-02. |
| **RF-64** | `ex:DelegationEvent`, `ex:hasRecoveryCondition`, `ex:plannedExpiry`, `ex:validTo` | `P-AUD-03` | `M-DELEG-02` | `EXT-Q63` | Directa | Cobertura/resultado esperado verificable en `EXT-Q63` conforme al artefacto y escenario versionados. |
| **RF-65** | `ex:MAPESymptom`, `ex:hasDetectedSymptom`, `ex:appliedPolicy`, `ex:EvaluationState` | `P-AUD-05` | `M-AUD-02` | `BASE-Q14`, `BASE-Q35`, `EXT-Q72` | Directa | 0 filas en `EXT-Q72`, tras las precondiciones de RF-71/RV-02. |
| **RF-66** | `ex:EvaluationState`, `ex:hasDetectedSymptom`, `ex:appliedPolicy`, `ex:auditsContract`, `ex:hasAuthorizationDecision`, `ex:selectedModelTier`, `ex:hasSelectionJustification`, `ex:resultedInAction` | `P-ADAPT-06`, `P-AUD-05`, `P-AUD-06` | `M-ADAPT-02`, `M-AUD-01`, `M-AUD-02` | `BASE-Q21`, `EXT-Q17`, `EXT-Q20`, `EXT-Q46`, `EXT-Q47`, `EXT-Q59`, `EXT-Q71`, `EXT-Q72` | Directa | 0 filas en `EXT-Q20`, `EXT-Q47`, `EXT-Q71`, `EXT-Q72`, tras las precondiciones de RF-71/RV-02. |
| **RF-67** | `ex:evaluationUser`, `ex:auditsContract`, `ex:hasEffectiveConsentRange`, `ex:evaluationPurpose`, `ex:evaluationZone`, `ex:hasDecisionAlternative`, `ex:hasTrustAssessment`, `ex:resultedInAction` | `P-AUD-05`, `P-AUD-07` | `M-AUD-02`, `M-AUD-03`, `M-TIME-01` | `BASE-Q35`, `EXT-Q70` | Directa | Cobertura/resultado esperado verificable en `BASE-Q35`, `EXT-Q70` conforme al artefacto y escenario versionados. |
| **RF-68** | `ex:OntologyArtifact`, `ex:PolicyArtifact`, `ex:RequirementsArtifact`, `ex:ScenarioArtifact`, `ex:QuerySpecification`, `ex:QueryType` | `P-VAL-04`, `P-VAL-08` | `M-GOV-04`, `M-VAL-04`, `M-VAL-07` | `BASE-Q31`, `BASE-Q32`, `EXT-Q01`, `EXT-Q02`, `EXT-Q80` | Directa | Cobertura/resultado esperado verificable en `BASE-Q31`, `BASE-Q32`, `EXT-Q01` conforme al artefacto y escenario versionados. |
| **RF-69** | `ex:OntologyArtifact`, `ex:QuerySpecification`, `SPARQL 1.1`, `RDF/OWL/Turtle` | `P-VAL-01` | `M-VAL-01` | `EXT-Q01`, `EXT-Q75`, `EXT-Q77` | Mixta: consulta indirecta | La TTL v3 debe cargarse en Apache Jena Fuseki y permitir ejecutar sin incompatibilidades la batería completa; `EXT-Q01`, `EXT-Q75` y `EXT-Q77` verifican artefactos, shapes y preparación reproducible. |
| **RF-70** | `ex:QuerySpecification`, `ex:InspectionQueryType`, `ex:User`, `ex:Wearable`, `ex:ComputationalNode`, `ex:AIModel`, `ex:State`, `ex:Policy`, `ex:SemanticContract`, `ex:FederatedLearningSession`, `ex:DelegationEvent` | `P-VAL-02` | `M-VAL-02` | `BASE-Q01`, `BASE-Q02`, `BASE-Q03`, `BASE-Q04`, `BASE-Q05`, `BASE-Q06`, `BASE-Q07`, `BASE-Q20`, `EXT-Q03` | Directa | Cobertura/resultado esperado verificable en `BASE-Q01`, `BASE-Q02`, `BASE-Q03` conforme al artefacto y escenario versionados. |
| **RF-71** | `ex:ViolationQueryType`, `ex:ValidationCampaign`, `ex:AcceptanceProfile`, `ex:OntologyArtifact`, `ex:ScenarioArtifact` | `P-VAL-02`, `P-VAL-03` | `M-VAL-02`, `M-VAL-03` | `EXT-Q75`, `EXT-Q77`, `EXT-Q80` | Directa | Revisión explícita de `EXT-Q77`; cualquier pendiente debe quedar justificado o resuelto antes de aceptación. |
| **RF-72** | `ex:Scenario`, `ex:ScenarioArtifact`, `ex:ValidationCampaign`, `ex:QuerySpecification` | `P-VAL-07` | `M-VAL-04`, `M-VAL-06` | `BASE-Q11`, `EXT-Q05`, `EXT-Q77` | Directa | Revisión explícita de `EXT-Q77`; cualquier pendiente debe quedar justificado o resuelto antes de aceptación. |

### 4.2 Requisitos no funcionales

| Requisito | Elementos ontológicos / estándares | Políticas | Mecanismos | Consultas | Cobertura | Criterio de aceptación |
|---|---|---|---|---|---|---|
| **RNF-01** | `ex:AcceptanceProfile`, `ex:T_inference_local` | `P-OPS-01` | `M-OPS-01`, `M-VAL-04` | `EXT-Q76` | Directa | Cumplir `T_inference_local` fijado(s) en `AcceptanceProfile`; evidencia mediante `EXT-Q76`. |
| **RNF-02** | `ex:AcceptanceProfile`, `ex:T_migration_max`, `ex:MigrationEvent`, `ex:DelegationEvent`, `ex:DataCriticality` | `P-ADAPT-04`, `P-ADAPT-08`, `P-OPS-01` | `M-ADAPT-01`, `M-AUD-01`, `M-DELEG-02`, `M-NODE-02`, `M-OPS-01`, `M-REPL-01`, `M-TX-02`, `M-VAL-04` | `EXT-Q76` | Directa | Cumplir `T_migration_max` fijado(s) en `AcceptanceProfile`; evidencia mediante `EXT-Q76`. |
| **RNF-03** | `ex:AcceptanceProfile`, `ex:AdaptationAction`, `ex:DegradationEvent`, `ex:MigrationEvent`, `ex:DelegationEvent`, `ex:BufferRecord` | `P-ADAPT-01`, `P-ADAPT-03` | `M-ADAPT-01`, `M-ADAPT-02`, `M-NODE-02`, `M-OPS-02` | `BASE-Q12`, `EXT-Q59`, `EXT-Q62`, `EXT-Q76` | Mixta: consulta indirecta | Revisión explícita de `EXT-Q76`; cualquier pendiente debe quedar justificado o resuelto antes de aceptación. |
| **RNF-04** | `ex:AcceptanceProfile`, `ex:T_sparql_monitor`, `ex:QuerySpecification` | `P-OPS-01` | `M-OPS-01`, `M-VAL-04` | `EXT-Q76` | Directa | Cumplir `T_sparql_monitor` fijado(s) en `AcceptanceProfile`; evidencia mediante `EXT-Q76`. |
| **RNF-05** | `ex:AcceptanceProfile`, `ex:T_decision_max`, `ex:EvaluationState`, `ex:TrustAssessment` | `P-MODEL-03`, `P-OPS-01` | `M-MODEL-02`, `M-OPS-01`, `M-TRUST-02`, `M-VAL-04` | `EXT-Q76` | Directa | Cumplir `T_decision_max` fijado(s) en `AcceptanceProfile`; evidencia mediante `EXT-Q76`. |
| **RNF-06** | `ex:AcceptanceProfile`, `ex:E_device_max`, `ex:DeviceState`, `ex:hasBatteryLevel` | `P-DATA-06`, `P-OPS-01` | `M-ADAPT-02`, `M-BUFFER-01`, `M-DEVICE-01`, `M-OPS-01`, `M-VAL-04` | `EXT-Q76` | Directa | Cumplir `E_device_max` fijado(s) en `AcceptanceProfile`; evidencia mediante `EXT-Q76`. |
| **RNF-07** | `ex:CloudNode`, `ex:FogNode`, `ex:hasElasticity` | `P-OPS-02` | `M-OPS-02` | `BASE-Q29` | Directa | Cobertura/resultado esperado verificable en `BASE-Q29` conforme al artefacto y escenario versionados. |
| **RNF-08** | `ex:AcceptanceProfile`, `ex:N_agents`, `ex:User` | `P-OPS-01` | `M-OPS-01`, `M-VAL-04` | `EXT-Q76` | Directa | Cumplir `N_agents` fijado(s) en `AcceptanceProfile`; evidencia mediante `EXT-Q76`. |
| **RNF-09** | `ex:AcceptanceProfile`, `ex:T_node_join`, `ex:EdgeNode`, `ex:FogNode` | `P-OPS-01`, `P-OPS-03` | `M-NODE-01`, `M-OPS-01`, `M-OPS-03`, `M-VAL-04` | `EXT-Q76` | Directa | Cumplir `T_node_join` fijado(s) en `AcceptanceProfile`; evidencia mediante `EXT-Q76`. |
| **RNF-10** | `ex:User`, `ex:ComputationalNode`, `ex:PhysiologicalSensor`, `ex:AIModel`, `ex:Policy`, `ex:SemanticContract` | `P-INT-02`, `P-OPS-03` | `M-INT-02`, `M-NODE-01`, `M-OPS-03`, `M-VAL-05` | `EXT-Q01`, `EXT-Q02`, `EXT-Q03`, `EXT-Q04`, `EXT-Q05` | Mixta: consulta indirecta | Cobertura/resultado esperado verificable en `EXT-Q01`, `EXT-Q02`, `EXT-Q03` conforme al artefacto y escenario versionados. |
| **RNF-11** | `ex:QuerySpecification`, `ex:QueryCatalog` | `P-VAL-05` | `M-VAL-04`, `M-VAL-05` | `EXT-Q01`, `EXT-Q77`, `EXT-Q80` | Mixta: consulta indirecta | Una ampliación de la batería debe superar una ejecución de regresión sin alterar el significado ni el resultado esperado de las consultas declaradas como línea base. |
| **RNF-12** | `ex:DeviceConnectionStatus`, `ex:BufferRecord`, `ex:SynchronizationEvent`, `ex:DataCriticality` | `P-ADAPT-02`, `P-DATA-05`, `P-DATA-07`, `P-FL-01`, `P-NODE-01`, `P-OPS-04`, `P-OPS-06` | `M-ADAPT-02`, `M-BUFFER-01`, `M-CONS-02`, `M-FL-01`, `M-MODEL-04`, `M-NODE-01`, `M-NODE-02`, `M-TX-02`, `M-ZONE-01` | `BASE-Q08`, `EXT-Q31`, `EXT-Q32` | Directa | 0 filas en `EXT-Q32`, tras las precondiciones de RF-71/RV-02. |
| **RNF-13** | `ex:SynchronizationEvent`, `ex:ReplicationEvent`, `ex:idempotencyKey`, `ex:DataCriticality` | `P-ADAPT-08`, `P-DATA-07`, `P-DATA-08`, `P-OPS-04` | `M-ADAPT-02`, `M-BUFFER-01`, `M-CONS-02`, `M-DELEG-02`, `M-NODE-02`, `M-REPL-01`, `M-TX-01`, `M-TX-02` | `EXT-Q33`, `EXT-Q34` | Directa | 0 filas en `EXT-Q34`, tras las precondiciones de RF-71/RV-02. |
| **RNF-14** | `ex:DelegationEvent`, `ex:delegationDepth`, `ex:parentDelegation`, `ex:D_delegation_max` | `P-ADAPT-07`, `P-AUD-04`, `P-OPS-01` | `M-DELEG-01`, `M-DELEG-03`, `M-OPS-01`, `M-TRUST-02`, `M-VAL-04` | `EXT-Q65`, `EXT-Q76` | Directa | Cumplir `D_delegation_max` fijado(s) en `AcceptanceProfile`; evidencia mediante `EXT-Q65`. |
| **RNF-15** | `ex:EncryptionMechanism`, `ex:SecurityMechanism`, `ex:protectsInTransit`, `ex:protectsAtRest`, `ex:securityBaselineVersion` | `P-DATA-03` | `M-SEC-01`, `M-VAL-04` | `EXT-Q29`, `EXT-Q30`, `EXT-Q32` | Directa | 0 filas en `EXT-Q30`, `EXT-Q32`, tras las precondiciones de RF-71/RV-02. |
| **RNF-16** | `ex:FederatedLearningSession`, `ex:hasPrivacyBudget`, `ex:noiseLevel`, `ex:hasPrivacyMechanism` | `P-FL-03`, `P-FL-07` | `M-AUD-01`, `M-FL-01`, `M-FL-02`, `M-FL-03`, `M-ID-01` | `EXT-Q68` | Directa | 0 filas en `EXT-Q68`, tras las precondiciones de RF-71/RV-02. |
| **RNF-17** | `ex:TransferEvent`, `ex:PhysiologicalObservation`, `ex:DirectIdentifier`, `ex:PseudonymousIdentifier`, `ex:AnonymousIdentifier` | `P-DATA-01`, `P-DATA-02`, `P-FL-03`, `P-FL-06` | `M-CONS-02`, `M-DATA-01`, `M-FL-02`, `M-FL-03`, `M-ID-01`, `M-TX-01`, `M-ZONE-01` | `EXT-Q22`, `EXT-Q27`, `EXT-Q28` | Directa | 0 filas en `EXT-Q22`, `EXT-Q27`, `EXT-Q28`, tras las precondiciones de RF-71/RV-02. |
| **RNF-18** | `ex:PrivacyBudgetAccount`, `ex:budgetForContract`, `ex:privacyBudgetMaximum`, `ex:privacyBudgetConsumed`, `ex:privacyBudgetRemaining` | `P-FL-04` | `M-AUD-01`, `M-FL-04` | `EXT-Q69` | Directa | Cobertura/resultado esperado verificable en `EXT-Q69` conforme al artefacto y escenario versionados. |
| **RNF-19** | `ex:PrivacyMechanism`, `ex:SecurityMechanism`, `ex:hasPrivacyMechanism`, `ex:appliedSecurityMechanism` | `P-DATA-02`, `P-FL-05` | `M-FL-03`, `M-ID-01`, `M-TX-01` | `EXT-Q26`, `EXT-Q68` | Directa | 0 filas en `EXT-Q68`, tras las precondiciones de RF-71/RV-02. |
| **RNF-20** | `ex:Policy`, `ex:policyVersion`, `ex:PolicyArtifact` | `P-GOV-04` | `M-GOV-02`, `M-GOV-04`, `M-VAL-04` | `EXT-Q10` | Directa | 0 filas en `EXT-Q10`, tras las precondiciones de RF-71/RV-02. |
| **RNF-21** | `ex:EvaluationState`, `ex:T_reselection_max`, `ex:AuthorizationDecision`, `ex:TrustAssessment` | `P-MODEL-09`, `P-OPS-01`, `P-ZONE-04` | `M-CTX-01`, `M-MODEL-04`, `M-OPS-01`, `M-VAL-04` | `EXT-Q76` | Directa | Cumplir `T_reselection_max` fijado(s) en `AcceptanceProfile`; evidencia mediante `EXT-Q76`. |
| **RNF-22** | `ex:PolicyCategoryRelation`, `ex:ConflictResolutionStrategy`, `ex:usesResolutionStrategy` | `P-CONS-04`, `P-GOV-03`, `P-GOV-04`, `P-ZONE-01` | `M-CONS-02`, `M-GOV-02`, `M-GOV-03`, `M-GOV-04`, `M-VAL-04`, `M-ZONE-01` | `EXT-Q07`, `EXT-Q15`, `EXT-Q78`, `EXT-Q79` | Directa | 0 filas en `EXT-Q15`, `EXT-Q79`, tras las precondiciones de RF-71/RV-02. |
| **RNF-23** | `ex:Wearable`, `ex:PhysiologicalSensor`, `ex:State`, `ex:User` | `P-INT-02` | `M-INT-02`, `M-VAL-05` | `BASE-Q03`, `BASE-Q05`, `EXT-Q01` | Mixta: consulta indirecta | Cobertura/resultado esperado verificable en `BASE-Q03`, `BASE-Q05`, `EXT-Q01` conforme al artefacto y escenario versionados. |
| **RNF-24** | `ex:OntologyArtifact`, `ex:QuerySpecification`, `rdf:RDF`, `owl:Ontology`, `SPARQL 1.1` | `P-INT-01`, `P-VAL-01` | `M-INT-01`, `M-VAL-01` | `EXT-Q01`, `EXT-Q75`, `EXT-Q77` | Mixta: consulta indirecta | La TTL debe parsearse/cargarse como RDF/OWL y la batería SPARQL 1.1 debe ejecutarse en el endpoint de referencia; `EXT-Q01`, `EXT-Q75` y `EXT-Q77` aportan evidencia de artefactos y campaña. |
| **RNF-25** | `ex:PhysiologicalSensor`, `sosa:Sensor`, `sosa:Observation`, `saref:Device`, `foaf:Person`, `geo:Feature` | `P-INT-01` | `M-INT-01`, `M-VAL-01` | `BASE-Q05` | Directa | Cobertura/resultado esperado verificable en `BASE-Q05` conforme al artefacto y escenario versionados. |
| **RNF-26** | `ex:OntologyArtifact`, `ex:QuerySpecification`, `owl:Ontology`, `SPARQL 1.1` | `P-INT-01`, `P-VAL-01` | `M-INT-01`, `M-VAL-01` | `EXT-Q01`, `EXT-Q75`, `EXT-Q77` | Mixta: consulta indirecta | La ontología debe cargar y ser consultable en el endpoint/razonador de referencia sin incompatibilidades con las características RDF/OWL utilizadas; comprobar además `EXT-Q01`, `EXT-Q75` y `EXT-Q77`. |
| **RNF-27** | `ex:EvaluationState`, `ex:MigrationEvent`, `ex:NodeState`, `ex:TrustAssessment`, `ex:observedModelQuality` | `P-DATA-10`, `P-MODEL-08`, `P-OPS-05` | `M-AUD-01`, `M-DATA-02`, `M-METRIC-01`, `M-TIME-01` | `BASE-Q33`, `EXT-Q54` | Directa | Las métricas exigidas deben quedar disponibles durante la campaña. La v3 modela carga, capacidad, trust, calidad y migración; la persistencia semántica de latencia/consumo energético observados requiere propiedades métricas específicas si se desea validación puramente ontológica. |
| **RNF-28** | `ex:EvaluationState`, `ex:hasDetectedSymptom`, `ex:appliedPolicy`, `ex:hasAuthorizationDecision`, `ex:selectedModelTier`, `ex:resultedInAction` | `P-AUD-06`, `P-GOV-02` | `M-AUD-01`, `M-GOV-02` | `EXT-Q20`, `EXT-Q47`, `EXT-Q71` | Directa | 0 filas en `EXT-Q20`, `EXT-Q47`, `EXT-Q71`, tras las precondiciones de RF-71/RV-02. |
| **RNF-29** | `ex:DecisionAlternative`, `ex:hasDecisionAlternative`, `ex:hasAHPScore`, `ex:hasSelectionJustification` | `P-AUD-06`, `P-MODEL-05` | `M-AUD-01`, `M-MODEL-01` | `EXT-Q51`, `EXT-Q52`, `EXT-Q71` | Directa | 0 filas en `EXT-Q71`, tras las precondiciones de RF-71/RV-02. |
| **RNF-30** | `ex:EvaluationState`, `ex:validFrom`, `ex:resultedInAction`, `ex:hasAuthorizationDecision`, `ex:appliedPolicy` | `P-AUD-07`, `P-GOV-02` | `M-AUD-01`, `M-AUD-03`, `M-GOV-02`, `M-TIME-01` | `EXT-Q70` | Directa | Cobertura/resultado esperado verificable en `EXT-Q70` conforme al artefacto y escenario versionados. |
| **RNF-31** | `ex:QuerySpecification`, `ex:InspectionQueryType`, `ex:WarningQueryType`, `ex:ViolationQueryType` | `P-VAL-02` | `M-VAL-02` | `EXT-Q80` | Mixta: consulta indirecta | Cada consulta debe declarar un tipo y criterio de interpretación inequívocos; la documentación de la batería y `EXT-Q80` deben permitir distinguir inspección, revisión/advertencia, incumplimiento, ASK y dashboard. |
| **RNF-32** | `ex:TrustAssessment`, `ex:trustRuleVersion`, `ex:trustWindowStart`, `ex:trustWindowEnd`, `ex:hasTrustEvidence` | `P-AUD-07`, `P-NODE-03`, `P-NODE-04` | `M-AUD-01`, `M-AUD-03`, `M-TIME-01`, `M-TRUST-01`, `M-VAL-04` | `EXT-Q40`, `EXT-Q43` | Directa | Revisión explícita de `EXT-Q43`; cualquier pendiente debe quedar justificado o resuelto antes de aceptación. |
| **RNF-33** | `ex:EvaluationState`, `ex:DecisionAlternative`, `ex:hasConsistencyThreshold`, `ex:hasTrustAssessment` | `P-AUD-07`, `P-MODEL-03`, `P-MODEL-05`, `P-NODE-04` | `M-AUD-01`, `M-AUD-03`, `M-MODEL-01`, `M-MODEL-02`, `M-TIME-01`, `M-TRUST-01`, `M-TRUST-02` | `EXT-Q49`, `EXT-Q52` | Directa | Revisión explícita de `EXT-Q52`; cualquier pendiente debe quedar justificado o resuelto antes de aceptación. |
| **RNF-34** | `ex:AHPDecisionMethod`, `ex:WeightedMulticriteriaMethod`, `ex:hasConsistencyRatio`, `ex:hasConsistencyThreshold` | `P-MODEL-02`, `P-MODEL-04` | `M-MODEL-02`, `M-MODEL-03` | `EXT-Q48`, `EXT-Q49`, `EXT-Q50`, `EXT-Q76` | Directa | 0 filas en `EXT-Q48`, `EXT-Q50`, tras las precondiciones de RF-71/RV-02. |
| **RNF-35** | `ex:State`, `ex:TemporalEntity`, `ex:validFrom`, `ex:validTo` | `P-GOV-05` | `M-TIME-01` | `BASE-Q09`, `EXT-Q73` | Directa | Cobertura/resultado esperado verificable en `BASE-Q09`, `EXT-Q73` conforme al artefacto y escenario versionados. |
| **RNF-36** | `ex:State`, `ex:validFrom`, `ex:validTo`, `ex:plannedExpiry` | `P-AUD-02`, `P-AUD-03`, `P-CONS-02`, `P-GOV-05` | `M-CONS-01`, `M-DELEG-01`, `M-DELEG-02`, `M-TIME-01` | `EXT-Q73`, `EXT-Q74` | Directa | 0 filas en `EXT-Q74`, tras las precondiciones de RF-71/RV-02. |
| **RNF-37** | `ex:State`, `ex:derivedFrom`, `ex:TemporalEntity` | `P-GOV-05` | `M-TIME-01` | `EXT-Q73`, `EXT-Q74` | Mixta: consulta indirecta | Todo `ex:State` que derive de una observación debe enlazarla mediante `ex:derivedFrom`. `EXT-Q73`/`EXT-Q74` cubren temporalidad de forma indirecta; la batería v3 no contiene todavía una consulta dedicada exclusivamente a `derivedFrom`. |
| **RNF-38** | `ex:OntologyArtifact`, `ex:PolicyArtifact`, `ex:QueryCatalog`, `ex:ScenarioArtifact`, `ex:artifactVersion` | `P-FL-08`, `P-GOV-04`, `P-INT-02`, `P-VAL-05` | `M-GOV-02`, `M-GOV-04`, `M-INT-02`, `M-MODEL-05`, `M-VAL-04`, `M-VAL-05` | `EXT-Q01`, `EXT-Q02`, `EXT-Q05`, `EXT-Q77`, `EXT-Q80` | Mixta: consulta indirecta | Una versión nueva debe superar regresión sobre escenarios y consultas de línea base; cambios incompatibles requieren nueva versión mayor y actualización de trazabilidad (`EXT-Q01`, `EXT-Q02`, `EXT-Q05`, `EXT-Q77`, `EXT-Q80`). |
| **RNF-39** | `ex:OntologyArtifact`, `ex:PolicyArtifact`, `ex:RequirementsArtifact`, `ex:ScenarioArtifact`, `ex:ValidationCampaign`, `ex:artifactVersion` | `P-DATA-03`, `P-FL-08`, `P-GOV-04`, `P-OPS-01`, `P-VAL-04`, `P-VAL-08` | `M-GOV-02`, `M-GOV-04`, `M-MODEL-05`, `M-OPS-01`, `M-SEC-01`, `M-VAL-04`, `M-VAL-07` | `EXT-Q01`, `EXT-Q08`, `EXT-Q77` | Directa | Revisión explícita de `EXT-Q77`; cualquier pendiente debe quedar justificado o resuelto antes de aceptación. |

### 4.3 Requisitos de validación y reproducibilidad

| Requisito | Elementos ontológicos / estándares | Políticas | Mecanismos | Consultas | Cobertura | Criterio de aceptación |
|---|---|---|---|---|---|---|
| **RV-01** | `ex:QuerySpecification`, `ex:QueryCatalog`, `ex:ValidationCampaign`, `ex:OntologyArtifact` | `P-VAL-02`, `P-VAL-04` | `M-GOV-04`, `M-VAL-02`, `M-VAL-04` | `EXT-Q01`, `EXT-Q75`, `EXT-Q80` | Directa | Cobertura/resultado esperado verificable en `EXT-Q01`, `EXT-Q75`, `EXT-Q80` conforme al artefacto y escenario versionados. |
| **RV-02** | `ex:ViolationQueryType`, `ex:ValidationCampaign`, `ex:AcceptanceProfile`, `ex:OntologyArtifact` | `P-VAL-03` | `M-VAL-03` | `EXT-Q77` | Directa | Cero filas solo tras superar precondiciones de versión, dataset, cobertura y ejecución (`EXT-Q01`, `EXT-Q02`, `EXT-Q05`, `EXT-Q76`, `EXT-Q77`). |
| **RV-03** | `ex:ValidationCampaign`, `ex:OntologyArtifact`, `ex:PolicyArtifact`, `ex:ScenarioArtifact`, `ex:QueryCatalog`, `Apache Jena Fuseki`, `SPARQL 1.1` | `P-VAL-01`, `P-VAL-04`, `P-VAL-07` | `M-GOV-04`, `M-VAL-01`, `M-VAL-04`, `M-VAL-06` | `EXT-Q01`, `EXT-Q05`, `EXT-Q77` | Directa | Revisión explícita de `EXT-Q77`; cualquier pendiente debe quedar justificado o resuelto antes de aceptación. |
| **RV-04** | `ex:Requirement`, `ex:tracedToPolicy`, `ex:tracedToMechanism`, `ex:Policy`, `ex:MechanismSpecification`, `ex:QuerySpecification` | `P-GOV-04`, `P-VAL-06` | `M-GOV-02`, `M-GOV-04`, `M-VAL-04`, `M-VAL-05` | `EXT-Q02`, `EXT-Q04`, `EXT-Q07`, `EXT-Q08`, `EXT-Q09` | Directa | Revisión explícita de `EXT-Q09`; cualquier pendiente debe quedar justificado o resuelto antes de aceptación. |
| **RV-05** | `ex:ConsentRecord`, `ex:SemanticContract`, `ex:Policy`, `ex:RestrictedZone`, `ex:TrustAssessment`, `ex:EvaluationState`, `ex:PrivacyBudgetAccount`, `ex:DelegationEvent` | `P-VAL-06`, `P-VAL-08` | `M-VAL-04`, `M-VAL-05`, `M-VAL-07` | `EXT-Q80` | Directa | Cobertura/resultado esperado verificable en `EXT-Q80` conforme al artefacto y escenario versionados. |

### 4.4 Cobertura global de la trazabilidad

- **Requisitos:** 72 RF + 39 RNF + 5 RV = **116 requisitos**.
- **Consultas disponibles:** 35 BASE + 80 EXT = **115 consultas SPARQL**.
- **Políticas:** **79 políticas** organizadas por categorías `GOV`, `CONS`, `DATA`, `ZONE`, `NODE`, `MODEL`, `ADAPT`, `FL`, `AUD`, `OPS`, `INT` y `VAL`.
- **Mecanismos:** **55 mecanismos** representados como `ex:MechanismSpecification`.
- **Escenarios:** **S1–S17**, representados y versionados mediante el artefacto de escenarios v3.
- **Trazabilidad estructural derivada:** `RF-01`, `RF-02`, `RF-06`, `RF-11`, `RF-12` y `RF-13` no poseen actualmente `ex:tracedToPolicy`/`ex:tracedToMechanism` directo en la TTL; la asociación indicada se deriva de las políticas temáticas y de las consultas v3 que los cubren.
- **Cobertura de consultas indirecta:** los requisitos con consultas marcadas `‡` disponen de consultas v3 pertinentes, pero el encabezado `Requirements:` de esas consultas no declara todavía el requisito.
- **Catálogo de consultas en la TTL:** la ontología v3 define `ex:QueryCatalog`/`ex:QuerySpecification`, pero las 115 consultas viven actualmente en el artefacto externo `sparql_battery_v3.0.0.sparql`; no están instanciadas individualmente dentro de la TTL.
- **Cobertura temporal pendiente:** `RNF-37` requiere `ex:derivedFrom`; la batería actual aporta cobertura temporal indirecta (`EXT-Q73`, `EXT-Q74`) pero no una consulta dedicada a esa propiedad.
- **Métricas observadas pendientes de especialización:** `RF-29` y `RNF-27` exigen latencia/consumo energético medibles. La ontología dispone de parámetros de aceptación y métricas de carga/migración, pero no de una propiedad genérica específica para persistir latencia observada ni consumo energético observado.
