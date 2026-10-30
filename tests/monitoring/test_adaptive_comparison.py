"""Reporting must preserve missing values and explicit workload denominators."""
import importlib.util
from pathlib import Path
import math

import pytest

SCRIPT = Path(__file__).resolve().parents[2]/'tools/report_adaptive_comparison.py'
spec = importlib.util.spec_from_file_location('adaptive_comparison', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_docker_memory_units_are_not_confused_with_ram_percent():
    assert module.memory_mib('1.5GiB / 2GiB') == 1536
    assert module.memory_mib('256MiB / 1.5GiB') == 256
    assert math.isnan(module.memory_mib('--'))


def test_docker_json_formats():
    assert module.json_rows('{"x":1}\n{"x":2}\n') == [{'x':1},{'x':2}]
    assert module.json_rows('[{"x":1}]') == [{'x':1}]
    assert module.json_rows('') == []


def test_invalid_numeric_measurement_stays_missing():
    assert math.isnan(module.number(''))
    assert math.isnan(module.number('nan'))
    assert module.number('0') == 0


def test_missing_baseline_is_not_silently_replaced(tmp_path):
    (tmp_path/'decisions.json').write_text('[]')
    (tmp_path/'provenance.json').write_text('{"baseline":"/nonexistent-continuum-evidence"}')
    with pytest.raises(FileNotFoundError,match='Baseline evidence unavailable'):
        module.comparison(tmp_path)


def test_physical_costs_follow_relocated_service():
    from continuum_bench.monitoring.adaptive_monitoring.docker_figures import remap_nodes
    from continuum_bench.monitoring.container_scale.resources import aggregate_nodes
    rows=[dict(node_id=n,status='completed',layout='distributed',reasoner='rdfs',run_id='1',process_cpu_ms='1000') for n in ('cloud-c1','edge2-c1')]
    mapped=remap_nodes(rows,{'cloud-c1':'cloud','edge2-c1':'cloud'})
    aggregated=aggregate_nodes(mapped,'process_cpu_ms',1000)
    assert aggregated=={('cloud','distributed','rdfs','1'):2.0}


def test_shared_node_axes_include_every_hosts_cost(tmp_path,monkeypatch):
    import json,csv
    import matplotlib.pyplot as plt
    from continuum_bench.monitoring.adaptive_monitoring import docker_figures as module
    baseline=tmp_path/'baseline';baseline.mkdir()
    output=tmp_path/'adaptive';output.mkdir();(output/'analysis').mkdir();(output/'figures').mkdir()
    config={'scenarios':[dict(name='users-1',family='users',users=1)],'experiment':{'reasoners':['rdfs']}}
    (output/'configuration.json').write_text(json.dumps(config))
    (baseline/'campaign.json').write_text(json.dumps({'steps':[dict(scenario='users-1',containers_per_host=1)]}))
    placement=baseline/'placement-1';placement.mkdir()
    (placement/'placement.json').write_text(json.dumps({'physical_hosts':[{'id':'cloud'},{'id':'edge1'}]}))
    path=placement/'users-1/measured/distributed-reasoning-scalability';path.mkdir(parents=True)
    rows=[dict(node_id=node,status='completed',layout='distributed',reasoner='rdfs',run_id='1',process_cpu_ms=cpu,current_rss_kib=1024,reasoning_ms=1000,input_triples=10) for node,cpu in [('cloud-c1',1000),('edge1-c1',100000)]]
    with (path/'node-runs.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    checked=[]
    def check(fig,folder,name,manifest):
        if name.endswith('-nodes-cpu.png'):
            assert all(ax.get_ylim()[1]>100 for ax in fig.axes if ax.get_visible())
            checked.append(True)
        plt.close(fig)
    monkeypatch.setattr(module,'save_figure',check)
    decision=dict(scenario='users-1',layout='distributed',attempt=1,status='not_recovered',results='users-1-distributed-1-1/measured/distributed-reasoning-scalability')
    module.docker_figures(output,baseline,[decision],output/'figures')
    assert checked


def test_paired_metrics_keep_unattempted_requests_distinct_from_failures(tmp_path):
    import csv
    from continuum_bench.monitoring.adaptive_monitoring.paired_figures import metrics
    rows=[dict(layout='distributed',reasoner='rdfs',status='timeout')]
    with (tmp_path/'distributed-reasoning-summary.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result=metrics(tmp_path,'distributed','rdfs')
    assert result['prepared']==0 and result['preparations']==1
    assert math.isnan(result['completion_percent'])
    rows=[dict(layout='distributed',reasoner='rdfs',concurrency=8,client_requests=8,error_count=8)]
    with (tmp_path/'query-scalability.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    assert metrics(tmp_path,'distributed','rdfs',8)['completion_percent']==0
    assert math.isnan(metrics(tmp_path,'distributed','rdfs',1)['completion_percent'])
