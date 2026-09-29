# Policy Evaluation Experiments

## Evaluation boundary

The evaluated system is policy-driven monitoring. The ontology validates policy
identifiers, supplies semantic context and contributes an internal reasoning
cost. It is not the outcome being optimized, and the primary figures do not rank
reasoners.

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
and resulting plans, decision time, detection latency, internal reasoning cost,
policy evaluation latency, plan-generation latency and total adaptation latency.

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

Network traffic is an estimate, not a host-interface measurement. It multiplies
the generated observation count by the configured payload size. The CSV labels
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
