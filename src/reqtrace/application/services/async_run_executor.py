"""Asynchronous traceability run execution service."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from queue import Empty, Queue
from threading import Lock
from uuid import uuid4

from reqtrace.application.result_enums import RunStatus
from reqtrace.application.results import TraceabilityRequest, TraceabilityResult
from reqtrace.application.services.traceability_service import TraceabilityService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AsyncRunEvent:
    job_id: str
    status: RunStatus
    result: TraceabilityResult | None = None
    error_message: str | None = None


class AsyncRunExecutor:
    """Executes traceability requests on background threads and emits events."""

    def __init__(self, service: TraceabilityService, *, max_workers: int = 4) -> None:
        self._service = service
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="reqtrace-run",
        )
        self._events: Queue[AsyncRunEvent] = Queue()
        self._in_flight: set[str] = set()
        self._lock = Lock()
        logger.info(
            "Async run executor initialized.",
            extra={"max_workers": max_workers},
        )

    def submit(self, request: TraceabilityRequest) -> str:
        job_id = f"job-{uuid4().hex}"
        with self._lock:
            self._in_flight.add(job_id)
        self._events.put(AsyncRunEvent(job_id=job_id, status=RunStatus.RUNNING))
        self._executor.submit(self._execute_job, job_id, request)
        logger.info(
            "Async run submitted.",
            extra={"job_id": job_id, "method_name": request.method_name},
        )
        return job_id

    def drain_events(self) -> list[AsyncRunEvent]:
        events: list[AsyncRunEvent] = []
        while True:
            try:
                events.append(self._events.get_nowait())
            except Empty:
                if events:
                    logger.debug(
                        "Drained async run events.",
                        extra={"event_count": len(events)},
                    )
                return events

    def has_in_flight_jobs(self) -> bool:
        with self._lock:
            return bool(self._in_flight)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False)
        logger.info("Async run executor shutdown requested.")

    def _execute_job(self, job_id: str, request: TraceabilityRequest) -> None:
        logger.debug(
            "Executing async run job.",
            extra={"job_id": job_id, "method_name": request.method_name},
        )
        try:
            result = self._service.execute(request)
        except Exception as exc:  # pragma: no cover - defensive boundary
            logger.error(
                "Async run job failed.",
                exc_info=exc,
                extra={"job_id": job_id, "method_name": request.method_name},
            )
            self._events.put(
                AsyncRunEvent(
                    job_id=job_id,
                    status=RunStatus.FAILED,
                    error_message=str(exc),
                )
            )
        else:
            logger.info(
                "Async run job completed.",
                extra={
                    "job_id": job_id,
                    "run_id": result.run.id,
                    "method_name": result.run.method_name,
                },
            )
            self._events.put(
                AsyncRunEvent(
                    job_id=job_id,
                    status=RunStatus.COMPLETED,
                    result=result,
                )
            )
        finally:
            with self._lock:
                self._in_flight.discard(job_id)
            logger.debug("Async run job removed from in-flight set.", extra={"job_id": job_id})
