import pytest
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import XSD

from continuum_bench.reasoners import materialize


TEST = Namespace("urn:literal-test:")


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (Literal(True), Literal(1)),
        (Literal(False), Literal(0)),
        (Literal(True), Literal("1.0", datatype=XSD.decimal)),
        (Literal("same", lang="en"), Literal("same", lang="es")),
        (Literal("same"), Literal("same", lang="en")),
        (Literal("same", datatype=XSD.anyURI), Literal("same")),
    ],
)
def test_rdfs_does_not_substitute_distinct_literal_value_spaces(left, right):
    source = Graph()
    source.add((TEST.a, TEST.value, left))
    source.add((TEST.b, TEST.value, right))

    result = materialize(source, "rdfs")

    assert (TEST.a, TEST.value, right) not in result.graph
    assert (TEST.b, TEST.value, left) not in result.graph
    assert len(source) == 2  # Materialisation must not mutate the caller's data.


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (Literal(1), Literal("1.0", datatype=XSD.decimal)),
        (
            Literal("1", datatype=XSD.boolean, normalize=False),
            Literal("true", datatype=XSD.boolean, normalize=False),
        ),
    ],
)
def test_rdfs_preserves_valid_literal_value_equivalences(left, right):
    source = Graph()
    source.add((TEST.a, TEST.value, left))
    source.add((TEST.b, TEST.value, right))

    result = materialize(source, "rdfs")

    assert (TEST.a, TEST.value, right) in result.graph
    assert (TEST.b, TEST.value, left) in result.graph
