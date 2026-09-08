# Test and validation catalogue

The project separates software checks, semantic validation, smoke tests and
measurement campaigns. A command returning zero only certifies the contract of
that command; it does not imply scientific acceptance of every requirement.

## Difference between benchmark families

| Family | Main question | What changes | Principal outputs |
| --- | --- | --- | --- |
| Normal cumulative | What is the cost of enabling more semantic/policy functionality? | Categories and all queries accumulated stage by stage | Per-stage/query execution and inference timings |
| Normal scalability | How does the monitoring ontology react to larger synthetic graphs and user populations? | Synthetic users and RDF individuals/volume | Per-block/query timings, inferred triples and timeout state |
| Load, one dimension | Where is the saturation point for one controlled factor? | One of events/s, users, triples, rules or active nodes | Event, node and summary rows with percentiles, throughput, loss and resources |
| Load, complete matrix | How does the system respond across all configured demand axes? | Every enabled load profile and dimension | The union of all load observations and coverage data |
| Experiments all | Which architectural mechanism explains performance? | Replicas/node count, reasoning hardware, then ontology partitioning | Three experiment datasets and architecture-specific comparisons |

“Normal” tests execute the ontology/query catalogue under two broad progression
models. Load tests model sustained request pressure and resource saturation.
Experiments deliberately isolate architectural hypotheses so that a speedup is
not attributed to distribution when it actually comes from replication,
different hardware or a smaller ontology fragment.

There is no literal `continuum-bench load all` command. The complete matrix is
selected by omitting filters:

```bash
continuum-bench load physical
```

By contrast, `continuum-bench experiment all physical` and `continuum-bench
experiment all physical` are real aggregate commands and execute the three
experiment families sequentially.

## Software and documentation checks

```bash
python -m pytest
continuum-bench preflight
python3 tools/check_documentation.py
git diff --check
```

`pytest` covers configuration loading, topology elasticity, ontology/query
contracts, mobility, placement, orchestration, timeout censoring and analysis.
The documentation checker validates internal links and documented paths.

## Semantic checks

```bash
continuum-bench validate
continuum-bench owl-validate
continuum-bench owl-validate --require-all
```

The first command runs the internal RDF/SHACL/query battery and the three
portable materialization profiles. The second invokes every available external
OWL validator. The strict form requires HermiT, Openllet, JFact and Konclude.
An unavailable reasoner is reported as unavailable, never as a success.

Scientific acceptance is stricter than process success. Known unmet external
query expectations, including EXT-Q76/EXT-Q77 when present in the current
reference set, remain explicit limitations and must not be hidden by a green
structural validation.

## Smoke tests



Physical:

```bash
continuum-smoke-physical-cumulative --ssh-user pi
continuum-smoke-physical-scalability --ssh-user pi
continuum-smoke-physical-load
continuum-smoke-physical-experiments
continuum-smoke-physical-cumulative --layout replicated --ssh-user pi
continuum-smoke-physical-scalability --layout replicated --ssh-user pi
```

Smokes use bounded profiles and one repetition to verify deployment,
partitioning, query execution, result transport and CSV generation. They now
inspect the generated summaries and exit non-zero for timeout, early skip,
event loss or incomplete semantic validation. They are not performance
evidence.

The unit suite also injects simulated HTTP 408/timeout failures into both
replicated and sharded scalability runners. It verifies that later points for
the affected reasoner become `skipped_after_timeout` while the other reasoners
still execute. This checks the failure policy without waiting for a real
deadline.

The independent semantic-product smoke is:

```bash
continuum-smoke-engines
continuum-bench engines plot
```

It checks already-running native RDFLib, Jena, RDF4J and Oxigraph services.

## Monitoring benchmarks

Run cumulative and scalability independently:

```bash
continuum-bench physical cumulative --layout sharded --ssh-user pi
continuum-bench physical scalability --layout sharded --ssh-user pi
```

Or run both with `all`:

```bash
continuum-bench physical all --layout sharded --ssh-user pi
continuum-bench physical all --layout replicated --ssh-user pi
```

`physical all` mean cumulative plus scalability only. They do
not include load, experiments, studies, unit tests or OWL validation.

## Load campaign

```bash
continuum-bench load physical
```

The campaign varies events/s, users, target triples, rules and active nodes. It
records latency percentiles, throughput, loss, inference time, alert accuracy,
CPU, memory, disk, network and recovery observations. Timeouts are recorded as
right-censored outcomes instead of blocking the suite indefinitely.

## Three separated experiments

```bash

continuum-bench experiment all physical

continuum-bench experiment scale-out physical
continuum-bench experiment reasoning-hardware physical
continuum-bench experiment distributed-ontology physical
continuum-bench experiment all physical
```

- `scale-out` evaluates replicated query service while varying workers.
- `reasoning-hardware` isolates materialization cost by node hardware.
- `distributed-ontology` evaluates authority/category fragments, local
  reasoning and federated result merge against a canonical result bag.

## Study and figures

```bash
continuum-bench study trace --target physical \
  --output-dir outputs/study/physical
continuum-bench study trace --target physical \
  --output-dir outputs/study/physical
continuum-bench study category-cost \
continuum-bench study category-cost \
  --events outputs/load/physical/event-runs.csv \
  --output-dir outputs/study/physical-cost
continuum-bench study category-cost \
  --events outputs/load/physical/event-runs.csv \
  --output-dir outputs/study/physical-cost
continuum-bench load plot
continuum-bench experiment plot all
continuum-bench experiment analyze
continuum-bench engines plot
```

Trace generation is deterministic workload preparation, not live semantic
replay. Cost analysis consumes measured event rows; it does not invent missing
resource metrics. Figures are generated as 300-DPI PNG, PDF and SVG where
supported. Experiment plotting also writes `experiment-data-quality.csv` and a
stacked coverage figure, keeping completed, censored and failed observations
visible.

The exact end-to-end command order is maintained in
[Command reference](COMMAND_REFERENCE.md).
