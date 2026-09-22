import csv

import pytest

from continuum_bench.monitoring.load_reporting import plot_load_comparison
from continuum_bench.monitoring.report_profiles import CURRENT_PROFILES


@pytest.mark.parametrize('profiles', [CURRENT_PROFILES, ('owlrl', 'rdfs_owlrl'), ('konclude',)])
def test_load_plots_use_only_recorded_profiles(tmp_path, monkeypatch, profiles):
    from continuum_bench.monitoring import load_reporting
    import matplotlib.pyplot as plt
    captured = []
    def save(fig, path):
        captured.extend(text.get_text() for legend in fig.legends for text in legend.get_texts())
        plt.close(fig)
        return []
    monkeypatch.setattr(load_reporting, '_save', save)
    # Metadata validation has its own contract tests; exercise plot generation here.
    monkeypatch.setattr(load_reporting, 'require_release_metadata', lambda path: {})
    rows = [dict(architecture='physical', reasoner=reasoner, profile='eps-50',
                 dimension='events_per_second', events_per_second='50', synthetic_users='500',
                 target_triples='25000', rule_count='25', node_count='5',
                 status='completed', latency_p50_ms='0', latency_p95_ms='10',
                 latency_p99_ms='15', events_processed_per_second='40') for reasoner in profiles]
    path=tmp_path/'summary.csv'
    with path.open('w', newline='') as handle:
        writer=csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    original=path.read_bytes()
    outputs=plot_load_comparison(tmp_path)
    data=list(csv.DictReader(outputs[0].open()))
    assert {r['reasoner'] for r in data} == set(profiles)
    assert path.read_bytes() == original
    assert all(float(r['latency_p50_ms_median']) == 0 for r in data)
    from continuum_bench.monitoring.report_profiles import LABELS
    assert set(captured) & set(LABELS.values()) == {LABELS[r] for r in profiles}
