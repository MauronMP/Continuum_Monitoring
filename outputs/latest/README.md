# Latest adaptive monitoring campaign

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
