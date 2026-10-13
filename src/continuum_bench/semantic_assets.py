"""Content identity for the semantic inputs shared by physical workers."""
from __future__ import annotations

import csv
from hashlib import sha256
from pathlib import Path
import tomllib

from .config import BenchmarkConfig, load_config


def semantic_assets_digest(config: BenchmarkConfig | None = None) -> str:
    """Hash manifests and their referenced files, independently of checkout path.

    This is a byte-level deployment check, not semantic graph equivalence. A
    comment or whitespace change also requires synchronization and restart.
    Benchmark sizes, timeouts and host-specific topology are separate contracts.
    """
    if config is None:
        manifest = Path.cwd() / 'configs/benchmark.toml'
        if not manifest.is_file():
            manifest = Path(__file__).resolve().parents[2] / 'configs/benchmark.toml'
        config = load_config(manifest)
    paths = {config.resolve(p) for p in (*config.ontology_files, *config.shape_files)}
    catalog = config.resolve(config.query_catalog)
    paths.add(catalog)
    with catalog.open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            paths.add(config.resolve(Path(row['path'])))
    placement = config.root / 'configs/ontology-placement.toml'
    paths.update({placement, config.root / 'queries/execution-plan.toml'})
    with placement.open('rb') as handle:
        for role in tomllib.load(handle)['roles'].values():
            paths.add(config.resolve(Path(role['profile'])))
            paths.update(config.resolve(Path(path)) for path in role['files'])
    digest = sha256()
    # Relative paths prevent a coordinator/worker home-directory mismatch.
    for path in sorted(paths, key=lambda p: p.relative_to(config.root).as_posix()):
        digest.update(path.relative_to(config.root).as_posix().encode('utf-8'))
        digest.update(b'\0')
        digest.update(path.read_bytes())
        digest.update(b'\0')
    return digest.hexdigest()
