# v3.0.0 artefact traceability

| Need | Verifiable artefact |
|---|---|
| Complete ontology | `ontology/legacy/smartcity_continuum-v3.0.0.ttl` |
| Modular continuum core | `ontology/core`, `ontology/modules` |
| Wellbeing extension | `ontology/domains/wellbeing` |
| Closed-world constraints | `ontology/shapes` and violation queries |
| Reference scenarios | `ontology/examples/reference-system.ttl` |
| Complete query source | `queries/legacy/sparql_battery-v3.0.0.sparql` |
| Executable query catalog | `queries/catalog.csv` and `.rq` files |
| Routing and merge | `queries/execution-plan.toml` |
| Tier placement | `configs/ontology-placement.toml`, `ontology/profiles` |
| Requirements | `docs/reference/REQUIREMENTS.md` |
| Policies/mechanisms | `docs/reference/POLICIES.md` |
| Ontology term catalog | `docs/reference/ONTOLOGY_REFERENCE.md` |
| Query reference | `docs/reference/SPARQL_QUERIES.md` |
| Release contract | `continuum_bench.specification` |
| Synthetic data | `continuum_bench.synthetic` |
| Cumulative/scalability | `continuum_bench.benchmark` |
| Multidimensional load | `continuum_bench.load_benchmark` |
| Three architecture experiments | `continuum_bench.experiments` |
| Product comparison | `continuum_bench.engines`, `engine-service` |
| Elastic topologies | `configs/topology.toml`, `configs/topologies` |
| Physical lifecycle | `continuum_bench.physical_cluster` |
| Result equivalence | canonical digest and `result-validation.csv` |
| Publication figures | plotting/reporting/experiment analysis modules |

The generated references are derived from executable RDF and CSV rather than
maintained as independent prose copies:

```bash
.venv/bin/python tools/generate_reference_docs.py
```

## Direct query coverage

The catalog currently references 102 of 116 requirements and 69 of 79
policies. Validation reports the exact uncovered IDs. An uncovered structural
requirement is not automatically violated; it means the query catalog lacks a
direct metadata link and the evidence must be supplied through ontology,
SHACL, system tests or a future query.

## Evidence levels

1. RDF trace: requirement-policy-mechanism links asserted in the ontology.
2. Catalog trace: query metadata lists requirement and policy IDs.
3. Runtime evidence: query/SHACL/reasoner output from a versioned graph.
4. Experimental evidence: matched workload, topology and hardware metadata.

Do not represent a thematic inference as a direct RDF/catalog trace. Do not
represent a smoke pass as acceptance or performance evidence.
