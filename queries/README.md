# Queries and execution plan

[All query texts](ALL_QUERIES.md) collects the complete catalogue.
`catalog.csv` is the runtime index: order, ID, category, expectation,
source path, purpose and policy/requirement traceability. Individual
`.rq` files are the executable sources; the bundle is documentation.

## Query categories

These 16 query groups are not the 12 policy categories. A policy may use
queries from several groups; shared query work must not be double counted.

| Category | Queries | Purpose |
| --- | ---: | --- |
| `topology` | 4 | Compute nodes, placement and infrastructure relationships. |
| `semantic_schema` | 4 | Classes, properties and semantic model structure. |
| `observability` | 5 | Node/device state, operational observations and availability. |
| `identity_consent` | 18 | Users, identifiers, permissions and consent evidence. |
| `data_lifecycle` | 8 | Retention, transfer, provenance and data handling. |
| `security_identity` | 6 | Identity representations and security-related evidence. |
| `context_zones` | 6 | Geographical or contextual zones and their restrictions. |
| `trust` | 6 | Trust assessments and supporting evidence. |
| `decision` | 17 | Candidate evaluation, alternatives and decision evidence. |
| `policy_governance` | 8 | Policy inventory, requirements and governance links. |
| `adaptation` | 8 | Adaptation and model/service change records. |
| `delegation` | 5 | Delegated work and recovery conditions. |
| `federation` | 7 | Federated-learning session and model-update records. |
| `audit_temporal` | 5 | Temporal validity, audit trails and recorded events. |
| `validation` | 4 | Evidence/constraint checks and missing required records. |
| `wellbeing` | 4 | Wearables, physiological observations and the health example. |

## What execution-plan.toml does

`execution-plan.toml` supplies coordinator routing and merge metadata.
It is not a scheduler, an OWL reasoner or an access-control enforcement engine.

| Scope | Query count | Destination |
| --- | ---: | --- |
| `cloud` | 20 | The configured cloud tier. |
| `fog` | 11 | The configured fog tier. |
| `authorities` | 78 | All configured private-data authorities, including Mist. |
| `authority_key:http://example.org/monitoringcontinuum#UserA` | 2 | The deterministic owner of the named user. |
| `authority_key:http://example.org/monitoringcontinuum#UserB` | 3 | The deterministic owner of the named user. |
| `authority_key:http://example.org/monitoringcontinuum#UserD` | 1 | The deterministic owner of the named user. |

`[merge]` specifies set union for designated multi-source SELECT results
and boolean OR for the listed ASK queries. Set union removes duplicate rows;
it does not implement arbitrary distributed joins or global OWL inference.
Other queries follow their assigned single scope. `[privacy]` records
restricted/confidential query classifications; labels alone are not
authorization. Instance partitioning and projection checks are separate.

User-specific routing and fragment construction must use the same authority
ordering. The active authority list includes Mist and all three Edge nodes.
Adding/removing authorities can change assignment. A profile import list
does not itself select query destinations.

## Updating the catalogue

Maintain unique IDs, source text, expectations, category and traceability
in `catalog.csv`; update the routing/merge/privacy entries for the same IDs.
Then regenerate and validate:

```bash
python tools/generate_project_indexes.py
python tools/generate_reference_docs.py
python tools/check_documentation.py
continuum-bench validate
```

Changes affect semantic fingerprints and require synchronization/restart
before a new physical run. See [Ontology distribution](../docs/ONTOLOGY_DISTRIBUTION.md)
and [Ontology review](../docs/ONTOLOGY_REVIEW.md).
