# Ontology, query and policy audit for v3.0.0

## Audit outcome

The executable release contains:

- 72 functional requirements;
- 39 non-functional requirements;
- 5 validation requirements;
- 79 policies in 12 categories;
- 55 enforcement mechanisms;
- 17 scenarios;
- 115 SPARQL queries (`35 BASE + 80 EXT`).

The canonical ontology is English and no longer combines language-tagged
requirement statements with an `xsd:string` range. The complete file for
Protégé is `ontology/legacy/smartcity_continuum-v3.0.0.ttl`.

## Executable controls

```bash
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench validate
.venv/bin/python -m pytest
```

These gates cover parsing, release counts, query expectations, SHACL,
RDFS/OWL-RL profiles, datatype ranges, contradictions, distributed fragment
reconstruction and privacy placement.

For release-grade OWL 2 DL profile and consistency verification:

```bash
python3 tools/check_owl_consistency.py --require-dl-profile \
  --output outputs/validation/ontology-hermit.json
```

That check requires Java and Protégé/HermiT and is intentionally outside timed
benchmarks.

## Corrections represented in the release

- Requirements, policies, mechanisms and ontology labels are English.
- `requirementStatement` accepts the literal representation actually used.
- RDFS literal value-space handling no longer conflates Boolean and integer
  lexical forms, preventing the previous EXT-Q68 false positive.
- Runtime modules preserve the canonical graph through stable skolemization.
- Consent, semantic contract and effective authorization are independent.
- Policy precedence applies the most restrictive hard constraint before AHP,
  trust or QoS optimization.
- Migration, delegation, degradation, synchronization, rollback and federated
  learning are separate auditable actions.
- Query expectations distinguish inventory/report/review from violation.
- Distributed queries use elastic authority scopes instead of fixed edge IDs.
- Result comparison uses canonical digests when available.

## Acceptance status

The ontology and benchmark can be validated reproducibly, but scientific
acceptance remains campaign-specific. `EXT-Q76` checks whether quantitative
acceptance parameters are configured. `EXT-Q77` checks campaign artefact and
version readiness. Rows from these review queries describe pending evidence;
they are not ontology inconsistency.

## Traceability coverage

The catalog currently links queries directly to 102 of 116 requirements and 69
of 79 policies. Unlinked structural or operational requirements remain visible
in validation and the generated references; they are not presented as direct
query coverage.

Run the reference generator after canonical changes:

```bash
.venv/bin/python tools/generate_reference_docs.py
```

## Audit limits

- OWL open-world consistency does not establish closed-world compliance.
- SHACL conformance does not establish query-result equivalence.
- Zero-row violation queries have meaning only after release/campaign
  preconditions pass.
- A successful smoke is a workflow check, not performance evidence.
- Physical performance depends on network, power, cooling and OS conditions
  that the ontology cannot encode automatically.
