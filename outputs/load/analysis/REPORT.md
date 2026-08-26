# Informe de la corrida de carga

Fecha de revisión: 2026-07-29.

## Aptitud de los datos

| Arquitectura | Repeticiones completadas | Intentos | Timeouts | Fallos no-timeout |
|---|---:|---:|---:|---:|
| Monolito | 156 | 189 | 33 | 0 |
| Docker local | 61 | 207 | 21 | 125 |
| Continuum físico | 57 | 207 | 150 | 0 |

La serie `events_per_second` es la única serie completa, con 3/3
repeticiones para las tres arquitecturas y los tres razonadores. También existe
un punto completo común de 25.000 triples. Las series posteriores no deben
usarse para afirmar superioridad entre las tres arquitecturas:

- en Docker, después de los primeros timeouts aparecen conexiones rechazadas;
- en el continuum físico, las preparaciones posteriores siguen agotando el
  timeout;
- estos fallos son observaciones censuradas, no tiempos de inferencia cero.

La figura `load-data-coverage` es el filtro previo obligatorio para seleccionar
datos de artículo. Un ratio solo se genera si sus dos extremos tienen todas las
repeticiones.

## Comparación común a 200 eventos/s

El workload usa 25.000 triples objetivo, 500 usuarios, 25 reglas y cinco nodos
en Docker/físico frente a un nodo monolítico.

| Arquitectura | Razonador | p95 (s) | Pico procesado/s | CPU/nodo (%) | RSS (MiB) | Inferencia (s) | Recuperación (s) |
|---|---|---:|---:|---:|---:|---:|---:|
| Monolito | RDFS | 4,79 | 58,7 | 99,1 | 322,9 | 5,0 | 5,4 |
| Monolito | OWL RL | 4,66 | 59,1 | 99,3 | 322,9 | 14,0 | 14,4 |
| Monolito | RDFS+OWL RL | 4,93 | 58,9 | 99,1 | 340,2 | 27,0 | 27,0 |
| Docker | RDFS | 0,55 | 164,7 | 87,3 | 193,2 | 10,9 | 11,6 |
| Docker | OWL RL | 0,50 | 165,0 | 91,4 | 211,3 | 28,9 | 29,7 |
| Docker | RDFS+OWL RL | 0,14 | 184,0 | 91,7 | 246,1 | 54,1 | 54,0 |
| Físico | RDFS | 2,53 | 85,8 | 82,2 | 204,7 | 19,8 | 21,2 |
| Físico | OWL RL | 2,23 | 91,2 | 84,1 | 204,7 | 50,4 | 52,1 |
| Físico | RDFS+OWL RL | 2,24 | 91,5 | 84,3 | 204,7 | 94,7 | 96,4 |

## Lectura referencial

- Docker reduce la p95 a 200 eventos/s entre 8,7× y 36,3× frente al monolito y
  multiplica el throughput entre 2,67× y 3,29×.
- El continuum físico reduce la p95 entre 1,9× y 2,2× y aumenta el throughput
  entre 1,50× y 1,64×.
- La eficiencia de scale-out observada es 53–66 % en Docker y 30–33 % en el
  continuum físico. Es throughput relativo dividido entre cinco nodos, no una
  medida de eficiencia energética.
- La distribución favorece la fase de consultas, pero no la preparación:
  Docker tarda aproximadamente 2× el monolito en inferencia/recuperación y el
  continuum físico entre 3,6× y 4×. Esto es coherente con cinco réplicas
  completas, no con una TBox/ABox particionada.
- A 2.500 eventos/s todas las arquitecturas están saturadas: pierden 83,7–88,3
  % de eventos. El mayor nivel probado con pérdida mediana inferior o igual al
  1 % es 200 eventos/s.
- Todas las corridas completadas conservan exactitud de alertas 1,0. La
  escalabilidad no introdujo falsos positivos ni falsos negativos.

## Límites

- Las tres arquitecturas se ejecutaron secuencialmente y sus metadatos tienen
  horas distintas; deben reportarse carga de fondo y condiciones térmicas.
- CPU es porcentaje medio por nodo respecto a un núcleo. RSS es el máximo
  observado; red son bytes JSON útiles y disco son contadores de proceso.
- `p50–p99` describe la distribución de latencia. Las barras mínimo–máximo
  describen variabilidad entre tres repeticiones y no son intervalos de
  confianza.
- Los resultados de reglas, nodos, usuarios y altos volúmenes de triples deben
  repetirse con worker protocol 3 antes de publicarse.

## Regeneración

```bash
.venv/bin/continuum-bench load plot
.venv/bin/continuum-bench load plot --show
```

Tablas de apoyo:

- `data/load-reference-summary.csv`;
- `data/load-data-quality.csv`;
- `data/load-comparison-summary.csv`;
- `data/load-architecture-ratios.csv`.
