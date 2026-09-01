# Elastic physical-continuum benchmark

## Default topology

The root catalog loads `configs/topologies/physical/topology.toml`, which
composes one file per tier from `configs/topologies/physical/nodes/`.

The initial example is:

| Node | Tier | Host | Endpoint |
|---|---|---|---|
| `cloud` | cloud | coordinator | `http://127.0.0.1:8391` |
| `fog` | fog | Raspberry Pi | `http://192.168.1.137:8391` |
| `edge1` | edge | Raspberry Pi | `http://192.168.1.138:8391` |
| `edge2` | edge | Raspberry Pi | `http://192.168.1.139:8391` |
| `edge3` | edge | Raspberry Pi | `http://192.168.1.140:8391` |

Edit the corresponding tier file when a host, address, port or tier differs.
Any positive number of cloud, fog, mist, edge and IoT nodes is supported,
subject to topology validation. The old `configs/physical-nodes.toml` is a
legacy reproduction format only.

## Coordinator prerequisites

The coordinator needs the normal project environment plus OpenSSH client and
`rsync`:

```bash
python3 tools/doctor.py --physical
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench topology show --name physical
```

## Remote worker prerequisites

On each Raspberry Pi or Linux worker:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv openssh-server rsync procps
python3 --version
sudo systemctl enable --now ssh
```

Python must be 3.11 or newer. Give every host a stable address and allow the
configured worker port from the coordinator.

Lightweight workers do not need Docker, Java, Maven, Matplotlib, NumPy,
PyOxigraph or Protégé. Deployment installs only the portable packages pinned in
`requirements-node.txt`.

Raspberry Pi 500 hardware uses a 64-bit CPU but may run a 32-bit userland. Such
workers can execute RDFLib RDFS/OWL-RL profiles. Do not label Jena, RDF4J or
Oxigraph as physical-node engines unless the operating system, Java runtime and
images have actually been migrated and validated for that platform.

## SSH authentication

Create a coordinator key if none exists:

```bash
ssh-keygen -t ed25519
```

Install it on every unique remote host:

```bash
.venv/bin/continuum-bench physical authorize --ssh-user pi
```

This command may ask for each remote password once through `ssh-copy-id`.
Passwords are never stored in TOML, environment files or source code. All
subsequent lifecycle commands use `BatchMode=yes` and fail rather than wait for
an interactive password.

Verify manually if needed:

```bash
ssh -o BatchMode=yes pi@192.168.1.137 true
ssh -o BatchMode=yes pi@192.168.1.138 true
ssh -o BatchMode=yes pi@192.168.1.139 true
ssh -o BatchMode=yes pi@192.168.1.140 true
```

## Deployment

```bash
.venv/bin/continuum-bench physical deploy --ssh-user pi
```

Deployment performs these steps:

1. validates key authentication and remote Python/venv/rsync/procps before
   copying any host;
2. mirrors only release-owned `src`, `configs`, `ontology` and `queries`;
3. copies `requirements-node.txt`;
4. creates or updates `.venv-node` under the dedicated remote directory;
5. installs pinned portable dependencies;
6. flattens the selected composed topology into
   `runtime/active-topology.toml` and copies the same fingerprinted snapshot to
   every worker.

`rsync --delete` is restricted to release-owned subdirectories. It does not
delete the virtual environment, runtime logs, results or parent directory.
Broad remote directories such as `/`, `/root`, `/tmp` or `/home/pi` are
rejected.

## Start, health and stop

```bash
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi
.venv/bin/continuum-bench physical stop --ssh-user pi
```

PID and log files are separated by node ID. Start replaces a stale worker only
when its expected identity/fingerprint contract fails. Stop matches executable,
node ID and port, allowing recovery from stale PID files without killing
unrelated processes.

Health requires the correct service, protocol, ontology version/revision,
reasoning contract, query count, node identity, tier and topology fingerprint.

## Smoke tests

Start the workers first, then run sharded smokes:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  physical cumulative \
  --layout sharded \
  --ssh-user pi \
  --output-dir outputs/physical-smoke-cumulative

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  physical scalability \
  --layout sharded \
  --ssh-user pi \
  --output-dir outputs/physical-smoke-scalability
```

Replicated smokes:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  physical cumulative \
  --layout replicated \
  --ssh-user pi \
  --output-dir outputs/physical-smoke-cumulative-replicated

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  physical scalability \
  --layout replicated \
  --ssh-user pi \
  --output-dir outputs/physical-smoke-scalability-replicated
```

## Full benchmark layouts

Authority-partitioned ontology:

```bash
.venv/bin/continuum-bench physical cumulative \
  --layout sharded --ssh-user pi
.venv/bin/continuum-bench physical scalability \
  --layout sharded --ssh-user pi
.venv/bin/continuum-bench physical all \
  --layout sharded --ssh-user pi
```

Complete replica per active node:

```bash
.venv/bin/continuum-bench physical cumulative \
  --layout replicated --ssh-user pi
.venv/bin/continuum-bench physical scalability \
  --layout replicated --ssh-user pi
.venv/bin/continuum-bench physical all \
  --layout replicated --ssh-user pi
```

`sharded physical ...` remains a compatible endpoint-only alias after workers
are already running:

```bash
.venv/bin/continuum-bench sharded physical all \
  --topology-name physical \
  --output-dir outputs/sharded-physical
```

## Adaptive replicated scheduling

The replicated physical coordinator calibrates query cost on the available
hardware and uses longest-processing-time scheduling. It does not assume that
the coordinator and Raspberry Pi workers have equal capacity.

Primary distributed latency is wall time. The sum of node work is a resource
cost. Waiting for the slowest preparation is expected because all replicas must
be ready before the measured query phase.

## Load and separated experiments

```bash
.venv/bin/continuum-bench load physical

.venv/bin/continuum-bench experiment scale-out physical
.venv/bin/continuum-bench experiment reasoning-hardware physical
.venv/bin/continuum-bench experiment distributed-ontology physical
.venv/bin/continuum-bench experiment all physical
```

The hardware experiment evaluates each endpoint independently. Scale-out uses
replicas. Distributed ontology uses authority placement and a monolithic oracle.
Do not merge these interpretations.

## Experimental controls

For publishable measurements:

- use wired Ethernet;
- synchronize clocks, even though latency is measured by the coordinator;
- fix Raspberry Pi power mode, CPU governor and cooling;
- record OS version and 32/64-bit userland;
- avoid SSH terminal sessions and unrelated workload;
- keep topology, reasoners, seeds, timeouts and query catalog identical;
- randomize or counterbalance architecture run order;
- preserve failures, resets and timeouts.

## Connection-reset diagnosis

An SSH message such as `Connection reset by peer` does not prove that the HTTP
worker stopped. Check separately:

```bash
ping 192.168.1.139
ssh -o ServerAliveInterval=15 -o ServerAliveCountMax=3 \
  pi@192.168.1.139
curl --fail http://192.168.1.139:8391/health
```

On the Raspberry Pi inspect:

```bash
free -h
df -h
uptime
vcgencmd get_throttled 2>/dev/null || true
tail -n 100 /home/pi/continuum-bench/runtime/edge2.log
```

Common causes are Wi-Fi instability, power/thermal throttling, out-of-memory,
stale workers, wrong addresses and firewall rules. Redeploy after code,
ontology, query, protocol or topology changes:

```bash
.venv/bin/continuum-bench physical stop --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi
```

## Interpretation limits

- Five physical nodes do not necessarily outperform a modern coordinator.
- Raspberry Pi materialization can dominate a barrier-based replicated run.
- Sharding reduces per-authority data but adds transport and merge overhead.
- Network and serialization cost must be reported, not hidden.
- The lightweight physical suite compares Python reasoning profiles only.
- Results from a 32-bit worker are not interchangeable with 64-bit container
  product results.
