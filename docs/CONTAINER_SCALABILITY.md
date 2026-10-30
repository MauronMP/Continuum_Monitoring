# Containerized continuum scalability

## Purpose and scope

This is Battery 3, implemented in `monitoring/container_scale/`. It measures how
policy-associated query work and distributed knowledge scale on the existing
physical Cloud, Fog, Mist and three Edge inventory. Each host runs its own Docker
Compose project; Tailscale carries traffic between the published host endpoints.
A central coordinator still constructs fragments, routes queries and merges
answers. Containers do not make this architecture decentralized.

The native physical battery and strategy-comparison battery remain separate.
`continuum-bench suite` does **not** launch this battery. The proposed four-strategy
comparison is still future work and is unrelated to this new deployment module.

## Physical resources and logical participants

A participant is one container running the existing worker protocol, catalog and
reasoner adapters. Its ID is `<physical-host>-c<number>`. Host identities, layers,
authorities, categories and locations come from the maintained physical topology.
Containers inherit a host's tier; Cloud containers are never presented as physical
Edge devices. Replicating containers does not add physical RAM, CPU or links.

The default deployment includes all six hosts: Cloud, Fog, Mist and three Edge
hosts. `deployment.exclude_hosts = []` records that no host is excluded.
Missing hosts fail preflight rather than silently reducing the placement.

The initial profile uses one participant on each active host, one CPU and 1536
MiB RAM per participant. It reserves 1536 MiB available host memory and requires
4096 MiB free storage before building. The approximately 32 GB SD cards are
storage, not RAM; the Raspberry Pi inventory has approximately 8 GB RAM. Actual
available memory, disk, CPU, Docker architecture and versions are probed before
deployment. The memory budget must fit both declared capacity and live availability.

`containers_per_host = [1, 2]` enables a subsequent two-per-host placement when
budgets permit it. Ten-per-host configurations are rejected with the supplied
limits. All hosts receive the same count in this initial module; per-host counts
are not yet a separate axis. The worker image is built once per host and reused
by its participants. Log rotation is limited to two 5 MB files per container.
Swap is not an extra memory budget. No bandwidth shaping is applied.

A read-only topology mount, an unprivileged worker UID, dropped Linux capabilities
and no Docker-socket mount limit container privileges. Published ports bind to
host VPN addresses. The SSH deployment account needs Docker access, which is
host-administrative access; containers themselves do not receive it.

Containers deliberately use `restart: "no"`: a process crash must remain visible
as an experiment failure, rather than silently resetting in-memory knowledge.
After a host reboot, run `container-scale deploy` (or `--host cloud` for just
the coordinator host) before acquisition. Every `container-scale run` also
deploys and validates its workers. Native services are managed separately.

## Installation and deployment

Install coordinator Python dependencies using [Installation](INSTALLATION.md).
Install Docker Engine and the Compose plugin on every host, then verify access
from a fresh SSH session. For Debian Bookworm/Trixie and Raspberry Pi OS based on
those releases, the supplied root installation script uses Docker's Debian
package repository. Existing Docker installations are preserved; missing plugins
or broken existing installations require repair rather than destructive removal.

```bash
# On a supported host, from a clone of this repository:
sudo sh containers/worker/install-docker.sh pi
# Reconnect before checking group membership and Docker access.
docker version
docker compose version
```

Docker must actually support memory, swap, CPU quota and PID cgroup limits; the
preflight rejects a daemon that only accepts but cannot enforce those settings.
Some Raspberry Pi OS installations boot without the memory controller. Check:

```bash
docker info --format '{{json .}}'
# On a Raspberry Pi reporting false memory/swap support:
sudo python3 containers/worker/enable-memory-cgroup.py
# The helper backs up cmdline.txt and does not reboot automatically.
# Reboot at an appropriate maintenance point, then verify the flags again:
sudo reboot
```

Use your actual account instead of `pi` on the Cloud coordinator. Other operating
systems should follow the official installation procedure for that OS. The module
does not store sudo passwords. Docker operations use the local user or configured
SSH account; images are built natively on each host, without an image registry.

```bash
source .venv/bin/activate
continuum-bench container-scale doctor
continuum-bench container-scale render
continuum-bench container-scale deploy
continuum-bench container-scale status
```

`render` creates inspectable Compose JSON files (accepted by Compose), a flattened
topology and placement mapping without contacting hosts. Deployment uses ports
8491 onward, separate from native worker port 8391. It copies only project assets
needed by the image, builds sequentially and starts participants. It does not stop
native workers. Do not run competing workloads on the same hosts during acquisition.

Generated deployment files live under `outputs/container-scale/deployment/`.
Remote working directories default to `/home/pi/continuum-container-scale`;
the coordinator uses `outputs/runtime/container-scale/host/`. Neither is the native
worker installation directory. `stop` removes only this module's Compose project,
not unrelated containers, images, native workers or benchmark results.

## Explicitly unavailable hosts

The default inventory includes all six physical hosts. If a host becomes
unavailable, explicitly pass `--exclude-host` or update `deployment.exclude_hosts`.
For example, the commands below exclude Mist only for the selected invocation.
This changes the effective placement and is recorded in the experiment metadata.
Do not use these exclusions for the current complete six-host deployment.
Results from different placements must retain their participant counts.

```bash
continuum-bench container-scale doctor --exclude-host mist
continuum-bench --timeout-mode bounded --keep-going container-scale run --exclude-host mist
continuum-bench container-scale status --exclude-host mist
continuum-bench container-scale stop --exclude-host mist
```

For maintenance, repeat `--host` to target only selected hosts with `doctor`,
`deploy`, `status` or `stop`. This does not change the logical experiment topology;
`--exclude-host` does. For example, `container-scale deploy --exclude-host mist
--host fog --host edge1` updates those two hosts in the five-host placement.
The default one-container placement is intentionally conservative.

## Complete execution

```bash
# Plan all placements and scenarios without Docker or SSH operations:
continuum-bench container-scale run --dry-run

# Full battery: deployment, warm-up, acquisition and PNG report:
continuum-bench --timeout-mode bounded --keep-going container-scale run

# Select a named scenario and reduce repetitions for an engineering check:
continuum-bench --timeout-mode bounded --keep-going --repetitions 1 \
  container-scale run --scenario users-1

# Explicit optional two-per-host placement; capacity checks remain enforced:
continuum-bench --timeout-mode bounded --keep-going container-scale run \
  --containers-per-host 2

# Re-render figures from an actual returned Results directory:
continuum-bench container-scale report --input-dir outputs/container-scale/REPLACE_WITH_RUN_ID

# Stop this module's containers after acquisition:
continuum-bench container-scale stop
```

A run redeploys each placement to match the current source, then executes scenarios
sequentially. It leaves the final placement running for inspection. `--keep-going`
continues to later scenarios after workload failures, restarting stopped module
containers before the next scenario when necessary. A partial campaign returns a
nonzero exit status even when later scenarios complete. Deployment failures stop
the campaign because unprepared hosts cannot provide valid workload measurements.
The common coordinator lease prevents overlapping managed physical operations.

Default request and point budgets are 120 and 600 seconds. Change
`configs/container-scale.toml`, or use global options **before** `container-scale`:

```bash
continuum-bench --request-timeout-seconds 180 --point-timeout-seconds 900 \
  --keep-going container-scale run
```

The inherited engine's point budget bounds preparation and semantic validation;
query traffic consists of individually bounded catalog requests and can make the
whole scenario longer than one point budget. Optional `--unlimited` disables
benchmark deadlines and can block on a reasoner. SSH/build/health budgets remain
bounded independently. Increasing timeouts cannot fix memory exhaustion.

`deployment.operation_timeout_seconds` defaults to 7200 seconds per deployment
operation, allowing cold Java/Maven builds on slower VPN links. This does not
extend experiment deadlines: requests remain bounded at 120 seconds and points
at 600 seconds in the supplied configuration. A deployment timeout must be
investigated separately from a reasoning or query timeout.

## Experimental matrix

The TOML file is the source of deployment and workload parameters. The default
reasoner is RDFS; native HermiT, Openllet, JFact and Konclude use the same adapters
as the physical battery. To enable them, set `install_dl = true`, update
`experiment.reasoners`, and rebuild. This installs Java/Maven/native dependencies
and requires additional disk and memory. There is no silent RDFS fallback. Native
image builds must be validated on each architecture before claiming their results.

| Family | Configured change | Interpretation |
| --- | --- | --- |
| `users` | 10 then 50 synthetic users, fixed participant placement | Growth of users and their generated instance data; actual triples are recorded. |
| `data` | Exact target graph sizes 50,000 and 100,000, fixed users | Neutral padding adds storage/processing load; it is not new clinical evidence or new policy complexity. |
| `requests` | Concurrency 1, 2 and 4; three rounds | Each client request evaluates the full maintained query catalog. Queueing is part of request latency. |
| `strong` | Fixed total users and target triples across configured placements | Benefit or overhead of repartitioning fixed work; with only placement 1 there is no scaling slope. |
| `weak` | Users and target triples proportional to participant count | Logical participant growth on a fixed physical host set; not additional physical capacity. |

Per-container CPU and memory limits stay fixed across placements. Adding participants
therefore increases the aggregate resource allowance on the same physical hosts.
These runs measure deployment scaling under that allocation rule; they do not
isolate partitioning benefits under a fixed aggregate quota. Use separate
configurations with a constant total quota for that comparison.

A positive target must accommodate the reference graph plus generated users;
a smaller target is rejected rather than truncating semantic data. `target_triples = 0` means no padding beyond that real graph, not an empty
ontology. Report actual input size. All semantic categories and the existing 115
queries remain fixed; this module does not fabricate additional policies by
copying policy labels. Policy-category cumulative experiments remain in Battery 1.

Warm-up runs are recorded under `warmup/`, excluded from measured plots. Each
measured repetition re-prepares the graph; this is not a cache-free experiment.
Query load runs on every measured repetition. The worker handles requests serially,
so concurrent clients exercise queueing and coordination, not a claim of parallel
query execution inside one worker.

## Distributed and replicated knowledge

Distributed placement reuses authority-aware partitioning and category routing.
Active Mist and Edge participants own deterministic partitions of users and their sensitive
observations. Cloud/Fog receive their existing projections and schemas. Adding
participants changes the authority list and therefore redistributes users.
This is controlled re-preparation between points, not live migration.

Replicated placement gives every selected participant the same full logical graph.
This is global workload replication, not only tier-local replication. Compare
layouts with the same seed, users, actual graph, participants and resource limits.
Schema duplication and coordination are real costs, not removed from measured work.
The first measured repetition compares supported query projections against the
replicated reference. Keep both layouts enabled when using that validation.
No complete global OWL closure equivalence or arbitrary distributed joins are claimed.

See [Ontology distribution](ONTOLOGY_DISTRIBUTION.md) for the underlying modules,
profile imports, private data and supported query-routing rules.

## Results and figures

```text
outputs/container-scale/<run-id>/
  configuration.json                 # Effective configuration, including CLI overrides
  source-config.toml                 # Original TOML; overrides are in configuration.json
  benchmark-config.json              # Shared benchmark settings
  campaign.json                      # Incremental scenario outcomes and errors
  placement-1/
    placement.json                   # Physical hosts, participants and fingerprint
    topology.toml                    # Effective worker topology
    <host>.compose.json              # Actual Compose service specification
    context.tar.gz                   # Source/config/ontology/query image-build inputs
    preflight.json                   # Measured capacity and Docker checks
    <scenario>/
      before.json / after.json       # Docker inspection/state and boundary stats
      warmup/                        # Excluded preparatory measurements
      measured/distributed-reasoning-scalability/
        metadata.json
        results.jsonl
        distributed-reasoning-summary.csv
        node-runs.csv
        query-scalability.csv
        client-throughput.csv
        semantic-validation.csv
  figures/                           # PNG only, plus manifest.json
```

Preparation time includes communication/partitioning; reasoning time is separately
reported. Node rows contain process CPU, RSS and triples. Host figures sum
participant process measurements; they are **not** whole-host RAM/CPU measurements.
Boundary Docker stats are snapshots, not continuously sampled peaks. Peak process
RSS is a process-lifetime high-water mark, not an isolated per-request measurement.
Protocol `network_bytes` counts serialized request/response payloads; it excludes
VPN framing and is not a NIC traffic counter. Docker inspect
preserves container exit state, including `OOMKilled`, and image identity. Protocol
and semantic digests reject workers built from incompatible source/assets.

`query-scalability.csv` retains the underlying engine's worker-query execution
count. Do not compare that count as logical throughput across layouts: distributed
fan-out can execute a query on several workers. `client-throughput.csv` supplies
completed full-catalog requests per second with the same unit for both layouts.
Failed requests are excluded from latency percentiles and shown in error fractions.

Figures cover per-scenario preparation/reasoning/RSS, logical participants,
physical-host aggregation, client concurrency and completion statuses. Family
curves use actual input sizes. Points/medians are observations, not inferred missing
values. These diagnostics support paper figure selection but do not establish
significance from one engineering repetition. Read status figures alongside
completed-only costs, especially when comparing timeouts or allocation failures.

## Implementation and limitations

- `config.py`: configuration, physical capacity validation and logical topology.
- `deployment.py`: probes, Compose rendering, build/deploy/stop and Docker evidence.
- `runner.py`: workload mapping, warm-up, repetitions, checkpointing and outcomes.
- `reporting.py`: figures from saved CSVs, independent from acquisition.
- `cli.py`: the dedicated command family; no changes to the native suite membership.
- `containers/worker/Dockerfile`: multi-architecture Python base and optional DL tools.
- `containers/worker/install-docker.sh`: installation helper for supported Debian hosts.
- `containers/worker/enable-memory-cgroup.py`: backed-up Pi boot correction when memory limits are unavailable.

The underlying engine uses coordinated preparation and local inference. Container
limits do not solve 32-bit native-process address-space constraints. A 64-bit kernel
may run 64-bit container userspace even when its host userspace is 32-bit; record
and verify the actual image architecture rather than assume it. The 20 October
engineering deployment observed 64-bit Python on Cloud and 32-bit Python on all
four reachable Raspberry hosts, despite their ARM64 kernels. The current 1536 MiB
limit fits that address space; larger limits do not remove the 32-bit boundary.
The 21 October six-host validation confirmed the same 32-bit userspace on Mist.
The observed values are recorded in the audit runtime-architecture evidence.
Images use a named
base tag; preserve the recorded image IDs and build context for provenance. Exact
future rebuilds also require preserving base/dependency artifacts, not just a tag.

This initial module measures static placements and synthetic load. It does not add
physical nodes, decentralization, mobile trajectories, real-time event ingestion,
service recovery or clinical accuracy. The participant source/query identity must
be frozen during acquisition. Docker image builds and warm-up are excluded from
workload timings; deployment evidence remains available separately.

## References

Docker's [Compose services specification](https://docs.docker.com/reference/compose-file/services/)
defines CPU/memory limits, published ports, logging and health checks. Its
[Debian installation guide](https://docs.docker.com/engine/install/debian/) supplies
the package-repository procedure used by the helper.

[Fluidity](https://doi.org/10.1016/j.future.2024.03.031) motivates controlled policy
experimentation across heterogeneous continuum deployments; this module does not
reproduce its scheduler. [FogMon](https://doi.org/10.1016/j.future.2020.08.011)
motivates explicit monitoring overhead and scaling measurements; this module does
not implement its self-organizing peer-to-peer mechanisms. Compare methods under
matched workloads, not numerical results from different published hardware.

## Selecting and validating reasoners

Repeat `--reasoner` to replace the configuration's reasoner list for that command.
The order is preserved and duplicates are removed. Selecting a native backend
also enables `install_dl` in the effective configuration, without editing the
source TOML. Both the effective JSON and original TOML are archived. `rdf` is a
CLI alias for `rdfs` (RDFS entailment, not a plain RDF store).

```bash
continuum-bench container-scale run --reasoner rdfs
continuum-bench container-scale run --reasoner rdfs --reasoner jfact
continuum-bench container-scale deploy --reasoner hermit --reasoner openllet --reasoner jfact --reasoner konclude
continuum-bench container-scale validate-reasoners --reasoner rdfs --reasoner hermit --reasoner openllet --reasoner jfact --reasoner konclude
continuum-bench --timeout-mode bounded --keep-going container-scale run --reasoner rdfs --reasoner hermit --reasoner openllet --reasoner jfact --reasoner konclude
```

`validate-reasoners` operates on already deployed containers, executes as their
unprivileged user and saves `reasoner-validation.json` in the selected output
directory. It checks real DL entailment and rejection of an inconsistent fixture
for every DL backend on each selected host; RDFS checks subclass inference and
source preservation without claiming OWL consistency detection. Use it between
campaigns: it takes the physical experiment lease. It continues across backend
failures and returns a failing exit status if any check fails. This complements,
but does not replace, the campaign's own query-equivalence checks.

DL dependencies reside inside `/app/.runtime/maven` so the runtime user can read
the isolated classpaths. Java defaults to a 512 MiB heap inside the 1536 MiB
container budget; native allocations, Python and Java overhead also consume
that budget. A fixture passing does not guarantee that a large ontology fits or
finishes within a workload deadline. Cross-reasoner results must distinguish the
RDFS closure contract from the DL named-class/individual inference contract.

Local deployment commands explicitly select Docker context `default`, and the
preflight rejects a Docker Desktop daemon. The user's interactive Docker context
is not changed. Remote accounts must likewise point to their native host Engine.

### Temporary DNS failures during image construction

The local coordinator's image builds use its Linux host network
(`build.network: host`) so dependency downloads use its working resolver.
Remote builds retain their default network, avoiding additional BuildKit
entitlements on the Raspberry hosts. This setting applies only to build steps:
experiment services retain their Compose network, VPN-bound ports
and resource limits. No daemon-wide DNS changes or public resolver overrides
are required.

A build error containing `Temporary failure in name resolution` is a network/DNS
failure, even when pip subsequently reports `No matching distribution found`.
Do not change pinned package versions solely on that message. Image construction
retries this DNS failure once after ten seconds; other build failures are not
retried automatically. Each attempt's captured diagnostic is saved as
`HOST-build-attempt-N.log` alongside `HOST-build.log` in the placement directory.
Both attempts remain bounded by the deployment-operation timeout.

`--keep-going` continues experimental scenarios after recoverable acquisition
failures; it cannot run a placement whose required workers failed to deploy.
If the second build also fails, repair host/Docker DNS and rerun the command.
Completed image layers are cached. Selecting RDFS versus DL no longer invalidates
the Python dependency layer solely through the `INSTALL_DL` build argument.

## Scientific campaign synthesis

`container-scale report` also produces `global-*.png` figures and an `analysis/`
directory with `global-costs.csv`, `layout-contrasts.csv` and interpretation notes.
Start with completion/semantic-reference availability, then compare total costs,
layout cost ratios, user/data sensitivity, request concurrency and per-host CPU.
Individual scenario figures remain available as supplementary diagnostics.

Ratios use complete cohorts with available sampled query equivalence. Missing
references and timeouts are not mismatches or zero costs. Observed min–max ranges
are not confidence intervals. The total-cost plots aggregate participant CPU,
RSS and input-copy counts; they do not measure all host or coordinator resources.
Preparation payload is not VPN traffic. Distributed fragment transfer and
replicated local generation are distinct ingestion procedures and must be named
when interpreting performance. A single participant count cannot establish
strong/weak scaling, and neutral padding does not increase policy complexity.

### Expanded user workload

The maintained user axis contains **1, 50, 100, 500, 1000 and 2000** synthetic
users. Each level generates its natural ontology population (`target_triples =
0`); it is not truncated or padded to a fixed graph size. The number of users is
independent of client concurrency, which stays at one for this axis. Both layouts
use the same workload seed and user count. The default campaign has eleven
scenarios; six belong to the user axis.

User plots spanning at least two orders of magnitude use a logarithmic user axis
with explicit measured-level labels. They do not extrapolate beyond observations.
The request/point limits remain 120/600 seconds; larger levels may legitimately
reach a boundary. Missing results stay visible and are excluded from speedup
claims. More levels improve the scaling assessment but do not turn synthetic
users into real human traffic or replace independent repetitions.

### Configurable concurrent requests

Use `--concurrency 1 2 4 8` with `container-scale run` to replace the concurrency
levels of the selected scenarios. Any positive integer is supported; `N` in an
example is a placeholder, not a literal argument. Levels are sorted and
deduplicated. The default TOML is unchanged, and effective levels are archived.
Each measured repetition sweeps these levels for full-catalog requests after
preparation. Request plots retain latency, throughput and error rates per level.
This increases workload duration; it does not create extra ontology users or
containers. Values beyond physical capacity may produce queueing or timeouts,
which remain visible. The override is also supported in `run --dry-run`.

## Node costs and infrastructure response

The report includes `global-*-nodes-cpu.png`, `nodes-memory.png`,
`nodes-reasoning.png` and `nodes-knowledge.png`: one panel per physical host,
shared vertical scales, medians and observed ranges over recorded preparations.
CPU/RSS/input copies are summed across containers on a host; reasoning uses the
maximum participant duration, not the sum of parallel wall times. These are
**preparation** metrics, not resource samples at each query-concurrency level.

`global-*-users-concurrency.png` crosses every attempted user count with the
configured concurrent catalog requests and shows latency, throughput and error
fraction. Failed scenarios without measured CSVs remain visible as NA.
`global-*-infrastructure-health.png` uses Docker health snapshots recorded after
each scenario. An unhealthy probe can reflect a busy sequential worker and is
not proof of a crashed machine or an OOM. Snapshots do not measure recovery time
or continuous CPU utilization. Exact aggregated data is exported to
`analysis/node-resources.csv` and `analysis/infrastructure-health.csv`.

Workers currently process HTTP operations sequentially. Concurrent clients
therefore exercise queuing and distribution across hosts, not simultaneous
reasoning inside one worker. In distributed mode each client may contact several
workers; in replicated mode catalog requests are assigned across replicas.
Historical query rows retain error counts but may lack error messages. New runs
include `error_details`, save preparation/query checkpoints after each matrix
point, and save `failure.log` if a scenario fails. Before measured acquisition,
workers must pass a bounded readiness wait following warm-up.

`global-*-failure-diagnosis.png` separates measured catalog request errors by recorded cause and shows completed/recorded preparations for warm-up and measurement. Its source tables are `analysis/query-errors.csv` and `analysis/phase-evidence.csv`. Missing phases are labelled as unavailable, never counted as successful or zero-cost measurements. An entirely unsuccessful preparation matrix still archives its failures and metadata; node/statistics tables are omitted when no samples exist.

## Optional recovery supervisor

The separate [adaptive monitoring module](ADAPTIVE_MONITORING.md) consumes this campaign evidence and can rebuild a failed logical service on an eligible host. Baseline commands remain unchanged; adaptation outcomes are stored separately and must not be merged into unadapted scalability curves.

### Request coverage

The default scenarios now use 18 query rounds. Each repetition issues
`query_rounds × concurrency` catalogue requests for each layout. Baseline routing
advances between rounds, so low concurrency does not repeatedly select only the
first hosts. This increases execution time and is an intentional workload change;
do not compare these totals directly with historical one-round campaigns.
