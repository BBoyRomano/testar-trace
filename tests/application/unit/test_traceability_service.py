from __future__ import annotations

from typing import NoReturn

import pytest

from reqtrace.application.exceptions import (
    RunCanceledError,
    TraceabilityMethodExecutionError,
    UnknownTraceabilityMethodError,
)
from reqtrace.application.results import TraceabilityRequest
from reqtrace.application.services.traceability_service import (
    TraceabilityService,
    build_default_traceability_service,
)


def test_service_exposes_all_default_methods() -> None:
    service = build_default_traceability_service()
    assert service.available_methods() == [
        "baseline",
        "candidate_match",
        "conformance_match",
        "flow_match",
        "hybrid_match",
    ]


def test_service_can_opt_in_to_experimental_methods() -> None:
    service = build_default_traceability_service(include_experimental_methods=True)
    assert service.available_methods() == [
        "baseline",
        "candidate_match",
        "conformance_match",
        "flow_match",
        "hybrid_match",
    ]


def test_service_can_limit_to_baseline_only() -> None:
    service = build_default_traceability_service(include_experimental_methods=False)
    assert service.available_methods() == ["baseline"]


def test_service_raises_on_unknown_method(
    build_evidence_snapshot,
    build_requirements_snapshot,
) -> None:
    request = TraceabilityRequest(
        method_name="unknown",
        requirements=build_requirements_snapshot(),
        evidence=build_evidence_snapshot(),
    )

    with pytest.raises(UnknownTraceabilityMethodError):
        build_default_traceability_service().execute(request)


def test_service_wraps_method_failure(
    build_evidence_snapshot,
    build_requirements_snapshot,
) -> None:
    class FailingMethod:
        name = "failing"

        def run(self, request: TraceabilityRequest) -> NoReturn:
            raise RuntimeError("boom")

    service = TraceabilityService(methods={"failing": FailingMethod()})
    request = TraceabilityRequest(
        method_name="failing",
        requirements=build_requirements_snapshot(),
        evidence=build_evidence_snapshot(),
    )

    with pytest.raises(TraceabilityMethodExecutionError):
        service.execute(request)


def test_service_propagates_run_canceled_error(
    build_evidence_snapshot,
    build_requirements_snapshot,
) -> None:
    class CancelingMethod:
        name = "canceling"

        def run(self, request: TraceabilityRequest, *, is_canceled=None) -> NoReturn:
            raise RunCanceledError("Canceled by user.")

    service = TraceabilityService(methods={"canceling": CancelingMethod()})
    request = TraceabilityRequest(
        method_name="canceling",
        requirements=build_requirements_snapshot(),
        evidence=build_evidence_snapshot(),
    )

    with pytest.raises(RunCanceledError):
        service.execute(request, is_canceled=lambda: True)
