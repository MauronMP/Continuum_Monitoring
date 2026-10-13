import json

import pytest

from continuum_bench.result_contract import require_release_metadata
from continuum_bench.specification import release_identity


def test_result_contract_accepts_current_metadata(tmp_path):
    (tmp_path / "metadata.json").write_text(
        json.dumps(release_identity()),
        encoding="utf-8",
    )

    assert require_release_metadata(tmp_path)["ontology_version"] == "4.0.0"


def test_result_contract_rejects_legacy_results(tmp_path):
    (tmp_path / "metadata.json").write_text(
        json.dumps({"ontology_version": "2.3.0", "query_count": 69}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="instead of mixing ontology releases"):
        require_release_metadata(tmp_path)


def test_result_contract_rejects_results_without_reasoning_contract(tmp_path):
    metadata = release_identity()
    del metadata["reasoning_contract"]
    (tmp_path / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="reasoning contract change"):
        require_release_metadata(tmp_path)


@pytest.mark.parametrize("revision", [None, "4.0.0-before-english"])
def test_result_contract_rejects_ontology_before_english_correction(tmp_path, revision):
    metadata = release_identity()
    metadata["ontology_revision"] = revision
    (tmp_path / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="ontology_revision"):
        require_release_metadata(tmp_path)


def test_result_contract_rejects_results_from_another_source_build(tmp_path):
    metadata = release_identity()
    metadata["software_build_id"] = "continuum-benchmark-stale-source"
    (tmp_path / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="software_build_id"):
        require_release_metadata(tmp_path)


def test_result_contract_rejects_same_version_changed_semantic_inputs(tmp_path):
    metadata = {**release_identity(), 'semantic_assets_digest': '0' * 64}
    (tmp_path / 'metadata.json').write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match='semantic_assets_digest'):
        require_release_metadata(tmp_path)
