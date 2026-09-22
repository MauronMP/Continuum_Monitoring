# Physical reasoning and execution controls

For the current end-to-end launch procedure, see [Run all physical tests](RUN_ALL_TESTS.md).

See the [local validation record](PHYSICAL_REASONING_VALIDATION.md) for checked
behavior and pending physical deployment validation.

## Current comparison

The default benchmark and both physical smoke configurations select `rdfs`,
`hermit`, `openllet`, `jfact`, and `konclude`. RDFS is the RDF Schema baseline;
plain RDF storage has no inference engine. The old OWL RL and combined profiles
remain readable in historical evidence and are not the default new comparison.

The external backends execute actual installed Java/native reasoners. An absent
runtime, inconsistent ontology, invalid fragment, or invalid query answer is an
error. No backend is silently replaced by RDFS or OWL RL.

DL materialization exposes a finite named-class/individual consequence contract:
class hierarchy, equivalent classes, individual types, and same individuals,
plus the original asserted graph. It is not an enumeration of every OWL DL
entailment or a complete SPARQL entailment regime. RDFS has its own rule closure;
its lower expressivity must be considered when interpreting costs. Layout
correctness compares each backend against its own canonical graph, not against
a different reasoner's answers. Native startup, serialization and extraction
are part of adapter elapsed time; it is not pure internal inference time.

## Placement terminology

- **Replicated:** each physical worker has the complete configured input. A
  logical query is scheduled on one replica. Input and inference are repeated.
- **Distributed:** the coordinator assigns ontology fragments to physical
  nodes; each worker receives and reasons over only its assigned fragment.
  Schema dependencies and permitted projections can occur on multiple nodes.
  Source queries are routed and their answers merged under the catalogue's
  query contract, then checked against the canonical reference.

The older term *shared* described common schema with authority-partitioned
assertions. It was not shared memory. The current public placement name is
`distributed`, replacing `sharded`; it is not a third independent treatment.
The implementation distributes RDF knowledge and query execution, not an
arbitrary complete distributed OWL DL decision procedure. Missing cross-fragment
consequences must be detected by answer validation rather than assumed away.
Older `sharded` measurements are not retained in the active `outputs/` tree and
must not be relabelled as measurements of this implementation.

## Independent budgets and skipped-point triggers

The benchmark TOML supports:

```toml
[distributed]
request_timeout_seconds = 300
request_retries = 0
query_batch_size = 4
worker_timeout_margin_seconds = 2

[limits]
timeout_mode = "bounded"
phase_timeout_seconds = 300
point_timeout_seconds = 900
calibration_query_limit = 16
stop_scaling_after_timeout = true
skip_repetitions_after_timeout = false
skip_larger_sizes_after_timeout = true
skip_cumulative_stages_after_timeout = false
consecutive_timeout_threshold = 2
```

The request budget bounds transport plus remote execution. The phase budget
bounds a logical preparation/query phase; the point budget bounds the measured
point. The earliest applicable limit wins. A worker receives a shorter deadline
to return a timeout response before its request expires.

Only actual timeouts increment the skip streak. A completed point resets its
reasoner's streak; skipped rows do not count as observed timeouts. Once the
threshold is reached, enabled skip scopes latch for their relevant series.
Other reasoners remain independent. Skipped records are unobserved work, not
zero-duration successes. Invalid configuration, unavailable runtimes and other
actual errors must not be converted to timeout-triggered skips.

CLI overrides precede the subcommand:

```bash
continuum-bench --request-timeout-seconds 300 --phase-timeout-seconds 300 \
  --point-timeout-seconds 900 --skip-after-timeouts 2 \
  --no-skip-repetitions --skip-larger-points --no-skip-cumulative-stages \
  physical all --layout distributed

continuum-bench --timeout-seconds 900 --keep-going physical all --layout replicated
continuum-bench --unlimited physical all --layout distributed
continuum-bench --unlimited physical all --layout replicated
continuum-bench --unlimited --repetitions 5 suite --dry-run
```

`--keep-going` disables all skip triggers but retains deadlines. `--unlimited`
(or `limits.timeout_mode = "unlimited"`) disables benchmark deadlines and skips,
retaining nominal budgets in metadata. Actual errors still fail. No completed
result is invented when a run was interrupted. The independent skip switches
apply to cumulative/scalability monitoring; separate load/experiment family
configs retain their own documented stopping rules.

## Offline preparation, then real deployment

On the coordinator:

```bash
. .venv/bin/activate
python tools/install_owl_reasoners.py
. .runtime/owl-reasoners.env
continuum-bench physical prepare
continuum-bench topology validate --name physical
```

`physical prepare` reads local dependencies and inventory, writes
`outputs/validation/readiness/offline-readiness.json`, and never contacts the other machines.
Local file readiness is not remote runtime certification. Java, Maven and
native Konclude must match each target's operating system and architecture.
Coordinator Maven classpaths contain absolute local paths and must not be copied
to remote hosts.

After devices are powered on, verify their configured SSH addresses and routable
worker endpoints in `configs/topologies/physical/nodes/*.toml`. Supply actual
resource/location values where known; unknown geography must remain unknown.
Then run:

```bash
continuum-bench physical authorize --ssh-user pi
continuum-bench physical deploy --with-dl-reasoners --ssh-user pi
continuum-bench physical start --ssh-user pi
continuum-bench physical status --ssh-user pi
continuum-smoke-physical-cumulative --ssh-user pi
continuum-smoke-physical-scalability --ssh-user pi
```

Configure network/firewall access for the declared worker ports over the trusted
benchmark network or private tunnel. The worker API is a benchmark service, not
a public Internet endpoint. Authentication and transport encryption are not
provided by the HTTP worker itself. Distribution over distant devices does not
imply simulated network delay or verified WAN performance.

Worker protocol version 8 rejects old workers; redeploy all participating nodes.
See [deployment details](../deployment/PHYSICAL_DEPLOYMENT.md). No remote execution
is certified while those devices remain offline.

## Offline verification and resource scope

```bash
. .runtime/owl-reasoners.env
CONTINUUM_TEST_NATIVE_OWL=1 python -m pytest tests/core/test_native_reasoners.py
python tools/verify_distributed_reasoning.py
```

The second command compares all 115 logical query answers between the canonical
input and five locally evaluated fragments for every configured reasoner. It
opens no sockets and is not evidence of physical network performance.

Imported schema dependencies are assembled on the coordinator before fragment
transport. A worker reasons over its supplied graph and never resolves imports
by reading another node's data or downloading ontology documents. Dependencies
can therefore increase schema duplication compared with the old placement.

Worker CPU and RSS measurements explicitly describe the Python process.
`children_cpu_ms` reports CPU consumed by waited-for native children during
preparation. `child_peak_rss_kib_lifetime` is the lifetime high-water mark for
waited-for children, not per-point memory or a sum of concurrent process memory.
These values must not be reported as equivalent to process-tree peak memory.
