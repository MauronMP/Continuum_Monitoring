# Complete installation guide

This guide starts with a clean clone and ends with a validated installation
that can run the monolithic, elastic-container Docker, and elastic-host physical
continuum experiments. Commands are intended to be run from the repository
root unless a section explicitly says otherwise.

## 1. Choose the role of each machine

| Machine | Role | Required software |
|---|---|---|
| Linux x86-64/ARM64 or macOS | Coordinator, monolithic benchmarks and reporting | Git, 64-bit CPython 3.11-3.13, `venv`, `pip` |
| Coordinator with Docker | Configurable local nodes and RDFLib/Jena/RDF4J/Oxigraph product benchmarks | Previous row plus a 64-bit Linux Docker daemon, Compose v2 and Buildx |
| Windows PC | Coordinator through WSL2 | WSL2 Linux distribution, Git and CPython inside WSL2; Docker Desktop with WSL integration for Docker runs |
| Raspberry Pi OS 32/64 bit | Lightweight physical worker | CPython >=3.11, `venv`, OpenSSH server, `rsync` and `procps` |

Native Windows Python is not supported. Use WSL2. The coordinator must use a
64-bit Python interpreter; a 32-bit Raspberry Pi is supported only as a
lightweight worker.

The tested Python matrix is CPython 3.11, 3.12 and 3.13. A newer interpreter
may work, but is not accepted until all pinned dependencies provide compatible
wheels. The installer deliberately refuses to compile missing native
dependencies.

Docker should expose at least 8 GiB of memory for a practical full run. This is
not a guarantee that every large profile will finish: each semantic engine has
a default 3 GiB limit and each topology node a 1 GiB limit. The limits are
caps, not reserved memory, and their sum may exceed physical RAM. Keep enough
free disk for Docker images, Maven dependencies, Python wheels and result
files. Large timeouts or out-of-memory outcomes are experimental evidence and
must not be silently discarded.

The first installation needs network access to GitHub and PyPI. Docker builds
also need access to the configured container registry and Maven Central. Do not
disable TLS verification to work around a proxy or certificate problem.

## 2. Install host prerequisites

### 2.1 Ubuntu 24.04 coordinator

Ubuntu 24.04 is the simplest Linux coordinator because its system Python is
new enough. Install the base packages once:

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv openssh-client rsync
python3 --version
```

The reported version must be at least 3.11. If a different supported
interpreter is installed, invoke the bootstrap with that exact executable, for
example `python3.13 tools/bootstrap.py`. Do not replace the Python interpreter
used internally by APT.

Optional host packages are installed only when their feature is needed:

```bash
# Vector ontology diagrams
sudo apt-get install -y graphviz

# Independent OWL 2 DL/HermiT check
sudo apt-get install -y openjdk-17-jre-headless

# Compile the supplied LaTeX paper example (optional)
sudo apt-get install -y texlive-latex-base
```

Java, Maven, Jena and RDF4J are not host prerequisites for the normal
benchmarks. Java and Maven are supplied by the semantic-engine Docker build.
Host Java is needed only for the independent Protégé/HermiT validation.

### 2.2 macOS coordinator

Install:

1. Git, either from Xcode Command Line Tools or another trusted package source.
2. A 64-bit CPython 3.11, 3.12 or 3.13 distribution.
3. Docker Desktop if Docker benchmarks will be run.
4. Graphviz if ontology diagrams will be regenerated.
5. Java 17 and Protégé if the independent HermiT check will be run.

Verify the command-line prerequisites:

```bash
git --version
python3 --version
```

Docker Desktop must be started before running Docker checks. Its official
installation page is
<https://docs.docker.com/desktop/setup/install/mac-install/>.

### 2.3 Windows coordinator through WSL2

Install WSL2 and an Ubuntu distribution, then run all repository commands
inside that Linux distribution. Inside WSL2 install:

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv openssh-client rsync
python3 --version
```

For container tests, install Docker Desktop and enable integration for the WSL2
distribution that contains the clone. Do not mix a Windows checkout, native
Windows Python and WSL commands. See the official Docker Desktop instructions:
<https://docs.docker.com/desktop/setup/install/windows-install/>.

### 2.4 Docker Engine on Ubuntu

Install Docker Engine from Docker's official APT repository, including these
packages:

```text
docker-ce
docker-ce-cli
containerd.io
docker-buildx-plugin
docker-compose-plugin
```

Follow the current official repository setup and package commands at
<https://docs.docker.com/engine/install/ubuntu/>. Do not use the obsolete
standalone `docker-compose` v1 executable; this project requires the
`docker compose` v2 plugin.

The user that launches the benchmarks must be able to access the daemon
without prefixing every command with `sudo`:

```bash
docker compose version
docker buildx version
docker info
```

If `docker info` reports a permission error, an administrator must configure
rootless Docker or grant access according to
<https://docs.docker.com/engine/install/linux-postinstall/>. Membership in the
`docker` group grants root-level privileges and requires a new login session.
The project does not change groups, run `chmod 666` on the Docker socket, or
run Python and pytest with `sudo`.

## 3. Clone the repository

Clone the complete repository and enter it:

```bash
git clone https://github.com/MauronMP/Continuum_Monitoring.git
cd Continuum_Monitoring
```

If a particular branch or release is required, check it out before installing:

```bash
git switch BRANCH_NAME
```

Confirm that the clone includes the code, pinned requirements, ontology and
query assets:

```bash
test -f pyproject.toml
test -f requirements/constraints.txt
test -f ontology/legacy/smartcity_continuum-v3.0.0.ttl
test -f queries/legacy/sparql_battery-v3.0.0.sparql
```

Do not copy `.venv`, `.venv-node`, `.cache`, `.env`, credentials or `outputs`
from another computer. Virtual environments contain machine-specific paths and
binaries; benchmark results from another machine are not installation assets.

## 4. Install the coordinator Python environment

Run the dependency-free pre-installation diagnostic:

```bash
python3 tools/doctor.py
```

It checks the Python version, operating system, word size and required project
files without importing the scientific stack.

Create the project environment and install the pinned dependencies:

```bash
python3 tools/bootstrap.py
```

The bootstrap creates `.venv`, installs the project in editable mode with its
development dependencies, checks dependency consistency and writes setup logs
under `outputs/runtime/setup/`. It uses `.cache/pip` inside the repository and
does not mutate the system Python installation.

If `python3` is not the supported interpreter selected in section 2, use that
interpreter explicitly:

```bash
python3.13 tools/bootstrap.py
```

To use a different new virtual-environment directory:

```bash
python3 tools/bootstrap.py --venv .venv-coordinator
```

Do not point `--venv` at a copied environment, a symbolic link, or a directory
that contains unrelated files. The installer intentionally refuses to erase or
replace such paths.

Confirm the installed command and dependencies:

```bash
.venv/bin/continuum-bench --help
.venv/bin/python -m pip check
```

## 5. Validate the clean installation

Validate ontology syntax, modules, query catalog, policies, expected results,
SHACL constraints and local reasoning profiles:

```bash
.venv/bin/continuum-bench validate
.venv/bin/python tools/check_documentation.py
```

The documentation check verifies every local Markdown link and deterministically
regenerates the four English v3 reference manuals in a temporary directory to
detect stale committed documentation.

Run the automated test suite:

```bash
.venv/bin/python -m pytest
```

Run both fast benchmark workflows without Docker:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  benchmark cumulative \
  --python-only

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  benchmark scalability \
  --python-only
```

These two commands validate only the Python/RDFLib pipeline. They do not prove
that the external products or distributed topologies are installed.

## 6. Prepare the Docker images

Run the Docker-aware diagnostic with the same unprivileged user that will run
the benchmarks:

```bash
python3 tools/doctor.py --docker
```

Build the two shared project images:

```bash
python3 tools/bootstrap.py --with-docker
```

This command:

- reuses the existing `.venv`;
- validates Compose, Buildx and the active Docker daemon;
- builds the Python image shared by RDFLib, Oxigraph and the configured topology
  nodes;
- builds the Java image shared by Jena and RDF4J;
- does not start a benchmark or leave topology nodes running.

The first build may take substantially longer because it downloads Python
wheels, base images and Maven dependencies. Later source/query changes reuse
the dependency layers.

The default local ports are:

| Purpose | Bound host ports |
|---|---|
| Default Docker continuum nodes | `127.0.0.1:8191-8195` (elastic in `configs/topologies/docker/nodes/`) |
| RDFLib, Jena, RDF4J and Oxigraph | `127.0.0.1:8291-8294` |
| Physical workers | LAN TCP port `8391` |

Check for conflicts before starting a campaign:

```bash
docker ps
```

## 7. Verify all four semantic products

The standard smoke commands automatically start RDFLib, Jena, RDF4J and
Oxigraph, execute the suites and stop the product stack:

```bash
.venv/bin/continuum-smoke-cumulative
.venv/bin/continuum-smoke-scalability
```

The semantic roles are intentionally not identical:

- RDFLib/OWL-RL, Jena and RDF4J execute the RDFS-equivalent comparison;
- Oxigraph is the SPARQL control without inference;
- the local benchmark also records RDFS, OWL RL and combined RDFS+OWL RL
  materialisation profiles.

Inspect the stack manually only when diagnosing a startup failure:

```bash
docker compose --progress plain \
  -f docker-compose.engines.yml \
  up -d --build

docker compose -f docker-compose.engines.yml ps -a
docker compose -f docker-compose.engines.yml logs --tail 80
```

Stop that diagnostic stack after inspection:

```bash
docker compose -f docker-compose.engines.yml down
```

## 8. Start and verify the elastic container topology

`configs/topology.toml` is the architecture catalogue. Docker deployment
settings live in `configs/topologies/docker/topology.toml`; node identity,
tier, endpoint, resource limits, authority and category affinities are split
across `configs/topologies/docker/nodes/{cloud,fog,mist,edge,iot}.toml`.
Validate the composed configuration after every edit. The lifecycle command
generates Compose at runtime, so no Python or static Compose rewrite is
required. See [Elastic topology](ELASTIC_TOPOLOGY.md).

Start one cloud, one fog and three edge containers:

```bash
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench topology up --name docker
.venv/bin/continuum-bench topology status --name docker
```

Verify every endpoint shown by `topology show --name docker`. For the default
manifest:

```bash
curl --fail http://127.0.0.1:8191/health
curl --fail http://127.0.0.1:8192/health
curl --fail http://127.0.0.1:8193/health
curl --fail http://127.0.0.1:8194/health
curl --fail http://127.0.0.1:8195/health
```

Run separate distributed smokes with sharded placement:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  docker cumulative \
  --layout sharded \
  --output-dir outputs/docker-smoke-cumulative

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  docker scalability \
  --layout sharded \
  --output-dir outputs/docker-smoke-scalability
```

Run the same checks with a complete replica on each node:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  docker cumulative \
  --layout replicated \
  --output-dir outputs/docker-smoke-cumulative-replicated

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  docker scalability \
  --layout replicated \
  --output-dir outputs/docker-smoke-scalability-replicated
```

The `docker` commands also run the four-product suite unless
`--topology-only` is explicitly supplied.

## 9. Prepare the four Raspberry Pi workers

The default physical layout uses the coordinator as `cloud` and four Raspberry
Pi hosts as `fog`, `edge1`, `edge2` and `edge3`. Its deployment settings are in
`configs/topologies/physical/topology.toml`; add nodes to the corresponding
file under `configs/topologies/physical/nodes/`. The root
`configs/topology.toml` only indexes the monolithic, Docker and physical
manifests. `configs/physical-nodes.toml` is a legacy compatibility inventory.

On every Raspberry Pi, install the worker prerequisites:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv openssh-server rsync procps
python3 --version
sudo systemctl enable --now ssh
```

Python must be at least 3.11. The Raspberry Pi does not need Docker, Java,
Maven, Matplotlib, NumPy, PyOxigraph or Protégé. Deployment installs only the
pure-Python packages pinned in `requirements-node.txt`.

Give the Raspberry Pi stable addresses and make TCP port 8391 reachable from
the coordinator. The repository's default inventory currently expects:

| Role | Address |
|---|---|
| cloud | `127.0.0.1:8391` on the coordinator |
| fog | `192.168.1.137:8391` |
| edge1 | `192.168.1.138:8391` |
| edge2 | `192.168.1.139:8391` |
| edge3 | `192.168.1.140:8391` |

Edit `configs/topologies/physical/topology.toml` if the username or remote
installation directory differs. Edit the appropriate layer file for addresses
and ports. Any positive number of remote roles is supported; retain at least
one cloud, one local coordinator node and one privacy authority. Use a
dedicated remote directory below the SSH user's home; broad paths such as `/`,
`/root` or `/home/pi` are rejected for safety.

On the coordinator, check the required SSH and transfer tools:

```bash
python3 tools/doctor.py --physical
```

Create an SSH key if the coordinator has none:

```bash
ssh-keygen -t ed25519
```

Install the public key on each remote host. The command requests the SSH
password once per Raspberry Pi; subsequent lifecycle commands are deliberately
non-interactive:

```bash
.venv/bin/continuum-bench physical authorize --ssh-user pi
```

Do not store the SSH password in the repository or inventory. Passwordless key
authentication is required because one benchmark performs many remote and HTTP
operations.

Deploy and start the physical cluster:

```bash
.venv/bin/continuum-bench physical stop --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi
```

`deploy` first checks every Raspberry Pi for Python, `venv`, `ensurepip`,
`rsync`, `pgrep` and `nohup`. It does not copy anything until all four machines
pass. It then synchronises only worker runtime assets and creates
`.venv-node` remotely.

If a Raspberry Pi already has its own complete clone, its lightweight
environment can also be prepared manually from that clone:

```bash
python3 tools/bootstrap.py --profile worker
PYTHONPATH=src .venv-node/bin/python -m continuum_bench.node --help
```

The normal coordinator-driven `physical deploy` workflow is preferred because
it keeps all four workers on the same repository revision.

## 10. Verify the physical topology

Run the two small physical suites before a full campaign:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  physical cumulative \
  --layout sharded \
  --ssh-user pi

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  physical scalability \
  --layout sharded \
  --ssh-user pi
```

Repeat with replicated placement when that architecture will be evaluated:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  physical cumulative \
  --layout replicated \
  --ssh-user pi

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  physical scalability \
  --layout replicated \
  --ssh-user pi
```

If a worker is unhealthy, inspect status first and then the corresponding log
under `/home/pi/continuum-bench/runtime/` on that Raspberry Pi. Restart from a
known state:

```bash
.venv/bin/continuum-bench physical stop --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi
```

## 11. Optional independent OWL 2 DL validation

The normal `continuum-bench validate` command checks the repository contract,
SHACL and the benchmark reasoning profiles. Release-grade OWL consistency is a
separate HermiT check because it uses an installed Protégé/OWLAPI runtime and
is intentionally excluded from timed benchmarks.

Install Java 11 or newer (Java 17 is recommended) and Protégé with HermiT,
then run:

```bash
python3 tools/check_owl_consistency.py \
  --require-dl-profile \
  --timeout 180 \
  --output outputs/validation/ontology-english-hermit.json
```

On Linux or for a non-standard Protégé installation, specify its directory:

```bash
python3 tools/check_owl_consistency.py \
  --protege-home /path/to/Protege \
  --require-dl-profile \
  --timeout 180 \
  --output outputs/validation/ontology-english-hermit.json
```

No Protégé files are modified and no reasoner dependency is downloaded by
this script. See [ONTOLOGY_PROTEGE.md](ONTOLOGY_PROTEGE.md) for classpath and
exit-code details.

## 12. Optional ontology diagrams

Install Graphviz using the host package manager, then add the diagram Python
extra to the existing environment:

```bash
.venv/bin/python -m pip install -e ".[diagrams]"
.venv/bin/python -m continuum_bench.diagrams
.venv/bin/python -m pytest tests/test_diagrams.py
```

The generated PDF, SVG, PNG, DOT and GraphML artefacts are written under
`ontology/diagrams`. If Graphviz is not installed, source-only artefacts can
still be regenerated:

```bash
.venv/bin/python -m continuum_bench.diagrams --sources-only
```

## 13. Run the complete benchmark families

Only start full campaigns after every relevant smoke has passed. Full profiles
can take a long time and may intentionally reach configured timeouts.

Monolithic cumulative and scalability suites:

```bash
.venv/bin/continuum-bench benchmark all
```

Elastic Docker topology, both placements:

```bash
.venv/bin/continuum-bench topology up --name docker
.venv/bin/continuum-bench docker all --layout sharded
.venv/bin/continuum-bench docker all --layout replicated
```

Elastic physical topology, both placements:

```bash
.venv/bin/continuum-bench physical status --ssh-user pi
.venv/bin/continuum-bench physical all --layout sharded --ssh-user pi
.venv/bin/continuum-bench physical all --layout replicated --ssh-user pi
```

Load experiment across monolithic, Docker and physical architectures:

```bash
.venv/bin/continuum-bench load all
```

Scale-out, hardware reasoning and truly distributed ontology experiments across
all three architectures:

```bash
.venv/bin/continuum-bench experiment all all
```

Generate the main plots and cross-architecture analysis:

```bash
.venv/bin/continuum-bench plot publication
.venv/bin/continuum-bench load plot
.venv/bin/continuum-bench experiment plot all
.venv/bin/continuum-bench experiment analyze
.venv/bin/continuum-report
```

The complete command catalogue and the meaning of each test are documented in
[TESTS.md](TESTS.md), [BENCHMARKS.md](BENCHMARKS.md),
[LOAD_BENCHMARKS.md](LOAD_BENCHMARKS.md),
[THREE_EXPERIMENTS.md](THREE_EXPERIMENTS.md),
[DOCKER_BENCHMARKS.md](DOCKER_BENCHMARKS.md) and
[PHYSICAL_CONTINUUM.md](PHYSICAL_CONTINUUM.md).

## 14. Resource configuration

The supplied Compose files apply identical defaults to comparable nodes and
engines. To make an explicit campaign-specific change:

```bash
cp .env.example .env
```

Then edit `.env` and record it with the experimental metadata. Available
settings are:

```text
CONTINUUM_NODE_CPUS
CONTINUUM_NODE_MEMORY
CONTINUUM_ENGINE_CPUS
CONTINUUM_ENGINE_MEMORY
CONTINUUM_JAVA_OPTIONS
```

Keep the same engine limit for RDFLib, Jena, RDF4J and Oxigraph. Keep the Java
maximum heap below the container memory limit. Never compare campaigns with
different resource limits as if architecture were the only independent
variable.

Compose build/start operations use a default 1,200-second setup timeout. It can
be changed explicitly for a slow first build:

```bash
CONTINUUM_COMPOSE_TIMEOUT=1800 \
  .venv/bin/continuum-smoke-cumulative
```

Changing this setup timeout does not change the workload/query timeouts defined
in the benchmark configuration files.

## 15. Troubleshooting

### Docker Compose cannot manage the semantic-engine stack

Collect the read-only diagnostic and inspect the retained setup logs:

```bash
python3 tools/doctor.py --docker --json
docker compose -f docker-compose.engines.yml ps -a
docker compose -f docker-compose.engines.yml logs --tail 80
ls -la outputs/runtime/setup
```

| Symptom | Meaning/action |
|---|---|
| `permission denied ... docker.sock` | The current user cannot access the daemon. Fix Docker access, then start a new login session. |
| `Cannot connect to the Docker daemon` | Start Docker Engine/Desktop and inspect `docker context show` and `DOCKER_HOST`. |
| `compose ... unknown command` | Install/upgrade the Compose v2 plugin; the legacy `docker-compose` binary is insufficient. |
| `buildx ... unknown command` | Install `docker-buildx-plugin`. |
| `port is already allocated` | Inspect `docker ps`; do not stop unrelated containers. Required ports are 8191-8195 and 8291-8294. |
| `no matching manifest` or `exec format error` | The active daemon/platform is incompatible. Product images require Linux amd64/arm64 of 64 bits. |
| `credential`, `x509`, DNS, `429` or timeout | Fix registry credentials, certificates, proxy/DNS or rate limits; do not disable TLS. |
| exit `137`, `OOMKilled` | Increase Docker memory or reduce an explicitly documented campaign profile. |
| `no space left on device` | Inspect `docker system df`; do not delete unrelated Docker data automatically. |

If startup fails, the runner preserves the failed containers and records the
command, exit code, last output lines and complete log in
`outputs/runtime/setup/`.

### Python dependency installation fails

Confirm the interpreter and rerun the doctor:

```bash
python3 --version
python3 tools/doctor.py
```

If `venv` or `ensurepip` is missing on Ubuntu, install the matching
`python3-venv` or `python3.X-venv` package. If pip reports that no compatible
binary wheel exists, use CPython 3.11-3.13 on a supported 64-bit Linux/macOS
platform. Do not remove PyOxigraph or loosen constraints to make a nominally
complete coordinator install pass.

### A physical worker is unreachable

```bash
.venv/bin/continuum-bench physical status --ssh-user pi
ssh -o ServerAliveInterval=15 -o ServerAliveCountMax=3 pi@192.168.1.139
```

Check the Raspberry Pi address, SSH service, key authentication, coordinator
route, firewall and TCP port 8391. Ethernet is strongly recommended for
publishable measurements; a Wi-Fi SSH reset does not by itself prove that the
HTTP worker stopped.

### A physical `partitioned-queries` phase times out

The default authority-sharded runner sends bounded groups of eight queries and
arms a worker-side deadline five seconds before the 900-second HTTP deadline.
These values are configured under `[distributed]` in `configs/benchmark.toml`.
Do not enable transport retries to compensate for slow reasoning: a repeated
POST can duplicate the same CPU work. Reduce `query_batch_size` to `4` or `1`
to isolate a slow query, then redeploy and restart every physical worker:

```bash
.venv/bin/continuum-bench physical stop --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi
```

The new terminal diagnostics report the batch number and exact query IDs. Use
the matching node log to distinguish a genuine reasoning timeout from process
termination or memory pressure.

## 16. Stop services cleanly

Stop the Docker topology nodes:

```bash
.venv/bin/continuum-bench topology down --name docker
```

Stop the independent product stack if it was started manually:

```bash
docker compose -f docker-compose.engines.yml down
```

Stop the physical workers without deleting their deployment or results:

```bash
.venv/bin/continuum-bench physical stop --ssh-user pi
```

These commands leave host-side result CSV/JSON/figures and built Docker images
in place.

## 17. Installation acceptance checklist

A coordinator-only installation is ready when all of the following pass:

```bash
python3 tools/doctor.py
.venv/bin/python -m pip check
.venv/bin/continuum-bench validate
.venv/bin/python tools/check_documentation.py
.venv/bin/python -m pytest
```

A complete Docker installation additionally requires:

```bash
python3 tools/doctor.py --docker
.venv/bin/continuum-smoke-cumulative
.venv/bin/continuum-smoke-scalability
.venv/bin/continuum-bench topology up --name docker
.venv/bin/continuum-bench topology status --name docker
```

A complete physical installation additionally requires:

```bash
python3 tools/doctor.py --physical
.venv/bin/continuum-bench physical status --ssh-user pi
```

Do not treat a smoke as benchmark evidence: it proves that the workflow and
expected-result contracts execute on that installation. Generate scientific
measurements with the full profiles, preserve metadata and failures, and avoid
running unrelated heavy workloads concurrently.
