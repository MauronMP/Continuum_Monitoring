# Scientific validity and limitations

## Status of the benchmark

This repository provides a reproducible validation and performance
infrastructure. It is not an ontology standard, accreditation procedure, or
formal certification. Passing the suite supports only the explicitly tested
structural, functional, and performance claims.

The quality gate distinguishes structural validity from scientific acceptance.
RDF syntax, SHACL, query expectations, and selected reasoning checks can pass
while the documented acceptance evidence checked by EXT-Q76 and EXT-Q77 remains
incomplete. A structurally executable ontology must not therefore be described
as fully policy-certified.

## Validation layers

The repository evaluates complementary concerns:

1. RDF/Turtle parsing and graph loading;
2. RDFS and OWL RL materialization plus detection of `owl:Nothing` membership;
3. closed-world SHACL constraints and violation queries;
4. functional competency through 115 queries traced to requirements and
   policies;
5. cumulative and synthetic-volume performance;
6. exact or declared-level result equivalence across monolith, Docker, and
   physical deployments;
7. cross-engine behavior with Apache Jena, Eclipse RDF4J, and RDFLib/OWL-RL
   under RDFS, plus Oxigraph as a no-inference control;
8. OWL 2 DL profile and HermiT consistency checks outside benchmark timing.

Absence of an inferred `owl:Nothing` member alone does not prove OWL
consistency. The separate checker also inspects datatype conflicts and invokes
HermiT when its pinned artifact is available. HermiT time is excluded from
performance measurements. See [Protégé and OWL consistency](ONTOLOGY_PROTEGE.md).

The general design follows established benchmark principles: deterministic
scalable data generation, a fixed SPARQL workload, explicit metrics,
per-repetition results, environment metadata, and separation between system,
workload, validation, and analysis. It is conceptually comparable to LUBM,
SP2Bench, WatDiv, and HOBBIT, but it is not an implementation of those suites.

## Claims the current suite can support

When all prerequisites and equivalence checks pass, the data can support
bounded statements such as:

- the tested release parses and satisfies the implemented structural checks;
- the reference data produce the catalog's expected observable SPARQL outcomes;
- one configured architecture had lower measured latency or higher throughput
  than another for the matched workload and environment;
- query replicas scaled to the tested node count with the reported efficiency;
- individual devices differed in materialization time for the same graph;
- an authority-partitioned deployment preserved or failed to preserve the
  monolithic oracle results under the declared execution plan.

Every statement must name the release, reasoner or product, architecture,
placement layout, profile, repetitions, and hardware environment.

## Claims the current suite cannot establish by itself

- universal superiority of a continuum architecture;
- compliance with every possible interpretation of the requirements or
  policies;
- complete OWL 2 DL behavior from RDFS/OWL RL tests;
- energy efficiency without power measurements;
- production availability or recovery from operating-system, network, daemon,
  container, or device failure;
- statistical significance from a one-repetition smoke;
- performance on arbitrary ontologies, queries, or data distributions;
- full SPARQL federation interoperability with third-party endpoints.

## Known limitations and required disclosure

### Statistical design

Three full repetitions provide a minimal variability check but are usually too
few for strong inferential statistics. Product-engine runs exclude one warm-up
by default. A paper must justify repetition and warm-up counts, randomization or
execution order, and the selected summary/statistical method. Pre-register the
analysis where practical.

Smoke tests have one repetition and validate integration only. Minimum-maximum
ranges are descriptive and must not be called confidence intervals.

### Resource measurements

The load benchmark records process CPU, current/peak RSS, process I/O, JSON body
bytes, timeouts, and loss. These do not replace energy, temperature, complete
host or cgroup telemetry, or link-level network capture. Distributed speedup
can coexist with higher aggregate resource consumption.

### Workload coverage

The synthetic generator independently scales users, triples, and rules, but it
does not independently scale every ontology population. Query-shape and
selectivity coverage is not yet a formal WatDiv-style matrix of star, chain,
snowflake, OPTIONAL/UNION, aggregation, and cardinality classes.

Direct query traceability currently covers 102 of 116 requirements and 69 of 79
policies. `validate` publishes the uncovered identifiers. Until the query
battery is extended, do not claim 100 percent SPARQL traceability.

### Ontology and release

The publication namespace still uses `example.org` and should be replaced by a
persistent IRI before external release. The v3 reference ABox retains documented
SHACL warnings and does not yet satisfy all EXT-Q76/EXT-Q77 scientific
acceptance evidence. These are disclosed gates, not runtime defects to hide.

### Entailment variation

Independent RDFS implementations need not materialize identical axiomatic or
datatype triples. Cross-engine conformance therefore uses the mandatory
observable decision—identical `ASK` or zero/non-zero row class—while retaining
exact cardinality as a diagnostic. RDFLib architecture comparisons additionally
use an order-independent digest of the canonical binding bag.

The OWL RL and combined profiles use the OWL-RL/RDFLib implementation; there is
not yet a multi-product OWL 2 RL comparison.

### Distributed-system scope

Docker and physical deployments support complete replicas and a project-defined
authority layout. The latter places ABox data by authority, retains required
TBox modules locally, and applies policy-aware projections. It is not a generic
SPARQL 1.1 Federation implementation.

Docker containers share one kernel and physical host. They model placement and
concurrency but not independent hardware, failure domains, or physical network
links. Physical results depend on each node's CPU architecture, memory, storage,
temperature, network, and background services.

### Timeouts and missing data

Timeouts are right-censored observations. Figures that aggregate completed runs
must be accompanied by completion coverage and timeout rates. Silently dropping
timeouts biases results toward the architecture that fails most often. A zero
must never be substituted for a censored latency or inference time.

## Experimental controls for a publication run

Record and, where possible, fix all of the following:

- Git commit and clean/dirty state;
- ontology revision, graph hash, query-catalog hash, and execution-plan hash;
- Python, Java, Docker, Compose, Jena, RDF4J, RDFLib, OWL-RL, and Oxigraph
  versions;
- host and node hardware, processor width, operating system, kernel, memory,
  storage, and network topology;
- container CPU, memory, and Java heap limits;
- topology manifests and enabled node order;
- synthetic seed, workload profile, timeout values, repetitions, and warm-ups;
- cache state and run order;
- background load and thermal stabilization procedure;
- all failures, retries, and excluded observations.

Use the same logical dataset and semantic contract across matched comparisons.
Do not compare historical result schemas with current exact-digest results
without explicitly downgrading the validation claim.

## Figure interpretation

The publication figures use the median and minimum-maximum range of available
complete repetitions. The experimental unit is one complete repetition of the
same release, logical dataset, reasoner, and query set. A no-inference control,
an RDFS reasoner, a complete replica, and an authority fragment are different
treatments and must be labelled as such.

Performance statements require semantic equivalence first. A faster result with
incorrect answers is a failed run, not a speedup.

## Primary references

- [W3C RDF 1.1 Concepts and Abstract Syntax](https://www.w3.org/TR/rdf11-concepts/)
- [W3C SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/)
- [W3C OWL 2 Web Ontology Language Profiles](https://www.w3.org/TR/owl2-profiles/)
- [W3C Shapes Constraint Language (SHACL)](https://www.w3.org/TR/shacl/)
- [Guo, Pan, and Heflin: LUBM](https://swat.cse.lehigh.edu/pubs/guo05a.pdf)
- [Schmidt et al.: SP2Bench](https://arxiv.org/abs/0806.4627)
- [Aluc et al.: WatDiv](https://olafhartig.de/files/AlucEtAl_ISWC14_Preprint.pdf)
- [Roeder et al.: HOBBIT](https://journals.sagepub.com/doi/10.3233/DS-190021)
