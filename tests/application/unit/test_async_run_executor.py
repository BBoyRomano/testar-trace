from __future__ import annotations

import time
from typing import NoReturn

from reqtrace.application.exceptions import RunCanceledError
from reqtrace.application.progress import RequirementProgress
from reqtrace.application.result_enums import RunStatus
from reqtrace.application.results import EvidenceSnapshot, RequirementSnapshot, TraceabilityRequest
from reqtrace.application.services.async_run_executor import AsyncRunExecutor
from reqtrace.application.services.traceability_service import (
    TraceabilityService,
    build_default_traceability_service,
)


def _minimal_request(*, method_name: str = "baseline") -> TraceabilityRequest:
    requirements = RequirementSnapshot.from_mapping(
        {
            "requirements": [{"id": "REQ-1", "kind": "use_case", "title": "Login"}],
            "fragments": [],
            "flows": [],
            "flow_edges": [],
        }
    )
    evidence = EvidenceSnapshot.from_mapping(
        {
            "states": [],
            "elements": [],
            "actions": [],
            "transitions": [],
            "runs": [],
            "observations": [],
            "attachments": [],
        }
    )
    return TraceabilityRequest(
        method_name=method_name,
        requirements=requirements,
        evidence=evidence,
    )


def test_async_run_executor_emits_running_and_completed_events() -> None:
    executor = AsyncRunExecutor(build_default_traceability_service())
    try:
        job_id = executor.submit(_minimal_request())
        saw_running = False
        saw_completed = False

        for _ in range(60):
            for event in executor.drain_events():
                if event.job_id != job_id:
                    continue
                if event.status == RunStatus.RUNNING:
                    saw_running = True
                if event.status == RunStatus.COMPLETED:
                    saw_completed = True
                    assert event.result is not None
            if saw_completed:
                break
            time.sleep(0.01)

        assert saw_running
        assert saw_completed
    finally:
        executor.shutdown()


def test_async_run_executor_has_in_flight_jobs_for_slow_run() -> None:
    class SlowMethod:
        name = "slow"

        def run(self, request: TraceabilityRequest):
            time.sleep(0.05)
            return build_default_traceability_service().execute(_minimal_request())

    service = TraceabilityService(methods={"slow": SlowMethod()})
    executor = AsyncRunExecutor(service)
    try:
        executor.submit(_minimal_request(method_name="slow"))
        observed_in_flight = False
        for _ in range(20):
            if executor.has_in_flight_jobs():
                observed_in_flight = True
                break
            time.sleep(0.005)
        assert observed_in_flight is True

        for _ in range(80):
            if not executor.has_in_flight_jobs():
                break
            time.sleep(0.01)
        assert executor.has_in_flight_jobs() is False
    finally:
        executor.shutdown()


def test_async_run_executor_emits_failed_event_for_method_error() -> None:
    class FailingMethod:
        name = "failing"

        def run(self, request: TraceabilityRequest) -> NoReturn:
            raise RuntimeError("boom")

    service = TraceabilityService(methods={"failing": FailingMethod()})
    executor = AsyncRunExecutor(service)
    try:
        job_id = executor.submit(_minimal_request(method_name="failing"))
        saw_failed = False
        for _ in range(60):
            for event in executor.drain_events():
                if event.job_id != job_id:
                    continue
                if event.status == RunStatus.FAILED:
                    saw_failed = True
                    assert "failed" in (event.error_message or "").lower()
            if saw_failed:
                break
            time.sleep(0.01)

        assert saw_failed
    finally:
        executor.shutdown()


def test_async_run_executor_can_cancel_queued_job() -> None:
    class SlowMethod:
        name = "slow"

        def run(self, request: TraceabilityRequest):
            time.sleep(0.15)
            return build_default_traceability_service().execute(_minimal_request())

    service = TraceabilityService(methods={"slow": SlowMethod()})
    executor = AsyncRunExecutor(service, max_workers=1)
    try:
        executor.submit(_minimal_request(method_name="slow"))
        queued_job_id = executor.submit(_minimal_request(method_name="slow"))

        assert executor.cancel(queued_job_id) is True

        saw_canceled_event = False
        for _ in range(80):
            for event in executor.drain_events():
                if event.job_id != queued_job_id:
                    continue
                if event.status == RunStatus.FAILED:
                    saw_canceled_event = True
                    assert "canceled by user" in (event.error_message or "").lower()
            if saw_canceled_event:
                break
            time.sleep(0.01)

        assert saw_canceled_event
    finally:
        executor.shutdown()


def test_async_run_executor_emits_requirement_progress_events() -> None:
    class ProgressMethod:
        name = "progress"

        def run(self, request: TraceabilityRequest, *, progress_callback=None):
            if progress_callback is not None:
                progress_callback(
                    RequirementProgress(
                        requirement_id="REQ-1",
                        requirement_title="Login",
                        state="processing",
                        processed_requirement_count=0,
                        total_requirement_count=1,
                        phase="progress",
                    )
                )
                progress_callback(
                    RequirementProgress(
                        requirement_id="REQ-1",
                        requirement_title="Login",
                        state="completed",
                        processed_requirement_count=1,
                        total_requirement_count=1,
                        phase="progress",
                    )
                )
            return build_default_traceability_service().execute(_minimal_request())

    service = TraceabilityService(methods={"progress": ProgressMethod()})
    executor = AsyncRunExecutor(service)
    try:
        job_id = executor.submit(_minimal_request(method_name="progress"))
        saw_processing = False
        saw_completed_progress = False
        saw_completed = False

        for _ in range(80):
            for event in executor.drain_events():
                if event.job_id != job_id:
                    continue
                if event.progress is not None and event.progress.state == "processing":
                    saw_processing = True
                if event.progress is not None and event.progress.state == "completed":
                    saw_completed_progress = True
                if event.status == RunStatus.COMPLETED:
                    saw_completed = True
            if saw_processing and saw_completed_progress and saw_completed:
                break
            time.sleep(0.01)

        assert saw_processing
        assert saw_completed_progress
        assert saw_completed
    finally:
        executor.shutdown()


def test_async_run_executor_can_cancel_running_job() -> None:
    class CancelableMethod:
        name = "cancelable"

        def run(self, request: TraceabilityRequest, *, is_canceled=None):
            for _ in range(80):
                if is_canceled is not None and is_canceled():
                    raise RunCanceledError("Canceled by user.")
                time.sleep(0.005)
            return build_default_traceability_service().execute(_minimal_request())

    service = TraceabilityService(methods={"cancelable": CancelableMethod()})
    executor = AsyncRunExecutor(service, max_workers=1)
    try:
        job_id = executor.submit(_minimal_request(method_name="cancelable"))
        time.sleep(0.03)
        assert executor.cancel(job_id) is True

        saw_canceled_event = False
        for _ in range(120):
            for event in executor.drain_events():
                if event.job_id != job_id:
                    continue
                if (
                    event.status == RunStatus.FAILED
                    and "canceled" in (event.error_message or "").lower()
                ):
                    saw_canceled_event = True
            if saw_canceled_event:
                break
            time.sleep(0.01)

        assert saw_canceled_event
    finally:
        executor.shutdown()


def test_async_run_executor_process_backend_completes_run() -> None:
    executor = AsyncRunExecutor(
        build_default_traceability_service(),
        execution_backend="process",
        max_workers=2,
    )
    try:
        job_id = executor.submit(_minimal_request())
        saw_running = False
        saw_completed = False

        for _ in range(200):
            for event in executor.drain_events():
                if event.job_id != job_id:
                    continue
                if event.status == RunStatus.RUNNING:
                    saw_running = True
                if event.status == RunStatus.COMPLETED:
                    saw_completed = True
                    assert event.result is not None
            if saw_completed:
                break
            time.sleep(0.01)

        assert saw_running
        assert saw_completed
    finally:
        executor.shutdown()
