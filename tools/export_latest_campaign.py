#!/usr/bin/env python3
"""Replace the publishable latest campaign, preserving raw evidence and its baseline."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(root, source, prune=False):
    root=root.resolve();source=source.resolve();outputs=root/'outputs'
    if not source.is_relative_to(outputs/'adaptive-monitoring'):
        raise ValueError('Source must be an archived adaptive-monitoring campaign')
    decisions=json.loads((source/'decisions.json').read_text())
    if not decisions or any(d['status'] in ('observing','deploying','verifying','planned') for d in decisions):
        raise ValueError('Campaign is incomplete or is only a plan; refusing replacement')
    provenance=json.loads((source/'provenance.json').read_text())
    baseline=Path(provenance['baseline'])
    if not baseline.is_absolute():baseline=source/baseline
    if not baseline.exists():raise ValueError('Missing baseline evidence')
    target=outputs/'latest';staging=outputs/'.latest-staging';backup=outputs/'.latest-backup'
    if staging.exists() or backup.exists():raise ValueError('Unfinished export exists; inspect staging/backup first')
    shutil.copytree(source,staging)
    # Verify copied evidence byte-for-byte before changing portable metadata.
    for f in source.rglob('*'):
        if f.is_file() and digest(f)!=digest(staging/f.relative_to(source)):
            raise ValueError(f'Copy verification failed: {f}')
    if baseline.is_relative_to(source):relative=baseline.relative_to(source)
    else:
        relative=Path('baseline')/baseline.name
        shutil.copytree(baseline,staging/relative)
        for f in baseline.rglob('*'):
            if f.is_file() and digest(f)!=digest(staging/relative/f.relative_to(baseline)):
                raise ValueError(f'Baseline copy verification failed: {f}')
    (staging/'archive-location.json').write_text(json.dumps(dict(campaign_id=source.name,baseline_relative=str(relative),original_provenance_preserved=True),indent=2)+'\n')
    shutil.copy2(root/'tools/report_latest_campaign.py',staging/'regenerate_figures.py')
    # Preserve the actual source tree used by the campaign, including uncommitted implementation.
    from subprocess import check_output
    code="from continuum_bench.protocol import SOFTWARE_BUILD_ID; print(SOFTWARE_BUILD_ID)"
    build=check_output([str(root/'.venv/bin/python'),'-c',code],cwd=root,text=True).strip()
    if build!=provenance['coordinator_build_id']:
        raise ValueError('Current source differs from archived build; provide the matching source before publication')
    with tarfile.open(staging/'source-snapshot.tar.gz','w:gz') as archive:
        for name in ('src','configs','ontology','queries','containers','tools','pyproject.toml','requirements-node.txt','requirements.txt'):
            path=root/name
            candidates=path.rglob('*') if path.is_dir() else [path]
            for f in candidates:
                if not f.is_file() or f.is_symlink():continue
                if any(part in ('target','__pycache__','local','.venv','.git') for part in f.relative_to(root).parts):continue
                if f.name.endswith('.local.toml') or f.name.startswith('.env'):continue
                archive.add(f,arcname=str(f.relative_to(root)),recursive=False)
    (staging/'README.md').write_text('''# Latest adaptive monitoring campaign

This directory is the only publishable results snapshot. Failed attempts are retained. Historical campaigns are not combined with this one.

Start with [review/ASSESSMENT.md](review/ASSESSMENT.md). The curated figure index is [review/manifest.json](review/manifest.json): adaptation triggers, attempt trajectories, warm-up/execution intervals, CPU/RAM traces, placement and the whole campaign timeline. The original detailed comparison figures remain in `figures/`.

Raw evidence: `decisions.json`, `configuration.json`, `policy.json`, per-attempt directories, and the nested `baseline/`. `archive-location.json` gives the portable baseline location. Original metadata, including original machine paths and VPN addresses, is retained as provenance; these historical paths need not exist on the reader's machine.

Regenerate the curated figures from this directory, without accessing the workers:

```bash
python -m venv .report-venv
.report-venv/bin/pip install numpy==2.5.1 matplotlib==3.11.1
.report-venv/bin/python regenerate_figures.py .
```

Use the Python version recorded in the experiment environment when available. The source snapshot matches the recorded coordinator build ID; generated build products and local configuration are excluded. Raw node package versions are in each engine metadata file. No raw benchmark needs to run to regenerate these figures.

`SHA256SUMS.json` covers every published file except itself. Verify after copying:

```bash
python -c "import hashlib,json,pathlib; p=pathlib.Path('.'); d=json.loads((p/'SHA256SUMS.json').read_text()); assert all(hashlib.sha256((p/n).read_bytes()).hexdigest()==h for n,h in d.items()); print('All checksums match')"
```

Replacing this directory removes earlier results from the next Git working tree snapshot. It does not erase previously published Git history. No history rewrite is performed.
''')
    checksums={str(f.relative_to(staging)):digest(f) for f in sorted(staging.rglob('*')) if f.is_file() and f.name!='SHA256SUMS.json'}
    (staging/'SHA256SUMS.json').write_text(json.dumps(checksums,indent=2)+'\n')
    if target.exists():target.rename(backup)
    staging.rename(target)
    if backup.exists():shutil.rmtree(backup)
    removed=[]
    if prune:
        for name in ('adaptive-monitoring','container-scale','comparison','suites','audit'):
            directory=outputs/name
            if directory.exists():shutil.rmtree(directory);removed.append(name)
    print(json.dumps(dict(published=str(target),files=len(checksums),removed=removed),indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path)
    parser.add_argument('--prune',action='store_true',help='Remove old result campaigns after verified publication; retain operational runtime files')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    source=args.input_dir
    if source is None:
        candidates=sorted((root/'outputs/adaptive-monitoring').glob('*/decisions.json'))
        if not candidates:parser.error('No adaptive campaign found')
        source=candidates[-1].parent
    export(root,source,args.prune)
