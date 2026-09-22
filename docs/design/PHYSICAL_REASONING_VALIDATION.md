# Physical reasoning validation

Validation date: 2026-09-21. Scope: coordinator code and installed native
reasoners. No remote physical device was contacted or started.

## Reproduction

From the repository root:

```bash
. .venv/bin/activate
. .runtime/owl-reasoners.env
CONTINUUM_TEST_NATIVE_OWL=1 python -m pytest -o addopts='' -q -ra \
  --junitxml=outputs/validation/readiness/final-tests.xml
python tools/check_documentation.py
continuum-bench physical prepare
python tools/verify_distributed_reasoning.py
```

The test suite requires permission to bind local loopback sockets. These tests
do not require the remote continuum devices.

## Evidence

- Full suite: 388 passed, 3 skipped, 147.55 seconds. Native HermiT, Openllet,
  JFact and Konclude tests were enabled.
- Two skipped parameter cases concern calibration that does not apply to the
  partitioned coordinator. One skipped test requires optional Graphviz.
- Three warnings explain Konclude annotation handling: annotations are excluded
  from its logical request and retained in the returned RDF graph.
- Documentation checker: 27 files passed link/generated-reference checks.
- Offline preparation: local files ready, remote devices not probed, deployment
  readiness false pending online verification.
- Retained offline semantic check: 115 queries for each of five reasoners,
  575 comparisons, zero mismatches, one synthetic user. This is a bounded
  correctness check, not a physical performance or scalability measurement.

Local generated evidence is stored in `outputs/validation/readiness/final-tests.log`,
`final-tests.xml`, `offline-readiness.json`, and `distributed-reasoning.json`.
These files are generated artifacts, not source-controlled benchmark evidence.

## Classpath regression verification

The inherited HermiT classpath pointed to Protégé OSGi bundles and failed to
load Caffeine during OWLAPI initialization. Native adapters now prefer the
project's installed isolated classpath. Explicit custom runtimes remain
available through `CONTINUUM_OWL_CLASSPATH_SOURCE=environment`; broken installed
classpaths fail rather than silently falling back. See
[runtime selection](OWL_REASONERS.md).

The full suite was rerun without sourcing `.runtime/owl-reasoners.env`, keeping
the inherited Protégé wildcard classpath and enabling native OWL tests:

```bash
CONTINUUM_TEST_NATIVE_OWL=1 .venv/bin/python -m pytest -o addopts='' -q -ra \
  --junitxml=outputs/validation/readiness/classpath-full-tests.xml
```

Result: 395 passed, 3 skipped, 3 expected Konclude annotation warnings in
143.38 seconds. The skips are the same two inapplicable calibration cases and
the optional Graphviz renderer described above. Evidence is retained in
`outputs/validation/readiness/classpath-full-tests.log` and `classpath-full-tests.xml`.

## Remaining limits

Remote OS/ABI compatibility, native Konclude availability on ARM, resource
capacity and network behavior require validation after devices are powered on.
No distributed deployment or remote performance claim follows from local tests.
Fragment reasoning is not a complete distributed OWL DL decision procedure;
new policies and queries require canonical-answer validation. Native memory
telemetry is a lifetime child high-water mark rather than a per-point process
tree peak. See [execution and reasoning contracts](PHYSICAL_REASONING.md).
