import ast
from pathlib import Path
import pytest
from continuum_bench.core import GeographicPosition
from continuum_bench.core.contracts import ReasoningResult
from continuum_bench.reasoners import get_reasoner, register_reasoner

@pytest.mark.parametrize('kwargs',[{'latitude':91,'longitude':0},{'latitude':1},{'latitude':0,'longitude':float('nan')}])
def test_geographic_position_rejects_invalid_coordinates(kwargs):
    with pytest.raises(ValueError): GeographicPosition(**kwargs)

def test_core_has_no_dependency_on_monitoring_or_adapters(root):
    for path in (root/'src/continuum_bench/core').glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom):
                assert node.level <= 1
                assert 'monitoring' not in (node.module or '')

def test_experiment_can_register_a_reasoner_without_backend_branching(monkeypatch):
    from continuum_bench import reasoners
    monkeypatch.setattr(reasoners, "_BACKENDS", dict(reasoners._BACKENDS))
    class Custom:
        name='test-custom'
        def materialize(self,source): return ReasoningResult(source,0,len(source),len(source))
    register_reasoner(Custom(),replace=True)
    assert get_reasoner('test-custom').materialize([1]).output_triples == 1
