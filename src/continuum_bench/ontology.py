from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Iterable

from rdflib import Graph, Literal, OWL, RDF, RDFS, XSD
from rdflib.compare import to_canonical_graph


def load_graph(paths: Iterable[Path]) -> Graph:
    graph = Graph()
    for path in paths:
        graph.parse(path, format="turtle")
    return graph


def graph_digest(graph: Graph) -> str:
    canonical_graph = to_canonical_graph(graph)
    canonical = sorted(
        f"{subject.n3()} {predicate.n3()} {obj.n3()} ."
        for subject, predicate, obj in canonical_graph
    )
    return sha256("\n".join(canonical).encode("utf-8")).hexdigest()


def contradiction_count(graph: Graph) -> int:
    """Count explicit bottom instances, not all OWL inconsistencies."""
    return sum(1 for _ in graph.subjects(RDF.type, OWL.Nothing))


def datatype_range_errors(graph: Graph) -> list[dict[str, str]]:
    """Detect definite string/language range clashes and ill-typed literals.

    This inexpensive guard catches the Protégé requirementStatement regression
    before any benchmark. It is deliberately not a complete OWL consistency
    checker: numeric value-space inclusion, anonymous dataranges, restrictions
    and other logical axioms require an OWL reasoner. Do not compare datatype
    IRIs blindly: xsd:int is compatible with xsd:integer, for example.
    """
    string_datatypes = {
        XSD.string, XSD.normalizedString, XSD.token, XSD.language,
        XSD.Name, XSD.NCName, XSD.NMTOKEN,
    }
    errors: set[tuple[str, str, str, str]] = set()
    for property_, range_ in graph.subject_objects(RDFS.range):
        if not (
            str(range_).startswith(str(XSD))
            or range_ in {RDF.langString, RDFS.Literal}
        ):
            continue
        # A subproperty inherits every range of its superproperties.
        for predicate in graph.transitive_subjects(RDFS.subPropertyOf, property_):
            for subject, value in graph.subject_objects(predicate):
                incompatible = not isinstance(value, Literal)
                if isinstance(value, Literal):
                    actual = value.datatype or (
                        RDF.langString if value.language else XSD.string
                    )
                    incompatible = (
                        value.ill_typed is True
                        or (range_ == XSD.string and actual not in string_datatypes)
                        or (range_ == RDF.langString and not value.language)
                        or (str(range_).startswith(str(XSD)) and bool(value.language))
                    )
                if incompatible:
                    errors.add((str(subject), str(predicate), str(range_), value.n3()))
    return [
        dict(subject=subject, property=predicate, range=range_, value=value)
        for subject, predicate, range_, value in sorted(errors)
    ]


def validate_shacl(data_graph: Graph, shape_paths: Iterable[Path]) -> tuple[bool, str]:
    try:
        from pyshacl import validate
    except ImportError as error:
        raise RuntimeError(
            "pyshacl is required for policy validation; install project dependencies"
        ) from error
    shape_graph = load_graph(shape_paths)
    conforms, _, report_text = validate(
        data_graph=data_graph,
        shacl_graph=shape_graph,
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
    )
    return bool(conforms), str(report_text)
