import json

import pytest

from continuum_bench.result_contract import require_release_metadata
from continuum_bench.specification import release_identity


def test_result_contract_accepts_v3_metadata(tmp_path):
    (tmp_path / "metadata.json").write_text(
        json.dumps(release_identity()),
        encoding="utf-8",
    )

    assert require_release_metadata(tmp_path)["ontology_version"] == "3.0.0"


def test_result_contract_rejects_legacy_results(tmp_path):
    (tmp_path / "metadata.json").write_text(
        json.dumps({"ontology_version": "2.3.0", "query_count": 69}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="instead of mixing v2.x and v3"):
        require_release_metadata(tmp_path)


def test_result_contract_rejects_v3_results_before_datatype_correction(tmp_path):
    metadata = release_identity()
    del metadata["reasoning_contract"]
    (tmp_path / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="RDFS datatype correction"):
        require_release_metadata(tmp_path)
