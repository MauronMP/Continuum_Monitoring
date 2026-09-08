# Modular physical monitoring

All benchmark execution targets physical HTTP workers in the continuum.
Canonical graph computations on the coordinator only validate result semantics;
they are excluded from benchmark performance measurements.

## Repository structure

```text
configs/
  topologies/physical/       Physical inventory and per-tier resources
  campaign-smoke.toml        Ten-axis acceptance campaign
  campaign.toml              Repeated configurable campaign
  benchmark.toml             Canonical ontology monitoring
  load-benchmark.toml        Event-load and saturation profiles
  owl-reasoners.toml         Native OWL validation adapters
src/continuum_bench/
  core/                     Reusable domain entities and ports
  monitoring/
    campaign_config.py      Validated experiment definitions
    campaign.py             Infrastructure-independent orchestration
    campaign_infrastructure.py  HTTP adapter and infrastructure port
    campaign_runtime.py     Worker execution through reasoner/metric ports
    workloads.py            Deterministic synthetic policy workloads
    metrics.py              Process CPU, memory and elapsed-time collector
    campaign_results.py     Versioned structured evidence sink
    provenance.py           Source snapshot and dependency evidence
    normalize.py            Canonical envelope for retained scientific suites
    distributed.py          HTTP transport and common distributed execution
    physical.py             Calibrated replica execution
    sharded.py              Authority-aware canonical ontology execution
    load_benchmark.py       Event-pressure and recovery measurements
    experiments.py          Scale-out, hardware and distributed ontology
    study/                  Real-query policy attribution and static trace tools
    *_reporting.py          Optional analysis and figures
  topology.py               TOML adapter to physical domain nodes
  node.py                   Physical worker HTTP boundary
  physical_cluster.py       SSH deployment and managed process lifecycle
  ontology.py               Semantic asset loading
  queries.py                Canonical SPARQL catalog and result contracts
  reasoners.py              Registered materialization backends
  owl_validation.py         External consistency validation
  cli.py                    Composition root
ontology/                   Schema, policies, requirements, SHACL and examples
queries/                    English canonical 115-query catalog and sources
tests/{core,infrastructure,monitoring,integration,reporting}/
tools/                      Bootstrap, native reasoners and documentation checks
docs/                       Installation, architecture and scientific contracts
outputs/                    Ignored machine-local evidence
```

Old imports such as `continuum_bench.load_benchmark` are small compatibility
aliases to `monitoring`. They contain no experiment implementation. The core has
no imports from monitoring, HTTP, plotting or a concrete reasoning library.

## Domain and ports

`PhysicalContinuum` contains `PhysicalContinuumNode` values. Each node separates
identity, tier, device type, host and endpoint from `NodeCapacity`,
`GeographicPosition` and sampled `NodeDynamicState`. Capacity describes CPU count
and architecture, RAM, storage, processing capacity and network bandwidth.
Position uses optional latitude/longitude, altitude and region. Unknown
coordinates are omitted rather than fabricated as latitude 0, longitude 0.
`TopologyNode.to_domain()` adapts deployment configuration to this shared model.

`Ontology`, `Policy`, `Requirement`, `Query` and `ReasonerConfiguration` describe
shared semantic concepts. `Reasoner`, `MetricCollector`, `ResultSink` and
`MobilityModel` are structural protocols. Tests inject implementations of these
ports. Adding a backend with `register_reasoner()` does not require an experiment
branch or modification to the core.

Only static mobility is implemented. Random Waypoint, Random Walk,
Manhattan/Grid and Gauss-Markov are future plugins registered through the mobility
factory. Selecting an unregistered model fails explicitly. Geographic domain
positions and local Cartesian trace coordinates remain distinct concepts.

## Experiment configuration

`campaign-smoke.toml` and `campaign.toml` define reasoners, repetitions, warm-up
requests, random seed, request and point deadlines, placement modes, categories,
a baseline workload and strictly increasing axes. A point changes exactly one
axis, leaving all other baseline values fixed:

- physical worker count;
- synthetic IoT devices, users, ontology individuals and requirements;
- synthetic policies, request count, query count and query join complexity;
- actual concurrent HTTP request count.

Node count cannot exceed the physical inventory. The supplied smoke contains
21 workload points, three reasoners and two layouts: 126 measurements.
Synthetic IoT entities are not additional connected hardware devices. The
microbenchmark schema and generated policies are explicitly synthetic. Use the
canonical load and study commands to measure the project's real policy catalog.

`replicated` prepares the same graph on every selected worker and routes each
request to one replica. `distributed` partitions entities and their join paths
across workers while sharing schema. `shared` is an explicit alias for this
shared-schema distributed-data treatment, not a third independent architecture.
Each logical result is compared as a complete bag with an independently
materialized native reference. Warm-up requests are excluded from measured query
throughput. Reference computation has a separate bounded budget.

Concurrency is pressure from the coordinator. Each current worker serializes
its reasoning/query operations; increasing client concurrency does not claim
parallel inference inside a Python worker. Distributed fan-out is sequential
within each logical request. These properties are part of the measured design.

## Reasoning abstraction

The materialization port accepts a graph and returns a graph, elapsed reasoning
time, asserted triples and output triples. Built-in physical backends are RDFS,
OWL RL and combined RDFS/OWL RL. They share one registry and contract.

HermiT, Openllet, JFact and native Konclude are evaluated by the separate OWL 2 DL
consistency port. The installed worker profile runs 32-bit Python on Raspberry Pi
OS and has only RDFLib/OWL-RL dependencies. These four external tools require a
Java or native runtime, have a different DL consistency task and do not currently
implement the worker's materialized-SPARQL-graph port. They are therefore not
silently treated as interchangeable timed workers. RDFS/OWL RL are the explicit
physical alternatives, with lower logical expressiveness recorded in the catalog.
All four external tools remain mandatory in the strict release validation gate.

JFact's Guice and AssistedInject dependencies are pinned together to 5.1.0.
An explicit Protégé selection takes precedence over an ambient HermiT classpath.
Konclude receives native OWL/XML converted from the canonical Turtle ontology.

## Results and policy cost

Every new campaign creates a unique directory. `manifest.json` records the exact
configuration and environment; `provenance.json` records dependency versions,
source hashes and the Git base commit. `source.tar.gz` contains the executed
source/assets and installation specifications. `campaign.toml` preserves the
input file; the manifest configuration is authoritative when CLI axis filters
were used.

`results.jsonl` and `results.csv` use `continuum.monitoring.v1` and retain a common
envelope: configuration ID, execution ID, configuration, infrastructure,
reasoner, measurements and final status. Campaign records also expose workload,
axis, placement, seed, repetition, request deadlines, node configuration and
observed hardware, graph sizes, reference time, reasoning and query time,
latency percentiles, throughput, process CPU, RSS and request validation.
Time units are milliseconds, memory is MiB, throughput is requests/second and
CPU percentages use one core as 100%. RSS is a process snapshot, not an energy
measurement or a precisely sampled high-water mark. Missing metrics remain null.

Canonical cumulative/scalability/load/experiment commands retain their existing
scientific CSVs and now add the same versioned JSONL envelope for newly written
summaries. Historical results are not relabelled or rewritten. Plot modules are
separate consumers; generating structured evidence does not require plotting.

Real-query cost attribution is in `monitoring/study/analysis.py`: it groups load
observations by actual category, policy and query structural complexity. Batch
CPU and transport costs are attributed by measured query duration; a query linked
to N policies contributes 1/N to each. Memory observations are not summed.
The new synthetic campaign additionally records per-request categories, policy
IDs, CPU, RSS, latency and query execution time for controlled complexity sweeps.

## Testing boundaries

`tests/core` checks domain invariants, semantics and result equivalence.
`tests/infrastructure` checks topology round trips, HTTP adapters and SSH/process
ownership. `tests/monitoring` injects in-memory infrastructure to test workloads,
concurrency, loss, timeouts, isolation and reproducibility. `tests/integration`
contains optional installed OWL checks. `tests/reporting` validates result
consumers, diagrams and documentation. Normal pytest runs do not operate the
physical cluster. Physical smokes are explicit CLI commands.

The coordinator takes a nonblocking exclusive file lease before physical
campaigns and lifecycle changes. A conflicting invocation fails before changing
worker state. This lease coordinates processes on one host; a second coordinator
host needs external scheduling. Worker campaign tokens additionally reject
queries against another execution's prepared state.

## Installation and reproduction

On an Ubuntu/Debian coordinator:

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip openssh-client rsync openjdk-17-jre-headless maven konclude
git clone https://github.com/MauronMP/Continuum_Monitoring.git
cd Continuum_Monitoring
python3 tools/bootstrap.py --profile coordinator
. .venv/bin/activate
python tools/install_owl_reasoners.py
python -m pytest
python tools/check_documentation.py
continuum-bench validate
continuum-bench preflight
continuum-bench owl-validate --require-all
continuum-bench campaign --validate-only
```

The clone must contain the version being evaluated; local uncommitted audit
changes are not available from the remote until published. Preserve the source
snapshot for reproducing these exact changes.

On each physical Debian/Raspberry Pi OS worker, install Python 3.11+,
`python3-venv`, `python3-pip`, `openssh-server`, `rsync` and `procps`, then enable
SSH. Edit the physical inventory for your network and hardware. From the
coordinator:

```bash
continuum-bench physical authorize --ssh-user pi
continuum-bench physical deploy --ssh-user pi
continuum-bench physical start --ssh-user pi
continuum-bench physical status --ssh-user pi
continuum-bench campaign
continuum-bench campaign --campaign-config configs/campaign.toml
continuum-bench campaign --axis physical_nodes --axis concurrency
continuum-smoke-physical-scalability
continuum-smoke-physical-scalability --layout replicated
continuum-smoke-physical-load
continuum-bench physical all --layout sharded
continuum-bench physical all --layout replicated
continuum-bench load physical
continuum-bench experiment all physical
continuum-bench study category-cost --events outputs/load/physical/event-runs.csv
continuum-bench physical stop --ssh-user pi
```

Run physical commands sequentially. Smoke acceptance rejects incomplete or
invalid results. Saturation campaigns may legitimately contain censored timeouts
and lost requests; those are measurements, not successful smoke acceptance.
Larger full-campaign configurations require calibration to the real hardware.
