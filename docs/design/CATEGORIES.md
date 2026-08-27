# Taxonomía v3 de consultas

La batería se clasifica con dos ejes independientes:

- `tier=core`: capacidad reutilizable para monitorizar cualquier sistema del
  continuum;
- `tier=domain`: consulta dependiente del perfil temático instalado, actualmente
  bienestar;
- `category`: responsabilidad funcional dentro del ciclo de monitorización,
  gobierno, decisión y validación.

Los IDs `BASE-Qxx` y `EXT-Qxx` se conservan por trazabilidad documental. No
determinan el `tier`.

## Categorías y tamaño

| Orden | Categoría | Total | Core | Domain | Responsabilidad |
|---:|---|---:|---:|---:|---|
| 1 | topology | 4 | 4 | 0 | nodos, tiers y relaciones del continuum |
| 2 | semantic_schema | 4 | 4 | 0 | versión, artefactos, requisitos y esquema |
| 3 | observability | 5 | 4 | 1 | estado, carga, disponibilidad y métricas |
| 4 | identity_consent | 18 | 16 | 2 | identidades, consentimiento, contratos y autorización |
| 5 | data_lifecycle | 8 | 7 | 1 | transferencia, buffer, retención e idempotencia |
| 6 | security_identity | 6 | 5 | 1 | cifrado, pseudonimización y exposición de datos |
| 7 | context_zones | 6 | 3 | 3 | contexto, movilidad, zona y georrestricción |
| 8 | trust | 6 | 6 | 0 | confianza dinámica, ventana y reproducibilidad |
| 9 | decision | 17 | 16 | 1 | alternativas, AHP, selección y consistencia |
| 10 | policy_governance | 8 | 8 | 0 | políticas, mecanismos, precedencia y conflictos |
| 11 | adaptation | 8 | 8 | 0 | migración, offloading, degradación y rollback |
| 12 | delegation | 5 | 5 | 0 | delegación temporal, profundidad y cierre |
| 13 | federation | 7 | 7 | 0 | sesiones FL, participantes, gradientes y privacidad |
| 14 | audit_temporal | 5 | 5 | 0 | causalidad, temporalidad y auditoría MAPE-K |
| 15 | validation | 4 | 4 | 0 | perfiles de aceptación y campañas científicas |
| 16 | wellbeing | 4 | 1 | 3 | wearables, fisiología, sueño y estrés |

Total: 115 consultas, 103 `core` y 12 `domain`. La distribución por tipo es 51
`report`, 32 `violation`, 14 `inventory`, 8 `review`, 5 `ask` y 5 `dashboard`.

## Criterio de separación

La división v3 sigue fronteras de autoridad y de cambio, no busca igualar el
número de consultas. Por ejemplo, `identity_consent` es deliberadamente amplio
porque representa una sola cadena de autorización efectiva; dividirla impediría
observar su coste acumulado completo. `validation` permanece independiente para
no mezclar preparación científica con cumplimiento operativo.

Para estudiar complejidad SPARQL debe añadirse otro eje experimental —forma del
grafo de consulta, selectividad, OPTIONAL/UNION, agregación y cardinalidad— sin
reclasificar artificialmente las responsabilidades funcionales.
