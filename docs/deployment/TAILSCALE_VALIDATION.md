# Tailscale deployment validation

For the current end-to-end launch procedure, see [Run all physical tests](../design/RUN_ALL_TESTS.md).

On 2026-09-21 the current worker code, ontology, queries, topology and pinned
Python dependencies were deployed to the four remote nodes. All five workers
were started and passed the protocol health check over their Tailscale IPs.
The native installer tools were also copied to each remote project directory.

Two physical acceptance runs used RDFS, one synthetic user, one repetition and
all 115 queries. Distributed and replicated runs completed with no timeouts or
skipped points. Distributed canonical reference validation completed. This
small acceptance check is not a statistically supported performance comparison.

Reproduce from the coordinator:

```bash
continuum-bench --config configs/smoke-vpn.toml --timeout-seconds 180 \
  physical scalability --reasoner rdfs --layout distributed
continuum-bench --config configs/smoke-vpn.toml --timeout-seconds 180 \
  physical scalability --reasoner rdfs --layout replicated
continuum-bench physical status
```

The acceptance configuration is intentionally RDFS-only. Standard monitoring
configurations select RDFS plus HermiT, Openllet, JFact and Konclude. The
dedicated distributed-reasoning configurations define a separate task-aware
matrix and must be invoked explicitly or through `suite`.

Local evidence: `outputs/validation/readiness/vpn-deploy.log`, `vpn-start.log`,
`vpn-services.json`, `vpn-smoke-distributed.log`, `vpn-smoke-replicated.log`,
and the CSV/JSON results under `outputs/validation/vpn-smoke/`.

## Native runtime installation

All four remote machines report Raspbian 12 armhf, an aarch64 kernel and
32-bit Python. The JDK compiler, Maven and Konclude were initially absent.
They have now been installed on all four targets. The installer verified native
inference and inconsistency detection for HermiT, Openllet, JFact and Konclude
on each target (16 successful backend/target checks). ELK was added later to the
isolated installer for OWL 2 EL-compatible experiments; it requires a new
deployment and target-local smoke before remote ELK measurements. No credentials are stored
in project files or installation logs.

To reproduce the package installation, run on each remote node:

```bash
sudo apt-get update
sudo apt-get install -y openjdk-17-jdk maven konclude
```

Then, from the coordinator:

```bash
continuum-bench physical deploy --with-dl-reasoners
continuum-bench physical stop
continuum-bench physical start
continuum-bench physical status
```

The deployment runs native inference self-checks on each target. Package
availability alone is not successful reasoner validation. The remote Java
maximum heap is configured to `512m`; large workloads can still exhaust it.
The installer defaults to 512 MiB on 32-bit Python and 2 GiB otherwise, and
accepts `--java-heap` or `CONTINUUM_OWL_JAVA_HEAP` overrides. Worker startup and
subsequent deployments load the target-local `.runtime/owl-reasoners.env`.
Do not copy the coordinator's classpaths or native binaries to remote devices.

Installed target versions are recorded in `outputs/validation/readiness/native-targets.json`:
Maven 3.8.7, Konclude 0.7.0 (Debian package revision
`0.7.0+1138+git20220514~dfsg-1`) and OpenJDK 17.0.20.1. Detailed installation
and native verification logs are `native-packages-*.log` and
`native-runtime-*.log` in that directory.

To check all five profiles with the small VPN workload, run each layout
sequentially:

```bash
. .runtime/owl-reasoners.env
for layout in distributed replicated; do
  continuum-bench --config configs/smoke-vpn.toml --unlimited \
    physical scalability --reasoner rdfs --reasoner hermit --reasoner openllet \
    --reasoner jfact --reasoner konclude --layout "$layout" \
    --output-dir outputs/validation/vpn-smoke/native || break
done
```

Unlimited mode does not conceal errors or remove memory limits.

The all-profile distributed acceptance run completed five points with no
timeouts or skipped points. Its `result-validation.csv` contains 575 successful
comparisons against the canonical reference (115 queries per reasoner).
Results are under `outputs/validation/vpn-smoke/native/distributed/scalability/`.
This confirms the configured query contract on this small physical workload;
it does not establish complete distributed OWL DL entailment.

The replicated run also completed all five profiles and 115 queries per profile
with no timeouts or skipped points. Together, both layouts completed 10 points
and 1,150 logical query executions. The final health check passed on all five
workers, which remain running. Machine-readable summaries are
`outputs/validation/readiness/native-acceptance.json` and `native-services.json`.

Local regression validation for the installer/checker and physical lifecycle
changes: 29 tests passed. Documentation link and generated-reference validation
passed for 29 files.

Version 0.4.0 introduced distributed fragment contract 3; version 0.4.1 keeps
that contract and corrects six-node authority routing. The HTTP envelope
uses protocol 9 so the coordinator also verifies benchmark release identity.
Deploy the current source to every node before
running `distributed-reasoning-scalability`; mixed worker revisions are rejected.

## Mist extension

The physical inventory now includes `mist` at `100.72.111.107`, between Fog and
Edge in topology order. On 2026-09-25, Tailscale ping succeeded through DERP
Madrid (43--80 ms), while SSH port 22 returned connection refused. The node is
configured but not deployment-ready. Six-node campaigns must wait until SSH,
the target-local virtual environment, reasoner runtimes and worker health have
all been verified. Earlier five-node measurements remain historical evidence
and must not be relabelled as six-node runs.

## 2026-09-27 deployment audit

Cloud, Fog and all three Edge workers run release 0.4.1, protocol 9 and the same
six-node topology fingerprint. HermiT, Openllet, JFact, ELK and native Konclude
passed inference and inconsistency smoke checks on every accessible Raspberry
Pi. Their Python environments pass dependency checks. Mist is visible in
Tailscale but rejects SSH and worker HTTP connections, so no six-node physical
benchmark was executed. A five-worker health result is operational readiness
evidence only and must not be reported as a complete six-node experiment.
