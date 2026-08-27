# Tests y comandos de ejecución

El proyecto distingue tres niveles: validación semántica, smoke automatizado y
benchmark experimental. Esta separación evita usar una corrida científica larga
como test de desarrollo.

Para un clon nuevo use `python3 tools/bootstrap.py`. Antes de los smokes Docker
use `python3 tools/doctor.py --docker` o prepare sus imágenes mediante
`python3 tools/bootstrap.py --with-docker`. Las instrucciones de Ubuntu Server,
WSL2, dependencias fijadas y workers están en [INSTALLATION.md](INSTALLATION.md).

## 1. Validación semántica

```bash
.venv/bin/python -m continuum_bench validate
```

Comprueba:

- carga de los 13 artefactos generados desde la fuente v3 más el módulo de
  despliegue del benchmark (14 Turtle de ejecución; los dos shapes están
  incluidos en ese conjunto);
- catálogo sin IDs duplicados y presencia de los 115 `.rq`;
- ejecución de las 115 consultas sobre el grafo de referencia;
- contrato v3 de RF/RNF/RV, políticas, mecanismos y escenarios;
- IDs desconocidos y cobertura observable: 102/116 requisitos y 69/79
  políticas aparecen en la trazabilidad consulta-a-especificación;
- expectativas `true`, `non_empty` y `zero_rows`;
- conformidad de todas las shapes SHACL (las advertencias de migración se
  reportan, pero no se convierten en falsas violaciones);
- materialización RDFS, OWL RL y RDFS+OWL RL;
- ausencia de individuos tipados como `owl:Nothing` y cero incumplimientos en
  las 32 consultas `violation` tras cada materialización;
- equivalencia de las 115 consultas entre monolito y fragmentación por
  autoridad;
- compatibilidad de protocolo, versión v3, catálogo y `reasoning_contract` en
  workers Docker/físicos (al descubrirlos en los tests de integración).

Un fallo devuelve código de salida distinto de cero.

## 2. Smoke pytest acumulativo

```bash
.venv/bin/python -m pytest -m smoke_cumulative
```

Prueba `tests/test_smoke_cumulative.py`. Para mantenerla rápida usa una sola
materialización RDFS y resultados temporales. Verifica que:

- las categorías se añaden en el orden configurado;
- el número de consultas crece de forma monótona;
- se ejecutan las dieciséis etapas;
- la etapa final contiene exactamente los 115 IDs.

## 3. Smoke pytest de escalabilidad

```bash
.venv/bin/python -m pytest -m smoke_scalability
```

Prueba `tests/test_smoke_scalability.py`. Usa bloques mínimos de 2 y 4 usuarios
y una materialización RDFS. Verifica que:

- el número de triples aumenta con el volumen;
- se conservan ambos bloques de datos;
- cada bloque ejecuta exactamente las 115 consultas;
- el CSV detallado contiene los 115 IDs para cada volumen.

## 4. Smoke medible acumulativo

```bash
.venv/bin/continuum-smoke-cumulative
```

Equivalente explícito:

```bash
.venv/bin/python -m continuum_bench \
  --config configs/smoke-cumulative.toml \
  benchmark cumulative
```

Ejecuta una repetición con RDFS, OWL RL y RDFS+OWL RL. Mantiene fijo el grafo de
referencia y añade:

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

Después ejecuta automáticamente el mismo acumulativo con Jena, RDF4J,
RDFLib/OWL-RL y Oxigraph. El usuario no selecciona motores ni arranca su Compose.

Si Docker no está disponible, la comprobación funcional local equivalente es:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  benchmark cumulative --python-only
```

Esta variante valida los tres perfiles RDFLib/OWL-RL, pero no sustituye la
comparación entre productos del ejecutable `continuum-smoke-cumulative`.

La terminal informa antes y después de cada etapa:

```text
[cumulative] reasoner=owlrl repetition=1/1 stage=11/16
category=adaptation cumulative_queries=84 status=running
```

Salida:

```text
outputs/smoke-cumulative/cumulative/
  query-runs.csv
  summary.csv
  metadata.json
  cumulative-total-time.png
  cumulative-p95-query-time.png
```

## 5. Smoke medible de escalabilidad

```bash
.venv/bin/continuum-smoke-scalability
```

Equivalente explícito:

```bash
.venv/bin/python -m continuum_bench \
  --config configs/smoke-scalability.toml \
  benchmark scalability
```

Genera bloques deterministas de 5 y 25 usuarios. Para cada volumen y cada uno de
los tres perfiles locales ejecuta las 115 consultas. A continuación repite
automáticamente los bloques en Jena, RDF4J, RDFLib/OWL-RL y Oxigraph.

Cada volumen se reconstruye desde el mismo grafo base; `25` significa 25
usuarios totales, no 5 anteriores más otros 25. Así cada punto es independiente,
reproducible y no hereda cachés ni inferencias del bloque previo.

Sin daemon Docker puede verificarse solo el pipeline Python con:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  benchmark scalability --python-only
```

La terminal identifica el bloque y el razonador activo:

```text
[scalability] block=2/2 users=25 reasoner=rdfs_owlrl
repetition=1/1 queries=115 phase=reasoning status=running
```

Salida:

```text
outputs/smoke-scalability/scalability/
  query-runs.csv
  summary.csv
  metadata.json
  scalability-total-time.png
  scalability-query-throughput.png
```

## 6. Resto de pruebas

```bash
# Suite completa
.venv/bin/python -m pytest

# Pruebas semánticas y unitarias, excluyendo los dos contratos smoke
.venv/bin/python -m pytest \
  -m "not smoke_cumulative and not smoke_scalability"
```

La suite adicional valida catálogo, consultas, preservación del monolito legado,
SHACL, los tres razonadores, determinismo del generador sintético, reconstrucción
isomorfa de fragmentos, privacidad sintética y compatibilidad de los informes
con resultados replicados o particionados.

La regresión RDFS verifica que los booleanos no se sustituyen por enteros ni
se mezclan idiomas, conservando equivalencias numéricas válidas. El camino
N-Triples del servicio externo ejecuta las 115 consultas con 0, 5 y 25 usuarios
en RDFLib y Oxigraph. EXT-Q68 se prueba también con datos deliberadamente
inválidos para asegurar que sigue detectando incumplimientos reales:

```bash
.venv/bin/python -m pytest tests/test_reasoners.py tests/test_external_engines.py
```

Pruebas focalizadas de distribución e informes:

```bash
.venv/bin/python -m pytest \
  tests/test_partitioning.py \
  tests/test_distributed.py \
  tests/test_physical.py \
  tests/test_compare.py \
  tests/test_reporting.py
```

## 7. Benchmark completo

```bash
.venv/bin/python -m continuum_bench benchmark cumulative
.venv/bin/python -m continuum_bench benchmark scalability
.venv/bin/python -m continuum_bench benchmark all
```

Usa `configs/benchmark.toml`: tres repeticiones y bloques de 10, 100, 500,
1.000, 2.500 y 5.000 usuarios. Es el nivel destinado a obtener resultados
comparables; los smoke solo comprueban rápidamente que ambos pipelines
funcionan.

## 8. Benchmark de carga multidimensional

El flujo nuevo conserva comandos independientes y un smoke común:

```bash
.venv/bin/continuum-bench load monolith \
  --load-config configs/load-smoke.toml \
  --output-dir outputs/load-smoke
.venv/bin/continuum-bench load docker \
  --load-config configs/load-smoke.toml \
  --output-dir outputs/load-smoke
.venv/bin/continuum-bench load physical \
  --load-config configs/load-smoke.toml \
  --output-dir outputs/load-smoke
```

Sin `--load-config`, recorre eventos/s, usuarios, triples, reglas y nodos a
volúmenes de experimento, con tres repeticiones y los tres razonadores:

```bash
.venv/bin/continuum-bench load monolith
.venv/bin/continuum-bench load docker
.venv/bin/continuum-bench load physical
.venv/bin/continuum-bench load plot --show
```

La terminal muestra arquitectura, perfil, dimensión, razonador, repetición,
tasa, usuarios, triples, reglas, nodos, fase y estado. La definición completa
de las métricas y los timeouts está en `docs/design/LOAD_BENCHMARKS.md`.

## 9. Regenerar y mostrar gráficas

Benchmark completo:

```bash
.venv/bin/continuum-bench plot cumulative --show
.venv/bin/continuum-bench plot scalability --show
.venv/bin/continuum-bench plot all --show
```

Smoke acumulativo:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  plot cumulative --show
```

Smoke de escalabilidad:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  plot scalability --show
```

`plot` lee el `summary.csv` ya generado y vuelve a crear los PNG. La opción
`--show` abre cada imagen con el visor configurado en el sistema. Para regenerar
sin abrir ventanas se omite esa opción.

En macOS también pueden abrirse directamente los resultados:

```bash
open outputs/cumulative/*.png
open outputs/scalability/*.png
open outputs/smoke-cumulative/cumulative/*.png
open outputs/smoke-scalability/scalability/*.png
```

## 10. Cinco nodos Docker: réplica y particionado

```bash
docker compose up -d --build

# Smokes distribuidos, separados
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  docker cumulative --output-dir outputs/docker-smoke-cumulative

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  docker scalability --output-dir outputs/docker-smoke-scalability

# Experimentos completos
.venv/bin/continuum-bench docker cumulative
.venv/bin/continuum-bench docker scalability

# Comparación completa y figuras de speedup
.venv/bin/continuum-bench compare all

# Los mismos tests con ABox particionado por autoridad
.venv/bin/continuum-bench sharded docker cumulative
.venv/bin/continuum-bench sharded docker scalability
.venv/bin/continuum-bench sharded docker all
```

El comparador no se limita al tiempo: coteja para cada consulta digest de
bindings, número de resultados y valor ASK cuando los CSV contienen digest.
Falla si Docker y el monolito difieren. Los detalles están en
`docs/design/DOCKER_BENCHMARKS.md`.

Los dos layouts no son intercambiables:

| Comando | Layout | Asignación | Salida |
|---|---|---|---|
| `docker --layout replicated` | cinco réplicas completas | afinidad de categoría | `outputs/docker/replicated` |
| `docker` | ABox por autoridad + perfil | scopes del plan | `outputs/docker/sharded` |

Para comprobar los fragmentos antes de ejecutar:

```bash
.venv/bin/continuum-bench fragments \
  --users 100 \
  --output-dir outputs/fragments
```

El modo particionado genera una fila fusionada por consulta en
`query-runs.csv` y respuestas por nodo en `node-query-runs.csv`. La validación
monolítica se ejecuta por defecto, fuera de los tiempos.

## 11. Motores independientes automáticos

```bash
# Smoke acumulativo
.venv/bin/continuum-smoke-cumulative

# Smoke de escalabilidad
.venv/bin/continuum-smoke-scalability

# Corridas completas por separado
.venv/bin/continuum-bench benchmark cumulative
.venv/bin/continuum-bench benchmark scalability

# Figuras generadas por los smoke
.venv/bin/continuum-bench plot engines \
  --engine-suite cumulative \
  --engine-dir outputs/smoke-cumulative/engines --show

.venv/bin/continuum-bench plot engines \
  --engine-suite scalability \
  --engine-dir outputs/smoke-scalability/engines --show
```

En el acumulativo cada motor prepara una vez el grafo de referencia y ejecuta
los conjuntos crecientes de 4 a 115 consultas en las 16 categorías. En
escalabilidad cada motor vuelve a preparar el grafo de cada bloque sintético y
ejecuta las 115 consultas.

El comando falla si una expectativa funcional no se cumple o si los tres
razonadores discrepan en el resultado observable. La cardinalidad exacta se
registra separadamente porque el entailment de datatypes varía entre productos.
La especificación completa está en `docs/design/ENGINE_BENCHMARKS.md`.

La automatización de Jena, RDF4J, RDFLib/OWL-RL y Oxigraph aplica a
`benchmark`, `continuum-smoke-*` y `docker`. Los comandos `physical` y
`sharded` recorren los tres perfiles Python de `benchmark.reasoners`; no
levantan el Compose de productos. En Raspberry Pi OS de 32 bits el banco Java
25/PyOxigraph no es portable: Jena/RDF4J se mantienen como validación de
productos en cloud y Oxigraph como control SPARQL sin inferencia, no como
razonador físico distribuido.

## 12. Informe comparativo de arquitecturas

```bash
.venv/bin/python tools/generate_comparative_figures.py
```

El script exige resultados completos en `outputs/cumulative`,
`outputs/scalability`, `outputs/docker/replicated/cumulative` y
`outputs/docker/replicated/scalability`. Antes de graficar vuelve a comprobar la
equivalencia de resultados. Genera las figuras y tablas científicas bajo
`outputs/analysis/`.

Con resultados físicos y particionados:

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

Las raíces opcionales solo se incluyen si contienen `cumulative/summary.csv` y
`scalability/summary.csv`. Para cada una se valida el resultado contra el
monolito, se calculan costes por nodo y se generan tablas
`multi-architecture-*.csv`.

## 13. Matriz completa de ejecución

| Arquitectura | Acumulativo | Escalabilidad | Ambos |
|---|---|---|---|
| Monolito | `benchmark cumulative` | `benchmark scalability` | `benchmark all` |
| Docker replicado | `docker cumulative --layout replicated` | `docker scalability --layout replicated` | `docker all --layout replicated` |
| Docker particionado | `docker cumulative` | `docker scalability` | `docker all` |
| Físico replicado | `physical cumulative --layout replicated` | `physical scalability --layout replicated` | `physical all --layout replicated` |
| Físico particionado | `physical cumulative` | `physical scalability` | `physical all` |

En todos los casos puede anteponerse
`--config configs/smoke-cumulative.toml` o
`--config configs/smoke-scalability.toml` para reducir el experimento. El
Compose o los workers físicos deben estar sanos antes de ejecutar cualquier
flujo distribuido.

## Límites de los tests distribuidos

- `sharded` fragmenta el ABox y aplica placement de perfiles; replica el núcleo
  inmutable, mantiene wellbeing fuera de fog y shapes fuera de fog/edge.
- Los CSV nuevos prueban digest del bag de bindings, cardinalidad y ASK. Los
  históricos sin digest usan `validation_level=cardinality_ask`.
- La coincidencia del digest no equivale a una demostración formal de la
  reescritura de agregaciones distribuidas.
- Las duraciones por nodo son proxies de trabajo, no medidas de energía, dinero
  o utilización real de CPU.
- Los tests pytest de distribución son locales y no sustituyen un smoke
  end-to-end con los cinco servicios.
- Que el test termine correctamente prueba equivalencia funcional y produce
  mediciones; no prueba por sí solo que cinco nodos sean más rápidos. El
  speedup debe calcularse sobre el mismo release, dataset, razonador, consultas,
  repeticiones y política de calentamiento.
- El timeout es un resultado censurado, no una latencia ordinaria: debe
  informarse junto con la tasa de timeouts y nunca descartarse del agregado.
