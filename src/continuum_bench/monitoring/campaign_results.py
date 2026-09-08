"""Versioned JSONL/CSV evidence sink; no plotting dependency."""
import csv
import json
from pathlib import Path

SCHEMA_VERSION = 'continuum.monitoring.v1'

class StructuredResults:
    def __init__(self, directory: Path, manifest: dict):
        directory.mkdir(parents=True, exist_ok=False)
        self.directory = directory
        self.manifest = manifest
        (directory / 'manifest.json').write_text(json.dumps({'schema_version': SCHEMA_VERSION, **manifest}, indent=2, default=str)+'\n')
        self.handle = (directory / 'results.jsonl').open('w')
        self.rows = []

    def write(self, record):
        record = {'schema_version': SCHEMA_VERSION,
                  'execution_id': f"{self.manifest.get('run_id', 'run')}-{len(self.rows)}",
                  'reasoner': record.get('reasoner'),
                  'configuration': self.manifest.get('configuration', {}),
                  'infrastructure': record.get('nodes', []),
                  'measurements': {key: value for key, value in record.items()
                      if key.endswith(('_ms', '_mib', '_rps')) or key in
                      {'input_triples','output_triples','result_validation_rate','completed_requests'}},
                  **record}
        self.handle.write(json.dumps(record, sort_keys=True, default=str)+'\n')
        self.handle.flush()
        self.rows.append(record)

    def close(self):
        self.handle.close()
        if not self.rows:
            return
        fields = sorted(set().union(*(row.keys() for row in self.rows)))
        with (self.directory / 'results.csv').open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in self.rows:
                writer.writerow({key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict, tuple)) else value for key, value in row.items()})
