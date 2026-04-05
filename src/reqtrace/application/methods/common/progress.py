"""Shared helpers for emitting progress updates and honoring cancellation."""

from __future__ import annotations

from reqtrace.application.exceptions import RunCanceledError
from reqtrace.application.progress import (
    CancellationCallback,
    ProgressCallback,
    RequirementProgress,
    RequirementProgressState,
)


def emit_requirement_progress(
    *,
    progress_callback: ProgressCallback | None,
    requirement_id: str,
    requirement_title: str,
    state: RequirementProgressState,
    processed_requirement_count: int,
    total_requirement_count: int,
    phase: str | None = None,
    message: str | None = None,
) -> None:
    if progress_callback is None:
        return
    progress_callback(
        RequirementProgress(
            requirement_id=requirement_id,
            requirement_title=requirement_title,
            state=state,
            processed_requirement_count=processed_requirement_count,
            total_requirement_count=total_requirement_count,
            phase=phase,
            message=message,
        )
    )


def raise_if_canceled(
    *,
    is_canceled: CancellationCallback | None,
    message: str = "Canceled by user.",
) -> None:
    if is_canceled is None:
        return
    if is_canceled():
        raise RunCanceledError(message)
