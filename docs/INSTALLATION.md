# Installation from a clean environment

This guide installs and configures the coordinator and six-node physical
continuum. It does not run experimental batteries. Continue with
[Experiments](EXPERIMENTS.md) for their purpose and
[Complete execution](COMPLETE_EXECUTION.md) for acquisition commands.

## 1. Operating system and dependencies

Use a Debian/Ubuntu-family Linux host with Python >=3.11. The coordinator requires
64-bit Python. A 64-bit Raspberry Pi OS is preferred for new worker installations;
the existing 32-bit worker userspace has an address-space limit even on a 64-bit
kernel. Do not upgrade an operating system during a campaign.

On the coordinator and each worker:

```bash
sudo apt-get update
sudo apt-get install -y curl ca-certificates git python3 python3-venv python3-pip openssh-client openssh-server rsync procps openjdk-17-jdk maven konclude
sudo systemctl enable --now ssh
python3 --version
java -version
mvn -version
command -v Konclude || command -v konclude
```

Package availability depends on the distribution/CPU. Use a distribution that
provides native Konclude, or install an architecture-compatible build before
continuing. Copying a binary from another architecture is not supported.
Java backends are installed later from the project's pinned Maven profiles.
No containers are used.

## 2. Tailscale and SSH

Install Tailscale using the [official Linux installer](https://tailscale.com/download/linux)
and join every host to the same authorized tailnet. Skip the first two commands
when Tailscale is already installed:

```bash
curl -fsSL https://tailscale.com/install.sh -o /tmp/tailscale-install.sh
sudo sh /tmp/tailscale-install.sh
sudo tailscale up
tailscale status
```

Authorize the device in the same tailnet. Confirm reachability of SSH (22) and
the worker endpoint (8391) over the VPN. Firewall and tailnet ACLs must allow the
coordinator to contact those services. Never commit credentials or private keys.

## 3. Clone and install the coordinator

```bash
git clone https://github.com/MauronMP/Continuum_Monitoring.git
cd Continuum_Monitoring
python3 tools/bootstrap.py --profile coordinator
source .venv/bin/activate
python tools/install_owl_reasoners.py
continuum-bench doctor --physical --owl
```

The bootstrap creates `.venv`, installs constrained coordinator dependencies and
checks package consistency. The reasoner installer resolves HermiT, Openllet and
JFact classpaths separately and verifies native inference and contradiction
handling, including Konclude. These dependency checks are not benchmark runs.
Do not copy virtual environments between hosts.

## 4. Configure the physical inventory

The root manifest is `configs/topologies/physical/topology.toml`; it references
`nodes/cloud.toml`, `fog.toml`, `mist.toml`, `edge.toml` and `iot.toml`.

| Node | Address | Role |
| --- | --- | --- |
| cloud | 100.86.63.53 | Local coordinator/worker |
| fog | 100.93.73.27 | Remote worker |
| mist | 100.72.111.107 | Remote authority worker |
| edge1 | 100.101.178.35 | Remote authority worker |
| edge2 | 100.70.9.117 | Remote authority worker |
| edge3 | 100.121.135.60 | Remote authority worker |

For a different installation update host, endpoint, CPU, RAM, storage, architecture
and location in these manifests. `local=true` belongs only to the coordinator.
Node IDs and tiers must remain distinct. `authority=true` controls private-data
placement. No IoT worker is enabled by default.

`network_mbps` records nominal capacity only; it does not shape VPN traffic or
measure available bandwidth. Real devices are geographically distributed, but
inventory region placeholders are not coordinates. Leave unknown coordinates
unset. The benchmark does not infer geographical distances from VPN addresses.

The configured remote account is `pi`, release directory
`/home/pi/continuum-bench`, interpreter `.venv-node/bin/python`, and port 8391.
For another account/path, update the physical manifest before deployment.
See [Ontology distribution](ONTOLOGY_DISTRIBUTION.md) for profile and data placement.

## 5. Authorize, synchronize and start

Create an SSH key only if an appropriate key does not already exist:

```bash
ssh-keygen -t ed25519
```

Then, from the coordinator:

```bash
export CONTINUUM_SSH_PROBE_TIMEOUT_SECONDS=120
export CONTINUUM_HEALTH_TIMEOUT_SECONDS=30
continuum-bench physical authorize --ssh-user pi
continuum-bench physical prepare --ssh-user pi
continuum-bench physical deploy --with-dl-reasoners --ssh-user pi
continuum-bench physical start --ssh-user pi
continuum-bench physical status --ssh-user pi
```

Authorization can prompt for remote credentials; subsequent work uses keys.
`prepare` records prerequisites; `deploy` synchronizes maintained assets, creates
worker environments and verifies native backends. `start` also launches Cloud.
The comparison module uses isolated SSH jobs with an archived source bundle,
while Battery 1 uses the running HTTP services. Both use the same inventory.

All six services must match the coordinator's code, topology and semantic digest.
Any later code/semantic edit requires synchronization and restart before a new
campaign. Installation logs and virtual environments are local generated assets.
Proceed to [Complete execution](COMPLETE_EXECUTION.md); outputs are explained in
[Outputs](OUTPUTS.md).
