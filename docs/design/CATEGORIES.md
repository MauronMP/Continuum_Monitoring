# Taxonomía de consultas

La clasificación usa dos ejes independientes:

- `tier`: `core` para capacidades reutilizables en cualquier sistema del
  continuum y `domain` para términos del tema instalado, actualmente wellbeing;
- `category`: función que ejerce la consulta dentro del sistema.

Los IDs históricos `BASE-Qxx` y `EXT-Qxx` se conservan solo por trazabilidad.
No determinan el eje `tier`.

## Categorías

| Orden | Categoría | Consultas | Responsabilidad |
|---:|---|---:|---|
| 1 | topology | 6 | nodos, modelos, cobertura y relaciones físicas/lógicas |
| 2 | semantic_schema | 2 | inventario de vocabulario y shapes |
| 3 | observability | 7 | estado, carga, conexión, disponibilidad y confianza |
| 4 | decision | 6 | elegibilidad, evaluación, AHP y resumen de cumplimiento |
| 5 | consent | 4 | estado y rango de consentimiento |
| 6 | contract_compliance | 7 | contratos semánticos y sus violaciones |
| 7 | access_control | 5 | roles, permisos y autorización |
| 8 | policy | 7 | inventario, integridad, gobierno y auditoría de políticas |
| 9 | migration | 8 | fallos, degradación, destino y decisión de migración |
| 10 | delegation | 5 | cadena, profundidad, ciclo y validez de delegaciones |
| 11 | federation | 3 | sesiones, participantes y contribuciones federadas |
| 12 | privacy | 3 | clipping, ruido y presupuesto diferencial |
| 13 | context | 2 | contexto urbano que condiciona la decisión |
| 14 | wellbeing | 4 | observaciones fisiológicas, sueño y estrés |

Total: 69 consultas. El catálogo contiene 60 `core` y 9 `domain`.

## Por qué se hizo la subdivisión

Las siete categorías iniciales mezclaban funciones distintas y producían saltos
acumulativos muy grandes. Una revisión intermedia de doce categorías todavía
incluía RBAC e inventario SHACL dentro de `topology`, y contratos dentro de
`consent`. La versión de catorce categorías separa:

- esquema semántico de topología operativa;
- consentimiento declarado de cumplimiento contractual;
- control de acceso de inventario físico;
- migración de la semántica de delegación.

Los grupos tienen entre 2 y 8 consultas. No se subdividen más `context`,
`semantic_schema`, `privacy` o `federation` porque quedarían categorías de una
sola consulta, poco útiles como etapa experimental. Para estudiar complejidad
SPARQL debe añadirse un eje distinto —forma de consulta, selectividad y
cardinalidad— y no seguir fragmentando la taxonomía funcional.
