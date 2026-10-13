# Documentation

- [Installation](INSTALLATION.md): clean coordinator and worker setup.
- [Experiments](EXPERIMENTS.md): contracts for the four policy evaluations.
- [Outputs](OUTPUTS.md): CSV schemas, PNG generation and result layout.
- [Physical continuum](PHYSICAL_CONTINUUM.md): inventory, deployment and complete execution.
- [Complete execution](COMPLETE_EXECUTION.md): clean installation and every full-suite or per-family command.
- [Tests and figures](TESTS_AND_FIGURES.md): purpose, evidence files and PNG provenance for every active test family.
- [Observed failures](OBSERVED_FAILURES.md): current timeout, semantic-validation, ontology-debt and remediation audit.
- [Project audit](AUDIT.md): verified release state, boundaries and known limitations.
- [Ontology distribution](ONTOLOGY_DISTRIBUTION.md): exact files per tier/node, instance ownership, routing and implementation limits.
- [Ontology reference](reference/ONTOLOGY_REFERENCE.md): generated internal model inventory.
- [Policies](reference/POLICIES.md): generated policy catalog.
- [Requirements](reference/REQUIREMENTS.md): generated requirement catalog.
- [SPARQL queries](reference/SPARQL_QUERIES.md): generated query catalog.

All commands assume the repository root and an activated `.venv` unless stated
otherwise.

## Optional comparative policy evaluation

The independent [comparative evaluation module](COMPARATIVE_EVALUATION.md) runs paired static,
procedural and semantic policy strategies on the physical hosts. It provides
its own bounded configuration, four experiments, durable JSON/CSV evidence and
per-node PNG figures. Published systems are methodological references, not
claimed reproductions. All six configured hosts, including Mist, are included by default.

```bash
.venv/bin/python -m continuum_bench.monitoring.comparison check
.venv/bin/python -m continuum_bench.monitoring.comparison run --smoke
.venv/bin/python -m continuum_bench.monitoring.comparison run
```
