# Policy-driven continuum monitoring

A modular architecture for monitoring physical Cloud–Fog–Mist–Edge infrastructure
through policies and an internal ontology. The health/stress example supplies a
motivating domain; it does not constitute a clinically validated detector.
The reusable core models infrastructure, nodes, resources, requirements, policies,
queries and reasoner configuration. The optional wellbeing vocabulary can evolve
without turning benchmark logic into the domain core.

## Documentation index

| Guide | Contents |
| --- | --- |
| [Installation](docs/INSTALLATION.md) | Clean OS dependencies, Python/native backends, Tailscale, inventory and worker deployment. |
| [Complete execution](docs/COMPLETE_EXECUTION.md) | Basic and complementary commands, separated by the two batteries, budgets and recovery. |
| [Experiments](docs/EXPERIMENTS.md) | Technical methods, scientific questions, metrics, interpretation limits and literature. |
| [Outputs](docs/OUTPUTS.md) | Result directories, raw evidence, status semantics and PNG provenance. |
| [Physical continuum](docs/PHYSICAL_CONTINUUM.md) | Six-node inventory, real VPN networking and lifecycle. |
| [Ontology distribution](docs/ONTOLOGY_DISTRIBUTION.md) | Exact files per tier/node, instance ownership, routing and implementation boundaries. |
| [Ontology review](docs/ONTOLOGY_REVIEW.md) | External vocabularies, validation commands and remaining model-data debt. |
| [Python reference](docs/PYTHON_REFERENCE.md) | Every maintained Python file and its responsibility/entry points. |
| [Query guide](queries/README.md) | Query categories, catalogue and execution-plan semantics. |
| [All queries](queries/ALL_QUERIES.md) | Consolidated texts of all 115 maintained queries. |
| [Comparison contract](docs/COMPARATIVE_EVALUATION.md) | Three current adapters, configuration and per-host execution boundaries. |
| [Research method](docs/RESEARCH_METHOD.md) | Architectural claims, fair comparisons and evidence requirements. |
| [Operational remediation](docs/REMEDIATION.md) | Diagnosing versions, busy processes, capacity and semantic failures. |
| [Project audit](docs/AUDIT.md) | Maintained checks and cleanup scope. |

Generated references: [ontology](docs/reference/ONTOLOGY_REFERENCE.md),
[policies](docs/reference/POLICIES.md), [requirements](docs/reference/REQUIREMENTS.md),
[queries and traceability](docs/reference/SPARQL_QUERIES.md).

## The two evaluation batteries

| Battery | Complete entry point | Scope |
| --- | --- | --- |
| Physical architecture | `continuum-bench --timeout-mode bounded --keep-going suite` | Distributed/replicated scalability and cumulative work, load, physical experiments, workload axes, local policy-plan evaluation and reports. |
| Strategy comparison | `python -m continuum_bench.monitoring.comparison run` | Static, procedural and semantic plans, evaluated individually on all six nodes. |

A third four-strategy battery (static, threshold/rule-based, context-aware,
ontology-plus-policy-aware) is planned, **not implemented**. Current results must
not be described as that comparison. Regression checks are software maintenance,
not a third experimental battery. No smoke commands or reduced physical profiles
are exposed. CI validates software and semantic assets; it does not run VPN campaigns.

## Start here

Follow [Installation](docs/INSTALLATION.md) from a clean machine. Once the environment
and workers are installed and synchronized, run from the repository root:

```bash
source .venv/bin/activate
export CONTINUUM_SSH_PROBE_TIMEOUT_SECONDS=120
export CONTINUUM_HEALTH_TIMEOUT_SECONDS=30
continuum-bench physical status --ssh-user pi
continuum-bench --timeout-mode bounded --keep-going suite
```

Run the separate comparison after the first campaign has finished:

```bash
python -m continuum_bench.monitoring.comparison check
python -m continuum_bench.monitoring.comparison run
```

The full command reference, standalone family commands and report regeneration are
in [Complete execution](docs/COMPLETE_EXECUTION.md). Do not modify code/semantic
assets or redeploy during a campaign. A nonzero exit and partial output remain
valid evidence of failure, not successful completion.

## Physical deployment and network

| Tier | Node | Tailscale address |
| --- | --- | --- |
| Cloud | cloud | 100.86.63.53 |
| Fog | fog | 100.93.73.27 |
| Mist | mist | 100.72.111.107 |
| Edge | edge1 | 100.101.178.35 |
| Edge | edge2 | 100.70.9.117 |
| Edge | edge3 | 100.121.135.60 |

All six nodes belong to the active inventory. Real devices are geographically
distributed under the same VPN. `network_mbps` is descriptive capacity, not a cap;
no benchmark command configures traffic shaping. Missing coordinates remain
unknown. IoT instances can appear in workloads, but no standalone IoT worker is
configured. Replicated and distributed are the two runtime placement modes.

## Repository structure

```text
configs/                 Production workloads, reasoners and six-node inventory
ontology/                Core, optional domain modules, profiles, shapes and examples
queries/                 Executable queries, catalogue, routing and generated guide
src/continuum_bench/
  core/                  Reusable domain contracts and node/resource models
  monitoring/            Physical evaluation, metrics and reporting
    comparison/          Independent paired decision comparison
    policy_evaluation/   Local plan-evaluation component of Battery 1
tools/                   Installation, semantic validation and documentation utilities
tests/                   Software regressions; internal fixtures are not campaigns
docs/                    Maintained guides and generated references
outputs/                 Ignored, generated measurements, reports and runtime state
```

RDFS, HermiT, Openllet, JFact and Konclude are explicit backends. The comparison
module deliberately uses RDFS only to isolate its semantic decision mechanism.
Distributed workers reason locally on their fragment; merged query responses are
not a globally complete OWL closure. Author-managed ontology illustrations are
not generated by this repository's code.

## Evidence and limitations

The reference ontology retains reviewed incomplete records and traceability gaps;
see [Ontology review](docs/ONTOLOGY_REVIEW.md). Existing Raspberry Pi userspace has
32-bit capacity limits that can cause native allocation failures at large sizes.
More time does not remove that limit. Supplied-context plan tests do not measure
real fault detection or clinical accuracy. Real VPN conditions vary across runs.
Reports retain failed/missing points and reject unsupported publication claims.
