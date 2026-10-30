# Documentation map

Start with [Installation](INSTALLATION.md), understand the three batteries in
[Experiments](EXPERIMENTS.md), then use [Complete execution](COMPLETE_EXECUTION.md).

| Topic | Maintained source |
| --- | --- |
| Full project index | [Repository README](../README.md) |
| Acquisition and optional commands | [Complete execution](COMPLETE_EXECUTION.md) |
| Scientific methods and references | [Experiments](EXPERIMENTS.md) |
| Result files and figures | [Outputs](OUTPUTS.md) |
| Container scalability | [Compose deployment and experiments](CONTAINER_SCALABILITY.md) |
| Six-node deployment | [Physical continuum](PHYSICAL_CONTINUUM.md) |
| Per-node ontology files | [Ontology distribution](ONTOLOGY_DISTRIBUTION.md) |
| Model validation and external elements | [Ontology review](ONTOLOGY_REVIEW.md) |
| Python responsibilities | [Python reference](PYTHON_REFERENCE.md) |
| Queries and routing | [Query guide](../queries/README.md) |
| Decision comparison internals | [Comparison](COMPARATIVE_EVALUATION.md) |
| Claim boundaries | [Research method](RESEARCH_METHOD.md) |
| Maintenance and failures | [Remediation](REMEDIATION.md), [observed failures](OBSERVED_FAILURES.md), [audit](AUDIT.md) |

Generated semantic references: [ontology](reference/ONTOLOGY_REFERENCE.md),
[policies](reference/POLICIES.md), [requirements](reference/REQUIREMENTS.md),
[SPARQL traceability](reference/SPARQL_QUERIES.md). Maintain source assets and
regenerate these documents; do not manually edit generated tables.

Three evaluation batteries are implemented: native physical evaluation, strategy
comparison and container scalability. The separate four-strategy comparison remains
future work.

- [Validation gaps](VALIDATION_GAPS.md): warning closure criteria, all uncovered requirements/policies and failure diagnosis.

See [Scope adaptation](SCOPE_ADAPTATION.md) for the revised requirements, policies and verification boundaries.

- [Adaptive monitoring](ADAPTIVE_MONITORING.md): policy-directed bounded recovery, execution and limitations.
