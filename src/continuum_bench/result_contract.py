"""Compatibility gate for benchmark artefacts consumed by reports/plots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .specification import EXPECTED_QUERY_IDS, ONTOLOGY_REVISION, ONTOLOGY_VERSION
from .reasoners import REASONING_CONTRACT


def require_release_metadata(directory: Path) -> dict[str, Any]:
    """Reject legacy/mixed result directories before comparing or plotting."""

    path = directory / "metadata.json"
    if not path.is_file():
        raise ValueError(
            f"{directory}: missing metadata.json; results cannot be proven "
            "compatible with ontology v3.0.0"
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
            "benchmark instead of mixing v2.x and v3 results."
        )
    if metadata.get("reasoning_contract") != REASONING_CONTRACT:
        raise ValueError(
            f"{directory}: incompatible reasoning_contract="
            f"{metadata.get('reasoning_contract')!r}; expected "
            f"{REASONING_CONTRACT!r}. Re-run every architecture after the "
            "RDFS datatype correction; old v3 results cannot be mixed."
        )
    if metadata.get("ontology_revision") != ONTOLOGY_REVISION:
        raise ValueError(
            f"{directory}: incompatible ontology_revision="
            f"{metadata.get('ontology_revision')!r}; expected "
            f"{ONTOLOGY_REVISION!r}. Re-run each architecture with the "
            "English, datatype-corrected ontology; do not relabel old results."
        )
    return metadata
