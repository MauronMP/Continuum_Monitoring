# Native monolith user guide

The monolith is the one-process, one-node control architecture. Its manifest is
`configs/topologies/monolith/topology.toml`; the tier files beneath
`configs/topologies/monolith/nodes/` keep the same elastic configuration shape
as the distributed targets, although exactly one local node must remain active.

## Fast acceptance

```bash
continuum-bench topology validate --name monolith
continuum-bench validate
continuum-bench preflight
continuum-smoke-local-cumulative
continuum-smoke-local-scalability
continuum-smoke-local-load
continuum-smoke-local-experiments
```

Every smoke uses one repetition and bounded data. It exits non-zero if any CSV
row is timed out, skipped, failed, loses events or lacks required reference
validation. Smoke output is isolated below `outputs/smoke/` and never replaces
full campaign data.

## Full native campaign

```bash
continuum-bench local cumulative
continuum-bench local scalability
continuum-bench local all
continuum-bench load local
continuum-bench experiment all local
```

`local all` is shorthand only for cumulative plus scalability. `load local`
uses every load profile but fixes the effective node count to one. In the
scale-out experiment, the monolith supplies only the one-node control point;
Physical runs supply the multi-node points.

## Semantic products and OWL validators

Start the four native semantic services before running their benchmarks:

```bash
continuum-smoke-engines
continuum-bench engines cumulative
continuum-bench engines scalability
continuum-bench engines all
continuum-bench engines plot
```

All four products—RDFLib, Jena, RDF4J and Oxigraph—run automatically. This is
not interchangeable with `continuum-bench owl-validate --require-all`, which
checks ontology consistency with HermiT, Openllet, JFact and Konclude.

The monolith cost study is generated and analyzed separately:

```bash
continuum-bench study trace --target local --output-dir outputs/study/local
continuum-bench study category-cost \
  --events outputs/load/local/event-runs.csv \
  --output-dir outputs/study/local-cost
```
