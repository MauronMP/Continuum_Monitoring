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
| Pytest acumulativo | RDFS, temporal, 14 etapas | Contrato rápido del pipeline acumulativo |
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
4. decision;
5. consent;
6. contract_compliance;
7. access_control;
8. policy;
9. migration;
10. delegation;
11. federation;
12. privacy;
13. context;
14. wellbeing.

La etapa final ejecuta las 69 consultas. Esto mide el coste de ampliar la
cobertura funcional, no el crecimiento del volumen RDF.

## Experimento de escalabilidad

Para cada tamaño configurado se parte de la misma ontología de referencia y se
añade un bloque ABox determinista. Cada usuario sintético incorpora usuario,
wearable, estados temporales, observación, contrato y relación usuario-nodo. Se
añaden nodos Edge a razón de uno por cada cien usuarios.

Cada razonador recibe una copia idéntica del grafo y ejecuta las 69 consultas.
Los volúmenes, repeticiones y semilla están en `configs/benchmark.toml`.

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
