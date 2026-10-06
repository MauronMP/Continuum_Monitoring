import signal

from continuum_bench.monitoring.lease import prevent_coordinator_suspension


def test_physical_campaign_ignores_terminal_suspend(monkeypatch, capsys):
    installed = []
    previous = object()
    monkeypatch.setattr(signal, "getsignal", lambda signum: previous)
    monkeypatch.setattr(
        signal,
        "signal",
        lambda signum, handler: installed.append((signum, handler)),
    )

    with prevent_coordinator_suspension(True):
        signum, handler = installed[-1]
        assert signum == signal.SIGTSTP
        handler(signum, None)

    assert installed[-1] == (signal.SIGTSTP, previous)
    assert "suspend ignored" in capsys.readouterr().out


def test_nonphysical_work_does_not_change_signal_handlers(monkeypatch):
    monkeypatch.setattr(
        signal,
        "signal",
        lambda *args: (_ for _ in ()).throw(AssertionError(args)),
    )

    with prevent_coordinator_suspension(False):
        pass
