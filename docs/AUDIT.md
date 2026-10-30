# Maintained project audit

## Scope of the current cleanup

The active project exposes three evaluation batteries, including the opt-in
container scalability module. The earlier cleanup removed obsolete smoke
entry points and public reduced profiles, five-node deployment variants, the
completed namespace-migration utility, redundant standalone preparation/verification
wrappers, implicit Protégé dependency discovery and the ontology illustration generator.
Retained internal regression fixtures, meaningful code/semantic assertions and
native dependency verification. CI runs these software checks without physical
campaigns or benchmark figure generation.

The `diagrams` packaging extra and its tests were removed. Core runtime
requirements remain RDFLib, owlrl, pySHACL, NumPy and Matplotlib, with pytest in
the development extra. Native reasoners remain separately installed. Campaign
CLI defaults now select `configs/campaign.toml`, the complete production profile.

The source inventory is [Python reference](PYTHON_REFERENCE.md). The generated
[query bundle](../queries/ALL_QUERIES.md) contains all catalogue queries; its
routing guide is [Queries](../queries/README.md). Documentation checks detect
stale generated indexes and broken local links.

## Validation and interpretation

Use the commands in [Complete execution](COMPLETE_EXECUTION.md) for software and
semantic validation. `tools/audit_repository.py` inventories maintained files and
checks syntax; it does not prove scientific validity or discover all dead code.
CLI entry points and standalone tools can be used without being imported by other
modules and must not be deleted solely on import counts.

The review verified that `network_mbps` is metadata, not rate limiting. Actual
VPN traffic remains unshaped. Analytical network estimates are labelled separately.
The two native batteries retain their six-worker inventory. The container battery now includes Mist again and uses all six physical hosts.
Earlier five-host evidence retains its explicit exclusion metadata. Reported health is a point-in-time observation and
becomes stale after source/semantic edits.

Known boundaries remain in [Ontology review](ONTOLOGY_REVIEW.md),
[Ontology distribution](ONTOLOGY_DISTRIBUTION.md) and [Remediation](REMEDIATION.md).
Historical measurements, logs and author-supplied figures are preserved; deleting
old launch profiles does not invalidate the provenance of archived acquisitions.

## Verification on 13 October 2026

The final native-enabled regression run passed 465 cases with no failures or
skips. Three expected Konclude warnings state that annotations are excluded from
its logical request and preserved in the returned RDF. Package dependency checks,
52 documented CLI argument sequences, workload preflight, topology validation,
repository syntax/inventory and generated-document checks passed. The ontology
module audit reports no errors; the validation-debt review retains 57 warnings.
Evidence is under `outputs/audit/project-cleanup-20261013/`. These are maintenance
checks, not a newly acquired scientific campaign.

## Completion review on 14 October 2026

The final import review removed the unused `monitoring/results.py` field tuple.
The Python reference now covers 152 maintained Python files. All 22 targeted
result-contract, release and physical-infrastructure regressions passed after
this deletion. Repository inspection covers 387 maintained files and reports no
syntax errors or undefined internal ontology subjects. Documentation validation
checks 21 guide files and the generated query/Python indexes.

The requested documentation responsibilities are separated as follows:

| Request | Maintained implementation or guide |
|---|---|
| Real VPN capacity without shaping | Physical node inventory and [Physical continuum](PHYSICAL_CONTINUUM.md) |
| Remove public smoke/reduced runs and obsolete tooling | CLI, packaging, internal regression fixtures and portability workflow |
| Complete commands for three batteries | [Complete execution](COMPLETE_EXECUTION.md) |
| Scientific contracts and primary references | [Experiments](EXPERIMENTS.md) |
| Clean installation and six-node setup | [Installation](INSTALLATION.md) |
| Ontology placement and distribution limits | [Ontology distribution](ONTOLOGY_DISTRIBUTION.md) |
| Ontology validation and external vocabulary boundaries | [Ontology review](ONTOLOGY_REVIEW.md) |
| Result families and provenance | [Outputs](OUTPUTS.md) |
| Navigation | [Documentation index](README.md) and [repository README](../README.md) |
| Python file responsibilities | [Python reference](PYTHON_REFERENCE.md) |
| All queries, categories and execution routing | [Query guide](../queries/README.md) and [query bundle](../queries/ALL_QUERIES.md) |
| Author-managed ontology figures | Generation package removed; existing author assets preserved |

The planned third battery remains explicitly future work. The 57 ontology
validation warnings remain disclosed; this maintenance pass does not claim to
resolve missing scenario evidence or to acquire new scientific measurements.

After source synchronization and controlled service restart, all six physical
workers passed the health contract with matching source build, semantic asset
digest and topology fingerprint. The independent comparison availability check
also passed for all six hosts. Point-in-time evidence is in
`outputs/audit/project-cleanup-20261014/final-status.json` and
`outputs/audit/project-cleanup-20261014/comparison-check.json`.

## Result retention update

On 14 October 2026, at the user's request, older results and maintenance evidence
(including the audit output paths cited above) were deleted. Those paths describe
historical checks and are no longer available locally. Only the latest acquired
physical suite and comparison run remain, together with operational runtime state.
See [Outputs](OUTPUTS.md) for the retained directories and their actual outcomes.


## Fresh project review — 14 October 2026

This review reran the checks after result cleanup; evidence is grouped in
`outputs/audit/current-review/`, separate from scientific acquisitions.

| Area | Fresh result | Interpretation |
| --- | --- | --- |
| Native-enabled software regression | 465 passed; no failures or skips; three expected Konclude annotation warnings | Current regression contracts pass. |
| Repository inventory | 387 maintained files; no syntax errors or undefined internal ontology subjects detected | Automated structural audit, not proof that every possible defect is absent. |
| Documentation and dependencies | 21 guides and generated references validated; dependency check passed | Local links/indexes and installed package requirements agree. |
| Modular ontology | Module/import/profile checks passed | Declared placement and ownership are structurally consistent. |
| Native consistency | HermiT, Openllet, JFact and Konclude all consistent | Reference ontology only; not proof about every generated workload. |
| Distributed RDFS diagnostic | 115/115 queries matched canonical results at 12 users | Local six-fragment semantic check, not new network performance evidence. |
| Physical services | Six healthy nodes with compatible fingerprints | Point-in-time operational readiness. |
| Comparison evidence | 720 completed jobs, 120 per host; raw records validate; summary recomputation has no differences | No missing listed figures; configured-plan evaluation only. |
| Image inspection | 101 PNGs decoded successfully; no near-blank images; all inspected in contact sheets | Legends/data are present. Dense all-node grids are overview/supplementary material; per-node panels are easier to read in a paper. |

The current source review covered comparison adapters, paired input validation,
measurement checks, report aggregation and module-boundary regressions. No new
runtime defect was reproduced in this pass; no speculative source change was
made merely to make the audit appear productive.

### Corrections made

The retained physical suite's reading guide still requested a full six-node
comparison and referred to a deleted reduced run. It now points to the completed
9 October comparison and distinguishes it from the incomplete physical suite.
Historical Mist-offline wording is dated explicitly. Numeric evidence and figures
were not relabelled as current acquisitions or silently regenerated.

### Remaining limitations

- SHACL still reports 57 reviewed warnings: 32 missing AHP inputs, 2 model
  timestamps, 14 trust-window boundaries and 9 acceptance parameters. Review
  dispositions are not evidence that these omissions are resolved.
- Traceability remains 102/116 requirements and 69/79 policies; three reference
  observations have unknown measurement units. Missing values were not invented.
- The retained physical acquisition has 18 distributed scalability timeouts,
  30 replicated scalability timeouts and 3 failures. Load has 227 completed,
  105 timed-out and 28 failed observations. Its four independent experiment
  families and campaign remain unacquired. The complete-publication gate still
  rejects this suite.
- All 23,640 recorded distributed semantic comparisons are valid; this says
  nothing about workloads that failed before producing comparable answers.
- Diagnostic curves based on completed observations can have survivor bias.
  They must accompany completion/capacity figures, not replace them.
- The comparison uses supplied contexts and configured acceptance plans. It
  establishes neither live service recovery nor superior clinical accuracy.
- The retained campaigns predate current source and ontology revisions. Fresh
  campaign evidence is required to evaluate this version scientifically.

No new full physical campaign was launched, and workers were not redeployed:
source and semantic fingerprints remain unchanged by these documentation fixes.


## Focused validation-debt review

The follow-up review hardened `review_validation_debt.py`: familiar property
names no longer mask invalid datatypes, blocking SHACL constraints or release
contract errors. The reference graph still has 57 missing-evidence warnings and
zero violations; no historical value or acceptance threshold was invented.
[Validation gaps](VALIDATION_GAPS.md) lists every uncovered requirement/policy,
closure criteria and the observed failure breakdown. The replicated-scalability
summary was corrected to distinguish two allocation failures from one native
Konclude crash with undetermined cause. Generated manuals now identify hard
constraint precedence as normative design rather than demonstrated enforcement.


## Scope adaptation — 19 October 2026

The user requested adapting the unsupported requirements/policies to the actual
project. Fourteen requirement statements and ten policy statements now have
explicit model-query or software verification boundaries. All identifiers and
entity inventories are preserved. Original statements are recorded in
`configs/scope-contracts.toml`; generated manuals expose the changed scope.

Query traceability is now 106/116 requirements and 73/79 policies. The remaining
10 requirements and 6 policies have software contracts rather than forced SPARQL
links. This supersedes the pre-adaptation coverage figures above, without
reinterpreting historical scientific evidence. See [Scope adaptation](SCOPE_ADAPTATION.md).

The semantic revision is `4.0.0-monitoringcontinuum-v2`, with policy artifact
`POLICIES-REV-02`. No numerical data, query bodies, ontology classes or historical
result files were changed in this adaptation. Query metadata gains only directly
relevant references. The 57 historical-evidence warnings remain; no blocking
SHACL violation was found in the adapted reference model.


Validation of this adaptation passed 472 native-enabled regression cases with no
failures or skips (three expected Konclude annotation warnings). All four native
reasoners found the reference ontology consistent; the local six-fragment RDFS
check matched all 115 queries at 12 users. The module audit, dependency checks,
391-file repository inspection and generated-document validation passed.
Evidence is grouped in `outputs/audit/scope-adaptation/`. These are engineering
and semantic checks, not new scientific benchmark results.

After deployment and controlled startup, all six workers passed the health
contract with matching source and semantic digests and ontology revision
`4.0.0-monitoringcontinuum-v2`. The point-in-time health evidence is in
`outputs/audit/scope-adaptation/nodes.json`. No scientific campaign was launched.

## Container deployment verification on 20 October 2026

Battery 3 adds host-local Compose projects and an explicitly coordinated
container scalability runner. Cloud, Fog and the three Edge hosts passed the live
Docker/Compose, free-memory, disk and cgroup-limit checks. Mist was explicitly
excluded because it was powered off; the maintained default inventory still
contains all six hosts. Raspberry memory controllers were enabled before
acquisition. Old `policy-benchmark-remote-node-ontology-node-1` prototype containers
on the four reachable Raspberry hosts were stopped and their automatic restart
disabled; they were retained for reversible inspection, not deleted.

The real acceptance run exposed an invalid no-padding sentinel. User/request
scenarios now use `target_triples = 0`, matching the underlying graph builder;
positive targets smaller than the natural graph remain errors. A regression
covers this contract. Container build staging removes only managed source folders
before extraction, and recreated workers must match source and topology identity.

Engineering evidence is under `outputs/audit/container-scale/`. Failed and
interrupted attempts remain labelled there; they are not scientific results.
The full native-enabled regression run passed 487 tests before the final
container corrections; targeted verification is recorded separately. Native DL
reasoners inside the optional container image and the complete multi-scenario
scientific campaign require their own measured validation.

## Container deployment verification — 2026-10-20

The new opt-in battery uses the same semantic engine and query catalog with
Compose participants and explicit resource limits. Cloud, Fog and three Edge
hosts have Docker/Compose, enforced memory/swap limits and synchronized native
workers. Mist remains in the general inventory but is explicitly excluded from
this battery while powered off. The software suite passed 490 tests, with three
known Konclude annotation warnings; the figure changes also passed 18 module tests.

A bounded engineering acceptance with one participant on each of five hosts
completed distributed and replicated RDFS workloads, including warm-up and one
measured repetition. All 115 distributed query projections matched the replicated
reference and no client requests failed. This checks integration, not statistical
performance or a completed scientific campaign. Raw evidence is retained under
`outputs/container-scale/20261020T184330Z-6cf8b0be/`.

Edge 2's wall clock was corrected against the coordinator after detecting a
large offset. At that checkpoint its NTP service reported unsynchronized: persistent time
synchronization needs network/service diagnosis before cross-host event-time
analysis. Elapsed benchmark timings use monotonic clocks. Four Pi container
runtimes are 32-bit despite their 64-bit kernels; memory limits do not remove
per-process address-space limits. Optional native DL images require separate
per-platform validation. See [Container scalability](CONTAINER_SCALABILITY.md)
for measurement boundaries and allocation caveats.

A second acceptance completed two participants per host (ten total), with the
same two layouts and RDFS, one warm-up and one measured repetition. All 20
measured participant preparations completed and all 115 distributed projections
matched the reference (230 validation rows including the reference checks).
Evidence: `outputs/audit/container-scale/two-participant-acceptance/20261020T185503Z-bdba6b37/`.
Six PNG diagnostics were generated and participant/host layouts visually checked.
Edge 2 showed substantially higher distributed preparation wall time than its
reasoning CPU time; retain this coordination/transport overhead in analysis rather
than interpreting it as logical reasoning cost. More repetitions are required
before drawing performance conclusions.


## Availability follow-up — 2026-10-21

All four remote native workers remained healthy. The Cloud native process and
container were stopped; the container's inspected port binding also differed
from the saved Compose manifest. Recreating only the managed Cloud container
restored the configured VPN binding and starting the native worker restored
five healthy native services. No cause is inferred from the stopped state alone.
The container policy intentionally avoids automatic restart during experiments;
post-reboot recovery commands are documented. Current evidence is under
`outputs/audit/container-scale/`: `native-current.json`,
`containers-current.json`, `current-doctor.log`, and `cloud-recovery.log`.
Mist remains excluded. At that checkpoint Edge 2 reported NTP unsynchronized despite an
approximately aligned clock; this limitation has not been silently marked fixed.


## DL and time synchronization follow-up — 2026-10-21

Edge 2 now accepts NTP samples from Fog over Tailscale and reports synchronized.
Fog's Chrony listener binds only its VPN address and permits Edge 2's address.
The last observed settled offset was approximately 1.2 ms, which is an observation
rather than an accuracy guarantee. The relay requires Fog and its upstream clock.
Persistent configuration and validation commands are in the installation guide.

A later Cloud session selected Docker Desktop. Container commands now explicitly
select the local native Engine (`default` context) and reject a Desktop daemon
in preflight. The managed Desktop container was removed and the physical Engine
is used for the new validation. Historical measurements must retain their
original engine provenance; do not combine unidentified VM and native-host runs.

The DL image now puts Maven dependencies in a directory accessible to its
unprivileged runtime user and preserves the 512 MiB Java heap at runtime.
Repeated `--reasoner` options select the campaign matrix and enable DL builds.
The regression suite passed 494 tests with three known Konclude annotation
warnings. The full seven-scenario plan selects five physical hosts and excludes
Mist explicitly. Planned runs are not measured performance evidence.

## Mist rejoined — 2026-10-21, afternoon follow-up

Mist is available again. The maintained container configuration now has
`exclude_hosts = []`, so all six hosts participate by default. Its Docker Engine,
Compose plugin, memory/swap cgroups, free RAM/storage and time synchronization
passed preflight. The six-host configuration passed 495 software tests with the
three known Konclude annotation warnings. The seven-scenario dry-run now records
six participants; the earlier five-host plan and measurements are historical.
All six hosts reported synchronized clocks in `six-host-clock-status.json` under
`outputs/audit/container-scale/`. This supersedes the earlier availability and
NTP limitations, without rewriting those historical measurements.

### Six-host DL runtime validation — 2026-10-21, evening

The cold Edge 2 image build completed successfully. Its download throughput over
the relayed VPN had exceeded the original 30-minute deployment budget; this was
a dependency-transfer limitation, not evidence of an inconsistent ontology.
The default deployment-operation budget is now 7200 seconds, independently of
the unchanged 120-second request and 600-second experiment-point deadlines.

All six deployed containers passed all five backend checks (30/30): RDFS,
HermiT, Openllet, JFact and Konclude. Checks ran as the unprivileged container
user and verified actual inference; DL checks also rejected an inconsistent
fixture. RDFS does not claim OWL inconsistency detection. Evidence is stored in
`outputs/audit/container-scale/six-host-dl-validation/`, including image IDs,
container resource limits, runtime architectures and individual outcomes.
Cloud runs 64-bit Python; Fog, Mist and all three Edge containers run 32-bit
Python despite their 64-bit kernels. Large-workload address-space limitations
therefore remain. Passing these fixtures does not establish campaign scalability
or equivalence for the complete application ontology.

The subsequent application-level acceptance used six participants, ten users,
the natural generated graph, one measured repetition, no warm-up, concurrency
one and one query round. All ten combinations (five backends × distributed and
replicated layouts) completed within the configured bounded deadlines. All 60
node measurements completed, and all ten query-load rows reported zero errors.
The semantic comparison contains 1,150 successful rows: 575 distributed checks
(115 queries × five backends) and 575 corresponding replicated reference rows.
All ten summary rows report equivalent input graphs and equivalent query
projections. This is equivalence within each backend across layouts, not proof
that RDFS and OWL have identical semantics, or equivalence for arbitrary queries.

Raw evidence is under
`outputs/audit/container-scale/dl-workload-six-hosts/`, including configuration,
rendered topology, before/after container inspection and the
`distributed-reasoning-scalability/` CSV/JSON results. This is engineering
acceptance, not the full seven-scenario campaign or statistically supported
scalability evidence. The full campaign remains an explicit user execution.
After increasing only the deployment budget, the 23 container-module regression
tests and the 24-file documentation validation passed again.

The native worker release was then synchronized to all five remote hosts and
the six native workers were started/reconciled successfully. Final health
verification reports six healthy workers in `native-six-final.json`; all six
clocks are synchronized in `six-host-clock-final.json` (same audit directory).
Post-acceptance container inspection reports six running containers, zero
restarts and no OOM-killed containers, each limited to one CPU and 1536 MiB RAM.

### RDFS cold-build DNS regression — 2026-10-21

Campaign `20261021T174805Z-96c460fd` failed before its first experiment while
Cloud's BuildKit step installed Python dependencies. The pip message about no
matching `owlrl==7.6.2` distribution followed repeated DNS resolution errors; it
was not evidence of an unavailable package or an ontology inconsistency. A
simple DNS probe succeeded but the real dependency-install step reproduced the
failure. The installation succeeded using the local host build network.

The local coordinator now explicitly uses `build.network: host`; runtime service
networking is unchanged. Remote builds retain their default network because
Mist's builder requires an additional host-network entitlement. Build DNS errors
receive one delayed retry with per-attempt captured diagnostics. Moving
`ARG INSTALL_DL` below the Python installation prevents that selection alone
from invalidating its cache. Persistent deployment failures still abort the
placement, including with `--keep-going`: experiments require healthy workers.
The 26 container-module tests and documentation validation pass.

The corrected end-to-end acceptance completed as campaign
`20261021T175251Z-9f87c399`: six hosts, RDFS, `users-10`, one warm-up and one
measured repetition, distributed and replicated layouts. Both measured points
completed, all 230 semantic-validation rows were equivalent (115 distributed
checks plus their replicated reference rows), and query errors were zero. The
report generated six PNG figures. This verifies deployment, acquisition and
report generation for this scenario; it is not the full scalability campaign.

### Full RDFS container campaign scientific review — 2026-10-21

Campaign `20261021T180113Z-5f50aac8` completed all seven scenarios with partial
acquisition: 30/42 measured preparations completed and twelve replicated
preparations timed out. All 42 recorded query-load rows completed with zero
query errors. Container inspection recorded no OOM kills or automatic restarts.
Detailed semantic evidence contains 690 equivalent rows and 460 rows without a
replicated reference. The summary incorrectly mapped missing references to
`query_projection_mismatch`; aggregation is corrected for future runs and the
new synthesis interprets historical detailed rows without rewriting raw results.

The report now includes infrastructure totals, per-host CPU across scenarios,
completion/validity, cost ratios, user/data sensitivity, request concurrency and
an additive preparation-time breakdown. It exports analysis CSVs and explains
censoring, small sample sizes, sequential-order/RSS carryover and asymmetric
fragment transfer versus local graph generation. The single-size requests plot
was removed in favor of concurrency plots. Single-placement strong/weak figures
explicitly state that they do not estimate scaling.

The measured tradeoff is important: at 50 users distribution reduces participant
CPU by about 32% and input copies by 36%, but preparation is about 9.5 times slower.
Replicated serving has higher throughput at concurrency four. Large-load
completion does not by itself prove superior reasoning capacity because the
prepare paths perform different work under their request deadlines. A detailed
review is archived as `analysis/FINDINGS.md` in that campaign.

### User/concurrency campaign review — 2026-10-22

Campaign `20261021T201406Z-14a2d4a1` attempted all six user counts and concurrency
1/2/4/8. The first four sizes have 24 completed preparation rows and 96 query-load
rows. Across those query rows, 24/360 client requests failed, all in distributed
mode at concurrency eight. Historical rows discarded the error details, so the
exact per-request failure mechanism cannot be established from these CSVs alone.
The sequential worker HTTP design and queueing are relevant limitations, not a
proven explanation for every recorded failure.

Scenarios 1000 and 2000 failed with `timed out` and left no measured CSVs. Their
warm-up results must not substitute for measurements. Docker snapshots contain
failed health probes; several workers were unhealthy after the 2000-user case.
No OOM-killed containers or automatic restarts were recorded. Reporting previously
ignored scenarios without CSVs and limited global concurrency plots to the
`requests` family. Both omissions are corrected: all attempted sizes remain
visible and user-family concurrency is shown globally and per scenario.

Added per-host CPU/RSS/reasoning/input-copy curves and end-of-scenario health
snapshots, with explicit measurement scope and NA treatment. New runs retain
query error details, checkpoints after completed matrix points and scenario
tracebacks, and wait for workers to become ready after warm-up. These diagnostic
and readiness changes have regression coverage but have not been validated by
rerunning the 1000/2000-user physical cases. They do not establish that the
underlying capacity/time-budget limit has disappeared.

## Container campaign checkpoint correction — 22 October 2026

Campaign `20261022T054656Z-7cc67481` recorded 29 completed measured preparations, one preparation timeout, and 28 failures among 435 catalog requests. The 2000-user warm-up timed out on edge2-c1; an empty checkpoint table then raised ValueError and aborted acquisition. Empty node/statistics tables are now omitted, retaining failures and metadata. A regression test verifies matrix continuation and final archival when every preparation times out (46 focused tests passed). Physical high-load success remains unverified after this correction. Reports now include phase evidence and classified request errors; missing 2000-user measurements remain NA.

## Adaptive monitoring extension — 22 October 2026

Added an opt-in supervisor around container scalability with ontology policy bindings, separate preparation/application failure evidence, live capacity probes, deterministic constrained destination ranking, isolated Compose recovery, service telemetry, and bounded matched-workload verification. The baseline command remains unchanged. Archived replicated errors lacking worker attribution produce abstention; new errors preserve role and endpoint. An empty query table after all preparation attempts fail no longer raises a throughput-writer error.

The focused supervisor/container/engine suite passes 57 tests, including failed deployment cleanup, restoration of only previously running services, missing attribution, authorization rejection, identity/authority preservation, and unchanged workload budgets during recovery. Documentation validation passes. A read-only physical plan on all six hosts selected Cloud for the failing Edge2 distributed service, and abstained on historical un-attributed replicated query failures. The first physical actuator validation correctly rejected stale cached worker builds; this is retained as failed validation evidence, not a recovered execution.

The extension reconstructs synthetic state at experiment boundaries. It does not implement live VM migration, patient-data authorization, global optimal placement, exactly-once synchronization, or continuous autonomous failover. Its execution-success state is deliberately separate from semantic validation. Physical 2000-user recovery remains an experiment to execute, not an established result.

After rebuilding the container images on Cloud, Fog, Mist and all three Edge hosts, physical actuator validation `validation-20261022T141430Z` completed. It relocated logical `edge2-c1` to a second service on Cloud while preserving six logical participants. With one synthetic user, one measured repetition and concurrency one, both distributed and replicated preparations and catalog requests completed; sampled query projections were equivalent. Service telemetry was recorded. Recovery containers were removed and all original baseline workers passed readiness after restoration, with no cleanup/restore errors. This checks deployment and small-load execution, not recovery at 2000 users.

## Matched scalability/adaptation reporting — 22 October 2026

Adaptive campaign `20261022T142233Z-ad7fe00f` completed the distributed relocation attempt but did not recover all requests. Distributed preparation improved from 0/3 completed in the original campaign to 3/3; 23/45 measured catalog requests succeeded after relocation (3/3, 6/6, 8/12 and 6/24 at concurrency 1, 2, 4 and 8). Replicated verification inside that same attempt completed 1/3 preparations and 0/15 requests, compared with 2/3 and 0/30 originally. The separate replicated action was abstained because historical errors lacked worker attribution. These cohorts are explicitly distinguished in plots and are not evidence of a successful replicated adaptation. Semantic reference validation remained unavailable for the affected distributed sample.

Added automatic integrated reporting using the container-scale metric definitions and physical-host aggregation. Thirteen PNGs cover the observed campaign, including the Docker six-cost user curves, user/concurrency matrices, and four per-host resource/knowledge comparisons. Relocated services are attributed to their actual physical host, and shared axes include every host's observed range. No adaptive values are invented for unselected user levels. Raw measurements were preserved.

The CLI now selects configured user levels with `--users` and accepts `--concurrency` only when generating a new baseline. Archived recovery preserves the original concurrency matrix. Healthy baseline scenarios are recorded as `not_needed` rather than disappearing from the action history. Different trigger layouts/attempts remain separate cohorts. The focused regression suite passed 65 tests, including host attribution, shared-axis limits, full user/concurrency selection and no-intervention records; Markdown validation also passed. Source changes require matching container images, which are refreshed separately from measured campaigns.

## Adaptive concurrency and paired-report correction

Reviewed adaptive archive `20261022T183904Z-a0ada3b2`. Distributed 2000-user recovery completed 3/3 preparations and 22/45 catalog requests. Observed failures include 120-second request timeouts and connection resets. The worker's sequential HTTP service can queue simultaneous catalog requests; evidence does not establish ontology inconsistency or a unique root cause.

Supervisor changes evaluate application triggers by reasoner/concurrency, assess every selected layout independently, and retain prior placements across bounded attempts. Defaults now permit action on any observed failure and up to six attempts. Candidate and ensemble checks account for cumulative CPU/RAM occupancy; tried source/destination pairs are excluded. Missing preparation evidence cannot be labelled healthy. CLI success depends on the final outcome for each scenario/layout, not an earlier failed attempt followed by recovery.

Three paired figure families were added: availability with denominators, concurrency completion/change, and intervention effectiveness/overhead. Only the target layout is treated as an adaptive trial. Raw historical outcomes are preserved. All 16 PNGs in this archive decode successfully; the three new figures were visually checked. Continuous telemetry remains recovery-only, and relocation is not load-balanced horizontal replication.

Validation: 24 adaptive/report tests passed after the final edits; the associated 46 container-scale/distributed-engine tests also passed. Documentation validation and whitespace checks passed. No new scientific campaign was run during this correction.
