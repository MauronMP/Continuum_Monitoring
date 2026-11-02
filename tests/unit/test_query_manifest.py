import hashlib
import json


def test_query_manifest_matches_files(root):
    manifest = json.loads((root / "queries/manifest.json").read_text())
    assert manifest["query_count"] == 113
    assert len(manifest["queries"]) == 113
    for query in manifest["queries"]:
        path = root / query["path"]
        assert path.is_file(), query["id"]
        assert hashlib.sha256(path.read_text().encode()).hexdigest() == query["query_sha256"]
        assert query["merge_strategy"] in {"single", "set_union", "boolean_or"}
        assert "# Current v" not in path.read_text()
        if query["execution_scope"] in {"authorities", "cloud_authorities", "all"}:
            assert query["merge_strategy"] != "single"
        if query["merge_strategy"] == "boolean_or":
            assert query["kind"] == "ask"
    payload = "\n".join(
        f"{query['order']}\x1f{query['id']}\x1f{query['path']}\x1f{query['query_sha256']}"
        f"\x1f{query['execution_scope']}\x1f{query['merge_strategy']}\x1f{query['privacy_class']}"
        for query in manifest["queries"]
    )
    assert hashlib.sha256(payload.encode()).hexdigest() == manifest["query_catalog_digest"]


def test_query_documentation_covers_the_executable_catalog(root):
    manifest = json.loads((root / "queries/manifest.json").read_text())
    documentation = (root / "docs/QUERY_CATALOG.md").read_text()
    for query in manifest["queries"]:
        assert f"`{query['id']}`" in documentation
