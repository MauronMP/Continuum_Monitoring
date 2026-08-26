# Trazabilidad de artefactos

| Necesidad | Artefacto verificable |
|---|---|
| Ontología estándar del continuum | `ontology/core/schema.ttl` |
| Extensión temática de estrés/sueño | `ontology/domains/wellbeing/schema.ttl` |
| Cumplimiento de políticas | `ontology/shapes/*.ttl` y consultas `violation` |
| Consultas núcleo/tema y por categoría | `queries/catalog.csv` |
| Routing, privacidad y merge distribuido | `queries/execution-plan.toml` |
| Placement cloud/fog/edge | `configs/ontology-placement.toml` y `ontology/profiles` |
| Todos los RF/RNF/políticas | `docs/reference` |
| Datos sintéticos por volumen | `continuum_bench.synthetic` |
| Test acumulativo | `continuum_bench.benchmark.run_cumulative` |
| Test de escalabilidad | `continuum_bench.benchmark.run_scalability` |
| Smoke acumulativo separado | `configs/smoke-cumulative.toml` y `continuum-smoke-cumulative` |
| Smoke de escalabilidad separado | `configs/smoke-scalability.toml` y `continuum-smoke-scalability` |
| Tres razonadores | `continuum_bench.reasoners` |
| Tiempos y gráficas | CSV, JSON y PNG en `outputs` |
| Docker replicado/particionado | `docker-compose.yml`, `distributed.py` y `sharded.py` |
| Continuum físico | `configs/physical-nodes.toml`, `physical_cluster.py` y `sharded.py` |
| Equivalencia de arquitecturas | digest de bindings en `compare.py` y `result-validation.csv` |
