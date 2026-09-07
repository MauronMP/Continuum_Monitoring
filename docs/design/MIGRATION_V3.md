# Ontology release migration

The repository treats the complete Turtle ontology and the SPARQL battery as
the authoritative semantic inputs. Derived query files, reference
documentation and validation summaries must be regenerated after semantic
changes.

## Canonical inputs

| Content | Canonical source |
|---|---|
| Complete ontology | `ontology/legacy/smartcity_continuum-v3.0.0.ttl` |
| Complete SPARQL battery | `queries/legacy/sparql_battery-v3.0.0.sparql` |
| Runtime query metadata | `queries/catalog.csv` |
| Physical topology | `configs/topologies/physical/topology.toml` |

The `legacy` directory name preserves compatibility with the received
single-file artefacts. The Turtle file remains the complete ontology to open in
Protégé.

## Regeneration workflow

After editing canonical ontology or battery sources:

```bash
.venv/bin/python tools/migrate_assets.py
.venv/bin/python tools/generate_reference_docs.py
.venv/bin/continuum-bench validate
.venv/bin/python -m pytest
```

Do not patch only a derived module or one `.rq` file when the canonical source
must remain authoritative.

## Runtime compatibility

Physical workers must run the same Git revision, ontology files, query catalog
and worker protocol as the coordinator. After a semantic migration, redeploy
the physical nodes:

```bash
.venv/bin/continuum-bench physical stop --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi
```

Historical CSV files without the current result schema are not directly
comparable with new publication runs.

## Explicit acceptance debt

`EXT-Q76` reports missing quantitative acceptance-profile parameters.
`EXT-Q77` reports missing validation-campaign or artefact readiness. They are
review gates and intentionally remain visible until the corresponding campaign
evidence exists.
