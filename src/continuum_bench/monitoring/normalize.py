"""Canonical result envelope for the retained scientific benchmark families."""
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from .campaign_results import SCHEMA_VERSION


def normalize_completed_outputs(config, output: Path, started_ns: int) -> None:
    """Add canonical JSONL to newly written summaries; preserve historical CSV schemas."""
    for summary in output.rglob('summary.csv') if output.is_dir() else ():
        if summary.stat().st_mtime_ns < started_ns:
            continue
        meta_path = summary.with_name('metadata.json')
        metadata = json.loads(meta_path.read_text()) if meta_path.is_file() else {}
        configuration = asdict(config)
        config_json = json.dumps(configuration, sort_keys=True, default=str)
        config_id = hashlib.sha256(config_json.encode()).hexdigest()
        with summary.open(newline='') as source, summary.with_name('results.jsonl').open('w') as target:
            for index, row in enumerate(csv.DictReader(source)):
                record = {
                    'schema_version': SCHEMA_VERSION, 'configuration_id': config_id,
                    'execution_id': f'{started_ns}-{index}',
                    'status': row.get('status', 'unknown'), 'reasoner': row.get('reasoner'),
                    'configuration': configuration, 'infrastructure': metadata,
                    'source_summary': str(summary), 'measurements': row,
                }
                target.write(json.dumps(record, sort_keys=True, default=str)+'\n')
