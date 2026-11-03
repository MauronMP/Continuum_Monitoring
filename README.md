# Continuum RDF Scalability Benchmark

This repository measures how a containerized semantic monitoring service scales as the monitored population and its RDF ABox grow on a physical Cloud–Fog–Mist–Edge continuum. The TBox, query catalog, container limits, physical hosts, and query concurrency remain fixed.

Python is the experiment control plane. Rust is the semantic data plane: it generates deterministic ABoxes, parses and serializes RDF, materializes RDFS, executes SPARQL with Oxigraph, and serves the worker HTTP protocol.

The executable semantic contract is RDFS plus Oxigraph SPARQL. Policies, requirements, mechanisms, and query categories are represented and queried as RDF; the scalability benchmark measures their semantic data-processing cost but does not claim autonomous policy enforcement or OWL DL/SHACL validation.

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

Use `--exclude-host <id>` only when a host is explicitly unavailable. `--diagnostic-unlimited` removes the complete remote `/prepare` request deadline and marks the run non-comparable; physical SPARQL requests and logical queries retain separate deadlines.

Only one logical monitoring query is active at a time. A distributed query issues concurrent physical requests to every participant required by its routing contract, waits for the complete fan-out, and then merges the results. A partial fan-out is a failed logical result. The first logical query timeout aborts its repetition; workers must recover to an idle state or be restarted before another repetition can begin.

Every scenario-layout combination restarts all workers before its warm-up. Resource evidence labels `reset`, `readiness`, `preparation`, `queries`, and `post_check`. `ready_seconds` measures the end-to-end interval from the beginning of partitioning until every worker exposes the expected prepared graph and RDFS closure.

Installation requires a complete repository clone because configuration, ontology, queries, Rust sources, and container definitions are repository assets rather than Python wheel data.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Benchmark method](docs/BENCHMARK.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Result contract](docs/RESULTS.md)
- [RDF model](docs/RDF_MODEL.md)
- [Requirements catalogue](docs/REQUIREMENTS.md)
- [SPARQL query catalogue](docs/QUERY_CATALOG.md)
- [Migration report](MIGRATION_REPORT.md)
