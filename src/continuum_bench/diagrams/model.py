"""Extract asserted schema, never inferred or guessed domain/range relations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from pathlib import Path
import re
from typing import Any

from rdflib import BNode, Graph, Literal, OWL, RDF, RDFS, URIRef
from rdflib.namespace import DCTERMS

from ..config import BenchmarkConfig


EX = "http://example.org/smartcity#"
SKOLEM = "urn:continuum:ontology:"
MODULES = {
    "foundation": ("Foundation", "#DDEBF7", "#0072B2"),
    "topology": ("Topology", "#E2F1EC", "#009E73"),
    "observability": ("Observability", "#E1F3FB", "#56B4E9"),
    "governance": ("Governance", "#FCEDD2", "#E69F00"),
    "orchestration": ("Orchestration", "#F1E3EF", "#AA5F97"),
    "federation": ("Federated learning", "#F9E7DE", "#D55E00"),
    "deployment": ("Deployment", "#EFEDCC", "#8A821A"),
    "wellbeing": ("Wellbeing (optional)", "#E9E4F4", "#7160A0"),
    "standards": ("External standards / SHACL", "#ECEFF1", "#59636B"),
}
KINDS = {
    OWL.Class: "class", OWL.ObjectProperty: "object_property",
    OWL.DatatypeProperty: "datatype_property",
    OWL.AnnotationProperty: "annotation_property", RDFS.Datatype: "datatype",
}
AXIOMS = {
    RDFS.subClassOf: "subclass", RDFS.subPropertyOf: "subproperty",
    OWL.equivalentClass: "equivalent_class", OWL.equivalentProperty: "equivalent_property",
    OWL.disjointWith: "disjoint", OWL.inverseOf: "inverse",
    RDFS.domain: "domain", RDFS.range: "range",
}


@dataclass
class Node:
    id: str
    qname: str
    label: str
    kind: str
    module: str
    comment: str = ""
    sources: list[str] = field(default_factory=list)
    punned: bool = False


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    kind: str
    predicate: str
    index: int = -1


@dataclass
class Property:
    id: str
    qname: str
    label: str
    kind: str
    module: str
    domains: list[str]
    ranges: list[str]
    characteristics: list[str]


@dataclass
class Schema:
    nodes: dict[str, Node]
    edges: list[Edge]
    properties: list[Property]
    sources: list[dict[str, str]]
    source_triples: int
    prefixes: dict[str, str]
    identity: dict[str, list[str]] = field(default_factory=dict)

    def text(self, identifier: str, seen: frozenset[str] = frozenset()) -> str:
        if identifier in seen:
            raise ValueError(f"Cyclic schema expression: {identifier}")
        node = self.nodes[identifier]
        members = sorted((edge for edge in self.edges if edge.source == identifier
                          and edge.kind in {"union_member", "intersection_member"}),
                         key=lambda edge: edge.index)
        if not members:
            return node.qname
        operator = " OR " if members[0].kind == "union_member" else " AND "
        return "(" + operator.join(self.text(edge.target, seen | {identifier})
                                    for edge in members) + ")"

    def constraints(self, values: list[str]) -> str:
        return " AND ".join(self.text(value) for value in values) or "not declared"

    def export(self) -> dict[str, Any]:
        classes = [node for node in self.nodes.values() if node.kind == "class"]
        return {
            "schema_version": 1,
            "scope": "Asserted conceptual schema (TBox), not an ABox instance graph",
            "counts": {
                "named_classes": len(classes),
                "anonymous_expressions": sum(n.kind == "expression" for n in self.nodes.values()),
                **{kind.replace("property", "properties"): sum(p.kind == kind for p in self.properties)
                   for kind in ("object_property", "datatype_property", "annotation_property")},
                "subclass_axioms": sum(e.kind == "subclass" for e in self.edges),
                "source_triples": self.source_triples,
            },
            "sources": self.sources,
            "prefixes": self.prefixes,
            "identity": self.identity,
            "nodes": [asdict(node) for node in sorted(self.nodes.values(), key=lambda n: n.id)],
            "edges": [asdict(edge) for edge in self.edges],
            "properties": [dict(asdict(p), domain_text=self.constraints(p.domains),
                                range_text=self.constraints(p.ranges)) for p in self.properties],
        }


def _module(path: Path, identifier: str) -> str:
    if not identifier.startswith((EX, SKOLEM, "_:")):
        return "standards"
    if "wellbeing" in path.parts:
        return "wellbeing"
    if path.parent.name == "modules":
        return path.stem
    return "foundation"


def extract_schema(config: BenchmarkConfig) -> Schema:
    graph = Graph()
    ownership: dict[str, list[str]] = {}
    modules: dict[str, str] = {}
    sources = []
    for relative in config.ontology_files:
        path = config.resolve(relative)
        part = Graph().parse(path, format="turtle")
        graph += part
        sources.append({"path": str(relative), "sha256": sha256(path.read_bytes()).hexdigest()})
        for subject, type_ in part.subject_objects(RDF.type):
            if type_ in KINDS:
                identifier = str(subject)
                ownership.setdefault(identifier, []).append(str(relative))
                modules.setdefault(identifier, _module(relative, identifier))
    graph.bind("ex", URIRef(EX), replace=True)
    # RDFLib does not prebind the HTTPS SAREF namespace used by this ontology.
    # A display prefix avoids long URI labels without changing the underlying IRI.
    graph.bind("saref", URIRef("https://saref.etsi.org/core/"), replace=True)
    prefixes = {str(prefix): str(namespace) for prefix, namespace in graph.namespaces()}
    nodes: dict[str, Node] = {}
    edges: set[Edge] = set()

    def add(term: object, default_kind: str = "reference") -> str:
        identifier = str(term)
        if identifier in nodes:
            return identifier
        anonymous = isinstance(term, BNode) or identifier.startswith(SKOLEM)
        types = set(graph.objects(term, RDF.type))
        kind = next((value for key, value in KINDS.items() if key in types), default_kind)
        if anonymous:
            kind = "expression"
        qname = ("expression-" + sha256(identifier.encode()).hexdigest()[:8]
                 if anonymous else graph.namespace_manager.normalizeUri(term))
        labels = sorted(graph.objects(term, RDFS.label),
                        key=lambda value: (getattr(value, "language", None) != "en", str(value)))
        comments = sorted(str(value) for value in graph.objects(term, RDFS.comment))
        fallback = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ",
                          qname.split(":")[-1])
        if kind.endswith('_property'):
            fallback = fallback.lower()
        nodes[identifier] = Node(
            identifier, qname, str(labels[0]) if labels else fallback,
            kind, modules.get(identifier, "standards"), " ".join(comments),
            sorted(ownership.get(identifier, [])), OWL.NamedIndividual in types,
        )
        operators = [predicate for predicate in (OWL.unionOf, OWL.intersectionOf)
                     if (term, predicate, None) in graph]
        if anonymous and len(operators) != 1:
            raise ValueError(f"Unsupported or ambiguous class expression: {identifier}")
        for predicate, edge_kind in ((OWL.unionOf, "union_member"),
                                     (OWL.intersectionOf, "intersection_member")):
            heads = list(graph.objects(term, predicate))
            if len(heads) > 1:
                raise ValueError(f"Multiple expression lists on {identifier}")
            for head in heads:
                for index, member in enumerate(graph.items(head)):
                    edges.add(Edge(identifier, add(member, "class"), edge_kind,
                                   str(predicate), index))
        return identifier

    for type_ in KINDS:
        for term in sorted(set(graph.subjects(RDF.type, type_)), key=str):
            add(term, KINDS[type_])
    for predicate, kind in AXIOMS.items():
        for subject, object_ in sorted(graph.subject_objects(predicate), key=lambda pair: tuple(map(str, pair))):
            if str(subject) in nodes:
                if isinstance(object_, Literal):
                    raise ValueError(f"Literal in schema axiom {subject} {predicate}")
                edges.add(Edge(add(subject), add(object_), kind, str(predicate)))
    properties = []
    for node in sorted(nodes.values(), key=lambda item: item.id):
        if not node.kind.endswith("_property"):
            continue
        properties.append(Property(
            node.id, node.qname, node.label, node.kind, node.module,
            sorted(str(value) for value in graph.objects(URIRef(node.id), RDFS.domain)),
            sorted(str(value) for value in graph.objects(URIRef(node.id), RDFS.range)),
            sorted(graph.namespace_manager.normalizeUri(value)
                   for value in graph.objects(URIRef(node.id), RDF.type)
                   if value not in KINDS),
        ))
    ontology_iri = URIRef(EX.removesuffix('#'))
    identity = {key: sorted(str(value) for value in graph.objects(ontology_iri, predicate))
                for key, predicate in [('versions', OWL.versionInfo), ('revisions', DCTERMS.identifier),
                                       ('languages', DCTERMS.language)]}
    schema = Schema(nodes, sorted(edges, key=lambda edge: (edge.source, edge.kind, edge.index, edge.target)),
                    properties, sources, len(graph), prefixes, identity)
    # Check every declared domain/range is represented, including external
    # terms, OR expressions, multiple ranges (AND) and missing constraints.
    for property_ in properties:
        schema.constraints(property_.domains)
        schema.constraints(property_.ranges)
    return schema


# A declared, non-exhaustive paper view. Every arrow must match an asserted
# domain/property/range triple; no observed ABox association is promoted to TBox.
SIMPLIFIED_PROPERTIES = (
    "hasConsentRecord", "hasSemanticContract", "auditsContract", "appliedPolicy",
    "tracedToPolicy", "evaluatesNode", "hasNodeState", "hasDecisionAlternative",
    "resultedInAction", "affectsModel", "updatesModel", "transfersData",
    "generatedBy", "hasWearable", "hostedAt",
)


def simplified(schema: Schema) -> tuple[set[str], list[Property]]:
    lookup = {prop.id: prop for prop in schema.properties}
    missing = [name for name in SIMPLIFIED_PROPERTIES if EX + name not in lookup]
    if missing:
        raise ValueError(f"Simplified figure needs review: missing properties {missing}")
    selected = [lookup[EX + name] for name in SIMPLIFIED_PROPERTIES]
    for prop in selected:
        if len(prop.domains) != 1 or len(prop.ranges) != 1:
            raise ValueError(f"Simplified figure needs review: {prop.qname} changed its schema")
        if any(schema.nodes[key].kind != "class" for key in prop.domains + prop.ranges):
            raise ValueError(f"Simplified figure needs review: {prop.qname} no longer joins classes")
    return {key for prop in selected for key in prop.domains + prop.ranges}, selected
