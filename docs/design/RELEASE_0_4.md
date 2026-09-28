# Release 0.4.0: distributed reasoning scalability

Version 0.4.0 adds a fourth separated physical experiment without changing the
canonical ontology release (`v3.0.0`) or the worker HTTP envelope (protocol 8).
Its distributed fragment contract is version 3, so every participating worker
must be redeployed from the same source revision before the experiment runs.

## What changed

- `distributed-reasoning-scalability` compares deterministic distributed and
  replicated placement under strong and weak scaling.
- Exact logical graph sizes range from 50,000 to 2,000,000 triples on 1, 2, 3,
  5 and 6 nodes in the supplied full configuration.
- Five repetitions, seed 2026, task contracts, query concurrency and bootstrap
  statistics are externalized in `configs/distributed-reasoning.toml`.
- Identity, RDFS, OWL RL, combined RDFS+OWL RL, ELK, HermiT, Openllet, JFact and
  Konclude use one registry. Results are compared only within equivalent task
  groups.
- Each point records logical and fragment digests, per-node graph/resource
  observations, inference and query time, throughput, network bytes, speedup,
  strong/weak efficiency, imbalance, overhead and final status.
- The first repetition of each matrix point validates query projections against
  a complete replicated reference outside measured end-to-end time.

ELK 0.4.3 passes the project EL smoke ontology. The complete ontology contains
RDF mappings that its OWLAPI 4.1.3 path cannot parse as OWL 2 EL input. The
runner records `profile_compatible=false` and skips later equivalent points.
This is a profile-suitability result, not an engine substitution or timeout.

## Run from a clean clone

```bash
python3 tools/bootstrap.py --profile coordinator
. .venv/bin/activate
python3 tools/install_owl_reasoners.py
continuum-bench physical authorize --ssh-user pi
continuum-bench physical deploy --with-dl-reasoners --ssh-user pi
continuum-bench physical start --ssh-user pi
continuum-bench physical status --ssh-user pi
continuum-bench experiment distributed-reasoning-scalability physical \
  --distributed-reasoning-config configs/distributed-reasoning-smoke.toml
continuum-bench experiment plot distributed-reasoning-scalability
```

Run the complete, potentially long matrix with:

```bash
continuum-bench --unlimited --repetitions 5 experiment \
  distributed-reasoning-scalability physical \
  --distributed-reasoning-config configs/distributed-reasoning.toml
```

Run every family with a unique retained suite directory:

```bash
continuum-bench --unlimited --repetitions 5 suite
```

## Compatibility and evidence status

- Existing `continuum.monitoring.v1` evidence remains readable.
- New experiment rows use `distributed-reasoning-v1`.
- Historical `sharded` labels are archived evidence. New commands accept
  `distributed` and `replicated`; `shared` is a documented alias for the
  distributed-data/shared-schema treatment where supported.
- A complete physical 0.4.0 matrix has not yet been accepted. Generated figures
  and paper claims must use only completed rows from a freshly deployed run.
- Arbitrary cross-fragment OWL DL completeness, energy use, wide-area mobility
  and clinical stress-detection accuracy remain outside the implemented claims.

See [Distributed reasoning scalability](DISTRIBUTED_REASONING_SCALABILITY.md),
[Run all physical tests](RUN_ALL_TESTS.md) and
[Output layout and execution controls](OUTPUTS_AND_EXECUTION.md).
