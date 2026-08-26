# Políticas y mecanismos

**Identificador del artefacto:** `POLICIES-REV-01`  
**Fecha de revisión:** 2026-08-26  
**Documento de requisitos de referencia:** versión revisada con RF-01–RF-72, RNF-01–RNF-39 y RV-01–RV-05.  
**Ontología de referencia:** `smartcity_continuum_v3.0.0.ttl`.  
**Batería SPARQL de referencia:** `sparql_battery_v3.0.0.sparql` (`BASE-Q01`–`BASE-Q35`, `EXT-Q01`–`EXT-Q80`).

Este documento sustituye la organización anterior de políticas. Las reglas se han reagrupado por dominio para eliminar solapamientos y resolver incompatibilidades con los requisitos revisados. Los identificadores anteriores `P-01`–`P-84` no se reutilizan porque varias reglas se han fusionado, dividido o cambiado de semántica.

Las consultas SPARQL de esta versión se han completado contra la batería `sparql_battery_v3.0.0.sparql`, formada por `BASE-Q01`–`BASE-Q35` y `EXT-Q01`–`EXT-Q80`. La trazabilidad se alinea con `smartcity_continuum_v3.0.0.ttl` y con el documento de requisitos revisado v3.0.0. El símbolo `†` identifica cobertura SPARQL indirecta: la consulta cubre los requisitos de la política, aunque el metadato `Políticas relacionadas` del catálogo no referencia nominalmente esa política.

## Índice

### Índice general

1. [Criterios generales de aplicación](#0-criterios-generales-de-aplicación)
2. [Políticas de gobernanza, precedencia y ciclo de vida](#1-políticas-de-gobernanza-precedencia-y-ciclo-de-vida)
3. [Políticas de consentimiento y contratos semánticos](#2-políticas-de-consentimiento-y-contratos-semánticos)
4. [Políticas de datos, privacidad, identidad y transmisión](#3-políticas-de-datos-privacidad-identidad-y-transmisión)
5. [Políticas de zona y georrestricción](#4-políticas-de-zona-y-georrestricción)
6. [Políticas de nodos y confianza dinámica](#5-políticas-de-nodos-y-confianza-dinámica)
7. [Políticas de selección de modelo y decisión AHP](#6-políticas-de-selección-de-modelo-y-decisión-ahp)
8. [Políticas de migración, offloading, degradación y continuidad](#7-políticas-de-migración-offloading-degradación-y-continuidad)
9. [Políticas de aprendizaje federado y ciclo de vida de modelos](#8-políticas-de-aprendizaje-federado-y-ciclo-de-vida-de-modelos)
10. [Políticas de delegación temporal, MAPE-K y auditoría](#9-políticas-de-delegación-temporal-mape-k-y-auditoría)
11. [Políticas operativas, escalabilidad y calidad de servicio](#10-políticas-operativas-escalabilidad-y-calidad-de-servicio)
12. [Políticas de interoperabilidad y extensibilidad semántica](#11-políticas-de-interoperabilidad-y-extensibilidad-semántica)
13. [Políticas de validación, reproducibilidad y mantenibilidad](#12-políticas-de-validación-reproducibilidad-y-mantenibilidad)
14. [Análisis de compatibilidad y conflictos](#13-análisis-de-compatibilidad-y-conflictos-entre-categorías-de-políticas)
15. [Mecanismos de actuación revisados](#14-mecanismos-de-actuación-revisados)
16. [Escenarios operativos y científicos](#15-escenarios-operativos-y-científicos-a-documentar)
17. [Principales correcciones respecto al documento anterior](#16-principales-correcciones-respecto-al-documento-anterior)
18. [Matriz completa de trazabilidad de políticas](#17-matriz-completa-de-trazabilidad-de-políticas)

### Índice de categorías de políticas

| Categoría | Dominio | Políticas | Nº |
|---|---|---|---:|
| `GOV` | Gobernanza, precedencia y temporalidad | `P-GOV-01`–`P-GOV-05` | 5 |
| `CONS` | Consentimiento y contratos | `P-CONS-01`–`P-CONS-06` | 6 |
| `DATA` | Datos, privacidad, identidad y transmisión | `P-DATA-01`–`P-DATA-10` | 10 |
| `ZONE` | Zonas y georrestricción | `P-ZONE-01`–`P-ZONE-04` | 4 |
| `NODE` | Nodos y confianza | `P-NODE-01`–`P-NODE-06` | 6 |
| `MODEL` | Selección de modelo y AHP | `P-MODEL-01`–`P-MODEL-09` | 9 |
| `ADAPT` | Migración, offloading y degradación | `P-ADAPT-01`–`P-ADAPT-08` | 8 |
| `FL` | Aprendizaje federado y modelos | `P-FL-01`–`P-FL-08` | 8 |
| `AUD` | Delegación, MAPE-K y auditoría | `P-AUD-01`–`P-AUD-07` | 7 |
| `OPS` | Operación, escalabilidad y QoS | `P-OPS-01`–`P-OPS-06` | 6 |
| `INT` | Interoperabilidad y extensibilidad | `P-INT-01`–`P-INT-02` | 2 |
| `VAL` | Validación y reproducibilidad | `P-VAL-01`–`P-VAL-08` | 8 |
| **Total** |  |  | **79** |

---

## 0. Criterios generales de aplicación

- Toda política formal debe pertenecer a **un único tipo**: obligación, abstención o prohibición.
- Las políticas de **prohibición** descartan una acción como no autorizada; las de **abstención** impiden ejecutar una acción opcional mientras no se cumpla una condición habilitante; las de **obligación** fuerzan una acción positiva.
- La autorización efectiva de procesamiento se determina aplicando conjuntamente consentimiento activo, contrato semántico, política de zona y demás restricciones duras. En caso de conflicto prevalece siempre la condición más restrictiva.
- Las restricciones duras se evalúan antes de optimizar latencia, calidad, carga, coste o confianza.
- `trust` es un criterio externo de elegibilidad/ordenación y **no forma parte de los pesos AHP**.
- El ámbito local se limita al dispositivo móvil/vestible y, cuando la política lo permita, a la capa mist asociada. Edge, Fog y Cloud se consideran externos a dicho ámbito.
- Una réplica controlada no debe confundirse con un duplicado accidental. La replicación autorizada debe ser versionada e idempotente.
- `validTo` representa el cierre efectivo de un estado o delegación. Una expiración planificada debe registrarse en un atributo o relación diferente.

---

## 1. Políticas de gobernanza, precedencia y ciclo de vida

### P-GOV-01 — Tipado único de políticas

**Tipo de política:** Obligación

Toda política formal del sistema debe representarse como una entidad explícita y clasificarse en exactamente uno de los tipos obligación, abstención o prohibición. Los tipos deben ser mutuamente distinguibles y no puede asignarse más de uno a la misma política formal.

**Requisitos relacionados:** `RF-39`, `RF-40`

**Mecanismos recomendados:** `M-GOV-01`

**Consultas SPARQL asociadas:** `EXT-Q03`, `EXT-Q06`, `EXT-Q10`  

### P-GOV-02 — Vinculación explícita de gobernanza

**Tipo de política:** Obligación

Toda entidad o decisión sujeta a gobernanza debe mantener una relación explícita con la política o conjunto de políticas que la gobiernan. Toda evaluación, migración, degradación, delegación o selección de modelo debe registrar qué política concreta se aplicó.

**Requisitos relacionados:** `RF-41`, `RF-44`, `RNF-28`, `RNF-30`

**Mecanismos recomendados:** `M-GOV-02`, `M-AUD-01`

**Consultas SPARQL asociadas:** `EXT-Q08`†, `EXT-Q70`†, `EXT-Q72`†  

### P-GOV-03 — Precedencia de la restricción más estricta

**Tipo de política:** Prohibición

No puede autorizarse una acción que exceda cualquiera de las restricciones vigentes de consentimiento, contrato semántico, zona, seguridad o capacidad del recurso. Cuando existan reglas concurrentes, la elegibilidad final debe corresponder a su intersección más restrictiva.

**Requisitos relacionados:** `RF-35`, `RF-42`, `RF-43`, `RNF-22`

**Mecanismos recomendados:** `M-GOV-03`, `M-CONS-02`, `M-ZONE-01`

**Consultas SPARQL asociadas:** `EXT-Q07`, `EXT-Q17`, `EXT-Q19`, `EXT-Q37`, `EXT-Q78`, `EXT-Q79`  

### P-GOV-04 — Determinismo y versionado de políticas

**Tipo de política:** Obligación

Las políticas de adaptación deben estar versionadas. Dado el mismo estado de entrada, consentimiento, contrato, zona y versión de políticas, el sistema debe obtener la misma decisión de elegibilidad y registrar la versión aplicada. Durante una campaña de aceptación no debe alterarse una política sin cambiar explícitamente la versión del artefacto.

**Requisitos relacionados:** `RNF-20`, `RNF-22`, `RNF-38`, `RNF-39`, `RV-04`

**Mecanismos recomendados:** `M-GOV-04`, `M-VAL-04`

**Consultas SPARQL asociadas:** `EXT-Q03`, `EXT-Q10`  

### P-GOV-05 — Ciclo temporal de estados

**Tipo de política:** Obligación

Todo estado debe modelarse como una entidad temporal de primera clase. Debe registrar `validFrom` al crearse y `validTo` únicamente cuando finalice. Cuando el estado derive de una observación, debe conservar un enlace explícito a la evidencia de origen. Una expiración planificada no debe reutilizar `validTo` antes del cierre efectivo.

**Requisitos relacionados:** `RNF-35`, `RNF-36`, `RNF-37`

**Mecanismos recomendados:** `M-TIME-01`

**Consultas SPARQL asociadas:** `BASE-Q09`, `EXT-Q73`, `EXT-Q74`  
---

## 2. Políticas de consentimiento y contratos semánticos

### P-CONS-01 — Consentimiento por rangos y revocación

**Tipo de política:** Obligación

El consentimiento debe expresarse mediante rangos de procesamiento que contemplen al menos ámbito local, agregación comunitaria, agregación global y denegación/revocación. Deben poder especificarse categorías de datos, propósito, intervalo de validez y rango máximo autorizado.

**Requisitos relacionados:** `RF-32`

**Mecanismos recomendados:** `M-CONS-01`

**Consultas SPARQL asociadas:** `BASE-Q01`, `BASE-Q15`, `BASE-Q31`, `EXT-Q11`, `EXT-Q13`, `EXT-Q16`  

### P-CONS-02 — Contrato efectivo único por usuario y propósito

**Tipo de política:** Prohibición

No pueden coexistir dos contratos semánticos efectivos para el mismo usuario, propósito e instante. Se permiten contratos históricos o contratos simultáneos para propósitos diferentes siempre que sus intervalos no produzcan ambigüedad para el mismo propósito.

**Requisitos relacionados:** `RF-33`, `RNF-36`

**Mecanismos recomendados:** `M-CONS-01`, `M-TIME-01`

**Consultas SPARQL asociadas:** `BASE-Q20`, `EXT-Q12`, `EXT-Q14`, `EXT-Q15`  

### P-CONS-03 — Contenido mínimo del contrato

**Tipo de política:** Obligación

Todo contrato semántico efectivo debe identificar al usuario, propósito de procesamiento, rango de consentimiento, intervalo de validez y políticas que gobiernan el tratamiento.

**Requisitos relacionados:** `RF-34`, `RF-41`

**Mecanismos recomendados:** `M-CONS-01`, `M-GOV-02`

**Consultas SPARQL asociadas:** `BASE-Q20`, `EXT-Q12`, `EXT-Q14`  

### P-CONS-04 — Autorización efectiva e inconsistencias

**Tipo de política:** Prohibición

Cuando consentimiento activo, contrato y política de zona no sean compatibles, no puede ejecutarse procesamiento externo que exceda la intersección más restrictiva. La inconsistencia debe quedar registrada y el procesamiento afectado permanecer bloqueado hasta que exista una autorización efectiva inequívoca.

**Requisitos relacionados:** `RF-35`, `RF-36`, `RNF-22`

**Mecanismos recomendados:** `M-CONS-02`, `M-GOV-03`

**Consultas SPARQL asociadas:** `BASE-Q15`, `BASE-Q25`, `BASE-Q28`, `EXT-Q11`, `EXT-Q16`, `EXT-Q17`, `EXT-Q18`, `EXT-Q19`, `EXT-Q20`, `EXT-Q39`, `EXT-Q56`  

### P-CONS-05 — Declaración del rango mínimo requerido

**Tipo de política:** Obligación

Todo recurso, permiso, modelo, servicio, sesión o acción que dependa del consentimiento debe declarar el rango mínimo necesario antes de ser considerado elegible.

**Requisitos relacionados:** `RF-37`

**Mecanismos recomendados:** `M-CONS-03`

**Consultas SPARQL asociadas:** `BASE-Q06`, `EXT-Q21`  

### P-CONS-06 — Recepción descendente sin ampliación de consentimiento

**Tipo de política:** Abstención

La recepción de modelos genéricos mejorados solo puede realizarse sin ampliar el rango de consentimiento cuando el flujo descendente cumple el contrato y las políticas activas y no contiene datos personales, gradientes individualizados ni identificadores persistentes derivados del usuario.

**Requisitos relacionados:** `RF-23`, `RF-38`

**Mecanismos recomendados:** `M-FL-02`, `M-CONS-02`

**Consultas SPARQL asociadas:** `BASE-Q15`†, `EXT-Q66`†  
---

## 3. Políticas de datos, privacidad, identidad y transmisión

### P-DATA-01 — Confinamiento de observaciones fisiológicas crudas

**Tipo de política:** Prohibición

Las observaciones fisiológicas crudas no pueden abandonar el ámbito local. No pueden transmitirse a Edge, Fog ni Cloud. Cualquier procesamiento externo debe utilizar datos parametrizados o actualizaciones de modelo expresamente autorizadas.

**Requisitos relacionados:** `RF-10`, `RF-60`, `RNF-17`

**Mecanismos recomendados:** `M-DATA-01`, `M-TX-01`

**Consultas SPARQL asociadas:** `BASE-Q18`, `EXT-Q22`  

### P-DATA-02 — Pseudonimización de identificadores externos

**Tipo de política:** Prohibición

Ningún identificador personal directo puede viajar fuera del ámbito local junto con datos parametrizados, gradientes o actualizaciones federadas. Todo flujo autorizado debe utilizar identificadores pseudónimos o anonimizados adecuados a su finalidad.

**Requisitos relacionados:** `RF-61`, `RNF-17`, `RNF-19`

**Mecanismos recomendados:** `M-ID-01`, `M-TX-01`

**Consultas SPARQL asociadas:** `BASE-Q01`, `EXT-Q23`, `EXT-Q26`, `EXT-Q27`, `EXT-Q28`  

### P-DATA-03 — Cifrado de información sensible

**Tipo de política:** Obligación

Todo dato clasificado como sensible debe protegerse en tránsito y en reposo de acuerdo con la línea base de seguridad versionada del despliegue. La política debe aplicarse también a buffers temporales y réplicas autorizadas.

**Requisitos relacionados:** `RNF-15`, `RNF-39`

**Mecanismos recomendados:** `M-SEC-01`, `M-VAL-04`

**Consultas SPARQL asociadas:** `EXT-Q23`, `EXT-Q29`, `EXT-Q30`, `EXT-Q32`  

### P-DATA-04 — Puerta de transmisión por tipo de dato

**Tipo de política:** Abstención

Un dato parametrizado no debe transmitirse hasta que esté marcado como preparado para transmisión y disponga de los metadatos contextuales exigidos. Esta regla no debe utilizarse para bloquear flujos de otro tipo, como descargas de modelos, que se gobiernan por sus propias políticas.

**Requisitos relacionados:** `RF-04`, `RF-09`, `RF-27`

**Mecanismos recomendados:** `M-TX-01`, `M-DATA-02`

**Consultas SPARQL asociadas:** `BASE-Q10`, `BASE-Q28`  

### P-DATA-05 — Retención en la capa más alta autorizada

**Tipo de política:** Obligación

Cuando un dato no pueda transmitirse por conectividad, energía, saturación, zona o autorización, debe conservarse temporalmente en la capa más alta permitida por la autorización efectiva. Si no se permite almacenamiento externo, debe permanecer exclusivamente en el ámbito local hasta una ventana segura o hasta su descarte autorizado.

**Requisitos relacionados:** `RF-08`, `RF-26`, `RNF-12`

**Mecanismos recomendados:** `M-BUFFER-01`, `M-CONS-02`, `M-ZONE-01`

**Consultas SPARQL asociadas:** `EXT-Q31`, `EXT-Q32`  

### P-DATA-06 — Gestión energética de procesamiento y transmisión

**Tipo de política:** Obligación

Con batería baja se deben reducir complejidad de modelo y transmisiones no críticas. Con batería crítica se debe intentar offloading únicamente hacia una capa autorizada y con conectividad suficiente; si no existe una opción externa autorizada, se debe aplicar degradación local y retención temporal.

**Requisitos relacionados:** `RF-07`, `RF-27`, `RNF-06`

**Mecanismos recomendados:** `M-DEVICE-01`, `M-ADAPT-02`, `M-BUFFER-01`

**Consultas SPARQL asociadas:** `BASE-Q10`  

### P-DATA-07 — Ventana segura de transmisión y reconexión

**Tipo de política:** Abstención

Los flujos pendientes no deben reanudarse simplemente por recuperar conectividad. La sincronización o transmisión solo puede reiniciarse cuando exista simultáneamente conectividad suficiente, autorización efectiva, destino elegible y condiciones de energía compatibles.

**Requisitos relacionados:** `RF-26`, `RF-27`, `RNF-12`, `RNF-13`

**Mecanismos recomendados:** `M-TX-02`, `M-NODE-02`, `M-CONS-02`

**Consultas SPARQL asociadas:** `BASE-Q10`, `BASE-Q17`, `EXT-Q31`, `EXT-Q38`  

### P-DATA-08 — Redundancia, replicación e idempotencia

**Tipo de política:** Prohibición

Los duplicados accidentales o datos marcados como redundantes sin finalidad de réplica no deben incorporarse a flujos externos. Las réplicas controladas quedan permitidas únicamente cuando se identifiquen como tales, estén versionadas y su sincronización sea idempotente.

**Requisitos relacionados:** `RF-19`, `RF-28`, `RNF-13`

**Mecanismos recomendados:** `M-REPL-01`, `M-TX-01`

**Consultas SPARQL asociadas:** `EXT-Q33`, `EXT-Q34`  

### P-DATA-09 — Priorización por criticidad

**Tipo de política:** Obligación

La programación de transmisión debe priorizar datos críticos sobre datos secundarios mediante una clasificación genérica de criticidad. Los datos no transmisibles o redundantes deben permanecer retenidos según la política aplicable y no desplazar a los datos críticos de una ventana limitada.

**Requisitos relacionados:** `RF-27`, `RF-28`

**Mecanismos recomendados:** `M-TX-03`, `M-BUFFER-01`

**Consultas SPARQL asociadas:** `EXT-Q35`  

### P-DATA-10 — Contexto mínimo de datos procesados

**Tipo de política:** Obligación

Los datos utilizados fuera de su observación inmediata deben conservar el contexto mínimo necesario para interpretar su uso: tiempo, localización o zona aplicable, calidad de señal, estado de dispositivo, estado de nodo, nivel de procesamiento y propósito.

**Requisitos relacionados:** `RF-09`, `RF-30`, `RNF-27`

**Mecanismos recomendados:** `M-DATA-02`, `M-TIME-01`

**Consultas SPARQL asociadas:** `EXT-Q23`, `EXT-Q24`, `EXT-Q25`  
---

## 4. Políticas de zona y georrestricción

### P-ZONE-01 — Zona restringida: confinamiento local

**Tipo de política:** Prohibición

Cuando el origen del procesamiento se encuentre en una zona restringida, los datos del usuario y el procesamiento asociado no pueden salir del ámbito local: quedan excluidos Edge, Fog y Cloud. La recepción de un modelo genérico no derivado del usuario solo puede permitirse si una política explícita de la zona autoriza tráfico de entrada y no implica extracción de información del usuario.

**Requisitos relacionados:** `RF-42`, `RF-43`, `RF-53`, `RNF-22`

**Mecanismos recomendados:** `M-ZONE-01`, `M-CONS-02`

**Consultas SPARQL asociadas:** `BASE-Q18`, `BASE-Q34`, `EXT-Q22`, `EXT-Q36`, `EXT-Q37`, `EXT-Q56`  

### P-ZONE-02 — Zona rural: retención por defecto

**Tipo de política:** Obligación

En zona rural los datos pendientes deben retenerse localmente por defecto y solo transmitirse durante una ventana segura que satisfaga conectividad, energía, autorización efectiva y elegibilidad del destino.

**Requisitos relacionados:** `RF-08`, `RF-26`, `RF-42`

**Mecanismos recomendados:** `M-ZONE-01`, `M-BUFFER-01`, `M-TX-02`

**Consultas SPARQL asociadas:** `BASE-Q17`, `EXT-Q38`  

### P-ZONE-03 — Zona urbana: agregación condicionada

**Tipo de política:** Abstención

La presencia de infraestructura urbana no autoriza por sí sola agregación Edge/Fog ni selección de tiers superiores. La agregación solo puede ejecutarse cuando consentimiento efectivo, contrato, política activa y elegibilidad del destino la permitan.

**Requisitos relacionados:** `RF-42`, `RF-15`, `RF-36`

**Mecanismos recomendados:** `M-ZONE-01`, `M-CONS-02`, `M-NODE-02`

**Consultas SPARQL asociadas:** `EXT-Q39`  

### P-ZONE-04 — Cambio de zona y reevaluación

**Tipo de política:** Obligación

Todo cambio de zona que pueda modificar la autorización o la elegibilidad de una capa debe invalidar la decisión previa y provocar una reevaluación antes de continuar nuevos flujos o procesamiento externo.

**Requisitos relacionados:** `RF-03`, `RF-15`, `RF-17`, `RNF-21`

**Mecanismos recomendados:** `M-CTX-01`, `M-MODEL-04`

**Consultas SPARQL asociadas:** `BASE-Q09`†, `BASE-Q23`†, `EXT-Q46`†, `EXT-Q59`†  
---

## 5. Políticas de nodos y confianza dinámica

### P-NODE-01 — Estados operativos y elegibilidad

**Tipo de política:** Prohibición

Un nodo `Inoperative` no puede seleccionarse como destino de procesamiento, migración, HFL o delegación. Un nodo `ComputeOnly` solo puede seleccionarse para operaciones explícitamente compatibles con sus capacidades y restricciones actuales.

**Requisitos relacionados:** `RF-05`, `RF-17`, `RNF-12`

**Mecanismos recomendados:** `M-NODE-01`, `M-NODE-02`

**Consultas SPARQL asociadas:** `BASE-Q07`, `BASE-Q08`, `BASE-Q26`, `EXT-Q41`  

### P-NODE-02 — Filtros duros de candidatos

**Tipo de política:** Prohibición

Ningún nodo puede entrar en la fase de optimización si incumple disponibilidad mínima, conectividad necesaria, capacidad residual, autorización efectiva o restricciones de zona para la operación evaluada.

**Requisitos relacionados:** `RF-15`, `RF-18`, `RF-47`

**Mecanismos recomendados:** `M-NODE-02`, `M-CONS-02`, `M-ZONE-01`

**Consultas SPARQL asociadas:** `BASE-Q08`, `BASE-Q12`, `BASE-Q19`, `BASE-Q23`, `EXT-Q41`, `EXT-Q42`  

### P-NODE-03 — Trust score reproducible

**Tipo de política:** Obligación

Todo estado de nodo utilizado en una decisión adaptativa debe disponer de un trust score normalizado, acompañado de la versión de la regla de cálculo y de la ventana histórica o periodo de evidencias utilizado.

**Requisitos relacionados:** `RF-45`, `RF-49`, `RNF-32`

**Mecanismos recomendados:** `M-TRUST-01`, `M-VAL-04`

**Consultas SPARQL asociadas:** `BASE-Q07`, `EXT-Q40`, `EXT-Q43`  

### P-NODE-04 — Actualización del trust y doble contabilización

**Tipo de política:** Prohibición

La regla de actualización de trust puede considerar fallos, desconexiones, saturación e incumplimientos de políticas, pero no debe provocar que el mismo efecto de latencia o carga se contabilice de nuevo como criterio independiente en una decisión posterior sin justificación explícita.

**Requisitos relacionados:** `RF-49`, `RNF-32`, `RNF-33`

**Mecanismos recomendados:** `M-TRUST-01`, `M-AUD-01`

**Consultas SPARQL asociadas:** `EXT-Q40`  

### P-NODE-05 — Ordenación por confianza entre candidatos elegibles

**Tipo de política:** Obligación

Una vez aplicados los filtros duros, los candidatos elegibles deben ordenarse o priorizarse utilizando la confianza junto con las métricas operativas requeridas. Deben evitarse nodos saturados, inestables o históricamente poco fiables cuando exista una alternativa elegible mejor.

**Requisitos relacionados:** `RF-46`, `RF-47`, `RF-48`

**Mecanismos recomendados:** `M-TRUST-02`, `M-NODE-02`

**Consultas SPARQL asociadas:** `BASE-Q19`, `EXT-Q42`, `EXT-Q44`  

### P-NODE-06 — Ausencia de alternativas confiables

**Tipo de política:** Abstención

Si no existe un nodo externo que cumpla los mínimos de elegibilidad y confianza, el sistema no debe forzar un tier superior. Debe preferir retención, degradación local o diferimiento de la operación y registrar la ausencia de alternativas.

**Requisitos relacionados:** `RF-47`, `RF-48`, `RF-53`

**Mecanismos recomendados:** `M-NODE-02`, `M-ADAPT-02`, `M-AUD-01`

**Consultas SPARQL asociadas:** `BASE-Q19`†, `EXT-Q42`†, `EXT-Q45`†, `EXT-Q56`†  
---

## 6. Políticas de selección de modelo y decisión AHP

### P-MODEL-01 — Selección por adecuación, no por tier máximo

**Tipo de política:** Obligación

El sistema debe seleccionar el tier más adecuado entre las alternativas elegibles y no el tier más alto por defecto. La decisión debe aplicar primero restricciones duras y después optimizar entre las alternativas restantes.

**Requisitos relacionados:** `RF-15`, `RF-52`, `RF-53`

**Mecanismos recomendados:** `M-MODEL-01`, `M-NODE-02`

**Consultas SPARQL asociadas:** `BASE-Q04`, `BASE-Q32`, `EXT-Q46`  

### P-MODEL-02 — Criterios y normalización AHP

**Tipo de política:** Obligación

Cuando se utilice AHP, los pesos normalizados deben corresponder a latencia, privacidad y calidad del modelo. Su suma debe ser 1 dentro de la tolerancia configurada. La confianza no forma parte de dicha normalización.

**Requisitos relacionados:** `RF-50`, `RF-55`, `RNF-34`

**Mecanismos recomendados:** `M-MODEL-02`

**Consultas SPARQL asociadas:** `EXT-Q48`  

### P-MODEL-03 — Confianza como criterio externo

**Tipo de política:** Prohibición

El trust score o peso de confianza no puede incorporarse como cuarto peso dentro de la normalización AHP. Puede utilizarse como filtro, criterio de ordenación o ajuste externo documentado después de establecer la elegibilidad.

**Requisitos relacionados:** `RF-46`, `RF-50`, `RF-55`, `RNF-05`, `RNF-33`

**Mecanismos recomendados:** `M-TRUST-02`, `M-MODEL-02`

**Consultas SPARQL asociadas:** `EXT-Q42`, `EXT-Q44`, `EXT-Q48`  

### P-MODEL-04 — Consistencia del método AHP

**Tipo de política:** Prohibición

Una evaluación etiquetada como AHP no puede considerarse válida si sus pesos no están normalizados o si el ratio de consistencia supera el umbral configurado. Si no se utilizan comparaciones por pares ni control de consistencia, la decisión debe etiquetarse como puntuación multicriterio ponderada y no como AHP.

**Requisitos relacionados:** `RF-55`, `RNF-34`

**Mecanismos recomendados:** `M-MODEL-03`

**Consultas SPARQL asociadas:** `EXT-Q49`, `EXT-Q50`  

### P-MODEL-05 — Puntuación por alternativa y explicación

**Tipo de política:** Obligación

Toda evaluación de selección debe conservar la puntuación de cada tier candidato evaluado, el tier finalmente seleccionado y una justificación que permita explicar por qué la alternativa ganadora superó a las demás.

**Requisitos relacionados:** `RF-51`, `RF-54`, `RNF-29`, `RNF-33`

**Mecanismos recomendados:** `M-MODEL-01`, `M-AUD-01`

**Consultas SPARQL asociadas:** `BASE-Q21`, `EXT-Q46`, `EXT-Q51`, `EXT-Q52`, `EXT-Q53`  

### P-MODEL-06 — Prioridad de privacidad

**Tipo de política:** Obligación

Cuando el criterio de privacidad sea dominante o el consentimiento efectivo limite la agregación, la decisión debe favorecer los tiers locales o Edge únicamente si Edge sigue siendo una alternativa autorizada. Una restricción dura siempre prevalece sobre la puntuación de calidad.

**Requisitos relacionados:** `RF-52`, `RF-35`, `RF-42`

**Mecanismos recomendados:** `M-MODEL-01`, `M-CONS-02`, `M-ZONE-01`

**Consultas SPARQL asociadas:** `BASE-Q15`  

### P-MODEL-07 — Selección de Cloud condicionada

**Tipo de política:** Abstención

Cloud no debe seleccionarse hasta verificar consentimiento efectivo, contrato, zona, elegibilidad del nodo y confianza. La privacidad diferencial se exige adicionalmente cuando la operación implique aprendizaje federado, gradientes o actualizaciones sujetas a dicha protección, pero no como condición genérica para toda inferencia.

**Requisitos relacionados:** `RF-53`, `RF-56`, `RF-59`

**Mecanismos recomendados:** `M-MODEL-01`, `M-FL-03`

**Consultas SPARQL asociadas:** `EXT-Q56`  

### P-MODEL-08 — Separación entre calidad observada y pesos de decisión

**Tipo de política:** Obligación

La confianza de predicción, error estimado, feedback local y calidad observada del modelo deben registrarse como métricas de evaluación independientes. Los pesos de AHP no pueden utilizarse como sustituto de estas métricas.

**Requisitos relacionados:** `RF-14`, `RNF-27`

**Mecanismos recomendados:** `M-METRIC-01`, `M-AUD-01`

**Consultas SPARQL asociadas:** `EXT-Q54`, `EXT-Q55`  

### P-MODEL-09 — Reevaluación de selección vigente

**Tipo de política:** Obligación

Cuando cambien contexto, consentimiento, contrato, zona, conectividad, carga o confianza y la selección vigente deje de ser válida, debe iniciarse una nueva evaluación y completarse dentro del límite configurado para reselección.

**Requisitos relacionados:** `RF-15`, `RF-17`, `RNF-21`

**Mecanismos recomendados:** `M-MODEL-04`, `M-CTX-01`

**Consultas SPARQL asociadas:** `BASE-Q21`†, `EXT-Q46`†, `EXT-Q59`†, `EXT-Q76`†  
---

## 7. Políticas de migración, offloading, degradación y continuidad

### P-ADAPT-01 — Decisión de migración multicondición

**Tipo de política:** Obligación

La migración u offloading debe decidirse considerando conjuntamente causa de adaptación, autorización efectiva, estado del origen, elegibilidad de destinos, latencia, coste, energía y continuidad del servicio. No debe activarse únicamente por una métrica aislada salvo que una política de seguridad la convierta en restricción dura.

**Requisitos relacionados:** `RF-16`, `RF-17`, `RF-18`, `RNF-03`

**Mecanismos recomendados:** `M-ADAPT-01`, `M-NODE-02`

**Consultas SPARQL asociadas:** `BASE-Q12`  

### P-ADAPT-02 — Degradación segura ante pérdida de comunicación o falta de destino

**Tipo de política:** Obligación

Ante pérdida de comunicación o ausencia de destinos elegibles, el sistema debe mantener las funciones críticas autorizadas localmente y degradar el procesamiento de forma controlada antes de intentar una transferencia no autorizada.

**Requisitos relacionados:** `RF-07`, `RF-17`, `RNF-12`

**Mecanismos recomendados:** `M-ADAPT-02`, `M-BUFFER-01`

**Consultas SPARQL asociadas:** `BASE-Q14`, `EXT-Q62`  

### P-ADAPT-03 — Degradación por sobrecarga

**Tipo de política:** Obligación

Ante sobrecarga, el sistema debe aplicar una degradación controlada del procesamiento, migración o delegación según las alternativas elegibles. El escalado a capas superiores solo puede utilizarse si supera las políticas de consentimiento, zona, capacidad y confianza.

**Requisitos relacionados:** `RF-17`, `RF-20`, `RNF-03`

**Mecanismos recomendados:** `M-ADAPT-01`, `M-ADAPT-02`, `M-OPS-02`

**Consultas SPARQL asociadas:** `EXT-Q62`  

### P-ADAPT-04 — Criterios de destino y coste de migración

**Tipo de política:** Abstención

Una migración no debe ejecutarse hacia un nodo no elegible ni cuando el tiempo/coste estimado exceda los límites configurados y exista una alternativa local o de degradación que preserve mejor la continuidad. La razón de la abstención debe registrarse.

**Requisitos relacionados:** `RF-16`, `RF-17`, `RNF-02`

**Mecanismos recomendados:** `M-ADAPT-01`, `M-NODE-02`, `M-AUD-01`

**Consultas SPARQL asociadas:** `EXT-Q45`  

### P-ADAPT-05 — Separación de migración, delegación y aprendizaje federado

**Tipo de política:** Prohibición

Una migración o delegación no debe crear automáticamente una sesión de aprendizaje federado ni un intercambio de gradientes. Las sesiones FL solo se crean cuando la operación sea realmente de aprendizaje federado y satisfaga sus políticas específicas.

**Requisitos relacionados:** `RF-16`, `RF-22`, `RF-25`, `RF-62`

**Mecanismos recomendados:** `M-ADAPT-03`, `M-FL-01`

**Consultas SPARQL asociadas:** `BASE-Q13`, `EXT-Q60`, `EXT-Q61`  

### P-ADAPT-06 — Registro de degradación y acción ejecutada

**Tipo de política:** Obligación

Toda degradación de modelo o servicio debe registrar una causa explícita y vincularse a la evaluación que la provocó y a la acción finalmente ejecutada.

**Requisitos relacionados:** `RF-20`, `RF-44`, `RF-66`

**Mecanismos recomendados:** `M-ADAPT-02`, `M-AUD-01`

**Consultas SPARQL asociadas:** `BASE-Q13`, `BASE-Q22`, `BASE-Q27`, `EXT-Q59`, `EXT-Q62`  

### P-ADAPT-07 — Delegación a destino elegible de mayor confianza

**Tipo de política:** Obligación

Cuando se decida delegar, debe elegirse preferentemente el destino con mayor confianza entre los candidatos que ya cumplen carga, disponibilidad, conectividad, capacidad residual y restricciones activas. No se exige que su trust score sea superior al del origen si la degradación del origen tiene otra causa.

**Requisitos relacionados:** `RF-48`, `RF-62`, `RNF-14`

**Mecanismos recomendados:** `M-TRUST-02`, `M-DELEG-01`

**Consultas SPARQL asociadas:** `EXT-Q45`  

### P-ADAPT-08 — Continuidad e idempotencia de recuperación

**Tipo de política:** Prohibición

Los procesos de migración, delegación, reconexión y recuperación no pueden producir pérdida de eventos críticos ni duplicados accidentales. Las operaciones reintentables deben disponer de semántica idempotente cuando corresponda.

**Requisitos relacionados:** `RF-19`, `RF-26`, `RNF-02`, `RNF-13`

**Mecanismos recomendados:** `M-REPL-01`, `M-TX-02`, `M-DELEG-02`

**Consultas SPARQL asociadas:** `BASE-Q10`†, `EXT-Q33`†, `EXT-Q34`†  
---

## 8. Políticas de aprendizaje federado y ciclo de vida de modelos

### P-FL-01 — Elegibilidad de sesiones federadas

**Tipo de política:** Abstención

Una sesión federada no debe iniciarse mientras alguno de los nodos participantes requeridos no cumpla las condiciones de elegibilidad, confianza y autorización aplicables al flujo. Si las condiciones pueden recuperarse, la sesión debe diferirse a una ventana válida.

**Requisitos relacionados:** `RF-21`, `RF-22`, `RF-25`, `RNF-12`

**Mecanismos recomendados:** `M-FL-01`, `M-NODE-02`

**Consultas SPARQL asociadas:** `BASE-Q16`, `BASE-Q30`, `EXT-Q66`  

### P-FL-02 — Autorización del flujo federado ascendente

**Tipo de política:** Prohibición

Ningún parámetro, modelo personalizado o gradiente puede enviarse hacia capas superiores si la autorización efectiva, la zona o las políticas de privacidad no permiten ese tipo de flujo.

**Requisitos relacionados:** `RF-21`, `RF-35`, `RF-42`

**Mecanismos recomendados:** `M-FL-01`, `M-CONS-02`, `M-ZONE-01`

**Consultas SPARQL asociadas:** `BASE-Q24`, `BASE-Q25`, `EXT-Q67`  

### P-FL-03 — Protección obligatoria de gradientes

**Tipo de política:** Obligación

Toda sesión que transporte gradientes debe declarar presupuesto de privacidad y nivel de ruido. Todo gradiente que salga de un dispositivo móvil debe estar anonimizado o pseudonimizado según corresponda y tener aplicado el ruido diferencial exigido antes de abandonar el dispositivo.

**Requisitos relacionados:** `RF-56`, `RF-57`, `RNF-16`, `RNF-17`

**Mecanismos recomendados:** `M-FL-03`, `M-ID-01`

**Consultas SPARQL asociadas:** `BASE-Q16`, `EXT-Q67`, `EXT-Q68`  

### P-FL-04 — Contabilidad del presupuesto epsilon

**Tipo de política:** Obligación

El presupuesto epsilon debe controlarse por operación o sesión conforme al propósito, contrato y política activa y no puede superar el máximo autorizado para ese contexto. El valor aplicado y su regla de consumo deben ser auditables.

**Requisitos relacionados:** `RF-59`, `RNF-18`

**Mecanismos recomendados:** `M-FL-04`, `M-AUD-01`

**Consultas SPARQL asociadas:** `BASE-Q24`, `EXT-Q69`  

### P-FL-05 — Mecanismo de privacidad explícito

**Tipo de política:** Obligación

Toda sesión o flujo federado protegido debe enlazar explícitamente el mecanismo de privacidad, anonimización o pseudonimización realmente aplicado; no basta con que exista una referencia documental externa sin vínculo verificable.

**Requisitos relacionados:** `RF-58`, `RNF-19`

**Mecanismos recomendados:** `M-FL-03`, `M-ID-01`

**Consultas SPARQL asociadas:** `BASE-Q16`, `EXT-Q68`  

### P-FL-06 — Flujo descendente de modelos mejorados

**Tipo de política:** Prohibición

Los modelos mejorados distribuidos hacia capas inferiores no pueden incluir datos personales, observaciones crudas, gradientes individualizados ni identificadores persistentes derivados del usuario. El flujo debe respetar contrato, zona y políticas activas.

**Requisitos relacionados:** `RF-23`, `RF-38`, `RNF-17`

**Mecanismos recomendados:** `M-FL-02`, `M-CONS-02`, `M-ZONE-01`

**Consultas SPARQL asociadas:** `EXT-Q66`  

### P-FL-07 — Metadatos mínimos de sesión HFL

**Tipo de política:** Obligación

Toda sesión HFL debe registrar al menos tiempo de sesión, nodos involucrados, modelo actualizado, tipo de información intercambiada y mecanismos de privacidad cuando sean aplicables.

**Requisitos relacionados:** `RF-25`, `RNF-16`

**Mecanismos recomendados:** `M-FL-01`, `M-FL-02`, `M-AUD-01`

**Consultas SPARQL asociadas:** `BASE-Q16`, `BASE-Q24`, `EXT-Q66`  

### P-FL-08 — Versionado y rollback de modelos

**Tipo de política:** Obligación

Toda actualización de modelo debe producir una versión identificable y registrar su fecha de actualización. Debe conservarse la capacidad de rollback a una versión anterior ante degradación, error o incumplimiento de política.

**Requisitos relacionados:** `RF-24`, `RNF-38`, `RNF-39`

**Mecanismos recomendados:** `M-MODEL-05`, `M-VAL-04`

**Consultas SPARQL asociadas:** `BASE-Q04`, `BASE-Q22`, `EXT-Q57`, `EXT-Q58`  
---

## 9. Políticas de delegación temporal, MAPE-K y auditoría

### P-AUD-01 — Delegación como evento semántico

**Tipo de política:** Obligación

Toda delegación temporal debe materializarse como un evento explícito y no únicamente como una relación estática entre nodos.

**Requisitos relacionados:** `RF-62`

**Mecanismos recomendados:** `M-DELEG-01`

**Consultas SPARQL asociadas:** `BASE-Q14`, `EXT-Q63`  

### P-AUD-02 — Contenido temporal de la delegación

**Tipo de política:** Obligación

Toda delegación debe registrar origen, destino, causa, inicio de validez y condición de recuperación. Una expiración planificada debe almacenarse por separado; `validTo` solo se completa cuando la delegación se cierra efectivamente.

**Requisitos relacionados:** `RF-63`, `RNF-36`

**Mecanismos recomendados:** `M-DELEG-01`, `M-TIME-01`

**Consultas SPARQL asociadas:** `EXT-Q63`, `EXT-Q64`, `EXT-Q73`  

### P-AUD-03 — Cierre efectivo de delegaciones

**Tipo de política:** Obligación

La delegación debe cerrarse cuando se cumpla la condición de recuperación o se alcance su expiración planificada. En el cierre debe registrarse `validTo` con el instante efectivo y detenerse cualquier nueva acción basada en la delegación finalizada.

**Requisitos relacionados:** `RF-64`, `RNF-36`

**Mecanismos recomendados:** `M-DELEG-02`

**Consultas SPARQL asociadas:** `EXT-Q63`  

### P-AUD-04 — Límite de cascada de delegación

**Tipo de política:** Prohibición

No puede crearse una cadena de delegaciones cuya profundidad supere `D_delegation_max` o la condición de corte equivalente fijada en el perfil de aceptación/política activa.

**Requisitos relacionados:** `RNF-14`

**Mecanismos recomendados:** `M-DELEG-03`

**Consultas SPARQL asociadas:** `EXT-Q65`  

### P-AUD-05 — Coherencia síntoma–política–acción

**Tipo de política:** Obligación

Toda acción adaptativa relevante debe estar justificada por un síntoma o condición MAPE-K identificable y por una política aplicable coherente con dicho síntoma. Las incompatibilidades deben marcarse como incumplimiento o evaluación inválida.

**Requisitos relacionados:** `RF-65`, `RF-66`, `RF-67`

**Mecanismos recomendados:** `M-AUD-02`

**Consultas SPARQL asociadas:** `BASE-Q14`, `BASE-Q35`, `EXT-Q72`  

### P-AUD-06 — Ticket completo de EvaluationState

**Tipo de política:** Obligación

Cada `EvaluationState` relevante debe registrar como mínimo síntoma, políticas aplicadas, contrato, consentimiento efectivo, alternativas evaluadas, puntuaciones AHP, criterio externo de confianza, tier seleccionado, justificación, instante de decisión y referencia a la acción ejecutada.

**Requisitos relacionados:** `RF-51`, `RF-54`, `RF-66`, `RNF-28`, `RNF-29`

**Mecanismos recomendados:** `M-AUD-01`

**Consultas SPARQL asociadas:** `BASE-Q21`, `EXT-Q20`, `EXT-Q46`, `EXT-Q47`, `EXT-Q59`, `EXT-Q71`  

### P-AUD-07 — Reconstrucción causal y temporal de decisiones

**Tipo de política:** Obligación

La información persistida debe permitir reconstruir a posteriori la cadena usuario → contrato → consentimiento efectivo → propósito → zona → política → estado de nodo → alternativas/puntuaciones → confianza → tier → acción, identificando qué valores estaban vigentes en el instante de la decisión.

**Requisitos relacionados:** `RF-67`, `RNF-30`, `RNF-32`, `RNF-33`

**Mecanismos recomendados:** `M-AUD-03`, `M-TIME-01`

**Consultas SPARQL asociadas:** `BASE-Q35`, `EXT-Q70`  
---

## 10. Políticas operativas, escalabilidad y calidad de servicio

### P-OPS-01 — Perfil de aceptación versionado

**Tipo de política:** Obligación

Antes de una campaña de aceptación deben fijarse y versionarse los umbrales operativos exigidos por los RNF, incluyendo como mínimo latencia local, interrupción máxima de migración, tiempo de monitorización SPARQL, tiempo de decisión, consumo energético, concurrencia, incorporación de nodos, profundidad de delegación y tiempo de reselección.

**Requisitos relacionados:** `RNF-01`, `RNF-02`, `RNF-04`, `RNF-05`, `RNF-06`, `RNF-08`, `RNF-09`, `RNF-14`, `RNF-21`, `RNF-39`

**Mecanismos recomendados:** `M-OPS-01`, `M-VAL-04`

**Consultas SPARQL asociadas:** `EXT-Q65`, `EXT-Q76`  

### P-OPS-02 — Escalado horizontal compatible con Fog y Cloud

**Tipo de política:** Obligación

La política de escalabilidad debe permitir escalado horizontal en Cloud y, cuando exista infraestructura Fog que lo soporte, también en Fog. No debe asumirse que Cloud es el único tipo de nodo con capacidad de elasticidad.

**Requisitos relacionados:** `RNF-07`, `RF-17`

**Mecanismos recomendados:** `M-OPS-02`

**Consultas SPARQL asociadas:** `BASE-Q02`, `BASE-Q29`  

### P-OPS-03 — Incorporación dinámica de nodos

**Tipo de política:** Obligación

Un nuevo nodo Edge o Fog debe poder registrarse y pasar a la fase de evaluación sin detener el sistema completo y dentro del límite `T_node_join` fijado en el perfil de aceptación.

**Requisitos relacionados:** `RNF-09`, `RNF-10`

**Mecanismos recomendados:** `M-OPS-03`, `M-NODE-01`

**Consultas SPARQL asociadas:** `BASE-Q02`  

### P-OPS-04 — Continuidad de funciones críticas

**Tipo de política:** Obligación

Ante fallos parciales, las funciones críticas autorizadas para ejecución local deben continuar operativas y los datos/eventos pendientes deben conservar su integridad hasta sincronización o descarte autorizado.

**Requisitos relacionados:** `RNF-12`, `RNF-13`

**Mecanismos recomendados:** `M-ADAPT-02`, `M-BUFFER-01`

**Consultas SPARQL asociadas:** `BASE-Q08`†, `EXT-Q31`†, `EXT-Q32`†, `EXT-Q33`†, `EXT-Q34`†  

### P-OPS-05 — Instrumentación mínima reproducible

**Tipo de política:** Obligación

Los escenarios de evaluación deben registrar las métricas necesarias para medir latencia, consumo energético, calidad/precisión del modelo, calidad de sueño/estrés, coste de migración, carga, capacidad residual y confianza del nodo.

**Requisitos relacionados:** `RF-29`, `RF-30`, `RNF-27`

**Mecanismos recomendados:** `M-METRIC-01`, `M-TIME-01`

**Consultas SPARQL asociadas:** `BASE-Q07`, `BASE-Q09`, `BASE-Q33`, `EXT-Q54`  

### P-OPS-06 — Restauración y vaciado seguro de buffers

**Tipo de política:** Abstención

La recuperación de carga o conectividad no autoriza automáticamente restaurar el nivel máximo de procesamiento ni vaciar todos los buffers. La restauración y sincronización deben realizarse únicamente cuando las condiciones que las habilitan sigan siendo válidas para cada servicio o dato pendiente.

**Requisitos relacionados:** `RF-08`, `RF-15`, `RF-26`, `RNF-12`

**Mecanismos recomendados:** `M-TX-02`, `M-BUFFER-01`, `M-MODEL-04`

**Consultas SPARQL asociadas:** `BASE-Q10`†, `BASE-Q17`†, `EXT-Q31`†, `EXT-Q38`†, `EXT-Q46`†  
---

## 11. Políticas de interoperabilidad y extensibilidad semántica

### P-INT-01 — Uso de estándares semánticos abiertos

**Tipo de política:** Obligación

La representación semántica y su consulta deben basarse en estándares abiertos compatibles con RDF/OWL/Turtle y SPARQL 1.1. Cuando exista un vocabulario estándar aplicable, incluyendo SOSA/SSN, SAREF, FOAF o GeoSPARQL, debe reutilizarse o alinearse con él; cualquier duplicación conceptual debe justificarse documentalmente.

**Requisitos relacionados:** `RNF-24`, `RNF-25`, `RNF-26`

**Mecanismos recomendados:** `M-INT-01`, `M-VAL-01`

**Consultas SPARQL asociadas:** `BASE-Q05`  

### P-INT-02 — Extensibilidad sin ruptura del núcleo conceptual

**Tipo de política:** Prohibición

La incorporación de nuevos usuarios, nodos, sensores, modelos, políticas, contratos o tipos de wearable no puede exigir modificar las abstracciones conceptuales centrales ya utilizadas por los escenarios de referencia, salvo que se declare explícitamente un cambio incompatible de versión mayor.

**Requisitos relacionados:** `RNF-10`, `RNF-23`, `RNF-38`

**Mecanismos recomendados:** `M-INT-02`, `M-VAL-05`

**Consultas SPARQL asociadas:** `BASE-Q03`  
## 12. Políticas de validación, reproducibilidad y mantenibilidad

### P-VAL-01 — Endpoint y entorno de referencia

**Tipo de política:** Obligación

La ontología debe exponerse mediante SPARQL 1.1. Apache Jena Fuseki se utiliza como entorno de referencia para reproducibilidad; otros endpoints solo se consideran equivalentes si soportan las características utilizadas y superan la misma batería de validación.

**Requisitos relacionados:** `RF-69`, `RNF-24`, `RNF-26`, `RV-03`

**Mecanismos recomendados:** `M-VAL-01`

**Consultas SPARQL asociadas:** `EXT-Q01`  

### P-VAL-02 — Clasificación de consultas de auditoría

**Tipo de política:** Obligación

Toda consulta de validación deberá clasificarse explícitamente como inspección/reporte, advertencia o incumplimiento y documentar su criterio de interpretación antes de incorporarse a la línea base.

**Requisitos relacionados:** `RF-70`, `RF-71`, `RNF-31`, `RV-01`

**Mecanismos recomendados:** `M-VAL-02`

**Consultas SPARQL asociadas:** `EXT-Q01`†, `EXT-Q75`†, `EXT-Q77`†, `EXT-Q80`†  

### P-VAL-03 — Precondiciones para interpretar cero filas

**Tipo de política:** Prohibición

Un resultado de cero filas en una consulta de incumplimiento no puede considerarse evidencia de cumplimiento si antes no se ha comprobado carga correcta del dataset, versión esperada de ontología, cobertura mínima y ejecución correcta de la consulta.

**Requisitos relacionados:** `RF-71`, `RV-02`

**Mecanismos recomendados:** `M-VAL-03`

**Consultas SPARQL asociadas:** `EXT-Q75`, `EXT-Q76`, `EXT-Q77`  

### P-VAL-04 — Versionado inequívoco de artefactos

**Tipo de política:** Obligación

Toda campaña de validación debe registrar versiones inequívocas de ontología, políticas, consultas, escenarios, perfil de aceptación y dataset. Referencias genéricas sin identificar el artefacto concreto no son válidas para reproducibilidad.

**Requisitos relacionados:** `RF-68`, `RNF-39`, `RV-01`, `RV-03`

**Mecanismos recomendados:** `M-VAL-04`

**Consultas SPARQL asociadas:** `EXT-Q01`, `EXT-Q77`  

### P-VAL-05 — Compatibilidad de línea base y cambios mayores

**Tipo de política:** Prohibición

Una ampliación de ontología, políticas o consultas no puede romper silenciosamente escenarios o consultas declarados como línea base. Todo cambio incompatible debe implicar una nueva versión mayor y una actualización explícita de la trazabilidad.

**Requisitos relacionados:** `RNF-11`, `RNF-38`

**Mecanismos recomendados:** `M-VAL-04`, `M-VAL-05`

**Consultas SPARQL asociadas:** `EXT-Q01`†, `EXT-Q02`†, `EXT-Q05`†, `EXT-Q77`†, `EXT-Q80`†  

### P-VAL-06 — Trazabilidad individual de requisitos

**Tipo de política:** Obligación

La documentación final debe mantener una matriz individual que relacione cada RF, RNF y RV con las políticas aplicables, mecanismos responsables, soporte semántico o estándar, consultas/validaciones y criterio de aceptación.

**Requisitos relacionados:** `RV-04`, `RV-05`

**Mecanismos recomendados:** `M-VAL-05`

**Consultas SPARQL asociadas:** `EXT-Q02`, `EXT-Q04`, `EXT-Q08`, `EXT-Q09`  

### P-VAL-07 — Escenarios versionados y reproducibles

**Tipo de política:** Obligación

Los escenarios S1–S17 deben definirse en un artefacto o anexo versionado y ejecutarse contra la misma versión de dataset, políticas y consultas utilizada para la campaña de validación.

**Requisitos relacionados:** `RF-31`, `RF-72`, `RV-03`

**Mecanismos recomendados:** `M-VAL-04`, `M-VAL-06`

**Consultas SPARQL asociadas:** `BASE-Q11`, `EXT-Q05`, `EXT-Q77`  

### P-VAL-08 — Cobertura global de cumplimiento

**Tipo de política:** Obligación

La campaña de validación debe producir métricas de cobertura y cumplimiento global sobre las áreas mínimas exigidas: consentimiento y contratos, políticas y zonas, confianza, decisión multicriterio, privacidad diferencial, pseudonimización/anonimización, delegación temporal y auditoría. Las métricas deben identificar la versión concreta de los artefactos evaluados.

**Requisitos relacionados:** `RF-68`, `RV-05`, `RNF-39`

**Mecanismos recomendados:** `M-VAL-07`, `M-VAL-04`

**Consultas SPARQL asociadas:** `EXT-Q80`  
---

## 13. Análisis de compatibilidad y conflictos entre categorías de políticas

La compatibilidad entre políticas se modela utilizando una taxonomía adaptada de la literatura de **policy conflict/anomaly analysis** empleada en firewalls, control de acceso, sistemas distribuidos y cloud. En lugar de usar estados genéricos como *compatible*, *parcialmente compatible* o *depende*, se separan dos cuestiones distintas:

1. **Relación estructural/semántica entre políticas:** cómo se solapan sus ámbitos de aplicación y sus efectos.
2. **Estrategia de resolución:** qué debe hacer el sistema cuando dos políticas aplicables producen restricciones o decisiones distintas.

La clasificación se aplica de forma rigurosa a **pares de políticas concretas**. La matriz entre categorías de esta sección representa el patrón de interacción predominante esperado entre sus políticas; no sustituye el análisis policy-to-policy durante la validación.

### 13.1 Taxonomía de relaciones

| Código | Relación | Definición aplicada en este documento | Estado de compatibilidad | Tratamiento |
|---|---|---|---|---|
| **IND** | **Independent / Disjoint** | Las políticas no comparten simultáneamente sujeto, acción, recurso y contexto relevante, o regulan decisiones independientes. | **Compatible** | No requiere resolución de conflicto. |
| **CO** | **Consistent Overlap** | Las políticas se solapan y sus efectos son compatibles; ambas pueden cumplirse simultáneamente. | **Compatible** | Aplicar conjuntamente. |
| **SUB** | **Subsumption / Specialization** | El ámbito de una política está contenido en el de otra y la política más específica añade o endurece restricciones sin contradecir el objetivo normativo general. | **Compatible con jerarquía** | Aplicar la política más específica dentro de su ámbito y conservar la general fuera de él. |
| **RED** | **Redundancy** | Una política no añade efecto observable porque otra cubre el mismo ámbito con el mismo efecto. | **Compatible, pero anómala** | Consolidar o eliminar la redundancia salvo justificación explícita. |
| **DEP** | **Policy Dependency / Order Dependency** | La evaluación o ejecución de una política requiere previamente el resultado de otra; no existe conflicto por sí mismo. | **Compatible si se respeta el orden** | Imponer dependencia explícita y rechazar ejecuciones fuera de orden. |
| **GEN** | **Generalization / Exception Conflict** | Una política general y otra más específica se solapan con efectos distintos. La regla específica actúa como excepción o restricción de la general. | **Conflicto resoluble** | Resolver mediante especificidad y precedencia normativa. |
| **COR** | **Correlation / Partial Conflict** | Las políticas se solapan parcialmente y producen efectos distintos en la intersección, sin que una contenga completamente a la otra. | **Conflicto contextual** | Resolver solo para la intersección afectada; registrar la decisión. |
| **CON** | **Contradiction / Direct Conflict** | Dos políticas aplicables al mismo sujeto, acción, recurso y contexto exigen efectos incompatibles. | **Incompatible** | La acción no puede ejecutarse hasta aplicar una regla de resolución inequívoca. |
| **SHD** | **Shadowing / Override** | Una política de mayor prioridad hace inefectiva, total o parcialmente, una política de menor prioridad dentro del mismo ámbito. | **Conflicto resuelto por precedencia** | Aplicar la de mayor prioridad y registrar qué política quedó sobrescrita. |
| **IRR** | **Irrelevance** | Una política no puede activarse en ningún estado válido del sistema o no gobierna ningún recurso/acción alcanzable. | **No evaluable como compatibilidad** | Marcar como anomalía de mantenibilidad y revisar/eliminar. |

**Criterio de compatibilidad:** `IND`, `CO`, `SUB` y `DEP` son relaciones válidas de composición; `RED` e `IRR` son anomalías de calidad sin conflicto de efectos; `GEN` y `COR` requieren resolución contextual; `CON` es incompatibilidad directa; `SHD` indica que el conflicto existe pero queda resuelto mediante una precedencia explícita.

### 13.2 Estrategias de resolución adoptadas

La taxonomía anterior identifica el tipo de relación, pero no determina por sí sola qué efecto debe prevalecer. Este sistema adopta las siguientes estrategias de resolución:

| Estrategia | Uso en este sistema | Regla |
|---|---|---|
| **Deny-overrides / Most-restrictive** | Prohibiciones de consentimiento, tipo de dato, privacidad y zona. | Si una política aplicable prohíbe una acción que otra permitiría, prevalece la prohibición mientras permanezca activa. |
| **Most-specific-policy** | Excepciones o restricciones específicas de zona, propósito, contrato, dato o recurso. | Una política más específica prevalece en su ámbito si no vulnera una prohibición de nivel superior. |
| **Priority-ordered** | Gobernanza, versiones de políticas y reglas de precedencia. | Se evalúan las políticas según la jerarquía normativa definida por `P-GOV`; una prioridad inferior no puede sobrescribir una superior. |
| **Constraint-before-optimization** | Selección de nodo, tier, AHP, trust y optimización operativa. | Primero se construye el conjunto de alternativas permitidas; después se optimiza únicamente sobre dicho conjunto. |
| **Defer-and-reevaluate** | Fallos recuperables de batería, conectividad, carga o ventana de transmisión. | No se convierte una indisponibilidad temporal en permiso ni prohibición permanente; la acción se difiere y se reevalúa desde el inicio. |
| **Explicit conflict rejection** | Contradicciones no cubiertas por una regla de precedencia. | Una decisión `CON` sin resolución determinista invalida la evaluación y bloquea la acción afectada. |

No se utiliza **permit-overrides** como estrategia general: una autorización de rendimiento, disponibilidad o calidad nunca puede ampliar una autorización restringida por consentimiento, datos, privacidad o zona.

### 13.3 Matriz de relación predominante entre categorías

La matriz siguiente indica la relación **predominante esperada** entre categorías. Es simétrica porque describe la relación semántica entre dominios, no el orden de ejecución. Cuando aparece `GEN`, `COR` o `SHD`, la subsección 13.4 especifica la resolución normativa concreta.

Abreviaturas de categorías: `GOV` gobernanza; `CONS` consentimiento/contratos; `DATA` datos/privacidad/identidad; `ZONE` georrestricción; `NODE` nodos/trust; `MODEL` selección/AHP; `ADAPT` migración/offloading/degradación; `FL` aprendizaje federado/model lifecycle; `AUD` delegación/MAPE-K/auditoría; `OPS` operación/escalabilidad/QoS; `INT` interoperabilidad; `VAL` validación/reproducibilidad.

|  | GOV | CONS | DATA | ZONE | NODE | MODEL | ADAPT | FL | AUD | OPS | INT | VAL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **GOV** | — | DEP | DEP | DEP | DEP | DEP | DEP | DEP | DEP | DEP | DEP | DEP |
| **CONS** | DEP | — | DEP | GEN | DEP | SHD | SHD | GEN | CO | DEP | CO | CO |
| **DATA** | DEP | DEP | — | SUB | DEP | SHD | DEP | GEN | CO | DEP | CO | CO |
| **ZONE** | DEP | GEN | SUB | — | SUB | SHD | SHD | SHD | CO | SUB | CO | CO |
| **NODE** | DEP | DEP | DEP | SUB | — | DEP | DEP | DEP | CO | DEP | CO | CO |
| **MODEL** | DEP | SHD | SHD | SHD | DEP | — | DEP | DEP | CO | DEP | CO | CO |
| **ADAPT** | DEP | SHD | DEP | SHD | DEP | DEP | — | IND | CO | DEP | CO | CO |
| **FL** | DEP | GEN | GEN | SHD | DEP | DEP | IND | — | CO | DEP | CO | CO |
| **AUD** | DEP | CO | CO | CO | CO | CO | CO | CO | — | CO | CO | DEP |
| **OPS** | DEP | DEP | DEP | SUB | DEP | DEP | DEP | DEP | CO | — | CO | CO |
| **INT** | DEP | CO | CO | CO | CO | CO | CO | CO | CO | CO | — | CO |
| **VAL** | DEP | CO | CO | CO | CO | CO | CO | CO | DEP | CO | CO | — |

**Lectura importante:** `SHD` no significa que una categoría completa anule a otra. Significa que, cuando ambas políticas regulan la misma acción, la restricción de la categoría prioritaria puede **shadow/override** la alternativa concreta de la otra. Por ejemplo, una política de zona puede dejar inoperante la alternativa `CloudModelTier` sin invalidar la categoría `MODEL` completa.

### 13.4 Relaciones que requieren resolución explícita

Las relaciones `GEN`, `COR`, `CON` y `SHD` son las que deben producir evidencia de resolución durante la evaluación. En el conjunto actual de políticas se esperan principalmente los siguientes patrones:

| Categorías | Relación | Situación típica | Resolución normativa |
|---|---|---|---|
| **CONS × ZONE** | **GEN** | El contrato/rango permite procesamiento externo de forma general, pero la zona actual introduce una excepción más restrictiva. | **Most-specific + deny-overrides**: prevalece la restricción de zona dentro de ese perímetro. |
| **CONS × MODEL** | **SHD** | El optimizador considera Edge/Fog/Cloud, pero el rango efectivo no autoriza alguno de esos tiers. | La autorización hace *shadowing* de esas alternativas antes de ejecutar AHP. |
| **CONS × ADAPT** | **SHD** | Una migración/offloading técnicamente viable movería procesamiento fuera del rango autorizado. | La acción adaptativa queda sobrescrita/bloqueada; debe buscarse alternativa local autorizada. |
| **CONS × FL** | **GEN** | La regla general de participación FL se especializa según flujo ascendente/descendente y rango de consentimiento. | Aplicar la política específica del sentido del flujo; el uplink sensible requiere autorización explícita. |
| **DATA × ZONE** | **SUB** | Una zona añade reglas de retención o transferencia a las restricciones generales por tipo de dato. | Aplicar ambas; la regla de zona actúa como especialización consistente. |
| **DATA × MODEL** | **SHD** | Un tier remoto sería elegible por calidad, pero requeriría transmitir una observación cruda prohibida. | La prohibición del dato elimina el tier/flujo antes de la optimización. |
| **DATA × FL** | **GEN** | Las reglas generales de protección de datos se especializan para gradientes, parámetros y modelos descendentes. | Aplicar primero clasificación de datos y después la política FL específica; nunca reinterpretar dato crudo como gradiente transmisible. |
| **ZONE × MODEL** | **SHD** | Una política de zona restringida excluye tiers externos que MODEL podría puntuar favorablemente. | La zona elimina alternativas antes de AHP. |
| **ZONE × ADAPT** | **SHD** | Migración, offloading o delegación cruzarían un perímetro prohibido. | Bloquear el destino afectado; si no hay otro candidato, degradar/retener/diferir según políticas aplicables. |
| **ZONE × FL** | **SHD** | Una ruta FL autorizada funcionalmente atraviesa un perímetro que prohíbe el flujo. | La sesión/ruta queda bloqueada mientras persista la restricción geográfica. |
| **ADAPT × FL** | **IND** | Migrar un servicio y ejecutar FL pueden coincidir temporalmente, pero ninguna operación implica automáticamente la otra. | Autorizar, ejecutar y auditar ambas operaciones por separado. |

En el estado revisado del documento **no se espera ninguna relación `CON` permanente entre categorías completas**. Una contradicción directa entre políticas individuales debe considerarse una anomalía de configuración y no una forma normal de composición. Del mismo modo, no se espera `RED` entre categorías; si aparece, es señal de que una misma obligación o prohibición se ha duplicado en dominios distintos y debe consolidarse.

### 13.5 Clasificador formal para pares de políticas

Para determinar la compatibilidad de dos políticas concretas `p1` y `p2`, se recomienda compararlas sobre una representación normalizada con al menos:

```text
<subject, action, resource/data, location, purpose,
 time/context, preconditions, effect, priority, version>
```

El clasificador debe aplicar el siguiente orden lógico:

1. **Sin intersección de ámbito** → `IND`.
2. **Mismo ámbito y mismo efecto** → `RED` si una no añade restricciones/obligaciones nuevas; en caso contrario `CO`.
3. **Un ámbito contiene al otro y el efecto es compatible** → `SUB`.
4. **Un ámbito contiene al otro y el efecto difiere** → `GEN`; resolver por especificidad y precedencia.
5. **Intersección parcial con efectos distintos** → `COR`; resolver únicamente la región intersectada.
6. **Ámbito equivalente con efectos incompatibles** → `CON`; bloquear si no existe regla de resolución explícita.
7. **Una política prioritaria hace imposible que la otra produzca efecto en su ámbito** → marcar adicionalmente `SHD` para trazabilidad de precedencia.
8. **Una política necesita la salida/estado producido por la otra** → marcar `DEP`; puede coexistir con cualquiera de las relaciones anteriores si además hay solapamiento normativo.

`DEP` y `SHD` son propiedades relacionales adicionales: por ejemplo, dos políticas pueden mantener una relación `GEN` y, tras aplicar prioridad, quedar resueltas mediante `SHD` de la política general en el subámbito específico.

### 13.6 Orden de evaluación derivado de la resolución de conflictos

El orden de evaluación se conserva porque implementa las estrategias anteriores:

```text
GOV
 │
 ▼
CONS + DATA + ZONE
 │     (deny-overrides / most-specific)
 ▼
NODE + restricciones OPS
 │     (eligibility filtering)
 ▼
MODEL
 │     (constraint-before-optimization; AHP solo sobre candidatos válidos)
 ▼
ADAPT y/o FL
 │
 ▼
AUD
 │
 ▼
VAL

INT actúa transversalmente como soporte semántico e interoperable.
```

Reglas invariantes:

1. Una política de optimización no puede sobreescribir una prohibición de autorización, dato, privacidad o zona.
2. Una política más general no puede ampliar el efecto de una excepción más específica que sea válida y de mayor precedencia.
3. `NODE`, trust, AHP y QoS solo ordenan o seleccionan alternativas **ya elegibles**.
4. Una condición operacional temporal genera diferimiento y reevaluación, no una autorización implícita.
5. `AUD`, `INT` y `VAL` no conceden autorización de procesamiento; registran, soportan o verifican decisiones.
6. Toda resolución `GEN`, `COR`, `CON` o `SHD` debe quedar registrada con las políticas implicadas, el ámbito intersectado, la estrategia aplicada y el resultado.

### 13.7 Uso de la taxonomía en validación

La batería v3 implementa la validación de compatibilidad mediante consultas separadas; la compatibilidad no se reduce a una única consulta booleana. El análisis debe distinguir al menos:

- detección de **redundancy** (`RED`);
- detección de **generalization/exception** (`GEN`);
- detección de **correlation/partial conflict** (`COR`);
- detección de **direct contradiction** (`CON`);
- detección de **shadowing/override** (`SHD`);
- detección de políticas **irrelevant/unreachable** (`IRR`);
- verificación de dependencias y precedencia (`DEP`).

**Consultas SPARQL asociadas:** `EXT-Q07`, `EXT-Q78`, `EXT-Q79`  

### 13.8 Base terminológica académica no normativa

La terminología anterior está adaptada, no copiada literalmente, de líneas de trabajo habituales en análisis de políticas:

- análisis de anomalías de firewall: **shadowing, correlation, generalization, redundancy e irrelevance**;
- análisis de políticas de acceso y cloud: **conflict/contradiction, exception, correlation, redundancy y overlap**;
- composición de políticas de autorización: estrategias como **deny-overrides, permit-overrides y first-applicable**;
- gestión distribuida/cloud: resolución jerárquica de conflictos y propagación de políticas.

La semántica normativa válida para este proyecto es la definida en las políticas `P-GOV`, `P-CONS`, `P-DATA`, `P-ZONE`, etc.; los términos académicos se utilizan como **clasificación de relaciones y anomalías**, no como sustitución de las reglas del sistema.

---

## 14. Mecanismos de actuación revisados

Los mecanismos describen **cómo** se materializan las políticas. No son políticas adicionales y no deben utilizarse como sustituto de una regla de gobernanza.

### M-GOV-01 — Clasificador de tipo de política

Validar al crear o cargar una política que tenga exactamente un tipo formal y que dicho tipo sea uno de los permitidos.

**Políticas soportadas:** `P-GOV-01`

**Consultas útiles:** `EXT-Q03`, `EXT-Q06`, `EXT-Q10`  

### M-GOV-02 — Resolución de políticas aplicables

Resolver las políticas vinculadas a usuario, contrato, zona, nodo, servicio, sesión o evaluación y conservar su versión.

**Políticas soportadas:** `P-GOV-02`, `P-GOV-04`

**Consultas útiles:** `EXT-Q03`, `EXT-Q08`, `EXT-Q10`, `EXT-Q70`, `EXT-Q72`  

### M-GOV-03 — Motor de precedencia

Combinar las restricciones duras aplicables y obtener la intersección más restrictiva antes de calcular cualquier optimización.

**Políticas soportadas:** `P-GOV-03`, `P-CONS-04`

**Consultas útiles:** `BASE-Q15`, `BASE-Q25`, `BASE-Q28`, `EXT-Q07`, `EXT-Q11`, `EXT-Q16`, `EXT-Q17`, `EXT-Q18`, `EXT-Q19`, `EXT-Q20`, `EXT-Q37`, `EXT-Q39`, `EXT-Q56`, `EXT-Q78`, `EXT-Q79`  

### M-GOV-04 — Registro de versión de políticas

Persistir la versión del conjunto de políticas usada por cada evaluación y campaña de validación.

**Políticas soportadas:** `P-GOV-04`, `P-VAL-04`

**Consultas útiles:** `EXT-Q01`, `EXT-Q03`, `EXT-Q10`, `EXT-Q77`  

### M-CONS-01 — Resolución de consentimiento y contrato

Determinar consentimiento activo, contrato efectivo por propósito, vigencia, categorías de datos y rango autorizado.

**Políticas soportadas:** `P-CONS-01`, `P-CONS-02`, `P-CONS-03`

**Consultas útiles:** `BASE-Q01`, `BASE-Q15`, `BASE-Q20`, `BASE-Q31`, `EXT-Q11`, `EXT-Q12`, `EXT-Q13`, `EXT-Q14`, `EXT-Q15`, `EXT-Q16`  

### M-CONS-02 — Cálculo de autorización efectiva

Calcular la autorización efectiva como intersección de consentimiento activo, contrato, zona y demás restricciones duras.

**Políticas soportadas:** `P-CONS-04`, `P-CONS-06`, `P-DATA-05`, `P-ZONE-03`

**Consultas útiles:** `BASE-Q15`, `BASE-Q25`, `BASE-Q28`, `EXT-Q11`, `EXT-Q16`, `EXT-Q17`, `EXT-Q18`, `EXT-Q19`, `EXT-Q20`, `EXT-Q31`, `EXT-Q32`, `EXT-Q39`, `EXT-Q56`, `EXT-Q66`  

### M-CONS-03 — Comprobación del rango requerido

Comparar el rango mínimo requerido por recurso/acción con la autorización efectiva antes de habilitarlo.

**Políticas soportadas:** `P-CONS-05`

**Consultas útiles:** `BASE-Q06`, `EXT-Q21`  

### M-DATA-01 — Clasificación crudo/parametrizado

Clasificar el dato antes de cualquier transferencia y bloquear observaciones fisiológicas crudas fuera del ámbito local.

**Políticas soportadas:** `P-DATA-01`

**Consultas útiles:** `BASE-Q18`, `EXT-Q22`  

### M-DATA-02 — Etiquetado contextual

Adjuntar o relacionar el contexto operativo mínimo necesario para interpretar cada dato procesado.

**Políticas soportadas:** `P-DATA-04`, `P-DATA-10`

**Consultas útiles:** `BASE-Q10`, `BASE-Q28`, `EXT-Q23`, `EXT-Q24`, `EXT-Q25`  

### M-ID-01 — Pseudonimización/anonimización de salida

Sustituir identificadores personales directos por identificadores pseudónimos o anónimos antes de autorizar un flujo externo.

**Políticas soportadas:** `P-DATA-02`, `P-FL-03`, `P-FL-05`

**Consultas útiles:** `BASE-Q01`, `BASE-Q16`, `EXT-Q23`, `EXT-Q26`, `EXT-Q27`, `EXT-Q28`, `EXT-Q67`, `EXT-Q68`  

### M-SEC-01 — Protección criptográfica

Aplicar y verificar la línea base de cifrado en tránsito y en reposo para información sensible y buffers autorizados.

**Políticas soportadas:** `P-DATA-03`

**Consultas útiles:** `EXT-Q23`, `EXT-Q29`, `EXT-Q30`, `EXT-Q32`  

### M-DEVICE-01 — Monitorización de estado del dispositivo

Leer batería, conectividad, sensores y disponibilidad de datos para disparar reglas energéticas y de transmisión.

**Políticas soportadas:** `P-DATA-06`

**Consultas útiles:** `BASE-Q10`  

### M-TX-01 — Puerta de transmisión

Comprobar tipo de dato, preparación, identidad protegida, autorización, zona, destino y reglas de redundancia antes de cada envío.

**Políticas soportadas:** `P-DATA-01`, `P-DATA-02`, `P-DATA-04`, `P-DATA-08`

**Consultas útiles:** `BASE-Q01`, `BASE-Q10`, `BASE-Q18`, `BASE-Q28`, `EXT-Q22`, `EXT-Q23`, `EXT-Q26`, `EXT-Q27`, `EXT-Q28`, `EXT-Q33`, `EXT-Q34`  

### M-TX-02 — Gestor de reconexión y ventana segura

Mantener pendientes los flujos bloqueados y revalidar todas las condiciones antes de reanudarlos tras una reconexión.

**Políticas soportadas:** `P-DATA-07`, `P-OPS-06`

**Consultas útiles:** `BASE-Q10`, `BASE-Q17`, `EXT-Q31`, `EXT-Q38`, `EXT-Q46`  

### M-TX-03 — Planificador por criticidad

Ordenar datos pendientes por criticidad, restricciones y coste de transmisión sin permitir que datos secundarios desplacen a los críticos.

**Políticas soportadas:** `P-DATA-09`

**Consultas útiles:** `EXT-Q35`  

### M-BUFFER-01 — Retención autorizada

Seleccionar la capa de almacenamiento temporal más alta permitida y mantener integridad hasta sincronización o descarte autorizado.

**Políticas soportadas:** `P-DATA-05`, `P-ZONE-02`, `P-OPS-04`

**Consultas útiles:** `BASE-Q08`, `BASE-Q17`, `EXT-Q31`, `EXT-Q32`, `EXT-Q33`, `EXT-Q34`, `EXT-Q38`  

### M-REPL-01 — Replicación controlada e idempotente

Identificar réplicas intencionadas, versionarlas, detectar duplicados accidentales y hacer idempotentes las reejecuciones de sincronización.

**Políticas soportadas:** `P-DATA-08`, `P-ADAPT-08`

**Consultas útiles:** `BASE-Q10`, `EXT-Q33`, `EXT-Q34`  

### M-ZONE-01 — Puerta de zona

Resolver la zona vigente y aplicar sus restricciones antes de autorizar almacenamiento, procesamiento o transferencia externa.

**Políticas soportadas:** `P-ZONE-01`, `P-ZONE-02`, `P-ZONE-03`

**Consultas útiles:** `BASE-Q17`, `BASE-Q18`, `BASE-Q34`, `EXT-Q22`, `EXT-Q36`, `EXT-Q37`, `EXT-Q38`, `EXT-Q39`, `EXT-Q56`  

### M-CTX-01 — Detección de cambios de contexto

Detectar movilidad, cambio de zona, conectividad, carga, batería y otras variaciones capaces de invalidar una decisión.

**Políticas soportadas:** `P-ZONE-04`, `P-MODEL-09`

**Consultas útiles:** `BASE-Q09`, `BASE-Q21`, `BASE-Q23`, `EXT-Q46`, `EXT-Q59`, `EXT-Q76`  

### M-NODE-01 — Monitorización de NodeState

Leer disponibilidad, carga, comunicación, capacidad residual, cola, estado operativo y trust de los nodos.

**Políticas soportadas:** `P-NODE-01`, `P-OPS-03`

**Consultas útiles:** `BASE-Q02`, `BASE-Q07`, `BASE-Q08`, `BASE-Q26`, `EXT-Q41`  

### M-NODE-02 — Filtro de elegibilidad de nodos

Excluir candidatos que incumplan estado operativo, capacidad, conectividad, autorización, zona o mínimos de confianza aplicables.

**Políticas soportadas:** `P-NODE-01`, `P-NODE-02`, `P-NODE-06`

**Consultas útiles:** `BASE-Q07`, `BASE-Q08`, `BASE-Q12`, `BASE-Q19`, `BASE-Q23`, `BASE-Q26`, `EXT-Q41`, `EXT-Q42`, `EXT-Q45`, `EXT-Q56`  

### M-TRUST-01 — Cálculo y actualización de confianza

Actualizar el trust score a partir de la ventana histórica y regla versionada, conservando evidencias de los factores utilizados.

**Políticas soportadas:** `P-NODE-03`, `P-NODE-04`

**Consultas útiles:** `BASE-Q07`, `EXT-Q40`, `EXT-Q43`  

### M-TRUST-02 — Ordenación externa por confianza

Aplicar trust únicamente sobre candidatos elegibles y fuera de la normalización AHP.

**Políticas soportadas:** `P-NODE-05`, `P-MODEL-03`, `P-ADAPT-07`

**Consultas útiles:** `BASE-Q19`, `EXT-Q42`, `EXT-Q44`, `EXT-Q45`, `EXT-Q48`  

### M-MODEL-01 — Evaluación de alternativas de tier

Calcular la puntuación de cada alternativa elegible y seleccionar la mejor según la política activa.

**Políticas soportadas:** `P-MODEL-01`, `P-MODEL-05`, `P-MODEL-06`, `P-MODEL-07`

**Consultas útiles:** `BASE-Q04`, `BASE-Q15`, `BASE-Q21`, `BASE-Q32`, `EXT-Q46`, `EXT-Q51`, `EXT-Q52`, `EXT-Q53`, `EXT-Q56`  

### M-MODEL-02 — Normalización AHP

Validar que los pesos de latencia, privacidad y calidad estén normalizados y que trust no se mezcle en ellos.

**Políticas soportadas:** `P-MODEL-02`, `P-MODEL-03`

**Consultas útiles:** `EXT-Q42`, `EXT-Q44`, `EXT-Q48`  

### M-MODEL-03 — Consistencia AHP

Calcular y registrar la métrica/ratio de consistencia y compararla con el umbral configurado; si el método no es AHP, etiquetarlo correctamente.

**Políticas soportadas:** `P-MODEL-04`

**Consultas útiles:** `EXT-Q49`, `EXT-Q50`  

### M-MODEL-04 — Reselección adaptativa

Invalidar y recalcular la selección cuando cambien las condiciones que hacían válida la decisión anterior.

**Políticas soportadas:** `P-MODEL-09`, `P-ZONE-04`, `P-OPS-06`

**Consultas útiles:** `BASE-Q09`, `BASE-Q10`, `BASE-Q17`, `BASE-Q21`, `BASE-Q23`, `EXT-Q31`, `EXT-Q38`, `EXT-Q46`, `EXT-Q59`, `EXT-Q76`  

### M-MODEL-05 — Versionado y rollback

Crear versiones de modelo identificables, registrar actualización y permitir volver a una versión válida anterior.

**Políticas soportadas:** `P-FL-08`

**Consultas útiles:** `BASE-Q04`, `BASE-Q22`, `EXT-Q57`, `EXT-Q58`  

### M-METRIC-01 — Instrumentación de métricas

Registrar métricas de modelo, sistema y usuario con referencias temporales/contextuales comunes.

**Políticas soportadas:** `P-MODEL-08`, `P-OPS-05`

**Consultas útiles:** `BASE-Q07`, `BASE-Q09`, `BASE-Q33`, `EXT-Q54`, `EXT-Q55`  

### M-ADAPT-01 — Evaluador de migración/offloading

Comparar continuidad, coste, latencia, energía y destinos elegibles antes de activar migración u offloading.

**Políticas soportadas:** `P-ADAPT-01`, `P-ADAPT-03`, `P-ADAPT-04`

**Consultas útiles:** `BASE-Q12`, `EXT-Q45`, `EXT-Q62`  

### M-ADAPT-02 — Gestor de degradación

Reducir procesamiento de forma controlada, registrar causa y conservar funciones críticas locales cuando no exista una alternativa externa válida.

**Políticas soportadas:** `P-DATA-06`, `P-ADAPT-02`, `P-ADAPT-03`, `P-ADAPT-06`

**Consultas útiles:** `BASE-Q10`, `BASE-Q13`, `BASE-Q14`, `BASE-Q22`, `BASE-Q27`, `EXT-Q59`, `EXT-Q62`  

### M-ADAPT-03 — Ejecutor de migración

Ejecutar la migración como una acción independiente de delegación y de aprendizaje federado, conservando referencia a la evaluación que la autorizó.

**Políticas soportadas:** `P-ADAPT-05`

**Consultas útiles:** `BASE-Q13`, `EXT-Q60`, `EXT-Q61`  

### M-FL-01 — Gestor de sesión federada ascendente

Crear una sesión federada únicamente tras validar participantes, autorización, zona, privacidad y tipo de actualización.

**Políticas soportadas:** `P-FL-01`, `P-FL-02`, `P-FL-07`

**Consultas útiles:** `BASE-Q16`, `BASE-Q24`, `BASE-Q25`, `BASE-Q30`, `EXT-Q66`, `EXT-Q67`  

### M-FL-02 — Gestor de distribución descendente

Distribuir modelos genéricos mejorados verificando que no contienen información individualizada y que el flujo cumple las políticas activas.

**Políticas soportadas:** `P-CONS-06`, `P-FL-06`

**Consultas útiles:** `BASE-Q15`, `EXT-Q66`  

### M-FL-03 — Aplicación de privacidad diferencial

Aplicar ruido y registrar presupuesto, nivel de ruido y mecanismo de privacidad antes de liberar gradientes protegidos.

**Políticas soportadas:** `P-FL-03`, `P-FL-05`, `P-MODEL-07`

**Consultas útiles:** `BASE-Q16`, `EXT-Q56`, `EXT-Q67`, `EXT-Q68`  

### M-FL-04 — Contabilidad epsilon

Acumular y validar el consumo del presupuesto epsilon por propósito, contrato, sesión y política.

**Políticas soportadas:** `P-FL-04`

**Consultas útiles:** `BASE-Q24`, `EXT-Q69`  

### M-DELEG-01 — Creación de DelegationEvent

Crear el evento de delegación con origen, destino, causa, validFrom, recuperación y expiración planificada cuando exista, dejando validTo vacío mientras esté activo.

**Políticas soportadas:** `P-ADAPT-07`, `P-AUD-01`, `P-AUD-02`

**Consultas útiles:** `BASE-Q14`, `EXT-Q45`, `EXT-Q63`, `EXT-Q64`, `EXT-Q73`  

### M-DELEG-02 — Cierre de delegación

Cerrar la delegación al cumplirse recuperación o expiración y registrar validTo como cierre efectivo.

**Políticas soportadas:** `P-AUD-03`, `P-ADAPT-08`

**Consultas útiles:** `BASE-Q10`, `EXT-Q33`, `EXT-Q34`, `EXT-Q63`  

### M-DELEG-03 — Control de profundidad

Comprobar la profundidad acumulada de la cadena antes de crear una nueva delegación.

**Políticas soportadas:** `P-AUD-04`

**Consultas útiles:** `EXT-Q65`  

### M-AUD-01 — Ticket semántico de evaluación

Persistir en EvaluationState las entradas, alternativas, puntuaciones, confianza, políticas, decisión, tiempo y acción ejecutada.

**Políticas soportadas:** `P-GOV-02`, `P-MODEL-05`, `P-MODEL-08`, `P-ADAPT-04`, `P-ADAPT-06`, `P-FL-04`, `P-AUD-06`

**Consultas útiles:** `BASE-Q13`, `BASE-Q21`, `BASE-Q22`, `BASE-Q24`, `BASE-Q27`, `EXT-Q08`, `EXT-Q20`, `EXT-Q45`, `EXT-Q46`, `EXT-Q47`, `EXT-Q51`, `EXT-Q52`, `EXT-Q53`, `EXT-Q54`, `EXT-Q55`, `EXT-Q59`, `EXT-Q62`, `EXT-Q69`, `EXT-Q70`, `EXT-Q71`, `EXT-Q72`  

### M-AUD-02 — Validador síntoma–política–acción

Comprobar que la política y la acción elegidas sean coherentes con el síntoma o condición detectada.

**Políticas soportadas:** `P-AUD-05`

**Consultas útiles:** `BASE-Q14`, `BASE-Q35`, `EXT-Q72`  

### M-AUD-03 — Reconstrucción de cadena de decisión

Recorrer relaciones causales y temporales desde usuario/contrato hasta la acción final utilizando los valores vigentes en el instante evaluado.

**Políticas soportadas:** `P-AUD-07`

**Consultas útiles:** `BASE-Q35`, `EXT-Q70`  

### M-TIME-01 — Gestión temporal de estados y contratos

Registrar validFrom; completar validTo únicamente al cierre efectivo y mantener separada cualquier expiración planificada.

**Políticas soportadas:** `P-CONS-02`, `P-DATA-10`, `P-AUD-02`, `P-AUD-07`

**Consultas útiles:** `BASE-Q20`, `BASE-Q35`, `EXT-Q12`, `EXT-Q14`, `EXT-Q15`, `EXT-Q23`, `EXT-Q24`, `EXT-Q25`, `EXT-Q63`, `EXT-Q64`, `EXT-Q70`, `EXT-Q73`  

### M-OPS-01 — Gestor de perfil de aceptación

Cargar y congelar los umbrales configurables de una campaña de aceptación junto con su versión.

**Políticas soportadas:** `P-OPS-01`

**Consultas útiles:** `EXT-Q65`, `EXT-Q76`  

### M-OPS-02 — Gestor de elasticidad y carga

Aplicar escalado horizontal donde exista capacidad compatible y registrar degradación/migración cuando el escalado no sea posible o no esté autorizado.

**Políticas soportadas:** `P-OPS-02`, `P-ADAPT-03`

**Consultas útiles:** `BASE-Q02`, `BASE-Q29`, `EXT-Q62`  

### M-OPS-03 — Registro dinámico de nodos

Incorporar un nodo nuevo, validar sus capacidades y hacerlo elegible sin detener el sistema completo.

**Políticas soportadas:** `P-OPS-03`

**Consultas útiles:** `BASE-Q02`  

### M-INT-01 — Verificador de interoperabilidad semántica

Comprobar que los artefactos utilizan los estándares declarados y registrar las alineaciones o justificaciones de conceptos propios frente a vocabularios existentes.

**Políticas soportadas:** `P-INT-01`

**Consultas útiles:** `BASE-Q05`  

### M-INT-02 — Validador de extensibilidad

Comprobar que la incorporación de nuevas instancias o especializaciones no altera las abstracciones centrales ni rompe los escenarios de referencia salvo cambio mayor explícito.

**Políticas soportadas:** `P-INT-02`

**Consultas útiles:** `BASE-Q03`  

### M-VAL-01 — Entorno de validación SPARQL

Cargar el dataset y ejecutar la batería sobre Fuseki como referencia, permitiendo comparar endpoints equivalentes.

**Políticas soportadas:** `P-VAL-01`

**Consultas útiles:** `EXT-Q01`  

### M-VAL-02 — Catálogo de consultas

Registrar para cada consulta su tipo, finalidad, precondiciones y criterio de interpretación.

**Políticas soportadas:** `P-VAL-02`

**Consultas útiles:** `EXT-Q01`, `EXT-Q75`, `EXT-Q77`, `EXT-Q80`  

### M-VAL-03 — Validador de precondiciones

Comprobar dataset, versión, cobertura y ejecución correcta antes de interpretar una consulta de incumplimiento vacía.

**Políticas soportadas:** `P-VAL-03`

**Consultas útiles:** `EXT-Q75`, `EXT-Q76`, `EXT-Q77`  

### M-VAL-04 — Registro de versiones de artefactos

Persistir identificadores inequívocos de ontología, políticas, consultas, escenarios, dataset y perfil de aceptación utilizados.

**Políticas soportadas:** `P-GOV-04`, `P-VAL-04`, `P-VAL-05`, `P-VAL-07`

**Consultas útiles:** `BASE-Q11`, `EXT-Q01`, `EXT-Q02`, `EXT-Q03`, `EXT-Q05`, `EXT-Q10`, `EXT-Q77`, `EXT-Q80`  

### M-VAL-05 — Matriz de trazabilidad

Mantener la relación individual entre requisitos, políticas, mecanismos, soporte semántico, consultas y criterios de aceptación.

**Políticas soportadas:** `P-VAL-05`, `P-VAL-06`

**Consultas útiles:** `EXT-Q01`, `EXT-Q02`, `EXT-Q04`, `EXT-Q05`, `EXT-Q08`, `EXT-Q09`, `EXT-Q77`, `EXT-Q80`  

### M-VAL-06 — Ejecutor de escenarios

Cargar y ejecutar el conjunto versionado de escenarios S1–S17 con los artefactos de la campaña seleccionada.

**Políticas soportadas:** `P-VAL-07`

**Consultas útiles:** `BASE-Q11`, `EXT-Q05`, `EXT-Q77`  

### M-VAL-07 — Agregador de métricas de cumplimiento

Calcular cobertura por dominio, contar incumplimientos/advertencias y vincular cada resultado con las versiones de artefactos utilizadas en la campaña.

**Políticas soportadas:** `P-VAL-08`

**Consultas útiles:** `EXT-Q80`  
---

## 15. Escenarios operativos y científicos a documentar

Los escenarios se conservan como conjunto S1–S17 porque los requisitos revisados exigen un artefacto versionado que los defina. La columna SPARQL se ha completado con las consultas principales de la batería v3 que permiten inspeccionar o validar cada escenario.

| ID | Nombre | Políticas principales | Mecanismos principales | Consultas SPARQL |
|---|---|---|---|---|
| S1 | Estado normal equilibrado | `P-GOV-03, P-NODE-02, P-MODEL-01, P-MODEL-05` | `M-GOV-03, M-NODE-02, M-MODEL-01, M-AUD-01` | `BASE-Q11`, `BASE-Q21`, `EXT-Q46`, `EXT-Q51` |
| S2 | Saturación urbana por evento masivo | `P-ZONE-03, P-ADAPT-01, P-ADAPT-03, P-OPS-02` | `M-ZONE-01, M-ADAPT-01, M-ADAPT-02, M-OPS-02` | `BASE-Q12`, `BASE-Q19`, `EXT-Q41`, `EXT-Q42`, `EXT-Q62` |
| S3 | Migración Edge → Fog | `P-ADAPT-01, P-ADAPT-04, P-ADAPT-05, P-ADAPT-06` | `M-ADAPT-01, M-ADAPT-03, M-AUD-01` | `BASE-Q13`, `EXT-Q59`, `EXT-Q60`, `EXT-Q61` |
| S4 | Fallo de comunicación y degradación | `P-DATA-07, P-ADAPT-02, P-NODE-01, P-OPS-04` | `M-TX-02, M-ADAPT-02, M-NODE-01` | `BASE-Q14`, `BASE-Q35`, `EXT-Q62`, `EXT-Q63`, `EXT-Q72` |
| S5 | Usuario con consentimiento denegado o solo local | `P-CONS-01, P-CONS-04, P-DATA-01, P-CONS-06` | `M-CONS-01, M-CONS-02, M-DATA-01, M-FL-02` | `BASE-Q15`, `EXT-Q11`, `EXT-Q17`, `EXT-Q19`, `EXT-Q22` |
| S6 | Sesión HFL global autorizada | `P-FL-01, P-FL-02, P-FL-03, P-FL-04, P-FL-07` | `M-FL-01, M-FL-03, M-FL-04, M-AUD-01` | `BASE-Q16`, `BASE-Q24`, `EXT-Q66`, `EXT-Q67`, `EXT-Q68`, `EXT-Q69` |
| S7 | Zona rural con retención local | `P-ZONE-02, P-DATA-05, P-DATA-07` | `M-ZONE-01, M-BUFFER-01, M-TX-02` | `BASE-Q17`, `EXT-Q31`, `EXT-Q38` |
| S8 | Zona restringida | `P-ZONE-01, P-GOV-03, P-DATA-01` | `M-ZONE-01, M-GOV-03, M-DATA-01` | `BASE-Q18`, `BASE-Q34`, `EXT-Q36`, `EXT-Q37` |
| S9 | Escalabilidad bajo crecimiento | `P-OPS-01, P-OPS-02, P-OPS-03, P-OPS-05` | `M-OPS-01, M-OPS-02, M-OPS-03, M-METRIC-01` | `BASE-Q02`, `BASE-Q07`, `BASE-Q29`, `BASE-Q33`, `EXT-Q76` |
| S10 | Propagación descendente de modelo | `P-CONS-06, P-FL-06, P-FL-08` | `M-FL-02, M-MODEL-05` | `BASE-Q04`, `BASE-Q16`, `EXT-Q57`, `EXT-Q58`, `EXT-Q66` |
| S11 | Contrato semántico consent-aware | `P-CONS-01, P-CONS-02, P-CONS-03, P-CONS-04, P-CONS-05` | `M-CONS-01, M-CONS-02, M-CONS-03` | `BASE-Q20`, `EXT-Q11`, `EXT-Q12`, `EXT-Q14`, `EXT-Q15`, `EXT-Q17`, `EXT-Q19`, `EXT-Q21` |
| S12 | Selección limitada por autorización efectiva | `P-GOV-03, P-CONS-04, P-NODE-02, P-MODEL-01` | `M-GOV-03, M-CONS-02, M-NODE-02, M-MODEL-01` | `BASE-Q21`, `BASE-Q25`, `EXT-Q17`, `EXT-Q19`, `EXT-Q20`, `EXT-Q42`, `EXT-Q46`, `EXT-Q56` |
| S13 | Delegación trust-based | `P-NODE-03, P-NODE-05, P-ADAPT-07, P-AUD-01, P-AUD-04` | `M-TRUST-01, M-TRUST-02, M-DELEG-01, M-DELEG-03` | `BASE-Q19`, `EXT-Q40`, `EXT-Q42`, `EXT-Q43`, `EXT-Q45`, `EXT-Q63`, `EXT-Q65` |
| S14 | Decisión AHP explicable | `P-MODEL-02, P-MODEL-03, P-MODEL-04, P-MODEL-05` | `M-MODEL-01, M-MODEL-02, M-MODEL-03, M-AUD-01` | `BASE-Q21`, `EXT-Q46`, `EXT-Q48`, `EXT-Q49`, `EXT-Q50`, `EXT-Q51`, `EXT-Q53` |
| S15 | Privacidad diferencial en gradientes FL | `P-FL-03, P-FL-04, P-FL-05, P-DATA-02` | `M-FL-03, M-FL-04, M-ID-01` | `BASE-Q24`, `EXT-Q23`, `EXT-Q26`, `EXT-Q27`, `EXT-Q29`, `EXT-Q30`, `EXT-Q66`, `EXT-Q68`, `EXT-Q69` |
| S16 | Gobernanza por obligación, abstención y prohibición | `P-GOV-01, P-GOV-02, P-GOV-03, P-GOV-04` | `M-GOV-01, M-GOV-02, M-GOV-03, M-GOV-04` | `EXT-Q03`, `EXT-Q06`, `EXT-Q07`, `EXT-Q10`, `EXT-Q78`, `EXT-Q79` |
| S17 | Auditoría semántica completa | `P-AUD-05, P-AUD-06, P-AUD-07, P-VAL-04` | `M-AUD-01, M-AUD-02, M-AUD-03, M-VAL-04` | `BASE-Q35`, `EXT-Q46`, `EXT-Q59`, `EXT-Q70`, `EXT-Q71`, `EXT-Q72`, `EXT-Q73`, `EXT-Q77`, `EXT-Q80` |

---

## 16. Principales correcciones respecto al documento anterior

- Se elimina la dependencia del consentimiento binario como regla principal y se adopta autorización efectiva por rangos, contrato y zona.
- Edge deja de considerarse parte del ámbito local para observaciones fisiológicas crudas.
- La selección de modelo deja de seguir la regla “usar siempre el tier más alto”; se selecciona la mejor alternativa elegible.
- Trust se separa explícitamente de los pesos AHP.
- Se exige normalización y consistencia para poder denominar AHP al mecanismo de decisión.
- Migración, delegación y aprendizaje federado se separan conceptualmente; una migración no crea por sí sola una sesión FL.
- `validTo` pasa a representar cierre efectivo y la expiración planificada se modela por separado.
- La política de zona restringida se alinea con el ámbito local y bloquea procesamiento externo en Edge, Fog y Cloud.
- Se distingue duplicado accidental de réplica controlada y se exige versionado e idempotencia.
- Se añaden políticas que faltaban para cifrado, rollback de modelos, ciclo temporal de estados, interoperabilidad semántica, límites de cascada de delegación, perfil de aceptación, versionado de artefactos, cobertura global y precondiciones de validación.
- Se elimina la afirmación de que solo Cloud puede escalar: Fog puede escalar cuando la infraestructura lo soporte.
- Se completan las referencias a consultas SPARQL de las 79 políticas, las consultas útiles de los 55 mecanismos y la trazabilidad SPARQL de S1–S17 usando la batería v3.0.0. Las asociaciones marcadas con `†` son coberturas indirectas a través de requisitos relacionados y se mantienen explícitamente diferenciadas de las asociaciones nominales del catálogo de consultas.

---

## 17. Matriz completa de trazabilidad de políticas

La matriz siguiente consolida la relación **política → requisitos → mecanismos → consultas**. La cobertura **Directa** significa que al menos una consulta de la batería v3 identifica nominalmente la política en su metadato `Políticas relacionadas`. La cobertura **Indirecta (`†`)** se utiliza únicamente cuando no existe ese enlace nominal pero sí existe cobertura verificable a través de los requisitos relacionados de la política.

| Política | Categoría | Tipo | Requisitos relacionados | Mecanismos | Consultas SPARQL | Cobertura |
|---|---|---|---|---|---|---|
| `P-GOV-01` | Gobernanza | Obligación | `RF-39`, `RF-40` | `M-GOV-01` | `EXT-Q03`, `EXT-Q06`, `EXT-Q10` | Directa |
| `P-GOV-02` | Gobernanza | Obligación | `RF-41`, `RF-44`, `RNF-28`, `RNF-30` | `M-GOV-02`, `M-AUD-01` | `EXT-Q08`†, `EXT-Q70`†, `EXT-Q72`† | Indirecta (`†`) |
| `P-GOV-03` | Gobernanza | Prohibición | `RF-35`, `RF-42`, `RF-43`, `RNF-22` | `M-GOV-03`, `M-CONS-02`, `M-ZONE-01` | `EXT-Q07`, `EXT-Q17`, `EXT-Q19`, `EXT-Q37`, `EXT-Q78`, `EXT-Q79` | Directa |
| `P-GOV-04` | Gobernanza | Obligación | `RNF-20`, `RNF-22`, `RNF-38`, `RNF-39`, `RV-04` | `M-GOV-04`, `M-VAL-04` | `EXT-Q03`, `EXT-Q10` | Directa |
| `P-GOV-05` | Gobernanza | Obligación | `RNF-35`, `RNF-36`, `RNF-37` | `M-TIME-01` | `BASE-Q09`, `EXT-Q73`, `EXT-Q74` | Directa |
| `P-CONS-01` | Consentimiento | Obligación | `RF-32` | `M-CONS-01` | `BASE-Q01`, `BASE-Q15`, `BASE-Q31`, `EXT-Q11`, `EXT-Q13`, `EXT-Q16` | Directa |
| `P-CONS-02` | Consentimiento | Prohibición | `RF-33`, `RNF-36` | `M-CONS-01`, `M-TIME-01` | `BASE-Q20`, `EXT-Q12`, `EXT-Q14`, `EXT-Q15` | Directa |
| `P-CONS-03` | Consentimiento | Obligación | `RF-34`, `RF-41` | `M-CONS-01`, `M-GOV-02` | `BASE-Q20`, `EXT-Q12`, `EXT-Q14` | Directa |
| `P-CONS-04` | Consentimiento | Prohibición | `RF-35`, `RF-36`, `RNF-22` | `M-CONS-02`, `M-GOV-03` | `BASE-Q15`, `BASE-Q25`, `BASE-Q28`, `EXT-Q11`, `EXT-Q16`, `EXT-Q17`, `EXT-Q18`, `EXT-Q19`, `EXT-Q20`, `EXT-Q39`, `EXT-Q56` | Directa |
| `P-CONS-05` | Consentimiento | Obligación | `RF-37` | `M-CONS-03` | `BASE-Q06`, `EXT-Q21` | Directa |
| `P-CONS-06` | Consentimiento | Abstención | `RF-23`, `RF-38` | `M-FL-02`, `M-CONS-02` | `BASE-Q15`†, `EXT-Q66`† | Indirecta (`†`) |
| `P-DATA-01` | Datos/privacidad | Prohibición | `RF-10`, `RF-60`, `RNF-17` | `M-DATA-01`, `M-TX-01` | `BASE-Q18`, `EXT-Q22` | Directa |
| `P-DATA-02` | Datos/privacidad | Prohibición | `RF-61`, `RNF-17`, `RNF-19` | `M-ID-01`, `M-TX-01` | `BASE-Q01`, `EXT-Q23`, `EXT-Q26`, `EXT-Q27`, `EXT-Q28` | Directa |
| `P-DATA-03` | Datos/privacidad | Obligación | `RNF-15`, `RNF-39` | `M-SEC-01`, `M-VAL-04` | `EXT-Q23`, `EXT-Q29`, `EXT-Q30`, `EXT-Q32` | Directa |
| `P-DATA-04` | Datos/privacidad | Abstención | `RF-04`, `RF-09`, `RF-27` | `M-TX-01`, `M-DATA-02` | `BASE-Q10`, `BASE-Q28` | Directa |
| `P-DATA-05` | Datos/privacidad | Obligación | `RF-08`, `RF-26`, `RNF-12` | `M-BUFFER-01`, `M-CONS-02`, `M-ZONE-01` | `EXT-Q31`, `EXT-Q32` | Directa |
| `P-DATA-06` | Datos/privacidad | Obligación | `RF-07`, `RF-27`, `RNF-06` | `M-DEVICE-01`, `M-ADAPT-02`, `M-BUFFER-01` | `BASE-Q10` | Directa |
| `P-DATA-07` | Datos/privacidad | Abstención | `RF-26`, `RF-27`, `RNF-12`, `RNF-13` | `M-TX-02`, `M-NODE-02`, `M-CONS-02` | `BASE-Q10`, `BASE-Q17`, `EXT-Q31`, `EXT-Q38` | Directa |
| `P-DATA-08` | Datos/privacidad | Prohibición | `RF-19`, `RF-28`, `RNF-13` | `M-REPL-01`, `M-TX-01` | `EXT-Q33`, `EXT-Q34` | Directa |
| `P-DATA-09` | Datos/privacidad | Obligación | `RF-27`, `RF-28` | `M-TX-03`, `M-BUFFER-01` | `EXT-Q35` | Directa |
| `P-DATA-10` | Datos/privacidad | Obligación | `RF-09`, `RF-30`, `RNF-27` | `M-DATA-02`, `M-TIME-01` | `EXT-Q23`, `EXT-Q24`, `EXT-Q25` | Directa |
| `P-ZONE-01` | Zona | Prohibición | `RF-42`, `RF-43`, `RF-53`, `RNF-22` | `M-ZONE-01`, `M-CONS-02` | `BASE-Q18`, `BASE-Q34`, `EXT-Q22`, `EXT-Q36`, `EXT-Q37`, `EXT-Q56` | Directa |
| `P-ZONE-02` | Zona | Obligación | `RF-08`, `RF-26`, `RF-42` | `M-ZONE-01`, `M-BUFFER-01`, `M-TX-02` | `BASE-Q17`, `EXT-Q38` | Directa |
| `P-ZONE-03` | Zona | Abstención | `RF-42`, `RF-15`, `RF-36` | `M-ZONE-01`, `M-CONS-02`, `M-NODE-02` | `EXT-Q39` | Directa |
| `P-ZONE-04` | Zona | Obligación | `RF-03`, `RF-15`, `RF-17`, `RNF-21` | `M-CTX-01`, `M-MODEL-04` | `BASE-Q09`†, `BASE-Q23`†, `EXT-Q46`†, `EXT-Q59`† | Indirecta (`†`) |
| `P-NODE-01` | Nodos/trust | Prohibición | `RF-05`, `RF-17`, `RNF-12` | `M-NODE-01`, `M-NODE-02` | `BASE-Q07`, `BASE-Q08`, `BASE-Q26`, `EXT-Q41` | Directa |
| `P-NODE-02` | Nodos/trust | Prohibición | `RF-15`, `RF-18`, `RF-47` | `M-NODE-02`, `M-CONS-02`, `M-ZONE-01` | `BASE-Q08`, `BASE-Q12`, `BASE-Q19`, `BASE-Q23`, `EXT-Q41`, `EXT-Q42` | Directa |
| `P-NODE-03` | Nodos/trust | Obligación | `RF-45`, `RF-49`, `RNF-32` | `M-TRUST-01`, `M-VAL-04` | `BASE-Q07`, `EXT-Q40`, `EXT-Q43` | Directa |
| `P-NODE-04` | Nodos/trust | Prohibición | `RF-49`, `RNF-32`, `RNF-33` | `M-TRUST-01`, `M-AUD-01` | `EXT-Q40` | Directa |
| `P-NODE-05` | Nodos/trust | Obligación | `RF-46`, `RF-47`, `RF-48` | `M-TRUST-02`, `M-NODE-02` | `BASE-Q19`, `EXT-Q42`, `EXT-Q44` | Directa |
| `P-NODE-06` | Nodos/trust | Abstención | `RF-47`, `RF-48`, `RF-53` | `M-NODE-02`, `M-ADAPT-02`, `M-AUD-01` | `BASE-Q19`†, `EXT-Q42`†, `EXT-Q45`†, `EXT-Q56`† | Indirecta (`†`) |
| `P-MODEL-01` | Modelo/AHP | Obligación | `RF-15`, `RF-52`, `RF-53` | `M-MODEL-01`, `M-NODE-02` | `BASE-Q04`, `BASE-Q32`, `EXT-Q46` | Directa |
| `P-MODEL-02` | Modelo/AHP | Obligación | `RF-50`, `RF-55`, `RNF-34` | `M-MODEL-02` | `EXT-Q48` | Directa |
| `P-MODEL-03` | Modelo/AHP | Prohibición | `RF-46`, `RF-50`, `RF-55`, `RNF-05`, `RNF-33` | `M-TRUST-02`, `M-MODEL-02` | `EXT-Q42`, `EXT-Q44`, `EXT-Q48` | Directa |
| `P-MODEL-04` | Modelo/AHP | Prohibición | `RF-55`, `RNF-34` | `M-MODEL-03` | `EXT-Q49`, `EXT-Q50` | Directa |
| `P-MODEL-05` | Modelo/AHP | Obligación | `RF-51`, `RF-54`, `RNF-29`, `RNF-33` | `M-MODEL-01`, `M-AUD-01` | `BASE-Q21`, `EXT-Q46`, `EXT-Q51`, `EXT-Q52`, `EXT-Q53` | Directa |
| `P-MODEL-06` | Modelo/AHP | Obligación | `RF-52`, `RF-35`, `RF-42` | `M-MODEL-01`, `M-CONS-02`, `M-ZONE-01` | `BASE-Q15` | Directa |
| `P-MODEL-07` | Modelo/AHP | Abstención | `RF-53`, `RF-56`, `RF-59` | `M-MODEL-01`, `M-FL-03` | `EXT-Q56` | Directa |
| `P-MODEL-08` | Modelo/AHP | Obligación | `RF-14`, `RNF-27` | `M-METRIC-01`, `M-AUD-01` | `EXT-Q54`, `EXT-Q55` | Directa |
| `P-MODEL-09` | Modelo/AHP | Obligación | `RF-15`, `RF-17`, `RNF-21` | `M-MODEL-04`, `M-CTX-01` | `BASE-Q21`†, `EXT-Q46`†, `EXT-Q59`†, `EXT-Q76`† | Indirecta (`†`) |
| `P-ADAPT-01` | Adaptación | Obligación | `RF-16`, `RF-17`, `RF-18`, `RNF-03` | `M-ADAPT-01`, `M-NODE-02` | `BASE-Q12` | Directa |
| `P-ADAPT-02` | Adaptación | Obligación | `RF-07`, `RF-17`, `RNF-12` | `M-ADAPT-02`, `M-BUFFER-01` | `BASE-Q14`, `EXT-Q62` | Directa |
| `P-ADAPT-03` | Adaptación | Obligación | `RF-17`, `RF-20`, `RNF-03` | `M-ADAPT-01`, `M-ADAPT-02`, `M-OPS-02` | `EXT-Q62` | Directa |
| `P-ADAPT-04` | Adaptación | Abstención | `RF-16`, `RF-17`, `RNF-02` | `M-ADAPT-01`, `M-NODE-02`, `M-AUD-01` | `EXT-Q45` | Directa |
| `P-ADAPT-05` | Adaptación | Prohibición | `RF-16`, `RF-22`, `RF-25`, `RF-62` | `M-ADAPT-03`, `M-FL-01` | `BASE-Q13`, `EXT-Q60`, `EXT-Q61` | Directa |
| `P-ADAPT-06` | Adaptación | Obligación | `RF-20`, `RF-44`, `RF-66` | `M-ADAPT-02`, `M-AUD-01` | `BASE-Q13`, `BASE-Q22`, `BASE-Q27`, `EXT-Q59`, `EXT-Q62` | Directa |
| `P-ADAPT-07` | Adaptación | Obligación | `RF-48`, `RF-62`, `RNF-14` | `M-TRUST-02`, `M-DELEG-01` | `EXT-Q45` | Directa |
| `P-ADAPT-08` | Adaptación | Prohibición | `RF-19`, `RF-26`, `RNF-02`, `RNF-13` | `M-REPL-01`, `M-TX-02`, `M-DELEG-02` | `BASE-Q10`†, `EXT-Q33`†, `EXT-Q34`† | Indirecta (`†`) |
| `P-FL-01` | Federated Learning | Abstención | `RF-21`, `RF-22`, `RF-25`, `RNF-12` | `M-FL-01`, `M-NODE-02` | `BASE-Q16`, `BASE-Q30`, `EXT-Q66` | Directa |
| `P-FL-02` | Federated Learning | Prohibición | `RF-21`, `RF-35`, `RF-42` | `M-FL-01`, `M-CONS-02`, `M-ZONE-01` | `BASE-Q24`, `BASE-Q25`, `EXT-Q67` | Directa |
| `P-FL-03` | Federated Learning | Obligación | `RF-56`, `RF-57`, `RNF-16`, `RNF-17` | `M-FL-03`, `M-ID-01` | `BASE-Q16`, `EXT-Q67`, `EXT-Q68` | Directa |
| `P-FL-04` | Federated Learning | Obligación | `RF-59`, `RNF-18` | `M-FL-04`, `M-AUD-01` | `BASE-Q24`, `EXT-Q69` | Directa |
| `P-FL-05` | Federated Learning | Obligación | `RF-58`, `RNF-19` | `M-FL-03`, `M-ID-01` | `BASE-Q16`, `EXT-Q68` | Directa |
| `P-FL-06` | Federated Learning | Prohibición | `RF-23`, `RF-38`, `RNF-17` | `M-FL-02`, `M-CONS-02`, `M-ZONE-01` | `EXT-Q66` | Directa |
| `P-FL-07` | Federated Learning | Obligación | `RF-25`, `RNF-16` | `M-FL-01`, `M-FL-02`, `M-AUD-01` | `BASE-Q16`, `BASE-Q24`, `EXT-Q66` | Directa |
| `P-FL-08` | Federated Learning | Obligación | `RF-24`, `RNF-38`, `RNF-39` | `M-MODEL-05`, `M-VAL-04` | `BASE-Q04`, `BASE-Q22`, `EXT-Q57`, `EXT-Q58` | Directa |
| `P-AUD-01` | Auditoría | Obligación | `RF-62` | `M-DELEG-01` | `BASE-Q14`, `EXT-Q63` | Directa |
| `P-AUD-02` | Auditoría | Obligación | `RF-63`, `RNF-36` | `M-DELEG-01`, `M-TIME-01` | `EXT-Q63`, `EXT-Q64`, `EXT-Q73` | Directa |
| `P-AUD-03` | Auditoría | Obligación | `RF-64`, `RNF-36` | `M-DELEG-02` | `EXT-Q63` | Directa |
| `P-AUD-04` | Auditoría | Prohibición | `RNF-14` | `M-DELEG-03` | `EXT-Q65` | Directa |
| `P-AUD-05` | Auditoría | Obligación | `RF-65`, `RF-66`, `RF-67` | `M-AUD-02` | `BASE-Q14`, `BASE-Q35`, `EXT-Q72` | Directa |
| `P-AUD-06` | Auditoría | Obligación | `RF-51`, `RF-54`, `RF-66`, `RNF-28`, `RNF-29` | `M-AUD-01` | `BASE-Q21`, `EXT-Q20`, `EXT-Q46`, `EXT-Q47`, `EXT-Q59`, `EXT-Q71` | Directa |
| `P-AUD-07` | Auditoría | Obligación | `RF-67`, `RNF-30`, `RNF-32`, `RNF-33` | `M-AUD-03`, `M-TIME-01` | `BASE-Q35`, `EXT-Q70` | Directa |
| `P-OPS-01` | Operación/QoS | Obligación | `RNF-01`, `RNF-02`, `RNF-04`, `RNF-05`, `RNF-06`, `RNF-08`, `RNF-09`, `RNF-14`, `RNF-21`, `RNF-39` | `M-OPS-01`, `M-VAL-04` | `EXT-Q65`, `EXT-Q76` | Directa |
| `P-OPS-02` | Operación/QoS | Obligación | `RNF-07`, `RF-17` | `M-OPS-02` | `BASE-Q02`, `BASE-Q29` | Directa |
| `P-OPS-03` | Operación/QoS | Obligación | `RNF-09`, `RNF-10` | `M-OPS-03`, `M-NODE-01` | `BASE-Q02` | Directa |
| `P-OPS-04` | Operación/QoS | Obligación | `RNF-12`, `RNF-13` | `M-ADAPT-02`, `M-BUFFER-01` | `BASE-Q08`†, `EXT-Q31`†, `EXT-Q32`†, `EXT-Q33`†, `EXT-Q34`† | Indirecta (`†`) |
| `P-OPS-05` | Operación/QoS | Obligación | `RF-29`, `RF-30`, `RNF-27` | `M-METRIC-01`, `M-TIME-01` | `BASE-Q07`, `BASE-Q09`, `BASE-Q33`, `EXT-Q54` | Directa |
| `P-OPS-06` | Operación/QoS | Abstención | `RF-08`, `RF-15`, `RF-26`, `RNF-12` | `M-TX-02`, `M-BUFFER-01`, `M-MODEL-04` | `BASE-Q10`†, `BASE-Q17`†, `EXT-Q31`†, `EXT-Q38`†, `EXT-Q46`† | Indirecta (`†`) |
| `P-INT-01` | Interoperabilidad | Obligación | `RNF-24`, `RNF-25`, `RNF-26` | `M-INT-01`, `M-VAL-01` | `BASE-Q05` | Directa |
| `P-INT-02` | Interoperabilidad | Prohibición | `RNF-10`, `RNF-23`, `RNF-38` | `M-INT-02`, `M-VAL-05` | `BASE-Q03` | Directa |
| `P-VAL-01` | Validación | Obligación | `RF-69`, `RNF-24`, `RNF-26`, `RV-03` | `M-VAL-01` | `EXT-Q01` | Directa |
| `P-VAL-02` | Validación | Obligación | `RF-70`, `RF-71`, `RNF-31`, `RV-01` | `M-VAL-02` | `EXT-Q01`†, `EXT-Q75`†, `EXT-Q77`†, `EXT-Q80`† | Indirecta (`†`) |
| `P-VAL-03` | Validación | Prohibición | `RF-71`, `RV-02` | `M-VAL-03` | `EXT-Q75`, `EXT-Q76`, `EXT-Q77` | Directa |
| `P-VAL-04` | Validación | Obligación | `RF-68`, `RNF-39`, `RV-01`, `RV-03` | `M-VAL-04` | `EXT-Q01`, `EXT-Q77` | Directa |
| `P-VAL-05` | Validación | Prohibición | `RNF-11`, `RNF-38` | `M-VAL-04`, `M-VAL-05` | `EXT-Q01`†, `EXT-Q02`†, `EXT-Q05`†, `EXT-Q77`†, `EXT-Q80`† | Indirecta (`†`) |
| `P-VAL-06` | Validación | Obligación | `RV-04`, `RV-05` | `M-VAL-05` | `EXT-Q02`, `EXT-Q04`, `EXT-Q08`, `EXT-Q09` | Directa |
| `P-VAL-07` | Validación | Obligación | `RF-31`, `RF-72`, `RV-03` | `M-VAL-04`, `M-VAL-06` | `BASE-Q11`, `EXT-Q05`, `EXT-Q77` | Directa |
| `P-VAL-08` | Validación | Obligación | `RF-68`, `RV-05`, `RNF-39` | `M-VAL-07`, `M-VAL-04` | `EXT-Q80` | Directa |

### 17.1 Resumen de cobertura SPARQL

- **Políticas totales:** 79.
- **Con cobertura SPARQL nominal/directa:** 69.
- **Con cobertura SPARQL indirecta (`†`):** 10: `P-ADAPT-08`, `P-CONS-06`, `P-GOV-02`, `P-MODEL-09`, `P-NODE-06`, `P-OPS-04`, `P-OPS-06`, `P-VAL-02`, `P-VAL-05`, `P-ZONE-04`.
- **Políticas sin ninguna consulta asociada:** 0.
- **Mecanismos con al menos una consulta útil derivada de sus políticas:** 55/55.
- **Escenarios S1–S17 con consultas principales asignadas:** 17/17.
