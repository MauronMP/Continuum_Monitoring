# v3.0.0 migration and release contract

## Canonical inputs

| Content | Canonical source |
|---|---|
| Complete ontology | `ontology/legacy/smartcity_continuum-v3.0.0.ttl` |
| Complete SPARQL battery | `queries/legacy/sparql_battery-v3.0.0.sparql` |
| Requirements | RDF individuals in the canonical ontology |
| Policies/mechanisms | RDF individuals in the canonical ontology |
| Runtime query metadata | `queries/catalog.csv` |

The `legacy` directory name describes compatibility with the received
single-file artefacts; the v3 Turtle file remains the complete source to open
in Protégé.

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

## Executable release contract

`continuum_bench.specification` verifies versioned artefacts, counts and IDs.
Worker protocol metadata additionally fixes:

- ontology version `3.0.0`;
- English datatype-safe ontology revision;
- query count 115;
- RDFS literal-value-space reasoning contract;
- topology fingerprint for distributed deployments.

Workers built from older releases are rejected before measurement.

## Main semantic changes from v2

- binary consent replaced by `ConsentRecord`, consent ranges and effective
  authorization;
- semantic contract, consent and zone remain independent restrictions;
- local processing means device/mobile and authorized mist, not edge;
- policy model expanded to 79 typed/versioned policies and 55 mechanisms;
- reproducible `TrustAssessment` separated from AHP weights;
- explicit decision alternatives and AHP consistency data;
- migration, delegation, degradation, retention, synchronization, rollback and
  federated learning represented as different actions;
- differential-privacy payload/accounting model;
- generalized temporal entities and planned expiry;
- 17 reproducible scenarios and an acceptance profile;
- 115 external SPARQL queries and expanded SHACL validation.

## English/datatype correction

The complete ontology uses English labels/statements. Requirement literals no
longer conflict with an `xsd:string` range through language tags. The RDFS
profile also guards Boolean/numeric literal value spaces, preventing the former
EXT-Q68 cross-engine false positive.

## Result compatibility

Results created before the current ontology revision, reasoning contract or
worker protocol are not directly comparable. Rebuild Docker images and redeploy
physical workers:

```bash
.venv/bin/continuum-bench topology down --name docker
.venv/bin/continuum-bench topology up --name docker

.venv/bin/continuum-bench physical stop --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
```

Historical CSV files without `result_digest` use a documented weaker
cardinality/ASK comparison. New publication campaigns should regenerate all
architectures with the current contract.

## Explicit acceptance debt

`EXT-Q76` reports missing quantitative acceptance-profile parameters.
`EXT-Q77` reports missing validation-campaign or artefact readiness. They are
review queries and intentionally remain visible rather than inventing
thresholds or claiming readiness from absent evidence.
