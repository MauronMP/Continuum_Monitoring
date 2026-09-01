#!/usr/bin/env python3
"""Validate active Markdown links and generated English reference manuals."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import tempfile
from urllib.parse import unquote

from generate_reference_docs import generate


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/reference"
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")
GENERATED_NAMES = (
    "REQUIREMENTS.md",
    "POLICIES.md",
    "SPARQL_QUERIES.md",
    "ONTOLOGY_REFERENCE.md",
)


def documentation_files(root: Path = ROOT) -> list[Path]:
    paths = [root / "README.md"]
    paths.extend((root / "docs").rglob("*.md"))
    paths.append(root / "ontology/diagrams/README.md")
    return sorted({path.resolve() for path in paths if path.is_file()})


def github_anchor(heading: str) -> str:
    """Return the GitHub-style anchor needed by the project's English headings."""

    value = re.sub(r"<[^>]+>", "", heading.strip().lower())
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "-", value)
    return value


def heading_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    occurrences: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue
        base = github_anchor(match.group(1))
        number = occurrences.get(base, 0)
        occurrences[base] = number + 1
        anchors.add(base if number == 0 else f"{base}-{number}")
    return anchors


def _link_destination(raw: str) -> str:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        return value[1 : value.index(">")]
    # Local project paths do not contain spaces. Removing an optional Markdown
    # title is sufficient and avoids interpreting shell examples as links.
    return value.split(maxsplit=1)[0]


def check_links(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}
    for source in paths:
        text = source.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in LINK_RE.finditer(line):
                destination = unquote(_link_destination(match.group(1)))
                if not destination or destination.startswith(
                    ("http://", "https://", "mailto:")
                ):
                    continue
                target_text, separator, fragment = destination.partition("#")
                target = (
                    source
                    if not target_text
                    else (source.parent / target_text).resolve()
                )
                if not target.exists():
                    errors.append(
                        f"{source.relative_to(ROOT)}:{line_number}: "
                        f"missing link target {destination!r}"
                    )
                    continue
                if separator and fragment and target.is_file() and target.suffix == ".md":
                    anchors = anchor_cache.setdefault(target, heading_anchors(target))
                    if fragment not in anchors:
                        errors.append(
                            f"{source.relative_to(ROOT)}:{line_number}: "
                            f"missing heading #{fragment} in {target.relative_to(ROOT)}"
                        )
    return errors


def check_generated_references() -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="continuum-docs-") as directory:
        generated = Path(directory)
        generate(generated)
        for name in GENERATED_NAMES:
            committed = REFERENCE / name
            candidate = generated / name
            if not committed.is_file():
                errors.append(f"missing generated manual docs/reference/{name}")
            elif committed.read_bytes() != candidate.read_bytes():
                errors.append(
                    f"docs/reference/{name} is stale; run "
                    ".venv/bin/python tools/generate_reference_docs.py"
                )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check local Markdown links and generated v3 manuals"
    )
    parser.add_argument(
        "--links-only",
        action="store_true",
        help="Skip deterministic regeneration of docs/reference",
    )
    args = parser.parse_args(argv)

    paths = documentation_files()
    errors = check_links(paths)
    if not args.links_only:
        errors.extend(check_generated_references())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Documentation validation failed with {len(errors)} error(s).")
        return 1
    mode = "links" if args.links_only else "links and generated references"
    print(f"Documentation validation passed: {len(paths)} files; {mode} verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
