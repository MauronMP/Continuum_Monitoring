# Complete Installation and Test Execution

This guide starts from a clean coordinator, prepares the physical workers and
runs every active test family. Run project commands from the repository root.
For the purpose, evidence files and generated figures of each family, see
[Test, experiment and figure reference](TESTS_AND_FIGURES.md).

## 1. Coordinator system packages

On Ubuntu or Debian, install the required system tools:

```bash
sudo apt-get update
sudo apt-get install -y \
  git \
  python3 \
  python3-venv \
  python3-pip \
  openssh-client \
  rsync \
  openjdk-17-jdk \
  maven \
  konclude \
  graphviz
```

Verify the host before installing the project:

```bash
python3 --version
java -version
mvn -version
Konclude --version
ssh -V
rsync --version
tailscale status
```

Python 3.11 or newer and a 64-bit coordinator runtime are required.

## 2. Clean project installation

Clone and bootstrap the coordinator with all reasoner dependencies:

```bash
git clone https://github.com/MauronMP/Continuum_Monitoring.git
cd Continuum_Monitoring
python3 tools/bootstrap.py \
  --profile coordinator \
  --with-owl-reasoners
. .venv/bin/activate
```

For an existing checkout:

```bash
cd /home/dsdservidor/Documentos/Continuum_Monitoring
python3 tools/bootstrap.py \
  --profile coordinator \
  --with-owl-reasoners
. .venv/bin/activate
```

Verify the installed Python distribution and isolated Java reasoners:

```bash
python -m pip check
python -m pip show continuum-monitoring-benchmark
python tools/install_owl_reasoners.py --verify-only
```

The bootstrap installs pinned HermiT, Openllet and JFact classpaths. Konclude is
a native executable and must be provided by the operating system.

## 3. Physical worker prerequisites

Run the following on each Raspberry Pi worker:

```bash
sudo apt-get update
sudo apt-get install -y \
  python3 \
  python3-venv \
  openssh-server \
  rsync \
  openjdk-17-jre-headless \
  maven
sudo systemctl enable --now ssh
tailscale status
```

Install and verify the native Konclude executable separately on every worker
that will execute the Konclude backend. Package availability depends on the
worker distribution and CPU architecture:

```bash
Konclude --version
```

All workers must belong to the same Tailscale network. The active inventory is:

| Tier | Node | Tailscale address |
| --- | --- | --- |
| Cloud | `cloud` | `100.86.63.53` |
| Fog | `fog` | `100.93.73.27` |
| Mist | `mist` | `100.72.111.107` |
| Edge | `edge1` | `100.101.178.35` |
| Edge | `edge2` | `100.70.9.117` |
| Edge | `edge3` | `100.121.135.60` |

Check each remote peer from the coordinator:

```bash
tailscale ping 100.93.73.27
tailscale ping 100.72.111.107
tailscale ping 100.101.178.35
tailscale ping 100.70.9.117
tailscale ping 100.121.135.60
```

## 4. Authorize and deploy the workers

Activate the coordinator environment and create key-based SSH access:

```bash
. .venv/bin/activate
continuum-bench physical authorize --ssh-user pi
continuum-bench physical prepare --ssh-user pi
continuum-bench physical deploy \
  --with-dl-reasoners \
  --ssh-user pi
continuum-bench physical start --ssh-user pi
continuum-bench physical status --ssh-user pi
```

Initial authorization may prompt for the remote account password. The project
does not store passwords or private keys. All benchmark runs use key-based SSH.

Redeploy workers after a project version or source-build change. The worker
protocol intentionally rejects stale code.

## 5. Mandatory pre-run validation

Run every local and semantic gate before starting a long physical campaign:

```bash
continuum-bench doctor --physical --owl
continuum-bench topology validate
continuum-bench validate
continuum-bench preflight
continuum-bench owl-validate --require-all
continuum-bench campaign \
  --campaign-config configs/campaign.toml \
  --validate-only
.venv/bin/python tools/check_documentation.py
```

`owl-validate --require-all` requires HermiT, Openllet, JFact and Konclude. A
failed reasoner prerequisite must be fixed before a complete run.

## 6. Recommended complete bounded suite

The recommended command enforces the configured request, phase and point
budgets. `--keep-going` records a timeout or real failure and attempts later
independent work:

```bash
continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  suite
```

The complete suite executes:

1. Python unit and integration tests, including native reasoner tests.
2. Documentation validation.
3. Ontology, policy, query and topology validation.
4. External OWL reasoner consistency checks.
5. Distributed physical cumulative and scalability benchmarks.
6. Replicated physical cumulative and scalability benchmarks.
7. The physical load benchmark.
8. Scale-out, hardware reasoning, distributed ontology and distributed
   reasoning scalability experiments.
9. The configurable multi-axis physical campaign.
10. Policy effectiveness, dynamic adaptation, policy scalability and
    computational-cost evaluations.
11. PNG figure and publication report generation.

Each invocation creates an isolated directory:

```text
outputs/suites/<UTC timestamp>-<run identifier>/
```

Long physical phases print the active family, reasoner, load, repetition and
stage. Worker heartbeats appear every 15 seconds, and each family updates
`progress.json` plus its checkpointed `summary.csv`. A deadline is recorded as
`timeout`; a native reasoner or implementation error is recorded as `failed`.
Both remain visible in the suite manifest and final report. The suite returns a
nonzero status when evidence is incomplete even though it continues through its
planned top-level steps.

Inspect the planned commands without contacting a worker:

```bash
continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  suite \
  --dry-run
```

## 7. Longer campaigns

Override repetitions when a larger sample is required:

```bash
continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  --repetitions 5 \
  suite
```

For a larger publication campaign:

```bash
continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  --repetitions 10 \
  suite
```

Increasing repetitions changes sample size and total duration. It does not
change the configured scale points, policy categories or reasoner matrix.

## 8. Run each family independently

### Software tests

Enable the installed native reasoner checks explicitly:

```bash
CONTINUUM_TEST_NATIVE_OWL=1 \
  .venv/bin/python -m pytest \
  -o addopts= \
  -q \
  -ra
```

### Documentation

```bash
.venv/bin/python tools/check_documentation.py
```

### Distributed physical monitoring

```bash
continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  physical all \
  --layout distributed \
  --output-dir outputs/monitoring
```

Bounded execution records slow points as timeouts. It does not turn a reasoner
crash or a semantic validation failure into success. The coordinator continues
with independent points, checkpoints each outcome and reports
`unvalidated_results` when physical timing completed without a completed
canonical reference. Publication reports use only `completed` points with exact
reference validation.

### Replicated physical monitoring

```bash
continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  physical all \
  --layout replicated \
  --output-dir outputs/monitoring
```

### Cumulative tests

```bash
continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  physical cumulative \
  --layout distributed \
  --output-dir outputs/monitoring

continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  physical cumulative \
  --layout replicated \
  --output-dir outputs/monitoring
```

### Scalability tests

```bash
continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  physical scalability \
  --layout distributed \
  --output-dir outputs/monitoring

continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  physical scalability \
  --layout replicated \
  --output-dir outputs/monitoring
```

### Physical load benchmark

```bash
continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  load physical \
  --load-config configs/load-benchmark.toml \
  --output-dir outputs/load
```

### Physical experiments

```bash
continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  experiment all physical \
  --experiment-config configs/experiments.toml \
  --distributed-reasoning-config configs/distributed-reasoning.toml \
  --output-dir outputs/experiments
```

### Multi-axis physical campaign

```bash
continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  campaign \
  --campaign-config configs/campaign.toml \
  --output-dir outputs/campaign
```

### Four policy evaluations

```bash
continuum-bench policy-evaluation all \
  --evaluation-config configs/policy-evaluation.toml \
  --output-dir outputs/policy-evaluation

continuum-bench policy-evaluation plot \
  --output-dir outputs/policy-evaluation
```

## 9. Timeout strategy and optional unlimited execution

Bounded mode is the normal execution strategy. The following example permits
300 seconds per worker request, 600 seconds per phase and 1,800 seconds per
point while attempting every configured observation:

```bash
continuum-bench \
  --timeout-mode bounded \
  --request-timeout-seconds 300 \
  --phase-timeout-seconds 600 \
  --point-timeout-seconds 1800 \
  --skip-after-timeouts 2 \
  --no-skip-repetitions \
  --no-skip-larger-points \
  --no-skip-cumulative-stages \
  --keep-going \
  suite
```

Persistent defaults are stored in:

- `configs/benchmark.toml`: global request, phase, point and skip policy.
- `configs/load-benchmark.toml`: physical load sizes and repetitions.
- `configs/experiments.toml`: scale-out and hardware experiments.
- `configs/distributed-reasoning.toml`: distributed reasoning scales.
- `configs/campaign.toml`: multi-axis physical campaign.
- `configs/policy-evaluation.toml`: four policy-monitoring evaluations.

Command-line values override the configuration files for one invocation.

`--unlimited` is optional. It disables coordinator, HTTP, worker and native
reasoner deadlines. Use it only for a supervised, reduced profile whose runtime
is already understood:

```bash
continuum-bench \
  --unlimited \
  --keep-going \
  --repetitions 1 \
  physical scalability \
  --reasoner rdfs \
  --layout distributed \
  --output-dir outputs/diagnostic-unlimited
```

`--keep-going` cannot recover control while an unbounded native call is still
running. In particular, HermiT, Openllet, JFact or Konclude may continue for
hours on constrained nodes. An unlimited run can therefore remain on one point
without reaching the next reasoner, repetition or family.

Do not use `Ctrl+Z` to leave a physical campaign in the background. The current
coordinator ignores that suspend signal while it holds the physical lease and
prints a warning. Use `Ctrl+C`, then stop and restart the workers before a new
campaign if a native child remains active.

The worker service handles one request at a time so that its Unix phase timer
can interrupt bounded CPU work. During a long native reasoner request,
`/health` also waits and may time out. Check the worker and Java/Konclude child
over SSH before classifying that node as offline.

## 10. Stop the workers

Stop the remote services after all output has been written:

```bash
continuum-bench physical stop --ssh-user pi
```

This command removes stale PID files and terminates project-owned native Java
materializers left by an interrupted worker. Current workers also clean their
active Java or Konclude process group when they receive `SIGTERM`.

The shortest complete sequence after installation is:

```bash
cd /home/dsdservidor/Documentos/Continuum_Monitoring
. .venv/bin/activate
continuum-bench physical start --ssh-user pi
continuum-bench physical status --ssh-user pi
continuum-bench --timeout-mode bounded --keep-going suite
continuum-bench physical stop --ssh-user pi
```

Do not start a physical suite while another campaign holds the physical lease.
Do not interpret results from a run whose workers failed release, source-build
or topology compatibility checks. Metadata from current runs contains
`software_build_id` and `topology_fingerprint`; missing values are treated as
historical, incompatible evidence.

## Optional comparative policy evaluation

The independent [comparative evaluation module](COMPARATIVE_EVALUATION.md) runs paired static,
procedural and semantic policy strategies on the physical hosts. It provides
its own bounded configuration, four experiments, durable JSON/CSV evidence and
per-node PNG figures. Published systems are methodological references, not
claimed reproductions. Mist is excluded by default.

```bash
.venv/bin/python -m continuum_bench.monitoring.comparison check
.venv/bin/python -m continuum_bench.monitoring.comparison run --smoke
.venv/bin/python -m continuum_bench.monitoring.comparison run
```

## Five-node operation while Mist is offline

Use the explicit topology and bounded smoke profile described in
[Audit remediation](REMEDIATION.md#operating-while-mist-is-offline). Deploy, start
and run with the same `--topology-file` selection. Do not combine five-node and
six-node outputs or silently remove Mist from the standard topology.
