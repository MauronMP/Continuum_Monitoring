# Validez científica y límites

## Dictamen

La batería es una infraestructura reproducible de validación y rendimiento, no
un estándar ni una certificación formal de la ontología. Cumple patrones
metodológicos reconocibles: datos sintéticos deterministas y escalables,
workload SPARQL explícito, varias métricas, resultados por repetición,
metadatos, validación SHACL y comprobación de equivalencia entre despliegues.
La puerta de calidad distingue `structural validity` de `scientific
acceptance`: la primera puede pasar aunque el perfil/campaña documentados por
`EXT-Q76` y `EXT-Q77` sigan incompletos.

La validación combina aspectos distintos:

1. sintaxis y carga RDF/Turtle;
2. inferencia RDFS/OWL RL y detección de `owl:Nothing`;
3. restricciones cerradas SHACL y consultas de incumplimiento;
4. competencia funcional mediante 115 consultas trazadas a requisitos y políticas;
5. rendimiento acumulativo y por volumen;
6. equivalencia de resultados monolito/Docker;
7. validación cruzada con Apache Jena, Eclipse RDF4J y RDFLib/OWL-RL bajo
   RDFS, más Oxigraph como control sin inferencia.

Esto está alineado conceptualmente con:

- LUBM: generador sintético escalable, workload fijo y múltiples métricas;
- SP²Bench: workload SPARQL reproducible;
- WatDiv: necesidad de diversidad estructural y de selectividad;
- HOBBIT: separación entre sistema, benchmark, evaluación y resultados
  reproducibles;
- estándares W3C RDF 1.1, SPARQL 1.1, OWL 2 RL y SHACL.

## Qué falta para sostener una evaluación de artículo

- La limitación de un único producto para RDFS queda mitigada con tres
  implementaciones independientes. Los perfiles OWL RL y RDFS+OWL RL continúan
  usando OWL-RL/RDFLib; todavía no hay una comparación multiproducto de OWL 2
  RL.
- Tres repeticiones sirven como control básico, pero son pocas para inferencia
  estadística. El benchmark multimotor descarta un warm-up por defecto; el
  artículo debe justificar tanto `n` como el número de warm-ups y reportar
  dispersión.
- El benchmark de carga registra CPU de proceso, RSS actual/máxima, E/S de
  proceso, bytes útiles HTTP, timeouts y pérdidas. Estas no sustituyen energía,
  temperatura, métricas completas de host/cgroup ni tráfico de enlace.
- Falta clasificar las consultas por forma y selectividad al estilo WatDiv:
  estrella, cadena, copo de nieve, OPTIONAL/UNION, agregación y cardinalidad.
- El generador escala el ABox de usuarios, dispositivos, estados y contratos,
  triples exactos y reglas sintéticas con factores independientes, pero no
  todas las poblaciones de la ontología por separado.
- Deben publicarse hardware, SO, versiones, límites de contenedor, carga de
  fondo, protocolo de caché y datos/semillas.
- El namespace `example.org` debe sustituirse por una URI persistente antes de
  publicar la ontología como artefacto estable.
- El ABox v3 actual conserva 57 advertencias SHACL y no satisface todavía las
  precondiciones de aceptación de `EXT-Q76`/`EXT-Q77`. No debe afirmarse
  certificación de cumplimiento hasta completar esos artefactos.
- Docker y físico ofrecen un baseline replicado y un layout híbrido: ABox por
  autoridad, núcleo TBox local y perfiles que omiten wellbeing en fog y shapes
  en fog/edge. No es un endpoint SPARQL 1.1 Federation genérico.
- Los cierres denominados RDFS no materializan necesariamente los mismos
  triples axiomáticos o de datatype. Por eso la decisión funcional
  cero/no-cero o `ASK` sigue siendo el criterio de conformidad multimotor. La
  equivalencia entre arquitecturas RDFLib usa además un digest exacto,
  independiente del orden sobre el conjunto canónico de bindings.
- La trazabilidad directa no cubre todo el inventario normativo: 102/116
  requisitos y 69/79 políticas aparecen en al menos una consulta. Los IDs no
  cubiertos se publican en la salida de `validate`; hasta ampliar la batería no
  debe afirmarse una cobertura SPARQL del 100 %.
- El smoke de una repetición es una prueba de integración. No es una muestra
  suficiente para concluir superioridad, equivalencia temporal o eficiencia
  energética entre arquitecturas.
- Los timeouts son observaciones censuradas. Las figuras que solo agregan
  corridas completas deben acompañarse de la tabla/tasa de timeouts; eliminarlos
  silenciosamente sesga el resultado a favor de la arquitectura que más falla.

## Interpretación de las figuras

Las figuras de publicación usan mediana y rango mínimo-máximo de las
repeticiones disponibles. El rango es descriptivo y no debe denominarse
intervalo de confianza. Para un artículo se recomienda aumentar repeticiones y
predefinir el análisis estadístico antes de recoger la corrida definitiva.

La unidad experimental debe ser una repetición completa del mismo release,
dataset lógico, razonador y conjunto de consultas. No son comparables entre sí
los CSV v2/v3, un control sin inferencia y un razonador RDFS, ni una réplica
completa y un fragmento de autoridad sin declarar ese factor.

## Referencias primarias

- W3C, RDF 1.1 Concepts: https://www.w3.org/TR/rdf11-concepts/
- W3C, SPARQL 1.1 Query: https://www.w3.org/TR/sparql11-query/
- W3C, OWL 2 Profiles: https://www.w3.org/TR/owl2-profiles/
- W3C, SHACL: https://www.w3.org/TR/shacl/
- Guo, Pan y Heflin, LUBM:
  https://swat.cse.lehigh.edu/pubs/guo05a.pdf
- Schmidt et al., SP²Bench: https://arxiv.org/abs/0806.4627
- Aluç et al., WatDiv:
  https://olafhartig.de/files/AlucEtAl_ISWC14_Preprint.pdf
- Röder et al., HOBBIT:
  https://journals.sagepub.com/doi/10.3233/DS-190021
