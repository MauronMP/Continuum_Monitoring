# Benchmark en cinco equipos físicos

## Topología

El inventario `configs/physical-nodes.toml` define:

| Rol | Equipo | Endpoint |
|---|---|---|
| cloud | Mac coordinador local | `http://127.0.0.1:8391` |
| fog | Raspberry Pi 500 | `http://192.168.1.137:8391` |
| edge1 | Raspberry Pi 500 | `http://192.168.1.138:8391` |
| edge2 | Raspberry Pi 500 | `http://192.168.1.139:8391` |
| edge3 | Raspberry Pi 500 | `http://192.168.1.140:8391` |

Las direcciones se han interpretado como `192.168.1.137`–`192.168.1.140`.
Edite el inventario si la asociación rol/IP es distinta. El usuario SSH por
defecto es `pi`; puede cambiarlo en el TOML o mediante `--ssh-user`. Las rutas
remotas usan `{ssh_user}` y se adaptan al usuario elegido.

El mismo inventario soporta dos experimentos:

| Flujo | Datos por nodo | Planificación |
|---|---|---|
| `physical --layout replicated` | réplica completa | calibración y LPT heterogénea |
| `physical` | ABox por autoridad + perfil | selección de fuentes declarativa |

El primero compara ejecución paralela y heterogeneidad de hardware. El segundo,
predeterminado, fragmenta el ABox sensible y aplica perfiles de placement:
núcleo común, wellbeing en cloud/edge y shapes solo en cloud.

## Preparación de las Raspberry Pi

Requisitos previos:

- Raspberry Pi OS de 32 bits con `python3`, `python3-venv`, `ssh` y `rsync`;
- IP fija y puerto TCP 8391 accesible desde el Mac;
- autenticación SSH por clave;
- reloj sincronizado mediante NTP;
- mismo modo energético y refrigeración durante todas las repeticiones.

Raspberry Pi 500 incorpora un procesador Arm de 64 bits, aunque Raspberry Pi OS
también se publica con userland de 32 bits. Para respetar el entorno indicado,
el worker usa solo `rdflib` y `owlrl`, que son dependencias Python, y no exige
Java, Jena, RDF4J ni PyOxigraph en los nodos remotos. Consulte la
[especificación de Raspberry Pi 500](https://www.raspberrypi.com/products/raspberry-pi-500/)
y la [documentación de arquitecturas de Raspberry Pi OS](https://www.raspberrypi.com/documentation/computers/os.html#architecture).

En los nodos de referencia se ha comprobado `aarch64` con userland ELF de
32 bits y Java 17. Este entorno no satisface el Java 25 requerido por RDF4J 6,
y la imagen Java 25/PyOxigraph del banco de productos no se considera portable
a ARM de 32 bits. Por tanto:

- el continuum físico distribuye los perfiles RDFLib `rdfs`, `owlrl` y
  `rdfs_owlrl`;
- Jena y RDF4J se comparan como productos RDFS en el banco monolítico/Docker
  del cloud;
- Oxigraph es un control SPARQL sin inferencia, no un razonador;
- no se mezclan tiempos cloud con tiempos distribuidos bajo la etiqueta de
  «motor continuum».

Para distribuir esos productos también en Raspberry se requiere migrar los
cuatro nodos a un sistema operativo de 64 bits, validar imágenes `linux/arm64`
y homogeneizar Java 25 antes de añadir ese experimento.

## Despliegue y ciclo de vida

```bash
# Instala la clave pública local. Solicita la contraseña una sola vez por Pi.
.venv/bin/continuum-bench physical authorize --ssh-user SU_USUARIO

# Copia el worker y crea .venv-node en las cuatro Raspberry Pi
.venv/bin/continuum-bench physical deploy --ssh-user SU_USUARIO

# Arranca cloud local, fog y los tres edges
.venv/bin/continuum-bench physical start --ssh-user SU_USUARIO

# Comprueba rol, endpoint y salud de los cinco nodos
.venv/bin/continuum-bench physical status --ssh-user SU_USUARIO

# Detiene procesos que coinciden con rol, puerto y comando de worker
.venv/bin/continuum-bench physical stop --ssh-user SU_USUARIO
```

`deploy` no usa `rsync --delete`: no elimina ficheros remotos. `stop` localiza
el worker por ejecutable, rol y puerto, por lo que también recupera un servicio
si su fichero PID quedó obsoleto. `start` detecta servicios ya sanos y no crea
una segunda instancia; al arrancar uno nuevo verifica que el PID escrito sea el
del proceso Python y que siga vivo.
Los comandos de ciclo de vida usan `BatchMode=yes`: nunca almacenan la
contraseña ni quedan esperando una entrada interactiva. Si todavía no hay una
clave autorizada, fallan inmediatamente indicando que debe ejecutarse
`physical authorize`. Si `ssh-copy-id` informa de que no hay identidades,
créela una sola vez con `ssh-keygen -t ed25519`.

El puerto físico `8391` se mantiene separado del `8080` empleado por otros
workers o despliegues Docker. El endpoint `/health` se acepta únicamente cuando
identifica `service=continuum-benchmark-node`, la versión de protocolo esperada
y el rol exacto del inventario; una respuesta genérica `status=ok` no basta.

## Ejecución replicada

Con los cinco servicios activos:

```bash
.venv/bin/continuum-bench physical cumulative --layout replicated --ssh-user SU_USUARIO
.venv/bin/continuum-bench physical scalability --layout replicated --ssh-user SU_USUARIO

# Ambos tests
.venv/bin/continuum-bench physical all --layout replicated --ssh-user SU_USUARIO
```

Los resultados se escriben en
`outputs/physical/replicated/{cumulative,scalability}`:

- `summary.csv`: tiempos de pared y trabajo agregado;
- `query-runs.csv`: resultado y duración de cada consulta;
- `assignments.csv`: nodo elegido y coste predicho;
- `node-runs.csv`: coste de preparación, calibración y consulta por equipo;
- `metadata.json`: inventario, método de balanceo y parámetros reproducibles.

## Ejecución particionada por autoridad

Tras `physical start`, los mismos workers pueden reconstruir su fragmento según
su rol:

```bash
.venv/bin/continuum-bench physical cumulative
.venv/bin/continuum-bench physical scalability

# Ambos tests
.venv/bin/continuum-bench physical all
```

El comando `sharded physical` lee `configs/physical-nodes.toml`; no acepta
`--ssh-user` porque no gestiona SSH, solo consume los endpoints ya arrancados.
Si se usa otro inventario:

```bash
.venv/bin/continuum-bench sharded physical all \
  --inventory configs/physical-nodes.toml \
  --output-dir outputs/sharded-physical
```

La salida añade `node-query-runs.csv` con las respuestas parciales,
`result-validation.csv` frente al oráculo monolítico y métricas
`logical_input_triples`, `aggregate_fragment_triples`,
`max_fragment_triples` y `storage_replication_factor`.

## Balanceo adaptativo

Para cada combinación de razonador y volumen, el coordinador hace una
preparación de calibración no medida y prueba una vez cada consulta en cada
nodo. Después vuelve a preparar el grafo desde cero para cada repetición medida.
El planificador ordena las consultas de mayor a menor coste y asigna cada una al
nodo que minimiza su tiempo de finalización predicho. Es una variante LPT
heterogénea.

La calibración:

- se ejecuta una vez por razonador y volumen y se reutiliza en sus repeticiones;
- no forma parte de `total_wall_ms`;
- queda registrada en `calibration_wall_ms_excluded` y `node-runs.csv`;
- permite que cloud, fog y edges reciban cantidades distintas de consultas.

Antes se repetía en cada repetición, añadiendo 69 consultas × 5 nodos sin que
ese coste apareciera en `total_wall_ms`. La reutilización elimina ese trabajo
redundante y mantiene simétricas las repeticiones mediante la preparación
independiente de calibración.

El tiempo medido sí incluye preparación/materialización y la ejecución paralela
del lote balanceado. `balance_efficiency` es la suma de trabajo SPARQL de los
nodos dividida entre `5 × query_wall_ms`; es un indicador de equilibrio, no una
medida energética.

Cada petición distribuida muestra en terminal fase, rol, endpoint y duración.
El timeout por nodo es de 900 segundos. Ante un reset transitorio se hacen hasta
dos reintentos con backoff; la espera permanece dentro del tiempo de pared de la
fase y se anuncia explícitamente, por lo que no queda oculta. Los contadores
`prepare_transport_retry_count` y `query_transport_retry_count` se guardan en
`summary.csv`; `node-runs.csv` conserva además los intentos por nodo.

El balanceo LPT solo corresponde al flujo replicado `physical`. En el modo
particionado, la autoridad y privacidad determinan las fuentes mediante
`queries/execution-plan.toml`; mover una consulta a un nodo sin sus datos
alteraría el experimento.

## Comparación de arquitecturas

Después de ejecutar monolito, Docker y físico:

```bash
.venv/bin/python -m continuum_bench.reporting \
  --monolith-dir outputs \
  --docker-dir outputs/docker/replicated \
  --physical-dir outputs/physical/replicated \
  --docker-sharded-dir outputs/docker/sharded \
  --physical-sharded-dir outputs/physical/sharded \
  --output-dir outputs/analysis
```

Para abrir los PNG:

```bash
.venv/bin/python -m continuum_bench.reporting \
  --physical-dir outputs/physical/replicated \
  --physical-sharded-dir outputs/physical/sharded \
  --show
```

Con monolito, Docker replicado y físico replicado se conservan
`architecture-cumulative`, `architecture-scalability` y `three-way-*.csv`.
Cuando se proporciona alguna raíz particionada también se crean
`architecture-all-*` y `multi-architecture-*.csv`. Antes de graficar cada raíz
distribuida se contrastan digest de bindings, cardinalidades y valores ASK con
el monolito.

## Control experimental

Para atribuir cambios a la arquitectura se recomienda ejecutar las tres
alternativas en la misma ventana temporal, cablear los nodos por Ethernet,
desactivar tareas ajenas, registrar temperatura/throttling y alternar el orden
de las arquitecturas. El benchmark actual registra tiempos y cardinalidad, pero
no consumo eléctrico; no debe inferirse eficiencia energética sin un medidor
externo.

Los CSV nuevos comparan también un digest completo de bindings. Los resultados
históricos sin digest quedan explícitamente en nivel `cardinality_ask`, que no
demuestra igualdad completa de SELECT. Además, el modo particionado replica
TBox, módulos y shapes; sus cifras no deben presentarse como distribución
completa de la ontología.

## Diagnóstico de cortes SSH y lentitud

Un mensaje `Connection reset by peer` pertenece al canal SSH, no demuestra por
sí solo que el worker HTTP o el sistema hayan caído. Compruebe:

```bash
.venv/bin/continuum-bench physical status --ssh-user pi
ssh -o ServerAliveInterval=15 -o ServerAliveCountMax=3 pi@192.168.1.139
```

Si quedaron PIDs antiguos tras una versión previa:

```bash
.venv/bin/continuum-bench physical stop --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
```

Para experimentos publicables se recomienda Ethernet. Con Wi-Fi, un corte
transitorio puede cerrar una sesión SSH aunque el worker HTTP continúe. El modo
replicado tampoco implica menor latencia: materializa el grafo completo en cinco
equipos y espera al nodo más lento. Solo distribuye el lote SPARQL; si la
preparación domina o el dataset es pequeño, el Mac monolítico será más rápido.
Compare `total_wall_ms` de los CSV y no el tiempo total del comando, porque la
calibración, la validación monolítica y la escritura de artefactos se excluyen
del intervalo experimental.
