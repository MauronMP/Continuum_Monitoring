# Maintained project audit

## Scope of the current cleanup

The active project exposes two evaluation batteries. Removed obsolete smoke
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
All six configured workers participate by default; reported health is a point-in-time
observation and becomes stale after source/semantic edits.

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
| Complete commands for two batteries | [Complete execution](COMPLETE_EXECUTION.md) |
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
