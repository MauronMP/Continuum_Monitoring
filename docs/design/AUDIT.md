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
| Separated hypotheses | Query scale-out, hardware reasoning, distributed ontology and strong/weak distributed reasoning | Implemented |
| Portable materialisers | RDFS, OWL RL and combined RDFS+OWL RL modes | Diagnostic adapters; outside the active matrix |
| OWL 2 DL validation | HermiT, Openllet, JFact and Konclude | Implemented as a separate consistency gate |
| Active reasoning matrix | RDFS, HermiT, Openllet, JFact and Konclude | Unified across monitoring, load, campaign and distributed reasoning scalability |
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
6. Custom elastic node identifiers could trigger eager tier inference despite a
   configured tier. Node startup now honours the declared tier first.
7. The duplicate flat physical inventory was removed. The layered topology is
   canonical, while the backward-compatible loader remains covered by a unit
   test.
8. The load generator previously sampled only alert queries and therefore
   omitted three categories from cost attribution. It now rotates through all
   115 queries while computing alert accuracy only over explicitly labelled
   alert checks.
9. Configuration files could place larger points before smaller ones, making
   monotone timeout pruning invalid. Loaders now reject duplicate or
   decreasing values per scale dimension before execution.
10. Partial architecture results could crash the load overview or disappear
   from experiment figures. The overview now tolerates missing combinations,
   and experiment reports include explicit completion/timeout/failure
   coverage.
11. The coordinator bootstrap unnecessarily required physical SSH tooling;
   `doctor --physical` now owns the optional SSH/rsync gate.
12. Global request, phase and point timeout overrides could overwrite one
   another while adapting family-specific configurations. Each override now
   updates only its intended budget; `--timeout-seconds` remains the explicit
   all-budget shortcut.
13. Distributed reasoning previously lacked a controlled strong/weak matrix.
   Exact graph-size padding, deterministic partitioning, per-node evidence,
   sampled answer validation, capacity censoring and query-concurrency metrics
   now form one independent experiment.
14. Release 0.4.1 adds a sixth Mist authority. The routing plan now places
    `EXT-Q36` with `UserD`, fans `EXT-Q39` across authorities and co-locates
    transfer identifiers with their events. Offline verification matches all
    115 query projections for every active reasoner across six fragments.
15. Publication acceptance now rejects mixed software releases, old topology
    fingerprints, reconstructed metadata, absent required families and families
    without a completed observation. Historical figures visibly disclose this
    status.

## Bounded-execution policy

| Suite | Request timeout | Point/phase deadline | Recovery deadline |
|---|---:|---:|---:|
| Monitoring full profiles | 300 s | 300--900 s | Not applicable |
| Load benchmark | 300 s | 900 s | 300 s |
| Research experiments | 300 s | 900 s | Not applicable |
| Distributed reasoning matrix | 300 s | 1,800 s | Not applicable |
| Monitoring/experiment smoke | 30 s | 45 s | Not applicable |
| Load smoke | 45 s | 90 s | 45 s |

A deadline creates a right-censored observation, not a fabricated latency.
Reports retain the timeout/error status and exclude incomplete rows from speedup
claims. Larger points are skipped only when monotonic workload growth makes them
uninformative for the same execution stratum.

## Semantic validation boundaries

- RDFS provides the portable rule-closure baseline used in timed physical
  experiments.
- HermiT, Openllet, JFact and Konclude provide the matched OWL DL named-class and
  individual contract. Their separate consistency-gate time must not be compared
  directly with timed materialization or SPARQL latency.
- ELK is an OWL 2 EL task. The current complete ontology is incompatible with
  its installed OWLAPI path, so those rows are profile evidence rather than
  successful performance observations.
- Exact result validation uses the canonical graph and query expectations; an
  HTTP success response alone is insufficient.

The runtime ontology is the union declared in `configs/benchmark.toml`.
`ontology/legacy/smartcity_continuum-v3.0.0.ttl` is retained as the controlled
release migration source and equivalence evidence; physical execution and
external OWL validation load the modular files. It changes only through the
documented regeneration workflow.

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
`docs/design/COMMAND_REFERENCE.md`. Physical smokes require reachable,
prepared hosts and therefore cannot be certified by an offline CI runner.

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

The entries below are historical functional checks. They do not supersede the
0.4.1 acceptance decision in `outputs/report/results-audit.json`.

| Validation | Observed result | Evidence |
|---|---|---|
| Version 0.4.0 default software suite | 399 passed; 12 documented optional skips | `outputs/validation/readiness/version-0.4-tests.log` |
| Version 0.4.0 focused native runtimes | 32 passed; 2 documented Konclude annotation warnings | `outputs/validation/readiness/version-0.4-native-tests.log` |
| Version 0.4.0 documentation | 33 files passed link/reference checks | `tools/check_documentation.py` |
| Fresh coordinator installation | Dependencies installed; pip check passed | `work/clean-venv` |
| Clean-environment software suite | 226 passed; 2 optional renderer tests skipped | `outputs/audit/pytest.xml` |
| Final CLI/campaign/result regression subset | 16 passed | Infrastructure, monitoring and reporting tests |
| Resource capacity adapter regression | 5 passed | `tests/infrastructure/test_topology.py` |
| Ontology validation and profile preflight | Both passed, scientific warnings retained | `continuum-bench validate` and `preflight` |
| Native OWL consistency | HermiT, Openllet, JFact and Konclude available and consistent | `outputs/validation/owl-reasoners.json` |
| Archived authority-partitioned scalability smoke | 6 completed, 0 timeouts | Historical `sharded` output, outside the active output tree |
| Physical replicated scalability smoke | 6 completed, 0 timeouts | `outputs/audit/monitoring/replicated/scalability` |
| Archived authority-partitioned scalability, 500 users | All 3 portable profiles completed, 0 timeouts | Historical `sharded` output, outside the active output tree |
| Physical event-load smoke | 6 completed, no lost events; acceptance passed | `outputs/audit/load` |
| Ten-axis physical campaign | 126 points, 0 failed | `outputs/audit/final-campaign/20260908T164004Z-967d25df` |
| Version 0.4.1 focused reporting/configuration tests | 34 passed | Publication acceptance and distributed-reasoner matrix tests |
| Version 0.4.1 six-fragment semantic verification | 115/115 queries matched for five active reasoners | Local canonical/partition projection check |

These are functional acceptance measurements, not a statistically powered
performance study. The larger repeated campaign configuration is provided but
has not been certified across its entire saturation range.

### Outstanding machine and scientific limits

Project container support has been removed. Any root-owned legacy containers are
outside the project lifecycle and are not benchmark dependencies. Physical
execution uses SSH, target-local virtual environments and native processes.

Configured resource capacities and processing scores are inventory declarations;
observed process architecture, CPU and memory are recorded separately. Storage
and network capacity are not calibrated hardware measurements. Location remains
unknown until supplied by the operator. Measurements taken with other host
activity are functional evidence and must be repeated on controlled hosts for
performance claims.

External OWL 2 DL tools now implement the finite named-class/individual
materialization contract as well as the separate consistency gate. This is not
a complete distributed OWL DL decision procedure. Synthetic campaign policies complement
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

This paragraph records the earlier physical-only migration gate: 227 tests passed
and one optional Graphviz renderer test was skipped. The physical load smoke
completed six points without lost events.
Load plots render successfully using the physical results alone. The cleanup
was synchronized to all four remote workers and file absence was checked over
SSH. Evidence is stored in `outputs/audit/physical-only-tests.xml` and
`outputs/audit/physical-only-load`.
