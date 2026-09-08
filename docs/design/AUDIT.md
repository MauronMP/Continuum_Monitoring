# Repository audit and acceptance status

## Scope

This audit covers executable objectives, package boundaries, ontology and query
contracts, topology elasticity, timeout behaviour, installation portability,
smoke-test acceptance, scientific outputs and documentation. A green software
gate does not prove that a distributed architecture is faster. It proves that
the same bounded workload can be measured without hiding failures.

## Objective traceability

| Objective | Implementation | Status |
|---|---|---|
| Native one-node control | `continuum-bench local` and the monolith topology | Implemented |
| Elastic local continuum | Generated Compose topology from per-tier TOML files | Implemented |
| Elastic physical continuum | SSH deployment from per-tier TOML files | Implemented |
| Cumulative category workload | Adds catalog categories and runs all accumulated queries | Implemented |
| Synthetic scalability | Increases users and ABox volume with bounded right-censoring | Implemented |
| Load dimensions | Events/s, users, triples, rules and effective node count | Implemented |
| Separated hypotheses | Query scale-out, hardware reasoning and distributed ontology | Implemented |
| Portable materialisers | RDFS, OWL RL and combined RDFS+OWL RL modes | Implemented |
| Independent RDF products | RDFLib, Apache Jena, Eclipse RDF4J and Oxigraph | Implemented in an isolated product matrix |
| OWL 2 DL validation | HermiT, Openllet, JFact and Konclude | Implemented as a separate consistency gate |
| Policy/category/query cost | Event attribution, including fractional attribution | Implemented |
| Three-architecture figures | Matched local, Docker and physical observations | Implemented |

## Critical findings corrected

1. Some configured triple targets were smaller than the immutable ontology plus
   generated observations. They failed remotely as HTTP 400 responses. Exact
   graph-size preflight validation now rejects impossible profiles before any
   worker is contacted.
2. A timeout in one reasoner previously suppressed later reasoners. Cumulative
   and scalability censor only larger points for the same reasoner. Load tests
   censor only the same reasoner and dimension; node-count scale-out points are
   retained because adding nodes may improve the result.
3. Contiguous query batches concentrated expensive queries on a single worker.
   Distributed execution now interleaves the cost-ranked battery across batches.
4. Remote HTTP errors discarded the worker response body. The client now keeps
   the diagnostic status and affected query identifiers.
5. Old smokes could return zero without examining their result tables. Every
   smoke now writes to `outputs/smoke`, checks the expected summaries and rejects
   timeout, error, loss or semantic-validation rows.
6. A prior cleanup removed the native monolith runner and the independent
   semantic-product matrix. Both have been restored as explicit, separately
   documented execution paths.
7. Custom elastic node identifiers could trigger eager tier inference despite a
   configured tier. Node startup now honours the declared tier first.
8. CI used removed command-line flags and a static Compose file. The workflow now
   validates configurations and exercises the generated topology commands.
9. The duplicate flat physical inventory was removed. The layered topology is
   canonical, while the backward-compatible loader remains covered by a unit
   test.
10. The load generator previously sampled only alert queries and therefore
    omitted three categories from cost attribution. It now rotates through all
    115 queries while computing alert accuracy only over explicitly labelled
    alert checks.
11. Configuration files could place larger points before smaller ones, making
    monotone timeout pruning invalid. Loaders now reject duplicate or
    decreasing values per scale dimension before execution.
12. Partial architecture results could crash the load overview or disappear
    from experiment figures. The overview now tolerates missing combinations,
    and experiment reports include explicit completion/timeout/failure
    coverage.
13. The coordinator bootstrap unnecessarily required physical SSH tooling for
    local-only and Docker installations. Base installation is now independent;
    `doctor --physical` owns the optional SSH/rsync gate.

## Bounded-execution policy

| Suite | Request timeout | Point/phase deadline | Recovery deadline |
|---|---:|---:|---:|
| Monitoring full profiles | 60 s | 60--90 s | Not applicable |
| Load benchmark | 45 s | 60 s | 45 s |
| Research experiments | 45 s | 60 s | Not applicable |
| Monitoring/experiment smoke | 30 s | 45 s | Not applicable |
| Load smoke | 15 s | 20 s | 20 s |
| Semantic-product Compose | 120 s startup | Per-query profile limit | 600 s image-build limit |

A deadline creates a right-censored observation, not a fabricated latency.
Reports retain the timeout/error status and exclude incomplete rows from speedup
claims. Larger points are skipped only when monotonic workload growth makes them
uninformative for the same execution stratum.

## Semantic validation boundaries

- RDFLib, Jena, RDF4J and Oxigraph compare query observability and product-level
  execution cost. They are not presented as interchangeable OWL 2 DL reasoners.
- RDFS, OWL RL and their combined materialisation modes exercise portable rule
  closure used by the monitoring workload.
- HermiT, Openllet, JFact and Konclude form an independent ontology-consistency
  gate. Their validation time must not be compared directly with SPARQL endpoint
  query latency.
- Exact result validation uses the canonical graph and query expectations; an
  HTTP success response alone is insufficient.

The canonical complete ontology remains
`ontology/legacy/smartcity_continuum-v3.0.0.ttl`. Runtime partitions are derived
artifacts and must not be opened in Protégé as replacements for that source.

## Repository hygiene

- Generated measurements, plots, runtime state, caches and rendered Compose
  files are ignored by Git.
- Existing `outputs/` data are deliberately preserved because they may contain
  the user's experiment evidence; cleanup never deletes measurements silently.
- Credentials are not stored in topology files. SSH keys or an external secret
  mechanism are required for unattended physical execution.
- Layer files under `configs/topologies/<architecture>/nodes/` are the only node
  inventory source for new deployments.

## Acceptance commands

```bash
.venv/bin/continuum-bench validate
.venv/bin/continuum-bench preflight
.venv/bin/python -m pytest -q
.venv/bin/python tools/check_documentation.py
```

Then run the architecture-specific smoke gates documented in
`docs/design/COMMAND_REFERENCE.md`. Run `continuum-smoke-engines` before
`continuum-bench engines plot`; plotting intentionally rejects a partial
four-product data set. Physical smokes require reachable, prepared hosts and
therefore cannot be certified by an offline CI runner.

## Scientific limits

The suite supports controlled comparisons; it does not encode the desired
conclusion that continuum deployment must be faster. Reported improvements must
come from matched profiles, repeated completed observations, uncertainty
intervals and disclosed timeout counts. A failed or censored high-load point is
capacity evidence, but it is not a valid speedup value. WAN conditions, thermal
throttling, JVM warm-up, cache state and heterogeneous ARM/x86 hardware remain
threats to validity and must accompany any paper-level result.

The current reference data are structurally valid but are not yet a completed
scientific acceptance campaign: `EXT-Q76` and `EXT-Q77` still expose missing
acceptance-profile/campaign evidence. Direct query metadata covers 102 of 116
requirements and 69 of 79 policies; uncovered IDs require other evidence or
future competency queries. Neither limitation is converted into a green claim
by the benchmark harness.
