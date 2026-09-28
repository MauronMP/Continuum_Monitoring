"""Keep removed execution targets out of every public benchmark entry point."""
from importlib.util import find_spec
import pytest
from continuum_bench.cli import _parser


@pytest.mark.parametrize('arguments', [
    ['local', 'all'], ['load', 'local'],
    ['experiment', 'all', 'local'], ['study', 'trace', '--target', 'local'],
])
def test_benchmark_cli_rejects_nonphysical_execution(arguments):
    with pytest.raises(SystemExit) as error:
        _parser().parse_args(arguments)
    assert error.value.code == 2


def test_removed_execution_module_and_inventory_are_absent(root):
    assert find_spec('continuum_bench.benchmark') is None
    assert find_spec('continuum_bench.monitoring.benchmark') is None
    assert find_spec('continuum_bench.engines') is None
    assert find_spec('continuum_bench.engine_stack') is None
    assert find_spec('continuum_bench.external_node') is None
    assert {path.name for path in (root / 'configs/topologies').iterdir()} == {'physical'}


def test_container_deployment_assets_are_absent(root):
    forbidden = {
        root / '.env.example',
        root / 'Dockerfile',
        root / 'docker-compose.yml',
        root / 'docker-compose.yaml',
        root / 'compose.yml',
        root / 'compose.yaml',
    }
    assert not any(path.exists() for path in forbidden)


def test_removed_local_product_matrix_cannot_reappear(root):
    assert not (root / 'engine-service').exists()
    project = (root / 'pyproject.toml').read_text(encoding='utf-8')
    runtime = (root / 'requirements/runtime.txt').read_text(encoding='utf-8')
    assert 'continuum-smoke-engines' not in project
    assert 'pyoxigraph' not in project + runtime
    with pytest.raises(SystemExit) as error:
        _parser().parse_args(['engines'])
    assert error.value.code == 2


@pytest.mark.parametrize('reasoner', ['none', 'owlrl', 'rdfs_owlrl', 'elk'])
def test_physical_cli_rejects_retired_comparison_profiles(reasoner):
    with pytest.raises(SystemExit) as error:
        _parser().parse_args(['physical', 'all', '--reasoner', reasoner])
    assert error.value.code == 2
