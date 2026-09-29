# Installation

## Coordinator

Install Python 3.11 or newer, Git, OpenSSH client tools, `rsync`, Java 17 and
Maven. Then run:

```bash
git clone https://github.com/MauronMP/Continuum_Monitoring.git
cd Continuum_Monitoring
python3 tools/bootstrap.py --profile coordinator
. .venv/bin/activate
python3 tools/install_owl_reasoners.py
continuum-bench doctor --physical --owl
continuum-bench validate
continuum-bench preflight
continuum-bench owl-validate --require-all
```

`tools/bootstrap.py` creates the local virtual environment and installs the
pinned project dependencies. `tools/install_owl_reasoners.py` prepares isolated
HermiT, Openllet and JFact classpaths. Konclude remains a native executable and
must be available on each host where it is selected.

## Physical workers

Join each host to the same Tailscale network, verify its address against
`configs/topologies/physical/nodes/`, and install Python 3.11 or newer, OpenSSH,
`rsync`, Java 17 and the selected native reasoners. From the coordinator:

```bash
continuum-bench physical authorize --ssh-user pi
continuum-bench physical prepare --ssh-user pi
continuum-bench physical deploy --with-dl-reasoners --ssh-user pi
continuum-bench physical start --ssh-user pi
continuum-bench physical status --ssh-user pi
```

The repository never stores SSH passwords or private keys. Password-based setup
may be used interactively for initial authorization; subsequent experiment runs
must use key-based SSH.

## Verification

```bash
.venv/bin/python -m pytest -q
.venv/bin/python tools/check_documentation.py
continuum-bench policy-evaluation all \
  --evaluation-config configs/policy-evaluation-smoke.toml
continuum-bench policy-evaluation plot
```

The smoke profile verifies contracts and output generation. It is not a
publication-size sample.

See [Complete installation and test execution](COMPLETE_EXECUTION.md) for the
ordered physical deployment, all full-suite commands, per-family execution and
timeout overrides.
