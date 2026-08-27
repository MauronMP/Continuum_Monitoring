# Metodología de benchmarks

## Razonadores

Se comparan tres perfiles de inferencia reproducibles, todos proporcionados por
OWL-RL sobre RDFLib:

1. `rdfs`: cierre RDFS.
2. `owlrl`: reglas OWL 2 RL.
3. `rdfs_owlrl`: cierre combinado RDFS + OWL 2 RL.

Son tres semánticas de razonamiento distintas dentro de un mismo producto. Esta
precisión es importante al interpretar los resultados.

Como experimento complementario, `continuum-bench engines` ejecuta el perfil
RDFS en tres implementaciones independientes: Apache Jena, Eclipse RDF4J y
RDFLib/OWL-RL. Oxigraph proporciona una línea base SPARQL sin inferencia. La
metodología y la validación cruzada se detallan en
`docs/design/ENGINE_BENCHMARKS.md`.

Se mide por separado:

- generación sintética;
- razonamiento/materialización;
- ejecución SPARQL;
- total;
- media y p95 por consulta;
- triples inferidos;
- throughput de consultas.

La ejecución emite progreso en tiempo real. El acumulativo informa de categoría,
etapa, consultas acumuladas, repetición y razonador. Escalabilidad informa de
bloque, usuarios sintéticos, triples, repetición y razonador. Los mensajes se
escriben con vaciado inmediato para que sigan siendo visibles en procesos largos.

## Perfiles de ejecución

| Nivel | Configuración | Propósito |
|---|---|---|
| Pytest acumulativo | RDFS, temporal, 16 etapas | Contrato rápido del pipeline acumulativo |
| Pytest escalabilidad | RDFS, 2/4 usuarios | Contrato rápido del crecimiento sintético |
| Smoke acumulativo | 3 razonadores, 1 repetición | Medición rápida de todas las categorías |
| Smoke escalabilidad | 3 razonadores, 5/25 usuarios, 1 repetición | Medición rápida de crecimiento |
| Benchmark completo | 3 razonadores, 10/100/500/1.000/2.500/5.000 usuarios, 3 repeticiones | Resultados comparables |
| Smoke multimotor | 3 RDFS + 1 control, 5/25 usuarios, 1 repetición | Integración entre productos |
| Benchmark multimotor | 3 RDFS + 1 control, 10/100/500/1.000/2.500/5.000 usuarios, 3 repeticiones | Comparación de productos |

Los comandos y el contenido exacto de cada prueba están documentados en
`docs/design/TESTS.md`.

## Experimento acumulativo

Usa el grafo de referencia constante. En cada etapa añade una categoría y ejecuta
todas las consultas acumuladas:

1. topology;
2. semantic_schema;
3. observability;
4. identity_consent;
5. data_lifecycle;
6. security_identity;
7. context_zones;
8. trust;
9. decision;
10. policy_governance;
11. adaptation;
12. delegation;
13. federation;
14. audit_temporal;
15. validation;
16. wellbeing.

La etapa final ejecuta las 115 consultas. Esto mide el coste de ampliar la
cobertura funcional, no el crecimiento del volumen RDF.

## Experimento de escalabilidad

Para cada tamaño configurado se parte de la misma ontología de referencia y se
añade un bloque ABox determinista. Cada usuario sintético incorpora usuario,
pseudónimo, consentimiento v3, wearable, estados temporales, observación, dato
parametrizado con contexto, contrato, autorización y relación usuario-nodo. Se
añaden nodos Edge a razón de uno por cada cien usuarios.

Cada razonador recibe una copia idéntica del grafo y ejecuta las 115 consultas.
Los volúmenes, repeticiones y semilla están en `configs/benchmark.toml`.

Los puntos son tamaños totales independientes. Por ejemplo, el punto de 500
usuarios no reutiliza el cierre ni el grafo materializado para 100: se clona el
grafo base y se generan exactamente 500 usuarios con la misma semilla. Esto
evita que el orden de los bloques convierta caché o estado incremental en una
ventaja experimental no declarada.

El benchmark básico mide p95 y throughput de consultas. El experimento
multidimensional `continuum-bench load` es el que añade p50/p99, eventos/s,
pérdidas, CPU, memoria, disco, red, exactitud de alertas, recuperación y
timeouts. No se deben atribuir estas métricas al acumulativo/escalabilidad
básicos si no aparecen en sus CSV.

## Reproducibilidad y lectura

Los CSV conservan cada repetición y cada consulta. Las gráficas usan la mediana
entre repeticiones. `metadata.json` registra versión de Python, plataforma,
semilla, razonadores, número de triples y SHA-256 del grafo base.

No deben interpretarse ejecuciones de una sola repetición como resultados
científicos definitivos. Las tres repeticiones del perfil completo permiten
detectar variabilidad básica, pero para publicación debe fijarse y justificarse
un número mayor, registrar calentamiento y ejecuciones frías/calientes, controlar
la carga y afinidad de CPU y reportar memoria máxima además de tiempo.

`continuum-bench plot publication` genera PNG a 300 dpi, PDF y SVG. Las figuras
representan mediana y rango completo de repeticiones; no presentan el rango como
intervalo de confianza.

## Comparabilidad y límites

- Solo se comparan salidas cuyo `metadata.json` declare ontología 3.0.0,
  contrato de 115 consultas y artefacto de políticas vigente; los informes
  rechazan resultados 2.x o metadatos incompletos.
- RDFS, OWL RL y RDFS+OWL RL son perfiles semánticos distintos, no réplicas de
  una misma condición. Jena/RDF4J/RDFLib son la comparación RDFS entre
  productos; Oxigraph es control SPARQL sin inferencia.
- El tiempo local incluye generación, materialización y consulta según las
  columnas separadas del CSV. Los tiempos distribuidos usan pared de preparación
  y consulta; calibración, oráculo y validación se registran fuera del intervalo.
- Un speedup distribuido solo es válido para el mismo dataset lógico y resultado
  canónico. Más nodos pueden empeorar el tiempo si dominan materialización,
  serialización, HTTP, sincronización o el nodo más lento.
- Tres repeticiones son el mínimo operativo de este proyecto, no una garantía
  universal de potencia estadística. Para publicación deben justificarse N,
  orden aleatorio/contrabalanceado, warm-ups, estado térmico y tratamiento de
  outliers/timeouts.
