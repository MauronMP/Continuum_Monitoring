# Reviewing and publishing only the latest campaign

The publishable snapshot is `outputs/latest/`. It contains one adaptive campaign and its own Docker-only baseline; both are required for a valid comparison. Operational files in `outputs/runtime/` remain local and ignored by Git.

After a new campaign finishes, generate the review and replace the snapshot:

```bash
source .venv/bin/activate
python tools/report_latest_campaign.py outputs/adaptive-monitoring/RUN_ID
python tools/export_latest_campaign.py --input-dir outputs/adaptive-monitoring/RUN_ID --prune
```

`--prune` removes previous adaptive, container-scale, comparison, suite and audit result directories only after copying and checking the latest campaign. It preserves the baseline inside the latest snapshot. Omit it to retain local history. The exporter rejects incomplete/planned campaigns or a current source build that differs from the recorded build. Do not export while a campaign is running. Only the reviewed campaign is automatically selected if `--input-dir` is omitted; review the selected run before pruning.

The snapshot includes raw evidence, PNGs, structured review data, a matching source snapshot, a standalone figure generator and SHA-256 checksums. Failed and unsuccessful attempts are included. Read `outputs/latest/review/ASSESSMENT.md` for the current interpretation. Subsequent campaigns need their own assessment; the exporter does not invent an assessment.

To publish the prepared results and the maintenance tools, without staging unrelated project changes:

```bash
git add .gitignore outputs/latest tools/report_latest_campaign.py tools/export_latest_campaign.py docs/LATEST_RESULTS.md
git diff --cached --stat
git commit -m "Publish latest adaptive campaign with evolution and resource analysis"
git push origin HEAD
```

Authenticate Git locally before pushing. Never commit credentials. Later exports replace the same path, so the current repository tree holds only the latest campaign. Previous commits still contain their historical snapshots; this workflow does not rewrite Git history.

To regenerate the curated review from a clone without workers, follow `outputs/latest/README.md`. Original provenance retains historical machine paths; `archive-location.json` identifies the portable baseline inside the snapshot. The dedicated standalone generator uses archived evidence and does not need those machine paths.
