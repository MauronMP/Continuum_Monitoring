#!/usr/bin/env python3
"""Render explicitly non-publication diagnostics using a suite's archived source.

The publication report and its acceptance gate remain unchanged. This separate
catalogue retains partial performance observations for troubleshooting, with
visible diagnostic labels and the original rejected acceptance status.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite', type=Path)
    args = parser.parse_args()
    suite = args.suite.resolve()
    output = suite / 'diagnostic-figures'
    archive = suite / 'source.tar.gz'
    with tempfile.TemporaryDirectory(prefix='continuum-diagnostics-') as temporary:
        root = Path(temporary)
        with tarfile.open(archive) as source:
            source.extractall(root, filter='data')
        sys.path.insert(0, str(root / 'src'))
        from continuum_bench.monitoring import publication
        original_save = publication.save_png

        def diagnostic_save(figure, base):
            title = figure._suptitle
            if title is not None:
                title.set_text('DIAGNOSTIC · ' + title.get_text())
                title.set_fontsize(10)
            return original_save(figure, base)

        publication.save_png = diagnostic_save

        class DiagnosticReport(publication.Report):
            def save(self, figure, name, caption):
                caption = 'PARTIAL RUN — NOT ACCEPTED FOR PUBLICATION. Completed observations only; consult coverage for missing and failed points. ' + caption
                return super().save(figure, name, caption)

            def apply_publication_gate(self, acceptance):
                self.findings.append('Explicit diagnostic catalogue: partial observations are retained for troubleshooting; publication acceptance is NOT overridden.')
                return []

            def apply_table_gate(self, acceptance):
                return []

        report = DiagnosticReport(root, suite, output).run()
        report['diagnostic_only'] = True
        report['archived_source_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
        report['renderer_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        # Correct obsolete geographical prose without altering source or data.
        index = output / 'README.md'
        text = index.read_text().replace('Nodes are colocated in one room (operator confirmation).', 'Node co-location is not established by this dataset; do not infer geographical distance from VPN addresses.')
        index.write_text('# Diagnostic catalogue — incomplete campaign\n\nThis is not the publication report. Performance charts describe completed observations from an incomplete run and may exhibit survivor bias. Missing experiment families cannot be reconstructed.\n\n' + text)
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'output': str(output), 'figures': len(report['figures']), 'acceptance': report['acceptance']}, indent=2))


if __name__ == '__main__':
    main()
