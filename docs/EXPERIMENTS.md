# Policy Evaluation Experiments

## Evaluation boundary

This controlled evaluator selects monitoring plans through procedural context
rules. The ontology validates identifiers; a separately timed synthetic reasoning
probe does not feed the decision engine. These experiments therefore do not
establish a semantic advantage over procedural rules. The alternative
[comparison module](COMPARATIVE_EVALUATION.md) explicitly distinguishes static,
procedural and semantic decisions.

Scenario generation, decision execution, process sampling, CSV export and figure
generation are separate components. The configuration is
`configs/policy-evaluation.toml`; the reduced verification profile is
`configs/policy-evaluation-smoke.toml`.

## Policy effectiveness

Each configured scenario defines ground truth for policies, resources, metrics,
sampling interval and actions. The static strategy always applies one broad plan.
The policy-driven strategy evaluates context conditions and creates a plan from
the active rules. A plan item is a policy, resource, metric, action or sampling
interval.

The experiment reports precision, coverage/recall, over-monitoring,
under-monitoring, policy false positives and false negatives, correctly selected
resources and metrics, and both actual and expected plans.

```bash
continuum-bench policy-evaluation effectiveness
```

## Dynamic adaptation

One run processes `normal → overload → failure → recovery`. Every transition
records the previous and new state, activated and deactivated policies, previous
and resulting plans, decision time, context-read time, separate reasoning cost,
policy evaluation and plan-generation time. Contexts and timeline timestamps are
supplied by configuration. The historical `detection_latency_ms` column times a
context assignment; `total_adaptation_latency_ms` includes the separate reasoning
probe. Neither measures physical fault detection or recovery.

Recovery is valid only when its plan matches ground truth and no policy from the
previous state remains stale.

```bash
continuum-bench policy-evaluation dynamic-adaptation
```

## Policy scalability

Every level increases all four independent workload variables: continuum
resources, evaluable policies, active policy categories and context events. The
same four context semantics are retained at every level. Warm-up and repetition
counts are configured outside the code.

Reported primary metrics are total policy-evaluation time, decision mean,
median, p95 and standard deviation, plan-generation time, decision throughput,
end-to-end throughput, CPU and RAM. Explicit triples, inferred triples, internal
reasoning time and final graph size remain secondary explanatory metrics.

```bash
continuum-bench policy-evaluation scalability
```

## Computational cost

Static and policy-driven strategies run the same scenario and resource set. The
experiment records mean and peak CPU, mean and peak RAM, decision and total
processing time, activated metrics, generated observations, aggregate sampling
frequency, event volume, monitored resources and timeouts. Policy-driven rows
also record reasoning, inferred triples, materialization and plan-generation
cost.

The cost runner repeats each decision a configured number of times before
reporting the mean per-decision cost. This avoids treating sub-millisecond
process-sampler startup as the workload itself.

Observation counts and network traffic are estimates, not emitted sensor events
or host-interface measurements. Traffic multiplies estimated observations by the
configured payload size. Cost figures divide the once-per-batch reasoning time
by `decision_iterations` before combining it with mean per-decision costs. The CSV labels
this method explicitly.

```bash
continuum-bench policy-evaluation computational-cost
```

## Reproducibility

Each row includes the experiment, scenario, strategy, load size, repetition,
policy category, random seed and final status. `metadata.json` records the source
revision, host, platform, ontology release, internal reasoner and complete public
configuration. Timing and operating-system resource measurements vary with the
host; scenario generation and policy activation are deterministic for a fixed
configuration and seed.

## Interpretation limits

Effectiveness scores combine policy identifiers with operational plan items;
they are plan-conformance diagnostics, not clinical effectiveness. Figure error
bars use scenario-averaged repetition means, not independent scenario samples.
Resource sampling covers the Python process, excluding native reasoner children.
Linux reports sampled current RSS; macOS reports explicitly labelled lifetime
peak RSS and cannot support an equivalent per-experiment memory comparison.
Use Linux for physical measurements. Missing resource values are never zero.
