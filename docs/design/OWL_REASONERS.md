# External OWL reasoner validation

Timed monitoring benchmarks use the portable RDFS and OWL RL materialisers.
OWL 2 DL consistency is a separate validation task because tableau reasoners
do not perform the same operation and their timings must not be mixed with
forward-materialisation measurements.

The external validation suite is configured in `configs/owl-reasoners.toml`
and supports HermiT, Openllet, JFact and Konclude. No third-party binaries or
JAR files are committed. A missing dependency is reported as `unavailable`,
never as a successful consistency result.

## HermiT

Install Protégé with its HermiT plugin, set `PROTEGE_HOME` when it cannot be
discovered automatically, or provide an explicit classpath:

```bash
export CONTINUUM_HERMIT_CLASSPATH=/path/to/owlapi-and-hermit-jars
```

## Openllet and JFact

Install Maven and generate the pinned validation classpath:

```bash
mkdir -p .runtime
mvn -f tools/owl/pom.xml dependency:build-classpath \
  -Dmdep.outputFile=../../.runtime/owl-validation.classpath
OWL_VALIDATION_CP=$(cat .runtime/owl-validation.classpath)
export CONTINUUM_OPENLLET_CLASSPATH="$OWL_VALIDATION_CP"
export CONTINUUM_JFACT_CLASSPATH="$OWL_VALIDATION_CP"
```

Alternatively, provide classpaths containing OWLAPI, the selected reasoner and
all transitive dependencies directly:

```bash
export CONTINUUM_OPENLLET_CLASSPATH=/path/to/openllet/classpath
export CONTINUUM_JFACT_CLASSPATH=/path/to/jfact/classpath
```

## Konclude

Install the `Konclude` executable and ensure it is on `PATH`. Its command and
machine-readable output patterns can be changed in `configs/owl-reasoners.toml`
without modifying Python.

## Execute

Inspect the local prerequisites first:

```bash
continuum-bench doctor --owl
```

Run all available reasoners:

```bash
continuum-bench owl-validate
```

Require all four engines to be installed, to finish before their timeout and
to report a consistent ontology with no unsatisfiable named classes:

```bash
continuum-bench owl-validate --require-all
```

The evidence file is `outputs/validation/owl-reasoners.json`. Each record
contains availability, consistency, OWL 2 DL profile status, unsatisfiable
classes, elapsed time and diagnostic detail. External reasoner results validate
logical consistency; they do not replace SHACL, SPARQL competency questions or
the scientific-acceptance gate.
