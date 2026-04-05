"""Asynchronous traceability run execution service."""

from __future__ import annotations

import logging
import multiprocessing as mp
from concurrent.futures import Future, ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from multiprocessing.managers import SyncManager
from queue import Empty, Queue
from threading import Event, Lock
from typing import Literal, Protocol
from uuid import uuid4

from reqtrace.application.exceptions import RunCanceledError
from reqtrace.application.progress import RequirementProgress
from reqtrace.application.result_enums import RunStatus
from reqtrace.application.results import TraceabilityRequest, TraceabilityResult
from reqtrace.application.services.traceability_service import (
    TraceabilityService,
    build_default_traceability_service,
)

logger = logging.getLogger(__name__)

ExecutionBackend = Literal["thread", "process"]
ProcessResult = tuple[str, TraceabilityResult | None, str | None]


class _Cancelable(Protocol):
    def set(self) -> None: ...

    def is_set(self) -> bool: ...


class _ProgressQueue(Protocol):
    def put(self, value: RequirementProgress) -> None: ...

    def get_nowait(self) -> RequirementProgress: ...


@dataclass(slots=True)
class AsyncRunEvent:
    job_id: str
    status: RunStatus
    result: TraceabilityResult | None = None
    error_message: str | None = None
    progress: RequirementProgress | None = None


def _execute_job_in_process(
    request: TraceabilityRequest,
    *,
    include_experimental_methods: bool,
    cancel_flag: _Cancelable,
    progress_queue: _ProgressQueue,
) -> ProcessResult:
    """Worker entrypoint for process backend execution."""

    service = build_default_traceability_service(
        include_experimental_methods=include_experimental_methods
    )
    try:
        result = service.execute(
            request,
            progress_callback=progress_queue.put,
            is_canceled=cancel_flag.is_set,
        )
    except RunCanceledError as exc:
        return ("failed", None, str(exc) or "Canceled by user.")
    except Exception as exc:  # pragma: no cover - defensive boundary
        return ("failed", None, str(exc))
    return ("completed", result, None)


class AsyncRunExecutor:
    """Executes traceability requests off the UI thread and emits events."""

    _MAX_EVENT_BATCH = 512
    _MAX_PROCESS_PROGRESS_PER_JOB_DRAIN = 256

    def __init__(
        self,
        service: TraceabilityService,
        *,
        max_workers: int = 4,
        execution_backend: ExecutionBackend = "thread",
    ) -> None:
        self._service = service
        self._execution_backend: ExecutionBackend = execution_backend
        self._events: Queue[AsyncRunEvent] = Queue()
        self._in_flight: set[str] = set()
        self._futures: dict[str, Future[None] | Future[ProcessResult]] = {}
        self._cancel_flags: dict[str, _Cancelable] = {}
        self._process_progress_queues: dict[str, _ProgressQueue] = {}
        self._lock = Lock()
        self._include_experimental_methods = len(service.available_methods()) > 1

        if execution_backend == "process":
            self._mp_context = mp.get_context("spawn")
            self._manager: SyncManager | None = self._mp_context.Manager()
            self._executor: ThreadPoolExecutor | ProcessPoolExecutor = ProcessPoolExecutor(
                max_workers=max_workers,
                mp_context=self._mp_context,
            )
        else:
            self._mp_context = None
            self._manager = None
            self._executor = ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix="reqtrace-run",
            )

        logger.info(
            "Async run executor initialized.",
            extra={"max_workers": max_workers, "execution_backend": execution_backend},
        )

    def submit(self, request: TraceabilityRequest) -> str:
        job_id = f"job-{uuid4().hex}"

        if self._execution_backend == "process":
            assert self._manager is not None
            cancel_flag = self._manager.Event()
            progress_queue = self._manager.Queue()
            with self._lock:
                self._in_flight.add(job_id)
                self._cancel_flags[job_id] = cancel_flag
                self._process_progress_queues[job_id] = progress_queue
            future = self._executor.submit(
                _execute_job_in_process,
                request,
                include_experimental_methods=self._include_experimental_methods,
                cancel_flag=cancel_flag,
                progress_queue=progress_queue,
            )
            with self._lock:
                self._futures[job_id] = future
            future.add_done_callback(
                lambda completed_future, tracked_job_id=job_id: self._on_process_job_done(
                    tracked_job_id,
                    completed_future,
                )
            )
        else:
            cancel_flag = Event()
            with self._lock:
                self._in_flight.add(job_id)
                self._cancel_flags[job_id] = cancel_flag
            future = self._executor.submit(self._execute_job, job_id, request)
            with self._lock:
                self._futures[job_id] = future

        self._events.put(AsyncRunEvent(job_id=job_id, status=RunStatus.RUNNING))
        logger.info(
            "Async run submitted.",
            extra={
                "job_id": job_id,
                "method_name": request.method_name,
                "execution_backend": self._execution_backend,
            },
        )
        return job_id

    def cancel(self, job_id: str) -> bool:
        """Cancel a queued or running job.

        Returns True if cancellation was requested/accepted, False if unknown.
        """

        with self._lock:
            future = self._futures.get(job_id)
            if future is None:
                return False

            canceled = future.cancel()
            if canceled:
                self._in_flight.discard(job_id)
                self._futures.pop(job_id, None)
                self._cancel_flags.pop(job_id, None)
                progress_queue = self._process_progress_queues.pop(job_id, None)
                self._close_progress_queue(progress_queue)
            else:
                cancel_flag = self._cancel_flags.get(job_id)
                if cancel_flag is None:
                    return False
                cancel_flag.set()
                logger.info("Async run cancellation requested.", extra={"job_id": job_id})
                return True

        if not canceled:
            return False

        self._events.put(
            AsyncRunEvent(
                job_id=job_id,
                status=RunStatus.FAILED,
                error_message="Canceled by user before execution started.",
            )
        )
        logger.info("Async queued run canceled.", extra={"job_id": job_id})
        return True

    def drain_events(self) -> list[AsyncRunEvent]:
        if self._execution_backend == "process":
            self._drain_process_progress()

        events: list[AsyncRunEvent] = []
        while len(events) < self._MAX_EVENT_BATCH:
            try:
                events.append(self._events.get_nowait())
            except Empty:
                break
        if events:
            logger.debug(
                "Drained async run events.",
                extra={"event_count": len(events), "max_batch": self._MAX_EVENT_BATCH},
            )
        return events

    def has_in_flight_jobs(self) -> bool:
        with self._lock:
            return bool(self._in_flight)

    def shutdown(self, *, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=True)
        if wait and self._manager is not None:
            self._manager.shutdown()
        logger.info(
            "Async run executor shutdown requested.",
            extra={"wait": wait, "execution_backend": self._execution_backend},
        )

    def _execute_job(self, job_id: str, request: TraceabilityRequest) -> None:
        logger.debug(
            "Executing async run job.",
            extra={"job_id": job_id, "method_name": request.method_name},
        )
        try:
            with self._lock:
                cancel_flag = self._cancel_flags.get(job_id)
            result = self._service.execute(
                request,
                progress_callback=lambda event: self._events.put(
                    AsyncRunEvent(
                        job_id=job_id,
                        status=RunStatus.RUNNING,
                        progress=event,
                    )
                ),
                is_canceled=cancel_flag.is_set if cancel_flag is not None else None,
            )
        except RunCanceledError as exc:
            logger.info(
                "Async run job canceled.",
                extra={"job_id": job_id, "method_name": request.method_name},
            )
            self._events.put(
                AsyncRunEvent(
                    job_id=job_id,
                    status=RunStatus.FAILED,
                    error_message=str(exc) or "Canceled by user.",
                )
            )
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
                self._futures.pop(job_id, None)
                self._cancel_flags.pop(job_id, None)
            logger.debug("Async run job removed from in-flight set.", extra={"job_id": job_id})

    def _on_process_job_done(
        self,
        job_id: str,
        future: Future[ProcessResult],
    ) -> None:
        with self._lock:
            tracked_future = self._futures.get(job_id)
            progress_queue = self._process_progress_queues.get(job_id)

        # Ignore callback for stale/canceled futures.
        if tracked_future is not future:
            self._close_progress_queue(progress_queue)
            return

        self._drain_single_process_progress(job_id, progress_queue)

        try:
            status_token, result, error_message = future.result()
        except Exception as exc:  # pragma: no cover - defensive boundary
            status = RunStatus.FAILED
            result = None
            error_message = str(exc)
        else:
            status = RunStatus.COMPLETED if status_token == "completed" else RunStatus.FAILED

        with self._lock:
            self._in_flight.discard(job_id)
            self._futures.pop(job_id, None)
            self._cancel_flags.pop(job_id, None)
            queue_to_close = self._process_progress_queues.pop(job_id, None)
        self._close_progress_queue(queue_to_close)

        self._events.put(
            AsyncRunEvent(
                job_id=job_id,
                status=status,
                result=result,
                error_message=error_message,
            )
        )

    def _drain_process_progress(self) -> None:
        with self._lock:
            tracked = list(self._process_progress_queues.items())
        for job_id, progress_queue in tracked:
            self._drain_single_process_progress(job_id, progress_queue)

    def _drain_single_process_progress(
        self,
        job_id: str,
        progress_queue: _ProgressQueue | None,
    ) -> None:
        if progress_queue is None:
            return
        drained = 0
        while drained < self._MAX_PROCESS_PROGRESS_PER_JOB_DRAIN:
            try:
                progress = progress_queue.get_nowait()
            except Empty:
                return
            drained += 1
            self._events.put(
                AsyncRunEvent(
                    job_id=job_id,
                    status=RunStatus.RUNNING,
                    progress=progress,
                )
            )

    @staticmethod
    def _close_progress_queue(progress_queue: _ProgressQueue | None) -> None:
        if progress_queue is None:
            return
        close = getattr(progress_queue, "close", None)
        if callable(close):
            close()
        cancel_join_thread = getattr(progress_queue, "cancel_join_thread", None)
        if callable(cancel_join_thread):
            cancel_join_thread()
