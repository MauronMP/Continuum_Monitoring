import hashlib
import json

from rdflib import RDF, Graph, Namespace


def test_canonical_base_manifest_matches_semantic_sources(root):
    manifest = json.loads((root / "ontology/benchmark/manifest.json").read_text())
    entries = manifest["sources"]
    for entry in entries:
        path = root / entry["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
    bundle = "\n".join(f"{entry['path']}\x1f{entry['sha256']}" for entry in entries)
    assert hashlib.sha256(bundle.encode()).hexdigest() == manifest["source_bundle_digest"]
    base = root / manifest["canonical_base"]["path"]
    assert base.stat().st_size == manifest["canonical_base"]["bytes"]
    assert hashlib.sha256(base.read_bytes()).hexdigest() == manifest["canonical_base"]["sha256"]
    assert sum(1 for line in base.read_text().splitlines() if line.strip()) == manifest["canonical_base"]["triples"]


def test_turtle_sources_parse_and_requirements_are_traced_and_documented(root):
    graph = Graph()
    for path in sorted((root / "ontology").rglob("*.ttl")):
        graph.parse(path, format="turtle")
    comon = Namespace("http://example.org/monitoringcontinuum#")
    requirements = set(graph.subjects(RDF.type, comon.Requirement))
    assert len(requirements) == 116
    documentation = (root / "docs/REQUIREMENTS.md").read_text()
    for requirement in requirements:
        identifier = str(next(graph.objects(requirement, comon.requirementIdentifier)))
        assert list(graph.objects(requirement, comon.tracedToPolicy)), identifier
        assert list(graph.objects(requirement, comon.tracedToMechanism)), identifier
        assert f"`{identifier}`" in documentation

    query_identifiers = {
        str(value)
        for subject in graph.subjects(RDF.type, comon.QuerySpecification)
        for value in graph.objects(subject, comon.queryIdentifier)
    }
    manifest = json.loads((root / "queries/manifest.json").read_text())
    assert query_identifiers == {query["id"] for query in manifest["queries"]}
