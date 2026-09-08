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
| Elastic physical continuum | SSH deployment from per-tier TOML files | Implemented |
| Cumulative category workload | Adds catalog categories and runs all accumulated queries | Implemented |
| Synthetic scalability | Increases users and ABox volume with bounded right-censoring | Implemented |
| Load dimensions | Events/s, users, triples, rules and effective node count | Implemented |
| Separated hypotheses | Query scale-out, hardware reasoning and distributed ontology | Implemented |
| Portable materialisers | RDFS, OWL RL and combined RDFS+OWL RL modes | Implemented |
| Independent RDF products | RDFLib, Apache Jena, Eclipse RDF4J and Oxigraph | Implemented in an isolated product matrix |
| OWL 2 DL validation | HermiT, Openllet, JFact and Konclude | Implemented as a separate consistency gate |
| Policy/category/query cost | Event attribution, including fractional attribution | Implemented |
| Physical figures | Resource and workload observations from continuum nodes | Implemented |

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
7. Custom elastic node identifiers could trigger eager tier inference despite a
   configured tier. Node startup now honours the declared tier first.
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
    `doctor --physical` owns the optional SSH/rsync gate.

## Bounded-execution policy

| Suite | Request timeout | Point/phase deadline | Recovery deadline |
|---|---:|---:|---:|
| Monitoring full profiles | 60 s | 60--90 s | Not applicable |
| Load benchmark | 45 s | 60 s | 45 s |
| Research experiments | 45 s | 60 s | Not applicable |
| Monitoring/experiment smoke | 30 s | 45 s | Not applicable |
| Load smoke | 45 s | 90 s | 45 s |

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

- Generated results, local configuration, environments, caches, IDE settings,
  logs and build artifacts are ignored by Git.
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

## September 2026 implementation audit

The implemented architecture, repository tree, ports, installation commands and
reproduction contracts are described in [Modular physical monitoring](MODULAR_MONITORING.md).

Additional corrections verified during this audit:

- Benchmark implementations now live in `monitoring`; root-level compatibility
  aliases preserve existing imports. The reusable core has no monitoring imports.
- Physical-only deployment replaces the removed container build files, topology,
  commands, CI job and native-reasoner container fallback.
- `EXT-Q26` binds its small type set before the user identifier join. Exact result
  bags remain equal across the three portable reasoning profiles.
- Native JFact uses matching Guice and AssistedInject versions. Explicit HermiT
  runtime selection takes precedence over ambient configuration.
- Unknown geographic coordinates are omitted from generated TOML. A round-trip
  regression prevents the previous invalid `null` values.
- Managed worker shutdown verifies process ownership, handles stale PID files,
  and recovers the live worker PID from verified health metadata.
- A coordinator lease prevents overlapping physical runs from resetting workers.
- Load smoke budgets now accommodate measured Raspberry Pi preparation times of
  approximately 23 seconds; the old 14-second worker budget was insufficient.
- Ten-axis campaigns inject infrastructure, reasoners, metrics and result sinks.
  They validate complete result bags against a bounded independent reference and
  preserve input configuration, source archives and dependency provenance.
- Query coverage is validated before execution: requests must cover query count.
  Timeouts, setup failures and unobserved requests remain explicit result states.
- Mobility implementation is static only; future models have an extension port.

### Observed acceptance evidence

Evidence is machine-local under `outputs/` and deliberately ignored by Git.

| Validation | Observed result | Evidence |
|---|---|---|
| Fresh coordinator installation | Dependencies installed; pip check passed | `work/clean-venv` |
| Clean-environment software suite | 226 passed; 2 optional renderer tests skipped | `outputs/audit/pytest.xml` |
| Final CLI/campaign/result regression subset | 16 passed | Infrastructure, monitoring and reporting tests |
| Resource capacity adapter regression | 5 passed | `tests/infrastructure/test_topology.py` |
| Ontology validation and profile preflight | Both passed, scientific warnings retained | `continuum-bench validate` and `preflight` |
| Native OWL consistency | HermiT, Openllet, JFact and Konclude available and consistent | `outputs/validation/owl-reasoners.json` |
| Physical sharded scalability smoke | 6 completed, 0 timeouts | `outputs/audit/monitoring/sharded/scalability` |
| Physical replicated scalability smoke | 6 completed, 0 timeouts | `outputs/audit/monitoring/replicated/scalability` |
| Physical sharded scalability, 500 users | All 3 reasoning profiles completed, 0 timeouts | `outputs/audit/scalability-500/sharded/scalability` |
| Physical event-load smoke | 6 completed, no lost events; acceptance passed | `outputs/audit/load` |
| Ten-axis physical campaign | 126 points, 0 failed | `outputs/audit/final-campaign/20260908T164004Z-967d25df` |

These are functional acceptance measurements, not a statistically powered
performance study. The larger repeated campaign configuration is provided but
has not been certified across its entire saturation range.

### Outstanding machine and scientific limits

The physical SSH account cannot access the system container socket and cannot
run `sudo` without an interactive password on the Raspberry Pi workers. Project
container support has been removed, but removal of root-owned legacy containers
has not been verified. An administrator must inspect those services and remove
only the legacy project instances. This is an operating-system privilege limit,
not an automatic approval-review rejection.

Configured resource capacities and processing scores are inventory declarations;
observed process architecture, CPU and memory are recorded separately. Storage
and network capacity are not calibrated hardware measurements. Location remains
unknown until supplied by the operator. Measurements taken with other host
activity are functional evidence and must be repeated on controlled hosts for
performance claims.

External OWL 2 DL tools currently validate consistency rather than implementing
the physical graph-materialization port. Synthetic campaign policies complement
the canonical policy workload; they do not prove coverage of every real policy.
Shared mode aliases the distributed-data/shared-schema treatment. Workers execute
queries serially; client concurrency measures queueing pressure. Cross-host
coordinator scheduling remains external. These boundaries are explicit in the
architecture guide and are not reported as completed future functionality.


## Physical-only execution acceptance

The execution surface now contains only the continuum topology. Cumulative and
scalability execution, load generation, separated experiments and study traces
all use physical nodes. The retired execution module, configuration inventory,
console scripts, tests and comparison-ratio plots have been removed. Native
ontology consistency checks and canonical result validation remain semantic
acceptance checks, outside measured experiment execution.

The current software suite passes 227 tests; one optional Graphviz renderer test
is skipped. The physical load smoke completes six points without lost events.
Load plots render successfully using the physical results alone. The cleanup
was synchronized to all four remote workers and file absence was checked over
SSH. Evidence is stored in `outputs/audit/physical-only-tests.xml` and
`outputs/audit/physical-only-load`.
