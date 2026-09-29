# Policy-Driven Continuum Monitoring

This project evaluates how policies select and adapt monitoring across a physical
Cloud–Fog–Mist–Edge continuum. The modular ontology is an internal knowledge
mechanism: the primary outcomes are monitoring coverage, adaptation latency,
scalability and computational cost.

## Install

The coordinator requires Python 3.11 or newer. Physical deployment additionally
requires OpenSSH, `ssh-copy-id`, `rsync`, Java 17 and Maven. Konclude is required
only when that native backend is selected.

```bash
git clone https://github.com/MauronMP/Continuum_Monitoring.git
cd Continuum_Monitoring
python3 tools/bootstrap.py --profile coordinator
. .venv/bin/activate
python3 tools/install_owl_reasoners.py
continuum-bench validate
continuum-bench doctor --physical --owl
```

See [Installation](docs/INSTALLATION.md) for clean-host and worker instructions.
The complete ordered command sequence is in
[Complete installation and test execution](docs/COMPLETE_EXECUTION.md).

## Four policy evaluation experiments

The main evaluation has four independently executable blocks:

1. **Policy effectiveness** compares a static plan with policy-driven decisions
   against explicit scenario ground truth.
2. **Dynamic adaptation** executes the controlled sequence normal, overload,
   failure and recovery in one trace.
3. **Policy scalability** jointly increases continuum resources, evaluable
   policies, active categories and context events.
4. **Computational cost** compares static and policy-driven monitoring on the
   same scenarios and resources.

Run a quick end-to-end verification and generate the four PNG figures:

```bash
continuum-bench policy-evaluation all \
  --evaluation-config configs/policy-evaluation-smoke.toml
continuum-bench policy-evaluation plot
```

Run the publication configuration:

```bash
continuum-bench policy-evaluation all \
  --evaluation-config configs/policy-evaluation.toml
continuum-bench policy-evaluation plot
```

The runner writes CSV first. Figure generation is a separate operation and never
changes measured data. See [Experiments](docs/EXPERIMENTS.md) and
[Outputs](docs/OUTPUTS.md).

## Physical continuum

The inventory in `configs/topologies/physical/` declares one Cloud coordinator,
one Fog node, one Mist node and three Edge nodes connected through Tailscale.
The active physical reasoning matrix supports RDFS, HermiT, Openllet, JFact and
Konclude. RDFS is the portable baseline. The policy evaluation uses one configured
reasoner only as an internal cost and does not rank reasoners.

```bash
continuum-bench physical authorize --ssh-user pi
continuum-bench physical deploy --with-dl-reasoners --ssh-user pi
continuum-bench physical start --ssh-user pi
continuum-bench physical status --ssh-user pi
continuum-bench --unlimited --keep-going suite
continuum-bench physical stop --ssh-user pi
```

Use `--unlimited` to record nominal budgets without cancelling slow benchmark
points. Timeout and skip controls are in `configs/benchmark.toml` under
`[distributed]` and `[limits]`. See [Physical continuum](docs/PHYSICAL_CONTINUUM.md).

## Modules

| Path | Responsibility |
| --- | --- |
| `src/continuum_bench/core` | Infrastructure-neutral domain contracts. |
| `src/continuum_bench/monitoring` | Physical orchestration, metrics and reporting. |
| `src/continuum_bench/monitoring/policy_evaluation` | Monitoring-plan engine and four policy experiments. |
| `ontology` | Modular internal knowledge model and validation shapes. |
| `queries` | Categorized SPARQL catalog with policy traceability. |
| `configs/topologies/physical` | Physical node resources, tiers and Tailscale endpoints. |
| `configs/policy-evaluation*.toml` | Reproducible policy scenarios and scalability levels. |
| `tests` | Unit, integration, infrastructure, monitoring and reporting checks. |

The small top-level configuration and experiment modules preserve the public
import API. Their maintained implementations live under `monitoring`; they are
compatibility facades rather than a second benchmark architecture.

Run the software and documentation checks with:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python tools/check_documentation.py
```

Generated benchmark data, figures, logs and local runtime files are excluded by
`.gitignore` and belong under `outputs/`.
