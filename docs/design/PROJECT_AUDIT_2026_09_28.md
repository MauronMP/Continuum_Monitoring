# Complete project audit — 2026-09-28

## Decision

The current source tree, modular ontology, query catalogue, physical execution
contracts and external reasoner gate are internally consistent. The project is
ready for local validation and for redeployment when the physical hosts are
reachable. It is not ready for a new six-node performance campaign or for
performance claims: four configured hosts are offline, Mist has no reachable
SSH/worker service, and the measurements under `outputs/` belong to older,
incomplete executions.

This audit covers authored source, configuration, ontology and query assets,
documentation, scripts, tests, generated result formats, publication figures
and the observed Tailscale/worker state. Generated environments and caches are
excluded from architectural review.

## Corrections made

- Removed the unrelated local RDF-product benchmark and Java service. New
  experiments run only through the physical continuum worker architecture.
- Removed the Compose-era environment template and retained regression tests
  that reject Docker/Compose deployment assets.
- Restricted physical CLI and benchmark configuration to RDFS, HermiT,
  Openllet, JFact and Konclude. Historical profile names can still be read by
  result normalizers but cannot be selected for a new physical campaign.
- Changed external OWL validation from the archived single-file release to the
  same 14 modules loaded by physical execution.
- Fixed flattened modular OWL validation: all 28 `owl:imports` edges must
  resolve to ontology declarations in the configured union. The temporary
  closed document removes those resolved edges so OWLAPI never dereferences
  project ontology IRIs over the network. Its SHA-256 and triple counts are
  recorded.
- Made the low-level OWL checker require an explicit ontology path, preventing
  accidental fallback to the archived monolithic release input.
- Removed fixed `rdfs`/`owlrl` assertions from tier placement profiles. A
  profile now controls module placement only; each experiment selects its
  reasoner independently.
- Removed the duplicate standalone doctor script. The supported interface is
  `continuum-bench doctor`.
- Added Python 3.14 to portability CI and updated the tested dependency range.
- Corrected duplicated and incomplete policy-cost/mobility documentation and
  improved the static mobility extension point without implementing movement.

## Repository and language

The authored tree contains about 400 files. Python source compiles, every TOML,
JSON and CSV authored asset parses, every Turtle file parses with RDFLib, and
the documentation checker validates links and generated references. No stored
password, API key or private key was found. Source, configuration, comments,
ontology labels used by the active release, generated references and project
documentation are in English. Identifiers such as `CONS`, `CON` and namespace
prefixes are domain codes, not untranslated prose.

Generated results, logs, local runtimes, IDE files, caches, build products and
benchmark evidence remain excluded by `.gitignore`. Generated evidence is kept
under one `outputs/` root with family-specific subdirectories.

## Architecture and module boundaries

| Boundary | Responsibility | Audit result |
| --- | --- | --- |
| `continuum_bench.core` | Reusable continuum nodes, capacities, position, dynamic state and ports | Independent from benchmark orchestration |
| `continuum_bench.monitoring` | Workloads, cumulative/scalability runs, load, experiments, metrics and reporting | Physical-only execution path |
| `continuum_bench.monitoring.study` | Replayable traces, static mobility extension point, network estimates and policy/query cost aggregation | No simulated movement is claimed |
| `continuum_bench.node` | Identical HTTP worker used on physical hosts | Protocol and source build checked by coordinator |
| `continuum_bench.physical_cluster` | SSH deployment and worker lifecycle | No container deployment path |
| `continuum_bench.partitioning` | Replicated and authority-distributed graph construction | Union and privacy contracts tested |
| `continuum_bench.owl_validation` | Independent four-engine OWL 2 DL release gate | Uses active modular graph |

The largest orchestration/reporting modules remain sizeable. Their boundaries
are coherent, but further decomposition is a maintainability improvement rather
than a prerequisite for the current campaign. Root compatibility modules only
redirect old import paths into `monitoring`; they do not implement duplicate
benchmark logic.

## Physical node model

Static node data separates CPU cores and architecture, RAM, storage, processing
capacity, network capacity, device type, authority, tier, endpoint and location.
Dynamic samples separately record CPU, memory, disk and network activity.
`GeographicPosition` supports latitude, longitude, altitude and region; the
current colocated lab inventory declares regions only because measured
coordinates and inter-node distances are unavailable.

Cloud, Fog, Mist and three Edge workers form the six-node configured topology.
The IoT tier is an empty, documented extension point. Random Waypoint, Random
Walk, Manhattan/Grid and Gauss-Markov remain future strategies; only a seeded,
deterministic static local-plane model is implemented.

## Ontology and relationship audit

The active runtime graph is the union of 14 configured files and contains 7,966
triples, 14 ontology declarations, 157 declared classes and 277 declared
properties. All 28 import targets resolve inside the configured union. No local
class referenced by an asserted property domain or range is undeclared.

The ontology is separated into foundation, topology, observability, governance,
orchestration, federation, deployment and wellbeing responsibilities, plus
vocabulary, examples and SHACL constraints. Profiles control tier-specific
placement and do not select reasoners. Stable skolem IRIs preserve identity
when restrictions are split into physical fragments.

The release represents 116 requirements, 79 policies, 55 mechanisms, 17
scenarios and 12 policy categories. Each current policy has one primary
`belongsToPolicyCategory` assertion. The property is not functional and the
model therefore permits a policy to belong to several categories, but this
release contains no multi-category policy individual. Multi-policy queries are
real and their cost attribution uses normalized `1/N` weights. The paper and
documentation must distinguish this implemented query attribution from the
still unevaluated multi-category-policy case.

The category-relation matrix contains the 66 unique pairs among 12 categories,
with explicit relation types and optional conflict-resolution strategies. A
symmetric dependency classification does not itself establish prerequisite
direction; operational ordering still needs directed policy-level evidence.

The archived complete Turtle and SPARQL battery remain controlled release
migration inputs. Physical execution never loads them. Regeneration and tests
require the modular graph and 115 individual query files to remain equivalent
to those release inputs.

## Queries, validation and reasoners

All 115 SPARQL files have exactly one catalogue row and every catalogue path
exists. Query type, expectation, requirement/policy trace and distributed merge
metadata validate. Direct catalogue links cover 102 of 116 requirements and 69
of 79 policies; uncovered identifiers need ontology, SHACL, system-test or new
query evidence.

The structural gate reports:

- 7,966 active triples and 115 queries;
- successful release contract and SHACL conformance;
- zero non-empty violation queries;
- no datatype-range errors or explicit bottom instances;
- an isomorphic union of the six physical fragments;
- no configured privacy-placement violation;
- no unresolved profile import.

RDFS materializes 12,396 triples. HermiT and Openllet each materialize 9,740,
JFact 9,749 and Konclude 9,740 under the finite named-class/individual contract.
The independent external gate loads the flattened 7,938-triple logical document
(the 7,966-triple union minus 28 resolved import statements), obtains 7,773
OWLAPI axioms, passes the OWL 2 DL profile and reports consistency with no
unsatisfiable named class in HermiT, Openllet, JFact and Konclude.

The offline distributed verifier compares every query for every active reasoner
over one canonical graph and six local fragments: 575 checks complete with zero
mismatch. This verifies the implemented query/merge contract; it is not proof
of arbitrary distributed OWL entailment.

## Tests and scripts

The normal suite collects 411 tests: 399 pass and 12 default skips after
removal of obsolete product-matrix tests. The skips are intentional:
native-runtime tests are selected
with `CONTINUUM_TEST_NATIVE_OWL=1`, two partitioned calibration cases are not
applicable, and optional diagram/Protégé integrations depend on local tools.
The installed native-reasoner integration subset passes 48 tests when
explicitly enabled.

Every standalone tool has a source, test or documentation reference. Supported
tools cover clean bootstrap, documentation generation/checking, ontology/query
migration, OWL runtime installation, low-level explicit-file OWL checking,
physical deployment preparation and offline distributed verification. CLI help
and package entry points load successfully.

## Results and figures

All 45 JSON, 57 CSV, 10 JSONL and other structured result files currently under
`outputs/` parse when the CSV field-size limit accounts for serialized query
payloads. Eleven PNG files are nonblank. The active report correctly retains
only five coverage/integrity figures and suppresses performance figures.

`outputs/report/results-audit.json` rejects performance claims because recorded
data mix versions 0.3.1 and 0.4.0, use five rather than six nodes, contain two
failed integrity checks, lack completed load and distributed-ontology points,
omit the distributed-reasoning-scalability dataset and come from an incomplete
suite. These data must remain diagnostic. They cannot support current category,
reasoner, placement or scalability rankings.

## Current physical state

On 2026-09-28, Tailscale reports Fog and Edge 1–3 offline for approximately 13
hours. Mist responds through the Madrid DERP relay but refuses SSH and worker
port 8391. Cloud was restarted from the audited source and reports the current
protocol-9 build ID. A six-node campaign must not start or accept partial
results in this state.

## Scientific acceptance and remaining risks

- `EXT-Q76` and `EXT-Q77` still expose missing quantitative acceptance-profile
  and validation-campaign evidence. Structural validity therefore does not
  permit a scientific compliance claim.
- The existing paper results use the retired three-profile/five-node dataset.
  They must be identified as historical diagnostics or replaced by one complete
  six-node run of the five active reasoners before submission.
- Raspberry Pi workers previously exposed a 32-bit Python user space despite an
  AArch64 kernel. Native Java memory and large OWL DL points may be censored by
  memory before elapsed-time limits.
- Inventory capacities are declared configuration, not calibrated measurements.
  Geographic distance and mobility costs are analytical placeholders until
  coordinates or a validated mobility scenario exist.
- Policy categories organize evidence and cost attribution; the project does
  not yet execute a complete policy-enforcement language or isolate causal
  enforcement overhead.
- The implemented fragment/query contract does not establish complete
  cross-fragment OWL DL entailment for arbitrary ontologies.

## Reproduction gates

```bash
. .venv/bin/activate
python -m pytest
CONTINUUM_TEST_NATIVE_OWL=1 python -m pytest
python tools/check_documentation.py
continuum-bench validate
continuum-bench preflight
continuum-bench owl-validate --require-all \
  --output outputs/validation/owl-reasoners.json
python tools/verify_distributed_reasoning.py \
  --benchmark-config configs/smoke-scalability.toml --users 10 \
  --output outputs/validation/distributed-reasoning.json
continuum-bench physical status --ssh-user pi
```

After all six workers report the current protocol, version, topology fingerprint
and source build ID, run the complete unlimited campaign documented in
[Run all physical tests](RUN_ALL_TESTS.md). Accept timing figures only when the
new suite's `results-audit.json` reports
`accepted_for_performance_claims: true`.
