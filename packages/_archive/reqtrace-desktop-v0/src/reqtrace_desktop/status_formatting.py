"""Pure formatting helpers used by the Desktop controller."""

from __future__ import annotations

from datetime import UTC, datetime

from reqtrace.application.history.models import RunHistoryEntry
from reqtrace.application.results.enums import RunStatus
from reqtrace.application.results.models import TraceabilityResult


def status_display(
    entry: RunHistoryEntry,
    *,
    animated: bool,
    spinner_frame: str,
    is_cancel_requested: bool,
    is_preparing: bool,
) -> str:
    if entry.status == RunStatus.RUNNING:
        if is_cancel_requested:
            return f"[{spinner_frame}] canceling"
        if is_preparing:
            if animated:
                return f"[{spinner_frame}] preparing"
            return "[~] preparing"
        if animated:
            return f"[{spinner_frame}] analyzing"
        return "[~] running"
    if entry.status == RunStatus.COMPLETED:
        return "[OK] completed"
    if entry.status == RunStatus.COMPLETED_WITH_ERRORS:
        return "[!] completed-with-errors"
    if entry.status == RunStatus.PENDING:
        return "[ ] pending"
    if entry.error_message and "canceled by user" in entry.error_message.lower():
        return "[X] canceled"
    return "[X] failed"


def requirement_status_display(status_value: str) -> str:
    return "[OK] done" if status_value == "done" else "[X] failed"


def live_requirement_status_display(status_value: str, *, spinner_frame: str) -> str:
    if status_value == "completed":
        return "[OK] done"
    if status_value == "failed":
        return "[X] failed"
    if status_value == "processing":
        return f"[{spinner_frame}] analyzing"
    return "[ ] waiting"


def timestamp_display(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")


def duration_display(result: TraceabilityResult) -> str:
    if result.run.ended_at is None:
        return "n/a"
    elapsed = result.run.ended_at - result.run.started_at
    return f"{elapsed.total_seconds():.2f}s"


def run_row_tag(entry: RunHistoryEntry) -> str:
    if entry.status == RunStatus.RUNNING:
        return "run_running"
    if entry.status == RunStatus.COMPLETED:
        return "run_completed"
    if entry.status == RunStatus.COMPLETED_WITH_ERRORS:
        return "run_warning"
    if entry.error_message and "canceled by user" in entry.error_message.lower():
        return "run_canceled"
    return "run_failed"


def live_requirement_row_tag(status_value: str) -> str:
    if status_value == "completed":
        return "req_completed"
    if status_value == "failed":
        return "req_failed"
    if status_value == "processing":
        return "req_processing"
    return "req_waiting"


def final_requirement_row_tag(status_value: str) -> str:
    return "req_completed" if status_value == "done" else "req_failed"

