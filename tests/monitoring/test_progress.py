import json

from continuum_bench.monitoring.progress import PointProgress


def test_progress_is_printed_and_persisted_atomically(tmp_path, capsys):
    progress = PointProgress(tmp_path, 'physical-replicated-scalability', 2)

    progress.start(reasoner='rdfs', users=10, phase='prepare')
    progress.finish('completed', reasoner='rdfs', users=10)

    output = capsys.readouterr().out
    assert 'point=1/2 percent=50.0 status=running' in output
    assert 'point=1/2 percent=50.0 status=completed' in output
    state = json.loads((tmp_path / 'progress.json').read_text())
    assert state['completed_points'] == 1
    assert state['total_points'] == 2
    assert state['current']['reasoner'] == 'rdfs'
    assert not list(tmp_path.glob('.progress.*.tmp'))
