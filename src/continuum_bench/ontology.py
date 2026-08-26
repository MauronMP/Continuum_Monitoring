from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Iterable

from rdflib import Graph, OWL, RDF
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
    return sum(1 for _ in graph.subjects(RDF.type, OWL.Nothing))


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
