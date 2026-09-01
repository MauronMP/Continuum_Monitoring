# Query taxonomy for v3.0.0

## Two independent classifications

Every query has:

1. a semantic tier: `core` or `domain`;
2. an operational category used by cumulative activation and deployment.

`core` queries are needed to validate a generic policy-aware continuum.
`domain` queries depend on an application extension; v3 currently uses the
wellbeing domain. BASE/EXT prefixes preserve historical identity and do not
determine core/domain membership.

## Operational categories

| Order | Category | Scope |
|---:|---|---|
| 1 | `topology` | Nodes, tiers, zones and connections |
| 2 | `semantic_schema` | Release artefacts, scenarios and schema coverage |
| 3 | `observability` | Device, user and node state |
| 4 | `identity_consent` | Identity, consent, contracts and authorization |
| 5 | `data_lifecycle` | Context, buffering, replication and transmission |
| 6 | `security_identity` | Identifiers, encryption and protected flows |
| 7 | `context_zones` | Rural, urban and restricted-zone decisions |
| 8 | `trust` | Trust evidence, reproducibility and eligibility |
| 9 | `decision` | Model tiers, AHP, alternatives and rollback |
| 10 | `policy_governance` | Policy inventory, types, conflicts and traceability |
| 11 | `adaptation` | Migration, degradation and adaptive actions |
| 12 | `delegation` | Temporary delegation, depth and recovery |
| 13 | `federation` | Federated learning, payload and differential privacy |
| 14 | `audit_temporal` | Audit chains and temporal validity |
| 15 | `validation` | SHACL, acceptance and campaign readiness |
| 16 | `wellbeing` | Wearables, sensors, stress and sleep |

The authoritative counts and ordering are in `queries/catalog.csv` and
`configs/benchmark.toml`. Validation fails if the catalog and configuration
category sets differ.

## Adding a generic continuum feature

Place its query below `queries/core/CATEGORY/`, add one catalog row, add an
execution-plan entry when federation is needed and ensure the category is
covered by at least one node in distributed topologies.

## Adding another application domain

Create `ontology/domains/DOMAIN`, place queries below
`queries/domain/DOMAIN/CATEGORY`, mark catalog tier `domain`, and declare
placement explicitly. Do not move generic topology, consent, policy or audit
concepts into the domain module.

## Query-kind semantics

- `inventory`: declared resource coverage;
- `report`: explanatory evidence, not automatic failure;
- `review`: pending configuration or human review;
- `violation`: zero rows only after validation preconditions;
- `ASK`: Boolean assertion interpreted by its expectation;
- `dashboard`: aggregated coverage/status.

`EXT-Q76` and `EXT-Q77` are review gates. Their rows identify missing
campaign-specific parameters and must not be misreported as ontology
inconsistency.
