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
fragment requires them; distributed placement does not mean shared memory. The
retired term `sharded` is not accepted for new runs.

## Complete execution

```bash
. .venv/bin/activate
continuum-bench physical status --ssh-user pi
continuum-bench --unlimited --keep-going suite
```

The complete suite runs software checks, documentation checks, ontology
validation, physical monitoring, load tests, physical experiments, configurable
campaigns, the four policy evaluations and report generation. Use a bounded run
only when cancellation is part of the protocol:

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

Stop workers after the campaign:

```bash
continuum-bench physical stop --ssh-user pi
```

The architecture reserves structured locations and node tiers for future
mobility models. Random Waypoint, Random Walk, Manhattan/Grid and Gauss–Markov
simulation are not implemented by the four policy experiments.

See [Complete installation and test execution](COMPLETE_EXECUTION.md) for the
clean-host setup and every complete or per-family command.
