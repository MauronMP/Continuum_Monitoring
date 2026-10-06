# Project Audit

Audit date: 6 October 2026. Active release: 0.5.0.

## Conclusion and scope

The local software checks and modular ontology validation pass. The initial physical snapshot below found no running HTTP workers. The authorized
follow-up has redeployed and started Cloud, Fog and the three Edge workers using
an explicit five-node topology; Mist remains offline. See
[Remediation](REMEDIATION.md) for the corrected Konclude conversion, lifecycle
isolation, execution profiles and current verification evidence. The initial
snapshot and test counts below are retained as dated audit evidence.

The audit inventories every existing tracked and unignored repository file,
including untracked source changes. It checks parseable formats, module and query
relations, configuration contracts, execution paths, generated documentation and
local runtimes. Generated outputs and installed dependencies are evaluated
separately. Inventory coverage does not imply a manual proof of every line or
of every ontology axiom. No complete paper manuscript is present in this checkout;
`ontology/diagrams/paper-example.tex` is only a diagram example.

Evidence is stored under `outputs/audit/2026-10-06/` (intentionally ignored by Git).

## Corrections made

| Finding | Correction |
| --- | --- |
| A cost figure stacked batch reasoning time with per-decision policy/plan time. | Reasoning is divided by `decision_iterations`; labels identify the separate probe and amortized units. |
| Effectiveness uncertainty pooled scenarios while claiming repetition uncertainty. | Scenario means are calculated within each repetition before summarizing repetitions. |
| Simulated contexts were described as observed transitions or physical detection. | Figures, metadata and documentation identify supplied contexts, context-read timing and estimated observation volumes. |
| The original evaluator was described as consuming semantic context. | It is explicitly documented as procedural; the independent comparison module consumes semantic tier membership. |
| Missing RSS could appear as zero; non-Linux measurements were ambiguous. | Missing values remain missing; memory provenance distinguishes Linux current RSS and Darwin lifetime peak RSS. Physical comparison requires Linux procfs; CI measurement tests have explicit platform requirements. |
| Topology and load configuration could admit non-finite numerical values. | Domain validation runs on loaded nodes; rate and duration must be finite. |
| JFact provenance contained a Java object address. | The OWLAPI version components are serialized explicitly. A backend-reported zero version remains unknown, not a claimed artifact version. |
| Markdown validation omitted root documents other than README. | All root Markdown files are checked, including CHANGELOG. |
| Audit documentation asserted an obsolete healthy deployment. | Current health and SSH observations replace the stale snapshot. |

Regression tests cover cost units, repetition aggregation, missing RSS and invalid
node capacity/location. Existing scientific CSV/JSON records are not rewritten.

## Architecture and measurement contracts

The reusable `core` owns nodes, capacity, geographic location, policies,
requirements and reasoner interfaces. `monitoring` owns experiment orchestration,
measurement and reporting. Ontology foundation, topology, governance,
observability, orchestration, federation, deployment and optional wellbeing
modules remain separate. No active Docker deployment or retired monolithic
experiment path was found.

`replicated` gives each worker the complete logical graph and distributes queries.
`distributed` places authority-aware fragments, selects sources and merges
answers; shared schema triples may occur in several fragments. This does not
make arbitrary fragment-local OWL DL reasoning equivalent to global closure.
RDFS, HermiT, Openllet, JFact and Konclude retain distinct reasoning contracts.

The comparison module contains controlled static, procedural and semantic
baselines. They are not reproductions of published systems. Its completed smoke
runs verify mechanics; a full comparative campaign has not been run. The older
four-block evaluator measures procedural plan conformance plus a separate
reasoning probe. Its quality score includes policy identifiers alongside
operational items and cannot establish clinical efficacy or semantic benefit.
CPU/RSS sampling covers the Python process, not native reasoner child processes.

## Verification evidence

- `repository.json`: 380 maintained files inventoried with SHA-256 hashes;
  Python, TOML, JSON, XML/SVG/GraphML, Turtle, SPARQL and rectangular CSV checks.
  No unresolved internal ontology IRIs or object/datatype-property collisions.
- `pytest.xml`: full suite, 459 cases: 448 passed and 11 expected skips.
  `regression-tests.xml`: 19 final checks passed, including four subsequently
  added non-finite workload cases (463 cases now collected).
- `native-tests.xml`: all 28 separately enabled native reasoner tests passed.
- `validation.json`: `ok=true`, 7,966 base triples, 115 query contracts pass,
  SHACL conforms with 57 warning-level findings. Fragment reconstruction and
  cloud/fog privacy checks pass.
- `owl-validation.json`: all four native backends available and consistent;
  OWLAPI profile checks pass and no unsatisfiable named class is reported.
- Local RDFS and four native materializations introduce no contradiction or
  violation-query failures. Dependency integrity and documentation checks pass.

The machine-readable test reports are authoritative for counts. Platform-specific
and opt-in skips are not evidence of a successful physical measurement.

## Initial physical-node snapshot (before remediation)

| Node | Tailscale IP | Host access | HTTP worker, port 8391 |
| --- | --- | --- | --- |
| Cloud | 100.86.63.53 | Local host available | Connection refused |
| Fog | 100.93.73.27 | SSH available | Connection refused |
| Edge 1 | 100.101.178.35 | SSH available | Connection refused |
| Edge 2 | 100.70.9.117 | SSH available | Connection refused |
| Edge 3 | 100.121.135.60 | SSH available | Connection refused |
| Mist | 100.72.111.107 | SSH timeout | HTTP timeout |

Evidence: `nodes-health.json` and `nodes-ssh.json`. The four reachable Raspberry
Pis expose four cores, about 8 GB RAM, a 64-bit kernel but 32-bit Python user space,
Python 3.11.2, Java and Konclude. Available root storage is approximately
12.5–13.4 GiB. They share the OS hostname `raspberrypi`; configured node IDs
disambiguate the protocol, but unique hostnames would improve operations.

Mist remains declared in the main topology: silently excluding it would change
the experiment. The separate comparison configuration explicitly excludes Mist.
A refused port is different from a busy worker: during a long request the
single-threaded worker can also delay health responses. Use SSH inspection when
that distinction matters. This snapshot alone does not diagnose service shutdown.

## Remaining scientific and operational limits

1. SHACL's 57 warnings and incomplete acceptance evidence remain. Nine acceptance
   thresholds require justified measurements; reproducibility records also need
   completion. Scientific acceptance is not ready. Do not invent values to pass.
2. Query traceability covers 102/116 requirements and 69/79 policies. The remaining
   items need explicit coverage decisions, not automatically generated claims.
3. Historical distributed Konclude outputs contain semantic mismatches. The
   follow-up reproduced and fixed relative-IRI loss in the OWLlink bridge;
   [Observed failures](OBSERVED_FAILURES.md) explains the cause and evidence.
   Historical invalid rows still cannot support speedup claims.
4. A 32-bit native process can exhaust its address space despite free host RAM.
   Larger physical campaigns still need bounded limits and failure analysis.
5. `--unlimited` can block indefinitely. Prefer bounded campaigns with explicit
   timeout/failure records. Do not treat skipped or censored rows as zero cost.
6. Tailscale supplies connectivity, not geographic distances or controlled WAN
   latency. No clinical stress-detection or mobility validation was performed.
7. Source changes invalidate exact build identity for new physical campaigns.
   Redeploy the same build to selected nodes and recheck readiness before running.
   Preserve historical metadata; do not relabel old results as new executions.
8. Linux checks were executed locally; the configured macOS CI matrix was not
   executed on this machine. Cross-platform fixes still require CI confirmation.

## Repeatable audit

Run from the repository with its virtual environment active:

```bash
python tools/audit_repository.py --output outputs/audit/repository.json
python -m compileall -q src tools tests
python -m pip check
python tools/check_documentation.py
pytest -q --junitxml=outputs/audit/pytest.xml
CONTINUUM_TEST_NATIVE_OWL=1 pytest tests/core/test_native_reasoners.py -q
continuum-bench validate
continuum-bench owl-validate --require-all
continuum-bench physical status --ssh-user pi
```

Follow [Complete execution](COMPLETE_EXECUTION.md) to deploy and verify workers
before launching a campaign. The audit did not run a new full physical campaign.
