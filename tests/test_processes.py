import sys

import pytest

from continuum_bench.processes import CommandFailure, run_logged


def test_streams_and_logs_both_stdout_and_stderr(tmp_path, capsys):
    log = run_logged(
        [
            sys.executable,
            "-c",
            "import sys; print('out'); print('err', file=sys.stderr)",
        ],
        root=tmp_path,
    )
    text = log.read_text()
    assert "out" in text and "err" in text
    assert "out" in capsys.readouterr().out


def test_failed_command_retains_output_exitcode_and_log(tmp_path):
    with pytest.raises(CommandFailure) as caught:
        run_logged(
            [
                sys.executable,
                "-c",
                "import sys; print('permission denied docker.sock'); sys.exit(7)",
            ],
            root=tmp_path,
        )
    assert caught.value.returncode == 7
    assert "permission denied docker.sock" in str(caught.value)
    assert "rootless" in str(caught.value)
    assert caught.value.log_path.is_file()


def test_silent_command_is_bounded(tmp_path):
    with pytest.raises(CommandFailure) as caught:
        run_logged(
            [sys.executable, "-c", "import time; time.sleep(20)"],
            root=tmp_path,
            timeout=0.3,
        )
    assert caught.value.timed_out


def test_missing_command_is_actionable(tmp_path):
    with pytest.raises(CommandFailure) as caught:
        run_logged([str(tmp_path / "missing")], root=tmp_path)
    assert caught.value.returncode == 127
    assert caught.value.log_path.exists()


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_timeout_must_be_finite_and_positive(tmp_path, timeout):
    with pytest.raises(ValueError, match="positivo"):
        run_logged([sys.executable, "-c", "pass"], root=tmp_path, timeout=timeout)
