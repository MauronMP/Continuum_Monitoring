"""Shared benchmark deadlines and right-censoring helpers.

Timeouts are observations (the response exceeded an acceptance threshold),
not harness crashes.  This module keeps that distinction consistent across
the physical coordinator and workers.
"""

from __future__ import annotations

from contextlib import contextmanager
from http.client import RemoteDisconnected
import signal
from threading import current_thread, main_thread
from time import monotonic
from typing import Iterator
from urllib.error import HTTPError, URLError


_UNLIMITED = False


def unlimited_execution() -> bool:
    """Process execution policy, shared by coordinator worker threads."""
    return _UNLIMITED


@contextmanager
def execution_policy(unlimited: bool = False) -> Iterator[None]:
    """Scope the CLI policy without changing configured acceptance budgets."""
    global _UNLIMITED
    previous = _UNLIMITED
    _UNLIMITED = unlimited
    try:
        yield
    finally:
        _UNLIMITED = previous


def execution_metadata() -> dict:
    return {"timeout_mode": "unlimited" if _UNLIMITED else "bounded",
            "configured_budgets_enforced": not _UNLIMITED}


def wait_timeout(seconds: float) -> float | None:
    """Use the blocking API's unbounded sentinel, never floating infinity."""
    return None if _UNLIMITED else seconds


class PhaseBudgetTimeout(TimeoutError):
    """Raised when a benchmark phase exceeds its configured wall budget."""


@contextmanager
def local_phase_timeout(seconds: float) -> Iterator[None]:
    """Interrupt a CPU-bound local phase on Unix without leaking SIGALRM."""

    if (
        unlimited_execution()
        or seconds <= 0
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

    if unlimited_execution():
        return float("inf")
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


def is_timeout_failure(error: BaseException) -> bool:
    """Accept typed deadline failures, never error-message guesses.

    Explicit causes may wrap a transport timeout. Implicit exception context
    does not turn a programming error raised during cleanup into a timeout.
    """
    seen: set[int] = set()
    while id(error) not in seen:
        seen.add(id(error))
        if isinstance(error, HTTPError):
            return error.code in {408, 504}
        if isinstance(error, TimeoutError):
            return True
        if isinstance(error, URLError) and isinstance(error.reason, BaseException):
            error = error.reason
        elif error.__cause__ is not None:
            error = error.__cause__
        else:
            return False
    return False


class TimeoutSkipState:
    """Per-run timeout streaks and independent, latched skip scopes.

    A completed point resets its reasoner's streak. Skipped points and shared
    setup successes do not count as observations. Once triggered, a skip stays
    latched for its scope, even if independent work subsequently succeeds.
    """

    def __init__(self, limits):
        self.limits = limits
        self.streaks: dict[str, int] = {}
        self.repetitions: dict[tuple[str, int], tuple[int, str]] = {}
        self.sizes: dict[str, tuple[int, str]] = {}
        self.stages: dict[tuple[str, int, int], tuple[int, str]] = {}

    def enabled(self, name: str) -> bool:
        value = getattr(self.limits, name)
        return not unlimited_execution() and (
            self.limits.stop_scaling_after_timeout if value is None else value
        )

    def skipped(self, reasoner: str, users: int, repetition: int, stage: int) -> str | None:
        if unlimited_execution():
            return None
        for previous, current in (
            (self.sizes.get(reasoner), users),
            (self.repetitions.get((reasoner, users)), repetition),
            (self.stages.get((reasoner, users, repetition)), stage),
        ):
            if previous is not None and current > previous[0]:
                return previous[1]
        return None

    def completed(self, reasoner: str) -> None:
        self.streaks[reasoner] = 0

    def timeout(self, reasoner: str, users: int, repetition: int, stage: int, error: BaseException) -> None:
        if not is_timeout_failure(error):
            raise error
        self.streaks[reasoner] = self.streaks.get(reasoner, 0) + 1
        if self.streaks[reasoner] < self.limits.consecutive_timeout_threshold:
            return
        reason = error_text(error)
        if self.enabled("skip_repetitions_after_timeout"):
            self.repetitions.setdefault((reasoner, users), (repetition, reason))
        if self.enabled("skip_larger_sizes_after_timeout"):
            self.sizes.setdefault(reasoner, (users, reason))
        if self.enabled("skip_cumulative_stages_after_timeout"):
            self.stages.setdefault((reasoner, users, repetition), (stage, reason))


def skip_metadata(limits) -> dict:
    state = TimeoutSkipState(limits)
    return {
        name: state.enabled(name)
        for name in (
            "skip_repetitions_after_timeout",
            "skip_larger_sizes_after_timeout",
            "skip_cumulative_stages_after_timeout",
        )
    } | {"consecutive_timeout_threshold": limits.consecutive_timeout_threshold}
