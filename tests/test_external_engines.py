import pytest
from rdflib import Graph, Literal, Namespace, RDF

from continuum_bench.external_node import ExternalRuntime
from continuum_bench.engines import _expectation_ok, _ntriples, _query_payload
from continuum_bench.ontology import load_graph
from continuum_bench.queries import load_catalog
from continuum_bench.synthetic import add_synthetic_data


EX = Namespace("http://example.org/smartcity#")


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


@pytest.mark.parametrize("engine", ("rdflib", "oxigraph"))
@pytest.mark.parametrize("users", (0, 5, 25))
def test_v3_external_roundtrip_satisfies_all_query_expectations(config, engine, users):
    """Exercise the actual N-Triples/prepare/query path used by Docker."""
    source = load_graph(config.resolve(path) for path in config.ontology_files)
    add_synthetic_data(source, users, config.seed)
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    by_id = {spec.id: spec for spec in specs}
    runtime = ExternalRuntime(engine)

    runtime.prepare(_ntriples(source))
    response = runtime.execute(_query_payload(specs)["queries"])

    failures = {
        item["query_id"]: item["result_count"]
        for item in response["measurements"]
        if not _expectation_ok(by_id[item["query_id"]], item)
    }
    assert len(response["measurements"]) == 115
    assert failures == {}


@pytest.mark.parametrize(
    ("noise", "anonymization", "mechanism", "violation"),
    [
        (True, True, True, False),
        (False, True, True, True),
        (True, False, True, True),
        (None, True, True, True),
        (True, None, True, True),
        (True, True, False, True),
        (1, True, True, True),  # An asserted integer is not a boolean flag.
    ],
)
def test_ext_q68_still_detects_real_privacy_violations(
    config, noise, anonymization, mechanism, violation
):
    spec = next(
        spec for spec in load_catalog(config.resolve(config.query_catalog), config.root)
        if spec.id == "EXT-Q68"
    )
    source = Graph()
    source.add((EX.TestGradient, RDF.type, EX.ModelGradientUpdate))
    source.add((EX.TestGradient, EX.originatesFromDevice, EX.TestDevice))
    source.add((EX.TestGradient, EX.sentToNode, EX.TestCloud))
    # The unrelated number used to contaminate the two boolean privacy flags.
    source.add((EX.Other, EX.someCount, Literal(1)))
    if noise is not None:
        source.add((EX.TestGradient, EX.hasNoiseApplied, Literal(noise)))
    if anonymization is not None:
        source.add((EX.TestGradient, EX.hasAnonymizationApplied, Literal(anonymization)))
    if mechanism:
        source.add((EX.TestGradient, EX.hasPrivacyMechanism, EX.TestPrivacyMechanism))
    runtime = ExternalRuntime("rdflib")
    runtime.prepare(_ntriples(source))

    measurement = runtime.execute(_query_payload([spec])["queries"])["measurements"][0]

    assert (measurement["result_count"] > 0) is violation
