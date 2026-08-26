# Benchmark de carga y escalabilidad multidimensional

## Objetivo experimental

Este benchmark complementa las pruebas de escalabilidad por tamaño del ABox.
Genera un flujo temporizado de evaluaciones de alerta y ejecuta exactamente el
mismo protocolo en:

1. un proceso monolítico y un nodo;
2. cinco workers locales de Docker Compose;
3. cinco equipos físicos: cloud, fog y tres edge.

Los despliegues distribuidos usan réplicas del grafo para aislar el efecto del
balanceo de consultas. `node_count` selecciona los primeros 1, 3 o 5 roles en
orden cloud, fog, edge1, edge2 y edge3. Por tanto, esta prueba no debe
interpretarse como una evaluación del layout particionado por autoridad.

## Diseño de carga

Un evento es una evaluación SPARQL de una alerta. El catálogo aporta 26
consultas con verdad conocida:

- cinco consultas `ASK` cuya expectativa es `true`;
- 21 consultas de incumplimiento cuya expectativa es `zero_rows`.

Los IDs se recorren circularmente. La llegada se programa a tasa constante y
los eventos que ya han llegado se agrupan hasta `batch_size`. Nunca se ejecuta
un evento antes de su instante programado. La cola central admite
`queue_capacity_events`; un exceso queda registrado como pérdida, no se oculta.
Los lotes aceptados se distribuyen round-robin entre los nodos activos.

Cada punto ejecuta, en orden:

1. reconstrucción del grafo de referencia;
2. generación determinista de usuarios, dispositivos, estados y contratos;
3. cadena sintética de reglas `rdfs:subClassOf`;
4. relleno determinista hasta el número exacto de triples objetivo;
5. materialización con RDFS, OWL RL o RDFS+OWL RL;
6. flujo de eventos;
7. pérdida lógica del estado y reconstrucción completa para medir recuperación.

La recuperación medida es la recuperación del estado de aplicación, no el
reinicio del SO, de Docker ni de la Raspberry Pi.

## Variables independientes

`configs/load-benchmark.toml` aplica un diseño one-factor-at-a-time:

| Dimensión | Niveles |
|---|---|
| Eventos/s | 50, 200, 500, 1.000, 2.500 |
| Usuarios sintéticos | 500, 1.000, 2.500, 5.000, 10.000 |
| Triples objetivo por nodo | 25.000, 50.000, 100.000, 250.000, 500.000 |
| Reglas sintéticas | 0, 25, 50, 100, 250 |
| Nodos activos | 1, 3, 5 |

Los demás factores permanecen en el baseline de cada serie. Hay tres
repeticiones por punto y se recorren automáticamente los tres perfiles de
razonamiento configurados. `configs/load-smoke.toml` mantiene la misma
estructura con volúmenes mínimos.

## Variables medidas

- `latency_p50_ms`, `latency_p95_ms`, `latency_p99_ms`: desde la llegada
  programada hasta la respuesta; incluyen cola, transporte y SPARQL.
- `events_processed_per_second`: eventos completados divididos por el tiempo
  real de la fase.
- `events_lost` y `event_loss_percent`: rechazo por capacidad, timeout o error.
- `inference_wall_ms`: camino crítico de materialización, es decir, el máximo
  entre nodos preparados en paralelo.
- `alert_precision`: `TP / (TP + FP)`.
- `alert_accuracy`: `(TP + TN) / procesados`; también se guardan recall y F1.
- `process_cpu_time_ms` y `cpu_percent_per_node_one_core`: CPU de proceso total
  y normalización por pared, nodos y un núcleo.
- `max_current_rss_kib`: mayor RSS observada al finalizar fases/lotes.
  `max_peak_rss_kib` conserva además el máximo histórico del proceso.
- `disk_read_bytes`, `disk_write_bytes`, `disk_io_bytes`: contadores de E/S de
  `/proc/self/io`; en plataformas sin procfs se registran como cero.
- `network_body_bytes`: bytes JSON de petición y respuesta. No incluye
  cabeceras HTTP, TCP, IP ni enlace.
- `recovery_wall_ms`: camino crítico para reconstruir el estado.
- estado y fase de timeout, matriz de confusión, tiempos completos y métricas
  por nodo.

Los CSV detallados son `summary.csv`, `event-runs.csv` y `node-runs.csv`. El
último permite analizar cloud, fog y cada edge por separado.

## Timeouts

El TOML define tres límites explícitos:

- `request_timeout_seconds`: preparación y petición HTTP individual;
- `point_timeout_seconds`: fase completa de eventos;
- `recovery_timeout_seconds`: reconstrucción.

Un timeout no elimina la observación: marca el estado, conserva la fase y el
límite y contabiliza los eventos no completados como perdidos. En local se usa
el deadline del coordinador. Los workers distribuidos aplican además un timer
interno un segundo antes del timeout HTTP: interrumpen el razonamiento Python,
liberan el lock y permanecen disponibles para el siguiente perfil.

## Preparación de los workers

El benchmark requiere el protocolo de worker 4, que añade reglas, triples
objetivo, relleno neutral/semántico, recuperación, telemetría y cancelación
interna de fases. Después de
actualizar el proyecto hay que
reconstruir Docker y volver a desplegar los nodos físicos:

```bash
docker compose down
docker compose up -d --build

.venv/bin/continuum-bench physical stop --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi
```

## Ejecución

Smoke independiente por arquitectura:

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

Experimento completo:

```bash
.venv/bin/continuum-bench load monolith
.venv/bin/continuum-bench load docker
.venv/bin/continuum-bench load physical
```

Para ejecutar una serie o puntos concretos sin editar el TOML:

```bash
.venv/bin/continuum-bench load monolith --dimension target_triples
.venv/bin/continuum-bench load docker --dimension events_per_second
.venv/bin/continuum-bench load physical --profile nodes-5
```

`--dimension` y `--profile` son repetibles y su combinación aplica una
intersección.

Si Docker y el cluster físico están activos simultáneamente:

```bash
.venv/bin/continuum-bench load all
```

## Figuras y comparación

```bash
.venv/bin/continuum-bench load plot
.venv/bin/continuum-bench load plot --show
```

Se generan PNG a 300 dpi, PDF y SVG para cada dimensión:

- rendimiento: p95 con banda p50–p99, throughput, pérdidas, inferencia, tiempo
  completo y porcentaje de corridas con timeout;
- recursos: exactitud, CPU, RSS, disco, red y recuperación;
- ratios respecto al monolito: speedup de latencia, ganancia de throughput,
  speedup de inferencia/recuperación, eficiencia de scale-out y diferencia de
  pérdidas.
- `load-data-coverage`: matriz de repeticiones completas por arquitectura,
  razonador y perfil; una comparación de rendimiento solo es publicable cuando
  ambos puntos tienen todas sus repeticiones.
- `load-reference-overview`: resumen directamente comparable de latencia a
  200 eventos/s, pico de throughput, pérdida a 2.500 eventos/s y RSS.

Los puntos completos muestran mediana y rango mínimo–máximo. Un marcador hueco
identifica un punto parcial y los ceros derivados de preparaciones fallidas se
excluyen de inferencia, recuperación y recursos. Las tablas agregadas incluyen
mediana, mínimo y máximo. Estos rangos son
descriptivos, no intervalos de confianza. Para publicación conviene fijar el
hardware, aislar carga de fondo y aumentar `repetitions` si se van a aplicar
pruebas estadísticas.
