"""Background preparation pipeline for desktop-triggered runs."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from queue import Queue
from threading import Event
from typing import Literal

from reqtrace.application.requests.preparation import prepare_traceability_request
from reqtrace.application.execution.async_executor import AsyncRunExecutor
from reqtrace import TraceRequest
from reqtrace.errors import InputError

logger = logging.getLogger(__name__)
PREPARATION_CANCELED_MESSAGE = "Canceled by user before execution started."
PreparationEventKind = Literal["prepared", "submitted", "failed"]


@dataclass(slots=True, frozen=True)
class PreparationEvent:
    entry_id: str
    kind: PreparationEventKind
    job_id: str | None = None
    requirements: list[tuple[str, str]] | None = None
    phase: str | None = None
    message: str | None = None


def _emit_failed(
    *,
    entry_id: str,
    events_queue: Queue[PreparationEvent],
    message: str,
) -> None:
    events_queue.put(
        PreparationEvent(entry_id=entry_id, kind="failed", message=message)
    )


def prepare_and_submit_run(
    entry_id: str,
    trace_request: TraceRequest,
    cancel_flag: Event,
    *,
    executor: AsyncRunExecutor,
    events_queue: Queue[PreparationEvent],
) -> None:
    if cancel_flag.is_set():
        _emit_failed(
            entry_id=entry_id,
            events_queue=events_queue,
            message=PREPARATION_CANCELED_MESSAGE,
        )
        return

    try:
        request = prepare_traceability_request(trace_request)
    except InputError as exc:
        _emit_failed(entry_id=entry_id, events_queue=events_queue, message=str(exc))
        return
    except Exception as exc:  # pragma: no cover - defensive boundary
        logger.error("Desktop run request build failed.", exc_info=exc)
        _emit_failed(
            entry_id=entry_id,
            events_queue=events_queue,
            message=f"Could not prepare run: {exc}",
        )
        return

    if cancel_flag.is_set():
        _emit_failed(
            entry_id=entry_id,
            events_queue=events_queue,
            message=PREPARATION_CANCELED_MESSAGE,
        )
        return

    requirements = [
        (requirement.id, requirement.title)
        for requirement in request.requirements.requirements
    ]
    events_queue.put(
        PreparationEvent(
            entry_id=entry_id,
            kind="prepared",
            requirements=requirements,
            phase=request.method_name,
        )
    )

    try:
        job_id = executor.submit(request)
    except Exception as exc:  # pragma: no cover - defensive boundary
        logger.error("Desktop async submission failed.", exc_info=exc)
        _emit_failed(
            entry_id=entry_id,
            events_queue=events_queue,
            message=f"Could not submit run: {exc}",
        )
        return

    events_queue.put(
        PreparationEvent(entry_id=entry_id, kind="submitted", job_id=job_id)
    )


__all__ = (
    "PREPARATION_CANCELED_MESSAGE",
    "PreparationEvent",
    "PreparationEventKind",
    "prepare_and_submit_run",
)

