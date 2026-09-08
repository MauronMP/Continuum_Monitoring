# Architecture

The project is an infrastructure-neutral monitoring benchmark with a native
monolith control plus a physical deployment adapter.

| Boundary | Package or path | Responsibility |
| --- | --- | --- |
| Core domain | `src/continuum_bench/core` | Nodes, resource capacity, geographic position, dynamic metrics and reasoner descriptors. |
| Semantic assets | `ontology`, `queries`, `docs/reference` | Modular ontology, SHACL shapes, SPARQL catalog, policies and requirements. |
| Native control | `src/continuum_bench/monitoring/benchmark.py` | One-process cumulative and scalability baseline without HTTP overhead. |
| Monitoring module | `src/continuum_bench/monitoring` | Shared cumulative/scalability orchestration for distributed targets. |
| Study module | `src/continuum_bench/monitoring/study` | Reproducible workload traces, mobility models, link estimates, SPARQL feature extraction and category-cost aggregation. |
| Worker runtime | `src/continuum_bench/node.py` | Identical HTTP worker executed on physical nodes. |
| Physical lifecycle | `src/continuum_bench/physical_cluster.py` | SSH authorization, deployment, start, status and stop operations. |
| Placement | `src/continuum_bench/monitoring/sharded.py`, `src/continuum_bench/monitoring/physical.py` | Authority-sharded and replicated execution over real endpoints. |
| Product matrix | `src/continuum_bench/monitoring/engines.py`, `engine-service` | RDFLib, Jena, RDF4J and Oxigraph execution under one wire contract. |
| OWL consistency | `src/continuum_bench/owl_validation.py`, `tools/owl` | Separate HermiT, Openllet, JFact and Konclude validation gate. |

The ontology, query catalog, reasoners and benchmark algorithms do not depend
on the deployment lifecycle.

## Monitoring Flow

1. The coordinator loads ontology modules, SHACL shapes, query catalog and the
   selected topology manifest.
2. SSH lifecycle commands start the same worker implementation.
3. Each node starts an HTTP worker with its own tier, categories, authority flag
   and topology fingerprint.
4. The coordinator runs either a sharded or replicated monitoring benchmark.
5. Every measurement point is bounded by configurable timeouts.
6. Target-separated CSV measurements and JSON metadata are written under
   `outputs/` for direct comparison.

## Future Extension Points

New modules should be added beside `monitoring`, for example:

```text
src/continuum_bench/monitoring/study/
src/continuum_bench/analysis/
src/continuum_bench/planning/
```

They should depend on `continuum_bench.core` and the semantic asset loaders,
not on monitoring-specific experiment code.
