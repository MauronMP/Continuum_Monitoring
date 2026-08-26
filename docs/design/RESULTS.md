# Resultados de referencia

Ejecución local del 27 de julio de 2026 en macOS ARM64 con Python 3.13.7,
tres repeticiones y semilla 2026. Son una línea base funcional, no una
comparación universal entre motores.

## Acumulativo

La etapa final contiene las 69 consultas sobre 2.205 triples de entrada.

| Perfil | Razonamiento mediano | 69 consultas | Total mediano |
|---|---:|---:|---:|
| RDFS | 175,8 ms | 784,4 ms | 960,2 ms |
| OWL RL | 625,8 ms | 845,9 ms | 1.469,6 ms |
| RDFS + OWL RL | 1.254,8 ms | 791,4 ms | 2.046,2 ms |

## Escalabilidad

Con 500 usuarios sintéticos el grafo alcanza 20.780 triples antes de inferencia.

| Perfil | Razonamiento mediano | 69 consultas | Total mediano | Consultas/s |
|---|---:|---:|---:|---:|
| RDFS | 2.433,0 ms | 3.774,2 ms | 6.360,7 ms | 18,28 |
| OWL RL | 5.886,1 ms | 3.783,2 ms | 9.897,4 ms | 18,24 |
| RDFS + OWL RL | 10.531,6 ms | 4.008,8 ms | 14.716,7 ms | 17,21 |

El coste de consulta crece de forma parecida entre perfiles; la diferencia
principal está en la materialización y en el número de triples inferidos. En el
bloque de 500 usuarios se materializan 16.860, 21.130 y 34.506 triples,
respectivamente.

## Monolito frente a cinco contenedores

Las 4.986 ejecuciones de consulta del acumulativo y las 1.863 de escalabilidad
produjeron el mismo número de filas y el mismo valor ASK en ambos despliegues.

Speedup mediano considerando todas las etapas o bloques:

| Perfil | Acumulativo | Escalabilidad |
|---|---:|---:|
| RDFS | 1,182 | 1,032 |
| OWL RL | 0,723 | 0,741 |
| RDFS + OWL RL | 0,671 | 0,614 |

En escalabilidad, RDFS pasa de 1,452 con 10 usuarios a 0,734 con 500. La réplica
completa del grafo en cinco procesos aumenta la presión de CPU y memoria a gran
volumen. Por tanto, este ordenador no muestra una mejora general con Docker:
solo RDFS y cargas pequeñas/medias amortizan la sobrecarga; OWL RL y el cierre
combinado son más rápidos en el monolito.

Estos resultados describen esta máquina y esta asignación replicada. No prueban
el comportamiento de un particionado RDF, un endpoint federado o cinco
ordenadores físicos.

Artefactos:

- `outputs/cumulative/summary.csv`
- `outputs/scalability/summary.csv`
- `outputs/cumulative/*.png`
- `outputs/scalability/*.png`
- `outputs/publication/*.{png,pdf,svg}`
- `outputs/comparison/*.csv`
- `outputs/comparison/figures/*.{png,pdf,svg}`

## Smoke de motores independientes

Corrida funcional de una repetición medida, precedida por un warm-up excluido,
con Jena 6.0.0, RDF4J 6.0.0, RDFLib 7.6.0/OWL-RL 7.6.2 y Oxigraph 0.5.9.
Estos números comprueban el pipeline; no sustituyen la corrida completa de tres
o más repeticiones.

En el acumulativo se compararon 554 combinaciones consulta-etapa: 554/554
coincidieron en resultado observable, Jena/RDF4J coincidieron exactamente en
554/554 y los tres motores RDFS en 444/554 cardinalidades. En escalabilidad
fueron 138/138, 138/138 y 112/138, respectivamente. La diferencia restante
procede del tratamiento de entailment de datatypes de RDFLib/OWL-RL y no cambió
ninguna decisión funcional.

| Motor | Régimen | Etapa 14: preparar + 69 consultas | 25 usuarios: preparar + 69 consultas |
|---|---|---:|---:|
| Apache Jena | RDFS | 74,26 ms | 155,75 ms |
| Eclipse RDF4J | RDFS | 70,01 ms | 49,35 ms |
| RDFLib/OWL-RL | RDFS | 622,29 ms | 803,72 ms |
| Oxigraph | sin inferencia | 10,26 ms | 12,93 ms |

Oxigraph es una línea base de consulta, no un razonador. Las diferencias entre
Jena y RDF4J con una sola repetición también pueden contener warm-up de JVM; no
deben generalizarse. Artefactos:

- `outputs/engines-smoke/cumulative/`
- `outputs/engines-smoke/scalability/`
- `outputs/engines-smoke/figures/*.{png,pdf,svg}`
