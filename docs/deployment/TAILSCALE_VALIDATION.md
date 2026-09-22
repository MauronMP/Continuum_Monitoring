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

The acceptance configuration is intentionally RDFS-only. The main comparison
and original smoke configurations still select all five reasoners.

Local evidence: `outputs/validation/readiness/vpn-deploy.log`, `vpn-start.log`,
`vpn-services.json`, `vpn-smoke-distributed.log`, `vpn-smoke-replicated.log`,
and the CSV/JSON results under `outputs/validation/vpn-smoke/`.

## Native runtime installation

All four remote machines report Raspbian 12 armhf, an aarch64 kernel and
32-bit Python. The JDK compiler, Maven and Konclude were initially absent.
They have now been installed on all four targets. The installer verified native
inference and inconsistency detection for HermiT, Openllet, JFact and Konclude
on each target (16 successful backend/target checks). No credentials are stored
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
