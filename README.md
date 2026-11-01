# Continuum RDF Scalability Benchmark

This repository measures how a containerized semantic monitoring service scales as the monitored population and its RDF ABox grow on a physical Cloud–Fog–Mist–Edge continuum. The TBox, query catalog, container limits, physical hosts, and query concurrency remain fixed.

Python is the experiment control plane. Rust is the semantic data plane: it generates deterministic ABoxes, parses and serializes RDF, materializes RDFS, executes SPARQL with Oxigraph, and serves the worker HTTP protocol.

The coordinator requires Python 3.11 or newer, Rust, Docker Compose, and key-based SSH access to the five remote hosts. Workers require Docker Compose, cgroup v2 CPU/memory/PID controllers, at least 1536 MiB available for the container plus 1536 MiB host reserve, and 4 GiB free disk.

## Quick start

```bash
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
continuum-bench report outputs/<run-id>
```

Use `--exclude-host <id>` only when a host is explicitly unavailable. `--diagnostic-unlimited` removes the preparation-request deadline and marks the run non-comparable; SPARQL requests retain their configured safety deadline.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Benchmark method](docs/BENCHMARK.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Result contract](docs/RESULTS.md)
- [RDF model](docs/RDF_MODEL.md)
- [Migration report](MIGRATION_REPORT.md)
