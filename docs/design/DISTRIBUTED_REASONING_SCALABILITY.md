# Distributed reasoning scalability

This experiment measures how ontology reasoning changes when the same logical
input graph is replicated or distributed over physical continuum nodes. It is
implemented by `continuum_bench.monitoring.distributed_reasoning_scalability`
and configured independently in [`configs/distributed-reasoning.toml`](../../configs/distributed-reasoning.toml).

## Experimental contract

Every strong-scaling point fixes the seed, logical asserted triple count,
reasoner, repetition and selected physical nodes. `replicated` sends the full
graph to every selected worker. `distributed` places deterministic ontology and
instance fragments on the selected workers, retains required shared schema, and
merges query answers. It is ontology distribution, not shared memory and not
the retired `sharded` mode.

The coordinator verifies the logical graph digest for both layouts. On the
first repetition of every matrix point it also compares every query projection
with the replicated reference: result count, ASK result and result-set digest
must match. This is a 1/N validation sample and is written separately from the
timed measurements. It validates the tested query projections; it does not
claim that arbitrary distributed OWL DL closure is globally complete.

Local inferred triples are retained per node and as an observed aggregate.
Because shared schema can make the same consequence appear in more than one
fragment, the global `normalized_inferred_triples` and closure expansion use the
equivalent complete replica as the de-duplicated reference. The local-minus-
reference delta remains available to quantify duplication or missing closure.

Strong scaling uses a fixed logical graph and reports:

```text
speedup(n) = T(1) / T(n)
parallel efficiency(n) = speedup(n) / n
```

Weak scaling keeps `weak_triples_per_node` fixed and reports:

```text
weak efficiency(n) = T(1) / T(n)
```

Timeout observations are right-censored capacity bounds. `largest_successful_graph`
and `smallest_censored_graph` expose the tested interval instead of treating a
timeout as a zero or completed measurement.

## Reasoning tasks

Reasoners are grouped by output contract. Performance claims must be made
inside one task group unless the semantic difference is itself the subject of
the comparison.

| Active reasoner | Task | Profile and purpose |
| --- | --- | --- |
| `rdfs` | `rdfs_closure` | Deterministic RDFS materialisation baseline. |
| `hermit`, `openllet`, `jfact`, `konclude` | `owl_dl_classification_realization` | Named-class/individual OWL DL output contract. |

The repository still implements identity, OWL RL, combined RDFS+OWL RL and ELK
for isolated diagnostics and historical-result decoding. They are deliberately
absent from the active TOML matrices, so current figures cannot silently mix
those older task groups with the required five-backend comparison. Native
engines have no fallback: a missing runtime, incompatible profile or engine
failure is recorded as a failed or censored point.

## Matrix and time controls

The full configuration varies 50,000 to 2,000,000 asserted triples over 1, 2,
3, 5 and 6 physical nodes, with five repetitions. It enables strong and weak
scaling, both layouts, the active RDFS and OWL DL task contracts, and concurrent
query clients.

Edit these fields in [`configs/distributed-reasoning.toml`](../../configs/distributed-reasoning.toml):

- `[experiment]`: repetitions, request and point timeouts, seed, synthetic
  users/rules, padding mode, semantic validation and timeout pruning;
- `[matrix]`: exact triple sizes, node counts, layouts, reasoners and task
  contracts;
- `[scaling]`: strong/weak switches and triples per node;
- `[statistics]`: bootstrap sample count and confidence level;
- `[queries]`: client concurrency and rounds.

`stop_after_timeout = false` keeps attempting later points. To remove benchmark
elapsed-time cancellation entirely, put the global option before the command:

```bash
continuum-bench --unlimited --repetitions 5 experiment \
  distributed-reasoning-scalability physical \
  --distributed-reasoning-config configs/distributed-reasoning.toml
```

For a bounded integration run:

```bash
continuum-bench experiment distributed-reasoning-scalability physical \
  --distributed-reasoning-config configs/distributed-reasoning-smoke.toml
```

Generate the nine 300-DPI PNG figures after execution:

```bash
continuum-bench experiment plot distributed-reasoning-scalability
```

## Evidence

Results are stored in `outputs/experiments/distributed-reasoning-scalability/`:

| File | Evidence |
| --- | --- |
| `distributed-reasoning-summary.csv` | One row per matrix point and repetition, including graph size, closure, throughput, speedup, efficiency, overhead, resources and final state. |
| `node-runs.csv` | Per-node fragment, inference, timing, CPU, memory and transport measurements. |
| `distributed-reasoning-statistics.csv` | Samples, mean, median, standard deviation, quartiles, IQR and bootstrap 95% confidence interval. |
| `capacity-summary.csv` | Largest completed and smallest censored graph per layout/reasoner/node count. |
| `query-scalability.csv` | QPS, P50/P95/P99 latency, errors and network bytes by concurrency. |
| `semantic-validation.csv` | Sampled distributed-versus-replicated query equivalence. |
| `results.jsonl`, `metadata.json` | Machine-readable observations and complete reproducibility metadata. |

The figure set covers reasoning time, throughput, strong speedup, parallel
efficiency, weak efficiency, coordination overhead, fragment imbalance,
closure expansion and layout comparison. Statistics use completed repetitions;
censored and failed observations remain visible in the coverage report and are
never converted into completed values.

Query-concurrency measurements run on the first repetition of each strong-
scaling point. This 1/N sampling keeps the core five-repetition reasoning
matrix statistically independent from repeated client-pressure work.

## Interpretation limits

Distributed workers currently compute local fragment closure. Cross-fragment
arbitrary OWL DL inference would require a sound distributed reasoning
algorithm with explicit exchange/fixpoint semantics. The experiment therefore
reports local inferred triples, query-projection equivalence and the exact input
graph contract separately. A replicated layout consumes more aggregate storage
but can answer from any complete replica. A distributed layout reduces each
worker's data footprint and can improve throughput when placement and query
locality dominate; serialization, transport, imbalance and stragglers can erase
that benefit. The recorded overhead fields make those conditions testable.
