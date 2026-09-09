import csv
from pathlib import Path
from continuum_bench.monitoring.publication import outcome, Report
from continuum_bench.monitoring.suite import suite_plan


def test_skipped_points_are_not_observed_timeouts():
    assert outcome({'status':'skipped_after_timeout'}) == 'skipped'
    assert outcome({'status':'prepare_timeout'}) == 'timeout'


def test_patient_suite_applies_budget_and_preserves_all_families(root,tmp_path):
    plan=suite_plan(root,root/'configs/benchmark.toml',tmp_path,patient=True,repetitions=5)
    assert {'monitoring-sharded','monitoring-replicated','load','experiments','campaign','report','software','owl-validation','start-workers'} <= {step['name'] for step in plan}
    for step in plan:
        if step['name']=='software':continue
        assert '--timeout-seconds' in step['command']
        assert '3600' in step['command']
        assert '--keep-going' in step['command']
        assert step['command'][step['command'].index('--repetitions')+1]=='5'


def test_report_does_not_fabricate_completed_timings(root,tmp_path):
    report=Report(root,tmp_path,tmp_path/'paper')
    report.curves([{'status':'timeout','x':'1','time':'100'}],'x',[('time','Time',1)],'censored')
    assert not report.figures
    assert 'no completed measurements' in report.findings[0]


def test_curves_preserve_zero_measurements_and_png_only(root,tmp_path):
    report=Report(root,tmp_path,tmp_path/'paper')
    report.curves([{'status':'completed','x':'1','cpu':'0','reasoner':'rdfs'}],'x',[('cpu','CPU',1)],'zero-cpu')
    assert len(report.figures)==1
    assert Path(report.figures[0]).suffix=='.png'


def test_suite_detects_incomplete_rows_even_when_process_succeeds(root,tmp_path,monkeypatch):
    from types import SimpleNamespace
    from continuum_bench.monitoring import suite
    def run(command, **kwargs):
        if 'load' in command:
            destination=Path(command[command.index('--output-dir')+1])/'physical'
            destination.mkdir(parents=True)
            (destination/'summary.csv').write_text('status\ntimeout\n')
        return SimpleNamespace(returncode=0)
    from continuum_bench.monitoring import provenance
    monkeypatch.setattr(provenance,'snapshot',lambda *args: {})
    monkeypatch.setattr(suite.subprocess,'run',run)
    result=suite.run_suite(root,root/'configs/benchmark.toml',tmp_path,families=['load'])
    load=next(step for step in result['steps'] if step['name']=='load')
    assert load['status']=='failed'
    assert load['incomplete_points']==1


def test_replica_resources_retain_idle_nodes_and_unknown_values():
    from continuum_bench.monitoring.physical import _resource_summary
    prepared={'a':{'process_cpu_ms':2,'peak_rss_kib':20,'current_rss_kib':10},
              'b':{'process_cpu_ms':3,'peak_rss_kib':30,'current_rss_kib':15}}
    responses={'a':{'process_cpu_ms':4,'peak_rss_kib':40,'current_rss_kib':25}}
    result=_resource_summary(prepared,responses)
    assert result['total_process_cpu_ms']==9
    assert result['max_sum_node_current_rss_kib']==40
    assert result['max_node_peak_rss_kib']==40
    assert result['disk_read_bytes'] is None
