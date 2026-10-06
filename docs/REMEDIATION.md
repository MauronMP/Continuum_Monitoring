# Audit Remediation and Five-Node Operation

This follow-up separates fixes, reproducible verification and evidence that
cannot be recovered from the repository. It does not waive scientific requirements.

## Operating while Mist is offline

Use `configs/topologies/physical/without-mist.toml`. It reuses the maintained
Cloud, Fog and Edge node definitions and explicitly excludes Mist. The normal
`topology.toml` continues to describe the six-node deployment. Do not mix their
results: their topology fingerprints and ownership partitions differ.

From the repository with the virtual environment activated:

```bash
continuum-bench --topology-file configs/topologies/physical/without-mist.toml physical deploy --ssh-user pi --with-dl-reasoners
continuum-bench --topology-file configs/topologies/physical/without-mist.toml physical start --ssh-user pi
continuum-bench --topology-file configs/topologies/physical/without-mist.toml physical status --ssh-user pi
continuum-bench --config configs/smoke-five-nodes.toml --keep-going physical scalability --layout distributed
continuum-bench --config configs/smoke-five-nodes.toml --keep-going physical scalability --layout replicated
```

This smoke profile tests 5 and 100 synthetic users, one repetition and all five
reasoners, using bounded deadlines. It is functional verification, not publication
statistics. The full configured suite can use the same explicit topology:

```bash
continuum-bench --topology-file configs/topologies/physical/without-mist.toml --timeout-mode bounded --keep-going suite \
  --load-config configs/load-five-nodes.toml \
  --experiment-config configs/experiments-five-nodes.toml \
  --distributed-reasoning-config configs/distributed-reasoning-five-nodes.toml \
  --campaign-config configs/campaign-five-nodes.toml
```

The explicit five-node variants preserve the other full-profile settings and remove
six-node scale points. Add `--dry-run` to inspect the suite before execution. Mist must be
redeployed with the same source when it is turned on. Then deploy and start the
full topology on all nodes; changing only Mist would leave mismatched fingerprints.
These commands manage user-owned workers; existing prerequisites do not require
sudo. Workers are explicitly started and are not installed as reboot services.

## Ontology and acceptance evidence

Revision `3.0.0-en-audit-v2` corrects the query-catalog artifact: its real location
is `queries/catalog.csv`, and its status is `validated-structural`. The catalog's
115 executable contracts are no longer described as nonexistent. Reference
manuals and ontology diagrams are regenerated with this revision.

Acceptance readiness now checks actual catalog status and a completed campaign
with typed result records. A seventh inventory row, a duplicate artifact or an
empty campaign declaration cannot establish readiness. A completed declaration
still requires independent review of the linked evidence; this is not a clinical
certification mechanism.

The following original evidence remains unavailable:

| Missing evidence | Count | Required resolution |
| --- | ---: | --- |
| Acceptance thresholds | 9 | Agree prospective, justified system targets before measuring; do not reuse timeout limits. |
| Historical alternative AHP scores | 32 | Recover original decision inputs or execute a new, separately identified decision campaign. |
| Historical model timestamps | 2 | Recover actual version dates from the originating model registry. |
| Trust-window boundaries | 14 | Recover original telemetry windows; the audit timestamp is not a replacement. |

The 57 SHACL warnings are retained. Recalculating on current inputs would create
new evidence, not restore these historical records. No source data supports
silencing them. Run the machine-readable review with:

```bash
python tools/review_validation_debt.py --output outputs/audit/validation-debt.json
```

The report lists each affected individual/property and its required action.
It fails if a new finding lacks a disposition. CI also executes this review.

## Requirement and policy coverage

`configs/traceability-review.toml` assigns an explicit disposition, rationale and
existing evidence path to all 14 requirements and 10 policies not referenced by
the query catalog. The review checks missing/stale entries and missing evidence
paths. Query coverage remains 102/116 requirements and 69/79 policies.

A software check is different from a semantic query or a physical experiment.
Several uncovered requirements concern endpoint interoperability, real mobility,
energy behavior, durable recovery and clinical model selection. Assigning an
unrelated SELECT query to them would be misleading. Partial or deferred entries
remain unsatisfied; review completion does not imply implementation completion.
In particular, the worker's query-ID HTTP API is not an arbitrary SPARQL 1.1
endpoint, and modeled recovery is not physical fault-recovery validation.

## Konclude equivalence diagnosis

A concrete adapter defect was reproduced: OWLAPI's relative OWL/XML IRIs lost
`xml:base` and Prefix context when moved into OWLlink. The adapter now expands
these IRIs before constructing the request and rejects unresolved references.
A regression covers relative classes, individuals, datatype references and
abbreviated IRIs. The formerly failing hash seed matches all 115 queries locally
with five and six fragments at 100 users. The earlier non-compositional-inference
explanation was a hypothesis, not the confirmed cause of this defect.

The diagnostic compares all query counts, ASK answers and
order-independent result digests between the canonical graph and fragment-local
inference with the actual routing/merge logic:

```bash
python tools/check_distributed_semantics.py --reasoner konclude --users 100 --output outputs/audit/konclude-five-node-local.json
python tools/check_distributed_semantics.py --reasoner konclude --users 100 --topology-file configs/topologies/physical/topology.toml --output outputs/audit/konclude-six-node-local.json
```

Both commands execute locally; the second does not contact or start Mist. This
checks semantics independently from network and 32-bit worker runtime effects.
Physical confirmation uses the bounded smoke commands above. Historical invalid
rows remain invalid and unchanged, even when a newer build passes. Finite matched
experiments cannot prove arbitrary OWL DL closure is distributable.

## Remaining platform constraints

The Raspberry Pi user spaces are 32-bit. Changing them to a supported 64-bit OS
requires a separate reinstallation and backup plan; installing Python packages
cannot remove a native process address-space limit. Bounded deadlines remain
necessary. This follow-up does not reinstall operating systems, invent geographic
distances, implement clinical validation or run the macOS CI matrix locally.

## Lifecycle isolation

Worker restart/stop now targets native descendants of the verified worker instead
of every materializer using the project directory. This prevents independent
reasoner tests from being terminated during deployment. Unattributed orphan
processes are intentionally left for explicit operator inspection.


## Result-envelope robustness

Canonical JSONL generation now compares summary fingerprints captured before the
command. This avoids losing a newly written result when filesystem modification
time is slightly older than the wall-clock start timestamp. Unchanged historical
summaries are not rewritten. A regression deliberately backdates the new file to
exercise this condition without timing-dependent sleeps.

## Confirmed physical verification

The corrected bridge completed all 10 distributed scalability points (5 reasoners
at 5 and 100 users, one repetition) on Cloud, Fog and three Edges. All 1,150
canonical query comparisons matched. Evidence is in
`outputs/audit/2026-10-06/physical-fixed/distributed/scalability/`.
These runs preceded the final lifecycle/JSONL-only changes and retain their actual
source identity. They are correctness smoke evidence, not publication statistics
or a replacement for a full capacity campaign. A final-build Konclude smoke check
and node health snapshot are recorded separately.
