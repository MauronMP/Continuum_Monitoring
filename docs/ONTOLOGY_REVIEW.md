# Monitoring Continuum Ontology: Version 4 Review and Migration

## Purpose and identity

The model is the internal knowledge mechanism of a policy-driven continuum
monitoring architecture. It is not a stress-detection algorithm or a clinical
validation dataset. The wellbeing extension supplies the motivating application;
the core describes reusable infrastructure, state, governance and adaptation.

Version **4.0.0**, revision **4.0.0-monitoringcontinuum-v1**, replaces the generic
SmartCity identity with **Monitoring Continuum**:

| Item | Current value |
| --- | --- |
| Ontology IRI | `http://example.org/monitoringcontinuum` |
| Entity namespace | `http://example.org/monitoringcontinuum#` |
| Turtle/SPARQL prefix | `mc:` |
| Canonical source | `ontology/core/schema.ttl` and its maintained modules |
| Full application manifest | `configs/benchmark.toml` |
| Physical placement | `configs/ontology-placement.toml` |

Changing an IRI changes RDF identity; changing only a prefix would not. This is a
breaking ontology release. There are no `owl:sameAs` bridges that silently merge
old and new experimental graphs. `example.org` remains an illustrative project
namespace, not a claim of published or resolvable vocabulary hosting. Registering
a persistent namespace requires a separately agreed publication location.

## Audit findings and implemented changes

| Finding | Resolution and rationale |
| --- | --- |
| All profiles effectively imported the entire application | The core excludes wellbeing and federation. Profiles explicitly import optional modules; their file lists equal the transitive import closure. |
| Undeclared dependencies between modules | Added `contracts.ttl` for minimal shared entity types. Moved general temporal concepts to foundation and device-specific relationships to their owning modules. Imports are explicit and acyclic. |
| Consent properties excluded actual subject types | Extended union domains: `hasConsentRange` includes `ConsentRecord`; `hasProcessingPurpose` includes `ConsentRecord` and `Service`; `requiresConsentRange` includes `ModelTier`. Existing valid alternatives remain. |
| `replicaOf` had duplicate ownership | Deployment owns this property, with fragment-to-fragment semantics. Replication events use their own source/target relationships. |
| Five orphan union expressions | Removed the unreferenced expressions and their list cells. Referenced unions remain explicit. |
| Transfer/replication properties lacked restrictive ranges | Retained intentionally open ranges and documented why: endpoints or payloads can have different kinds. An arbitrary compute-node range would produce false inferred types. Domain/range is inference, not an input-validation rule. |
| Deprecated recovery relationship still instantiated | Removed the deprecated example use; the existing explicit `hasRecoveryCondition` relation remains. The deprecated property declaration is retained for interpretation of legacy material. |
| Full profile lacked its semantic profile type | All profiles, including `full`, are typed as `SemanticNodeProfile`. |
| Weak contradiction detection | Direct, pseudonymous and anonymous identifier representations are pairwise disjoint. Node roles, policy categories and context-dependent participation are not made globally disjoint. Native consistency and SHACL remain separate gates. |
| Controlled identity constraints only existed in examples | Moved the three `AllDifferent` declarations and their lists to the controlled core vocabulary. |
| SOSA observable properties were untyped | Declared observable properties and sensor `sosa:observes` links. Converted the three recorded scalar results to numeric literals. |
| Measurement units were absent | Added `MeasurementUnit`, `hasMeasurementUnit` and `measurementUnitStatus`. Existing observations explicitly record `not-recorded-in-source`; no unit is invented. |
| Single-category restriction conflicted with cross-cutting policies | Removed the category maximum cardinality while retaining minimum cardinality and type validation. Reference generation now preserves every category. |
| Missing labels and comments | All locally declared classes and properties have labels and descriptions. Cross-module and deployment descriptions explain responsibility. Axiom-based descriptions do not constitute new domain requirements or evidence of implementation. |

## Module responsibilities and boundaries

| Module | Responsibility |
| --- | --- |
| Foundation | General entities, temporal concepts and reused external vocabulary declarations. |
| Contracts | Minimal shared types such as state, service, model, purpose, transfer and validation artifacts. A shared type does not import its complete feature implementation. |
| Topology | Computational nodes, device relationships, geography and continuum structure. |
| Observability | Recorded node, device and user state and monitoring evidence. |
| Governance | Policies, requirements, consent, authorization and identity constraints. |
| Orchestration | Decisions, alternatives, adaptation, delegation and model/service lifecycle relations. |
| Deployment | Fragment placement, authority, privacy classification and semantic profiles. |
| Federation — optional | Federated-learning relationships and session details. Its shared session type is declared in contracts. |
| Wellbeing — optional | Wearables, physiological/stress observations and domain-specific vocabulary. |

The core closure has eight files: the core schema and seven general modules.
The complete benchmark manifest has fifteen files, including vocabularies,
optional extensions, shapes and reference individuals. Import closure is resolved
from local maintained files; workers do not fetch these IRIs from the network.

| Profile | Wellbeing | Federation | Validation shapes |
| --- | --- | --- | --- |
| Cloud / full | Yes | Yes | Core compliance and federated learning |
| Fog | No | No | No |
| Edge / Mist | Yes | Yes | No |
| IoT | Yes | No | No |

Schema selection and instance-data placement are different. The privacy and
query-routing code decides which instance statements are sent to a node. A Fog
profile without wellbeing definitions does not by itself guarantee absence of
sensitive instance data; privacy tests remain mandatory. Importing a shared
`FederatedLearningSession` type also does not install a learning algorithm.

## Validation and reproducibility

Run from the repository root with the environment installed:

```bash
.venv/bin/python tools/audit_ontology_modules.py
.venv/bin/python tools/review_validation_debt.py
.venv/bin/pytest -q
.venv/bin/continuum-bench owl-validate --require-all \
  --output outputs/validation/owl-reasoners.json
.venv/bin/python tools/check_distributed_semantics.py \
  --reasoner konclude --users 100 \
  --output outputs/audit/konclude-local.json
.venv/bin/python tools/generate_reference_docs.py
.venv/bin/python -m continuum_bench.diagrams
```

The module audit fails on unresolved/cyclic imports, duplicate term ownership,
missing declared dependencies, orphan unions, missing labels/descriptions,
optional modules leaking into the core and placement/profile disagreement.
Regression tests cover consent domains, controlled-vocabulary identity,
SOSA examples and safe namespace migration. Native OWL checks cover logical
consistency and the OWL 2 DL profile; the distributed diagnostic compares all
115 query counts, Boolean answers and result digests. The latter runs locally
and is not a physical performance measurement.

Review evidence is recorded under `outputs/audit/ontology-v4/`. Evidence from
version 3 remains under its original directory and must not be relabeled as a
version-4 experiment. New triple counts and logical axioms can change costs, so
performance comparisons need new, consistently versioned runs.

Some reference individuals, shape identifiers and synthetic rule identifiers retain
`v3` in their local names. They identify carried-forward records or unchanged
constraints introduced in the earlier model; they are not the ontology release
identifier. Renaming them must not imply new historical observations or new rule
semantics. The ontology version, revision and namespace identify the active release.

## Deployment and external-data migration

1. Keep old experiment outputs unchanged. The pre-migration local backup is
   `outputs/audit/ontology-v4/pre-migration.tar.gz`.
2. Redeploy and restart every participating worker from the same checkout.
   Worker protocol 10 checks ontology version/revision, Python build, topology
   and `semantic_assets_digest`. The digest includes ontology, SHACL, selected
   profiles, placement, query catalog, query texts and execution plan. Relative
   paths make it independent of the coordinator/worker installation directory.
   Byte-level edits, including comments, require synchronization and restart.
   A worker whose files changed after startup reports stale health and rejects
   preparation. Do not edit sources or data during a running campaign.
   The preparation integrity check precedes the worker CPU/phase timers;
   coordinator wall time includes it. Do not interpret the difference as pure
   network latency.
   Scalability/cumulative metadata records the digest; plotting rejects a recorded
   digest that differs from the active semantic inputs.
3. Use the explicit five-node topology while Mist is offline. Before returning
   Mist to service, deploy the same release and topology to all participating
   nodes; do not mix five-node and six-node fingerprints.
4. Rebuild cached fragments and rerun bounded validation before full campaigns.

```bash
.venv/bin/continuum-bench --topology-file configs/topologies/physical/without-mist.toml physical deploy --ssh-user pi
.venv/bin/continuum-bench --topology-file configs/topologies/physical/without-mist.toml physical start --ssh-user pi
.venv/bin/continuum-bench --topology-file configs/topologies/physical/without-mist.toml physical status --ssh-user pi
.venv/bin/continuum-bench --config configs/smoke-five-nodes.toml --keep-going physical scalability --layout distributed
.venv/bin/continuum-bench --config configs/smoke-five-nodes.toml --keep-going physical scalability --layout replicated
```

For external RDF instance data, the optional helper copies a graph and renames
only RDF URI terms in the old namespace. It preserves literals, including quoted
historical URIs, and refuses to overwrite an existing destination:

```bash
.venv/bin/python tools/migrate_ontology_namespace.py legacy-instances.ttl migrated-instances.ttl
```

This helper does **not** upgrade old schema axioms, rewrite embedded SPARQL string
literals or certify the result as version 4. Use the maintained schema, review any
embedded queries separately and validate imported instances before use. Do not
run the helper over historical result directories.

## Verified outcome (reviewed 2026-10-07)

The final portable suite passed 474 cases, with 15 explicit skips: 13 native
opt-in cases covered by the separate native run, and two calibration cases that
do not apply to distributed runners. The native suite passed all 35 cases.
These suites overlap; their counts are not a total of unique tests. The portable
run used an unavailable Java executable to check that native runtimes are optional.
HermiT, Openllet, JFact and Konclude passed the native consistency checks.

Bounded physical verification completed eight points: distributed and replicated
layouts, RDFS and Konclude, and 5 and 100 synthetic users, with one repetition.
All 460 distributed query results matched the canonical reference; all 460
corresponding replicated results matched the distributed results. Both layouts
record the current semantic-file fingerprint. This is functional verification,
not a statistical performance comparison or a publication campaign.

Cloud, Fog and all three Edge workers passed the final health and fingerprint
checks. The local Cloud service was found stopped and restarted; its stop cause
was not established. The four remote services were already healthy. Mist remains
excluded from this verification.

Local evidence is stored under `outputs/audit/ontology-v4/`: `verification.json`,
`portable-tests.xml`, `native-tests.xml`, `nodes-final.json`, and
`verified-physical/{distributed,replicated}/scalability/`. Intermediate results
remain separately identified in that directory's README. Generated audit outputs
are local artifacts; the maintained instructions above allow fresh verification.

## Remaining limits

The review retains 57 known SHACL warnings: 32 missing historical AHP inputs,
2 model timestamps, 14 trust-window boundaries and 9 prospective acceptance
parameters. Their dispositions are tracked, not waived. Query traceability remains
102/116 requirements and 69/79 policies. The three missing measurement units are
additional explicit data-quality limitations, not part of those 57 shape warnings.

Consistency does not prove policy enforcement, privacy compliance, clinical
accuracy or complete distributed OWL inference. Policy categories are not globally disjoint. SHACL now permits multiple
`belongsToPolicyCategory` values, requires at least one, and validates each value
as a category. Reference generation lists every membership deterministically.
The existing reference assignments remain unchanged: no additional classifications
have been invented. `EXT-Q03` returns one row per policy/category combination;
count distinct policy identifiers when computing policy counts. The 12 policy
categories are distinct from the 16 query groups used by cumulative schedules;
shared query work must not be counted repeatedly as independent policy cost. Conflict resolution
needs implemented evaluation mechanisms and context, not category labels alone.
