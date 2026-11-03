from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from time import monotonic, sleep

from .config import MonitoringTask

Clock = Callable[[], float]
Sleeper = Callable[[float], None]
TaskExecutor = Callable[[MonitoringTask, float, float], dict]


def _deadline(task: MonitoringTask, global_timeout: float) -> float:
    policy_deadline = task.deadline_seconds if task.deadline_seconds is not None else task.interval_seconds
    return min(policy_deadline, global_timeout)


def run_scheduler(
    tasks: tuple[MonitoringTask, ...],
    measurement_seconds: float,
    global_timeout: float,
    execute: TaskExecutor,
    *,
    clock: Clock = monotonic,
    sleeper: Sleeper = sleep,
) -> dict:
    start = clock()
    end = start + measurement_seconds
    next_due = {task.task_id: start + task.interval_seconds for task in tasks}
    events: list[dict] = []
    busy_seconds = 0.0
    max_pending = 0
    while tasks and clock() < end:
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
                            {
                                **asdict(task),
                                "effective_deadline_seconds": _deadline(task, global_timeout),
                                "scheduled_at": scheduled,
                                "scheduled_at_monotonic": scheduled,
                                "actual_start": None,
                                "actual_end": None,
                                "schedule_lag": None,
                                "status": "missed_schedule",
                                "missed_cycle": True,
                                "reason": "scheduler_busy",
                            }
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
                    {
                        **asdict(task),
                        "effective_deadline_seconds": effective_deadline,
                        "scheduled_at": scheduled,
                        "scheduled_at_monotonic": scheduled,
                        "actual_start": None,
                        "actual_end": None,
                        "schedule_lag": None,
                        "status": "missed_schedule",
                        "missed_cycle": True,
                        "reason": "task_deadline_elapsed_before_start",
                    }
                )
                continue
            outcome = execute(task, scheduled, remaining_deadline)
            actual_end = clock()
            busy_seconds += max(0.0, min(actual_end, end) - actual_start)
            status = str(outcome.get("status", "physical_failure"))
            if status == "completed" and actual_end <= scheduled + effective_deadline:
                status = "completed_on_time"
            elif status == "completed":
                status = "completed_late"
            events.append(
                {
                    **asdict(task),
                    "effective_deadline_seconds": effective_deadline,
                    "scheduled_at": scheduled,
                    "scheduled_at_monotonic": scheduled,
                    "actual_start": actual_start,
                    "actual_start_monotonic": actual_start,
                    "actual_end": actual_end,
                    "actual_end_monotonic": actual_end,
                    "schedule_lag": max(0.0, actual_start - scheduled),
                    "schedule_lag_seconds": max(0.0, actual_start - scheduled),
                    "status": status,
                    "missed_cycle": False,
                    **{key: value for key, value in outcome.items() if key != "status"},
                }
            )
    for task in tasks:
        scheduled = next_due[task.task_id]
        while scheduled < end:
            events.append(
                {
                    **asdict(task),
                    "effective_deadline_seconds": _deadline(task, global_timeout),
                    "scheduled_at": scheduled,
                    "scheduled_at_monotonic": scheduled,
                    "actual_start": None,
                    "actual_end": None,
                    "schedule_lag": None,
                    "status": "missed_schedule",
                    "missed_cycle": True,
                    "reason": "measurement_window_closed_while_scheduler_busy",
                }
            )
            scheduled += task.interval_seconds
    scheduled = len(events)
    compliant = sum(event["status"] == "completed_on_time" for event in events)
    return {
        "events": events,
        "scheduled_cycles": scheduled,
        "completed_on_time": compliant,
        "completed_late": sum(event["status"] == "completed_late" for event in events),
        "missed_cycles": sum(event["status"] == "missed_schedule" for event in events),
        "logical_timeouts": sum(event["status"] == "logical_timeout" for event in events),
        "semantic_failures": sum(event["status"] == "semantic_failure" for event in events),
        "physical_failures": sum(event["status"] == "physical_failure" for event in events),
        "monitoring_compliance": compliant / scheduled if scheduled else 1.0,
        "scheduler_busy_seconds": busy_seconds,
        "scheduler_idle_seconds": max(0.0, measurement_seconds - busy_seconds),
        "scheduler_utilization": busy_seconds / measurement_seconds,
        "max_pending_monitoring_tasks": max_pending,
    }
