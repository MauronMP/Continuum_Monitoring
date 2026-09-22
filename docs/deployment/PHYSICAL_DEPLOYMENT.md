# Offline physical deployment preparation

For the current end-to-end launch procedure, see [Run all physical tests](../design/RUN_ALL_TESTS.md).

For the subsequent online deployment and outstanding native dependencies, see
[Tailscale validation](TAILSCALE_VALIDATION.md).

Run `python tools/prepare_physical_deployment.py` from the coordinator. This
writes `outputs/validation/readiness/offline-readiness.json`. It reads local files and the
inventory only: no SSH, DNS lookup, HTTP health check, installation, or worker
startup. Exit 1 means a local prerequisite/file is missing; the report is still
written. Exit 0 means local presence checks passed, not that devices can run.
The report always keeps `deployment_ready=false` until a separate online
validation occurs. Executable presence does not verify JVM versions or ABI.

The current Tailscale inventory declares cloud at 100.86.63.53 (x86_64), fog at
100.93.73.27, and edge1/edge2/edge3 at 100.101.178.35, 100.70.9.117,
100.121.135.60 (armv7l-32bit). These are configuration declarations, not fresh
hardware measurements. Use the Tailscale addresses for SSH and worker HTTP;
the direct LAN addresses printed by `tailscale ping` are transport details,
not inventory endpoints. Cloud remains `local = true` for process management,
but advertises its VPN address so remote nodes can reach it.

On 2026-09-21, all four remote nodes answered Tailscale ping and authenticated
SSH as `pi`. Each reported an aarch64 kernel and 32-bit Python. Java was found
on PATH; Maven and Konclude were not. All five HTTP endpoints refused port
8391 connections, so no worker was certified ready. These are point-in-time
observations, not throughput measurements. Local diagnostic evidence is in
`outputs/validation/readiness/tailscale-check.json`. No remote service was changed.

Regions `local-lab` and `physical-lab` are legacy inventory labels, not verified
geographic locations after the VPN migration. They come directly
from inventory. Coordinates remain null. Do not derive geography from IPs or
replace missing coordinates with fabricated values. Future placement should
update the node inventory with verified address, CPU/OS/ABI, RAM, bandwidth,
and location observations before selecting a target. Unknown compatibility is
not eligibility for DL execution.

## Offline CLI and library API

The integrated command is:

```bash
continuum-bench physical prepare
```

It writes `outputs/validation/readiness/offline-readiness.json` without contacting any worker.

`offline_preflight(root: Path, inventory: PhysicalInventory) -> dict` returns
JSON-serializable checks and placement declarations.
`write_offline_manifest(root, inventory, output: Path) -> dict` also writes it.
Load the inventory using `load_physical_inventory(path, ssh_user=...,
topology_name=...)`. The offline command uses these functions directly rather
than invoking lifecycle or status operations.
The standalone script supports `--inventory`, `--topology-name`, `--ssh-user`,
`--root`, and `--output`.

## DL runtime handoff and future online installation

`deploy_cluster(root, inventory, with_dl_reasoners=True)` is an **online**
operation for later explicit use. It copies tools alongside worker assets,
installs worker dependencies, then invokes the target's configured Python with
`tools/install_owl_reasoners.py`. The default remains the existing lightweight
worker deployment. Neither mode starts workers. The offline preparation does
not call either mode.

The reasoner installer owns these paths:

- `.runtime/owl-validation-{hermit,openllet,jfact}.classpath`
- `.runtime/owl-validation.classpath` for OWLAPI conversion
- `.runtime/owl-reasoners.env`
- `tools/owl/` Java sources, pinned Maven POM, adapter and smoke ontology

Generate runtime files on each target. Maven classpaths contain absolute
host-local paths; copying the coordinator's `.runtime`, Maven cache paths,
virtualenv or x86 binaries to ARM is invalid. The installer resolves the pinned
Java dependencies and performs actual reasoner smoke tests. Remote installation
needs dependency repository access or a separately prepared target-compatible
cache; this preparation is not an air-gapped package bundle.

Before online deployment, provision Python >=3.11 with venv/ensurepip, rsync,
procps, Java 17 and Maven on each target. JAR portability does not establish
JVM availability, heap sufficiency or native ABI compatibility on 32-bit ARM.
Native Konclude must be installed for the target OS/CPU/ABI and discoverable as
`Konclude` on PATH (or explicitly configured using
`CONTINUUM_KONCLUDE_EXECUTABLE`). No supported ARM binary is assumed. If it
cannot run, mark Konclude unavailable and leave its placement blocked. Never
substitute OWL-RL, another Java reasoner, or a successful help command.
Deployment deliberately does not pass `--skip-konclude`; installer failure
propagates instead of claiming a complete DL runtime. Runtime installation is
not atomic across hosts: a later failure can leave earlier hosts installed.

For custom executable paths, ensure the worker launch environment receives the
installer-generated environment (or provision the binary on PATH). Inspect
`.runtime/owl-reasoners.env` on that same host before sourcing it. Validate each
backend there before starting workers or admitting DL workloads. Hardware
measurements, reachability, target installation and runtime validation remain
pending while the devices are offline.
