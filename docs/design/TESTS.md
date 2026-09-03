# Test suites and command reference

This manual groups commands by purpose, architecture and experimental family.
Run commands from the repository root. Complete
[installation](INSTALLATION.md) and `continuum-bench topology validate` before
starting measured tests.

## 1. Test levels

| Level | Purpose | Publication evidence |
|---|---|---|
| Static/semantic validation | Reject invalid artefacts and expectations | Necessary, not sufficient |
| Pytest smoke | Fast developer workflow contract | No |
| Measurable smoke | End-to-end execution with tiny profiles | No |
| Full benchmark | Repeated configured measurements | Yes, with metadata and controls |
| Cross-architecture analysis | Matched speedup, costs and equivalence | Yes, if comparison gates pass |

Never report smoke timings as performance results. They use small data,
minimal repetitions and may share caches or host activity with development.

## 2. Installation and read-only diagnostics

```bash
# Standard-library pre-install check
python3 tools/doctor.py

# Coordinator environment
python3 tools/bootstrap.py

# Docker daemon, Compose and Buildx
python3 tools/doctor.py --docker

# SSH, rsync and local physical prerequisites
python3 tools/doctor.py --physical

# Machine-readable diagnostics
.venv/bin/continuum-bench doctor --docker --physical --json
```

`bootstrap.py --with-docker` additionally prepares the Docker images used by
the smoke entry points:

```bash
python3 tools/bootstrap.py --with-docker
```

## 3. Topology validation

```bash
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench topology show --name monolith
.venv/bin/continuum-bench topology show --name docker
.venv/bin/continuum-bench topology show --name physical
```

This checks composed architecture/tier files, identifiers, endpoints, ports,
privacy authorities, remote paths and topology fingerprints. It does not start
services.

Render Docker Compose without starting it:

```bash
.venv/bin/continuum-bench topology render --name docker \
  --output outputs/runtime/docker-compose-docker.yml

docker compose \
  -f outputs/runtime/docker-compose-docker.yml \
  config --quiet
```

## 4. Semantic release validation

```bash
.venv/bin/continuum-bench validate
```

The gate verifies:

- parsing of canonical and modular Turtle artefacts;
- v3 identity and expected counts: 72 RF, 39 RNF, 5 RV, 79 policies,
  55 mechanisms, 17 scenarios and 115 queries;
- unique query IDs, file presence and catalog/category agreement;
- all 115 reference query expectations;
- SHACL conformance;
- RDFS, OWL RL and RDFS+OWL RL materialization;
- datatype range safety, including language strings versus `xsd:string`;
- absence of resources inferred as `owl:Nothing`;
- zero post-entailment violation-query failures;
- authority-aware fragment reconstruction and privacy isolation;
- release and traceability coverage reporting.

A non-zero exit code means the release is not ready for benchmarking.

Validate local documentation links and generated v3 reference manuals:

```bash
.venv/bin/python tools/check_documentation.py
```

Run `.venv/bin/python tools/generate_reference_docs.py` first after changing
the canonical ontology or query catalog.

### Optional OWL 2 DL and HermiT gate

```bash
python3 tools/check_owl_consistency.py \
  --require-dl-profile \
  --timeout 180 \
  --output outputs/validation/ontology-hermit.json

.venv/bin/python -m pytest -m owl_consistency
```

This requires Java 11+ and Protégé/HermiT. The pytest is skipped when that
external runtime is absent; the direct checker fails rather than claiming a
successful consistency check.

## 5. Pytest suites

```bash
# Entire unit, semantic and workflow suite
.venv/bin/python -m pytest

# Fast cumulative workflow contract
.venv/bin/python -m pytest -m smoke_cumulative

# Fast scalability workflow contract
.venv/bin/python -m pytest -m smoke_scalability

# Everything except the two marked smoke contracts
.venv/bin/python -m pytest \
  -m "not smoke_cumulative and not smoke_scalability"
```

The cumulative pytest uses a temporary one-repetition RDFS configuration and
requires all 16 stages to grow monotonically to 115 query IDs. The scalability
pytest uses tiny independent user volumes and verifies growth, complete query
coverage and detailed CSV output.

The wider suite covers ontology integrity, query expectations, deterministic
generation, result digests, topology composition, Compose rendering, physical
lifecycle commands, privacy, partition reconstruction and reports.

## 6. Monolithic smoke suites

### 6.1 Cumulative smoke

Automatic Python profiles plus RDFLib/Jena/RDF4J/Oxigraph:

```bash
.venv/bin/continuum-smoke-cumulative
```

Equivalent explicit command:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  benchmark cumulative
```

Python-only fallback when Docker is intentionally unavailable:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  benchmark cumulative --python-only
```

The suite performs one repetition with `rdfs`, `owlrl` and `rdfs_owlrl`. It
adds these categories cumulatively:

1. `topology`
2. `semantic_schema`
3. `observability`
4. `identity_consent`
5. `data_lifecycle`
6. `security_identity`
7. `context_zones`
8. `trust`
9. `decision`
10. `policy_governance`
11. `adaptation`
12. `delegation`
13. `federation`
14. `audit_temporal`
15. `validation`
16. `wellbeing`

The terminal reports reasoner, repetition, stage, added category and cumulative
query count. Outputs are written below
`outputs/smoke-cumulative/cumulative/`.

### 6.2 Scalability smoke

```bash
.venv/bin/continuum-smoke-scalability
```

Explicit and Python-only forms:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  benchmark scalability

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  benchmark scalability --python-only
```

The smoke rebuilds independent deterministic graphs for 5 and 25 users. Each
point executes all 115 queries with all three Python reasoning profiles. The
second point is 25 total users, not 5 plus 25. Outputs are written below
`outputs/smoke-scalability/scalability/`.

## 7. Complete monolithic benchmarks

```bash
.venv/bin/continuum-bench benchmark cumulative
.venv/bin/continuum-bench benchmark scalability
.venv/bin/continuum-bench benchmark all
```

Use `--python-only` only when the independent product dimension is outside the
study. Product warm-ups can be configured explicitly:

```bash
.venv/bin/continuum-bench benchmark all \
  --engine-warmups 2
```

Primary outputs:

```text
outputs/cumulative/{summary.csv,query-runs.csv,metadata.json}
outputs/scalability/{summary.csv,query-runs.csv,metadata.json}
outputs/engines/...
```

## 8. Independent semantic-product benchmarks

Normal `benchmark` and `docker` commands start and stop the independent product
stack automatically. To operate it manually:

```bash
docker compose -f docker-compose.engines.yml up -d --build

.venv/bin/continuum-bench engines cumulative
.venv/bin/continuum-bench engines scalability
.venv/bin/continuum-bench engines all

docker compose -f docker-compose.engines.yml down
```

The default endpoints are RDFLib `8291`, Jena `8292`, RDF4J `8293` and
Oxigraph `8294`. Jena, RDF4J and RDFLib use the common RDFS contract. Oxigraph
is a no-entailment SPARQL control and must not be described as an OWL reasoner.

Regenerate product figures:

```bash
.venv/bin/continuum-bench plot engines \
  --engine-dir outputs/engines \
  --engine-suite all
```

## 9. Docker architecture

### 9.1 Lifecycle

```bash
.venv/bin/continuum-bench topology up --name docker
.venv/bin/continuum-bench topology status --name docker
.venv/bin/continuum-bench topology logs --name docker
```

### 9.2 Separate Docker smokes

Authority-partitioned cumulative:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  docker cumulative \
  --layout sharded \
  --topology-only \
  --output-dir outputs/docker-smoke-cumulative
```

Authority-partitioned scalability:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  docker scalability \
  --layout sharded \
  --topology-only \
  --output-dir outputs/docker-smoke-scalability
```

Replicated variants:

```bash
.venv/bin/continuum-bench \
  --config configs/smoke-cumulative.toml \
  docker cumulative \
  --layout replicated \
  --topology-only \
  --output-dir outputs/docker-smoke-cumulative-replicated

.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  docker scalability \
  --layout replicated \
  --topology-only \
  --output-dir outputs/docker-smoke-scalability-replicated
```

Remove `--topology-only` when the same command must also run the independent
four-product benchmark.

### 9.3 Complete Docker suites

```bash
.venv/bin/continuum-bench docker cumulative --layout sharded
.venv/bin/continuum-bench docker scalability --layout sharded
.venv/bin/continuum-bench docker all --layout sharded

.venv/bin/continuum-bench docker cumulative --layout replicated
.venv/bin/continuum-bench docker scalability --layout replicated
.venv/bin/continuum-bench docker all --layout replicated
```

Legacy-compatible sharded aliases:

```bash
.venv/bin/continuum-bench sharded docker cumulative
.venv/bin/continuum-bench sharded docker scalability
.venv/bin/continuum-bench sharded docker all
```

Stop the topology after the campaign:

```bash
.venv/bin/continuum-bench topology down --name docker
```

## 10. Physical architecture

### 10.1 Provision and lifecycle

```bash
.venv/bin/continuum-bench physical authorize --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi
```

`authorize` may request each Raspberry Pi password once through
`ssh-copy-id`. Later commands require key authentication and never read a
password from TOML.

### 10.2 Separate physical smokes

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

### 10.3 Complete physical suites

```bash
.venv/bin/continuum-bench physical all \
  --layout sharded --ssh-user pi

.venv/bin/continuum-bench physical all \
  --layout replicated --ssh-user pi
```

The `[distributed]` table in the selected benchmark TOML bounds one remote
request and one worker phase. Sharded query assignments are split according to
`query_batch_size` (4 by default), and the terminal reports every batch. The
default `request_retries = 0` prevents a timed-out 70+ query POST from being
executed repeatedly on a single-threaded Raspberry Pi. After changing this
configuration, run `physical stop`, `physical deploy`, `physical start`, and
`physical status` so every node uses the same release.

The publication configuration uses a 60-second request/phase ceiling and a
90-second complete-point ceiling. If a sharded timeout occurs, the terminal
identifies the node, batch and exact query IDs. The coordinator writes a
right-censored timeout row, does not validate the partial answer, and records
larger points as `skipped_after_timeout` rather than waiting for them or
aborting the complete command. Smoke ceilings are 30 seconds per phase and 45
seconds per point.

Stop workers without deleting deployments or outputs:

```bash
.venv/bin/continuum-bench physical stop --ssh-user pi
```

## 11. Multidimensional load tests

### 11.1 Architectures

```bash
.venv/bin/continuum-bench load monolith
.venv/bin/continuum-bench load docker
.venv/bin/continuum-bench load physical
.venv/bin/continuum-bench load all
```

Docker and physical services must already be healthy. `load all` does not
provision them.

### 11.2 Independent-variable blocks

```bash
.venv/bin/continuum-bench load all --dimension events_per_second
.venv/bin/continuum-bench load all --dimension users
.venv/bin/continuum-bench load all --dimension target_triples
.venv/bin/continuum-bench load all --dimension rule_count
.venv/bin/continuum-bench load all --dimension node_count
```

`--dimension` is repeatable. Run an individual named profile with:

```bash
.venv/bin/continuum-bench load all --profile eps-2500
```

Profile names are declared in `configs/load-benchmark.toml`.

### 11.3 Load figures

```bash
.venv/bin/continuum-bench load plot
.venv/bin/continuum-bench load plot --show
```

Measured variables include p50/p95/p99 latency, processed/lost events,
throughput, inference, alert precision/accuracy, CPU, current/peak RSS, disk,
HTTP body bytes and recovery time.

## 12. Three separated architecture experiments

### 12.1 Query scale-out with replicas

```bash
.venv/bin/continuum-bench experiment scale-out monolith
.venv/bin/continuum-bench experiment scale-out docker
.venv/bin/continuum-bench experiment scale-out physical
.venv/bin/continuum-bench experiment scale-out all
```

Smoke profile example:

```bash
.venv/bin/continuum-bench experiment scale-out all \
  --experiment-config configs/experiments-smoke.toml \
  --output-dir outputs/experiments-smoke
```

### 12.2 Reasoning scalability by hardware

```bash
.venv/bin/continuum-bench experiment reasoning-hardware monolith
.venv/bin/continuum-bench experiment reasoning-hardware docker
.venv/bin/continuum-bench experiment reasoning-hardware physical
.venv/bin/continuum-bench experiment reasoning-hardware all
```

Select one reasoner or hardware profile:

```bash
.venv/bin/continuum-bench experiment reasoning-hardware physical \
  --reasoner rdfs \
  --profile triples-25000
```

Use an exact profile name from `configs/experiments.toml`.

### 12.3 Truly distributed ontology

```bash
.venv/bin/continuum-bench experiment distributed-ontology monolith
.venv/bin/continuum-bench experiment distributed-ontology docker
.venv/bin/continuum-bench experiment distributed-ontology physical
.venv/bin/continuum-bench experiment distributed-ontology all
```

### 12.4 Run all three families

```bash
.venv/bin/continuum-bench experiment all monolith
.venv/bin/continuum-bench experiment all docker
.venv/bin/continuum-bench experiment all physical
.venv/bin/continuum-bench experiment all all
```

### 12.5 Figures and hypothesis analysis

```bash
.venv/bin/continuum-bench experiment plot scale-out
.venv/bin/continuum-bench experiment plot reasoning-hardware
.venv/bin/continuum-bench experiment plot distributed-ontology
.venv/bin/continuum-bench experiment plot all --show
.venv/bin/continuum-bench experiment analyze --show
```

The analysis reports matched throughput/latency speedups, CPU/RSS cost ratios,
scale-out efficiency, timeouts, equivalence, break-even points and an explicit
claim verdict. It never assumes that a distributed architecture must be
faster.

## 13. Comparisons and publication figures

Compare monolithic and Docker cumulative/scalability results:

```bash
.venv/bin/continuum-bench compare cumulative
.venv/bin/continuum-bench compare scalability
.venv/bin/continuum-bench compare all
```

Regenerate figures from existing CSV files:

```bash
.venv/bin/continuum-bench plot cumulative
.venv/bin/continuum-bench plot scalability
.venv/bin/continuum-bench plot all
.venv/bin/continuum-bench plot publication
```

Generate the full architecture/product report:

```bash
.venv/bin/continuum-report \
  --monolith-dir outputs \
  --docker-dir outputs/docker/replicated \
  --physical-dir outputs/physical/replicated \
  --docker-sharded-dir outputs/docker/sharded \
  --physical-sharded-dir outputs/physical/sharded \
  --output-dir outputs/report
```

Use `--show` only on commands that expose it. On headless servers omit it and
copy the generated PNG/PDF/SVG files elsewhere.

## 14. Complete campaigns

### 14.1 Local-only complete run

```bash
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench validate
.venv/bin/python tools/check_documentation.py
.venv/bin/python -m pytest
.venv/bin/continuum-bench benchmark all
.venv/bin/continuum-bench load monolith
.venv/bin/continuum-bench experiment all monolith
.venv/bin/continuum-bench plot publication
```

### 14.2 Docker complete run

```bash
.venv/bin/continuum-bench topology up --name docker
.venv/bin/continuum-bench topology status --name docker
.venv/bin/continuum-bench docker all --layout sharded
.venv/bin/continuum-bench docker all --layout replicated
.venv/bin/continuum-bench load docker
.venv/bin/continuum-bench experiment all docker
.venv/bin/continuum-bench topology down --name docker
```

### 14.3 Physical complete run

```bash
.venv/bin/continuum-bench physical status --ssh-user pi
.venv/bin/continuum-bench physical all --layout sharded --ssh-user pi
.venv/bin/continuum-bench physical all --layout replicated --ssh-user pi
.venv/bin/continuum-bench load physical
.venv/bin/continuum-bench experiment all physical
.venv/bin/continuum-bench physical stop --ssh-user pi
```

### 14.4 Three-architecture comparison run

With Docker and physical workers already healthy:

```bash
.venv/bin/continuum-bench benchmark all
.venv/bin/continuum-bench docker all --layout sharded
.venv/bin/continuum-bench physical all --layout sharded --ssh-user pi
.venv/bin/continuum-bench load all
.venv/bin/continuum-bench experiment all all
.venv/bin/continuum-bench compare all
.venv/bin/continuum-bench load plot
.venv/bin/continuum-bench experiment analyze
.venv/bin/continuum-report
```

## 15. Output interpretation and limits

- `total_ms` is local phase time; distributed suites use wall-time fields.
- Do not add per-node durations and describe the sum as distributed latency.
- Replicated mode evaluates query distribution, not distributed reasoning.
- Hardware reasoning evaluates endpoints independently, not a cluster speedup.
- Distributed ontology mode includes partitioning/federation semantics and must
  pass the monolithic result oracle.
- In every benchmark family, a timeout is a censored observation, not a missing
  row. Partial distributed answers are never treated as completed or
  semantically valid.
- Event loss and failed profiles must remain in summaries and figures.
- Result count alone is weaker than the canonical result digest; use the digest
  when both result sets provide it.
- `EXT-Q76` and `EXT-Q77` are acceptance-readiness reviews. Pending rows are
  expected until campaign-specific thresholds and metadata are configured.
- More nodes can be slower for small datasets because preparation,
  serialization, network and federation overhead dominate.

Read [BENCHMARKS.md](BENCHMARKS.md),
[THREE_EXPERIMENTS.md](THREE_EXPERIMENTS.md) and
[SCIENTIFIC_VALIDITY.md](SCIENTIFIC_VALIDITY.md) before drawing claims.
