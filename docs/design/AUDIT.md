# Auditoría de ontología, consultas y políticas

## Resultado

La versión modular 2.3 queda validada con 69 consultas, SHACL, tres perfiles semánticos y
tres implementaciones RDFS independientes: Jena, RDF4J y RDFLib/OWL-RL.
Oxigraph actúa como control SPARQL sin inferencia. Los documentos conservan
trazabilidad completa de RF-01..RF-71, RNF-01..RNF-75, P-01..P-84 y M-01..M-50.

## Problemas corregidos

| Hallazgo | Cambio |
|---|---|
| TBox, ABox, shapes y dominio estaban en un único TTL | Separación en núcleo, vocabularios, perfil de bienestar, shapes y ejemplos |
| 69 consultas en un fichero difícil de mantener | Un `.rq` por consulta y catálogo validado |
| Clasificación histórica BASE/EXT no distinguía núcleo y tema | Nueva clasificación ortogonal `core/domain` y catorce categorías funcionales |
| Tres `ServiceState` incumplían RNF-67 por no tener `validFrom` | Se añadieron marcas temporales |
| `NodeState_S2_Edge1` no estaba enlazado al nodo y activaba EXT-Q32 | Se añadió `EdgeNode1 hasNodeState NodeState_S2_Edge1` |
| Requisitos usaban ocho nombres distintos de los implementados | Documentación alineada con las propiedades canónicas |
| Pesos AHP mezclaban normalización de tres y cuatro criterios | Los cuatro pesos suman 1 y EXT-Q21 lo verifica |
| Solo había una shape de privacidad FL | Shapes para temporalidad, contratos, políticas, trust, AHP, auditoría, delegación y gradientes |
| No existía ejecución reproducible | CLI, configuraciones, semilla, CSV, hashes y gráficas |
| Los perfiles dependían de una única implementación | Comparación automática con Jena, RDF4J, RDFLib/OWL-RL y control Oxigraph |
| El continuum replicaba grafo y shapes completos | Placement híbrido por rol y fragmentación ABox por autoridad |
| La equivalencia distribuida solo comparaba cardinalidad | Digest exacto del bag de bindings y tratamiento seguro de agregaciones |
| Las relaciones hacia objetos privados podían replicarse | Cierre de autoridad por sujeto/objeto y proyecciones mediante allowlist |

## Decisiones de modelado

- OWL/RDFS se usa para inferencia de mundo abierto.
- SHACL y consultas `violation_*` se usan para cumplimiento de mundo cerrado.
- Los IDs BASE/EXT permanecen por compatibilidad documental; no son la nueva
  arquitectura de categorías.
- `http://example.org/smartcity#` se conserva para no romper todos los datos y
  consumidores existentes. Antes de publicar la ontología como estándar externo
  debe reservarse una URI persistente y publicar una migración `owl:equivalent*`
  versionada.
- El consentimiento binario se mantiene solo como compatibilidad; las decisiones
  nuevas se basan en `SemanticContract` y `ConsentRange`.

## Riesgos que deben medirse en fases posteriores

- consumo energético, temperatura y coste monetario;
- memoria/CPU del host y cgroup, además de la telemetría de proceso disponible;
- diferencias entre materialización previa y razonamiento del endpoint;
- consistencia de reloj entre máquinas;
- equivalencia de límites entre contenedores y equipos físicos;
- persistencia, índices y calentamiento de caché.
