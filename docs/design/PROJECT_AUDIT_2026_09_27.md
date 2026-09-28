# Project audit — 2026-09-27

> Historical snapshot. Superseded by the
> [complete 2026-09-28 audit](PROJECT_AUDIT_2026_09_28.md). The local Java
> product service mentioned below was subsequently removed because it was
> outside the physical continuum benchmark.

## Decision

The local software, modular ontology and semantic contracts pass their release
checks. Five of the six configured workers are deployed and healthy. The
project is not ready for a complete physical performance campaign because Mist
is unavailable and the recorded benchmark results belong to older releases and
topologies.

## Verified software gates

| Gate | Result |
| --- | --- |
| Python suite | 414 passed; 12 documented optional skips; no failures |
| Documentation | 37 English documents; links and generated references valid |
| Package environment | Installed release 0.4.1; dependency check passed |
| Ontology structure | 7,966 triples; SHACL conforms; 115 queries load |
| OWL consistency | HermiT, Openllet, JFact and Konclude consistent; OWL 2 DL profile valid |
| Distributed equivalence | 115/115 query projections match for each active reasoner over six fragments |
| Load/experiment preflight | 24 load and 16 experiment targets accepted |
| Java engine service | Maven test lifecycle passed |

Ontology structural validity is separate from scientific acceptance. `EXT-Q76`
and `EXT-Q77` still expose missing acceptance-profile and campaign evidence.
Direct query traceability covers 102 of 116 requirements and 69 of 79 policies.

## Physical state

| Node | State | Release/runtime evidence |
| --- | --- | --- |
| Cloud | Healthy | 0.4.1, protocol 9, x86_64/64-bit |
| Fog | Healthy | 0.4.1, protocol 9, AArch64 kernel, 32-bit Python |
| Edge 1 | Healthy | 0.4.1, protocol 9, AArch64 kernel, 32-bit Python |
| Edge 2 | Healthy | 0.4.1, protocol 9, AArch64 kernel, 32-bit Python |
| Edge 3 | Healthy | 0.4.1, protocol 9, AArch64 kernel, 32-bit Python |
| Mist | Blocked | Tailscale responds through DERP Madrid; worker port 8391 refuses connections |

The four accessible Raspberry Pi hosts pass target-local dependency checks and
native inference/inconsistency smokes for HermiT, Openllet, JFact, ELK and
Konclude. Every healthy worker reports the same six-node topology fingerprint.
All five also report the exact current source build
`continuum-benchmark-0.4.1-protocol-9-source-bd6e7b2f04842145`.
No partial five-node result is accepted as a six-node campaign.

## Corrections made during this audit

- The inventory now records AArch64 hardware and leaves the 32-bit process ABI
  to dynamic health metadata.
- Worker protocol 9 records `benchmark_version` and a source-derived `build_id`;
  mixed releases or source trees are rejected during discovery and status checks.
- The offline distributed verifier now names its input
  `--benchmark-config`, validates malformed inputs and records the topology
  fingerprint and node count. `--config` remains a compatibility alias.
- The obsolete Compose environment template and its ignore exception were
  removed. A regression test prevents container deployment files from returning.
- Nine generated analysis/figure artifacts were removed from version control.
  All generated evidence belongs under ignored `outputs/` paths.
- Generated Python caches and temporary audit environments are ignored and are
  removed after validation.

## Repository boundaries

`continuum_bench.core` contains reusable domain contracts. Monitoring,
experiments, load generation, result normalization and reporting live under
`continuum_bench.monitoring`. Four-line root modules are compatibility imports,
not duplicate implementations. `ontology/legacy` and `queries/legacy` are the
immutable migration source used to check release equivalence; runtime execution
uses the modular ontology and individual query catalog.

Identity, OWL RL, combined RDFS+OWL RL and ELK remain diagnostic adapters and
historical labels. Active physical matrices use RDFS, HermiT, Openllet, JFact
and Konclude. ELK is still installed and smoke-tested because it is a useful
OWL 2 EL diagnostic, but it is not part of active performance comparisons.

## Remaining risks

- Mist must enable SSH, receive the same deployment, pass all native reasoner
  smokes and expose a protocol-9 worker before physical benchmarks can run.
- Existing `outputs/` results remain historical and rejected by publication
  acceptance because they mix older software, five-node topology and incomplete
  families.
- Raspberry Pi Java workloads run in a 32-bit user space with a 512 MiB heap;
  large OWL DL points may become memory-censored even in unlimited mode.
- Configured storage, processing and network capacities are inventory values,
  not calibrated measurements. Geographic coordinates remain unknown because
  the nodes are colocated and mobility is not yet simulated.
- Several orchestration modules are intentionally large. Further decomposition
  should follow stable runtime boundaries and measured maintenance needs rather
  than changing the tested execution contract during a benchmark campaign.

## Reproduction commands

```bash
. .venv/bin/activate
python -m pytest
python tools/check_documentation.py
continuum-bench validate
continuum-bench preflight
continuum-bench owl-validate --require-all
python tools/verify_distributed_reasoning.py \
  --benchmark-config configs/smoke-scalability.toml --users 10
continuum-bench physical status --ssh-user pi
```

After Mist is ready, redeploy every node and run the complete suite described in
[Run all physical tests](RUN_ALL_TESTS.md). Accept results only when
`outputs/report/results-audit.json` reports
`accepted_for_performance_claims: true`.
