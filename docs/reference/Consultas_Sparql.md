# Batería de consultas SPARQL — SmartCity Continuum v3.0.0

Este documento documenta la batería de consultas asociada a `smartcity_continuum_v3.0.0.ttl`. Sustituye la documentación v2.1 y está alineado con los requisitos revisados `RF-01–RF-72`, `RNF-01–RNF-39`, `RV-01–RV-05` y con `POLICIES-REV-01`.

## 1. Cambios respecto a la batería anterior

La familia `BASE-Q01–BASE-Q35` se conserva por continuidad, pero se actualiza a la semántica v3. Se elimina el consentimiento binario; S3 representa migración sin implicar FL; S8 exige confinamiento Local/Mist; Cloud y Fog se tratan como capacidades condicionadas; y las consultas de usuario/consentimiento utilizan `ConsentRecord`, `SemanticContract` y `AuthorizationDecision`.

La extensión se amplía de `EXT-Q01–EXT-Q34` a `EXT-Q01–EXT-Q80`. La ampliación cubre los elementos que no existían en v2.1: artefactos versionados y trazabilidad RF/RNF/RV, 79 políticas y 55 mecanismos, autorización efectiva, cifrado, identidad pseudónima, contexto de datos, replicación/idempotencia, trust reproducible, alternativas de decisión, AHP frente a weighted multicriteria, linaje/rollback de modelos, acciones adaptativas separadas de FL, perfil de aceptación y relaciones/conflictos entre categorías de políticas.

## 2. Familias de consultas

| Familia | Rango | Finalidad |
|---|---:|---|
| BASE | `BASE-Q01–BASE-Q35` | Estructura, operación, escenarios S1–S8, ASK y agregados de continuidad. |
| EXT v3 | `EXT-Q01–EXT-Q80` | Validación semántica, privacidad, gobernanza, decisión, auditoría y reproducibilidad v3. |

## 3. Tipos y criterio de interpretación

| Tipo | Interpretación |
|---|---|
| `inventory` | Inventario/cobertura; debe devolver los recursos esperados del artefacto cargado. |
| `report` | Evidencia explicativa; las filas no representan por sí mismas incumplimiento. |
| `review` | Deuda, configuración pendiente o condición que requiere revisión. Puede devolver filas en una migración válida. |
| `violation` | Incumplimiento: debe devolver **0 filas**, pero solo tras superar las precondiciones de validación. |
| `ASK` | Comprobación booleana operativa; `true`/`false` se interpreta según la finalidad de la consulta. |
| `dashboard` | Métricas agregadas de cobertura/estado. |

### 3.1 Precondiciones obligatorias para interpretar “0 filas = cumplimiento”

Antes de utilizar cualquier consulta `violation` como evidencia deben ejecutarse, como mínimo, `EXT-Q01` (versión/artefactos), `EXT-Q02` (cobertura RF/RNF/RV), `EXT-Q05` (S1–S17), `EXT-Q76` (perfil de aceptación) y `EXT-Q77` (preparación de campaña). Una consulta vacía sobre un dataset incompleto **no** acredita cumplimiento, conforme a RF-71, RV-02 y P-VAL-03.

## 4. Resumen por bloques

| Bloque | Consultas | Nº |
|---|---|---:|
| BASE — Operación, estructura y escenarios | `BASE-Q01`–`BASE-Q35` | 35 |
| EXT v3 — Inventario, artefactos y trazabilidad | `EXT-Q01`–`EXT-Q10` | 10 |
| EXT v3 — Consentimiento, contratos y autorización efectiva | `EXT-Q11`–`EXT-Q21` | 11 |
| EXT v3 — Datos, identidad, seguridad y transmisión | `EXT-Q22`–`EXT-Q35` | 14 |
| EXT v3 — Zonas, nodos y confianza | `EXT-Q36`–`EXT-Q58` | 23 |
| EXT v3 — Adaptación, FL y delegación | `EXT-Q59`–`EXT-Q69` | 11 |
| EXT v3 — Auditoría, temporalidad, aceptación y validación | `EXT-Q70`–`EXT-Q80` | 11 |

## 5. Catálogo completo


### BASE — Operación, estructura y escenarios

#### BASE-Q01 — Usuarios, consentimiento activo e identificador externo

- **Tipo:** `inventory`
- **Qué valida / hace:** Inventariar usuarios y su rango de consentimiento activo sin recurrir al consentimiento binario heredado.
- **Requisitos relacionados:** `RF-01`, `RF-32`, `RF-61`, `RF-70`
- **Políticas relacionadas:** `P-CONS-01`, `P-DATA-02`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **4 filas**.

#### BASE-Q02 — Nodos computacionales, tipo y elasticidad

- **Tipo:** `inventory`
- **Qué valida / hace:** Listar la infraestructura del continuum incluyendo nodos Mist, Edge, Fog y Cloud.
- **Requisitos relacionados:** `RF-02`, `RF-05`, `RF-70`
- **Políticas relacionadas:** `P-OPS-02`, `P-OPS-03`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **8 filas**.

#### BASE-Q03 — Wearables asociados a usuarios

- **Tipo:** `inventory`
- **Qué valida / hace:** Comprobar la asociación usuario-dispositivo vestible.
- **Requisitos relacionados:** `RF-01`, `RF-70`
- **Políticas relacionadas:** `P-INT-02`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **4 filas**.

#### BASE-Q04 — Modelos, tier, versión, host y linaje

- **Tipo:** `inventory`
- **Qué valida / hace:** Inspeccionar distribución y ciclo de vida de modelos.
- **Requisitos relacionados:** `RF-11`, `RF-12`, `RF-13`, `RF-24`, `RF-70`
- **Políticas relacionadas:** `P-FL-08`, `P-MODEL-01`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **7 filas**.

#### BASE-Q05 — Sensores fisiológicos y dispositivo host

- **Tipo:** `inventory`
- **Qué valida / hace:** Validar la instrumentación fisiológica y la reutilización SOSA/SAREF.
- **Requisitos relacionados:** `RF-06`, `RNF-25`, `RF-70`
- **Políticas relacionadas:** `P-INT-01`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **5 filas**.

#### BASE-Q06 — Roles y permisos RBAC

- **Tipo:** `inventory`
- **Qué valida / hace:** Inspeccionar roles, permisos y restricciones de consentimiento vinculadas al acceso.
- **Requisitos relacionados:** `RF-37`, `RF-70`
- **Políticas relacionadas:** `P-CONS-05`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **10 filas**.

#### BASE-Q07 — Estados de nodo y métricas operativas

- **Tipo:** `report`
- **Qué valida / hace:** Obtener carga, disponibilidad, comunicación, capacidad residual, recursos y trust actual asociado al estado.
- **Requisitos relacionados:** `RF-05`, `RF-29`, `RF-45`, `RF-70`
- **Políticas relacionadas:** `P-NODE-01`, `P-NODE-03`, `P-OPS-05`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **7 filas**.

#### BASE-Q08 — Nodos saturados, no disponibles o desconectados

- **Tipo:** `report`
- **Qué valida / hace:** Detectar estados no elegibles o críticos para selección/migración.
- **Requisitos relacionados:** `RF-17`, `RF-47`, `RNF-12`
- **Políticas relacionadas:** `P-NODE-01`, `P-NODE-02`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **2 filas**.

#### BASE-Q09 — Estados de usuario, movilidad y estrés

- **Tipo:** `report`
- **Qué valida / hace:** Monitorizar el contexto humano y sus estados temporales.
- **Requisitos relacionados:** `RF-03`, `RF-30`, `RNF-35`
- **Políticas relacionadas:** `P-GOV-05`, `P-OPS-05`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **6 filas**.

#### BASE-Q10 — Estado de dispositivos y puerta de transmisión

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar batería, conectividad y disponibilidad de datos parametrizados.
- **Requisitos relacionados:** `RF-04`, `RF-26`, `RF-27`
- **Políticas relacionadas:** `P-DATA-04`, `P-DATA-06`, `P-DATA-07`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **4 filas**.

#### BASE-Q11 — Escenario S1 — operación normal

- **Tipo:** `report`
- **Qué valida / hace:** Validar la línea base de operación normal con evaluación y selección de modelo.
- **Requisitos relacionados:** `RF-31`, `RF-72`
- **Políticas relacionadas:** `P-VAL-07`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### BASE-Q12 — Escenario S2 — saturación y candidato Fog

- **Tipo:** `report`
- **Qué valida / hace:** Validar saturación Edge y disponibilidad de alternativa sin asumir automáticamente una migración.
- **Requisitos relacionados:** `RF-17`, `RF-31`
- **Políticas relacionadas:** `P-ADAPT-01`, `P-NODE-02`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### BASE-Q13 — Escenario S3 — migración Edge → Fog

- **Tipo:** `report`
- **Qué valida / hace:** Validar que S3 se representa mediante MigrationEvent y no implica por sí mismo una sesión FL.
- **Requisitos relacionados:** `RF-16`, `RF-17`, `RF-31`
- **Políticas relacionadas:** `P-ADAPT-05`, `P-ADAPT-06`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### BASE-Q14 — Escenario S4 — fallo, delegación y degradación

- **Tipo:** `report`
- **Qué valida / hace:** Trazar fallo de nodo, delegación temporal y fallback/degradación.
- **Requisitos relacionados:** `RF-17`, `RF-20`, `RF-62`, `RF-65`
- **Políticas relacionadas:** `P-ADAPT-02`, `P-AUD-01`, `P-AUD-05`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### BASE-Q15 — Escenario S5 — consentimiento local

- **Tipo:** `report`
- **Qué valida / hace:** Comprobar operación local autorizada para un usuario con RangeLocalOnly.
- **Requisitos relacionados:** `RF-32`, `RF-36`, `RF-38`
- **Políticas relacionadas:** `P-CONS-01`, `P-CONS-04`, `P-MODEL-06`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### BASE-Q16 — Escenario S6 — aprendizaje federado protegido

- **Tipo:** `report`
- **Qué valida / hace:** Trazar sesiones FL ascendentes/descendentes, payload y privacidad.
- **Requisitos relacionados:** `RF-21`, `RF-22`, `RF-25`, `RF-56`, `RF-58`
- **Políticas relacionadas:** `P-FL-01`, `P-FL-03`, `P-FL-05`, `P-FL-07`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **3 filas**.

#### BASE-Q17 — Escenario S7 — zona rural y retención

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar contexto rural, conectividad y acciones de retención/sincronización cuando existan.
- **Requisitos relacionados:** `RF-08`, `RF-27`, `RF-31`
- **Políticas relacionadas:** `P-ZONE-02`, `P-DATA-07`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### BASE-Q18 — Escenario S8 — zona restringida y confinamiento local

- **Tipo:** `report`
- **Qué valida / hace:** Validar que el escenario restringido usa LocalModelTier y no Edge/Fog/Cloud para el procesamiento protegido.
- **Requisitos relacionados:** `RF-42`, `RF-43`, `RF-60`
- **Políticas relacionadas:** `P-ZONE-01`, `P-DATA-01`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### BASE-Q19 — Candidatos operativamente elegibles

- **Tipo:** `report`
- **Qué valida / hace:** Listar nodos con disponibilidad, comunicación, carga, capacidad y trust compatibles con selección.
- **Requisitos relacionados:** `RF-18`, `RF-47`, `RF-48`
- **Políticas relacionadas:** `P-NODE-02`, `P-NODE-05`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **4 filas**.

#### BASE-Q20 — Perfil semántico completo del usuario

- **Tipo:** `report`
- **Qué valida / hace:** Obtener usuario, dispositivos, zona, contrato, consentimiento y registro activo.
- **Requisitos relacionados:** `RF-02`, `RF-33`, `RF-34`, `RF-70`
- **Políticas relacionadas:** `P-CONS-02`, `P-CONS-03`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **4 filas**.

#### BASE-Q21 — Resumen de EvaluationState y acción ejecutada

- **Tipo:** `report`
- **Qué valida / hace:** Resumir decisiones MAPE-K, tier, rentabilidad y acción resultante.
- **Requisitos relacionados:** `RF-14`, `RF-15`, `RF-66`
- **Políticas relacionadas:** `P-AUD-06`, `P-MODEL-05`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **11 filas**.

#### BASE-Q22 — Modelos y eventos de degradación

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar causas de degradación y acciones registradas.
- **Requisitos relacionados:** `RF-20`, `RF-24`
- **Políticas relacionadas:** `P-ADAPT-06`, `P-FL-08`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **3 filas**.

#### BASE-Q23 — Relaciones usuario–nodo y distancia

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar asignación contextual entre usuarios y nodos.
- **Requisitos relacionados:** `RF-02`, `RF-03`, `RF-18`
- **Políticas relacionadas:** `P-NODE-02`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### BASE-Q24 — Cadena de aprendizaje federado

- **Tipo:** `report`
- **Qué valida / hace:** Trazar sesiones FL, nodos, payload, modelo, datos y presupuesto.
- **Requisitos relacionados:** `RF-21`, `RF-22`, `RF-25`, `RF-59`
- **Políticas relacionadas:** `P-FL-02`, `P-FL-04`, `P-FL-07`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **5 filas**.

#### BASE-Q25 — Usuarios autorizados para FL global

- **Tipo:** `report`
- **Qué valida / hace:** Identificar usuarios cuya autorización efectiva permite RangeGlobalAgg para propósito federado global.
- **Requisitos relacionados:** `RF-21`, `RF-32`, `RF-36`
- **Políticas relacionadas:** `P-CONS-04`, `P-FL-02`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### BASE-Q26 — ASK — existe algún nodo saturado

- **Tipo:** `ASK`
- **Qué valida / hace:** Comprobación rápida de saturación.
- **Requisitos relacionados:** `RF-05`, `RF-29`
- **Políticas relacionadas:** `P-NODE-01`
- **Criterio:** interpretar el booleano según la finalidad indicada.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **true**.

#### BASE-Q27 — ASK — existe degradación registrada

- **Tipo:** `ASK`
- **Qué valida / hace:** Comprobación rápida de existencia de degradación de modelo/servicio.
- **Requisitos relacionados:** `RF-20`
- **Políticas relacionadas:** `P-ADAPT-06`
- **Criterio:** interpretar el booleano según la finalidad indicada.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **true**.

#### BASE-Q28 — ASK — existe transferencia externa que viole confinamiento o identidad

- **Tipo:** `ASK`
- **Qué valida / hace:** Detectar de forma rápida una transferencia externa de observación cruda o con identificador directo/no seguro.
- **Requisitos relacionados:** `RF-36`, `RF-60`, `RF-61`
- **Políticas relacionadas:** `P-CONS-04`, `P-DATA-04`
- **Criterio:** interpretar el booleano según la finalidad indicada.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **false**.

#### BASE-Q29 — ASK — existe capacidad elástica en Fog o Cloud

- **Tipo:** `ASK`
- **Qué valida / hace:** Comprobar que la elasticidad se modela como capacidad del nodo y no como propiedad fija exclusiva de Cloud.
- **Requisitos relacionados:** `RNF-07`
- **Políticas relacionadas:** `P-OPS-02`
- **Criterio:** interpretar el booleano según la finalidad indicada.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **true**.

#### BASE-Q30 — ASK — existe sesión FL con Cloud

- **Tipo:** `ASK`
- **Qué valida / hace:** Confirmar existencia de aprendizaje federado global.
- **Requisitos relacionados:** `RF-22`
- **Políticas relacionadas:** `P-FL-01`
- **Criterio:** interpretar el booleano según la finalidad indicada.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **true**.

#### BASE-Q31 — Conteo de usuarios por rango activo

- **Tipo:** `dashboard`
- **Qué valida / hace:** Agregar usuarios por rango de consentimiento activo.
- **Requisitos relacionados:** `RF-32`, `RF-68`
- **Políticas relacionadas:** `P-CONS-01`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **3 filas**.

#### BASE-Q32 — Conteo de modelos por tier

- **Tipo:** `dashboard`
- **Qué valida / hace:** Resumir distribución de modelos por tier.
- **Requisitos relacionados:** `RF-13`, `RF-68`
- **Políticas relacionadas:** `P-MODEL-01`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **4 filas**.

#### BASE-Q33 — Uso medio de recursos por tipo de nodo

- **Tipo:** `dashboard`
- **Qué valida / hace:** Calcular uso medio de recursos por tipo de nodo en estados instrumentados.
- **Requisitos relacionados:** `RF-29`, `RNF-27`
- **Políticas relacionadas:** `P-OPS-05`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **5 filas**.

#### BASE-Q34 — Nodos que cubren zonas restringidas

- **Tipo:** `report`
- **Qué valida / hace:** Inventariar infraestructura geográficamente asociada a RestrictedZone sin asumir que esté autorizada para procesar datos protegidos.
- **Requisitos relacionados:** `RF-42`, `RF-43`
- **Políticas relacionadas:** `P-ZONE-01`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### BASE-Q35 — Cadena de fallo → evaluación → acción

- **Tipo:** `report`
- **Qué valida / hace:** Reconstruir decisiones asociadas a síntomas/fallos y su acción adaptativa final.
- **Requisitos relacionados:** `RF-20`, `RF-65`, `RF-67`
- **Políticas relacionadas:** `P-AUD-05`, `P-AUD-07`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **86 filas**.


### EXT v3 — Inventario, artefactos y trazabilidad

#### EXT-Q01 — Inventario de versión y artefactos v3

- **Tipo:** `inventory`
- **Qué valida / hace:** Verificar versión de ontología y artefactos versionados asociados.
- **Requisitos relacionados:** `RF-68`, `RNF-39`, `RV-01`, `RV-03`
- **Políticas relacionadas:** `P-VAL-01`, `P-VAL-04`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **6 filas**.

#### EXT-Q02 — Cobertura de requisitos RF/RNF/RV

- **Tipo:** `dashboard`
- **Qué valida / hace:** Comprobar que los requisitos revisados están representados en la ontología.
- **Requisitos relacionados:** `RV-04`, `RF-68`
- **Políticas relacionadas:** `P-VAL-06`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **3 filas**.

#### EXT-Q03 — Inventario completo de políticas

- **Tipo:** `inventory`
- **Qué valida / hace:** Listar las 79 políticas v3 con categoría, tipo y versión.
- **Requisitos relacionados:** `RF-39`, `RF-40`, `RF-70`
- **Políticas relacionadas:** `P-GOV-01`, `P-GOV-04`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **79 filas**.

#### EXT-Q04 — Inventario completo de mecanismos

- **Tipo:** `inventory`
- **Qué valida / hace:** Listar los 55 mecanismos y las políticas que soportan.
- **Requisitos relacionados:** `RV-04`
- **Políticas relacionadas:** `P-VAL-06`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **55 filas**.

#### EXT-Q05 — Inventario de escenarios S1–S17

- **Tipo:** `inventory`
- **Qué valida / hace:** Verificar el artefacto versionado de escenarios y su cobertura.
- **Requisitos relacionados:** `RF-31`, `RF-72`, `RV-03`
- **Políticas relacionadas:** `P-VAL-07`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **17 filas**.

#### EXT-Q06 — Categorías de política

- **Tipo:** `inventory`
- **Qué valida / hace:** Inventariar las 12 categorías de gobernanza.
- **Requisitos relacionados:** `RF-39`, `RF-40`
- **Políticas relacionadas:** `P-GOV-01`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **12 filas**.

#### EXT-Q07 — Relaciones entre categorías de políticas

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar la taxonomía de compatibilidad/conflicto y la estrategia de resolución cuando exista.
- **Requisitos relacionados:** `RNF-22`, `RV-04`
- **Políticas relacionadas:** `P-GOV-03`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **67 filas**.

#### EXT-Q08 — Trazabilidad requisito → política → mecanismo

- **Tipo:** `report`
- **Qué valida / hace:** Mostrar trazabilidad individual de requisitos a políticas y mecanismos.
- **Requisitos relacionados:** `RV-04`, `RNF-39`
- **Políticas relacionadas:** `P-VAL-06`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1089 filas**.

#### EXT-Q09 — Revisión — requisito sin política ni mecanismo explícito

- **Tipo:** `review`
- **Qué valida / hace:** Listar requisitos que no tienen política ni mecanismo explícito; los requisitos puramente estructurales pueden ser válidos y deben trazarse a ontología/consulta en la matriz documental.
- **Requisitos relacionados:** `RV-04`
- **Políticas relacionadas:** `P-VAL-06`
- **Criterio:** Las filas requieren revisión de la matriz RV-04; no son automáticamente incumplimiento.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **6 filas**.

#### EXT-Q10 — Incumplimiento — política o mecanismo incompleto

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar políticas/mecanismos sin metadatos mínimos para gobernanza reproducible.
- **Requisitos relacionados:** `RF-39`, `RF-40`, `RNF-20`
- **Políticas relacionadas:** `P-GOV-01`, `P-GOV-04`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.


### EXT v3 — Consentimiento, contratos y autorización efectiva

#### EXT-Q11 — Reporte de ConsentRecord

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar consentimiento independiente del contrato: sujeto, rango, propósito, categorías y vigencia.
- **Requisitos relacionados:** `RF-32`, `RF-35`
- **Políticas relacionadas:** `P-CONS-01`, `P-CONS-04`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **25 filas**.

#### EXT-Q12 — Reporte de contratos semánticos

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar contratos efectivos, rangos, propósitos, políticas y vigencia.
- **Requisitos relacionados:** `RF-33`, `RF-34`
- **Políticas relacionadas:** `P-CONS-02`, `P-CONS-03`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **28 filas**.

#### EXT-Q13 — Incumplimiento — ConsentRecord incompleto

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar registros de consentimiento sin sujeto, rango, propósito, categorías autorizadas o validFrom.
- **Requisitos relacionados:** `RF-32`, `RF-35`
- **Políticas relacionadas:** `P-CONS-01`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q14 — Incumplimiento — contrato semántico incompleto

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar contratos sin sujeto, rango, propósito, política o inicio de vigencia.
- **Requisitos relacionados:** `RF-33`, `RF-34`
- **Políticas relacionadas:** `P-CONS-02`, `P-CONS-03`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q15 — Incumplimiento — contratos solapados para usuario y propósito

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar dos contratos del mismo usuario y propósito con intervalos de vigencia solapados.
- **Requisitos relacionados:** `RF-33`, `RNF-22`
- **Políticas relacionadas:** `P-CONS-02`
- **Criterio:** 0 filas si se exige un único contrato efectivo por usuario y propósito.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q16 — Incumplimiento — rango activo no respaldado por ConsentRecord

- **Tipo:** `violation`
- **Qué valida / hace:** Comprobar que el rango activo del usuario coincide con al menos un ConsentRecord vigente asociado.
- **Requisitos relacionados:** `RF-35`
- **Políticas relacionadas:** `P-CONS-01`, `P-CONS-04`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q17 — Reporte de autorizaciones efectivas

- **Tipo:** `report`
- **Qué valida / hace:** Mostrar autorización efectiva utilizada por cada evaluación.
- **Requisitos relacionados:** `RF-35`, `RF-36`, `RF-66`
- **Políticas relacionadas:** `P-CONS-04`, `P-GOV-03`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **8 filas**.

#### EXT-Q18 — Incumplimiento — autorización efectiva incompleta

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar AuthorizationDecision sin outcome, rango efectivo, consentimiento, contrato, zona o validFrom.
- **Requisitos relacionados:** `RF-35`, `RF-36`
- **Políticas relacionadas:** `P-CONS-04`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q19 — Incumplimiento — autorización efectiva excede consentimiento o contrato

- **Tipo:** `violation`
- **Qué valida / hace:** Comparar niveles de rango mediante orden explícito Denied=0, Local=1, Community=2, Global=3.
- **Requisitos relacionados:** `RF-35`, `RF-36`
- **Políticas relacionadas:** `P-CONS-04`, `P-GOV-03`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q20 — Incumplimiento — EvaluationState sin autorización concedida

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar decisiones relevantes sin AuthorizationDecision concedida.
- **Requisitos relacionados:** `RF-36`, `RF-66`, `RNF-28`
- **Políticas relacionadas:** `P-CONS-04`, `P-AUD-06`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q21 — Inventario de rangos mínimos requeridos

- **Tipo:** `inventory`
- **Qué valida / hace:** Listar recursos que declaran requiresConsentRange para preparar validaciones de autorización.
- **Requisitos relacionados:** `RF-37`
- **Políticas relacionadas:** `P-CONS-05`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **11 filas**.


### EXT v3 — Datos, identidad, seguridad y transmisión

#### EXT-Q22 — Incumplimiento — observación fisiológica cruda fuera del ámbito local

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar observaciones crudas enviadas a Edge/Fog/Cloud mediante sentToNode o TransferEvent.
- **Requisitos relacionados:** `RF-10`, `RF-60`, `RNF-17`
- **Políticas relacionadas:** `P-DATA-01`, `P-ZONE-01`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q23 — Reporte de transferencias externas de datos

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar datos, categoría, sensibilidad, origen, destino, identificador y seguridad de cada transferencia.
- **Requisitos relacionados:** `RF-09`, `RF-27`, `RF-61`
- **Políticas relacionadas:** `P-DATA-02`, `P-DATA-03`, `P-DATA-10`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **3 filas**.

#### EXT-Q24 — Reporte de contexto de datos

- **Tipo:** `report`
- **Qué valida / hace:** Mostrar el contexto operativo persistido con cada dato parametrizado.
- **Requisitos relacionados:** `RF-09`, `RF-30`
- **Políticas relacionadas:** `P-DATA-10`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **2 filas**.

#### EXT-Q25 — Incumplimiento — DataContext incompleto

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar datos parametrizados transmitidos sin contexto mínimo.
- **Requisitos relacionados:** `RF-09`
- **Políticas relacionadas:** `P-DATA-10`
- **Criterio:** 0 filas para datos que requieren contexto completo.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q26 — Inventario de identificadores

- **Tipo:** `inventory`
- **Qué valida / hace:** Listar identificadores por tipo y scope.
- **Requisitos relacionados:** `RF-61`, `RNF-19`
- **Políticas relacionadas:** `P-DATA-02`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **4 filas**.

#### EXT-Q27 — Incumplimiento — transferencia externa sin identificador seguro

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar transferencias a Edge/Fog/Cloud sin pseudónimo o identificador anónimo.
- **Requisitos relacionados:** `RF-61`, `RNF-17`
- **Políticas relacionadas:** `P-DATA-02`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q28 — Incumplimiento — identificador directo en flujo externo

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar cualquier uso explícito de DirectIdentifier en transferencias externas.
- **Requisitos relacionados:** `RF-61`, `RNF-17`
- **Políticas relacionadas:** `P-DATA-02`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q29 — Reporte de línea base de cifrado

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar mecanismos de cifrado y sus garantías declaradas.
- **Requisitos relacionados:** `RNF-15`
- **Políticas relacionadas:** `P-DATA-03`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### EXT-Q30 — Incumplimiento — transferencia sensible sin cifrado en tránsito

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar TransferEvent con dato sensible sin mecanismo que declare protectsInTransit=true.
- **Requisitos relacionados:** `RNF-15`
- **Políticas relacionadas:** `P-DATA-03`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q31 — Reporte de buffers y retención

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar registros de buffer/retención cuando existan, incluyendo temporalidad y seguridad.
- **Requisitos relacionados:** `RF-08`, `RNF-12`
- **Políticas relacionadas:** `P-DATA-05`, `P-DATA-07`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q32 — Incumplimiento — buffer sensible sin protección en reposo

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar buffers de datos sensibles sin mecanismo protectsAtRest=true.
- **Requisitos relacionados:** `RNF-15`, `RNF-12`
- **Políticas relacionadas:** `P-DATA-03`, `P-DATA-05`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q33 — Reporte de replicación y sincronización

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar eventos de replicación/sincronización y su control de duplicados.
- **Requisitos relacionados:** `RF-19`, `RNF-13`
- **Políticas relacionadas:** `P-DATA-08`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q34 — Incumplimiento — replicación sin versión o idempotencia

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar ReplicationEvent/SynchronizationEvent incompleto para reejecución segura.
- **Requisitos relacionados:** `RF-19`, `RNF-13`
- **Políticas relacionadas:** `P-DATA-08`
- **Criterio:** 0 filas cuando existan eventos de replicación/sincronización.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q35 — Reporte de criticidad y prioridad de datos

- **Tipo:** `report`
- **Qué valida / hace:** Comprobar criticidad genérica independiente del nivel de estrés.
- **Requisitos relacionados:** `RF-28`
- **Políticas relacionadas:** `P-DATA-09`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **6 filas**.


### EXT v3 — Zonas, nodos y confianza

#### EXT-Q36 — Reporte de zona restringida

- **Tipo:** `report`
- **Qué valida / hace:** Mostrar usuarios, evaluaciones y tiers asociados a RestrictedZone.
- **Requisitos relacionados:** `RF-42`, `RF-43`
- **Políticas relacionadas:** `P-ZONE-01`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### EXT-Q37 — Incumplimiento — procesamiento/transferencia externa en RestrictedZone

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar tier Edge/Fog/Cloud seleccionado o TransferEvent externo asociado a evaluación/usuario en RestrictedZone.
- **Requisitos relacionados:** `RF-42`, `RF-43`, `RF-60`
- **Políticas relacionadas:** `P-ZONE-01`, `P-GOV-03`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q38 — Reporte de zona rural y ventanas de transmisión

- **Tipo:** `review`
- **Qué valida / hace:** Revisar usuarios rurales, conectividad y eventos de retención/sincronización; la ausencia de eventos no implica por sí sola incumplimiento si no había datos pendientes.
- **Requisitos relacionados:** `RF-08`, `RF-27`
- **Políticas relacionadas:** `P-ZONE-02`, `P-DATA-07`
- **Criterio:** las filas requieren revisión; no equivalen automáticamente a incumplimiento.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### EXT-Q39 — Reporte de procesamiento urbano condicionado

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar evaluaciones urbanas junto con consentimiento efectivo y tier.
- **Requisitos relacionados:** `RF-42`
- **Políticas relacionadas:** `P-ZONE-03`, `P-CONS-04`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **5 filas**.

#### EXT-Q40 — Reporte de NodeState y trust reproducible

- **Tipo:** `report`
- **Qué valida / hace:** Listar estados de nodo y TrustAssessment separado de los pesos AHP.
- **Requisitos relacionados:** `RF-45`, `RF-49`, `RNF-32`
- **Políticas relacionadas:** `P-NODE-03`, `P-NODE-04`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **7 filas**.

#### EXT-Q41 — Incumplimiento — NodeState sin campos de elegibilidad

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar estados de nodo sin disponibilidad, workload, comunicación, capacidad residual u operational status.
- **Requisitos relacionados:** `RF-05`, `RF-47`
- **Políticas relacionadas:** `P-NODE-01`, `P-NODE-02`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q42 — Candidatos elegibles ordenados por trust

- **Tipo:** `report`
- **Qué valida / hace:** Aplicar primero filtros duros y después exponer score de confianza para ordenación externa.
- **Requisitos relacionados:** `RF-47`, `RF-48`
- **Políticas relacionadas:** `P-NODE-02`, `P-NODE-05`, `P-MODEL-03`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **4 filas**.

#### EXT-Q43 — Revisión — TrustAssessment no plenamente reproducible

- **Tipo:** `review`
- **Qué valida / hace:** Señalar trust histórico sin versión, ventana o evidencia suficiente. Los datos migrados pueden aparecer aquí hasta ser re-medidos.
- **Requisitos relacionados:** `RF-49`, `RNF-32`
- **Políticas relacionadas:** `P-NODE-03`
- **Criterio:** las filas requieren revisión; no equivalen automáticamente a incumplimiento.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **7 filas**.

#### EXT-Q44 — Reporte de confianza externa usada en evaluación

- **Tipo:** `report`
- **Qué valida / hace:** Mostrar hasTrustWeight/TrustAssessment como criterio externo, separado de los tres pesos AHP.
- **Requisitos relacionados:** `RF-46`, `RF-55`
- **Políticas relacionadas:** `P-MODEL-03`, `P-NODE-05`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **10 filas**.

#### EXT-Q45 — Incumplimiento — destino adaptativo explícitamente no elegible

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar MigrationEvent/DelegationEvent cuando existe un snapshot del destino en el mismo escenario y dicho snapshot demuestra inelegibilidad dura o menor trust que el origen comparable.
- **Requisitos relacionados:** `RF-18`, `RF-48`
- **Políticas relacionadas:** `P-ADAPT-04`, `P-ADAPT-07`
- **Criterio:** 0 filas cuando existen snapshots comparables; la ausencia de snapshot debe tratarse como deuda de evidencia, no como falsa violación.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q46 — Reporte completo de decisiones de modelo

- **Tipo:** `report`
- **Qué valida / hace:** Mostrar usuario, método, pesos, tier, justificación, trust externo y acción.
- **Requisitos relacionados:** `RF-15`, `RF-51`, `RF-66`
- **Políticas relacionadas:** `P-MODEL-01`, `P-MODEL-05`, `P-AUD-06`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **11 filas**.

#### EXT-Q47 — Incumplimiento — evaluación sin campos de decisión mínimos

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar EvaluationState sin usuario, propósito, zona, contrato, autorización, método, tres pesos, tier, justificación, instante o acción.
- **Requisitos relacionados:** `RF-54`, `RF-66`, `RNF-28`
- **Políticas relacionadas:** `P-AUD-06`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q48 — Incumplimiento — pesos multicriterio no normalizados

- **Tipo:** `violation`
- **Qué valida / hace:** Comprobar que latencia+privacidad+calidad=1 con tolerancia; trust se excluye.
- **Requisitos relacionados:** `RF-50`, `RF-55`, `RNF-34`
- **Políticas relacionadas:** `P-MODEL-02`, `P-MODEL-03`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q49 — Reporte de método y consistencia

- **Tipo:** `report`
- **Qué valida / hace:** Distinguir AHP real de weighted multicriteria y exponer ratio/umbral cuando aplica.
- **Requisitos relacionados:** `RF-55`, `RNF-33`, `RNF-34`
- **Políticas relacionadas:** `P-MODEL-04`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **8 filas**.

#### EXT-Q50 — Incumplimiento — evaluación AHP sin consistencia válida

- **Tipo:** `violation`
- **Qué valida / hace:** Para AHPDecisionMethod exigir comparaciones, ratio, umbral y ratio≤umbral.
- **Requisitos relacionados:** `RF-55`, `RNF-34`
- **Políticas relacionadas:** `P-MODEL-04`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q51 — Reporte de alternativas por evaluación

- **Tipo:** `report`
- **Qué valida / hace:** Mostrar cada tier candidato, elegibilidad, score y razón.
- **Requisitos relacionados:** `RF-51`, `RNF-29`
- **Políticas relacionadas:** `P-MODEL-05`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **32 filas**.

#### EXT-Q52 — Revisión — alternativas pendientes de recalcular

- **Tipo:** `review`
- **Qué valida / hace:** Identificar alternativas migradas sin score/elegibilidad completos.
- **Requisitos relacionados:** `RF-51`, `RNF-29`, `RNF-33`
- **Políticas relacionadas:** `P-MODEL-05`
- **Criterio:** las filas requieren revisión; no equivalen automáticamente a incumplimiento.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **32 filas**.

#### EXT-Q53 — Incumplimiento — alternativa seleccionada inválida

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar selectedAlternative ausente, no elegible o cuyo tier no coincide con selectedModelTier.
- **Requisitos relacionados:** `RF-51`, `RF-54`
- **Políticas relacionadas:** `P-MODEL-05`
- **Criterio:** 0 filas una vez recalculadas y completadas las alternativas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q54 — Reporte de calidad observada de modelo

- **Tipo:** `report`
- **Qué valida / hace:** Separar evidencia de calidad/predicción de hasModelQualityWeight.
- **Requisitos relacionados:** `RF-14`, `RF-29`, `RNF-27`
- **Políticas relacionadas:** `P-MODEL-08`, `P-OPS-05`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q55 — Revisión — evidencia de calidad insuficiente

- **Tipo:** `review`
- **Qué valida / hace:** Señalar evaluaciones que ponderan calidad pero no enlazan evidencia observada suficiente; puede reflejar datos heredados pendientes.
- **Requisitos relacionados:** `RF-14`, `RF-54`
- **Políticas relacionadas:** `P-MODEL-08`
- **Criterio:** las filas requieren revisión; no equivalen automáticamente a incumplimiento.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **8 filas**.

#### EXT-Q56 — Incumplimiento — Cloud seleccionado sin condiciones suficientes

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar CloudModelTier cuando rango efectivo no sea global, zona sea restringida o autorización no esté concedida.
- **Requisitos relacionados:** `RF-53`
- **Políticas relacionadas:** `P-MODEL-07`, `P-ZONE-01`, `P-CONS-04`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q57 — Reporte de versionado y linaje de modelos

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar versión, fecha, modelo previo y estado de linaje.
- **Requisitos relacionados:** `RF-24`
- **Políticas relacionadas:** `P-FL-08`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **7 filas**.

#### EXT-Q58 — Revisión — preparación de rollback

- **Tipo:** `review`
- **Qué valida / hace:** Listar RollbackEvent y modelos sin linaje suficiente para rollback reproducible.
- **Requisitos relacionados:** `RF-24`
- **Políticas relacionadas:** `P-FL-08`
- **Criterio:** las filas requieren revisión; no equivalen automáticamente a incumplimiento.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **7 filas**.


### EXT v3 — Adaptación, FL y delegación

#### EXT-Q59 — Reporte de acciones adaptativas

- **Tipo:** `report`
- **Qué valida / hace:** Listar acciones de adaptación y evaluación que las autorizó.
- **Requisitos relacionados:** `RF-16`, `RF-17`, `RF-20`, `RF-66`
- **Políticas relacionadas:** `P-ADAPT-06`, `P-AUD-06`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **11 filas**.

#### EXT-Q60 — Reporte específico de migraciones

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar MigrationEvent independiente de FL.
- **Requisitos relacionados:** `RF-16`, `RF-17`
- **Políticas relacionadas:** `P-ADAPT-05`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### EXT-Q61 — Incumplimiento — migración/delegación confundida con sesión FL

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar un mismo individuo tipado simultáneamente como MigrationEvent/DelegationEvent y FederatedLearningSession.
- **Requisitos relacionados:** `RF-16`, `RF-22`
- **Políticas relacionadas:** `P-ADAPT-05`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q62 — Reporte de degradaciones

- **Tipo:** `report`
- **Qué valida / hace:** Listar DegradationEvent y causa explícita.
- **Requisitos relacionados:** `RF-20`
- **Políticas relacionadas:** `P-ADAPT-02`, `P-ADAPT-03`, `P-ADAPT-06`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### EXT-Q63 — Reporte de delegaciones temporales

- **Tipo:** `report`
- **Qué valida / hace:** Mostrar origen, destino, disparador, recuperación, profundidad, expiración planificada y cierre real.
- **Requisitos relacionados:** `RF-62`, `RF-63`, `RF-64`
- **Políticas relacionadas:** `P-AUD-01`, `P-AUD-02`, `P-AUD-03`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **1 filas**.

#### EXT-Q64 — Incumplimiento — delegación incompleta

- **Tipo:** `violation`
- **Qué valida / hace:** Exigir origen, destino, causa/estado disparador, validFrom y condición de recuperación; validTo puede faltar mientras esté activa.
- **Requisitos relacionados:** `RF-63`
- **Políticas relacionadas:** `P-AUD-02`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q65 — Incumplimiento — profundidad de delegación excede perfil

- **Tipo:** `violation`
- **Qué valida / hace:** Comparar delegationDepth con D_delegation_max únicamente cuando el perfil esté configurado.
- **Requisitos relacionados:** `RNF-14`
- **Políticas relacionadas:** `P-AUD-04`, `P-OPS-01`
- **Criterio:** 0 filas; si D_delegation_max no está configurado, esta consulta no constituye evidencia y debe acompañarse de EXT-Q76.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q66 — Reporte de sesiones FL y payload

- **Tipo:** `report`
- **Qué valida / hace:** Distinguir flujo ascendente de gradientes y descendente de parámetros mejorados.
- **Requisitos relacionados:** `RF-21`, `RF-22`, `RF-23`, `RF-25`
- **Políticas relacionadas:** `P-FL-01`, `P-FL-06`, `P-FL-07`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **2 filas**.

#### EXT-Q67 — Incumplimiento — sesión FL ascendente no autorizada

- **Tipo:** `violation`
- **Qué valida / hace:** Para payload de gradientes exigir RangeGlobalAgg, propósito global y ausencia de datos personales/identificador persistente.
- **Requisitos relacionados:** `RF-21`, `RF-56`
- **Políticas relacionadas:** `P-FL-02`, `P-FL-03`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q68 — Incumplimiento — gradiente sin anonimización, ruido o mecanismo de privacidad

- **Tipo:** `violation`
- **Qué valida / hace:** Validar protección fuerte de cada ModelGradientUpdate saliente.
- **Requisitos relacionados:** `RF-57`, `RF-58`, `RNF-16`, `RNF-19`
- **Políticas relacionadas:** `P-FL-03`, `P-FL-05`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q69 — Privacidad diferencial y contabilidad epsilon

- **Tipo:** `report`
- **Qué valida / hace:** Auditar presupuesto por sesión, propósito y contrato, incluyendo cuenta acumulada cuando esté disponible.
- **Requisitos relacionados:** `RF-56`, `RF-59`, `RNF-18`
- **Políticas relacionadas:** `P-FL-04`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **2 filas**.


### EXT v3 — Auditoría, temporalidad, aceptación y validación

#### EXT-Q70 — Cadena completa de auditoría semántica

- **Tipo:** `report`
- **Qué valida / hace:** Reconstruir usuario→contrato→consentimiento efectivo→propósito→zona→política→nodo→alternativa→trust→tier→acción.
- **Requisitos relacionados:** `RF-67`, `RNF-30`
- **Políticas relacionadas:** `P-AUD-07`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **204 filas**.

#### EXT-Q71 — Incumplimiento — ticket de auditoría incompleto

- **Tipo:** `violation`
- **Qué valida / hace:** Aplicar contenido mínimo de P-AUD-06, incluyendo alternativas y políticas.
- **Requisitos relacionados:** `RF-54`, `RF-66`, `RNF-28`, `RNF-29`
- **Políticas relacionadas:** `P-AUD-06`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q72 — Incumplimiento — acción sin justificación de evaluación/política

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar acciones adaptativas no autorizadas por EvaluationState o evaluaciones sin política aplicada.
- **Requisitos relacionados:** `RF-65`, `RF-66`
- **Políticas relacionadas:** `P-AUD-05`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q73 — Reporte de entidades temporales

- **Tipo:** `report`
- **Qué valida / hace:** Inspeccionar validFrom/validTo y diferenciar cierre real de plannedExpiry.
- **Requisitos relacionados:** `RNF-35`, `RNF-36`
- **Políticas relacionadas:** `P-GOV-05`, `P-AUD-02`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **79 filas**.

#### EXT-Q74 — Incumplimiento — entidad temporal sin validFrom o intervalo inválido

- **Tipo:** `violation`
- **Qué valida / hace:** Detectar temporal entities sin inicio o con validTo anterior a validFrom.
- **Requisitos relacionados:** `RNF-36`
- **Políticas relacionadas:** `P-GOV-05`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q75 — Inventario de shapes SHACL v3

- **Tipo:** `inventory`
- **Qué valida / hace:** Listar shapes y severidades disponibles para validación estructural.
- **Requisitos relacionados:** `RF-71`, `RV-01`
- **Políticas relacionadas:** `P-VAL-03`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **74 filas**.

#### EXT-Q76 — Revisión — perfil de aceptación incompleto

- **Tipo:** `review`
- **Qué valida / hace:** Comprobar parámetros necesarios para interpretar RNF cuantitativos antes de una campaña de aceptación.
- **Requisitos relacionados:** `RNF-01`, `RNF-02`, `RNF-04`, `RNF-05`, `RNF-06`, `RNF-08`, `RNF-09`, `RNF-14`, `RNF-21`, `RNF-34`
- **Políticas relacionadas:** `P-OPS-01`, `P-VAL-03`
- **Criterio:** las filas requieren revisión; no equivalen automáticamente a incumplimiento.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **9 filas**.

#### EXT-Q77 — Revisión — preparación de campaña reproducible

- **Tipo:** `review`
- **Qué valida / hace:** Verificar artefactos/versiones y ValidationCampaign antes de interpretar consultas de incumplimiento.
- **Requisitos relacionados:** `RF-71`, `RF-72`, `RNF-39`, `RV-02`, `RV-03`
- **Políticas relacionadas:** `P-VAL-03`, `P-VAL-04`, `P-VAL-07`
- **Criterio:** las filas requieren revisión; no equivalen automáticamente a incumplimiento.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **6 filas**.

#### EXT-Q78 — Reporte de resolución de conflictos de políticas

- **Tipo:** `report`
- **Qué valida / hace:** Listar relaciones no triviales y estrategia de resolución asociada.
- **Requisitos relacionados:** `RNF-22`
- **Políticas relacionadas:** `P-GOV-03`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **37 filas**.

#### EXT-Q79 — Incumplimiento — relación conflictiva sin estrategia de resolución

- **Tipo:** `violation`
- **Qué valida / hace:** Exigir estrategia explícita para relaciones de conflicto/generalización/shadowing; DEP puede resolverse por orden y se informa aparte.
- **Requisitos relacionados:** `RNF-22`
- **Políticas relacionadas:** `P-GOV-03`
- **Criterio:** 0 filas.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **0 filas**.

#### EXT-Q80 — Dashboard global v3 de cobertura y deuda de migración

- **Tipo:** `dashboard`
- **Qué valida / hace:** Resumir cobertura estructural y elementos pendientes antes de aceptación científica.
- **Requisitos relacionados:** `RF-68`, `RF-71`, `RV-01`, `RV-05`
- **Políticas relacionadas:** `P-VAL-08`
- **Criterio:** inspección/cobertura; comparar con el artefacto y escenario versionados.
- **Resultado al ejecutarla sobre `smartcity_continuum_v3.0.0.ttl`:** **13 filas**.


## 6. Consultas prioritarias para aceptación científica

| Orden | Consulta | Motivo |
|---:|---|---|
| 1 | `EXT-Q01` | Verificar versión de ontología y artefactos versionados asociados. |
| 2 | `EXT-Q02` | Comprobar que los requisitos revisados están representados en la ontología. |
| 3 | `EXT-Q05` | Verificar el artefacto versionado de escenarios y su cobertura. |
| 4 | `EXT-Q13` | Detectar registros de consentimiento sin sujeto, rango, propósito, categorías autorizadas o validFrom. |
| 5 | `EXT-Q14` | Detectar contratos sin sujeto, rango, propósito, política o inicio de vigencia. |
| 6 | `EXT-Q19` | Comparar niveles de rango mediante orden explícito Denied=0, Local=1, Community=2, Global=3. |
| 7 | `EXT-Q20` | Detectar decisiones relevantes sin AuthorizationDecision concedida. |
| 8 | `EXT-Q22` | Detectar observaciones crudas enviadas a Edge/Fog/Cloud mediante sentToNode o TransferEvent. |
| 9 | `EXT-Q27` | Detectar transferencias a Edge/Fog/Cloud sin pseudónimo o identificador anónimo. |
| 10 | `EXT-Q30` | Detectar TransferEvent con dato sensible sin mecanismo que declare protectsInTransit=true. |
| 11 | `EXT-Q37` | Detectar tier Edge/Fog/Cloud seleccionado o TransferEvent externo asociado a evaluación/usuario en RestrictedZone. |
| 12 | `EXT-Q43` | Señalar trust histórico sin versión, ventana o evidencia suficiente. Los datos migrados pueden aparecer aquí hasta ser re-medidos. |
| 13 | `EXT-Q48` | Comprobar que latencia+privacidad+calidad=1 con tolerancia; trust se excluye. |
| 14 | `EXT-Q50` | Para AHPDecisionMethod exigir comparaciones, ratio, umbral y ratio≤umbral. |
| 15 | `EXT-Q53` | Detectar selectedAlternative ausente, no elegible o cuyo tier no coincide con selectedModelTier. |
| 16 | `EXT-Q56` | Detectar CloudModelTier cuando rango efectivo no sea global, zona sea restringida o autorización no esté concedida. |
| 17 | `EXT-Q64` | Exigir origen, destino, causa/estado disparador, validFrom y condición de recuperación; validTo puede faltar mientras esté activa. |
| 18 | `EXT-Q68` | Validar protección fuerte de cada ModelGradientUpdate saliente. |
| 19 | `EXT-Q69` | Auditar presupuesto por sesión, propósito y contrato, incluyendo cuenta acumulada cuando esté disponible. |
| 20 | `EXT-Q70` | Reconstruir usuario→contrato→consentimiento efectivo→propósito→zona→política→nodo→alternativa→trust→tier→acción. |
| 21 | `EXT-Q71` | Aplicar contenido mínimo de P-AUD-06, incluyendo alternativas y políticas. |
| 22 | `EXT-Q74` | Detectar temporal entities sin inicio o con validTo anterior a validFrom. |
| 23 | `EXT-Q76` | Comprobar parámetros necesarios para interpretar RNF cuantitativos antes de una campaña de aceptación. |
| 24 | `EXT-Q77` | Verificar artefactos/versiones y ValidationCampaign antes de interpretar consultas de incumplimiento. |
| 25 | `EXT-Q79` | Exigir estrategia explícita para relaciones de conflicto/generalización/shadowing; DEP puede resolverse por orden y se informa aparte. |
| 26 | `EXT-Q80` | Resumir cobertura estructural y elementos pendientes antes de aceptación científica. |

## 7. Trazabilidad resumida por requisito / tema

| Tema | Requisitos | Consultas principales |
|---|---|---|
| Dispositivos, nodos y contexto | `RF-01–RF-05` | `BASE-Q01–BASE-Q10, BASE-Q20, BASE-Q23, EXT-Q40–EXT-Q42` |
| Datos y transmisión | `RF-06–RF-10, RF-26–RF-30` | `BASE-Q10, EXT-Q22–EXT-Q35` |
| Modelos y selección | `RF-11–RF-15, RF-50–RF-55` | `BASE-Q04, BASE-Q21, EXT-Q46–EXT-Q58` |
| Adaptación/migración | `RF-16–RF-20` | `BASE-Q12–BASE-Q14, EXT-Q45, EXT-Q59–EXT-Q62` |
| FL y versionado | `RF-21–RF-25, RF-56–RF-59` | `BASE-Q16, BASE-Q24, EXT-Q57–EXT-Q58, EXT-Q66–EXT-Q69` |
| Consentimiento/contratos | `RF-32–RF-38` | `BASE-Q15, BASE-Q20, BASE-Q25, EXT-Q11–EXT-Q21` |
| Políticas y zonas | `RF-39–RF-44` | `EXT-Q03, EXT-Q06–EXT-Q10, EXT-Q36–EXT-Q39, EXT-Q78–EXT-Q79` |
| Trust | `RF-45–RF-49` | `BASE-Q07, BASE-Q19, EXT-Q40–EXT-Q45` |
| Pseudonimización | `RF-61` | `EXT-Q23, EXT-Q26–EXT-Q30` |
| Delegación/auditoría | `RF-62–RF-68` | `BASE-Q35, EXT-Q59, EXT-Q63–EXT-Q65, EXT-Q70–EXT-Q74, EXT-Q80` |
| SPARQL/reproducibilidad | `RF-69–RF-72, RV-01–RV-05` | `EXT-Q01–EXT-Q10, EXT-Q75–EXT-Q80` |
| RNF cuantitativos | `RNF-01–RNF-39` | `EXT-Q29–EXT-Q30, EXT-Q40–EXT-Q50, EXT-Q65, EXT-Q73–EXT-Q80` |

## 8. Deuda de datos heredados visible en v3.0.0

La ontología v3 conserva explícitamente algunos elementos heredados que **no deben ocultarse**: las 32 alternativas de decisión no tienen todavía puntuaciones por alternativa completas y los `TrustAssessment` migrados no conservan ventanas/evidencias históricas suficientes. Por ello `EXT-Q52` y `EXT-Q43` son consultas de `review`, no de `violation`. Del mismo modo, el perfil `AcceptanceProfile_v3_Draft` solo fija el valor que estaba determinado por los requisitos (`T_inference_local`); `EXT-Q76` enumera los umbrales aún pendientes. Hasta completar esos datos no debe declararse una campaña de aceptación científica final.

## 9. Compatibilidad con Fuseki y uso del fichero `.sparql`

Todas las consultas utilizan SPARQL 1.1 y prefijos explícitos. El fichero `.sparql` es un **catálogo de consultas independientes**, delimitadas por comentarios `START QUERY` / `END QUERY`; no debe enviarse entero como una única sentencia al endpoint. Para reproducibilidad, ejecutar cada bloque por separado sobre la misma versión de `smartcity_continuum_v3.0.0.ttl` y registrar la versión del catálogo de consultas junto con los demás artefactos de la campaña.
