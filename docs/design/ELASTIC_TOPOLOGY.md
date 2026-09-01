# Elastic configuration by architecture and tier

## Source-of-truth hierarchy

Topology configuration has three levels. `configs/topology.toml` is the common
catalog and contains no node definitions. Each architecture owns a deployment
manifest, and each continuum tier owns a node file:

```text
configs/
├── topology.toml
└── topologies/
    ├── monolith/
    │   ├── topology.toml
    │   └── nodes/{cloud,fog,mist,edge,iot}.toml
    ├── docker/
    │   ├── topology.toml
    │   └── nodes/{cloud,fog,mist,edge,iot}.toml
    └── physical/
        ├── topology.toml
        └── nodes/{cloud,fog,mist,edge,iot}.toml
```

Architecture manifests contain deployment properties and an ordered
`node_files` array. Tier files contain a `[layer]` table and zero or more
`[[nodes]]` tables. TOML has no native include statement; the project loader
implements this composition, resolves paths relative to the declaring file and
validates the effective document before execution.

The catalog currently exposes:

- `monolith`: exactly one local cloud process used as the baseline;
- `docker`: local containers generated dynamically with Compose;
- `physical`: a local coordinator plus SSH-managed remote hosts.

Do not edit generated `outputs/runtime/docker-compose-*.yml` or
`outputs/physical/runtime/active-topology.toml`. The old
`configs/physical-nodes.toml` exists only for legacy `--inventory` campaigns.

## Node contract

Each node has an identity independent of its tier:

| Field | Required | Meaning |
|---|---:|---|
| `id` | yes | Stable unique lowercase identity and service name |
| `endpoint` | yes | Absolute coordinator-visible HTTP(S) URL |
| `host` | recommended | Host used for listener and SSH validation |
| `port` | yes | Coordinator-visible or physical listener port |
| `local` | yes | Whether a physical process runs on the coordinator |
| `authority` | yes | Whether the node may hold sensitive ABox resources |
| `categories` | no | Query affinities; defaults are inherited from the tier |
| `enabled` | no | Temporarily removes a node when set to `false` |
| `cpus` | Docker | Positive Compose CPU limit |
| `memory` | Docker | Compose memory limit such as `1g` or `768m` |
| `container_port` | Docker | Internal worker port, normally 8080 |

The surrounding `[layer]` supplies `tier`, which must be `cloud`, `fog`,
`mist`, `edge` or `iot`. A node entry that tries to declare a different tier
is rejected. This prevents a copied edge node from silently remaining in a fog
file with contradictory metadata.

Validation rejects:

- invalid or duplicate IDs;
- duplicate enabled endpoints;
- unsupported categories;
- malformed URLs, ports, CPU or memory limits;
- duplicate Docker host ports;
- duplicate physical host/port listeners;
- distributed topologies without a cloud or privacy authority;
- physical topologies without a local coordinator;
- unsafe remote deployment paths;
- missing, duplicate or circular includes;
- mixed v1/v2 manifest forms.

The monolithic topology has the additional invariant of exactly one enabled,
local, cloud-tier node.

## Inspect and validate

Run these commands after every edit:

```bash
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench topology show --name monolith
.venv/bin/continuum-bench topology show --name docker
.venv/bin/continuum-bench topology show --name physical
```

Output includes the architecture source file, enabled node count by tier and a
SHA-256 fingerprint. The fingerprint covers every field that affects placement
or routing. Workers publish it at `/health`, and coordinators reject stale or
mismatched workers before timing starts.

## Configure the monolithic baseline

Edit only `configs/topologies/monolith/nodes/cloud.toml`. The other tier files
are intentionally empty so all architectures retain the same directory shape.
Do not add active fog, mist, edge or IoT nodes to the monolith; doing so would
remove the one-node baseline required for scientific comparisons.

The `benchmark`, `load monolith` and `experiment ... monolith` runners validate
this manifest. Cumulative and scalability `metadata.json` files contain its
source, node count and fingerprint.

## Add Docker nodes

Edit the file belonging to the new node's tier. For example,
`configs/topologies/docker/nodes/mist.toml` may contain:

```toml
[layer]
tier = "mist"

[[nodes]]
id = "mist1"
endpoint = "http://127.0.0.1:8196"
host = "127.0.0.1"
port = 8196
container_port = 8080
local = true
authority = false
cpus = 0.75
memory = "768m"

[[nodes]]
id = "mist2"
endpoint = "http://127.0.0.1:8197"
host = "127.0.0.1"
port = 8197
container_port = 8080
local = true
authority = false
cpus = 0.75
memory = "768m"
```

Render and start the effective topology:

```bash
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench topology render --name docker
.venv/bin/continuum-bench topology up --name docker
.venv/bin/continuum-bench topology status --name docker
.venv/bin/continuum-bench docker all
.venv/bin/continuum-bench topology down --name docker
```

The default generated path is
`outputs/runtime/docker-compose-docker.yml`. Both `up` and `down` use
`--remove-orphans`, so disabling or deleting a node does not leave its previous
container running. The repository-root `docker-compose.yml` is a compatibility
snapshot of the initial five nodes, not the elastic source of truth.

## Add physical nodes

Install Python 3.11+, `python3-venv`, OpenSSH server, `rsync` and `procps` on
the new host. Then add it to the appropriate physical tier file. Example
`configs/topologies/physical/nodes/iot.toml`:

```toml
[layer]
tier = "iot"

[[nodes]]
id = "iot-south-01"
host = "192.168.1.141"
endpoint = "http://192.168.1.141:8391"
local = false
port = 8391
authority = true
enabled = true
categories = ["observability", "identity_consent", "context_zones"]
```

Authorize, deploy and verify:

```bash
.venv/bin/continuum-bench topology validate
.venv/bin/continuum-bench physical authorize --ssh-user pi
.venv/bin/continuum-bench physical deploy --ssh-user pi
.venv/bin/continuum-bench physical start --ssh-user pi
.venv/bin/continuum-bench physical status --ssh-user pi
```

Preparation is deduplicated by host. Multiple logical nodes may share a host
only when their listeners differ. PID and log paths are separated by node ID.

`deploy` flattens the selected composed topology into the self-contained
`runtime/active-topology.toml` sent to every remote. The generated snapshot has
the same fingerprint as the source. Remote workers therefore do not depend on
relative includes and cannot accidentally use a different topology revision.

## Placement, privacy and routing

`configs/ontology-placement.toml` selects TBox profiles by tier. The sensitive
ABox is partitioned among every node with `authority=true` using one
deterministic function shared by partitioning and routing.

Authorities are ordered by tier (`cloud`, `fog`, `mist`, `edge`, `iot`) and
then by ID. Reordering TOML text does not change ownership. Adding or removing
an authority does change ownership and the topology fingerprint, so it defines
a new experimental condition.

`queries/execution-plan.toml` supports elastic scopes:

- a tier name selects a deterministic replica from that tier;
- `authorities` queries every authority and merges with the declared strategy;
- `authority_key:IRI` selects the owner of a specific resource;
- `cloud_authorities` and `all` express explicit federation;
- `node:ID` is a deliberate affinity to one identity.

Every worker publishes ID, tier, authority status, categories, protocol and
fingerprint. Distributed CSV files record both node identity and tier.

## Resize scientific profiles

Adding nodes does not automatically add experimental points. Update:

- `configs/experiments.toml`, `scale_out.node_counts`;
- `configs/load-benchmark.toml`, the `node_count` profiles.

Both loaders accept any positive integer and fail before measurement when a
profile requests more nodes than the selected topology exposes. Reports derive
node IDs dynamically and compute scale-out efficiency using the recorded node
count, not a hard-coded value.

## Create another architecture variant

Copy an architecture directory, change `topology.name`, endpoints and nodes,
then add its `topology.toml` to `manifest.topology_files` in the root catalog.
Alternatively, supply a standalone catalog before the subcommand:

```bash
.venv/bin/continuum-bench \
  --topology-file configs/lab/topology.toml \
  topology validate

.venv/bin/continuum-bench \
  --topology-file configs/lab/topology.toml \
  docker all --topology-name docker-lab
```

Legacy `--endpoints` and `--inventory` overrides remain for reproduction of old
campaigns. Composed manifests are the recommended workflow for new runs.
