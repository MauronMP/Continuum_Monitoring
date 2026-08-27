# Instalación, portabilidad y diagnóstico de un clon limpio

## Alcance soportado

| Entorno | Función | Requisitos mínimos de software |
|---|---|---|
| Ubuntu/Linux x86-64 o ARM64 | Coordinador y pruebas locales | Git, CPython >=3.11, venv y pip |
| macOS Intel/Apple Silicon | Coordinador y pruebas locales | Git, CPython >=3.11, venv y pip |
| Windows | Coordinador dentro de WSL2 | Distribución Linux en WSL2; no Python nativo de Windows |
| Docker | Cinco nodos y cuatro productos | Daemon Linux amd64/arm64, `docker compose` >=2 y Buildx |
| Raspberry Pi OS de 32/64 bits | Worker físico ligero | Python >=3.11, venv, SSH, rsync y procps |

La instalación completa necesita wheels compatibles con el sistema: en Linux
use una distribución moderna con glibc (por ejemplo Ubuntu 24.04), no presuponga
compatibilidad con Alpine/musl o distribuciones antiguas. La instalación se
detiene con diagnóstico si la plataforma no dispone de esos binarios.

El código del worker mide recursos mediante POSIX (`resource`, señales y,
cuando existe, `/proc`). No se promete ejecución nativa de toda la suite en
Windows ni del coordinador completo en ARM de 32 bits. Se comprueban estas
restricciones antes de instalar. CPython 3.11–3.13 es la matriz de CI; versiones
posteriores requieren verificar que las dependencias fijadas tienen wheels.

No hay un mínimo de RAM que garantice terminar todos los perfiles. Cada motor
tiene por defecto un límite de 3 GiB y cada nodo de 1 GiB; no son reservas de
memoria. La suma de límites puede superar la RAM física. El diagnóstico avisa
si Docker ve menos de 8 GiB. Los timeouts/OOM de campañas grandes siguen siendo
resultados o errores que hay que inspeccionar, no fallos que se deban ocultar.

## 1. Preparación del sistema en Ubuntu Server

Un administrador instala los paquetes básicos una vez:

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv
python3 --version
```

Se requiere Python >=3.11; Ubuntu 24.04 proporciona Python 3.12. Si el
`python3` del sistema es anterior, seleccione explícitamente un intérprete
compatible con su módulo venv. No sustituya el Python que usa APT.

Para Docker use la [instalación oficial de Docker Engine en Ubuntu](https://docs.docker.com/engine/install/ubuntu/),
incluidos el plugin Compose y Buildx. No se ejecutan instaladores remotos
mediante `curl | sh` ni se elimina una instalación Docker existente.

Compruebe con el usuario que ejecutará las pruebas:

```bash
docker compose version
docker buildx version
docker info
```

Si hay `permission denied` sobre `docker.sock`, un administrador debe elegir
entre Docker rootless o acceso mediante el grupo Docker y renovar la sesión
del usuario. El [grupo Docker concede privilegios equivalentes a root](https://docs.docker.com/engine/install/linux-postinstall/).
El proyecto no añade usuarios a grupos, no ejecuta `chmod 666`, no desactiva TLS
y no requiere ejecutar Python/pytest mediante `sudo`.

Docker Desktop es la alternativa en macOS y Windows/WSL2. El código localiza
los auxiliares de Docker Desktop en macOS sin sustituir el CLI, contexto o
proxy elegidos por el usuario. Se respetan `DOCKER_HOST`, contexto y proxy.
Los endpoints automáticos son locales: si usa un daemon remoto, debe exponer
los servicios y usar los comandos avanzados con `--endpoints` adecuados.

## 2. Clonar e instalar

Clone la revisión que contiene estos cambios, incluidos `requirements/`, los
scripts y todos los artefactos de ontología/consultas v3. No copie `.venv`,
`.cache`, `.env`, credenciales ni resultados de otra máquina.

Desde la raíz del clon:

```bash
python3 tools/doctor.py
python3 tools/bootstrap.py
.venv/bin/continuum-bench validate
.venv/bin/python -m pytest
```

El bootstrap:

- solo crea/reutiliza `.venv` dentro del proyecto (o el destino `--venv`);
- rechaza sobrescribir un directorio que no sea virtualenv o un enlace;
- instala versiones fijadas de dependencias, incluido pytest;
- reutiliza la caché `.cache/pip` y no depende de cachés del administrador;
- exige wheels: no instala Rust, GCC o Fortran silenciosamente;
- comprueba dependencias con `pip check`;
- conserva un log por comando y limita cada instalación a 20 minutos.

Si falta `ensurepip`, instale el paquete venv del intérprete. Si faltan wheels,
use una combinación soportada de CPython/plataforma; no se omite Oxigraph ni
otro producto para presentar falsamente una suite completa.

El bootstrap no instala Docker Engine ni arranca servicios privilegiados. Esa
preparación depende del administrador, de políticas de seguridad y de la red.

## 3. Preparar Docker y ejecutar los smokes

```bash
python3 tools/doctor.py --docker
python3 tools/bootstrap.py --with-docker

.venv/bin/continuum-smoke-cumulative
.venv/bin/continuum-smoke-scalability

# Cinco nodos: reutiliza la imagen Python que acaba de construirse
docker compose up -d --no-build
.venv/bin/continuum-bench --config configs/smoke-cumulative.toml \
  docker cumulative --output-dir outputs/docker-smoke-cumulative
.venv/bin/continuum-bench --config configs/smoke-scalability.toml \
  docker scalability --output-dir outputs/docker-smoke-scalability
```

`--with-docker` construye imágenes, no ejecuta benchmarks ni reinicia workers.
El arranque automático también funciona sin esa preparación previa: comprueba
Compose, Buildx, daemon, arquitectura Linux y configuración; construye una sola vez
cada imagen compartida (RDFLib/Oxigraph y Jena/RDF4J); después arranca los cuatro
motores. Las capas de dependencias se reutilizan al cambiar código o consultas.
Solo cloud/RDFLib y Jena declaran un build; los demás reutilizan esas imágenes
locales y no intentan descargarlas de Docker Hub. Este comportamiento también
se aplica al arranque manual mediante `docker compose up -d --build`.

Las consultas, tres perfiles y cuatro productos siguen siendo los mismos.
Oxigraph sigue siendo control SPARQL sin inferencia. Los puertos locales
8191–8195 y 8291–8294 se vinculan solo a `127.0.0.1`; los workers físicos usan
el inventario y el puerto 8391 en la LAN.

Sin Docker puede comprobar exclusivamente el pipeline Python:

```bash
.venv/bin/continuum-bench --config configs/smoke-cumulative.toml benchmark cumulative --python-only
.venv/bin/continuum-bench --config configs/smoke-scalability.toml benchmark scalability --python-only
```

## 4. Diagnosticar un fallo de Compose

```bash
python3 tools/doctor.py --docker --json
docker compose --progress plain -f docker-compose.engines.yml up -d --build
docker compose -f docker-compose.engines.yml ps -a
docker compose -f docker-compose.engines.yml logs --tail 80
```

Los errores ahora incluyen comando, código de salida, últimas 40 líneas y
ruta del log completo en `outputs/runtime/setup/`. Mientras un comando está
silencioso se emite progreso cada 30 s. El timeout por build/arranque es de
1.200 s y puede ajustarse con `CONTINUUM_COMPOSE_TIMEOUT` (segundos positivos).
El cierre y la recogida de diagnósticos tienen un límite independiente de 60 s.
Las comprobaciones iniciales tienen 20 s por comando y las peticiones de salud
del arranque 2 s por endpoint; ya no heredan el timeout de consulta de 900 s.

| Mensaje original | Qué revisar |
|---|---|
| `permission denied ... docker.sock` | Acceso al daemon con el mismo usuario, no el código SPARQL |
| `Cannot connect to the Docker daemon` | Servicio/Desktop, contexto y `DOCKER_HOST` |
| `compose ... unknown command` | Plugin Compose; no sirve el ejecutable legacy v1 |
| `port ... allocated` | Conflicto en los puertos; no detener contenedores ajenos |
| `no matching manifest` | Arquitectura del daemon; productos solo Linux de 64 bits |
| `credential`, `x509`, `resolve`, `429` | Credenciales, certificados, DNS/proxy o límites de descarga |
| `137`, `OOMKilled`, `no space left` | Memoria o disco disponibles, sin borrar datos automáticamente |

Si falla el arranque, se recogen `ps` y logs y se conservan los contenedores
para inspección. No se ejecuta `down` contra un arranque parcial de procedencia
incierta. Un error de cierre nunca sustituye un error anterior de consultas.
Si el único fallo es el cierre, se indica que el benchmark ya había terminado.

Para una máquina con menos recursos puede copiar `.env.example` a `.env` y
ajustar límites explícitamente. Mantenga el mismo límite para los cuatro
productos y un heap Java menor que el límite de memoria. Conserve esa
configuración con la campaña: no compare límites distintos como si fueran el
mismo experimento. No se reducen perfiles ni límites de manera silenciosa.

## 5. Nodos físicos

En el coordinador: `openssh-client`, `ssh-copy-id` y `rsync`. En cada Raspberry:
Python >=3.11, `python3-venv`, `openssh-server`, `rsync` y `procps`; SSH activo,
clave autorizada y puerto 8391 accesible desde el coordinador.

```bash
python3 tools/doctor.py --physical
.venv/bin/continuum-bench physical authorize --ssh-user pi
.venv/bin/continuum-bench physical stop --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi
```

`deploy` comprueba Python/venv/ensurepip/rsync/pgrep/nohup en los cuatro remotos
antes de copiar a ninguno. Instala únicamente RDFLib, OWL-RL y PyParsing, con
versiones exactas y wheels puros; no instala Java ni librerías de gráficos.
También rechaza `remote_dir` amplios como `/` o `/home/pi`: la réplica rsync
solo debe gestionarse dentro de un directorio dedicado.

Para instalar manualmente el worker en un clon en una Raspberry:

```bash
python3 tools/bootstrap.py --profile worker
PYTHONPATH=src .venv-node/bin/python -m continuum_bench.node --help
```

## 6. Reproducibilidad y comprobaciones

`requirements/constraints.txt` fija versiones directas y transitivas del
entorno comprobado. NumPy usa 2.3.5 en Python 3.11 y 2.5.1 en Python >=3.12;
use la misma versión de Python al comparar máquinas. Los resultados registran
`runtime_versions`, además del contrato de ontología/razonamiento.

Esto no constituye una construcción bit a bit: las bases Docker conservan
etiquetas, no digests; los wheels varían por plataforma; las constraints no son
un lock con hashes. Maven fija las versiones principales en `pom.xml`.
El sistema tampoco garantiza conectividad, credenciales o permisos en una
máquina remota que no se ha inspeccionado.

`.github/workflows/portability.yml` prueba clones limpios en Ubuntu 24.04 y
macOS con CPython 3.11/3.12/3.13. Otro job ejecuta los dos smokes multimotor y
los cinco nodos Docker. Esos jobs se ejecutarán al publicar los cambios; que
exista el workflow no significa que ya se haya ejecutado en GitHub.

### Verificación de esta revisión (2026-08-27)

Se comprobaron entornos nuevos en macOS/Python 3.13 y Linux ARM64/Python
3.11 y 3.12, la instalación mínima del worker, ambos Dockerfiles y los smokes
acumulativo/escalabilidad del monolito, cinco nodos Docker y cuatro productos.
La suite local final contiene 148 pruebas aprobadas. La construcción Java
reutilizó la caché Maven; no se presenta como una descarga Maven desde cero.
Ubuntu nativo, Linux x86-64 y las Raspberry reales no se han ejecutado en esta
revisión; la matriz de CI queda preparada para ampliar esa comprobación.

Los resultados funcionales Docker están en `outputs/portability/`, y los logs
de preparación en `outputs/runtime/setup/`. No use estos tiempos como datos de
artículo: hubo verificaciones concurrentes. Que un smoke termine correctamente
comprueba sus expectativas, no una equivalencia total entre motores. En el
smoke de escalabilidad hubo 230/230 acuerdos de resultado observable y 220/230
de cardinalidad exacta entre los tres motores RDFS; las diferencias quedan
registradas en `rdfs-equivalence-summary.json`, no se ocultan ni se corrigen
alterando consultas para pasar la prueba.
