"""PNG-only reports from raw evidence, with paired repetition-level statistics."""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path

import numpy as np

from ...csv_utils import write_dict_rows
from .figures import figures, point_table
from .statistics import estimate

def summarize(record):
    events = record.get("events", [])
    row = {key: record[key] for key in ("job_id", "node", "tier", "experiment", "size", "repetition", "strategy",
                                       "status", "resource_count", "policy_count", "event_count", "trace_sha256", "workload_sha256", "timeout_seconds")}
    row["error"] = record.get("error", "")
    if record["status"] == "completed" and events:
        latencies = [e["decision_ms"] for e in events]
        row.update(decision_mean_ms=float(np.mean(latencies)), decision_p95_ms=float(np.percentile(latencies, 95)),
                   coverage=float(np.mean([e["coverage"] for e in events])),
                   over_monitoring=float(np.mean([e["over_monitoring"] for e in events])),
                   plan_correct=float(np.mean([e["plan_correct"] for e in events])),
                   cumulative_decision_ms=events[-1]["cumulative_decision_ms"],
                   setup_ms=record["setup_ms"], reasoning_ms=record["reasoning_ms"],
                   throughput_decisions_per_second=record["throughput_decisions_per_second"],
                   setup_amortized_throughput=record["setup_amortized_throughput"],
                   ram_max_mib=record["measurement"]["ram_max_mib"],
                   setup_ram_max_mib=record["setup_measurement"]["ram_max_mib"],
                   peak_sampled_rss_mib=max(record["measurement"]["ram_max_mib"], record["setup_measurement"]["ram_max_mib"]),
                   cpu_time_ms=record["measurement"]["process_cpu_time_ms"],
                   cpu_mean_percent=record["measurement"]["cpu_mean_percent"],
                   transport_wall_ms=record["transport_wall_ms"])
    return row


def paired_statistics(rows):
    blocks = defaultdict(dict)
    for row in rows:
        if row["status"] == "completed":
            blocks[(row["node"], row["experiment"], row["size"], row["repetition"])][row["strategy"]] = row
    groups = defaultdict(list)
    for (node, experiment, size, repetition), block in blocks.items():
        proposed = block.get("semantic")
        if not proposed:
            continue
        for baseline in ("static", "procedural"):
            reference = block.get(baseline)
            if not reference or reference["trace_sha256"] != proposed["trace_sha256"] or reference["workload_sha256"] != proposed["workload_sha256"]:
                continue
            for metric in ("decision_mean_ms", "setup_ms", "coverage", "over_monitoring", "plan_correct", "ram_max_mib", "peak_sampled_rss_mib", "cpu_time_ms"):
                groups[(node, experiment, size, baseline, metric)].append(proposed[metric] - reference[metric])
    output = []
    for (node, experiment, size, baseline, metric), values in sorted(groups.items()):
        interval = estimate(values, (node, experiment, size, baseline, metric))
        output.append({"node": node, "experiment": experiment, "size": size, "baseline": baseline,
                       "metric": metric, "paired_repetitions": len(values), "semantic_minus_baseline": float(np.mean(values)),
                       "bootstrap_low_95": interval["low"], "bootstrap_high_95": interval["high"],
                       "interval_method": "paired repetition bootstrap; 5000 resamples; stable group seed; minimum n=5"})
    return output


def report(directory: Path):
    directory = Path(directory)
    records = []
    content = (directory / "jobs.jsonl").read_text()
    lines = content.splitlines()
    truncated_tail = False
    for index, line in enumerate(lines):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            if index != len(lines)-1 or content.endswith("\n"):
                raise
            truncated_tail = True
            # Only an unterminated final append may be ignored, visibly.
    if not records:
        raise ValueError("No completed job records available")
    from .validation import validate_records
    validate_records(records)
    rows = [summarize(r) for r in records]
    write_dict_rows(directory / "summary.csv", rows, empty_message="No jobs")
    paired = paired_statistics(rows)
    if paired:
        write_dict_rows(directory / "paired-comparisons.csv", paired, empty_message="No paired jobs")
    else:
        (directory / "paired-comparisons.csv").unlink(missing_ok=True)
    outcomes = defaultdict(int)
    for r in rows:
        outcomes[(r["node"], r["experiment"], r["strategy"], r["status"])] += 1
    write_dict_rows(directory / "outcomes.csv", [dict(zip(("node", "experiment", "strategy", "status", "jobs"), (*k, v))) for k, v in sorted(outcomes.items())], empty_message="No outcomes")
    paths = figures(directory, records, rows)
    from .figures import paired_cost_figure
    paths.extend(paired_cost_figure(directory, paired))
    planned = None
    config_path, metadata_path = directory / "configuration.json", directory / "metadata.json"
    if config_path.is_file() and metadata_path.is_file():
        from .runner import jobs
        config = json.loads(config_path.read_text())
        metadata = json.loads(metadata_path.read_text())
        planned = len(list(jobs(config))) * len(metadata["selected_nodes"])
    from .transport import source_bundle
    import hashlib
    rendering_source = source_bundle()
    (directory / "report-source.zip").write_bytes(rendering_source)
    manifest = {"report_source_sha256": hashlib.sha256(rendering_source).hexdigest(),
                "measurement_contracts": sorted({r.get("measurement_contract", "comparison-v1") for r in records if r["status"] == "completed"}),
                "adaptive_plan_mismatches": sum(not e["plan_correct"] for r in records if r["status"] == "completed" and r["strategy"] != "static" for e in r["events"]),
                "report_version": 2, "truncated_final_record_ignored": truncated_tail,
                "planned_jobs": planned, "unrecorded_jobs": max(0, planned-len(records)) if planned is not None else None,
                "minimum_completed_repetitions": min(p["n"] for p in point_table(records, rows) if p["recorded_jobs"]),
                "figure_data": "figure-data.csv", "captions": "figure-captions.md","summary": "summary.csv", "paired": "paired-comparisons.csv" if paired else None,
                "outcomes": "outcomes.csv", "figures": [str(p.relative_to(directory)) for p in paths],
                "evidence": "jobs.jsonl and <experiment>/raw/*.json", "completed_jobs": sum(r["status"] == "completed" for r in rows),
                "unsuccessful_jobs": sum(r["status"] != "completed" for r in rows)}
    (directory / "report.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
