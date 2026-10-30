# Origin-preserving adaptive monitoring

The default strategy is `origin-preserving-pools-v1`. It replaces the earlier relocation experiment, which could concentrate all logical services on Cloud. Historical archives retain their original behaviour and must not be presented as results of this strategy.

## Objective and mechanism

A saturated Edge, Mist or Fog authority keeps its existing container and fragment. The supervisor can create a read-only copy on an authorized host with enough CPU/RAM and route part of the catalog requests to it. Every original physical placement remains unchanged. Existing origin containers are never stopped or restarted by adaptation; Compose `start` only starts a service that was already stopped. Cleanup removes only the extra replica project.

Distributed preparation partitions the ontology using the original logical authorities only. A replica receives exactly its owner's serialized fragment, including its hash and privacy scope. A unique worker ID identifies the physical copy; `--replica-of` declares its logical owner and is checked against the explicit topology. Adding a replica does not create another authority or repartition users.

For a distributed catalog request, the coordinator chooses exactly one member of each required authority pool. Deterministic round-robin routing keeps the origin eligible and prevents duplicate contributions to union, count or single-source results. For replicated-layout requests, the original authority-selection order is retained, then successive requests assigned to that authority alternate across its pool. Very small request counts need not exercise every copy: consult actual routing evidence.

The current workload is read-only during query phases. Replicas are prepared from the same deterministic state before routing begins. There is no concurrent-write synchronization, live process-memory migration, decentralized controller or uninterrupted in-flight failover. Adaptation is evaluated between benchmark scenarios/attempts. Both verification layouts retain the original users, seed, query matrix, repetitions and deadlines.

## Policies and constraints

Executable bindings remain P-ADAPT-01/04/06/07/08, P-NODE-02/05, P-GOV-03, P-AUD-07 and P-OPS-02. They connect failure evidence, destination capacity/trust/authorization and an auditable action. This is a configured experimental interpretation of the policy declarations, not arbitrary natural-language policy execution.

`configs/adaptive-monitoring.toml` controls:

- `minimum_failures=1`, `max_failure_fraction=0.0`: consider any observed failure, independently per reasoner/concurrency stratum.
- `max_attempts=6`: bounded attempts per selected scenario/layout.
- `max_replicas_per_authority=2`: at most two extra copies; the origin remains in a pool of at most three.
- `max_extra_containers_per_host=2`: limit concentration, including on Cloud.
- Minimum trust, allowed destinations, cross-tier authorization and bounded lifecycle times.

Eligible non-Cloud hosts are preferred, then hosts with fewer additional containers, then trust and residual RAM/CPU. Cloud is a fallback within the same limits. All original and extra service reservations count towards capacity. These are conservative capacity proxies, not predicted latency or energy optima.

An action that worsens preparation failures or the overall request failure fraction is rejected for the following attempt; the preceding accepted pool is retained. All trial measurements, including rejected candidates, remain in the archive. This rollback rule is an experimental guard and not a statistical significance test.

A failed preparation does not automatically trigger a full-fragment copy: duplicating the same fragment cannot reduce its single-worker preparation cost while retaining the origin. The supervisor abstains explicitly in this case. Further intra-authority partitioning would need a separate correctness-preserving design. Unattributed failures, insufficient capacity and authorization failures also remain explicit abstentions.

The grant is restricted to `synthetic-container-scale`. Real health data needs effective consent, contract, residency and security enforcement before copying it. A physical Edge service copied to Fog retains its logical Edge scope.

## Evidence and acceptance

`decisions.json` records the strategy, owner/replica map, unchanged origins, candidates, phases, acceptance or rollback and cleanup. `phase_times` records warm-up and measured-phase start/end timestamps directly for new runs.

Every measured request produces `replica-routing.csv`: logical owner, actual worker, original/copy flag, layout, concurrency, success/failure, elapsed time, successful-request CPU and RSS. Missing failed-request CPU is unavailable, not zero. `node-runs.csv` identifies `replica_of`; physical storage and CPU costs include the copies, whereas logical inferred closure excludes duplicate replica contributions.

When digest validation is enabled, origin and replica input/closure digests must match. Semantic query validation remains separate from execution recovery. `execution_recovered` additionally requires observed successful query CPU on every replicated origin, so leaving the original container alive but unused is not enough.

`*-origin-work.png` shows original versus copy completed/failed worker requests and CPU. `analysis/replica-workshare.csv` preserves its values. Existing preparation, concurrency, CPU/RAM and placement plots remain available. Host telemetry now covers original containers and extra copies on every host. This does not retroactively create continuous baseline telemetry.

## Commands

Synchronize the new worker contract before a fresh campaign:

```bash
source .venv/bin/activate
continuum-bench --timeout-mode bounded container-scale deploy
continuum-bench --timeout-mode bounded --keep-going adaptive-monitoring run \
  --users 1 50 100 500 1000 2000 --concurrency 1 2 4 8
```

`--input-dir` accepts a compatible archived baseline; new concurrency overrides apply only to new baselines. Use `plan --input-dir PATH` for a non-mutating placement assessment. `report --input-dir PATH` regenerates reports without running workers. Unlimited mode is intentionally rejected.

The existing `outputs/latest` snapshot documents the previous relocation strategy. Keep it unchanged for traceability until a new, reviewed campaign replaces it using [the publication workflow](LATEST_RESULTS.md). It is not evidence of origin-preserving scale-out.

For a bounded physical mechanism check, run `python tools/validate_origin_pool.py`.
It records original container IDs, process IDs and start times before and after
adding an Edge 2 copy on Fog, then checks completed queries and query CPU on
both workers. An unavailable host can be explicitly excluded with
`--exclude-host HOST`; the validation record lists excluded hosts and the actual
origin count. Such a partial check does not validate the excluded host or replace
a complete scalability campaign.

The bounded validation additionally checks query CPU on every selected original,
semantic agreement for all sampled query comparisons, and telemetry coverage
across the selected hosts. It writes these checks to `validation.json` and creates
PNG work-sharing figures. A successful small check validates the mechanism; it
does not establish a scalability gain under high load.

## Replica coverage and completion guards (2026-10-27)

Replicated requests now advance across rounds in both the baseline and adaptive
execution. Each request selects one authority, then one member of its replica
pool; original services remain eligible. The default container scenarios use
18 rounds: at concurrency 1 this covers six authorities with up to two extra
copies per authority. Concurrency 2 and 4 generate 36 and 72 catalogue requests
per repetition respectively. These are catalogue requests, not individual queries.

Use the same rounds, workload, concurrency and deadlines for baseline and
adaptation. Larger topologies require proportionally more rounds. An archived
baseline with too few requests is rejected for adaptation before replica
deployment; run a new baseline rather than silently increasing only adaptive work.

Measured routing must cover every configured worker in each observed
reasoner/concurrency stratum. Missing participation cannot count as recovery.
A completed recovery also requires successful work on retained origins.
Expansion stops when preparation/request completion does not improve; equal
failure rates are no longer accepted as progress. A service-time timeout at
concurrency 1 may require query optimisation or smaller work units rather than
extra replicas.

Historical campaign 20261026T192739Z-42eb473e remains unchanged: its additional
replicas received no measured catalogue requests. It cannot establish adaptive
throughput benefits. New measurements are required.
