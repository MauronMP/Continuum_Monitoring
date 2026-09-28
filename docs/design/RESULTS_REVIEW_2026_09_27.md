# Results and figures review — 2026-09-27

## Decision

The recorded measurements are useful for diagnosing execution and coverage,
but they are not suitable for performance claims or paper figures. The active
report therefore retains only coverage and integrity diagnostics. Performance,
cost, scalability, placement and network panels remain suppressed until one
complete version-0.4.1 six-node suite satisfies the result contract.

## Evidence defects

- The datasets combine releases 0.3.1 and 0.4.0 with a five-node topology; the
  active release is 0.4.1 with six configured nodes.
- Distributed cumulative and scalability validation contain respectively 42
  and 48 mismatched query projections. Konclude is excluded from those timing
  curves.
- Physical load contains 345 records but no completed benchmark point: 65 are
  timeout-class outcomes and 280 are skipped.
- Distributed ontology contains five failures and 85 skipped observations.
  The recorded worker rejected preparation because the obsolete request did
  not include a serialized ontology fragment.
- Scale-out contains only two completed observations at one node-count value.
  It cannot establish a scale-out trend.
- Reasoning hardware contains 434 completed rows, 64 timeouts and 627 skipped
  rows. Several reasoner/dimension panels have no progression or only one
  completed x value.
- The dedicated distributed-reasoning-scalability dataset is absent.
- The latest recorded suite is incomplete and one metadata record was
  reconstructed after a failed validation.

## Reporting corrections

- A rejected report keeps only `evidence-readiness`, `execution-coverage`,
  `semantic-equivalence-coverage`, `load-completion-matrix` and
  `load-failures-and-loss`.
- Rejected performance figures are deleted from the report tree and listed in
  `report.json` under `suppressed_figures`.
- Derived performance tables are also deleted and listed under
  `suppressed_tables`; only integrity and coverage tables, plus any statistics
  belonging to retained figures, may remain in the generated report directory.
- `png-quality-audit.json` is regenerated from the retained image set. The
  current audit contains five PNG files and reports no blank image.
- Historical diagnostics carry a prominent red incompatibility banner.
- Progression figures require at least two distinct completed x values.
- Placement figures require at least one completed x value shared by both
  distributed and replicated layouts.
- Semantic-equivalence diagnostics show only the active physical matrix: RDFS,
  HermiT, Openllet, JFact and Konclude.
- Timeout/failure diagnostics aggregate the load dimensions instead of drawing
  unreadable reasoner-by-dimension labels.

## Execution corrections

Production configurations now use a five-minute request/phase budget and a
fifteen-minute point budget. A timed-out observation is retained and later
repetitions, sizes and stages continue. Smoke configurations remain short for
connectivity checks. `--unlimited` remains the correct mode when elapsed-time
cancellation must be disabled entirely.

## Required rerun

Do not reuse or relabel the current timing, category or policy rankings. After
Mist is deployed and healthy, create a new isolated suite directory:

```bash
. .venv/bin/activate
continuum-bench --unlimited --repetitions 5 suite
```

Accept its figures only when the suite is complete, every required family has
completed observations, distributed answer validation has no mismatch, all
five active reasoners have the intended matched coverage, and
`results-audit.json` contains
`"accepted_for_performance_claims": true`.
