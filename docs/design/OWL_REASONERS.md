# Automated external OWL reasoner installation

HermiT, Openllet, JFact and Konclude validate OWL 2 DL consistency on the
coordinator. They are deliberately separate from timed RDFS/OWL RL benchmark
materialization and are not installed on Docker/physical workers.

## Prerequisites

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y openjdk-17-jre-headless maven docker.io docker-compose-plugin
sudo systemctl enable --now docker
```

macOS:

```bash
brew install openjdk@17 maven
export PATH="$(brew --prefix openjdk@17)/bin:$PATH"
```

Install/start Docker Desktop when no native Konclude executable is available.

## One-command project installation

Install Python and every external validation dependency during bootstrap:

```bash
python3 tools/bootstrap.py --profile coordinator --with-owl-reasoners
. .venv/bin/activate
continuum-bench doctor --owl
continuum-bench owl-validate --require-all
```

For an existing `.venv`, install only the reasoner runtime:

```bash
. .venv/bin/activate
python3 tools/install_owl_reasoners.py
continuum-bench doctor --owl
continuum-bench owl-validate --require-all
```

The installer:

1. verifies Java 17 and Maven;
2. resolves pinned Maven dependencies from `tools/owl/pom.xml`;
3. writes `.runtime/owl-validation.classpath`;
4. uses an existing native Konclude, or pulls `konclude/konclude` with Docker;
5. writes the optional shell environment file
   `.runtime/owl-reasoners.env`.

The Python validator automatically reads the project classpath, so sourcing the
environment file is normally unnecessary. It can be loaded for direct manual
tool execution:

```bash
. .runtime/owl-reasoners.env
```

`.runtime/` is machine-local and ignored by Git. Re-run the installer after
cloning, changing machines or changing `tools/owl/pom.xml`.

## Pinned Java reasoners

The Maven runtime contains:

| Reasoner | Artifact | Version |
| --- | --- | --- |
| HermiT | `net.sourceforge.owlapi:org.semanticweb.hermit` | `1.4.5.519` |
| Openllet | `com.github.galigator.openllet:openllet-owlapi` | `2.6.5` |
| JFact | `net.sourceforge.owlapi:jfact` | `5.0.3` |

All are invoked through the same OWLAPI checker but with their own factory.
The generated classpath is supplied automatically; Protégé is no longer
required for command-line HermiT validation.

## Konclude execution

`tools/owl/run_konclude.py` provides a stable adapter:

1. loads the configured Turtle ontology with OWLAPI;
2. writes a temporary OWL/XML document, which is Konclude's native format;
3. invokes `CONTINUUM_KONCLUDE_EXECUTABLE`, a `Konclude` binary on `PATH`, or
   the pinned Docker image fallback;
4. mounts only the temporary input directory read-only and disables container
   networking;
5. removes the temporary conversion after the process exits.

To use a native binary instead of Docker:

```bash
export CONTINUUM_KONCLUDE_EXECUTABLE=/absolute/path/to/Konclude
python3 tools/install_owl_reasoners.py --skip-konclude-image
```

To override the container image explicitly:

```bash
export CONTINUUM_KONCLUDE_IMAGE=konclude/konclude
```

## Validation commands

Run every available reasoner while allowing unavailable optional tools:

```bash
continuum-bench owl-validate
```

Release gate requiring all four engines to complete, report consistency, pass
the OWL 2 DL structural profile and report no unsatisfiable named classes:

```bash
continuum-bench owl-validate --require-all
```

Run HermiT alone for diagnostics:

```bash
python3 tools/check_owl_consistency.py \
  --reasoner hermit \
  --require-dl-profile \
  --output outputs/validation/hermit.json
```

Evidence from the combined command is written to
`outputs/validation/owl-reasoners.json`. Missing dependencies remain
`unavailable`; timeouts remain `timeout`; neither is reported as consistency.

## Troubleshooting

```bash
java -version
mvn -version
docker info
docker image inspect konclude/konclude
continuum-bench doctor --owl
```

- Maven download failure: check DNS/proxy access to Maven Central and rerun the
  installer; Maven reuses its local cache.
- Docker permission failure on Linux: configure daemon access for the current
  user, then start a new login session. Do not run the benchmark with `sudo`.
- Apple Silicon image warning: install a compatible native Konclude binary and
  set `CONTINUUM_KONCLUDE_EXECUTABLE`.
- Konclude parse errors: use the project wrapper, not a direct `.ttl` command;
  the wrapper performs OWL/XML conversion.
- Timeout: increase `validation.timeout_seconds` only when a longer logical
  consistency run is scientifically intended.
