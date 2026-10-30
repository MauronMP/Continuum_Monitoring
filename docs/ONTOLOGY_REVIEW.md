# Ontology validation and external vocabulary review

## Purpose and identity

Monitoring Continuum is the internal knowledge mechanism of policy-driven
monitoring. The wellbeing extension represents the motivating health domain;
it is not a clinically validated stress detector. The reusable core does not
require wellbeing or a federated-learning implementation.

| Item | Value |
| --- | --- |
| Version / revision | `4.0.0` / `4.0.0-monitoringcontinuum-v2` |
| Ontology IRI | `http://example.org/monitoringcontinuum` |
| Term namespace / prefix | `http://example.org/monitoringcontinuum#` / `comon:` |
| Full input manifest | `configs/benchmark.toml` |
| Shape sources | `ontology/shapes/core-compliance.ttl`, `ontology/shapes/federated-learning.ttl` |

`example.org` is illustrative, not a published persistent vocabulary service.
The earlier SmartCity migration is complete in maintained semantic assets.
Historical identifiers containing `v3` denote retained records/contracts, not the
active ontology release. Do not rename historical outputs to imply new evidence.

For module responsibilities, exact per-node files, ownership and inference
boundaries, see [Ontology distribution](ONTOLOGY_DISTRIBUTION.md). Those tables
are deliberately maintained in one place rather than repeated here.

## External elements actually used

| Element | Use and boundary |
| --- | --- |
| RDF / RDFS / OWL and XSD | Graph representation, class/property axioms, datatypes and reasoning contracts. |
| SOSA (`http://www.w3.org/ns/sosa/`) | Sensor, observation, observed-property and result relationships. |
| SAREF (`https://saref.etsi.org/core/`) | Reused device-related vocabulary. |
| FOAF (`http://xmlns.com/foaf/0.1/`) | Person/name relationships. |
| GeoSPARQL (`http://www.opengis.net/ont/geosparql#`) | Geographic feature vocabulary; no automatic distance or spatial reasoning service is installed. |
| Dublin Core Terms (`http://purl.org/dc/terms/`) | Descriptive metadata where present. |
| SHACL and SPARQL 1.1 | Structural validation and executable query constraints. |
| RDFLib, owlrl and pySHACL | Parsing/query execution, datatype-aware RDFS materialization and shape validation. |
| OWLAPI with HermiT, Openllet and JFact; native Konclude | Separate native consistency/materialization backends, installed outside the Python graph stack. |

Prefix declarations alone are not evidence that a complete external ontology is
imported. The maintained local import closure determines loaded axioms; workers
do not fetch arbitrary remote vocabularies during a benchmark. Reusing SOSA/SAREF
terms does not reproduce an external application's implementation or evaluation.
No ontology image generation dependency is required.

## Validation commands

From the installed repository environment:

```bash
source .venv/bin/activate
continuum-bench doctor --owl
python tools/audit_ontology_modules.py
python tools/review_validation_debt.py
continuum-bench validate
continuum-bench owl-validate --require-all --output outputs/validation/owl-reasoners.json
python tools/check_distributed_semantics.py --reasoner rdfs --users 12 --output outputs/audit/distributed-semantics-rdfs.json
continuum-bench fragments --users 12 --output-dir outputs/fragments/physical
python tools/generate_reference_docs.py
python tools/generate_project_indexes.py
python tools/check_documentation.py
```

`validate` runs the backends selected by `configs/benchmark.toml`, so install the
native runtimes first. `check_distributed_semantics.py` is an offline comparison
of canonical and fragment results; it is not a distributed performance campaign.
Change `--reasoner` explicitly when examining a native backend. Generated manuals
and the query bundle must be refreshed when their source assets change.

| Check | What passing establishes | What it does not establish |
| --- | --- | --- |
| Module audit | Import closure, term ownership, labels/comments and profile/manifest agreement. | Application correctness or privacy enforcement. |
| SHACL/project validation | Configured record constraints and query expectations. | Clinical validity or satisfaction of every prose requirement. |
| Native OWL consistency | No detected logical contradiction under the selected backend/contract. | Complete support for every ontology feature in every distributed placement. |
| Canonical/fragment comparison | Agreement for the tested graph, queries and reasoner. | Arbitrary distributed OWL entailment or unseen-query completeness. |
| Traceability review | Missing requirement/policy coverage is explicitly classified. | That missing evidence has been implemented or measured. |

## Resolved structural issues

Module imports are explicit and acyclic; shared contracts remove duplicated term
ownership. Optional wellbeing/federation imports are excluded from the core.
Consent union domains include the intended example subjects. Orphan unions were
removed; controlled identity constraints are in the reusable vocabulary.
Reference observation values are numeric and unknown units are explicitly marked.
Local classes/properties have labels and descriptions. SHACL permits multiple
policy-category memberships while requiring at least one valid category.

These changes do not make policy categories mutually exclusive or implement
conflict precedence. `EXT-Q03` produces a row per policy/category association;
use distinct policy identifiers when computing policy counts.

## Remaining model and evidence limitations

The maintained reference data still contain 57 reviewed SHACL warnings:
32 missing historical AHP inputs, 2 model timestamps, 14 trust-window boundaries
and 9 prospective acceptance parameters. `configs/traceability-review.toml`
records dispositions. Three observations have unknown source measurement units;
these are additional data-quality limitations, not part of the 57 warnings.
Do not invent historical values to remove warnings.

Query traceability covers 106 of 116 requirements and 73 of 79 policies. The remaining 10 requirements and 6 policies have software verification contracts,
not SPARQL coverage. Some declared concepts
model future capabilities, including learning and mobility; declarations do not
establish an operational implementation. Multicategory policy cost attribution
must account for shared queries rather than double counting their elapsed time.

These limitations are compatible with evaluating architecture cost and configured
plan conformance. They preclude claims of full policy enforcement, complete
clinical validation or universal semantic correctness. Distribution-specific
limits, production privacy boundaries, absent IoT workers and topology changes
are documented only in [Ontology distribution](ONTOLOGY_DISTRIBUTION.md).

For the revised statements and their verification boundaries, see
[Scope adaptation](SCOPE_ADAPTATION.md). Historical failures and warning closure
criteria remain in [Validation gaps](VALIDATION_GAPS.md).

## Public namespace notation

The maintained Turtle, SPARQL and reference documentation use `comon:` for
Continuum Monitoring. Its namespace remains
`http://example.org/monitoringcontinuum#`; this is a prefix change, not an entity
or ontology-IRI migration. Existing full-IRI identifiers remain valid. The
catalogue's former empty SPARQL prefix is now explicit as `comon:` as well.
Historical experiment archives retain their original notation and checksums.

The migration checks resolved query algebra for all 115 queries and graph
isomorphism after normalizing the changed prefix wording in RDF comments.
Resource identities, axioms, policies and query operations are unchanged.
Semantic asset byte digests nevertheless change, so workers must be synchronized
before new experiments. Use a fresh baseline for comparisons with the updated
adaptive implementation.
