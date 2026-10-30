# Campaign interpretation

Start with `../figures/global-*-completion.png`, then `global-*-costs.png` and
`global-*-tradeoffs.png`. Load-specific figures compare users and neutral data
padding. Individual host and request-concurrency figures remain in `figures/`.
CSV tables contain the exact plotted statistics and cost ratios.

- Missing or timed-out results are not zero and are not imputed as deadline values.
- Cost ratios require complete cohorts and available sampled query equivalence.
- Error bars are observed min–max ranges, not confidence intervals. Three
  repetitions do not support strong inferential claims.
- Layouts run sequentially, not in randomized order. Process RSS may retain
  allocator state from earlier scenarios and is not host/cgroup memory.
- Preparation is asymmetric: distributed sends fragments; replicated generates
  its graph locally. Payload bytes are serialized messages, not VPN traffic.
  Completion under these budgets does not isolate reasoning capacity alone.
- Semantic checks cover the first repetition and the configured query catalog.
  An unavailable replicated reference cannot establish correctness or mismatch.
- Neutral padding tests data volume, not richer policies or ontology complexity.
- One participant-count level cannot demonstrate strong/weak scaling efficiency.
  Two user or data levels show sensitivity, not an asymptotic scaling law.
- Historical raw results are unchanged. Read semantic-validation.csv to distinguish
  a missing reference from historical summary labels saying mismatch.
