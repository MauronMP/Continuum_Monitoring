# Informe comparativo de arquitecturas

## Comando

Después de ejecutar el monolito y ambos layouts Docker:

```bash
.venv/bin/python tools/generate_comparative_figures.py
```

Alternativa equivalente:

```bash
.venv/bin/python -m continuum_bench.reporting
```

Para regenerar en otra ruta y abrir los PNG:

```bash
.venv/bin/python -m continuum_bench.reporting \
  --monolith-dir outputs \
  --docker-dir outputs/docker/replicated \
  --physical-dir outputs/physical/replicated \
  --docker-sharded-dir outputs/docker/sharded \
  --physical-sharded-dir outputs/physical/sharded \
  --output-dir outputs/analysis \
  --show
```

Tras reinstalar el proyecto también está disponible:

```bash
.venv/bin/continuum-report --show
```

## Familias de figuras

El informe base genera diez figuras, cada una en PNG a 300 dpi, PDF y SVG:

1. `monolith-cumulative`: tiempo total, descomposición
   razonamiento/SPARQL, p95 y expansión de materialización.
2. `monolith-scalability`: tiempo total, throughput, descomposición en el
   volumen máximo y triples inferidos.
3. `docker-cumulative`: tiempo de pared, preparación/consulta, coste SPARQL de
   cloud/fog/edge1/edge2/edge3 y trabajo agregado por tiempo de pared.
4. `docker-scalability`: las mismas métricas por volumen sintético.
5. `deployment-cumulative`: speedup, tiempos monolito/Docker, eficiencia
   paralela y cambio porcentual.
6. `deployment-scalability`: comparación para 10, 100, 500, 1.000, 2.500 y
   5.000 usuarios.
7. `monolith-products-cumulative`: Jena, RDF4J, RDFLib/OWL-RL y Oxigraph en el
   test acumulativo monolítico.
8. `monolith-products-scalability`: los cuatro productos por volumen.
9. `docker-products-cumulative`: productos ejecutados por el flujo Docker.
10. `docker-products-scalability`: productos ejecutados por el flujo Docker.

Oxigraph se representa de forma explícita como control SPARQL sin inferencia.
Sus tiempos no se interpretan como un cuarto razonador RDFS. Las figuras de
producto permanecen separadas de los perfiles RDFS, OWL RL y RDFS+OWL RL.

Si existen resultados físicos y particionados, también genera:

- `physical-cumulative` y `physical-scalability`, incluidos costes por nodo;
- `architecture-cumulative` y `architecture-scalability`, con monolito,
  Docker y continuum físico.
- `article-cumulative-summary` y `article-scalability-summary`, con mediana y
  rango mínimo-máximo, speedup frente al monolito, porcentaje dedicado a
  preparación y throughput SPARQL efectivo;
- `architecture-all-cumulative` y `architecture-all-scalability`, con todas
  las variantes disponibles, más `multi-architecture-*.csv`.

Las líneas muestran mediana y rango mínimo-máximo entre repeticiones. El rango
es descriptivo y no es un intervalo de confianza.

## Definición de coste

`docker-node-costs.csv` agrega por nodo:

- número de consultas asignadas;
- suma de duraciones SPARQL;
- latencia media;
- p95.

La suma de duraciones es un proxy de trabajo de consulta, útil para
detectar desequilibrio entre cloud, fog y edges. No representa coste monetario,
energía ni coste monetario. Las corridas nuevas añaden CPU de proceso, RSS
máxima del proceso y bytes del cuerpo HTTP; RSS es un máximo de vida del proceso
y los bytes no incluyen cabeceras ni tráfico TCP.

También se informa del trabajo agregado:

```text
(suma de razonamiento de los nodos + suma de consulta de los nodos)
------------------------------------------------------------------
                         tiempo de pared
```

Esta relación ayuda a interpretar cuánto trabajo concurrente sostiene cada
segundo observado, pero no debe denominarse eficiencia energética.

## Tablas generadas

`outputs/analysis/data/` contiene:

- `monolith-reasoner-summary.csv`;
- `docker-reasoner-summary.csv`;
- `docker-node-costs.csv`;
- `deployment-summary.csv`;
- `product-engine-summary.csv`;
- comparaciones acumulativa y de escalabilidad;
- validación consulta a consulta entre arquitecturas.

Con la arquitectura física se añaden `physical-node-costs.csv`,
`physical-reasoner-summary.csv`, `three-way-cumulative.csv`,
`three-way-scalability.csv`, `article-cumulative-summary.csv`,
`article-scalability-summary.csv` y la validación monolito/físico.

`deployment-summary.csv` identifica qué arquitectura fue más rápida en el punto
de carga máximo de cada experimento. La validación nueva exige digest del bag
de bindings, cardinalidad y `ASK`; los CSV históricos sin digest quedan
marcados explícitamente con `validation_level=cardinality_ask`.
