# Run all physical tests

This is the operational entry point for the current five-reasoner continuum.
Run commands from the repository root with `.venv` activated. Configuration,
installation and historical measurements are documented separately; historical
RDFS/OWL-RL results are not evidence for the current native comparison.

## 1. Prepare a clean environment

Follow [installation](INSTALLATION.md). On Debian/Raspberry Pi OS, install Java
17 JDK, Maven and Konclude on the coordinator and every participating worker:

```bash
sudo apt-get update
sudo apt-get install -y openjdk-17-jdk maven konclude
```

On the coordinator, after cloning and bootstrapping:

```bash
. .venv/bin/activate
python tools/install_owl_reasoners.py
continuum-bench topology validate --name physical
continuum-bench doctor --physical --owl
```

The native adapters prefer installed isolated classpaths; inherited Protégé
variables do not override them. No shell-profile edits are required. The remote
32-bit runtimes use a 512 MiB Java heap; larger workloads may exhaust memory
even in unlimited mode. See [reasoner configuration](OWL_REASONERS.md).

## 2. Deploy or check the existing deployment

| Node | Tailscale IP |
| --- | --- |
| Cloud/coordinator | `100.86.63.53` |
| Fog | `100.93.73.27` |
| Edge 1 | `100.101.178.35` |
| Edge 2 | `100.70.9.117` |
| Edge 3 | `100.121.135.60` |

The inventory is `configs/topologies/physical/topology.toml` with per-tier files
in `nodes/`. SSH uses `pi` on remote nodes; HTTP endpoints use port 8391.
Cloud advertises its VPN IP while retaining local process management.

For a fresh deployment or changed worker code, with no campaign running:

```bash
continuum-bench physical authorize --ssh-user pi
continuum-bench physical stop
continuum-bench physical deploy --with-dl-reasoners
continuum-bench physical start
continuum-bench physical status
```

Key authorization is needed only once. For an unchanged deployment, use
`physical status`; restart or deploy only when needed. The suite starts existing
deployments but does not install packages or synchronize code. Do not run two
campaigns against the same workers: preparation replaces their active graph.
See the [recorded Tailscale validation](../deployment/TAILSCALE_VALIDATION.md).

## 3. Check the launch plan

```bash
continuum-bench --unlimited --repetitions 5 suite --dry-run
```

This writes and prints `suite.json` with exact commands and environment overrides.
It does not contact workers or execute tests. Each invocation gets a unique UTC
timestamp/ID directory under `outputs/suites/`.

## 4. Run the complete suite

```bash
continuum-bench --unlimited --repetitions 5 suite
```

Keep the terminal/session alive for long runs. This executes sequentially:

1. Software tests with native OWL integration enabled, JUnit evidence, and
   documentation validation.
2. Semantic validation, load/experiment preflight, and strict external OWL
   validation requiring HermiT, Openllet, JFact and Konclude.
3. Campaign configuration/topology preflight and physical worker startup.
4. Cumulative and scalability monitoring, distributed then replicated.
5. All configured load profiles and the three physical experiments.
6. The ten-axis policy/scalability campaign in both configured layouts.
7. Publication reporting from that run's evidence, with PNG figures.

RDFS, HermiT, Openllet, JFact and Konclude are the default profiles. Separate
native semantic products (Jena, RDF4J, Oxigraph), optional Graphviz rendering
and study trace generation require their own setup and are not secretly
installed or included by this command.

The full campaign can be expensive: the monitoring configuration reaches 5,000
synthetic users, while the campaign varies ten axes. Unlimited mode removes
benchmark time limits and timeout pruning, not memory limits or correctness
checks. Load duration still determines the offered workload. Startup/health
checks and external OWL validation retain their operational limits.

## 5. Short acceptance run or finite budgets

For a smaller end-to-end benchmark plan, retain the five-reasoner monitoring
smoke and select the separate smoke configurations explicitly:

```bash
continuum-bench --config configs/smoke-scalability.toml --unlimited \
  --repetitions 1 suite --load-config configs/load-smoke.toml \
  --experiment-config configs/experiments-smoke.toml \
  --campaign-config configs/campaign-smoke.toml --dry-run
```

Remove `--dry-run` to execute it. `physical all` still includes cumulative
monitoring with every configured category, so this is more than a connectivity
check. The minimal connectivity check uses `configs/smoke-vpn.toml`; it defaults
to RDFS and is not a replacement for all-five-reasoner acceptance.

```bash
continuum-bench --timeout-seconds 7200 --keep-going --repetitions 3 suite
continuum-bench suite --patient
```

The first enforces two-hour request/phase/point budgets and disables timeout
pruning. `--patient` uses one-hour budgets unless explicitly overridden. For
independent monitoring budgets and skip triggers, see
[execution controls](PHYSICAL_REASONING.md). Global options precede `suite`.

## 6. Select stages and inspect results

```bash
continuum-bench suite --families software validation
continuum-bench --unlimited suite --families monitoring load experiments campaign report
```

The second command is for an already validated deployment. The configurable
files are `--config` (monitoring), and suite-local `--load-config`,
`--experiment-config`, `--campaign-config`. A global `--topology-file` override
is forwarded to all benchmark subprocesses. Repetitions are overridden across
families; warm-up, load dimensions and seeds remain in the respective TOMLs.

Each run records `suite.json`, individual step logs, `software-tests.xml`,
provenance, benchmark CSV/JSON/JSONL and `paper/` reports. Read the printed output
directory, then inspect it, for example:

```bash
cat outputs/suites/<run-id>/suite.json
tail -f outputs/suites/<run-id>/monitoring-distributed.log
continuum-bench report --input-dir outputs/suites/<run-id> \
  --output-dir outputs/suites/<run-id>/report
```

Replace `<run-id>` with the actual directory name. A failed subprocess or
missing measurement evidence makes the suite exit nonzero. Recorded monitoring,
load and experiment timeouts/skips are distinct outcomes; they are not successful
measurements even when the runner exits zero. Campaign errors use its own
nonzero exit contract. Later stages continue after failures so logs and reports
remain available; inspect all step statuses before accepting a run.

Interrupting a run does not resume it automatically. Preserve partial evidence,
check worker state, and start a new suite directory. Stop services only when no
other authorized run is using them:

```bash
continuum-bench physical stop
```

The [test catalogue](TESTS.md) and [command reference](COMMAND_REFERENCE.md)
describe individual families, configuration and interpretation limits.
