# Deployment

The coordinator needs Python 3.11+, Rust/Cargo, Docker Compose, and SSH key access. Worker hosts need Docker Compose, cgroup CPU/memory support, 1536 MiB reservable RAM plus host reserve, and 4096 MiB free disk. The worker accepts preparation payloads up to `deployment.max_prepare_mib` (256 MiB by default); this explicit limit is exposed by `/health` and checked before a campaign starts.

```bash
git clone https://github.com/MauronMP/Continuum_Monitoring.git
cd Continuum_Monitoring
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
rustup component add rustfmt clippy
cargo build --release --manifest-path rust/Cargo.toml
continuum-bench doctor
continuum-bench render
continuum-bench deploy
continuum-bench status
continuum-bench run
```

Edit `configs/topology.toml` only when addresses or authorities change. `doctor` must report all requested hosts ready. `deploy` synchronizes the Rust/Docker sources, releases the dedicated benchmark port from a previous worker, builds natively and concurrently on the six hosts, starts one constrained container per host, and then verifies the Rust protocol and semantic fingerprints. `status` must show `continuum-rdf-worker-v1`, 113 queries, `idle=true`, and the same topology, ontology, and catalog digests everywhere.

Run `deploy` again whenever the ontology base, query manifest, topology, worker protocol, or container image changes. A campaign refuses workers whose fingerprints differ from the local repository. The timeout, memory, disk, topology, and scenario validators reject non-positive limits, duplicate scenario names, duplicate hosts, invalid ports, unsupported tiers, and unknown exclusions before deployment or measurement.

The multi-stage worker image contains no Python, Java, Maven, OWL DL reasoner, or SHACL engine. It records its Rust compiler, build target, and `max_prepare_bytes` in `/health`. A normal status response must report `max_prepare_bytes=268435456`. `restart: "no"` keeps crashes observable. Do not start a campaign after excluding a host unless that reduced topology is the intended and documented experiment.
