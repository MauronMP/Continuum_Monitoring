"""Native execution tests opt in via CONTINUUM_TEST_NATIVE_OWL=1."""
import os
from pathlib import Path
import sys
import time

import pytest
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, RDFS, OWL

from continuum_bench import owl_materialization as native
from continuum_bench.reasoners import (
    available_reasoners, materialize, reasoner_contract, reasoner_readiness,
    REASONING_CONTRACT,
)

EX = Namespace("urn:materialization:test:")
NAMES = ("hermit", "openllet", "jfact", "konclude")
PREFIX = '''@prefix : <urn:materialization:test:> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
'''


def fixture():
    return Graph().parse(data=PREFIX + '''
:A a owl:Class; rdfs:subClassOf :B . :B a owl:Class .
:C a owl:Class; owl:equivalentClass [ a owl:Restriction; owl:onProperty :p; owl:someValuesFrom :B ] .
:p a owl:ObjectProperty . :a a owl:NamedIndividual; :p :b; rdfs:label "retained" .
:b a :A . :c a owl:NamedIndividual; owl:sameAs :a .
''', format="turtle")


def test_public_defaults_and_contracts():
    assert available_reasoners() == ("rdfs", *NAMES)
    assert reasoner_contract("rdfs") == REASONING_CONTRACT
    assert {reasoner_contract(n) for n in NAMES} == {"named-class-individual-v1"}
    assert native.NativeOWLReasoner("hermit").timeout is None
    assert materialize(Graph(), "owlrl").graph is not None


@pytest.mark.parametrize("name", NAMES)
def test_missing_runtime_no_fallback(name, monkeypatch):
    monkeypatch.setenv("JAVA", "/missing/java")
    with pytest.raises(native.MaterializationError, match="Java"):
        materialize(Graph(), name)
    readiness = reasoner_readiness(name)
    assert not readiness["runtime_present"]
    assert not readiness["execution_verified"]


@pytest.mark.parametrize("name", NAMES)
def test_imports_rejected_before_execution(name):
    graph = Graph()
    graph.add((EX.ontology, OWL.imports, EX.remote))
    with pytest.raises(native.MaterializationError, match="flattened"):
        materialize(graph, name)


def test_explicit_bad_classpath(monkeypatch):
    monkeypatch.setenv("CONTINUUM_OWL_CLASSPATH_SOURCE", "environment")
    monkeypatch.setenv("CONTINUUM_HERMIT_CLASSPATH", "/no/such.jar")
    with pytest.raises(native.MaterializationError, match="invalid classpath"):
        native._classpath("hermit")


@pytest.mark.parametrize("name", NAMES)
def test_installed_classpath_wins_over_stale_shell(name, monkeypatch, tmp_path):
    monkeypatch.setattr(native, "ROOT", tmp_path)
    monkeypatch.delenv("CONTINUUM_OWL_CLASSPATH_SOURCE", raising=False)
    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    jar = tmp_path / "isolated.jar"
    jar.touch()
    filename = "owl-validation.classpath" if name == "konclude" else f"owl-validation-{name}.classpath"
    (runtime / filename).write_text(str(jar))
    key = "CONTINUUM_OWL_CLASSPATH" if name == "konclude" else f"CONTINUUM_{name.upper()}_CLASSPATH"
    monkeypatch.setenv(key, "/opt/protege/bundles/*:/opt/protege/plugins/*")
    assert native._classpath(name) == str(jar)
    monkeypatch.setenv("CONTINUUM_OWL_CLASSPATH_SOURCE", "environment")
    monkeypatch.setenv(key, "/missing/custom.jar")
    with pytest.raises(native.MaterializationError, match="invalid classpath"):
        native._classpath(name)
    custom = tmp_path / "custom.jar"
    custom.touch()
    monkeypatch.setenv(key, str(custom))
    assert native._classpath(name) == str(custom)


def test_environment_classpath_without_installation(monkeypatch, tmp_path):
    monkeypatch.setattr(native, "ROOT", tmp_path)
    monkeypatch.delenv("CONTINUUM_OWL_CLASSPATH_SOURCE", raising=False)
    jar = tmp_path / "custom.jar"
    jar.touch()
    monkeypatch.setenv("CONTINUUM_HERMIT_CLASSPATH", str(jar))
    assert native._classpath("hermit") == str(jar)


def test_corrupt_installation_does_not_fall_back(monkeypatch, tmp_path):
    monkeypatch.setattr(native, "ROOT", tmp_path)
    monkeypatch.delenv("CONTINUUM_OWL_CLASSPATH_SOURCE", raising=False)
    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    (runtime / "owl-validation-hermit.classpath").write_text("/missing/installed.jar")
    jar = tmp_path / "custom.jar"
    jar.touch()
    monkeypatch.setenv("CONTINUUM_HERMIT_CLASSPATH", str(jar))
    with pytest.raises(native.MaterializationError, match="invalid classpath"):
        native._classpath("hermit")


def test_timeout_kills_descendants(tmp_path):
    marker = tmp_path / "escaped"
    child = f"import time;from pathlib import Path;time.sleep(0.5);Path({str(marker)!r}).write_text('bad')"
    parent = f"import subprocess,sys,time;subprocess.Popen([sys.executable,'-c',{child!r}]);time.sleep(10)"
    with pytest.raises(TimeoutError):
        native._run([sys.executable, "-c", parent], time.perf_counter() + 0.15)
    time.sleep(0.6)
    assert not marker.exists()


def test_unlimited_process():
    assert native._run([sys.executable, "-c", "print('done')"], None).stdout.strip() == "done"


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.skipif(os.environ.get("CONTINUUM_TEST_NATIVE_OWL") != "1", reason="requires installed local native runtimes")
def test_real_inference_and_inconsistency(name):
    source = fixture()
    before = set(source)
    result = native.NativeOWLReasoner(name, 30).materialize(source)
    assert set(source) == before
    assert before <= set(result.graph)
    assert (EX.a, RDF.type, EX.C) in result.graph  # Existential restriction inference.
    assert (EX.c, RDF.type, EX.C) in result.graph  # sameAs propagation.
    assert (EX.b, RDF.type, EX.B) in result.graph
    assert bool(result.graph.query('ASK { <urn:materialization:test:a> a <urn:materialization:test:C> }'))
    assert result.input_triples == len(source)
    assert result.output_triples == len(result.graph)
    assert result.duration_ms > 0
    source.add((EX.A, OWL.disjointWith, EX.B))
    with pytest.raises(native.InconsistentOntologyError):
        native.NativeOWLReasoner(name, 30).materialize(source)


@pytest.mark.skipif(os.environ.get("CONTINUUM_TEST_NATIVE_OWL") != "1", reason="requires installed local native runtimes")
def test_native_contract_graph_equivalence():
    # Reuse one graph to preserve source blank-node identifiers.
    source = fixture()
    graphs = [set(native.NativeOWLReasoner(name, 30).materialize(source).graph) for name in NAMES]
    assert all(g == graphs[0] for g in graphs[1:])


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.skipif(os.environ.get("CONTINUUM_TEST_NATIVE_OWL") != "1", reason="requires installed local native runtimes")
def test_invalid_dl_not_rewritten(name):
    source = Graph().parse(data=PREFIX + ':p a owl:ObjectProperty, owl:DatatypeProperty .', format="turtle")
    with pytest.raises(native.MaterializationError):
        native.NativeOWLReasoner(name, 30).materialize(source)


def test_konclude_unsupported_key_and_datatypes():
    for data, message in ((":A owl:hasKey (:p) .", "HasKey"), (':range <http://www.w3.org/2001/XMLSchema#pattern> "x" .', "pattern")):
        source = Graph().parse(data=PREFIX + data, format="turtle")
        with pytest.raises(native.MaterializationError, match=message):
            materialize(source, "konclude")
