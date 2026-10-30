# Baseline versus recorded adaptation

Figures are in `../figures/`; their manifest lists every generated PNG. CSVs in this directory preserve denominators, strata and sample counts. Raw evidence is unchanged.

## Recorded actions

- users-1: edge1-c1 → cloud; not_recovered. Deployment 43.0 s; whole attempt 6.8 min (not service recovery time).
- users-1: edge2-c1 → cloud; not_recovered. Deployment 28.4 s; whole attempt 4.9 min (not service recovery time).
- users-1: edge3-c1 → cloud; not_recovered. Deployment 26.0 s; whole attempt 4.7 min (not service recovery time).
- users-1: fog-c1 → cloud; not_recovered. Deployment 24.0 s; whole attempt 4.7 min (not service recovery time).
- users-1: mist-c1 → cloud; execution_recovered. Deployment 21.1 s; whole attempt 2.9 min (not service recovery time).
- users-1 / replicated: not_needed; No configured failure threshold exceeded in this layout
- users-50: edge1-c1 → cloud; not_recovered. Deployment 31.7 s; whole attempt 7.6 min (not service recovery time).
- users-50: edge2-c1 → cloud; not_recovered. Deployment 28.5 s; whole attempt 5.7 min (not service recovery time).
- users-50: edge3-c1 → cloud; not_recovered. Deployment 27.1 s; whole attempt 5.8 min (not service recovery time).
- users-50: fog-c1 → cloud; not_recovered. Deployment 24.4 s; whole attempt 5.6 min (not service recovery time).
- users-50: mist-c1 → cloud; execution_recovered. Deployment 21.1 s; whole attempt 3.5 min (not service recovery time).
- users-50 / replicated: not_needed; No configured failure threshold exceeded in this layout
- users-100: edge1-c1 → cloud; not_recovered. Deployment 32.0 s; whole attempt 8.9 min (not service recovery time).
- users-100: edge2-c1 → cloud; not_recovered. Deployment 29.3 s; whole attempt 7.0 min (not service recovery time).
- users-100: edge3-c1 → cloud; not_recovered. Deployment 26.5 s; whole attempt 6.8 min (not service recovery time).
- users-100: fog-c1 → cloud; not_recovered. Deployment 24.1 s; whole attempt 6.5 min (not service recovery time).
- users-100: mist-c1 → cloud; execution_recovered. Deployment 21.3 s; whole attempt 4.1 min (not service recovery time).
- users-100 / replicated: not_needed; No configured failure threshold exceeded in this layout
- users-500: edge1-c1 → cloud; not_recovered. Deployment 32.5 s; whole attempt 24.4 min (not service recovery time).
- users-500: edge2-c1 → cloud; not_recovered. Deployment 28.9 s; whole attempt 20.8 min (not service recovery time).
- users-500: edge3-c1 → cloud; not_recovered. Deployment 26.2 s; whole attempt 21.1 min (not service recovery time).
- users-500: fog-c1 → cloud; not_recovered. Deployment 24.5 s; whole attempt 21.2 min (not service recovery time).
- users-500: mist-c1 → cloud; execution_recovered. Deployment 25.1 s; whole attempt 12.3 min (not service recovery time).
- users-500: edge2-c1 → cloud; execution_recovered. Deployment 31.9 s; whole attempt 21.0 min (not service recovery time).
- users-1000: edge1-c1 → cloud; not_recovered. Deployment 32.9 s; whole attempt 47.9 min (not service recovery time).
- users-1000: edge2-c1 → cloud; not_recovered. Deployment 29.8 s; whole attempt 43.2 min (not service recovery time).
- users-1000: edge3-c1 → cloud; not_recovered. Deployment 26.2 s; whole attempt 41.8 min (not service recovery time).
- users-1000: fog-c1 → cloud; not_recovered. Deployment 25.3 s; whole attempt 41.9 min (not service recovery time).
- users-1000: mist-c1 → cloud; execution_recovered. Deployment 21.4 s; whole attempt 29.4 min (not service recovery time).
- users-1000: mist-c1 → cloud; not_recovered. Deployment 33.7 s; whole attempt 47.5 min (not service recovery time).
- users-1000: edge1-c1 → cloud; not_recovered. Deployment 30.7 s; whole attempt 46.8 min (not service recovery time).
- users-1000: edge2-c1 → cloud; execution_recovered. Deployment 26.5 s; whole attempt 40.5 min (not service recovery time).
- users-2000: edge2-c1 → cloud; not_recovered. Deployment 31.4 s; whole attempt 49.7 min (not service recovery time).
- users-2000: edge1-c1 → cloud; not_recovered. Deployment 28.7 s; whole attempt 47.9 min (not service recovery time).
- users-2000: edge3-c1 → cloud; not_recovered. Deployment 27.7 s; whole attempt 45.7 min (not service recovery time).
- users-2000: mist-c1 → cloud; not_recovered. Deployment 25.1 s; whole attempt 55.2 min (not service recovery time).
- users-2000: edge1-c1 → mist; not_recovered. Deployment 26.6 s; whole attempt 54.8 min (not service recovery time).
- users-2000: edge1-c1 → edge2; not_recovered. Deployment 28.1 s; whole attempt 45.1 min (not service recovery time).
- users-2000 / replicated: failed; no measured recovery result

## Interpretation

Completion compares recorded preparations and complete catalog requests. Missing requests are not successes or zero-cost measurements. Replicated measurements inside a distributed relocation trial are retained, explicitly labelled; they are not evidence that the supervisor executed a separate replicated recovery. An abstention remains an abstention.

Latency includes successful requests only. P95 values are medians of run-level quantiles, not a pooled tail estimate, and are weakly estimated with few requests. Node preparation plots show conditional costs from successful preparations, with observed ranges rather than confidence intervals. Recovery telemetry covers warm-up and both verification layouts and has no equivalent continuously sampled baseline in this archive. Do not use it as a before/after resource reduction claim.

A placement intervention may improve preparation without restoring service-level success. Restart effects, changing host load, limited repetitions and unequal successful sample counts prevent a causal superiority claim. Missing replicated reference validation does not prove semantic inconsistency or equivalence. Deployment duration and complete experiment duration are not production recovery time.
