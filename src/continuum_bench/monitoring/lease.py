"""Prevent overlapping physical campaigns and lifecycle mutations on one coordinator."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import signal
from threading import current_thread, main_thread


@contextmanager
def prevent_coordinator_suspension(enabled: bool):
    """Keep an interactive Ctrl-Z from orphaning active worker requests."""

    supported = (
        enabled
        and hasattr(signal, "SIGTSTP")
        and current_thread() is main_thread()
    )
    if not supported:
        yield
        return
    previous = signal.getsignal(signal.SIGTSTP)

    def warn_and_continue(signum, frame):  # noqa: ARG001
        print(
            "[execution-policy] suspend ignored while a physical campaign is "
            "active; use Ctrl+C for a controlled interruption",
            flush=True,
        )

    signal.signal(signal.SIGTSTP, warn_and_continue)
    try:
        yield
    finally:
        signal.signal(signal.SIGTSTP, previous)

@contextmanager
def physical_lease(root: Path):
    directory = root/'outputs/runtime/physical'
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/'coordinator.lock').open('a+') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError('Another physical campaign or lifecycle operation is active on this coordinator') from error
        handle.seek(0)
        handle.truncate()
        handle.write(str(os.getpid()))
        handle.flush()
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
