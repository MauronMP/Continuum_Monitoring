# Tres experimentos de arquitectura sin factores confundidos

## Propósito

Estos experimentos separan tres preguntas que no deben responderse con una
única corrida:

1. ¿cuánto mejora el servicio de consultas al añadir réplicas?;
2. ¿cuánto tarda cada equipo en materializar exactamente el mismo grafo?;
3. ¿qué ocurre al distribuir realmente la ontología y el ABox por autoridad?

Los tres se ejecutan con los perfiles RDFS, OWL RL y RDFS+OWL RL definidos en
`configs/benchmark.toml`. Jena, RDF4J y Oxigraph siguen perteneciendo al
benchmark independiente de productos: no se etiquetan como razonadores
distribuidos porque no están instalados en las Raspberry Pi de 32 bits.

La configuración completa está en `configs/experiments.toml` y la configuración
rápida en `configs/experiments-smoke.toml`.

## Preparación común

El contrato de worker es la versión 5 y exige ontología 3.0.0 con 115
consultas. Hay que reconstruir Docker y desplegar la misma revisión en los
equipos físicos:

```bash
docker compose down
docker compose up -d --build

.venv/bin/continuum-bench physical stop --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi
```

El coordinador se ejecuta siempre en este PC. En el escenario físico usa
`configs/physical-nodes.toml`: cloud local, fog y tres Raspberry Pi.

## Experimento 1: scale-out de consultas con réplicas

Cada nodo activo recibe una réplica completa e idéntica. La preparación y la
materialización se miden, pero se excluyen expresamente de la métrica primaria.
Durante la calibración, cada réplica ejecuta las 115 consultas. Esos tiempos se
excluyen y alimentan un planificador LPT adaptativo: asigna primero las consultas
costosas al nodo que minimiza la carga predicha. Así no se presupone que el PC y
las Raspberry tengan la misma capacidad. Después, cada consulta se ejecuta una
vez por ronda medida.

Variables:

- independiente: 1, 3 y 5 nodos activos;
- controladas: dataset, reglas, razonador, consultas y semilla;
- medidas: consultas/s, pared de la ronda, p50/p95/p99 del motor, CPU de
  consulta, RSS, consistencia exacta de todas las réplicas, asignación por nodo
  y factor de replicación.

El monolito solo tiene el punto de un nodo. Docker y físico tienen 1, 3 y 5.
Este experimento mide servicio de consultas, no inferencia distribuida.

```bash
.venv/bin/continuum-bench experiment scale-out monolith
.venv/bin/continuum-bench experiment scale-out docker
.venv/bin/continuum-bench experiment scale-out physical
```

Smoke:

```bash
.venv/bin/continuum-bench experiment scale-out monolith \
  --experiment-config configs/experiments-smoke.toml \
  --output-dir outputs/experiments-smoke
```

Resultados: `outputs/experiments/ARQUITECTURA/scale-out/`.

## Experimento 2: escalabilidad del razonamiento por hardware

Cada endpoint se evalúa de manera aislada y secuencial. Nunca se espera a los
cinco como una barrera ni se suman sus recursos. Por tanto, puede compararse:

- proceso monolítico del PC;
- cada contenedor Docker;
- cloud físico;
- fog y cada edge Raspberry Pi.

Los perfiles varían por separado triples, reglas o usuarios. El relleno para la
serie de triples usa `padding_mode = "neutral"`: no crea instancias de
`continuum:User`. Se conservan entrada y salida porque RDFS todavía puede
derivar axiomas genéricos de cualquier triple RDF.

Se registran tiempo de generación, razonamiento y pared, triples afirmados,
inferidos y materializados, factor de expansión de clausura, CPU, RSS, disco y
timeout. Un timeout es censura por la derecha, no un tiempo cero.
Los metadatos guardan por endpoint versión de Python, plataforma, arquitectura,
número de CPU, ancho del proceso (32/64 bits) y memoria total disponible en
Linux; esto permite comprobar que los resultados físicos pertenecen realmente
a las Raspberry configuradas.

```bash
.venv/bin/continuum-bench experiment reasoning-hardware monolith
.venv/bin/continuum-bench experiment reasoning-hardware docker
.venv/bin/continuum-bench experiment reasoning-hardware physical
```

Ejecutar solo algunos puntos:

```bash
.venv/bin/continuum-bench experiment reasoning-hardware physical \
  --profile triples-25000 \
  --profile rules-25 \
  --reasoner rdfs
```

Resultados: `outputs/experiments/ARQUITECTURA/reasoning-hardware/`.

## Experimento 3: ontología realmente distribuida

El dataset lógico es idéntico entre arquitecturas:

- monolito: grafo completo y una clausura;
- Docker/físico: TBox colocada mediante
  `configs/ontology-placement.toml`, ABox fragmentado por autoridad,
  materialización local y consultas federadas;
- datos sensibles: permanecen en su edge propietario;
- cloud/fog: reciben solamente las proyecciones permitidas por las políticas;
- resultados: unión determinista o OR para ASK según
  `queries/execution-plan.toml`.

Cada resultado distribuido se contrasta, fuera del tiempo medido, con el
conjunto canónico de resultados del oráculo monolítico. El oráculo se calcula después de las
repeticiones medidas, para que su CPU y memoria no calienten el cloud local
antes de medirlo. Se registra el factor real de almacenamiento
`suma de fragmentos / grafo lógico`, el fragmento máximo, preparación, suma y
máximo de inferencia por nodo, consultas federadas, CPU, memoria y tráfico JSON.

```bash
.venv/bin/continuum-bench experiment distributed-ontology monolith
.venv/bin/continuum-bench experiment distributed-ontology docker
.venv/bin/continuum-bench experiment distributed-ontology physical
```

Resultados: `outputs/experiments/ARQUITECTURA/distributed-ontology/`.

## Ejecución conjunta

Los tres experimentos para una arquitectura:

```bash
.venv/bin/continuum-bench experiment all monolith
.venv/bin/continuum-bench experiment all docker
.venv/bin/continuum-bench experiment all physical
```

Todas las combinaciones, si Docker y el cluster físico ya están activos:

```bash
.venv/bin/continuum-bench experiment all all
```

El orden recomendado para evitar carga simultánea es monolito, Docker y físico,
con un periodo térmico estable entre escenarios.

## Gráficas

```bash
.venv/bin/continuum-bench experiment plot scale-out
.venv/bin/continuum-bench experiment plot reasoning-hardware
.venv/bin/continuum-bench experiment plot distributed-ontology
.venv/bin/continuum-bench experiment plot all --show
```

Se guardan PNG a 300 dpi, PDF y SVG en
`outputs/experiments/figures/`. Las figuras agregan por mediana las
repeticiones completas. Los fallos/timeouts no se convierten en latencias
ficticias: quedan como censura y deben leerse junto a las tablas de cobertura y
timeout generadas por el análisis.

## Verificar automáticamente la hipótesis

Después de ejecutar las tres arquitecturas:

```bash
.venv/bin/continuum-bench experiment analyze --show
```

Este comando no presupone que el continuum gane. Genera:

- `analysis/scale-out-comparison.csv`: speedup frente a un nodo, eficiencia,
  costes y equivalencia exacta de las réplicas;
- `analysis/hardware-comparison.csv`: slowdown, CPU, RSS y equivalencia del
  grafo afirmado/materializado para cada equipo;
- `analysis/distributed-comparison.csv`: speedup de preparación, consultas y
  tiempo total, coste CPU/RSS, almacenamiento, censura y validación;
- `analysis/claim-verdict.csv`: resultado por arquitectura y razonador;
- `analysis/REPORT.md`: dictamen legible y reglas de interpretación;
- gráficas de speedup con una línea de equilibrio en 1×.

El dictamen `supported` exige simultáneamente:

1. todas las repeticiones del mayor nivel configurado;
2. resultados semánticos idénticos al oráculo;
3. throughput mínimo de cinco nodos superior al máximo observado con un nodo;
4. tiempo distribuido total máximo inferior al mínimo monolítico en el mayor
   nivel, o un
   límite inferior de speedup superior a 1× cuando el monolito agota timeout.

CPU y RSS se informan como criterios secundarios independientes: terminar antes
no implica necesariamente consumir menos recursos agregados.

## Interpretación correcta

- Scale-out: compare throughput y latencia; no use su preparación para afirmar
  inferencia distribuida.
- Hardware: compare un endpoint con otro; no presente la suma de cinco equipos
  como potencia disponible para una sola clausura.
- Distribuido: compare el mismo dataset lógico, factor de almacenamiento,
  camino crítico y exactitud; no compare triples por nodo como si fueran el
  total del sistema.
- Antes de publicar, compruebe `status`, las repeticiones completas y
  `result_validation_rate = 1`.
- Si el informe devuelve `not_supported`, no debe modificarse el benchmark para
  forzar una mejora: hay que informar que el overhead o el hardware no compensa
  el particionado bajo esas condiciones.
