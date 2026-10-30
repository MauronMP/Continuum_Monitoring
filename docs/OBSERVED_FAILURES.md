# Observed Failures and Remediation

This audit is a snapshot of the evidence available on 1 October 2026. It
separates ontology validity, semantic-result validity, timeout censoring and
infrastructure capacity. The files under `outputs/` may be replaced by later
direct runs, so publication evidence should be generated in an isolated
`outputs/suites/<run>/` directory.

## Evidence reviewed

- `outputs/monitoring/distributed/cumulative/`
- `outputs/monitoring/distributed/scalability/`
- `outputs/monitoring/replicated/cumulative/`
- `outputs/monitoring/replicated/scalability/`
- `outputs/policy-evaluation/`
- `outputs/validation/owl-reasoners.json`
- active coordinator and worker processes and health endpoints

The three directories below `outputs/suites/` contain dry-run plans only. They
do not contain an executed complete-suite result. Load, architecture-experiment
and campaign evidence is also absent from the current direct output tree.

## Result status

| Family | Recorded outcome | Interpretation |
| --- | --- | --- |
| Distributed cumulative | 240/240 completed; 15,360/15,360 query validations matched. | Complete and semantically valid for the recorded matrix. |
| Distributed scalability | 54 valid completions, 13 physical timeouts, 12 invalid-result points and 11 unvalidated physical completions out of 90 configured points. | Incomplete scientific evidence; only the 54 validated completions are eligible for performance analysis. |
| Replicated cumulative | 240/240 completed. | Complete for the recorded matrix. |
| Replicated scalability | 63/90 checkpointed as completed; point 64 remained active. | Incomplete unlimited run; no final metadata or complete family evidence. |
| Policy evaluations | 120/120 rows completed across the four evaluations. | Controlled functional/cost experiment completed. Its ground truth is configured, not externally observed clinical truth. |

## Failure 1: unlimited replicated HermiT execution

At 08:42 Europe/Madrid on 1 October 2026, the active command was:

```text
continuum-bench --unlimited --keep-going physical all --layout replicated
```

It had been active for approximately 23 hours. The scalability progress file
remained at point 64/90, HermiT, 2,500 users, repetition 1,
`calibration-prepare`. The Cloud worker completed its local HermiT preparation
after approximately 30.4 million milliseconds (8.45 hours). The five Raspberry
Pi workers still had Java HermiT processes at 100% of one core after more than
ten hours, and their HTTP health endpoints timed out.

The coordinator process was also observed in Linux state `T` (`stopped`) because its
terminal had suspended the process. Its progress timestamp had not changed
since 30 September at 20:10 UTC. The workers were still processing the requests,
so the campaign could not consume their responses or advance even if they
finished. Current source ignores `SIGTSTP` during a physical campaign and tells
the operator to use `Ctrl+C`; the older process did not contain that protection.

This is not evidence of ontology inconsistency. It is a capacity/runtime
problem caused by unbounded OWL DL realization on constrained hardware. In
unlimited mode there is no process, worker, socket or coordinator deadline, so
`--keep-going` cannot advance until the active native process returns.

Remediation:

1. Use bounded mode with `--keep-going` for complete matrices.
2. Treat a timeout as a right-censored capacity boundary rather than increasing
   it until every reasoner finishes.
3. Use reasoner-specific scale ceilings for additional diagnostic campaigns,
   or enable `--skip-larger-points` after a confirmed timeout.
4. Run an unlimited point only as a supervised one-reasoner, one-repetition
   diagnostic on a scale already known to be feasible.
5. To recover an active unlimited run, interrupt its coordinator, stop the
   physical workers, verify that native Java/Konclude children are gone, and
   start the workers again before launching a bounded run.
6. Do not interpret `/health` timeout alone as a dead worker while its
   single-threaded service is executing a request; inspect the worker and native
   child process over SSH.

Recovery completed on 1 October 2026. The stopped coordinator disappeared, the
cluster stop operation terminated every worker and project-owned native child,
and the source was redeployed with all four native backends verified on every
Raspberry Pi. The six restarted workers report build
`continuum-benchmark-0.5.0-protocol-9-source-cee2a8ba52a26916`, topology
fingerprint `c4c7dca3a306b571d340c0c13aa420a7571c72b8acec1c4e57b0103ee4b8360b`
and exactly one listener each. This failure remains documented because the
incomplete output is historical evidence and must not be interpreted as a
completed replicated campaign.

## Failure 2: distributed scalability timeouts

Thirteen physical points reached a configured boundary:

| Backend and scale | Timed-out repetitions | Failing phase/node |
| --- | ---: | --- |
| HermiT, 2,500 users | 3 | Distributed preparation on `edge1`. |
| HermiT, 5,000 users | 3 | Distributed preparation on `edge1`. |
| JFact, 2,500 users | 3 | Distributed preparation on `edge1`. |
| JFact, 5,000 users | 3 | Distributed preparation on `cloud`. |
| Openllet, 5,000 users | 1 | Query batch 20/21 on `mist`. |

The repeated failures at the same reasoner/scale boundary indicate
computational capacity, not random network loss. The Openllet query timeout is
more localized and should be repeated in bounded mode to distinguish an
outlier from a stable query-capacity boundary.

Remediation:

- retain the timeout rows and their lower bounds;
- compare the largest completed scale per reasoner;
- use a larger bounded request budget only when the expected runtime remains
  operationally reasonable;
- avoid presenting missing later points as zero cost or successful completion.

## Failure 3: canonical reference did not complete

Eleven points completed physical work but their full canonical reference
timed out:

- HermiT at 1,000 users: repetitions 1–3;
- RDFS at 5,000 users: repetitions 1–3;
- Openllet at 5,000 users: repetitions 1 and 3;
- Konclude at 5,000 users: repetitions 1–3.

The version that produced these CSV files labelled the physical rows
`completed`. That label is too strong because no semantic reference was
available. The current implementation changes future rows to
`unvalidated_results`, retains their timing for diagnosis and excludes them
from scientific curves. The publication reader also repairs the old label in
memory by checking `reference_status`.

Remediation is already implemented in the current source and covered by
`test_reference_timeout_retains_timing_but_excludes_point_from_curves`.
Existing raw CSV files are preserved as historical evidence and must not be
edited in place.

## Failure 4: Konclude distributed/reference mismatch

Twelve Konclude points were invalid at 100, 500, 1,000 and 2,500 users, in all
three repetitions. Seventy-two query validations differed from the canonical
result. The affected queries are:

| Query | Category | Invalid validations | Role in the model |
| --- | --- | ---: | --- |
| `BASE-Q02` | topology | 9 | Compute-node type and elasticity inventory. |
| `BASE-Q33` | observability | 9 | Mean resource use grouped by inferred node type. |
| `BASE-Q35` | delegation | 12 | Failure, evaluation, policy and action chain. |
| `EXT-Q21` | identity/consent | 12 | Resources and required consent ranges. |
| `EXT-Q59` | adaptation | 12 | Adaptive-action report. |
| `EXT-Q73` | audit/temporal | 12 | Temporal-entity report. |
| `EXT-Q75` | validation | 3 | SHACL shape inventory. |
| `EXT-Q80` | validation | 3 | Coverage and migration-debt dashboard. |

The same canonical ontology is consistent under Konclude, and the mismatch
appears only after fragment-local reasoning and federated result merge. The
most likely cause is therefore the non-compositional nature of OWL DL
classification/realization over authority fragments, combined with query
merge semantics for inferred and aggregate results. A union of independently
closed fragments is not generally equivalent to closing the union graph. This
is an architectural semantic limitation, not evidence that the eight queries
or their associated policies are meaningless.

Remediation requires one of these explicit designs:

- add an iterative federated saturation protocol that exchanges required
  boundary entailments until a fixpoint is reached;
- execute global OWL DL classification at a designated coordinator while data
  ownership and query routing remain distributed;
- define and validate a formally supported distributable OWL fragment;
- restrict Konclude distributed results to diagnostic evidence and compare its
  validated performance only in replicated placement until equivalence is
  implemented.

The current result-validation gate is behaving correctly: it marks only the
affected points `invalid_results` and prevents them from entering performance
figures.

## Ontology and policy audit

The active ontology does not show a logical inconsistency:

- project validation returned `ok=true`;
- SHACL returned `Conforms: True`;
- HermiT, Openllet, JFact and Konclude reported the compiled ontology
  consistent;
- HermiT, Openllet and JFact reported OWL 2 DL profile compliance;
- no unsatisfiable named classes were reported;
- all 115 catalog queries met their declared asserted-graph expectations;
- no violation query became nonzero after inference;
- distributed fragments reconstruct the canonical asserted graph exactly;
- no privacy-placement error or unresolved profile import was found.

The ontology still contains documented completeness debt. It does not make the
ontology inconsistent, but it blocks a full scientific-acceptance claim:

1. `AcceptanceProfile_v3_Draft` lacks nine thresholds:
   `AHP_consistency_threshold`, `D_delegation_max`, `E_device_max`, `N_agents`,
   `T_decision_max`, `T_migration_max`, `T_node_join`, `T_reselection_max` and
   `T_sparql_monitor`.
2. The reproducibility review has six of seven expected records. The query
   catalog is still `pending-definition`, and no `ValidationCampaign` instance
   is present.
3. SHACL reports 57 warnings: the nine thresholds above, two models without
   `lastUpdated`, 32 migrated decision alternatives without `hasAHPScore`, and
   14 missing trust-window start/end values.
4. Query traceability covers 102 requirements and 69 policies. Fourteen
   requirements and ten policies remain unreferenced by the query catalog.

These items should be resolved with real experiment or domain values. Inventing
thresholds, AHP scores or historical trust windows merely to silence validation
would make the model less credible. The appropriate fixes are to define a
versioned acceptance profile for the intended campaign, create its
`ValidationCampaign` individual, mark the query catalog ready only after review,
and complete or explicitly waive migrated historical fields with provenance.

## Policy-evaluation interpretation

All policy-evaluation rows completed. Policy-driven decisions achieved 100%
coverage and precision with zero over/under-monitoring in the configured
scenarios; the static strategy averaged approximately 64.5% coverage and 51.7%
precision. These values validate that the policy engine reproduces its own
configured ground truth. They do not independently prove that the policies are
clinically correct, complete for real deployments or superior under unseen
contexts. External scenario review and physical event traces are still needed
for those claims.

## Recommended next run

```bash
continuum-bench \
  --timeout-mode bounded \
  --keep-going \
  --no-skip-repetitions \
  --no-skip-larger-points \
  --no-skip-cumulative-stages \
  suite
```

For a faster capacity-oriented campaign, replace
`--no-skip-larger-points` with `--skip-larger-points`. The first timed-out point
remains recorded, and larger points for that reasoner are explicitly marked as
skipped rather than silently omitted.

## Follow-up on 6 October 2026

The records above remain historical. The proposed cause of the Konclude mismatch
is not established by consistency checks alone. The current implementation is
being checked with canonical-versus-fragment result digests and an explicitly
historical five-node physical deployment (superseded by the current six-node inventory). See [Audit remediation](REMEDIATION.md)
and its recorded verification results. The query-catalog artifact is now
structurally validated rather than pending; campaign and historical measurement
evidence remain separate prerequisites.


### Confirmed Konclude conversion defect

A deterministic reproduction with `PYTHONHASHSEED=3` exposed the root cause of
current mismatches: OWLAPI can serialize entities as relative OWL/XML IRIs under
`xml:base`. The Konclude adapter copied axioms into OWLlink while discarding the
base and Prefix declarations. Inferred triples could therefore contain relative
or incorrectly identified entities. This explains serialization-order-dependent
answers; it is not proof of an inconsistency or of non-compositional reasoning.

The adapter now expands relative and abbreviated entity IRIs, IRI text nodes and
datatype IRIs before creating the OWLlink request. Unresolved references fail
explicitly. The previously failing seed matches all 115 query counts, ASK answers
and digests for both five- and six-fragment local diagnostics at 100 users. The
six-fragment diagnostic is local and did not contact Mist, which was offline at the time. All six nodes passed
the fresh health check on 14 October 2026.
Physical confirmation is recorded separately in the remediation report. Historical
invalid rows are unchanged and remain excluded.

### Worker cleanup ownership

During deployment, the former local cleanup matched every native process using
the checkout's Java helper. This interrupted an independent native regression
check (exit 143). Cleanup now follows descendants of an identity-verified worker;
remote cleanup captures that worker's direct native child groups. It does not kill
independent diagnostics merely because they use the same repository. Orphans
without provable ownership require explicit inspection, not broad process killing.
