from __future__ import annotations

from typing import NoReturn, cast

import pytest

from reqtrace.application.exceptions import (
    RunCanceledError,
    TraceabilityMethodExecutionError,
    UnknownTraceabilityMethodError,
)
from reqtrace.application.ports import TraceabilityMethod
from reqtrace.application.execution.orchestrator import (
    TraceabilityOrchestrator,
    build_default_orchestrator,
)
from reqtrace.application.requests import TraceabilityRequest


def test_orchestrator_exposes_all_default_methods() -> None:
    orchestrator = build_default_orchestrator()
    assert orchestrator.available_methods() == [
        "baseline",
        "candidate_match",
        "conformance_match",
        "flow_match",
        "hybrid_match",
    ]


def test_orchestrator_can_opt_in_to_experimental_methods() -> None:
    orchestrator = build_default_orchestrator(include_experimental_methods=True)
    assert orchestrator.available_methods() == [
        "baseline",
        "candidate_match",
        "conformance_match",
        "flow_match",
        "hybrid_match",
    ]


def test_orchestrator_can_limit_to_baseline_only() -> None:
    orchestrator = build_default_orchestrator(include_experimental_methods=False)
    assert orchestrator.available_methods() == ["baseline"]


def test_orchestrator_raises_on_unknown_method(
    build_evidence_snapshot,
    build_requirements_snapshot,
) -> None:
    request = TraceabilityRequest(
        method_name="unknown",
        requirements=build_requirements_snapshot(),
        evidence=build_evidence_snapshot(),
    )

    with pytest.raises(UnknownTraceabilityMethodError):
        build_default_orchestrator().execute(request)


def test_orchestrator_wraps_method_failure(
    build_evidence_snapshot,
    build_requirements_snapshot,
) -> None:
    class FailingMethod:
        name = "failing"

        def run(
            self,
            request: TraceabilityRequest,
            *,
            progress_callback=None,
            is_canceled=None,
        ) -> NoReturn:
            raise RuntimeError("boom")

    orchestrator = TraceabilityOrchestrator(
        methods={"failing": cast(TraceabilityMethod, FailingMethod())}
    )
    request = TraceabilityRequest(
        method_name="failing",
        requirements=build_requirements_snapshot(),
        evidence=build_evidence_snapshot(),
    )

    with pytest.raises(TraceabilityMethodExecutionError):
        orchestrator.execute(request)


def test_orchestrator_propagates_run_canceled_error(
    build_evidence_snapshot,
    build_requirements_snapshot,
) -> None:
    class CancelingMethod:
        name = "canceling"

        def run(
            self,
            request: TraceabilityRequest,
            *,
            progress_callback=None,
            is_canceled=None,
        ) -> NoReturn:
            raise RunCanceledError("Canceled by user.")

    orchestrator = TraceabilityOrchestrator(
        methods={"canceling": cast(TraceabilityMethod, CancelingMethod())}
    )
    request = TraceabilityRequest(
        method_name="canceling",
        requirements=build_requirements_snapshot(),
        evidence=build_evidence_snapshot(),
    )

    with pytest.raises(RunCanceledError):
        orchestrator.execute(request, is_canceled=lambda: True)



