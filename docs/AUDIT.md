# Project Audit

Audit date: 2026-09-29. Active release: 0.5.0.

## Scope and verified boundary

The repository implements reproducible evaluation of policy-driven monitoring
on a physical Cloud–Fog–Mist–Edge continuum. The ontology is an internal,
modular knowledge mechanism. Monitoring effectiveness, adaptation, scalability
and computational cost are the primary outcomes.

The audit covers Python source, command-line interfaces, configuration loaders,
ontology modules and SHACL shapes, SPARQL catalogs, external reasoner setup,
physical topology, result contracts, plotting, documentation, packaging, tests
and continuous integration.

## Architecture

| Area | Responsibility | Audit result |
| --- | --- | --- |
| `src/continuum_bench/core` | Infrastructure-neutral domain contracts | Reusable and independent of experiment runners. |
| `src/continuum_bench/monitoring` | Physical orchestration, experiments, metrics and reporting | Owns benchmark-specific behavior. |
| `src/continuum_bench/monitoring/policy_evaluation` | Four policy-monitoring evaluations | Separates decisions, sampling, CSV output and plotting. |
| `ontology` | Foundation, domain, task and application modules | Validated as an internal semantic model. |
| `queries` | Categorized SPARQL catalog and execution plan | Traceable to requirements and policy categories. |
| `configs` | Workloads, budgets, reasoners and topology | Parsed and validated outside experiment code. |
| `tests` | Unit, integration, infrastructure and reporting checks | Does not require a monolithic deployment. |

Top-level modules such as `continuum_bench.config`, `distributed`, `experiments`
and `study` are public compatibility facades. The maintained implementations
remain under `monitoring`; the facades contain no second benchmark engine.

## Placement and reasoning contracts

Physical placement has two unambiguous modes:

- `replicated` prepares a complete logical graph on each selected worker and
  routes a request to one replica.
- `distributed` assigns authority-aware fragments to workers, executes against
  those fragments and merges source results at the coordinator.

The previous `shared` campaign alias was removed because it executed with the
same branch as `distributed` and could therefore mislabel evidence. The active
reasoner matrix is RDFS, HermiT, Openllet, JFact and Konclude. Experiment logic
uses a common reasoner interface and records the selected implementation.

## Reproducibility and evidence

TOML files hold workload sizes, repetitions, warm-up, seeds, reasoners,
concurrency, placement, request budgets and skip policy. Structured outputs are
written under `outputs/` as CSV or JSON before any PNG is generated. Metadata
records the release, configuration, source revision, topology and runtime.

Release 0.5.0 uses the distribution name `continuum-monitoring-benchmark`.
Publication readers retain read-only support for historical metadata created
under `continuum-ontology-benchmark`; new runs emit only the current name.

The clean-install workflow covers Python 3.11 through 3.14 on Linux and macOS.
It runs the complete software test suite, ontology validation, preflight checks,
the four policy-evaluation smoke experiments, PNG generation and documentation
validation.

## Audit evidence

| Check | Result on 2026-09-29 |
| --- | --- |
| Editable package and dependencies | 0.5.0 installed; `pip check` reports no broken requirements. |
| Python compilation | Source, tools and tests compile without errors. |
| Structured configuration | Project TOML and JSON parse; the 115-row query catalog is rectangular. |
| Software suite | 415 tests collected: 403 passed, 12 optional tests skipped, 0 failed. |
| Documentation | 12 Markdown files checked; links and generated references are current. |
| Topology and preflight | Six nodes parsed; 7,966 base triples, 115 queries, 16 categories and all configured targets validated. |
| Internal semantic validation | RDFS, HermiT, Openllet, JFact and Konclude completed with no contradiction, datatype or violation-query error. |
| External OWL gate | HermiT, Openllet, JFact and Konclude report a consistent ontology; OWLAPI reports OWL 2 DL with no unsatisfiable class. |
| Policy evaluation | 120 publication-profile rows completed with no timeout or failure; four nonblank 300 dpi PNG files regenerated. |
| Physical workers | Not executed: all five remote Tailscale peers were offline. |

The policy-driven effectiveness rows match declared ground truth with zero
over-monitoring and under-monitoring. Every dynamic transition matches its
ground truth, and recovery has no stale policy. Scalability progresses from
24 resources, 12 policies and 100 events to 1,536 resources, 768 policies and
8,000 events. All paired computational-cost scenarios completed.

## Physical inventory state

The manifest declares one local Cloud coordinator, one Fog node, one Mist node
and three Edge nodes on Tailscale. At audit time the five remote workers were
reported offline by Tailscale, so deployment compatibility and live physical
execution could not be revalidated. Local topology parsing, protocol contracts,
reasoner prerequisites and physical preflight checks remain verifiable.

Workers must be redeployed before the next physical run because release and
source-build compatibility checks intentionally reject stale worker code.

## Scientific and operational limitations

- Node locations currently contain region labels but no verified latitude,
  longitude or inter-site distance. The project must not present physical
  distance results until measured or configured locations are available.
- Policy-effectiveness ground truth is controlled by the experiment
  configuration. It validates decision correctness against declared scenarios;
  it is not independent clinical evidence of stress-detection effectiveness.
- Network traffic in the policy computational-cost experiment is estimated from
  observation count and configured payload bytes. It is not an interface-level
  packet measurement.
- CPU and resident-memory fields in local policy evaluations measure the
  coordinator process. Physical campaigns record worker telemetry separately.
- Operating-system scheduling, VPN routing and native reasoner startup make
  elapsed-time and resource measurements host-dependent despite deterministic
  workload generation.
- Konclude may warn about unsupported annotation handling. Assertions and query
  results remain the comparable semantic contract; annotations are not used as
  inferred facts.
- Structural validation passes, but the reference ontology's scientific
  acceptance profile remains a draft. `EXT-Q76` reports nine incomplete
  acceptance-profile items and `EXT-Q77` reports six of the seven required
  readiness records. SHACL also reports warning-level gaps for acceptance
  thresholds, model timestamps, AHP scores and historical trust windows. These
  warnings prohibit a blanket compliance claim but do not invalidate the four
  configured policy-monitoring experiments.
- Query traceability currently covers 102 of 116 declared requirements and 69
  of 79 policies. There are no unknown identifiers, but the remaining declared
  entities require either query coverage or an explicit out-of-scope decision.
- Mobility types are represented by extension points only. Random Waypoint,
  Random Walk, Manhattan/Grid and Gauss–Markov simulations are not implemented.

## Revalidation commands

Run from a clean checkout after following `docs/INSTALLATION.md`:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python tools/check_documentation.py
continuum-bench topology validate
continuum-bench validate
continuum-bench preflight
continuum-bench owl-validate --require-all
continuum-bench policy-evaluation all \
  --evaluation-config configs/policy-evaluation-smoke.toml \
  --output-dir outputs/policy-evaluation-smoke
continuum-bench policy-evaluation plot \
  --output-dir outputs/policy-evaluation-smoke
```

Once every remote node is online and redeployed, run:

```bash
continuum-bench physical status --ssh-user pi
continuum-bench --unlimited --keep-going suite
```
