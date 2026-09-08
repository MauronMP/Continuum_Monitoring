# Installation and environment preparation

This guide starts from a clean clone. Run every command from the repository root.

## 1. Coordinator prerequisites

Required for every installation:

- Git;
- 64-bit Python 3.11 or newer, including `venv` and `pip`;
- enough disk space for generated RDF data and `outputs/`;
- POSIX shell commands. Windows users should use WSL2.

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip build-essential
```

macOS: install Git and Python 3.11+ with Homebrew or python.org. Confirm the
selected interpreter before creating the environment:

```bash
python3 --version
python3 -c "import platform; print(platform.machine())"
```

## 2. Clone and bootstrap

```bash
git clone https://github.com/MauronMP/Continuum_Monitoring.git
cd Continuum_Monitoring
python3 tools/bootstrap.py --profile coordinator
. .venv/bin/activate
continuum-bench --help
```

`tools/bootstrap.py` creates `.venv`, upgrades the packaging tools and installs
the project with its test dependencies. It does not require SSH/rsync
or Java unless that optional target is used. Add the optional `diagrams` extra only
when regenerating the ontology atlas. The equivalent manual
installation is:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev,diagrams]"
```

Do not copy a virtual environment between machines or architectures; run the
bootstrap again after cloning.

## 4. Physical workers

The coordinator needs an SSH client, `ssh-copy-id` and `rsync`:

```bash
sudo apt-get install -y openssh-client rsync
```

Install the following packages once on every Debian/Raspberry Pi OS worker:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip openssh-server rsync procps
sudo systemctl enable --now ssh
```

Python 3.11+ is required. A 32-bit Raspberry Pi is supported through the
lightweight worker profile; do not install or copy the coordinator `.venv` to
it. Configure addresses, ports, architectures and tiers in
`configs/topologies/physical/nodes/*.toml`, then install SSH keys and deploy:

```bash
continuum-bench doctor --physical
continuum-bench physical authorize --ssh-user pi
continuum-bench physical deploy --ssh-user pi
continuum-bench physical start --ssh-user pi
continuum-bench physical status --ssh-user pi
```

The deployment creates `.venv-node` remotely with the worker profile. Passwords
must not be stored in TOML or source control; `authorize` configures key-based
authentication.

## 5. External OWL 2 DL reasoners

The portable benchmark materializers (`rdfs`, `owlrl`, `rdfs_owlrl`) are Python
dependencies. HermiT, Openllet, JFact and Konclude are separate ontology
consistency validators and are not silently substituted when unavailable.

Install Java 17, Maven and native Konclude, then use the project installer:

```bash
sudo apt-get install -y openjdk-17-jre-headless maven konclude
python3 tools/install_owl_reasoners.py
```

The installer resolves pinned HermiT, Openllet and JFact dependencies into
separate classpaths, preventing incompatible transitive OWLAPI libraries from
being mixed. It then self-tests all three Java factories and executes a real
Konclude consistency smoke through the native backend. Turtle
is converted to OWL/XML before Konclude. The same operation can be requested
during initial setup with
`python3 tools/bootstrap.py --profile coordinator --with-owl-reasoners`.
Platform-specific details are in [External OWL reasoners](OWL_REASONERS.md).

```bash
continuum-bench doctor --owl
continuum-bench owl-validate
continuum-bench owl-validate --require-all
```

Use `--require-all` only as the strict release gate: it fails if any configured
reasoner is missing, times out, reports inconsistency or cannot complete.

## 6. Installation verification

```bash
continuum-bench doctor --physical --owl
continuum-bench topology validate --name physical
continuum-bench validate
continuum-bench preflight
python -m pytest
python3 tools/check_documentation.py
```

`continuum-bench validate` checks parsing, SHACL, query contracts and portable
materialization. It does not prove OWL 2 DL consistency; that is the purpose of
`owl-validate`.

`continuum-bench preflight` calculates the exact asserted graph lower bound for
every load and experiment profile. It rejects an impossible `target_triples`
value locally, before an HTTP request can become a worker-side 400 response.
