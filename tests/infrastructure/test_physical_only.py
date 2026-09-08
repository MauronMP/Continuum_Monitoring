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
    assert {path.name for path in (root / 'configs/topologies').iterdir()} == {'physical'}
