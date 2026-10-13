"""Compatibility gate for benchmark artefacts consumed by reports/plots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .specification import EXPECTED_QUERY_IDS, ONTOLOGY_REVISION, ONTOLOGY_VERSION
from .reasoners import REASONING_CONTRACT
from .protocol import SOFTWARE_BUILD_ID


def require_release_metadata(directory: Path) -> dict[str, Any]:
    """Reject legacy/mixed result directories before comparing or plotting."""

    path = directory / "metadata.json"
    if not path.is_file():
        raise ValueError(
            f"{directory}: missing metadata.json; results cannot be proven "
            "compatible with ontology v4.0.0"
        )
    metadata = json.loads(path.read_text(encoding="utf-8"))
    observed_version = str(metadata.get("ontology_version", ""))
    observed_queries = metadata.get("query_count")
    try:
        observed_queries = int(observed_queries)
    except (TypeError, ValueError):
        observed_queries = -1
    expected_queries = len(EXPECTED_QUERY_IDS)
    if (
        observed_version != ONTOLOGY_VERSION
        or observed_queries != expected_queries
    ):
        raise ValueError(
            f"{directory}: incompatible benchmark release "
            f"ontology_version={observed_version!r}, "
            f"query_count={observed_queries!r}; expected "
            f"{ONTOLOGY_VERSION!r} and {expected_queries}. Re-run the "
            "benchmark instead of mixing ontology releases."
        )
    if metadata.get("reasoning_contract") != REASONING_CONTRACT:
        raise ValueError(
            f"{directory}: incompatible reasoning_contract="
            f"{metadata.get('reasoning_contract')!r}; expected "
            f"{REASONING_CONTRACT!r}. Re-run every architecture after the "
            "reasoning contract change; incompatible results cannot be mixed."
        )
    if metadata.get("ontology_revision") != ONTOLOGY_REVISION:
        raise ValueError(
            f"{directory}: incompatible ontology_revision="
            f"{metadata.get('ontology_revision')!r}; expected "
            f"{ONTOLOGY_REVISION!r}. Re-run each architecture with the "
            "current ontology release; do not relabel old results."
        )
    if metadata.get("software_build_id") != SOFTWARE_BUILD_ID:
        raise ValueError(
            f"{directory}: incompatible software_build_id="
            f"{metadata.get('software_build_id')!r}; expected "
            f"{SOFTWARE_BUILD_ID!r}. Re-run the benchmark with the active "
            "source tree instead of mixing outputs from different builds."
        )
    if "semantic_assets_digest" in metadata:
        from .semantic_assets import semantic_assets_digest
        if metadata["semantic_assets_digest"] != semantic_assets_digest():
            raise ValueError(
                f"{directory}: incompatible semantic_assets_digest; ontology, queries or placement changed. "
                "Do not relabel old measurements or combine different semantic inputs."
            )
    return metadata
