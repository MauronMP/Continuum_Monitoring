# Physical results audit — 2026-09-25

## Acceptance decision

The recorded campaign is **not accepted for aggregate performance claims**.
Software and ontology checks passed, and several benchmark subsets contain
usable completed observations, but the complete suite did not finish and two
recorded distributed datasets fail their semantic acceptance gate. The active
software is release 0.4.1 with six physical nodes; the recorded metadata belongs
to releases 0.3.1/0.4.0 and a five-node topology. The figures are therefore
historical diagnostics, not measurements of the current architecture.

The report generator writes the machine-readable decision to
`outputs/report/results-audit.json` and exposes failures in PNG coverage panels.
Completed subsets may be inspected descriptively when their exact dataset,
backend, layout, workload and limitations are stated.

## Recorded outcomes

| Dataset | Recorded outcomes | Audit interpretation |
| --- | --- | --- |
| Distributed cumulative | 240 raw rows; 192 accepted completed; 48 failed validation | Konclude performance is rejected for this dataset. |
| Distributed scalability | 48 raw completed; 12 failed validation; 5 timeout; 37 skipped | Konclude performance is rejected for this dataset. |
| Replicated cumulative | 240 completed | Accepted within the recorded configuration. |
| Replicated scalability | 42 completed; 5 timeout; 43 skipped | Completed points are usable; later capacity is censored. |
| Load | 26 workload timeout; 35 prepare timeout; 4 recovery timeout; 280 skipped | No completed benchmark point; no throughput ranking is supported. |
| Scale-out | 2 completed; 9 timeout; 30 skipped; 6 warm-up failed | Insufficient node-count coverage for a scaling claim. |
| Reasoning hardware | 434 completed; 64 timeout; 627 skipped | Only completed matched subsets are usable. |
| Distributed ontology | 5 transport errors; 85 skipped | No completed point in the current output. |
| Distributed reasoning scalability | No result dataset | The new experiment was not executed in the recorded campaign. |

The latest non-dry complete-suite record finished software, documentation,
semantic validation, preflight, external reasoner validation and worker startup.
Distributed and replicated monitoring then failed, load was interrupted, and
experiments, campaign and reporting were not executed by that suite. Later
top-level outputs come from independent invocations and are not one complete
suite run.

## Root causes and implemented corrections

1. **Distributed Konclude answer mismatch.** Recorded distributed validation
   contains 42 invalid cumulative projections and 48 invalid scalability
   projections, affecting `BASE-Q35`, `EXT-Q21`, `EXT-Q59` and `EXT-Q73`.
   The deployed worker revision used the previous partition contract. Current
   fragment contract 3 was checked offline on 2026-09-25: all 115 query
   projections matched the canonical graph for RDFS, HermiT, Openllet, JFact
   and Konclude. The old rows remain invalid and are never rewritten.
2. **Konclude native failure.** One replicated preparation ended with native
   exit `-11` after Konclude attempted to parse annotation literals as logical
   datatypes. Current code removes OWL annotations from the OWLlink logical
   request and restores the source annotations in the returned RDF graph.
   Native regression and offline six-fragment verification pass.
3. **Timeout propagation.** The recorded load worker still used a 44-second
   alarm even though the suite requested 180 seconds. Current CLI adaptation
   propagates request, phase and point overrides independently to every family.
   `--unlimited` disables benchmark alarms and timeout pruning while preserving
   real errors and nominal budgets.
4. **Stale distributed-ontology worker contract.** The output reports
   `Distributed preparation requires a serialized fragment`. Redeploying all
   workers from the same fragment-contract-3 revision is mandatory.
5. **Misleading empty figures.** Reasoner/category panels were emitted for
   backends with attempted events but no completed requests. They are now
   omitted. The report removes obsolete generated PNGs and adds semantic
   equivalence, load completion, capacity-frontier and normalized evidence
   readiness figures. All generated paper figures use one typographic style,
   panel letters, explicit units, legends, source captions and 300-DPI PNG.
6. **Authority routing exposed by the Mist node.** `EXT-Q36` was incorrectly
   routed with the `UserA` authority key although its result belongs to
   `UserD`; `EXT-Q39` was incorrectly treated as a single-authority query even
   though it combines several authorities. The three-authority topology hid
   this through a hash collision. The generated execution plan now routes
   `EXT-Q36` to `UserD`, executes `EXT-Q39` across authorities with set union,
   and co-locates transfer identifiers with their transfer events. All 115
   query projections now match the canonical graph for every configured
   reasoner across six local fragments.

## New Mist node

The inventory now contains Raspberry Pi 500 node `mist` at `100.72.111.107`.
It is a data authority, so distributed experiments assign it an ontology
fragment. Tailscale ping succeeds through DERP Madrid, but SSH port 22 refused
connections on 2026-09-25. Declared CPU, RAM, storage and network values remain
unverified.
Six-node results cannot be accepted until SSH, target dependencies, reasoner
runtimes and worker health pass on this node.

The final connectivity probe on 2026-09-25 showed Cloud and Mist online in
Tailscale, while Fog and all three Edge nodes had been offline for approximately
16 hours. Port 8391 refused connections on Cloud and Mist and timed out on the
offline nodes. No worker passed the HTTP health check, so a physical rerun was
not attempted during this audit.

## Repository and figure audit

- No active Dockerfile, Compose file or container deployment path is present.
- `ontology/legacy/` and `queries/legacy/` are immutable migration/reference
  inputs. Runtime code does not select them as a monolithic benchmark mode.
- Root-level monitoring modules that remain are compatibility imports; the
  implementations live under `continuum_bench.monitoring`.
- `sharded`, Identity, OWL RL, combined RDFS+OWL RL and ELK remain only in
  historical-result decoding, diagnostic adapters and their regression tests.
  New physical comparison configurations use RDFS, HermiT, Openllet, JFact and
  Konclude.
- The regenerated report contains 63 benchmark PNGs before the audit contact
  sheet. Every figure has non-empty raster content and publication-scale pixel
  dimensions. This is a rendering check; it does not make rejected data valid.
- `evidence-readiness.png` is the entry figure for deciding whether a dataset
  supports comparison. It exposes completion, timeout, skip and semantic-failure
  shares before any latency or resource chart is interpreted.

## Required rerun

After all six nodes are online:

```bash
continuum-bench physical authorize --ssh-user pi
continuum-bench physical stop --ssh-user pi
continuum-bench physical deploy --with-dl-reasoners --ssh-user pi
continuum-bench physical start --ssh-user pi
continuum-bench physical status --ssh-user pi

continuum-bench --config configs/smoke-vpn.toml --unlimited \
  physical scalability --layout distributed
continuum-bench experiment distributed-reasoning-scalability physical \
  --distributed-reasoning-config configs/distributed-reasoning-smoke.toml

continuum-bench --unlimited --repetitions 5 suite
```

Accept the rerun only if `results-audit.json` reports
`accepted_for_performance_claims: true`, semantic validation has no mismatch,
every required family contains completed rows and the suite records every step
as completed. It must also record release 0.4.1 and the active six-node topology
fingerprint. Preserve the current outputs as failed/censored historical evidence
rather than combining them with the new six-node campaign.
