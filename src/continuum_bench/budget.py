"""Shared benchmark deadlines and right-censoring helpers.

Timeouts are observations (the response exceeded an acceptance threshold),
not harness crashes.  This module keeps that distinction consistent across
the monolithic, container and physical coordinators.
"""

from __future__ import annotations

from contextlib import contextmanager
from http.client import RemoteDisconnected
import signal
from threading import current_thread, main_thread
from time import monotonic
from typing import Iterator
from urllib.error import HTTPError, URLError


class PhaseBudgetTimeout(TimeoutError):
    """Raised when a benchmark phase exceeds its configured wall budget."""


@contextmanager
def local_phase_timeout(seconds: float) -> Iterator[None]:
    """Interrupt a CPU-bound local phase on Unix without leaking SIGALRM."""

    if (
        seconds <= 0
        or not hasattr(signal, "setitimer")
        or current_thread() is not main_thread()
    ):
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)

    def alarm_handler(signum, frame):  # noqa: ARG001
        raise PhaseBudgetTimeout(
            f"local phase exceeded its {seconds:.1f}s budget"
        )

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def remaining_seconds(started: float, total_seconds: float) -> float:
    """Return a strictly positive remainder or raise a budget timeout."""

    remaining = total_seconds - (monotonic() - started)
    if remaining <= 0:
        raise PhaseBudgetTimeout(
            f"benchmark point exceeded its {total_seconds:.1f}s budget"
        )
    return remaining


def _error_chain(error: BaseException) -> Iterator[BaseException]:
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def is_boundary_failure(error: BaseException) -> bool:
    """Return whether a failure can represent overload at a process boundary."""

    boundary_types = (
        TimeoutError,
        ConnectionError,
        BrokenPipeError,
        ConnectionResetError,
        RemoteDisconnected,
        URLError,
    )
    for item in _error_chain(error):
        if isinstance(item, boundary_types):
            return True
        if isinstance(item, HTTPError) and item.code in {
            408,
            413,
            429,
            500,
            502,
            503,
            504,
        }:
            return True
        message = str(item).lower()
        if any(
            token in message
            for token in (
                "timed out",
                "timeout",
                "broken pipe",
                "connection reset",
                "remote end closed",
            )
        ):
            return True
    return False


def failure_status(error: BaseException) -> str:
    """Classify a bounded observation for CSV/report consumers."""

    for item in _error_chain(error):
        if isinstance(item, TimeoutError):
            return "timeout"
        if isinstance(item, HTTPError) and item.code in {408, 504}:
            return "timeout"
        message = str(item).lower()
        if "timed out" in message or "timeout" in message:
            return "timeout"
    return "transport_error" if is_boundary_failure(error) else "failed"


def error_text(error: BaseException, limit: int = 500) -> str:
    value = f"{type(error).__name__}: {error}".replace("\n", " ")
    return value if len(value) <= limit else value[: limit - 3] + "..."
