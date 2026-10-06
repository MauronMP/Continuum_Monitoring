# Policy-Driven Continuum Monitoring

This project evaluates how policies select and adapt monitoring across a physical
Cloud–Fog–Mist–Edge continuum. The modular ontology is an internal knowledge
mechanism: the primary outcomes are monitoring coverage, adaptation latency,
scalability and computational cost.

Read the [research method and system guide](docs/RESEARCH_METHOD.md) for the proposal, hypotheses, experimental procedure, measurement boundaries and interpretation.

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
The purpose of every software and physical test, together with the exact CSV to
PNG provenance, is documented in
[Test, experiment and figure reference](docs/TESTS_AND_FIGURES.md).

## Four policy evaluation experiments

The controlled evaluator has four independently executable blocks. Decisions
use procedural context rules; ontology validation and a separate reasoning probe
do not establish a semantic advantage. The [comparison module](docs/COMPARATIVE_EVALUATION.md)
implements a distinct semantic decision strategy.

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

Run the larger configured evaluation (publication requires checking its interpretation limits):

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
continuum-bench --timeout-mode bounded --keep-going suite
continuum-bench physical stop --ssh-user pi
```

Bounded execution with `--keep-going` is the recommended mode: deadlines remain
active, while timeout and failed observations are recorded and independent work
continues. `--unlimited` is optional and should be restricted to supervised
diagnosis or a known small profile. It disables coordinator, socket, worker and
native-process deadlines; a DL reasoner can therefore occupy a worker
indefinitely and prevent the remaining matrix from starting. The runner prints
point percentages and pending workers, and checkpoints `progress.json` and
`summary.csv` throughout the run. Timeout and skip controls are in
`configs/benchmark.toml` under `[distributed]` and `[limits]`. See
[Physical continuum](docs/PHYSICAL_CONTINUUM.md) and the
[observed failure review](docs/OBSERVED_FAILURES.md).

Raw timing is retained when canonical validation cannot finish, but those rows
are labelled `unvalidated_results` and excluded from scientific performance
curves. Exact distributed/reference mismatches are labelled `invalid_results`.

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

Shared configuration lives at `continuum_bench.config`. Experiment runners,
budgets, result normalization, analysis and reporting live only under
`continuum_bench.monitoring`; retired top-level experiment facades are not part
of the supported API.

Run the software and documentation checks with:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python tools/check_documentation.py
```

Generated benchmark data, figures, logs and local runtime files are excluded by
`.gitignore` and belong under `outputs/`.

## Optional comparative policy evaluation

The independent [comparative evaluation module](docs/COMPARATIVE_EVALUATION.md) runs paired static,
procedural and semantic policy strategies on the physical hosts. It provides
its own bounded configuration, four experiments, durable JSON/CSV evidence and
per-node PNG figures. Published systems are methodological references, not
claimed reproductions. Mist is excluded by default.

```bash
.venv/bin/python -m continuum_bench.monitoring.comparison check
.venv/bin/python -m continuum_bench.monitoring.comparison run --smoke
.venv/bin/python -m continuum_bench.monitoring.comparison run
```
