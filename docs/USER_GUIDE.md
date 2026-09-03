# Continuum benchmark user guide

This guide provides the shortest complete path from a clean clone to validated
monolithic, Docker and physical-continuum results. Detailed method and option
references are linked where each step introduces them.

## 1. Select the deployment scope

| Scope | Required host capabilities |
|---|---|
| Monolithic Python | 64-bit CPython 3.11-3.13 |
| Semantic products | Docker, Compose v2 and Buildx |
| Elastic local continuum | Docker plus ports 8191-8195 or configured alternatives |
| Physical continuum | Coordinator plus SSH-accessible Python 3.11+ workers |
| OWL 2 DL release check | Java 11+ and Protégé/HermiT |

Use WSL2 on Windows. A 32-bit Raspberry Pi is supported as a lightweight
physical worker, not as a coordinator or independent Jena/RDF4J/Oxigraph host.

## 2. Install from a clean clone

```bash
git clone https://github.com/MauronMP/Continuum_Monitoring.git
cd Continuum_Monitoring
python3 tools/doctor.py
python3 tools/bootstrap.py
.venv/bin/python -m pip check
```

For Docker:

```bash
python3 tools/doctor.py --docker
python3 tools/bootstrap.py --with-docker
```

Do not copy `.venv`, `.venv-node`, `.env`, credentials or `outputs` from
another machine. Follow [INSTALLATION.md](design/INSTALLATION.md) if any doctor
check fails.

## 3. Validate configuration and semantics

```bash
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench validate
.venv/bin/python tools/check_documentation.py
.venv/bin/python -m pytest
```

Do not proceed to a long campaign until these commands pass. The optional
HermiT gate is documented in [ONTOLOGY_PROTEGE.md](design/ONTOLOGY_PROTEGE.md).

## 4. Run smoke tests

```bash
.venv/bin/python -m pytest -m smoke_cumulative
.venv/bin/python -m pytest -m smoke_scalability
.venv/bin/continuum-smoke-cumulative
.venv/bin/continuum-smoke-scalability
```

The first two are fast development contracts. The latter two create measured
outputs and automatically exercise RDFLib, Jena, RDF4J and Oxigraph. See
[TESTS.md](design/TESTS.md) for Python-only and architecture-specific variants.

## 5. Configure nodes

Edit only the architecture and layer concerned:

```text
configs/topologies/ARCHITECTURE/topology.toml
configs/topologies/ARCHITECTURE/nodes/cloud.toml
configs/topologies/ARCHITECTURE/nodes/fog.toml
configs/topologies/ARCHITECTURE/nodes/mist.toml
configs/topologies/ARCHITECTURE/nodes/edge.toml
configs/topologies/ARCHITECTURE/nodes/iot.toml
```

Then run:

```bash
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench topology show --name ARCHITECTURE
```

Use `monolith`, `docker` or `physical` for `ARCHITECTURE`. The complete field
contract and resize procedure are in
[ELASTIC_TOPOLOGY.md](design/ELASTIC_TOPOLOGY.md).

## 6. Run the monolithic baseline

```bash
.venv/bin/continuum-bench benchmark all
.venv/bin/continuum-bench load monolith
.venv/bin/continuum-bench experiment all monolith
```

This establishes the one-node baseline needed by comparative reports.

## 7. Run the local Docker continuum

```bash
.venv/bin/continuum-bench topology up --name docker
.venv/bin/continuum-bench topology status --name docker

.venv/bin/continuum-bench docker all --layout sharded
.venv/bin/continuum-bench docker all --layout replicated
.venv/bin/continuum-bench load docker
.venv/bin/continuum-bench experiment all docker

.venv/bin/continuum-bench topology down --name docker
```

Leave the topology running between commands to avoid including setup in
measured phases. Use `--topology-only` on `docker` benchmark commands only when
the separate semantic-product dimension is intentionally excluded.

## 8. Deploy and run physical workers

Install Python 3.11+, `python3-venv`, OpenSSH server, `rsync` and `procps` on
every remote host. Configure stable IP addresses in
`configs/topologies/physical/nodes/*.toml`.

```bash
python3 tools/doctor.py --physical
.venv/bin/continuum-bench physical authorize --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi

.venv/bin/continuum-bench physical all --layout sharded --ssh-user pi
.venv/bin/continuum-bench physical all --layout replicated --ssh-user pi
.venv/bin/continuum-bench load physical
.venv/bin/continuum-bench experiment all physical

.venv/bin/continuum-bench physical stop --ssh-user pi
```

Use Ethernet, synchronized clocks, fixed cooling and a fixed power mode for
publication runs. See [PHYSICAL_CONTINUUM.md](design/PHYSICAL_CONTINUUM.md).

## 9. Run all architecture experiments

When Docker and physical workers are already healthy:

```bash
.venv/bin/continuum-bench load all
.venv/bin/continuum-bench experiment all all
```

For clearer failure isolation, run each architecture and experiment separately
as listed in [TESTS.md](design/TESTS.md).

## 10. Generate comparisons

```bash
.venv/bin/continuum-bench compare all
.venv/bin/continuum-bench load plot
.venv/bin/continuum-bench experiment plot all
.venv/bin/continuum-bench experiment analyze
.venv/bin/continuum-bench plot publication
.venv/bin/continuum-report
```

Keep the CSV, JSON and metadata next to PNG/PDF/SVG figures. A comparison is
valid only when matched profiles have equivalent result digests and compatible
ontology, query, reasoner and topology versions.

### Bounded execution and timeout results

The default full configuration uses a 60-second phase/request ceiling and a
90-second complete-point ceiling; smoke configurations use 30 and 45 seconds.
These are acceptance thresholds, not estimates of the eventual completion
time. `summary.csv` records `status=completed`, `timeout`, `transport_error`, or
`skipped_after_timeout`, together with `censored`, `failed_phase`, the threshold
and the error. Larger scalability blocks are not executed after a timeout has
already shown that the topology or engine exceeds the threshold. Do not compute
speedups from censored rows; report completion/timeout coverage with latency.

Edit `[limits]` and `[distributed]` in the selected benchmark TOML to change
the scientific threshold. Use exactly the same values for all architectures in
a comparison and redeploy physical workers after a configuration change.

## 11. Preserve a reproducible campaign

Record:

- Git commit and dirty-worktree state;
- ontology and query release identifiers;
- all TOML configuration files;
- topology fingerprints;
- host OS, CPU, memory, architecture and Python version;
- Docker and image versions where applicable;
- Raspberry Pi model, OS bitness, power mode, cooling and network;
- warm-ups, repetitions, timeouts and failures;
- complete result directories.

Read [SCIENTIFIC_VALIDITY.md](design/SCIENTIFIC_VALIDITY.md) before using a
figure in a paper.

## 12. Stop services

```bash
.venv/bin/continuum-bench topology down --name docker
docker compose -f docker-compose.engines.yml down
.venv/bin/continuum-bench physical stop --ssh-user pi
```

These commands preserve result files and built images.
