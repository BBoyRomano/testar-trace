from collections.abc import Callable
from typing import cast

import pytest

from testar_trace import (
    CancellationToken,
    ProgressEvent,
    RequirementSet,
    StateModelCollection,
    TraceabilityResult,
    TraceCallable,
    TraceCancelledError,
    TraceContext,
    analyze_traceability,
)


def test_analyze_traceability_runs_the_supplied_method(
    requirement_set: RequirementSet,
    state_model_collection: StateModelCollection,
    dummy_trace_method: TraceCallable,
) -> None:
    result = analyze_traceability(
        requirement_set,
        state_model_collection,
        method=dummy_trace_method,
    )

    assert result.id == "test-result"


def test_analyze_traceability_reports_its_orchestration_boundary(
    requirement_set: RequirementSet,
    state_model_collection: StateModelCollection,
    dummy_trace_method: TraceCallable,
) -> None:
    events: list[ProgressEvent] = []

    analyze_traceability(
        requirement_set,
        state_model_collection,
        method=dummy_trace_method,
        context=TraceContext(progress=events.append),
    )

    assert [event.phase for event in events] == [
        "analysis.started",
        "analysis.completed",
    ]


def test_analyze_traceability_rejects_a_non_callable_method(
    requirement_set: RequirementSet,
    state_model_collection: StateModelCollection,
) -> None:
    with pytest.raises(TypeError, match="method must be callable"):
        analyze_traceability(
            requirement_set,
            state_model_collection,
            method=cast("TraceCallable", "not-callable"),
        )


def test_analyze_traceability_honors_cancellation_before_start(
    requirement_set: RequirementSet,
    state_model_collection: StateModelCollection,
    dummy_trace_method: TraceCallable,
) -> None:
    cancellation = CancellationToken()
    cancellation.cancel()

    with pytest.raises(TraceCancelledError, match="cancelled"):
        analyze_traceability(
            requirement_set,
            state_model_collection,
            method=dummy_trace_method,
            context=TraceContext(cancellation=cancellation),
        )


def test_analyze_traceability_rejects_an_invalid_method_result(
    requirement_set: RequirementSet,
    state_model_collection: StateModelCollection,
) -> None:
    invalid_method = cast(
        "Callable[[RequirementSet, StateModelCollection, TraceContext], TraceabilityResult]",
        lambda _requirements, _state_models, _context: object(),
    )

    with pytest.raises(TypeError, match="must return a TraceabilityResult"):
        analyze_traceability(
            requirement_set,
            state_model_collection,
            method=invalid_method,
        )
