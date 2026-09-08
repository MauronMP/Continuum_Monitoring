# Scientific validity and limitations

This repository provides a reproducible validation and performance
infrastructure for a modular monitoring ontology on a native monolith, local
containers and real continuum nodes. It is
not an ontology standard, accreditation procedure or formal certification.
Passing the suite supports only the structural, functional and performance
claims that are explicitly tested.

## Validation layers

The complete suite evaluates complementary concerns:

1. RDF/Turtle parsing and graph loading;
2. RDFS and OWL RL materialisation plus detection of `owl:Nothing`
   membership;
3. SHACL constraints and violation queries;
4. functional competency through the 115-query catalog traced to requirements
   and policies;
5. cumulative category activation;
6. synthetic-volume scalability with right-censored timeouts;
7. exact result preservation for the authority-partitioned physical layout;
8. isolated reasoning-hardware measurements for each physical node;
9. query scale-out with calibrated replica scheduling;
10. independent product behaviour in RDFLib, Jena, RDF4J and Oxigraph;
11. OWL 2 DL consistency with HermiT, Openllet, JFact and Konclude.

Absence of an inferred `owl:Nothing` member alone does not prove complete OWL
2 DL consistency. The separate Protégé workflow remains the appropriate tool
for deep DL inspection. See [Protégé and OWL consistency](ONTOLOGY_PROTEGE.md).

## Supported claims

When prerequisites and equivalence checks pass, results can support bounded
statements such as:

- the tested release parses and satisfies the implemented structural checks;
- the reference data produce the catalog's expected observable SPARQL
  outcomes;
- a physical node or tier had lower latency, higher throughput, fewer
  timeouts, or lower resource cost than another for the matched workload;
- query replicas scaled to the tested node count with the reported efficiency;
- authority-partitioned execution preserved or failed to preserve the canonical
  logical graph results under the declared execution plan.

Every claim must name the release, reasoner profile, topology, workload,
repetitions, timeout policy and hardware environment.

## Unsupported claims

The current suite cannot establish by itself:

- universal superiority of any continuum architecture;
- compliance with every possible interpretation of the requirements or
  policies;
- complete OWL 2 DL behaviour from RDFS/OWL RL benchmark timings;
- energy efficiency without external power measurements;
- production availability under arbitrary operating-system, network or device
  failures;
- statistical significance from a one-repetition smoke run.

## Timeouts and censored observations

Timeouts are right-censored observations. Figures that aggregate completed runs
must be accompanied by completion coverage and timeout rates. A zero must never
be substituted for a censored latency or inference time.

## Publication controls

Record and, where possible, fix all of the following:

- Git commit and clean/dirty state;
- ontology revision, graph hash, query-catalog hash and topology fingerprint;
- Python, RDFLib, OWL-RL and pyoxigraph versions;
- external OWL 2 DL consistency evidence from HermiT, Openllet, JFact and
  Konclude when those independently installed engines are available;
- host and node hardware, processor width, operating system, memory, storage
  and network topology;
- synthetic seed, workload profile, timeout values, repetitions and warm-ups;
- background load, thermal stabilisation and node availability;
- all failures, retries and excluded observations.

Performance statements require semantic equivalence first. A faster result with
incorrect answers is a failed run, not a speedup.
