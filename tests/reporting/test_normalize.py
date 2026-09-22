import json
import time
from continuum_bench.monitoring.normalize import normalize_completed_outputs

def test_only_new_summaries_receive_a_canonical_envelope(config, tmp_path):
    old=tmp_path/'old';old.mkdir()
    (old/'summary.csv').write_text('status,reasoner\ncompleted,rdfs\n')
    started=time.time_ns()
    current=tmp_path/'current';current.mkdir()
    (current/'summary.csv').write_text('status,reasoner,reasoning_ms\ncompleted,rdfs,12.5\n')
    normalize_completed_outputs(config,tmp_path,started)
    assert not (old/'results.jsonl').exists()
    row=json.loads((current/'results.jsonl').read_text())
    assert row['schema_version']=='continuum.monitoring.v1'
    assert row['reasoner']=='rdfs' and row['status']=='completed'
    assert row['measurements']['reasoning_ms']=='12.5'
    assert row['configuration']['seed']==config.seed


def test_envelope_preserves_historical_identity_and_censoring(config, tmp_path):
    (tmp_path/'summary.csv').write_text('status,reasoner,layout,profile\nskipped_after_timeout,owlrl,sharded,legacy-profile\n')
    normalize_completed_outputs(config, tmp_path, 0)
    row=json.loads((tmp_path/'results.jsonl').read_text())
    assert row['reasoner']=='owlrl'
    assert row['layout']=='sharded'
    assert row['profile']=='legacy-profile'
    assert row['status']=='skipped_after_timeout'
    assert row['outcome']=='skipped'
