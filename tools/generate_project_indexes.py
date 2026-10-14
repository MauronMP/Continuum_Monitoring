#!/usr/bin/env python3
"""Generate the Python file reference and consolidated query documentation."""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import csv
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
CATEGORY_DESCRIPTIONS = {
    'topology': 'Compute nodes, placement and infrastructure relationships.',
    'semantic_schema': 'Classes, properties and semantic model structure.',
    'observability': 'Node/device state, operational observations and availability.',
    'identity_consent': 'Users, identifiers, permissions and consent evidence.',
    'data_lifecycle': 'Retention, transfer, provenance and data handling.',
    'security_identity': 'Identity representations and security-related evidence.',
    'context_zones': 'Geographical or contextual zones and their restrictions.',
    'trust': 'Trust assessments and supporting evidence.',
    'decision': 'Candidate evaluation, alternatives and decision evidence.',
    'policy_governance': 'Policy inventory, requirements and governance links.',
    'adaptation': 'Adaptation and model/service change records.',
    'delegation': 'Delegated work and recovery conditions.',
    'federation': 'Federated-learning session and model-update records.',
    'audit_temporal': 'Temporal validity, audit trails and recorded events.',
    'validation': 'Evidence/constraint checks and missing required records.',
    'wellbeing': 'Wearables, physiological observations and the health example.',
}

def render(root: Path = ROOT) -> dict[str, str]:
    guide = ['# Python source reference', '',
             'Generated from maintained Python files. Regenerate with',
             '`python tools/generate_project_indexes.py`; do not edit generated tables.', '',
             'Scientific experiment contracts belong in [Experiments](EXPERIMENTS.md),',
             'commands in [Complete execution](COMPLETE_EXECUTION.md). There are two',
             'evaluation batteries; regression tests are engineering checks.', '',
             'This inventory covers every Python file in `src/`, `tools/` and `tests/`.',
             'Module descriptions and exposed definitions identify code responsibilities,',
             'not evidence that every modelled capability is implemented.', '']
    groups = {}
    for base in ('src', 'tools', 'tests'):
        for path in sorted((root / base).rglob('*.py')):
            relative = path.relative_to(root).as_posix()
            group = path.parent.relative_to(root).as_posix()
            tree = ast.parse(path.read_text(), filename=relative)
            doc = ast.get_docstring(tree)
            definitions = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
            if doc:
                description = ' '.join(doc.split('\n\n', 1)[0].split())
            elif path.name == '__init__.py':
                description = 'Package boundary and public exports.'
            elif base == 'tests':
                description = 'Regression coverage for ' + path.stem.removeprefix('test_').replace('_', ' ') + '.'
            else:
                description = 'Implementation of ' + path.stem.replace('_', ' ') + '.'
            description = description.replace('|', '\\|')
            names = ', '.join(f'`{n}`' for n in definitions[:8]) or 'Module constants/imports.'
            if len(definitions) > 8:
                names += f' (+{len(definitions) - 8} definitions)'
            groups.setdefault(group, []).append(f'| [{path.name}](../{relative}) | {description} | {names} |')
    for group, rows in groups.items():
        guide += [f'## {group}', '', '| File | Responsibility | Main definitions |', '| --- | --- | --- |', *rows, '']
    with (root / 'queries/catalog.csv').open(newline='') as handle:
        entries = sorted(csv.DictReader(handle), key=lambda row: int(row['order']))
    plan = tomllib.loads((root / 'queries/execution-plan.toml').read_text())
    scopes = {q: scope for scope, ids in plan['scopes'].items() for q in ids}
    bundle = ['# Complete SPARQL query catalogue', '',
              'Generated reading/export bundle, not one executable SPARQL statement.',
              'The worker loads `catalog.csv` and the individual `.rq` files. Edit those',
              'sources and regenerate this file; do not execute this document as a query.', '',
              f'Contains all {len(entries)} queries in catalogue order.', '']
    for row in entries:
        bundle += [f"## {row['id']}: {row['title']}", '',
                   f"Category: `{row['category']}`. Scope: `{scopes[row['id']]}`.", '',
                   f"Source: [{row['path'].removeprefix('queries/')}](../{row['path']}).", '',
                   row['purpose'], '', '```sparql', (root / row['path']).read_text().strip(), '```', '']
    counts = Counter(row['category'] for row in entries)
    readme = ['# Queries and execution plan', '',
              '[All query texts](ALL_QUERIES.md) collects the complete catalogue.',
              '`catalog.csv` is the runtime index: order, ID, category, expectation,',
              'source path, purpose and policy/requirement traceability. Individual',
              '`.rq` files are the executable sources; the bundle is documentation.', '',
              '## Query categories', '',
              'These 16 query groups are not the 12 policy categories. A policy may use',
              'queries from several groups; shared query work must not be double counted.', '',
              '| Category | Queries | Purpose |', '| --- | ---: | --- |']
    for category in CATEGORY_DESCRIPTIONS:
        readme.append(f'| `{category}` | {counts[category]} | {CATEGORY_DESCRIPTIONS[category]} |')
    readme += ['', '## What execution-plan.toml does', '',
               '`execution-plan.toml` supplies coordinator routing and merge metadata.',
               'It is not a scheduler, an OWL reasoner or an access-control enforcement engine.', '',
               '| Scope | Query count | Destination |', '| --- | ---: | --- |']
    for scope, ids in plan['scopes'].items():
        destination = ('The deterministic owner of the named user.' if scope.startswith('authority_key:')
                       else 'All configured private-data authorities, including Mist.' if scope == 'authorities'
                       else f'The configured {scope} tier.')
        readme.append(f'| `{scope}` | {len(ids)} | {destination} |')
    readme += ['', '`[merge]` specifies set union for designated multi-source SELECT results',
               'and boolean OR for the listed ASK queries. Set union removes duplicate rows;',
               'it does not implement arbitrary distributed joins or global OWL inference.',
               'Other queries follow their assigned single scope. `[privacy]` records',
               'restricted/confidential query classifications; labels alone are not',
               'authorization. Instance partitioning and projection checks are separate.', '',
               'User-specific routing and fragment construction must use the same authority',
               'ordering. The active authority list includes Mist and all three Edge nodes.',
               'Adding/removing authorities can change assignment. A profile import list',
               'does not itself select query destinations.', '',
               '## Updating the catalogue', '',
               'Maintain unique IDs, source text, expectations, category and traceability',
               'in `catalog.csv`; update the routing/merge/privacy entries for the same IDs.',
               'Then regenerate and validate:', '', '```bash',
               'python tools/generate_project_indexes.py',
               'python tools/generate_reference_docs.py',
               'python tools/check_documentation.py',
               'continuum-bench validate', '```', '',
               'Changes affect semantic fingerprints and require synchronization/restart',
               'before a new physical run. See [Ontology distribution](../docs/ONTOLOGY_DISTRIBUTION.md)',
               'and [Ontology review](../docs/ONTOLOGY_REVIEW.md).', '']
    return {'docs/PYTHON_REFERENCE.md': '\n'.join(guide),
            'queries/ALL_QUERIES.md': '\n'.join(bundle), 'queries/README.md': '\n'.join(readme)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    stale = []
    for name, text in render().items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_text() != text:
                stale.append(name)
        else:
            path.write_text(text)
    if stale:
        raise SystemExit('Stale indexes: ' + ', '.join(stale))

if __name__ == '__main__':
    main()
