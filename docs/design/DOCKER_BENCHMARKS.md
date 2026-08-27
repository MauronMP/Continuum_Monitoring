# Benchmark Docker: réplica y particionado en cinco nodos

## Modelo experimental

`docker-compose.yml` crea cinco servicios:

| Servicio | Puerto host | Categorías |
|---|---:|---|
| cloud | 8191 | semantic_schema, decision, policy_governance y validation |
| fog | 8192 | topology, data_lifecycle, trust, adaptation, delegation, federation y audit_temporal |
| edge1..edge3 | 8193..8195 | observability, identity_consent, security_identity, context_zones y wellbeing, en round-robin |

El comando `docker` usa `sharded` de forma predeterminada. Para cargar una
réplica completa de la ontología y del ABox en cada nodo use
`docker ... --layout replicated`.
El coordinador prepara los cinco nodos en paralelo y reparte cada consulta
exactamente una vez. La réplica completa permite comparar los resultados con el
monolito sin introducir semántica de particionado.

El tiempo distribuido es tiempo de pared:

`prepare_wall_ms + query_wall_ms`.

También se guardan la suma de trabajo de los nodos y el máximo de razonamiento
por nodo. No se suma el trabajo de cinco nodos como si fuera latencia.

En modo `sharded`, cada servicio construye su fragmento ABox según su rol y
carga el perfil declarado en `configs/ontology-placement.toml`: núcleo común,
wellbeing en cloud/edge y shapes solo en cloud.

| Flujo | Datos | Reparto de consultas | Motores |
|---|---|---|---|
| `docker --layout replicated` | grafo completo por nodo | una consulta en un nodo por afinidad | 3 perfiles Python y stack de productos automático |
| `docker` | ABox por autoridad + perfil | una o varias autoridades según el plan | 3 perfiles Python y stack de productos automático separado |

## Arranque y salud

```bash
docker compose up -d --build
docker compose ps

curl http://127.0.0.1:8191/health
curl http://127.0.0.1:8192/health
curl http://127.0.0.1:8193/health
curl http://127.0.0.1:8194/health
curl http://127.0.0.1:8195/health
```

## Smokes separados

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  docker cumulative --output-dir outputs/docker-smoke-cumulative

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  docker scalability --output-dir outputs/docker-smoke-scalability
```

La terminal muestra nodo lógico, razonador, repetición, etapa/categoría o bloque
de usuarios. Los resultados se escriben bajo el `--output-dir` indicado. Después
de la topología de cinco nodos, el mismo comando levanta automáticamente Jena,
RDF4J, RDFLib/OWL-RL y Oxigraph, ejecuta la misma suite y los detiene. Sus
resultados quedan en `<output-dir>/<layout>/engines/`.

No se seleccionan motores ni endpoints. La opción `--topology-only` existe para
experimentos que quieran excluir deliberadamente la dimensión de producto.

## Actualización tras el fallo EXT-Q68

Si aparece `cross-engine query expectations failed: rdflib:EXT-Q68`, actualice
los contenedores desde la raíz de esta copia del proyecto. Espere a que termine
cualquier benchmark en curso antes de reconstruirlos:

```bash
docker compose up -d --build

.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  docker cumulative --output-dir outputs/docker-rdfs-fixed-cumulative

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  docker scalability --output-dir outputs/docker-rdfs-fixed-scalability
```

Cada comando comprueba y reconstruye automáticamente el stack independiente
de cuatro motores si su `/health` no publica el contrato de razonamiento
corregido. Si gestiona los servicios manualmente con el subcomando `engines`,
reconstrúyalos con `docker compose -f docker-compose.engines.yml up -d --build`.

El fallo procedía de inferencias de literales booleanos incorrectas en el
servicio RDFLib; no se desactiva la validación de privacidad para evitarlo.
Los resultados anteriores a la corrección deben regenerarse también para el
monolito y el continuum físico antes de comparar arquitecturas.

## Benchmark completo

Primero se generan resultados comparables con la misma configuración:

```bash
.venv/bin/continuum-bench benchmark all
.venv/bin/continuum-bench docker all
.venv/bin/continuum-bench docker all --layout replicated
.venv/bin/continuum-bench compare all
```

Los dos primeros comandos incluyen automáticamente la comparación de todos los
motores semánticos. `compare all` mantiene como objetivo específico la
comparación temporal entre el monolito Python y la topología cloud/fog/edge.

## Benchmark particionado por autoridad

Con los mismos cinco contenedores activos:

```bash
# Inspección opcional de los cinco fragmentos
.venv/bin/continuum-bench fragments \
  --users 100 \
  --output-dir outputs/fragments

# Tests separados o ambos
.venv/bin/continuum-bench sharded docker cumulative
.venv/bin/continuum-bench sharded docker scalability
.venv/bin/continuum-bench sharded docker all
```

Las salidas se escriben por defecto en
`outputs/sharded-docker/{cumulative,scalability}`:

- `summary.csv`: tiempo de pared y métricas de almacenamiento distribuido;
- `query-runs.csv`: resultado fusionado por consulta;
- `node-query-runs.csv`: coste y resultado parcial por nodo;
- `result-validation.csv`: digest de bindings, cardinalidad y ASK frente al
  monolito;
- `metadata.json`: endpoints, razonadores y política de routing.

`queries/execution-plan.toml` define los scopes `cloud`, `fog`, `edges`,
`edge1`, `edge2`, `edge3` y `cloud_edges`, además de las clases de privacidad.
El routing no es
round-robin: respeta la autoridad declarada y fusiona las respuestas. La
validación contra el monolito está habilitada de forma predeterminada y queda
fuera del tiempo medido.

Este flujo no arranca Jena, RDF4J u Oxigraph. Esos productos pertenecen al
benchmark independiente y al flujo Docker replicado. En las Raspberry de
32 bits tampoco se presupone disponibilidad de Java o PyOxigraph.

`compare all` produce:

- `outputs/comparison/cumulative.csv`;
- `outputs/comparison/scalability.csv`;
- validación resultado-a-resultado de las 115 consultas;
- figuras PNG 300 dpi, PDF y SVG de speedup.

Se define:

- `speedup = tiempo_monolito / tiempo_docker`;
- `eficiencia_paralela = speedup / 5`;
- `speedup > 1`: Docker fue más rápido;
- `speedup < 1`: serialización, HTTP, réplicas o contención dominaron.

Para comparar smokes, cada raíz debe contener el mismo experimento:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  compare cumulative \
  --monolith-dir outputs/smoke-cumulative \
  --docker-dir outputs/docker-smoke-cumulative/sharded \
  --output-dir outputs/comparison-smoke-cumulative
```

El comparador acepta también una raíz particionada:

```bash
.venv/bin/continuum-bench compare all \
  --docker-dir outputs/sharded-docker \
  --output-dir outputs/comparison-sharded-docker
```

Para un informe que conserve por separado réplica y particionado:

```bash
.venv/bin/python -m continuum_bench.reporting \
  --monolith-dir outputs \
  --docker-dir outputs/docker/replicated \
  --docker-sharded-dir outputs/docker/sharded \
  --output-dir outputs/analysis
```

El informe usa `node-query-runs.csv` para los costes del modo particionado y
genera `architecture-all-*` y `multi-architecture-*.csv`, sin sustituir las
figuras históricas monolito/Docker.

## Límites científicos

- El núcleo TBox inmutable se replica para permitir razonamiento local. El
  placement omite wellbeing en fog y shapes en fog/edge.
- Los resultados nuevos comparan el digest del conjunto canónico de bindings,
  cardinalidad y ASK. Los CSV históricos sin digest usan un fallback de
  cardinalidad/ASK identificado en `validation_level`.
- Un digest coincidente no sustituye una demostración formal de la reescritura
  de agregados distribuidos.
- `query_cpu_ms` es una suma de duraciones y solo un proxy de trabajo; no es
  consumo de CPU, energía ni coste monetario.
- `docker-compose.yml` no simula latencia WAN ni heterogeneidad física. Sus
  resultados deben interpretarse como paralelismo local con sobrecarga HTTP.

## Cierre

```bash
docker compose down
```

Los contenedores no usan volúmenes persistentes; `down` elimina contenedores y
red, pero conserva la imagen construida y todos los CSV del host.
