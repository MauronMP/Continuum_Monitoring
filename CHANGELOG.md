# Changelog

## 0.4.1 — 2026-09-25

- Restricted every active physical comparison, including distributed reasoning
  scalability, to RDFS, HermiT, Openllet, JFact and Konclude.
- Added the sixth Mist authority and corrected query routing exposed by the
  four-authority partition.
- Added release/topology compatibility gates to publication reporting so
  five-node 0.4.0 evidence cannot be presented as a current six-node result.
- Added publication-style figures with explicit evidence status, panel labels,
  sample coverage and machine-readable acceptance findings.
- Added worker protocol 9 with exact benchmark-version and source build-ID validation.
- Corrected Raspberry Pi inventory architecture while retaining observed
  32-bit user-space details in dynamic health metadata.
- Removed tracked generated results and the final Compose-era environment file.
- Clarified the offline distributed verifier configuration interface and added
  topology/release provenance to its output.
- Removed the unrelated local RDF-product service and its RDFLib/Jena/RDF4J/
  Oxigraph comparison path; physical commands now expose only the five active
  backends.
- External OWL validation now compiles the 14 active modules, resolves their
  import closure locally, and records the flattened graph digest instead of
  validating the archived single-file source implicitly.

## 0.4.0 — 2026-09-22

- Added a dedicated physical `distributed-reasoning-scalability` experiment
  with strong and weak scaling, exact logical graph sizes and deterministic
  distributed/replicated placement.
- Added task-aware backends for identity, RDFS, OWL RL, combined RDFS+OWL RL,
  ELK, HermiT, Openllet, JFact and Konclude. Cross-engine performance is grouped
  by equivalent semantic output contracts.
- Added per-node measurements, capacity censoring, query-concurrency results,
  sampled semantic validation, bootstrap statistics and nine publication PNGs.
- Added ELK's isolated Maven runtime and explicit OWL 2 EL profile-incompatibility
  reporting. No fallback reasoner is used.
- Upgraded distributed RDF fragments to contract version 3 while retaining HTTP
  worker protocol version 8.
- Fixed independent propagation of request, phase and point timeout overrides.
  Unlimited execution disables benchmark alarms and timeout pruning without
  concealing application errors.
- Added the experiment to complete suites and consolidated evidence under
  `outputs/` by benchmark family.
- Updated installation, deployment, execution, audit, scientific-validity and
  publication documentation for the new contracts.
- Added the Raspberry Pi 500 Mist node at `100.72.111.107` and extended full
  node-count matrices to six physical workers. The node remains pending SSH and
  runtime provisioning.
- Corrected authority routing for `EXT-Q36` and `EXT-Q39`, and kept transfer
  identifiers with their transfer event during fragmentation. This removes
  semantic errors exposed when the Mist node increased the authority count.

## 0.3.1

- Established physical-only monitoring, native reasoner execution, modular
  ontology workloads and structured publication reporting.
