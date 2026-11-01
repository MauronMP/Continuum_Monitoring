# SPARQL Catalog

`manifest.json` is the executable catalog contract. It records order, identifier, category, kind, path, execution scope, merge strategy, privacy class, per-query SHA-256, total query count, and catalog digest. The final RDF/RDFS benchmark contains 113 queries. Two former SHACL-only inventory queries were removed with the SHACL runtime.

One catalog round executes every manifest query once as a logical request. Replicated routing selects one participant and rotates selections across rounds. Distributed routing fans out and merges canonical set results. Physical executions and logical requests are persisted separately.

Modify a query only together with its manifest hash and differential tests. Query text must remain valid for Oxigraph SPARQL under the documented RDFS closure.
