# Documentation index

All active project documentation is written in English. Commands assume the
repository root unless stated otherwise.

## Start here

- [User guide](USER_GUIDE.md): end-to-end workflow from clone to reports.
- [Installation](design/INSTALLATION.md): host packages, bootstrap, Docker,
  Raspberry Pi workers and troubleshooting.
- [Tests](design/TESTS.md): every smoke, suite, architecture and plotting
  command, grouped by purpose.

## Configuration and architecture

- [Architecture](design/ARCHITECTURE.md)
- [Elastic topology](design/ELASTIC_TOPOLOGY.md)
- [Query categories](design/CATEGORIES.md)
- [v3 migration contract](design/MIGRATION_V3.md)
- [Traceability](design/TRACEABILITY.md)

## Experimental methods

- [Core benchmark methodology](design/BENCHMARKS.md)
- [Independent semantic engines](design/ENGINE_BENCHMARKS.md)
- [Docker deployments](design/DOCKER_BENCHMARKS.md)
- [Physical continuum](design/PHYSICAL_CONTINUUM.md)
- [Multidimensional load](design/LOAD_BENCHMARKS.md)
- [Three separated architecture experiments](design/THREE_EXPERIMENTS.md)
- [Comparative report](design/COMPARATIVE_REPORT.md)
- [Scientific validity and limitations](design/SCIENTIFIC_VALIDITY.md)

## Ontology assurance

- [Audit](design/AUDIT.md)
- [Protégé and OWL 2 DL](design/ONTOLOGY_PROTEGE.md)
- [Ontology diagrams](../ontology/diagrams/README.md)

## Generated v3 references

- [Requirements](reference/REQUIREMENTS.md)
- [Policies and mechanisms](reference/POLICIES.md)
- [SPARQL battery](reference/SPARQL_QUERIES.md)
- [Ontology term catalog](reference/ONTOLOGY_REFERENCE.md)

Regenerate those four references after changing canonical v3 assets:

```bash
.venv/bin/python tools/generate_reference_docs.py
.venv/bin/python tools/check_documentation.py
```
