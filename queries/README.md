# SPARQL Catalog

`manifest.json` is the executable catalog contract. It records order, identifier, category, kind, path, execution scope, merge strategy, privacy class, per-query SHA-256, total query count, and catalog digest. The final RDF/RDFS benchmark contains 113 queries. Two former SHACL-only inventory queries were removed with the SHACL runtime.

One catalogue round executes every manifest query once as a logical request. Replicated routing selects one complete participant and rotates selections across rounds. Distributed routing fans out ABox-dependent work to Edge authorities, deduplicates canonical set results, and applies logical OR to federated ASK queries. The Cloud consent dashboard runs against a minimal global consent projection. Physical executions and logical requests are persisted separately.

Modify a query only together with its manifest hash and differential tests. Query text must remain valid for Oxigraph SPARQL under the documented RDFS closure.

The human-readable index of all queries, categories, requirements, policies, scopes, and merge strategies is [docs/QUERY_CATALOG.md](../docs/QUERY_CATALOG.md).
