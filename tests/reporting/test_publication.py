import csv
from pathlib import Path
from continuum_bench.monitoring.publication import outcome, Report
from continuum_bench.monitoring.suite import suite_plan


def test_skipped_points_are_not_observed_timeouts():
    assert outcome({'status':'skipped_after_timeout'}) == 'skipped'
    assert outcome({'status':'prepare_timeout'}) == 'timeout'


def test_patient_suite_applies_budget_and_preserves_all_families(root,tmp_path):
    plan=suite_plan(root,root/'configs/benchmark.toml',tmp_path,patient=True,repetitions=5)
    assert {'monitoring-distributed','monitoring-replicated','load','experiments','campaign','report','software','owl-validation','start-workers'} <= {step['name'] for step in plan}
    for step in plan:
        if step['name'] in {'software', 'documentation'}:continue
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
            destination=Path(command[command.index('--output-dir')+1])
            destination.mkdir(parents=True)
            (destination/'summary.csv').write_text('status\ntimeout\n')
        return SimpleNamespace(returncode=0)
    from continuum_bench.monitoring import provenance
    monkeypatch.setattr(provenance,'snapshot',lambda *args: {})
    monkeypatch.setattr(suite.subprocess,'run',run)
    result=suite.run_suite(root,root/'configs/benchmark.toml',tmp_path,families=['load'])
    load=next(step for step in result['steps'] if step['name']=='load')
    assert load['status']=='timeout'
    assert load['returncode']==0
    assert load['outcomes']['timeout']==1
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


def test_comparative_population_requires_completed_coverage_in_every_group():
    from continuum_bench.monitoring.comparative_reporting import matched_users
    first = [{'synthetic_users':'10','status':'completed'}, {'synthetic_users':'100','status':'completed'}]
    second = [{'synthetic_users':'10','status':'timeout'}, {'synthetic_users':'100','status':'completed'}]
    assert matched_users([first,second]) == 100
    assert matched_users([first,[]]) is None


def test_comparative_statistics_preserve_zero_and_exclude_missing():
    from continuum_bench.monitoring.comparative_reporting import summarize
    rows = [{'role':'cloud','duration_ms':'0'}, {'role':'cloud','duration_ms':'10'},
            {'role':'edge','duration_ms':''}, {'role':'edge','duration_ms':'nan'}]
    result = summarize(rows,['role'],'duration_ms')
    assert len(result) == 1
    assert result[0]['n'] == 2
    assert result[0]['median'] == 5
    assert result[0]['total'] == 10


def test_figure_groups_keep_query_and_node_panels_distinct():
    from continuum_bench.monitoring.publication import figure_group
    assert figure_group('expensive-queries-sharded') == 'queries'
    assert figure_group('node-category-sharded-rdfs') == 'nodes-and-layers'
    assert figure_group('placement-scalability-rdfs') == 'scalability-and-placement'


def test_publication_reads_large_federated_result_bags(tmp_path):
    from continuum_bench.monitoring.publication import read_csv
    path = tmp_path/'node-query-runs.csv'
    path.write_text('query_id,result_keys\nQ,' + 'a'*200000 + '\n')
    assert len(read_csv(path)[0]['result_keys']) == 200000


def test_comparisons_render_all_observed_profiles_for_current_layouts(root, tmp_path):
    import matplotlib.pyplot as plt
    from continuum_bench.monitoring.comparative_reporting import generate_comparisons
    from continuum_bench.monitoring.report_profiles import CURRENT_PROFILES, LABELS
    report = Report(root, tmp_path, tmp_path/'paper')
    profiles = (*CURRENT_PROFILES, 'owlrl', 'rdfs_owlrl')
    def read(path):
        if path.name == 'summary.csv':
            return [dict(reasoner=r, status='completed', synthetic_users='10', stage='1', repetition='1', total_wall_ms='12') for r in profiles]
        if path.name in ('node-query-runs.csv', 'query-runs.csv'):
            return [dict(reasoner=r, status='completed', synthetic_users='10', repetition='1', role='cloud', category='C', query_id='Q', duration_ms='2') for r in profiles]
        return []
    captured = {}
    def save(fig, name, caption):
        captured[name] = [ax.get_title() for ax in fig.axes]
        plt.close(fig)
    report.read = read
    report.save = save
    generate_comparisons(report)
    assert [title for title in captured['category-evaluation-methods'] if title] == [LABELS[r] for r in profiles]
    assert 'expensive-queries-distributed' in captured
    assert 'expensive-queries-sharded' not in captured
    rows = list(csv.DictReader((report.output/'placement-comparison.csv').open()))
    assert {r['layout'] for r in rows} == {'distributed', 'replicated'}
    assert {r['reasoner'] for r in rows} == set(profiles)


def test_comparisons_accept_a_single_available_profile(root, tmp_path):
    import matplotlib.pyplot as plt
    from continuum_bench.monitoring.comparative_reporting import generate_comparisons
    report = Report(root, tmp_path, tmp_path/'paper')
    report.read = lambda path: ([dict(reasoner='hermit', status='completed', synthetic_users='1', repetition='1', total_wall_ms='0')]
                               if str(path).endswith('distributed/scalability/summary.csv') else [])
    report.save = lambda fig, *args: plt.close(fig)
    generate_comparisons(report)
    rows = list(csv.DictReader((report.output/'placement-comparison.csv').open()))
    assert len(rows) == 1
    assert rows[0]['reasoner'] == 'hermit'
    assert float(rows[0]['median']) == 0


def test_suite_records_censoring_and_real_failures(root, tmp_path, monkeypatch):
    from types import SimpleNamespace
    from continuum_bench.monitoring import suite, provenance
    monkeypatch.setattr(provenance, 'snapshot', lambda *args: {})
    for statuses, code, expected in [('skipped_after_timeout', 0, 'skipped'), ('failed', 0, 'failed'), ('completed', 2, 'failed'), ('', 0, 'missing_evidence')]:
        def run(command, **kwargs):
            if 'load' in command:
                destination=Path(command[command.index('--output-dir')+1])
                destination.mkdir(parents=True)
                (destination/'summary.csv').write_text('status\n'+statuses+'\n')
            return SimpleNamespace(returncode=code)
        monkeypatch.setattr(suite.subprocess, 'run', run)
        result=suite.run_suite(root, root/'configs/benchmark.toml', tmp_path, families=['load'])
        step=next(s for s in result['steps'] if s['name']=='load')
        assert step['status'] == expected
        assert step['returncode'] == code


def test_suite_forwards_explicit_timeout_over_patient_default(root, tmp_path):
    plan = suite_plan(root, root/'configs/benchmark.toml', tmp_path, patient=True, timeout_seconds=42, families=['monitoring'])
    for step in plan:
        assert step['command'][step['command'].index('--timeout-seconds')+1] == '42'
    assert {s['command'][s['command'].index('--layout')+1] for s in plan if '--layout' in s['command']} == {'distributed', 'replicated'}


def test_suite_forwards_independent_policy_options(root, tmp_path):
    plan=suite_plan(root, root/'configs/benchmark.toml', tmp_path,
                    timeout_mode='bounded', request_timeout_seconds=11,
                    phase_timeout_seconds=22, point_timeout_seconds=33,
                    skip_after_timeouts=2, skip_repetitions=False,
                    skip_larger_points=True, skip_cumulative_stages=False,
                    keep_going=True)
    for step in plan:
        command=step['command']
        if step['name'] in {'software', 'documentation'}:
            assert '--timeout-mode' not in command
            continue
        for flag, value in [('timeout-mode','bounded'), ('request-timeout-seconds','11'),
                            ('phase-timeout-seconds','22'), ('point-timeout-seconds','33'),
                            ('skip-after-timeouts','2')]:
            assert command[command.index('--'+flag)+1]==value
        assert {'--no-skip-repetitions','--skip-larger-points','--no-skip-cumulative-stages','--keep-going'} <= set(command)
        assert '--unlimited' not in command


def test_suite_unspecified_policy_preserves_config(root, tmp_path):
    plan=suite_plan(root, root/'configs/benchmark.toml', tmp_path, families=['monitoring'])
    for step in plan:
        assert not any('timeout' in arg or 'skip-' in arg for arg in step['command'])
        assert '--keep-going' not in step['command']


def test_archived_summary_read_preserves_labels_and_bytes(root, tmp_path):
    import json
    from continuum_bench.reasoners import REASONING_CONTRACT
    from continuum_bench.specification import ONTOLOGY_VERSION, ONTOLOGY_REVISION, EXPECTED_QUERY_IDS
    directory=tmp_path/'monitoring/sharded/scalability'
    directory.mkdir(parents=True)
    summary=directory/'summary.csv'
    summary.write_text('reasoner,status,profile\nowlrl,completed,old-profile\nrdfs_owlrl,timeout,old-profile\n')
    metadata=directory/'metadata.json'
    metadata.write_text(json.dumps(dict(ontology_version=ONTOLOGY_VERSION,
                                       ontology_revision=ONTOLOGY_REVISION,
                                       query_count=len(EXPECTED_QUERY_IDS),
                                       reasoning_contract=REASONING_CONTRACT,
                                       mode='physical-elastic-authority-sharded')))
    original={p:p.read_bytes() for p in (summary, metadata)}
    report=Report(root,tmp_path,tmp_path/'paper')
    rows=report.read(summary)
    assert [r['reasoner'] for r in rows]==['owlrl','rdfs_owlrl']
    assert {r['profile'] for r in rows}=={'old-profile'}
    assert all(p.read_bytes()==content for p,content in original.items())
    assert not (tmp_path/'monitoring/distributed').exists()
