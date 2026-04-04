from __future__ import annotations

import time
from typing import NoReturn

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
