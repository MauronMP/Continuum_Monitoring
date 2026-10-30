# Latest campaign: outcome and scientific interpretation

Campaign: `20261022T195405Z-d0e49f90`. RDFS, six physical hosts, six user levels and concurrent catalog-request levels 1, 2, 4 and 8. The baseline began at 2026-10-22 19:54:05 UTC. The last adaptive attempt finished at 2026-10-23 12:26:46 UTC: approximately 16 h 33 min, excluding final report generation. The adaptive section accounts for approximately 14 h 7 min. This is experiment duration, not production recovery latency.

## Final outcomes

| Users | Distributed | Replicated |
| --- | --- | --- |
| 1 | Recovered after 5 attempts; 45/45 requests | No intervention required |
| 50 | Recovered after 5 attempts; 45/45 requests | No intervention required |
| 100 | Recovered after 5 attempts; 45/45 requests | No intervention required |
| 500 | Recovered after 5 attempts; 45/45 requests | Recovered after 1 attempt; 45/45 requests |
| 1000 | Recovered after 5 attempts; 45/45 requests | Recovered after 3 attempts; 45/45 requests |
| 2000 | Unresolved after 6 attempts; final preparation 0/3 | Deployment failed; application not measured |

There are 36 actual attempts: 7 ended in execution recovery, 28 did not recover, and 1 failed during deployment. Three further scenario/layout decisions required no intervention. No cleanup errors were recorded. Recovery here means successful preparation and catalog requests, not clinical accuracy or proof of all ontology entailments.

## What improved, and at what cost

All distributed recoveries through 1000 users ultimately placed all six logical services on Cloud. This demonstrates recovery by relocating distributed logical authorities onto a stronger physical host, not preservation of a geographically distributed architecture. The placement matrix makes this explicit. Replicated 500 users used two services on Cloud; replicated 1000 users used four.

At 2000 distributed users the attempt sequence completed 21/45, 22/45, 24/45, 37/45 and 24/45 requests; the sixth attempt failed all three preparations and attempted no requests. The fourth attempt was the best observed, not the final result. Moving Edge 1 from Cloud to Mist and subsequently to Edge 2 worsened execution. The policy has no performance-regression rollback: capacity eligibility and trust ranking do not predict query latency. Do not present the best attempt as a successful final recovery.

The replicated 2000-user action attempted to move the Cloud authority to Mist. All recovery endpoints subsequently refused connections during readiness checks. The archive establishes deployment failure, but does not contain sufficient container startup logs to identify why. This is not evidence of an ontology contradiction, nor proof that Mist cannot execute any replica.

## When adaptation triggers

Decisions occur after completion of an archived baseline scenario, then between attempts; this is not immediate, continuously triggered recovery during baseline execution. The recorded policy uses one failure and a zero permitted failure fraction, separately by concurrency/reasoner. `baseline-triggers.png` shows request failure strata; preparation failures are separately recorded in `scenario-outcomes.csv`. `attempt-phases.csv` contains each decision's actual start, source, destination, triggering strata and outcome.

The current sequential HTTP workers may queue concurrent requests. Connection resets and timeouts alone do not identify a semantic error. Future experiments should distinguish admission/backlog limitations from reasoning cost, and compare relocation against an identical restart-only control. Add a policy constraint against excessive Cloud concentration if maintaining physical distribution is part of the research claim.

## Timing and resources

The new review contains 20 PNGs: per-scenario attempt trajectories, CPU/RAM timelines, trigger strata, placement evolution and the full adaptation schedule. Warm-up and measured intervals are reconstructed from recorded setup duration and engine metadata generation timestamps. They include waits/report generation and are labelled as intervals, not exact profiler timings. No missing phase has been invented. Failed deployment has no application or RAM measurements.

There are 11,721 host samples, including 90 sample records with an error. Missing telemetry remains missing, not zero. The largest sampled per-host aggregate Docker RAM was 2,984.6 MiB. These are sampled values, not guaranteed instantaneous peaks. Docker CPU 100% means one core; aggregation across six Cloud services can approach 600%. These traces include warm-up and both verification layouts. There is no matched continuous baseline telemetry, so they cannot establish a before/after resource saving.

Three measured repetitions and one warm-up are repeated for each intervention, including both layouts and all concurrency levels. That repeated verification, together with timeouts, explains the long duration. Multiple adaptive attempts are dependent observations, not independent statistical repetitions. Conditional latency measurements exclude failed requests; always show completion beside latency.

## Files to use

- `campaign-timeline.png`: actual decision/attempt schedule.
- `baseline-triggers.png`: baseline request failure percentage by concurrency.
- `placement-evolution.png`: planned service counts per physical host and attempt, including the failed deployment plan.
- `users-*-trajectory.png`: success denominators, phase intervals and sampled RAM peaks.
- `users-*-resources.png`: CPU/RAM response with attempt-start markers and gaps preserved.
- `scenario-outcomes.csv`, `attempt-phases.csv`, `baseline-trigger-strata.csv`, `resource-samples.csv`: underlying data.

Original detailed comparison plots remain in `../figures/`; raw inputs and the nested baseline are retained. No new benchmark or node deployment was run for this review.
