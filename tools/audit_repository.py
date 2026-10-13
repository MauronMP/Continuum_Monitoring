#!/usr/bin/env python3
"""Read-only inventory and syntax audit of all maintained repository files.

Outputs are written only to the requested audit directory. Semantic consistency,
scientific interpretation and execution tests remain separate gates.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib
import xml.etree.ElementTree as ET

from rdflib import Graph, OWL, RDF, URIRef
from rdflib.plugins.sparql.parser import parseQuery

ROOT = Path(__file__).resolve().parents[1]


def audit(root: Path) -> dict:
    listed = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root)
    paths = sorted({root / name.decode() for name in listed.split(b"\0") if name and (root / name.decode()).is_file()})
    inventory, errors, counts = [], [], {}
    combined = Graph()
    for path in paths:
        relative = str(path.relative_to(root))
        payload = path.read_bytes()
        suffix = path.suffix.lower()
        counts[suffix or "extensionless"] = counts.get(suffix or "extensionless", 0) + 1
        inventory.append({"path": relative, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
        try:
            if suffix == ".py":
                ast.parse(payload, filename=relative)
            elif suffix == ".toml":
                tomllib.loads(payload.decode())
            elif suffix == ".json":
                json.loads(payload)
            elif suffix in (".xml", ".svg", ".graphml"):
                ET.fromstring(payload)
            elif suffix == ".ttl":
                graph = Graph().parse(data=payload, format="turtle")
                combined += graph
            elif suffix == ".rq":
                parseQuery(payload.decode())
            elif suffix == ".csv":
                rows = list(csv.reader(payload.decode().splitlines()))
                if rows and any(len(row) != len(rows[0]) for row in rows[1:]):
                    raise ValueError("Non-rectangular CSV")
        except Exception as error:
            errors.append({"path": relative, "error": f"{type(error).__name__}: {error}"})
    namespace = "http://example.org/monitoringcontinuum#"
    subjects = set(combined.subjects())
    unresolved = sorted({str(term) for triple in combined for term in triple if isinstance(term, URIRef)
                         and str(term).startswith(namespace) and term not in subjects})
    mixed_properties = sorted(str(term) for term in set(combined.subjects(RDF.type, OWL.ObjectProperty))
                              & set(combined.subjects(RDF.type, OWL.DatatypeProperty)))
    if mixed_properties:
        errors.append({"path": "ontology", "error": "Mixed object/datatype properties", "terms": mixed_properties})
    return {"scope": "All existing tracked and unignored files; generated outputs and local runtimes are excluded",
            "ok": not errors, "file_count": len(paths), "extension_counts": counts, "errors": errors,
            "ontology_union_triples_including_profiles_and_shapes": len(combined),
            "internal_iris_without_subject_definition_review_required": unresolved, "inventory": inventory}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/audit/repository.json")
    args = parser.parse_args()
    result = audit(ROOT)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k:v for k,v in result.items() if k != "inventory"}, indent=2))
    return int(not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())
