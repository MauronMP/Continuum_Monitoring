# Continuum Monitoring Ontology Benchmark

Proyecto modular para validar y medir una ontología de monitorización de sistemas
en el computing continuum. El núcleo es independiente del dominio; el perfil de
bienestar (wearables, estrés y sueño) es una extensión opcional.

## Qué contiene

- `ontology/core`: esquema y vocabularios comunes para nodos Mist/Edge/Fog/Cloud,
  estados temporales, MAPE-K, políticas, consentimiento, confianza, AHP,
  delegación y aprendizaje federado.
- `ontology/domains/wellbeing`: conceptos propios de wearables, fisiología,
  estrés y sueño.
- `ontology/shapes`: reglas SHACL de cumplimiento cerrado.
- `ontology/examples`: ABox de referencia con escenarios reproducibles.
- `queries/core` y `queries/domain`: 69 consultas separadas por categoría y tipo.
- `queries/catalog.csv`: catálogo único, orden acumulativo, finalidad y
  expectativa de cada consulta.
- `queries/execution-plan.toml`: autoridad, privacidad y selección de fuentes
  para ejecución particionada.
- `src/continuum_bench`: generador sintético, razonadores, benchmarks y gráficas.
- `engine-service`: adaptadores Java para Apache Jena y Eclipse RDF4J.
- `docker-compose.engines.yml`: comparación aislada RDFLib/Jena/RDF4J/Oxigraph.
- `docs/reference`: requisitos, políticas y documentación revisada.

La batería conserva los IDs `BASE-Qxx` y `EXT-Qxx` para trazabilidad histórica,
pero la clasificación canónica nueva es `tier + category`.

## Instalación

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## Validación

```bash
.venv/bin/python -m continuum_bench validate
```

La validación exige:

- carga correcta de todos los módulos Turtle;
- ejecución de las 69 consultas;
- cero resultados en consultas de incumplimiento;
- conformidad SHACL;
- ausencia de instancias de `owl:Nothing` tras materializar con RDFS, OWL RL y
  el cierre combinado RDFS+OWL RL.

## Benchmarks

Los comandos de benchmark ejecutan automáticamente:

- los perfiles locales RDFS, OWL RL y RDFS+OWL RL;
- Apache Jena RDFS;
- Eclipse RDF4J RDFS;
- RDFLib/OWL-RL RDFS como referencia de producto;
- Oxigraph como control SPARQL sin inferencia.

El coordinador arranca y detiene `docker-compose.engines.yml` automáticamente.
No es necesario indicar motores ni endpoints. Docker debe estar disponible.

```bash
# Ambos experimentos y sus gráficas
.venv/bin/python -m continuum_bench benchmark all

# Experimentos por separado
.venv/bin/python -m continuum_bench benchmark cumulative
.venv/bin/python -m continuum_bench benchmark scalability

# Smoke acumulativo: 14 etapas, 69 consultas finales, 3 perfiles
.venv/bin/continuum-smoke-cumulative

# Smoke de escalabilidad: bloques de 5 y 25 usuarios, 69 consultas, 3 perfiles
.venv/bin/continuum-smoke-scalability
```

El test acumulativo añade categorías en el orden configurado y vuelve a ejecutar
todo el conjunto acumulado. La última etapa siempre contiene las 69 consultas.
El test de escalabilidad añade bloques deterministas de usuarios y estados
sintéticos y ejecuta toda la batería en cada volumen.

El benchmark de carga adicional eleva el escalado hasta 10.000 usuarios,
500.000 triples objetivo, 250 reglas, 2.500 eventos/s y cinco nodos. Mide
percentiles de latencia, throughput, pérdidas, inferencia, exactitud de alertas,
CPU, memoria, disco, red, recuperación y timeouts:

```bash
# Smoke separado
.venv/bin/continuum-bench load monolith \
  --load-config configs/load-smoke.toml \
  --output-dir outputs/load-smoke
.venv/bin/continuum-bench load docker \
  --load-config configs/load-smoke.toml \
  --output-dir outputs/load-smoke
.venv/bin/continuum-bench load physical \
  --load-config configs/load-smoke.toml \
  --output-dir outputs/load-smoke

# Experimento completo por arquitectura
.venv/bin/continuum-bench load monolith
.venv/bin/continuum-bench load docker
.venv/bin/continuum-bench load physical

# Comparación y figuras PNG/PDF/SVG
.venv/bin/continuum-bench load plot --show
```

Tras cambios del worker se debe ejecutar `docker compose up -d --build` y
volver a desplegar/reiniciar el cluster físico. Consulte el
[benchmark de carga multidimensional](docs/design/LOAD_BENCHMARKS.md).
Cuando ya existen resultados, `outputs/load/analysis/REPORT.md` resume la
comparabilidad, los límites y los valores de referencia de la última corrida.

Durante la ejecución, la terminal muestra el razonador, repetición, categoría o
bloque activo, número de consultas, triples y tiempos parciales.

## Tres experimentos de arquitectura

El proyecto separa ahora las tres preguntas arquitectónicas para evitar que la
replicación se interprete como inferencia distribuida:

```bash
# 1. Scale-out de consultas; la preparación queda fuera del tiempo principal
.venv/bin/continuum-bench experiment scale-out monolith
.venv/bin/continuum-bench experiment scale-out docker
.venv/bin/continuum-bench experiment scale-out physical

# 2. Razonamiento por equipo, ejecutando cada endpoint aisladamente
.venv/bin/continuum-bench experiment reasoning-hardware monolith
.venv/bin/continuum-bench experiment reasoning-hardware docker
.venv/bin/continuum-bench experiment reasoning-hardware physical

# 3. TBox/ABox por autoridad, clausuras locales y consultas federadas
.venv/bin/continuum-bench experiment distributed-ontology monolith
.venv/bin/continuum-bench experiment distributed-ontology docker
.venv/bin/continuum-bench experiment distributed-ontology physical

# Los tres para una arquitectura o todas las combinaciones
.venv/bin/continuum-bench experiment all monolith
.venv/bin/continuum-bench experiment all all

# Figuras PNG/PDF/SVG
.venv/bin/continuum-bench experiment plot all --show

# Speedup, costes, punto de equilibrio y veredicto de la hipótesis
.venv/bin/continuum-bench experiment analyze --show
```

Para pruebas rápidas, añada
`--experiment-config configs/experiments-smoke.toml
--output-dir outputs/experiments-smoke`. La metodología, las variables y la
interpretación de cada CSV están en
[tres experimentos de arquitectura](docs/design/THREE_EXPERIMENTS.md).

## Motores semánticos independientes

El benchmark de productos compara tres implementaciones RDFS independientes:
Apache Jena, Eclipse RDF4J y RDFLib/OWL-RL. Añade Oxigraph como control SPARQL
sin inferencia; sus tiempos no se interpretan como los de un cuarto razonador.

No hay que seleccionarlos en los flujos monolítico y Docker replicado:
`benchmark cumulative`, `benchmark scalability`, `benchmark all`, `docker` y
los dos comandos `continuum-smoke-*` recorren todos los motores. Para ejecutar
únicamente los perfiles Python se dispone de `--python-only` en `benchmark` o
`--topology-only` en `docker`.

Los flujos `physical` y `sharded` ejecutan los tres perfiles Python configurados
y no levantan automáticamente el Compose de productos. Esta separación evita
presuponer Java o PyOxigraph en Raspberry Pi OS de 32 bits. Jena/RDF4J requieren
el banco Java del cloud y Oxigraph es un control sin inferencia; no se etiquetan
como motores distribuidos cuando solo podrían ejecutarse en el cloud.

Además de expectativas funcionales, genera un informe de acuerdo observable y
otro de cardinalidad exacta entre razonadores. Consulte la
[metodología multimotor](docs/design/ENGINE_BENCHMARKS.md).

## Mostrar las gráficas

```bash
# Benchmark completo
.venv/bin/continuum-bench plot cumulative --show
.venv/bin/continuum-bench plot scalability --show
.venv/bin/continuum-bench plot all --show

# Figuras para publicación: PNG 300 dpi y formatos vectoriales PDF/SVG
.venv/bin/continuum-bench plot publication

# Gráficas de los smoke separados
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  plot cumulative --show

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  plot scalability --show
```

Sin `--show`, el comando regenera los PNG desde `summary.csv` y muestra sus
rutas, pero no abre el visor del sistema.

## Informe comparativo completo

Después de disponer de las corridas monolítica y Docker:

```bash
.venv/bin/python tools/generate_comparative_figures.py
```

Para abrir las figuras automáticamente:

```bash
.venv/bin/python -m continuum_bench.reporting --show
```

Si también se han ejecutado los layouts particionados:

```bash
.venv/bin/python -m continuum_bench.reporting \
  --docker-dir outputs/docker/replicated \
  --physical-dir outputs/physical/replicated \
  --docker-sharded-dir outputs/docker/sharded \
  --physical-sharded-dir outputs/physical/sharded \
  --show
```

Genera comparaciones por razonador en el monolito, tiempos y coste de consulta
por cada nodo cloud/fog/edge, y speedup/eficiencia monolito frente a Docker.
Produce PNG 300 dpi, PDF, SVG, tablas agregadas y validación consulta a consulta
en `outputs/analysis/`. Consulte la
[documentación del informe](docs/design/COMPARATIVE_REPORT.md).

El informe incluye además figuras específicas
`monolith-products-*` y `docker-products-*` con Apache Jena, Eclipse RDF4J,
RDFLib/OWL-RL y Oxigraph. Oxigraph aparece marcado como control SPARQL sin
inferencia para evitar una comparación metodológicamente incorrecta.

Los resultados incluyen CSV detallado, resumen, metadatos de reproducibilidad,
PNG de inspección y figuras vectoriales. Consulte
[metodología](docs/design/BENCHMARKS.md),
[guía completa de tests](docs/design/TESTS.md),
[validez científica](docs/design/SCIENTIFIC_VALIDITY.md),
[motores semánticos](docs/design/ENGINE_BENCHMARKS.md),
[informe comparativo](docs/design/COMPARATIVE_REPORT.md),
[carga multidimensional](docs/design/LOAD_BENCHMARKS.md),
[tres experimentos separados](docs/design/THREE_EXPERIMENTS.md),
[taxonomía](docs/design/CATEGORIES.md),
[Docker](docs/design/DOCKER_BENCHMARKS.md),
[resultados de referencia](docs/design/RESULTS.md) y
[auditoría](docs/design/AUDIT.md).

## Pruebas automatizadas separadas

```bash
# Solo el contrato del flujo acumulativo
.venv/bin/python -m pytest -m smoke_cumulative

# Solo el contrato del flujo de escalabilidad
.venv/bin/python -m pytest -m smoke_scalability

# Toda la suite
.venv/bin/python -m pytest
```

Las pruebas pytest usan volúmenes mínimos y RDFS para dar feedback rápido y no
requieren Docker. Los comandos `continuum-smoke-*` son los smoke de integración:
ejecutan automáticamente los tres perfiles locales y todos los productos
semánticos, y generan CSV, metadatos y gráficas.

## Benchmark en cinco contenedores

```bash
docker compose up -d --build

# Layout particionado por autoridad (predeterminado)
.venv/bin/continuum-bench docker cumulative
.venv/bin/continuum-bench docker scalability
.venv/bin/continuum-bench docker all

# Baseline de cinco réplicas completas
.venv/bin/continuum-bench docker all --layout replicated

# Comprueba equivalencia de resultados y calcula speedup/eficiencia
.venv/bin/continuum-bench compare all

# Alias compatibles del layout particionado
.venv/bin/continuum-bench sharded docker cumulative
.venv/bin/continuum-bench sharded docker scalability
.venv/bin/continuum-bench sharded docker all

docker compose down
```

El comando `docker` usa por defecto el layout `sharded`; `--layout replicated`
selecciona el baseline de cinco réplicas. Las salidas se separan en
`outputs/docker/{sharded,replicated}`. Cada comando ejecuta además el stack de
productos semánticos independiente; `--topology-only` permite omitirlo.
Consulte `docs/design/DOCKER_BENCHMARKS.md`.

En el layout particionado cada rol carga su fragmento ABox y el perfil de
`configs/ontology-placement.toml`: el núcleo inmutable se replica, wellbeing se
omite en fog y los shapes se mantienen en cloud. Las consultas se enrutan por
`queries/execution-plan.toml`. `sharded docker` permanece como alias compatible
y escribe en `outputs/sharded-docker/`.

## Benchmark en cinco equipos físicos

La topología física preconfigurada utiliza este equipo como cloud,
`192.168.1.137` como fog y `192.168.1.138`–`192.168.1.140` como tres edges
Raspberry Pi 500:

```bash
# Ajuste SU_USUARIO al usuario SSH creado en Raspberry Pi OS
.venv/bin/continuum-bench physical authorize --ssh-user SU_USUARIO
.venv/bin/continuum-bench physical deploy --ssh-user SU_USUARIO
.venv/bin/continuum-bench physical start --ssh-user SU_USUARIO
.venv/bin/continuum-bench physical status --ssh-user SU_USUARIO

# Layout particionado por autoridad (predeterminado)
.venv/bin/continuum-bench physical cumulative --ssh-user SU_USUARIO
.venv/bin/continuum-bench physical scalability --ssh-user SU_USUARIO
.venv/bin/continuum-bench physical all --ssh-user SU_USUARIO

# Baseline replicado y alias compatibles
.venv/bin/continuum-bench physical all --layout replicated \
  --ssh-user SU_USUARIO
.venv/bin/continuum-bench sharded physical cumulative
.venv/bin/continuum-bench sharded physical scalability
.venv/bin/continuum-bench sharded physical all
```

El coordinador calibra todas las consultas en cada host y las balancea según el
coste observado. Hace una calibración por razonador y volumen, la reutiliza
entre repeticiones y vuelve a preparar antes de cada medición. La calibración
queda fuera del tiempo experimental. Para
comparar monolito, Docker y continuum físico:

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

Consulte la [guía del continuum físico](docs/design/PHYSICAL_CONTINUUM.md).

## Matriz de arquitecturas

| Arquitectura | Comando base | Layout de datos | Salida |
|---|---|---|---|
| Monolito | `benchmark` | grafo local completo | `outputs/` |
| Docker replicado | `docker --layout replicated` | cinco réplicas | `outputs/docker/replicated/` |
| Docker particionado | `docker` | ABox por autoridad + perfiles | `outputs/docker/sharded/` |
| Físico replicado | `physical --layout replicated` | cinco réplicas | `outputs/physical/replicated/` |
| Físico particionado | `physical` | ABox por autoridad + perfiles | `outputs/physical/sharded/` |

Cada comando de benchmark acepta `cumulative`, `scalability` o `all`. Las
comparaciones nuevas verifican un digest independiente del orden que conserva
la multiplicidad de los bindings, además de cardinalidad y ASK. Los CSV antiguos
sin digest usan el fallback `cardinality_ask`, indicado en
`validation_level`; este fallback no prueba igualdad de bindings. Los costes por
nodo son proxies de duración, no medidas de energía o coste monetario.
