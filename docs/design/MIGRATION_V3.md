# Migración y contrato de release v3.0.0

## Fuentes canónicas

La release se deriva de estos artefactos versionados:

| Artefacto | Ruta |
|---|---|
| Ontología monolítica v3 | `ontology/legacy/smartcity_continuum-v3.0.0.ttl` |
| Batería SPARQL v3 | `queries/legacy/sparql_battery-v3.0.0.sparql` |
| Requisitos | `docs/reference/RN_RNF.md` |
| Políticas y mecanismos | `docs/reference/Políticas.md` |
| Documentación ontológica | `docs/reference/Documentacion_Ontologia.md` |
| Documentación de consultas | `docs/reference/Consultas_Sparql.md` |

`tools/migrate_assets.py` es el transformador reproducible. Genera módulos,
perfiles, shapes, 115 ficheros `.rq`, catálogo y plan de ejecución. No edite un
artefacto generado sin trasladar el cambio a la fuente o al transformador.

```bash
.venv/bin/python tools/migrate_assets.py
.venv/bin/python -m continuum_bench validate
.venv/bin/python -m pytest
```

## Contrato verificable

- `owl:versionInfo = 3.0.0`;
- consultas `BASE-Q01–BASE-Q35` y `EXT-Q01–EXT-Q80`;
- 72 requisitos funcionales, 39 no funcionales y 5 de validación;
- 79 políticas, 55 mecanismos, 17 escenarios y 12 categorías de política;
- metadatos de finalidad, RF/RNF/RV y políticas para las 115 consultas;
- plan `queries/execution-plan.toml` v3.0.0 completo y sin IDs duplicados;
- reconstrucción isomorfa del monolito y equivalencia de las 115 consultas bajo
  la fragmentación por autoridad.

La trazabilidad no debe confundirse con cobertura total: las consultas recibidas
referencian 102/116 requisitos y 69/79 políticas. La validación informa de los
14 y 10 IDs no cubiertos, respectivamente, sin inventar asociaciones que no
aparecen en los documentos fuente.

## Correcciones locales sobre la fuente recibida

Las formas de `mechanismDescription` y `hasPolicyStatement` exigían
`xsd:string`, aunque sus 134 valores eran `rdf:langString` con `@es`. Se
actualizó la fuente a una disyunción SHACL válida y los rangos a `rdfs:Literal`.
Esto elimina 134 violaciones sin borrar el idioma.

Los módulos generados skolemizan estructuras anónimas con IRIs estables de la
forma `urn:continuum:ontology:3.0.0:node:*`. Es una transformación de identidad
RDF necesaria para que cinco fragmentos no creen cinco copias distintas de cada
lista/shape anónima.

El generador sintético dejó de emitir `hasConsent`, `ConsentGiven` y políticas
v2 inexistentes. Cada usuario sintético incorpora ahora identificador
pseudónimo, `ConsentRecord`, `SemanticContract`, `AuthorizationDecision`,
`DataContext` y dato parametrizado; los nodos incluyen `TrustAssessment`
versionado. El conjunto generado pasa SHACL y las 32 consultas `violation`.

`EXT-Q25` se reescribió sin cambiar su resultado de referencia: usa tipos
acotados con `VALUES` y dos ramas `UNION` con `FILTER NOT EXISTS`, en vez de un
`OPTIONAL` seguido de un OR correlacionado. Esto evita el producto intermedio
que dominaba los tiempos RDFS/OWL-RL al crecer el ABox.

## Compatibilidad de resultados

Los directorios `outputs` producidos con v2.x no son comparables con v3.0.0:
cambiaron ontología, ABox, número de consultas, categorías y contrato del worker.
Archive o use otro directorio de salida antes de una campaña v3. El worker
publica protocolo v5, versión ontológica y número de consultas; coordinadores
Docker/físicos rechazan una imagen o despliegue anterior.

También se exige `reasoning_contract=rdfs-literal-value-space-v1` en los
metadatos de resultados y la salud de los workers. La primera implementación
v3 heredaba una sustitución incorrecta de booleanos por enteros del cierre
RDFS de OWL-RL, visible en EXT-Q68. El adaptador compartido la corrige sin
modificar la ontología ni la consulta. Las corridas v3 previas deben repetirse;
no basta con renombrarlas o añadir el campo a sus metadatos. Reconstruya Docker
y redespliegue/reinicie los workers físicos antes de repetir las mediciones.
Véanse el [detalle semántico](ENGINE_BENCHMARKS.md#corrección-rdfs-de-literales-y-ext-q68)
y los [comandos Docker](DOCKER_BENCHMARKS.md#actualización-tras-el-fallo-ext-q68).

## Deuda explícita de aceptación

La integridad estructural no equivale a una certificación científica. El ABox
v3 mantiene 57 advertencias SHACL y resultados de revisión en `EXT-Q76` y
`EXT-Q77`: faltan parámetros del perfil de aceptación y una campaña completa.
Hasta resolverlos, `scientific_acceptance.ready=false` y
`compliance_claim_permitted=false`, aunque `validate` indique `ok=true`.
