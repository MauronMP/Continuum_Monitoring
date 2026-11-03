from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from time import monotonic, sleep

from .config import MonitoringTask

Clock = Callable[[], float]
Sleeper = Callable[[float], None]
TaskExecutor = Callable[[MonitoringTask, float, float], dict]
WallClock = Callable[[], datetime]


def _deadline(task: MonitoringTask, global_timeout: float) -> float:
    policy_deadline = task.deadline_seconds if task.deadline_seconds is not None else task.interval_seconds
    return min(policy_deadline, global_timeout)


def _utc_at(start_utc: datetime, offset: float) -> str:
    return (start_utc + timedelta(seconds=offset)).isoformat()


def _missed_event(task, scheduled, start, start_utc, global_timeout, reason) -> dict:
    offset = scheduled - start
    return {
        **asdict(task),
        "effective_deadline_seconds": _deadline(task, global_timeout),
        "scheduled_at_monotonic": scheduled,
        "scheduled_offset_seconds": offset,
        "scheduled_at_utc": _utc_at(start_utc, offset),
        "actual_start_monotonic": None,
        "actual_start_offset_seconds": None,
        "actual_start_utc": None,
        "actual_end_monotonic": None,
        "actual_end_offset_seconds": None,
        "actual_end_utc": None,
        "schedule_lag_seconds": None,
        "execution_status": "not_executed",
        "schedule_status": "missed_schedule",
        "observation_outcome": "not_observed",
        "monitoring_compliant": False,
        "missed_cycle": True,
        "reason": reason,
    }


def run_scheduler(
    tasks: tuple[MonitoringTask, ...],
    measurement_seconds: float,
    global_timeout: float,
    execute: TaskExecutor,
    *,
    clock: Clock = monotonic,
    sleeper: Sleeper = sleep,
    wall_clock: WallClock = lambda: datetime.now(UTC),
) -> dict:
    start = clock()
    start_utc = wall_clock()
    end = start + measurement_seconds
    next_due = {task.task_id: start + task.interval_seconds for task in tasks}
    events: list[dict] = []
    busy_seconds = 0.0
    max_pending = 0
    scheduler_halted = False
    while tasks and clock() < end and not scheduler_halted:
        nearest = min(next_due.values())
        if nearest >= end:
            sleeper(max(0.0, end - clock()))
            break
        if clock() < nearest:
            sleeper(nearest - clock())
        now = clock()
        due: list[tuple[MonitoringTask, float]] = []
        for task in tasks:
            scheduled = next_due[task.task_id]
            if scheduled <= now and scheduled < end:
                if now - scheduled >= task.interval_seconds:
                    while scheduled <= now and scheduled < end:
                        events.append(
                            _missed_event(task, scheduled, start, start_utc, global_timeout, "scheduler_busy")
                        )
                        scheduled += task.interval_seconds
                else:
                    due.append((task, scheduled))
                    scheduled += task.interval_seconds
            next_due[task.task_id] = scheduled
        due.sort(key=lambda item: (-item[0].priority, _deadline(item[0], global_timeout), item[1], item[0].task_id))
        max_pending = max(max_pending, len(due))
        for task, scheduled in due:
            actual_start = clock()
            effective_deadline = _deadline(task, global_timeout)
            remaining_deadline = min(scheduled + effective_deadline - actual_start, end - actual_start)
            if remaining_deadline <= 0:
                events.append(
                    _missed_event(
                        task, scheduled, start, start_utc, global_timeout, "task_deadline_elapsed_before_start"
                    )
                )
                continue
            outcome = execute(task, scheduled, remaining_deadline)
            actual_end = clock()
            busy_seconds += max(0.0, actual_end - actual_start)
            execution_status = str(outcome.get("execution_status", "physical_failure"))
            schedule_status = "completed_on_time" if actual_end <= scheduled + effective_deadline else "completed_late"
            compliant = execution_status == "completed" and schedule_status == "completed_on_time"
            scheduled_offset = scheduled - start
            start_offset = actual_start - start
            end_offset = actual_end - start
            events.append(
                {
                    **asdict(task),
                    "effective_deadline_seconds": effective_deadline,
                    "scheduled_at_monotonic": scheduled,
                    "scheduled_offset_seconds": scheduled_offset,
                    "scheduled_at_utc": _utc_at(start_utc, scheduled_offset),
                    "actual_start_monotonic": actual_start,
                    "actual_start_offset_seconds": start_offset,
                    "actual_start_utc": _utc_at(start_utc, start_offset),
                    "actual_end_monotonic": actual_end,
                    "actual_end_offset_seconds": end_offset,
                    "actual_end_utc": _utc_at(start_utc, end_offset),
                    "schedule_lag_seconds": max(0.0, actual_start - scheduled),
                    "execution_status": execution_status,
                    "schedule_status": schedule_status,
                    "observation_outcome": outcome.get("observation_outcome", "not_observed"),
                    "monitoring_compliant": compliant,
                    "missed_cycle": False,
                    **{
                        key: value
                        for key, value in outcome.items()
                        if key not in {"execution_status", "observation_outcome"}
                    },
                }
            )
            if outcome.get("recovery_succeeded") is False:
                scheduler_halted = True
                break
    for task in tasks:
        scheduled = next_due[task.task_id]
        while scheduled < end:
            reason = "timeout_recovery_failed" if scheduler_halted else "measurement_window_closed_while_scheduler_busy"
            events.append(_missed_event(task, scheduled, start, start_utc, global_timeout, reason))
            scheduled += task.interval_seconds
    measurement_actual_seconds = max(0.0, clock() - start)
    scheduled_count = len(events)
    compliant_count = sum(bool(event["monitoring_compliant"]) for event in events)
    recovery_failure = next((event for event in events if event.get("recovery_succeeded") is False), None)
    return {
        "events": events,
        "scheduled_cycles": scheduled_count,
        "completed_on_time": sum(event["schedule_status"] == "completed_on_time" for event in events),
        "completed_late": sum(event["schedule_status"] == "completed_late" for event in events),
        "missed_cycles": sum(event["schedule_status"] == "missed_schedule" for event in events),
        "logical_timeouts": sum(event["execution_status"] == "logical_timeout" for event in events),
        "semantic_failures": sum(event["execution_status"] == "semantic_failure" for event in events),
        "physical_failures": sum(event["execution_status"] == "physical_failure" for event in events),
        "recovery_count": sum(int(event.get("recovery_count", 0)) for event in events),
        "recovery_seconds": sum(float(event.get("recovery_seconds", 0.0)) for event in events),
        "worker_restart_count": sum(int(event.get("worker_restart_count", 0)) for event in events),
        "monitoring_compliant_cycles": compliant_count,
        "monitoring_compliance": compliant_count / scheduled_count if scheduled_count else 1.0,
        "scheduler_busy_seconds": busy_seconds,
        "scheduler_idle_seconds": max(0.0, measurement_actual_seconds - busy_seconds),
        "scheduler_utilization": busy_seconds / measurement_actual_seconds if measurement_actual_seconds else 0.0,
        "max_pending_monitoring_tasks": max_pending,
        "scheduler_halted": scheduler_halted,
        "measurement_requested_seconds": measurement_seconds,
        "measurement_actual_seconds": measurement_actual_seconds,
        "failure_reason": recovery_failure.get("failure_reason") if recovery_failure else None,
        "failed_task": recovery_failure.get("failed_task") if recovery_failure else None,
        "failed_query": recovery_failure.get("failed_query") if recovery_failure else None,
        "failed_hosts": recovery_failure.get("failed_hosts") if recovery_failure else None,
        "measurement_started_at_utc": start_utc.isoformat(),
    }
