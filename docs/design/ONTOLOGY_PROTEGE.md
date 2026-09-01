# English ontology and Protégé validation

## Which file to open

Open `ontology/legacy/smartcity_continuum-v3.0.0.ttl` with **File → Open**.
Despite the historical directory name, this is the maintained, complete
canonical ontology: schema, controlled vocabularies, reference individuals,
requirements, policies, mechanisms, scenarios and embedded SHACL shapes. It
has no remote imports. Its ontology IRI and version remain
`http://example.org/smartcity` and `3.0.0`; the corrected artifact revision is
`3.0.0-en-datatypes-v1`, recorded as `dcterms:identifier`.

Stop any running Protégé reasoner and reopen the file from disk after updating
the repository. Do not save the previously loaded, stale ontology over the
corrected file. Select **Reasoner → HermiT → Start reasoner**. If your renderer
uses `rdfs:label`, labels are now English too.

`ontology/profiles/full.ttl` is an import profile, not a self-contained copy.
The benchmark loads its explicitly configured modules, including the additional
deployment module. Their stable skolem IRIs support distributed RDF identity;
open the canonical file, with native anonymous OWL structures, for editing in
Protégé. Do not overwrite modules by saving a Protégé rendering of them.

## Cause of the inconsistency

There were 116 assertions such as:

```turtle
:requirementStatement rdfs:range xsd:string .
:RF-22 :requirementStatement "A language-tagged statement"@es .
```

The range requires an XML Schema string, but a language-tagged RDF literal
has datatype `rdf:langString`. The two value spaces are incompatible here.
Merely replacing `@es` with `@en` leaves the same contradiction. See
[RDF 1.1 literal semantics](https://www.w3.org/TR/rdf11-concepts/#section-Graph-Literal).

The correction keeps the `xsd:string` requirement range and writes its English
content as untagged strings (equivalent to `xsd:string` in RDF 1.1). Policy
statements and mechanism descriptions also use English strings; their existing
`rdfs:Literal` ranges and SHACL alternatives remain compatible. Labels may use
English language tags when their property permits them. `dcterms:language`
declares the artifact language without changing the datatype of its values.

The translation covers 116 requirement statements, 79 policy statements,
55 mechanism descriptions and 151 policy/mechanism/scenario labels: 401 values.
Identifiers, numerical acceptance thresholds and normative references are
retained. The generated reference manuals expose the corrected English
executable content; historical source material is not loaded by Protégé.

## Additional OWL 2 DL corrections

The profile checker also found missing declarations and an invalid use of
reserved OWL vocabulary. These are corrected independently of the string clash:

- SHACL predicates are explicitly declared as OWL annotation properties and
  `sh:NodeShape` as a class. They remain SHACL constraints, not OWL enforcement
  rules. Existing shape triples and their validation behavior are preserved.
- `foaf:name` is explicitly a datatype property; `xsd:duration` is explicitly
  declared as a datatype. Duration arithmetic is not provided by this declaration.
- `appliesToZoneType` remains an object property, but its range is now the
  explicit class `ZoneType`, not the reserved metaclass `owl:Class`.
  `UrbanZone`, `RuralZone` and `RestrictedZone` retain their class meaning and
  existing IRIs; they are also named `ZoneType` individuals (OWL 2 punning).
  Class and individual interpretations are separate; this does not make zone
  policies automatically apply to every class instance. SPARQL/SHACL and the
  orchestrator still implement operational policy checks.

See [OWL 2 declarations and metamodeling](https://www.w3.org/TR/owl2-syntax/#Metamodeling).
The canonical file passes the OWLAPI OWL 2 DL profile check and HermiT reports
consistency with no unsatisfiable named classes. This does not certify runtime
security, policy enforcement or scientific acceptance.

## Reproducible checks

From the repository root, with the project Python environment installed:

```bash
# Regenerate runtime assets after editing the canonical source
.venv/bin/python tools/migrate_assets.py

# Datatype guards, 115 queries, SHACL, three entailment profiles and partitioning
.venv/bin/continuum-bench validate
.venv/bin/python -m pytest

# OWL 2 DL profile + HermiT consistency, outside timed benchmarks
python3 tools/check_owl_consistency.py --require-dl-profile \
  --output outputs/validation/ontology-english-hermit.json
```

The last command requires Java 11+ (Java 17 recommended) and an existing Protégé
installation with HermiT. It discovers the macOS application automatically.
On Linux or for a nonstandard installation:

```bash
python3 tools/check_owl_consistency.py \
  --protege-home /path/to/Protege \
  --require-dl-profile --timeout 180 \
  --output outputs/validation/ontology-english-hermit.json
```

Alternatively set `PROTEGE_HOME`, or pass `--classpath` containing compatible
OWLAPI, HermiT and dependency jars. `--java` selects a Java executable. No jars
are downloaded, no application files are changed, and temporary extracted
dependencies are removed automatically. Java/HermiT is an optional release
check: Python benchmarks and Raspberry Pi workers do not acquire this dependency.

The JSON report records file SHA-256, loaded axiom count, reasoner version,
consistency, unsatisfiable classes, profile violations and wall time. Exit codes:
`0` passed; `1` logical/profile failure; `2` missing dependencies, timeout or
execution error. A timeout means unknown consistency, not inconsistency. The
optional pytest integration skips when Protégé/Java is unavailable; select it
with `-m owl_consistency`.

`continuum-bench validate` explicitly reports OWL consistency as `not_checked`:
its inexpensive datatype guard and absence of explicit `owl:Nothing` instances
are necessary checks, not a substitute for HermiT. SHACL warnings and the
`EXT-Q76`/`EXT-Q77` scientific-acceptance debt remain separate.

## Existing Docker/physical deployments and results

Benchmark metadata and worker health now include
`ontology_revision=3.0.0-en-datatypes-v1`. The coordinator rejects stale workers;
reports reject earlier or mixed ontology revisions. Rebuild Docker images or
redeploy and restart physical workers before rerunning benchmarks. Keep old
results for provenance, but do not rename or relabel them as corrected runs.
See [Docker updates](DOCKER_BENCHMARKS.md#ext-q68-and-stale-images) and
[physical deployment](PHYSICAL_CONTINUUM.md).
