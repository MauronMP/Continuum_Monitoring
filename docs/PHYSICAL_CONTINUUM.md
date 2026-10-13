# Physical Continuum

## Inventory

The physical manifest contains six configured hosts:

| Tier | Node | Tailscale address | Device |
| --- | --- | --- | --- |
| Cloud | `cloud` | `100.86.63.53` | x86_64 coordinator |
| Fog | `fog` | `100.93.73.27` | Raspberry Pi 500 |
| Mist | `mist` | `100.72.111.107` | Raspberry Pi 500 |
| Edge | `edge1` | `100.101.178.35` | Raspberry Pi 500 |
| Edge | `edge2` | `100.70.9.117` | Raspberry Pi 500 |
| Edge | `edge3` | `100.121.135.60` | Raspberry Pi 500 |

Addresses, ports, CPU, RAM, storage, processing capacity, network capacity and
region are declared in `configs/topologies/physical/nodes/`. Runtime health and
resource use are measured separately and do not overwrite static capacity.

## Placement modes

`replicated` sends a complete input graph to every active worker. `distributed`
assigns authority-aware ontology and data fragments to workers and merges source
query results at the coordinator. Shared schema triples may be repeated where a
fragment requires them; distributed placement does not mean shared memory.
Only these two explicit layout names are accepted for new runs.

## Complete execution

```bash
. .venv/bin/activate
continuum-bench physical status --ssh-user pi
continuum-bench --timeout-mode bounded --keep-going suite
```

The complete suite runs software checks, documentation checks, ontology
validation, physical monitoring, load tests, physical experiments, configurable
campaigns, the four policy evaluations and report generation. Bounded execution
is recommended because it preserves the complete outcome matrix without giving
a native reasoner unlimited control of a worker:

```bash
continuum-bench \
  --timeout-mode bounded \
  --request-timeout-seconds 300 \
  --phase-timeout-seconds 600 \
  --point-timeout-seconds 1800 \
  --skip-after-timeouts 2 \
  --no-skip-repetitions \
  --no-skip-larger-points \
  --no-skip-cumulative-stages \
  --keep-going \
  suite
```

The defaults are in `configs/benchmark.toml`: worker request limits are in
`[distributed]`; phase, point and skip behavior are in `[limits]`. The dedicated
load and physical experiment files contain family-specific sizes and repetitions.

`--keep-going` allows independent work to continue after a recorded timeout or
failure. Without it, non-timeout runtime, ontology and programming errors remain
fail-fast inside the current command.

`--unlimited` is an optional diagnostic mode. It disables coordinator, socket,
worker and native-process deadlines. A slow worker remains active for as long as
the backend needs, but `--keep-going` cannot start another point until that call
returns. Native DL reasoners can therefore consume a worker for hours or remain
blocked indefinitely. Use unlimited mode only with a reduced, supervised
profile; do not use it as the default complete-suite command.

On 30 September 2026, an unlimited replicated HermiT point with 2,500 users
demonstrated this risk: the coordinator remained at point 64/90, five Raspberry
Pi workers stayed inside Java materialization for more than ten hours, and their
health endpoints could not respond. See
[Observed failures and remediation](OBSERVED_FAILURES.md).

The worker HTTP service is deliberately single-threaded because bounded native
reasoning uses a main-thread Unix timer. While a worker handles a long request,
its `/health` endpoint cannot answer. A health timeout during an active native
process therefore means `busy or blocked`, not necessarily `offline`; confirm
the worker and child-process state through SSH. A separate liveness control
plane remains future work.

Do not suspend a physical campaign with `Ctrl+Z`. Current commands ignore the
suspend signal while they hold the physical lease and print a warning; use
`Ctrl+C` for a controlled interruption. A command started from older source may
still be suspended by the shell and must be recovered manually before another
campaign can acquire the lease.

The Raspberry Pi workers currently run a 32-bit user space, and their native
Konclude build is also 32-bit. The replicated 5,000-user graph contains about
359,000 asserted triples. Konclude has reached `std::bad_alloc` on that point,
despite host RAM remaining available, because one 32-bit process cannot address
all physical memory. This is a measured replicated-layout capacity boundary.
The distributed layout completed the physical timing at the corresponding
scale because each node materializes only its assigned fragment. That timing is
not sufficient to claim semantic equivalence: the 5,000-user canonical
Konclude reference timed out, and lower Konclude scales produced recorded query
mismatches. Those rows remain available as `unvalidated_results` or
`invalid_results`, but reports exclude them from performance comparisons. The
replicated `failed` point still records the 32-bit resource ceiling, and later
reasoners and families continue under `--keep-going`.

Stop workers after the campaign:

```bash
continuum-bench physical stop --ssh-user pi
```

The stop operation also removes project-owned native Java materializers left
after an interrupted worker. Current workers translate `SIGTERM` into a
controlled interruption so their isolated Java or Konclude process group is
terminated before the HTTP service exits.

After any source change, deploy again before restarting the workers. New result
metadata records the exact source-build identifier and topology fingerprint;
reports reject absent or different values instead of mixing experiments from
different code or placement definitions.

The architecture reserves structured locations and node tiers for future
mobility models. Random Waypoint, Random Walk, Manhattan/Grid and Gauss–Markov
simulation are not implemented by the four policy experiments.

See [Complete installation and test execution](COMPLETE_EXECUTION.md) for the
clean-host setup and every complete or per-family command.


## Native IRI preservation and worker ownership

The Konclude bridge expands relative and abbreviated OWL/XML IRIs using the
original base and Prefix declarations before moving axioms into OWLlink. Losing
that context changes entity identity; a consistent output alone would not detect
the error. Canonical-versus-fragment checks compare query counts, ASK values and
result digests, including the formerly failing serialization seed.

Worker stop/restart targets only processes descended from the verified managed
worker. Independent native tests using the same checkout are not worker children.
Unattributed orphans require explicit inspection. For current five-node deployment
commands and evidence, see [Audit remediation](REMEDIATION.md).

## Semantic input compatibility

Worker protocol 10 compares a content digest of ontology modules, shapes, role
profiles, placement, query catalog, query text and execution plan. Identical
version labels cannot hide stale files. Synchronize and restart all participating
workers after semantic edits, including comment-only changes. Preparation rejects
files modified after worker startup. The HTTP health response exposes
`semantic_assets_digest` and `semantic_assets_error`; use `physical status` to
identify a mismatched deployment. Do not modify inputs during a campaign.

## VPN lifecycle probe budgets

Worker deployment and readiness have finite connectivity budgets separate from
benchmark request, phase and point limits. The default SSH precheck budget is
60 seconds; the default HTTP health budget is 10 seconds. For a slow VPN relay:

```bash
export CONTINUUM_SSH_PROBE_TIMEOUT_SECONDS=120
export CONTINUUM_HEALTH_TIMEOUT_SECONDS=30
continuum-bench physical deploy --ssh-user pi &&
continuum-bench physical start --ssh-user pi &&
continuum-bench physical status --ssh-user pi
```

Both environment variables accept finite values from 1 to 600 seconds. The health
budget applies to lifecycle status and benchmark discovery. SSH transport still
has its own connection and keepalive limits; increasing the probe budget does not
repair an unavailable peer. The SSH budget covers authentication and prerequisite
probes, not arbitrary remote deployment commands. A timed-out prerequisite probe
cannot establish that dependencies are missing, and an SSH timeout is not proof
of rejected credentials. Explicit permission-denied errors require checking SSH
authorization. `--unlimited` does not disable these connectivity checks.

Keep these exports in the coordinator shell when starting a suite. Confirm all
workers are healthy before launching it. A source-code change, including report
code, changes the package fingerprint and requires synchronization and restart.
