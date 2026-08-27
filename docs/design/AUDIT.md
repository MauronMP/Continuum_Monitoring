# Auditoría de ontología, consultas y políticas v3.0.0

## Resultado

La migración modular contiene 7.938 triples lógicos, 115 consultas (103 core y
12 de dominio), 16 categorías, 72 RF, 39 RNF, 5 RV, 79 políticas, 55 mecanismos
y 17 escenarios. El catálogo enlaza cada consulta con finalidad, requisitos,
políticas, resultado de referencia, autoridad, privacidad y estrategia de
fusión.

La puerta estructural valida Turtle, inventarios, SPARQL, SHACL, ausencia de
`owl:Nothing`, privacidad y reconstrucción distribuida. Jena, RDF4J y
RDFLib/OWL-RL cubren RDFS; Oxigraph es control SPARQL sin inferencia.

## Cambios aplicados

| Hallazgo | Cambio v3 |
|---|---|
| Fuente monolítica difícil de desplegar | 13 artefactos derivados, módulo de despliegue del benchmark y perfiles de placement |
| 115 consultas en una batería única | Un `.rq` por consulta y catálogo generado |
| Trazabilidad documental no ejecutable | RF/RNF/RV y políticas se validan contra IDs RDF |
| Routing únicamente por categoría | Alcance por consulta: cloud, fog, edges o edge concreto |
| Bnodes OWL/SHACL se duplicaban entre nodos | Skolemización determinista al modularizar |
| Datos personales podían ascender por enlaces | Propiedad por autoridad y proyecciones allowlist |
| Agregados federados no componibles | Autoridad única para agregados; unión solo para resultados componibles |
| Variantes numéricas RDFS producían falsos desacuerdos | Conjunto canónico de bindings y normalización numérica |
| Shapes `xsd:string` rechazaban textos `@es` | `sh:or` para string/rdf:langString y rango `rdfs:Literal` |
| Generador aún emitía consentimiento binario v2 | ABox sintético v3 con ConsentRecord, pseudónimo, contrato, autorización y DataContext |
| `EXT-Q25` combinaba OPTIONAL, OR correlacionado y tipos abiertos | Reescritura estándar con VALUES, UNION y anti-joins acotados |
| Workers antiguos podían mezclarse con v3 | Protocolo v5 con versión 3.0.0 y 115 consultas en `/health` |

## Estado de aceptación

SHACL no presenta violaciones; conserva 57 advertencias de migración relativas a
parámetros de aceptación, puntuaciones AHP, ventanas de confianza y fechas. Las
consultas `EXT-Q76` y `EXT-Q77` confirman que el perfil y la campaña aún no están
completos. Por ello la validación estructural puede ser correcta, pero
`scientific_acceptance.ready` y `compliance_claim_permitted` permanecen falsos.

Este comportamiento es intencionado: una consulta `violation` vacía no se usa
como certificado sin superar primero `EXT-Q01`, `EXT-Q02`, `EXT-Q05`, `EXT-Q76`
y `EXT-Q77`.

## Cobertura de trazabilidad pendiente

La batería suministrada referencia 102 de los 116 requisitos (87,93 %) y 69 de
las 79 políticas (87,34 %). Los 14 requisitos y 10 políticas restantes están
declarados y son válidos, pero no tienen una consulta asociada en los metadatos
v3 recibidos. `validate` publica las listas exactas como
`unreferenced_requirements` y `unreferenced_policies`; no las convierte en un
fallo estructural ni permite afirmar cobertura SPARQL del 100 %.

## Decisiones y límites

- OWL/RDFS representa conocimiento abierto; SHACL y consultas `violation`
  comprueban restricciones cerradas.
- El namespace `example.org` debe migrarse a una URI persistente antes de
  publicar la ontología como estándar externo.
- La fragmentación implementada es authority-aware con TBox local, no un
  endpoint SPARQL Federation genérico.
- Las métricas de coste son proxies de tiempo/recursos; no sustituyen energía o
  coste monetario medido.
- Los resultados v2.x son históricos y no deben combinarse estadísticamente con
  corridas v3.0.0.
- La eliminación de artefactos v2 del árbol de trabajo no corrige esta deuda:
  para cerrarla hay que diseñar y versionar nuevas consultas en la fuente v3.
