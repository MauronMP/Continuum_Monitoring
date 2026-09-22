"""Local native DL adapters implementing named-class-individual-v1.

Only the supplied graph is loaded; imported modules must be assembled by the caller.
No downloads, remote workers, or approximate reasoning fallbacks are used.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import signal
import math
import glob
import warnings
import subprocess
import tempfile
from time import perf_counter
import xml.etree.ElementTree as ET

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import OWL, RDF, RDFS, XSD

from .core.contracts import ReasoningResult

OWL_MATERIALIZATION_CONTRACT = "named-class-individual-v1"
ROOT = Path(__file__).resolve().parents[2]
FACTORIES = {
    "hermit": "org.semanticweb.HermiT.ReasonerFactory",
    "openllet": "openllet.owlapi.OpenlletReasonerFactory",
    "jfact": "uk.ac.manchester.cs.jfact.JFactFactory",
}
LINK = "http://www.owllink.org/owllink#"
OWL_NS = str(OWL)
ET.register_namespace("", LINK)
ET.register_namespace("owl", OWL_NS)


class MaterializationError(RuntimeError):
    """The requested backend could not produce a verified inferred graph."""


class InconsistentOntologyError(MaterializationError):
    """The backend found the supplied ontology inconsistent."""


def _classpath(name: str) -> str:
    key = "CONTINUUM_OWL_CLASSPATH" if name == "konclude" else f"CONTINUUM_{name.upper()}_CLASSPATH"
    filename = "owl-validation.classpath" if name == "konclude" else f"owl-validation-{name}.classpath"
    path = ROOT / ".runtime" / filename
    source = os.environ.get("CONTINUUM_OWL_CLASSPATH_SOURCE", "auto")
    if source not in {"auto", "environment"}:
        raise MaterializationError("CONTINUUM_OWL_CLASSPATH_SOURCE must be auto or environment")
    # Shell profiles may still export incomplete Protege/OSGi classpaths.
    # Prefer the project's isolated installation unless explicitly overridden.
    if source == "auto" and path.is_file():
        value = path.read_text().strip()
        origin = str(path)
    else:
        value = os.environ.get(key)
        origin = key
    if not value:
        raise MaterializationError(f"{name}: missing isolated classpath; run tools/install_owl_reasoners.py or set {key}")
    for entry in value.split(os.pathsep):
        if not entry or not glob.glob(entry):
            raise MaterializationError(f"{name}: invalid classpath entry {entry!r} from {origin}; run tools/install_owl_reasoners.py to repair the installation")
    return value


class MaterializationTimeoutError(TimeoutError, MaterializationError):
    """The explicit execution deadline expired; the process group was killed."""


def _run(command: list[str], deadline: float | None) -> subprocess.CompletedProcess:
    remaining = None if deadline is None else deadline - perf_counter()
    if remaining is not None and remaining <= 0:
        raise MaterializationTimeoutError("OWL materialization timed out")
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=True)
    except OSError as error:
        raise MaterializationError(f"Cannot execute OWL runtime: {error}") from error
    try:
        stdout, stderr = process.communicate(timeout=remaining)
    except BaseException as error:
        # Native helpers may spawn descendants. Terminate the whole isolated
        # session before temporary input/output files are removed.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        if isinstance(error, subprocess.TimeoutExpired):
            raise MaterializationTimeoutError("OWL materialization timed out") from error
        raise
    result = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    if result.returncode == 3 and "CONTINUUM_INCONSISTENT" in stderr:
        raise InconsistentOntologyError("Ontology is inconsistent")
    if result.returncode:
        raise MaterializationError(f"OWL runtime exit {result.returncode}: {(stdout + stderr)[-4000:]}")
    return result


def _konclude(converted: Path, directory: Path, deadline: float | None) -> Graph:
    native = shutil.which(os.environ.get("CONTINUUM_KONCLUDE_EXECUTABLE", "Konclude"))
    if not native:
        raise MaterializationError("Native Konclude unavailable; install Konclude or set CONTINUUM_KONCLUDE_EXECUTABLE")
    ontology = ET.parse(converted).getroot()
    classes = sorted({e.attrib["IRI"] for e in ontology.iter(f"{{{OWL_NS}}}Class")})
    individuals = sorted({e.attrib["IRI"] for e in ontology.iter(f"{{{OWL_NS}}}NamedIndividual")})
    request = ET.Element(f"{{{LINK}}}RequestMessage")
    kb = "urn:continuum:materialization"
    ET.SubElement(request, f"{{{LINK}}}CreateKB", kb=kb)
    tell = ET.SubElement(request, f"{{{LINK}}}Tell", kb=kb)
    annotation_tags = {"Annotation", "AnnotationAssertion", "SubAnnotationPropertyOf", "AnnotationPropertyDomain", "AnnotationPropertyRange"}
    ignored_annotations = 0
    for axiom in ontology:
        local = axiom.tag.rsplit("}", 1)[-1]
        if local == "Prefix":
            continue
        if local in annotation_tags or (local == "Declaration" and any(e.tag == f"{{{OWL_NS}}}AnnotationProperty" for e in axiom)):
            ignored_annotations += 1
            continue
        # Axiom annotations have no OWL Direct Semantics meaning either.
        for parent in axiom.iter():
            for child in list(parent):
                if child.tag == f"{{{OWL_NS}}}Annotation":
                    parent.remove(child)
                    ignored_annotations += 1
        tell.append(axiom)
    if ignored_annotations:
        warnings.warn("Konclude does not parse annotations: excluded from its logical request, preserved verbatim in returned RDF graph", RuntimeWarning, stacklevel=2)
    ET.SubElement(request, f"{{{LINK}}}IsKBSatisfiable", kb=kb)
    queries = []
    for entities, operations, kind in (
        (classes, ("GetSuperClasses", "GetEquivalentClasses"), "Class"),
        (individuals, ("GetTypes", "GetSameIndividuals"), "NamedIndividual"),
    ):
        for entity in entities:
            for operation in operations:
                query = ET.SubElement(request, f"{{{LINK}}}{operation}", kb=kb)
                if operation in ("GetSuperClasses", "GetTypes"):
                    query.set("direct", "false")
                ET.SubElement(query, f"{{{OWL_NS}}}{kind}", IRI=entity)
                queries.append((operation, URIRef(entity)))
    input_file, output_file = directory / "request.xml", directory / "response.xml"
    ET.ElementTree(request).write(input_file, encoding="utf-8", xml_declaration=True)
    _run([native, "owllinkfile", "-w", "2", "-i", str(input_file), "-o", str(output_file)], deadline)
    responses = list(ET.parse(output_file).getroot())
    # A false consistency result takes precedence over subsequent query errors.
    if len(responses) >= 3 and responses[2].tag == f"{{{LINK}}}BooleanResponse" and responses[2].get("result") == "false":
        raise InconsistentOntologyError("Konclude: ontology is inconsistent")
    if (len(responses) != len(queries) + 3 or
            responses[2].tag != f"{{{LINK}}}BooleanResponse" or
            responses[2].get("result") != "true" or
            any(e.tag == f"{{{LINK}}}Error" for e in responses)):
        raise MaterializationError(f"Konclude returned an invalid/error response: {ET.tostring(ET.parse(output_file).getroot(), encoding='unicode')[-3000:]}")
    graph = Graph()
    expected = {"GetSuperClasses": "SetOfClassSynsets", "GetEquivalentClasses": "SetOfClasses", "GetTypes": "SetOfClassSynsets", "GetSameIndividuals": "IndividualSynonyms"}
    for (operation, subject), response in zip(queries, responses[3:]):
        if response.tag != f"{{{LINK}}}{expected[operation]}":
            raise MaterializationError(f"Konclude unexpected {operation} response: {response.tag}")
        kind = "NamedIndividual" if operation == "GetSameIndividuals" else "Class"
        for entity in response.iter(f"{{{OWL_NS}}}{kind}"):
            obj = URIRef(entity.attrib["IRI"])
            if operation == "GetSuperClasses":
                graph.add((subject, RDFS.subClassOf, obj))
            elif operation == "GetEquivalentClasses":
                graph.add((subject, RDFS.subClassOf, obj))
                if subject != obj:
                    graph.add((subject, OWL.equivalentClass, obj))
            elif operation == "GetTypes":
                graph.add((subject, RDF.type, obj))
            elif subject != obj:
                graph.add((subject, OWL.sameAs, obj))
    return graph


def _local_import_closure(source: Graph) -> Graph:
    """Require an explicitly assembled import closure; never read worker files.

    Import declarations are retained in returned RDF, but are not handed to
    OWLAPI's network import loader. The assembler supplies declared modules.
    """
    declared = set(source.subjects(RDF.type, OWL.Ontology))
    missing = set(source.objects(None, OWL.imports)) - declared
    if missing:
        raise MaterializationError(f"Unknown local OWL import {sorted(map(str, missing))}; imports must be flattened by the coordinator")
    expanded = Graph()
    for triple in source:
        expanded.add(triple)
    return expanded


@dataclass(frozen=True)
class NativeOWLReasoner:
    name: str
    timeout: float | None = None

    def materialize(self, source: Graph) -> ReasoningResult:
        if self.timeout is not None and (self.timeout <= 0 or not math.isfinite(self.timeout)):
            raise ValueError("Materialization timeout must be positive")
        expanded = _local_import_closure(source)
        object_properties = set(expanded.subjects(RDF.type, OWL.ObjectProperty))
        data_properties = set(expanded.subjects(RDF.type, OWL.DatatypeProperty))
        annotation_properties = set(expanded.subjects(RDF.type, OWL.AnnotationProperty))
        if (object_properties & data_properties or object_properties & annotation_properties or data_properties & annotation_properties):
            raise MaterializationError("Unsupported OWL 2 DL input: incompatible property declarations")
        if self.name == "konclude":
            if any(expanded.triples((None, OWL.hasKey, None))):
                raise MaterializationError("Konclude does not support HasKey axioms")
            if any(expanded.triples((None, XSD.pattern, None))):
                raise MaterializationError("Konclude does not support xsd:pattern facets")
        heap = os.environ.get("CONTINUUM_OWL_JAVA_HEAP", "2g")
        import re
        if not re.fullmatch(r"[1-9][0-9]*[kKmMgG]?", heap):
            raise MaterializationError("CONTINUUM_OWL_JAVA_HEAP must be a Java heap size such as 512m or 2g")
        started = perf_counter()
        deadline = None if self.timeout is None else started + self.timeout
        java = shutil.which(os.environ.get("JAVA", "java"))
        if not java:
            raise MaterializationError("Java 11+ unavailable; install the local OWL runtime")
        classpath = _classpath(self.name)
        try:
            with tempfile.TemporaryDirectory(prefix=f"continuum-{self.name}-") as temporary:
                directory = Path(temporary)
                input_file, output_file = directory / "input.rdf", directory / "output.rdf"
                reasoning_input = Graph()
                for triple in expanded:
                    if triple[1] != OWL.imports:
                        reasoning_input.add(triple)
                reasoning_input.serialize(input_file, format="xml")
                result = _run([java, f"-Xmx{heap}", "-cp", classpath, str(ROOT / "tools/owl/MaterializeOntology.java"), str(input_file), str(output_file), "convert" if self.name == "konclude" else FACTORIES[self.name]], deadline)
                if self.name == "konclude":
                    inferred = _konclude(output_file, directory, deadline)
                else:
                    if "CONTINUUM_MATERIALIZED" not in result.stdout.splitlines():
                        raise MaterializationError(f"{self.name}: missing materialization success marker")
                    inferred = Graph().parse(output_file, format="nt")
            graph = Graph()
            for prefix, namespace in source.namespaces():
                graph.bind(prefix, namespace)
            for triple in expanded:
                graph.add(triple)
            # OWLAPI serializers emit declarations and ontology headers; these
            # are not inferred facts in our shared contract.
            for s, p, o in inferred:
                if not isinstance(s, URIRef) or not isinstance(o, URIRef):
                    continue
                if p in (RDFS.subClassOf, OWL.equivalentClass, OWL.sameAs) or (p == RDF.type and o not in (OWL.Ontology, OWL.Class, OWL.NamedIndividual)):
                    graph.add((s, p, o))
                if p in (OWL.equivalentClass, OWL.sameAs):
                    graph.add((o, p, s))
            return ReasoningResult(graph=graph, duration_ms=(perf_counter()-started)*1000, input_triples=len(source), output_triples=len(graph))
        except (MaterializationError, TimeoutError):
            raise
        except Exception as error:
            raise MaterializationError(f"{self.name}: cannot materialize ontology: {error}") from error
