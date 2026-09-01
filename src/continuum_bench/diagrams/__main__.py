"""Generate ontology/diagrams without modifying ontology or benchmark data."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

from ..config import load_config
from ..specification import ONTOLOGY_REVISION, ONTOLOGY_VERSION
from .model import MODULES, extract_schema, simplified
from .render import (
    dot_view, export_data, graphml, render_graphviz,
    verify_complete_coverage, verify_edge_labels,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('configs/benchmark.toml'))
    parser.add_argument('--output', type=Path, default=Path('ontology/diagrams'))
    parser.add_argument('--dot', default='dot', help='Graphviz dot executable')
    parser.add_argument('--atlas-python', default=sys.executable,
                        help='Python interpreter with ReportLab (default: current interpreter)')
    parser.add_argument('--no-atlas', action='store_true', help='Generate graphs without the PDF reference atlas')
    parser.add_argument('--sources-only', action='store_true', help='Only DOT, GraphML and inventories; no renderer needed')
    parser.add_argument('--timeout', type=float, default=120, help='Timeout in seconds per rendering process')
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('--timeout must be finite and positive')
    try:
        dot = shutil.which(args.dot)
        if not args.sources_only and dot is None:
            raise RuntimeError('Graphviz is required: install graphviz (dot), or use --sources-only.')
        if not (args.no_atlas or args.sources_only):
            dependency = subprocess.run([args.atlas_python, '-c', 'import reportlab'],
                capture_output=True, text=True, timeout=10, check=False)
            if dependency.returncode:
                raise RuntimeError('ReportLab is required only for the atlas. Install the diagrams extra '
                                   '(python -m pip install -e ".[diagrams]"), pass --atlas-python, or use --no-atlas.')
        schema = extract_schema(load_config(args.config))
        if (schema.identity['versions'] != [ONTOLOGY_VERSION]
                or schema.identity['revisions'] != [ONTOLOGY_REVISION]
                or schema.identity['languages'] != ['en']):
            raise ValueError('The configured ontology does not match the English project release: '
                             + str(schema.identity))
        selected, properties = simplified(schema)
        output = args.output.resolve()
        sources = output / 'sources'
        sources.mkdir(parents=True, exist_ok=True)
        print('[ontology-diagrams] extracting asserted schema', flush=True)
        data = export_data(schema, output / 'data')
        data.update(ontology_version=ONTOLOGY_VERSION, ontology_revision=ONTOLOGY_REVISION,
                    modules=MODULES)
        schema_file = output / 'data/schema.json'
        schema_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        # Invalidate any previous success manifest before replacing its figures.
        (output / 'manifest.json').write_text(json.dumps({'status': 'in_progress',
            'schema_sha256': sha256(schema_file.read_bytes()).hexdigest()}) + '\n', encoding='utf-8')
        (sources / 'ontology.graphml').write_text(graphml(schema), encoding='utf-8')
        figures = {}
        coverage = {}
        definitions = [('ontology-simplified', dict(simple=True)),
                       ('ontology-complete', dict())]
        definitions += [('modules/' + name, dict(module=name)) for name in MODULES]
        for name, options in definitions:
            source = sources / (name + '.dot')
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(dot_view(schema, **options), encoding='utf-8')
            if not args.sources_only:
                print(f'[ontology-diagrams] rendering {name}', flush=True)
                formats = ('svg',) if name.startswith('modules/') else ('svg', 'pdf', 'png')
                figures[name] = render_graphviz(source, output / 'figures' / name,
                    executable=dot, formats=formats, preview_dpi=300 if options.get('simple') else 180,
                    timeout=args.timeout)
                expected = {prop.id: prop.label if options.get('simple') else prop.qname
                            for prop in (properties if options.get('simple') else schema.properties)
                            if prop.kind == 'object_property' and (prop.domains or prop.ranges)
                            and (not options.get('module') or prop.module == options['module'])}
                verify_edge_labels(output / 'figures' / (name + '.svg'), expected)
            if name == 'ontology-complete':
                coverage = verify_complete_coverage(schema, source.read_text(encoding='utf-8'),
                    None if args.sources_only else output / 'figures/ontology-complete.svg')
        # A monochrome source/vector variant avoids depending on color alone.
        mono = sources / 'ontology-simplified-monochrome.dot'
        mono.write_text(dot_view(schema, simple=True, monochrome=True), encoding='utf-8')
        if not args.sources_only:
            figures['ontology-simplified-monochrome'] = render_graphviz(mono,
                output / 'figures/ontology-simplified-monochrome', executable=dot,
                formats=('svg',), timeout=args.timeout)
            verify_edge_labels(output / 'figures/ontology-simplified-monochrome.svg',
                               {prop.id: prop.label for prop in properties})
        atlas = {}
        if not (args.no_atlas or args.sources_only):
            print('[ontology-diagrams] building the readable schema atlas', flush=True)
            process = subprocess.run([args.atlas_python, str(Path(__file__).with_name('atlas.py')),
                str(schema_file), str(output / 'ontology-atlas.pdf')],
                capture_output=True, text=True, timeout=args.timeout, check=False)
            if process.returncode:
                raise RuntimeError(f'Atlas generation failed: {process.stderr}')
            atlas = json.loads(process.stdout)
        version = (subprocess.run([dot, '-V'], capture_output=True, text=True,
                                 timeout=10, check=True).stderr.strip()
                   if dot and not args.sources_only else 'not run')
        manifest = {
            'status': 'complete',
            'ontology_version': ONTOLOGY_VERSION, 'ontology_revision': ONTOLOGY_REVISION,
            'scope': data['scope'], 'counts': data['counts'], 'sources': data['sources'],
            'schema_sha256': sha256(schema_file.read_bytes()).hexdigest(),
            'graphviz': version, 'rendered': not args.sources_only,
            'simplified': {'classes': len(selected), 'properties': len(properties),
                           'property_iris': [p.id for p in properties]},
            'complete': coverage,
            'figures': figures, **atlas,
        }
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        print('[ontology-diagrams] done: ' + str(output), flush=True)
        print(json.dumps(data['counts'], indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'Ontology diagram generation failed: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
