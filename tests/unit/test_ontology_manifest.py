import hashlib
import json


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
