import pytest

from continuum_bench.external_node import ExternalRuntime


DATA = """
<urn:test:Child> <http://www.w3.org/2000/01/rdf-schema#subClassOf> <urn:test:Parent> .
<urn:test:alice> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <urn:test:Child> .
"""

QUERY = {
    "id": "TEST-Q01",
    "category": "topology",
    "tier": "core",
    "kind": "select",
    "text": """
        SELECT ?value WHERE {
          ?value a <urn:test:Parent>
        }
    """,
}


@pytest.mark.parametrize(
    ("engine", "expected_count"),
    (("rdflib", 1), ("oxigraph", 0)),
)
def test_python_external_engines_expose_inference_profile(
    engine,
    expected_count,
):
    runtime = ExternalRuntime(engine)
    prepared = runtime.prepare(DATA)
    result = runtime.execute([QUERY])

    assert prepared["engine"] == engine
    assert prepared["input_triples"] == 2
    assert result["measurements"][0]["result_count"] == expected_count
    assert result["measurements"][0]["result_digest"] == ""
    assert prepared["inference_profile"] == (
        "rdfs" if engine == "rdflib" else "none"
    )
