import pytest

from continuum_bench.protocol import wait_ready


def test_wait_ready_has_global_deadline():
    with pytest.raises(TimeoutError):
        wait_ready("http://127.0.0.1:1", deadline_seconds=0.05)
