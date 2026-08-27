# Arquitectura del proyecto

## Separación semántica

La ontología anterior mezclaba TBox, vocabularios, shapes, individuos de ejemplo
y conceptos del dominio de bienestar en un único fichero. La versión 3.0.0 usa:

```text
core/schema + core/vocabulary
        │
        ├── modules (foundation, topology, observability, governance,
        │            orchestration, federation y deployment)
        ├── shapes (cumplimiento cerrado)
        ├── examples (escenarios de referencia)
        └── domains/wellbeing (extensión opcional)
```

El núcleo modela cualquier sistema desplegado a lo largo del continuum:
infraestructura, telemetría, estados temporales, decisiones MAPE-K, políticas,
contratos, consentimiento, confianza, AHP, privacidad y delegación. El perfil de
bienestar aporta los tipos de wearable, sensores fisiológicos, sueño y estrés.

Los imports OWL se documentan en los módulos, pero el cargador usa una lista
explícita de ficheros. Así no depende de acceso a red ni de la resolución de
imports durante un experimento.

## Consultas

`queries/catalog.csv` es la fuente de verdad. Cada fila declara:

- ID estable;
- `tier`: `core` o `domain`;
- categoría acumulativa;
- tipo: inspección, ASK, reporte, advertencia o incumplimiento;
- expectativa verificable;
- cardinalidad o resultado ASK del ABox de referencia;
- finalidad y trazabilidad hacia RF/RNF/RV y políticas;
- ruta al fichero `.rq`.

El cargador rechaza IDs duplicados, ficheros ausentes o categorías no declaradas.
Esto impide que una consulta quede accidentalmente fuera de los experimentos.

## Componentes Python

- `ontology.py`: carga, hash reproducible y SHACL.
- `reasoners.py`: adaptadores de materialización.
- `queries.py`: catálogo y ejecución SPARQL.
- `synthetic.py`: ABox determinista y conforme.
- `benchmark.py`: experimentos acumulativo y de escalabilidad.
- `engines.py`: coordinador de productos RDF independientes y equivalencia.
- `external_node.py`: servicios HTTP para RDFLib y Oxigraph.
- `distributed.py`: coordinador del despliegue cloud/fog/edge.
- `partitioning.py`: fragmentación determinista del ABox por autoridad.
- `sharded.py`: selección de fuentes y fusión de resultados particionados.
- `physical.py`: planificación adaptativa sobre cinco equipos.
- `compare.py`: comparación del monolito con resultados replicados o
  particionados.
- `reporting.py`: informe conjunto de las arquitecturas disponibles.
- `plotting.py`: gráficas no interactivas.
- `validation.py`: puerta de calidad.
- `cli.py`: interfaz estable para ejecución local y futura orquestación.

## Servicios semánticos y despliegue

`engine-service` implementa en Java el mismo contrato HTTP para Apache Jena y
Eclipse RDF4J. `docker-compose.engines.yml` levanta esos adaptadores junto con
RDFLib y Oxigraph. Todos reciben el mismo N-Triples y el mismo texto SPARQL; el
coordinador no traduce las consultas por producto.

`docker-compose.yml` es un experimento distinto: cinco réplicas funcionales
cloud/fog/edge para medir reparto de consultas. No debe confundirse la dimensión
de producto semántico con la dimensión de topología de despliegue.

## Modos de distribución

| Modo | Comando | Datos por nodo | Planificación |
|---|---|---|---|
| Monolito | `benchmark` | grafo completo local | secuencial |
| Docker replicado | `docker --layout replicated` | cinco réplicas completas | afinidad por categoría |
| Docker particionado | `docker` | ABox por autoridad + perfiles | `execution-plan.toml` |
| Físico replicado | `physical --layout replicated` | cinco réplicas completas | calibración LPT heterogénea |
| Físico particionado | `physical` | ABox por autoridad + perfiles | `execution-plan.toml` |

En el modo particionado, el ABox sensible pertenece a los edges y cloud/fog
reciben proyecciones o resúmenes. Las consultas `edges` y `cloud_edges` se
ejecutan en varias fuentes y se fusionan mediante `set_union` o `boolean_or`.
Las agregaciones no se fusionan de forma aproximada: `BASE-Q33` se dirige a
`edge2`, propietario de la proyección Mist completa, con estrategia `single`.
Los alcances `edge1`, `edge2` y `edge3` expresan autoridad concreta; `edges`
conserva la unión federada de los tres propietarios.

`configs/ontology-placement.toml` replica el núcleo inmutable necesario para
razonar localmente, omite el dominio wellbeing en fog y coloca los shapes solo
en cloud. Es un placement híbrido de perfiles y ABox, no una federación de TBox
con resolución remota de imports. Los informes
separan `logical_input_triples`, `aggregate_fragment_triples`,
`max_fragment_triples` y `storage_replication_factor` para que esta replicación
no quede oculta.

Los despliegues físicos reutilizan el mismo contrato HTTP y el inventario
`configs/physical-nodes.toml`. Los IDs de consulta y la generación determinista
permanecen estables para poder contrastar cada resultado con el oráculo
monolítico.

## Límites de equivalencia

Los resultados nuevos incluyen un digest independiente del orden sobre el
conjunto canónico SPARQL; la comparación exige digest, cardinalidad y ASK
cuando ambos lados lo ofrecen. Para CSV históricos sin digest aplica el fallback
`cardinality_ask` y lo marca en `validation_level`. Ninguno de los dos niveles
constituye por sí solo una certificación formal de federación RDF o de la
reescritura algebraica de agregados.

La fuente v3 se skolemiza de forma estable al generar módulos. Así, estructuras
OWL/SHACL originalmente anónimas mantienen el mismo IRI en cloud, fog y edge;
la unión de cinco fragmentos no multiplica listas RDF ni cierres anónimos.
