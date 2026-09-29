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


def test_progression_figure_requires_two_distinct_completed_x_values(root,tmp_path):
    report=Report(root,tmp_path,tmp_path/'paper')
    rows=[
        {'status':'completed','x':'1','cpu':'1','reasoner':'rdfs'},
        {'status':'completed','x':'1','cpu':'2','reasoner':'rdfs'},
    ]
    report.curves(
        rows,
        'x',
        [('cpu','CPU',1)],
        'underpowered-scale-out',
        min_distinct_x=2,
    )
    assert not report.figures
    assert 'suppressed because only 1 distinct completed x value' in report.findings[0]


def test_rejected_report_retains_only_integrity_diagnostics(root,tmp_path):
    report=Report(root,tmp_path,tmp_path/'paper')
    report.figures=[
        str(report.output/'coverage-and-integrity/execution-coverage.png'),
        str(report.output/'queries/expensive-queries-distributed.png'),
    ]
    suppressed=report.apply_publication_gate({
        'accepted_for_performance_claims':False,
    })
    assert [Path(path).stem for path in report.figures] == ['execution-coverage']
    assert [Path(path).stem for path in suppressed] == [
        'expensive-queries-distributed'
    ]


def test_rejected_report_removes_derived_performance_tables(root, tmp_path):
    report=Report(root,tmp_path,tmp_path/'paper')
    report.output.mkdir(parents=True, exist_ok=True)
    for name in ('execution-coverage.csv', 'data-integrity.csv',
                 'query-ranking.csv', 'placement-comparison.csv'):
        (report.output/name).write_text('value\n1\n')
    report.figures=[
        str(report.output/'coverage-and-integrity/execution-coverage.png')
    ]
    report.statistics=[
        {'figure':'execution-coverage', 'median':1},
        {'figure':'placement-scalability-rdfs', 'median':2},
    ]

    suppressed=report.apply_table_gate({
        'accepted_for_performance_claims':False,
    })

    assert {Path(path).name for path in suppressed} == {
        'query-ranking.csv', 'placement-comparison.csv'
    }
    assert (report.output/'execution-coverage.csv').is_file()
    assert (report.output/'data-integrity.csv').is_file()
    assert report.statistics == [
        {'figure':'execution-coverage', 'median':1}
    ]


def test_png_quality_audit_tracks_only_existing_nonblank_pngs(root, tmp_path):
    import json
    from PIL import Image, ImageDraw

    report=Report(root,tmp_path,tmp_path/'paper')
    path=report.output/'coverage-and-integrity/diagnostic.png'
    path.parent.mkdir(parents=True,exist_ok=True)
    image=Image.new('RGB',(320,240),'white')
    ImageDraw.Draw(image).rectangle((20,20,300,220),fill='green')
    image.save(path)

    audit_path=Path(report.write_png_quality_audit())
    rows=json.loads(audit_path.read_text())

    assert len(rows) == 1
    assert rows[0]['path'] == 'coverage-and-integrity/diagnostic.png'
    assert rows[0]['width'] == 320
    assert rows[0]['height'] == 240
    assert rows[0]['colors_sampled'] >= 2
    assert rows[0]['near_blank'] is False


def test_report_rejects_stale_release_and_topology(root, tmp_path):
    import json
    metadata = tmp_path/'load/metadata.json'
    metadata.parent.mkdir(parents=True)
    metadata.write_text(json.dumps({
        'runtime_versions': {'continuum-ontology-benchmark': '0.4.0'},
        'available_endpoints': [{'url': f'http://node-{i}'} for i in range(5)],
    }))
    report = Report(root, tmp_path, tmp_path/'paper')
    assert report.evidence_context['version_compatible'] is False
    assert report.evidence_context['topology_compatible'] is False
    assert report.evidence_context['current_topology_node_count'] == 6


def test_report_accepts_current_distribution_metadata(root, tmp_path):
    import json
    from continuum_bench import __version__

    metadata = tmp_path / 'load/metadata.json'
    metadata.parent.mkdir(parents=True)
    metadata.write_text(json.dumps({
        'runtime_versions': {'continuum-monitoring-benchmark': __version__},
        'available_endpoints': [
            {'url': f'http://node-{index}'} for index in range(6)
        ],
    }))
    report = Report(root, tmp_path, tmp_path / 'paper')
    assert report.evidence_context['version_compatible'] is True
    assert report.evidence_context['topology_compatible'] is True


def test_evidence_readiness_is_a_normalized_png(root, tmp_path):
    report = Report(root, tmp_path, tmp_path/'paper')
    report.evidence_readiness(
        {'physical/load': [
            {'status': 'completed'}, {'status': 'timeout'},
            {'status': 'skipped_after_timeout'},
        ]},
        {'status': 'rejected', 'blocking_findings': ['incomplete']},
    )
    assert Path(report.figures[0]).name == 'evidence-readiness.png'


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


def test_empty_generated_csv_removes_stale_file(tmp_path):
    from continuum_bench.monitoring.publication import write_csv

    path=tmp_path/'stale.csv'
    path.write_text('old\nvalue\n')

    write_csv(path, [])

    assert not path.exists()


def test_quality_figures_expose_semantic_failures_and_capacity(root, tmp_path):
    import matplotlib.pyplot as plt
    validation = tmp_path/'monitoring/distributed/scalability/result-validation.csv'
    validation.parent.mkdir(parents=True)
    validation.write_text(
        'reasoner,query_id,valid\n'
        'rdfs,Q1,True\n'
        'konclude,Q1,False\n'
    )
    report = Report(root, tmp_path, tmp_path/'paper')
    captured = []
    report.save = lambda fig, name, caption: (captured.append(name), plt.close(fig))
    datasets = {
        'distributed/scalability': [
            {'reasoner':'rdfs','status':'completed','synthetic_users':'10'},
            {'reasoner':'konclude','status':'invalid_results','synthetic_users':'10'},
        ],
        'replicated/scalability': [
            {'reasoner':'rdfs','status':'completed','synthetic_users':'100'},
        ],
        'distributed/cumulative': [
            {'reasoner':'rdfs','status':'completed','stage':'16'},
        ],
        'replicated/cumulative': [
            {'reasoner':'rdfs','status':'completed','stage':'16'},
        ],
        'physical/load': [
            {'reasoner':'rdfs','dimension':'users','status':'timeout'},
            {'reasoner':'rdfs','dimension':'users','status':'completed'},
        ],
    }
    report.quality_figures(datasets)
    assert {'semantic-equivalence-coverage', 'reasoner-capacity-frontier',
            'load-completion-matrix'} <= set(captured)


def test_policy_figures_skip_profiles_without_completed_requests(root, tmp_path):
    import matplotlib.pyplot as plt
    events = tmp_path/'load/event-runs.csv'
    events.parent.mkdir(parents=True)
    events.write_text(
        'profile,reasoner,query_id,processed,engine_duration_ms,process_cpu_ms,current_rss_kib\n'
        'p,rdfs,BASE-Q01,true,2,1,1024\n'
        'p,hermit,BASE-Q01,false,,,,\n'
    )
    report = Report(root, tmp_path, tmp_path/'paper')
    captured=[]
    report.save=lambda fig,name,caption:(captured.append(name),plt.close(fig))
    report.policy_costs()
    assert 'category-cost-rdfs' in captured
    assert 'category-cost-hermit' not in captured
    assert 'category-tail-and-total-hermit' not in captured


def test_comparisons_render_all_observed_profiles_for_current_layouts(root, tmp_path):
    import matplotlib.pyplot as plt
    from continuum_bench.monitoring.comparative_reporting import generate_comparisons
    from continuum_bench.monitoring.report_profiles import CURRENT_PROFILES, LABELS
    report = Report(root, tmp_path, tmp_path/'paper')
    profiles = tuple(dict.fromkeys((*CURRENT_PROFILES, 'owlrl', 'rdfs_owlrl')))
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


def test_comparisons_do_not_claim_placement_with_one_layout(root, tmp_path):
    import matplotlib.pyplot as plt
    from continuum_bench.monitoring.comparative_reporting import generate_comparisons
    report = Report(root, tmp_path, tmp_path/'paper')
    report.read = lambda path: ([dict(reasoner='hermit', status='completed', synthetic_users='1', repetition='1', total_wall_ms='0')]
                               if str(path).endswith('distributed/scalability/summary.csv') else [])
    report.save = lambda fig, *args: plt.close(fig)
    generate_comparisons(report)
    assert not (report.output/'placement-comparison.csv').exists()
    assert any(
        'placement-scalability-hermit: suppressed' in finding
        for finding in report.findings
    )


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
