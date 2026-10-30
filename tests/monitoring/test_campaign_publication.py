"""Publication must preserve evidence and refuse unfinished campaigns."""
import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

spec=importlib.util.spec_from_file_location('export_latest_campaign',Path(__file__).resolve().parents[2]/'tools/export_latest_campaign.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def fixture_campaign(tmp_path,status='execution_recovered'):
    source=tmp_path/'outputs/adaptive-monitoring/run';source.mkdir(parents=True)
    (source/'decisions.json').write_text(json.dumps([dict(status=status)]))
    baseline=source/'baseline/run';baseline.mkdir(parents=True);(baseline/'raw.csv').write_text('value\n1\n')
    (source/'provenance.json').write_text(json.dumps(dict(baseline=str(baseline),coordinator_build_id='test-build')))
    tools=tmp_path/'tools';tools.mkdir();(tools/'report_latest_campaign.py').write_text('# report\n')
    return source


def test_unfinished_campaign_cannot_replace_snapshot(tmp_path):
    source=fixture_campaign(tmp_path,'verifying')
    with pytest.raises(ValueError,match='incomplete'):
        module.export(tmp_path,source,True)
    assert source.exists() and not (tmp_path/'outputs/latest').exists()


def test_export_verifies_baseline_before_pruning_and_keeps_runtime(tmp_path,monkeypatch):
    source=fixture_campaign(tmp_path)
    runtime=tmp_path/'outputs/runtime';runtime.mkdir();(runtime/'worker-state').write_text('keep')
    monkeypatch.setattr(subprocess,'check_output',lambda *a,**k:'test-build\n')
    module.export(tmp_path,source,True)
    target=tmp_path/'outputs/latest'
    checks=json.loads((target/'SHA256SUMS.json').read_text())
    assert all(module.digest(target/name)==value for name,value in checks.items())
    assert (target/'baseline/run/raw.csv').read_text()=='value\n1\n'
    assert not source.exists() and (runtime/'worker-state').exists()
