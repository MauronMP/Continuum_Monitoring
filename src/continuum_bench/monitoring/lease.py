"""Prevent overlapping physical campaigns and lifecycle mutations on one coordinator."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path

@contextmanager
def physical_lease(root: Path):
    directory = root/'outputs/physical/runtime'
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
