from typing import cast

import pytest

from testar_trace import CompletenessReferenceLabel, evaluate_completeness
from testar_trace.domain import AssessmentScopeKind, CompletenessStatus
from testar_trace.execution import TraceContext
from testar_trace.methods.noop import trace_with_noop


def test_evaluate_completeness_reports_three_class_metrics(
    requirement_set,
    state_model_collection,
) -> None:
    result = trace_with_noop(requirement_set, state_model_collection, TraceContext())
    labels = (
        CompletenessReferenceLabel(
            scope_kind=AssessmentScopeKind.REQUIREMENT,
            scope_id="req-1",
            completeness=CompletenessStatus.NOT_ASSESSABLE,
        ),
    )

    evaluation = evaluate_completeness(result, labels)

    assert evaluation.total == 1
    assert evaluation.correct == 1
    assert evaluation.accuracy == 1
    assert evaluation.assessability_rate == 0
    assert evaluation.confusion_matrix[2].not_assessable == 1


def test_evaluate_completeness_rejects_unknown_scopes(
    requirement_set,
    state_model_collection,
) -> None:
    result = trace_with_noop(requirement_set, state_model_collection, TraceContext())
    labels = (
        CompletenessReferenceLabel(
            scope_kind=AssessmentScopeKind.REQUIREMENT,
            scope_id="missing",
            completeness=CompletenessStatus.COMPLETE,
        ),
    )

    with pytest.raises(ValueError, match="no collection assessment"):
        evaluate_completeness(result, labels)


def test_reference_label_rejects_non_enum_values() -> None:
    with pytest.raises(TypeError, match="scope_kind"):
        CompletenessReferenceLabel(
            scope_kind=cast(AssessmentScopeKind, "requirement"),
            scope_id="req-1",
            completeness=CompletenessStatus.COMPLETE,
        )


def test_evaluate_completeness_requires_an_immutable_label_collection(
    requirement_set,
    state_model_collection,
) -> None:
    result = trace_with_noop(requirement_set, state_model_collection, TraceContext())

    with pytest.raises(TypeError, match="tuple"):
        evaluate_completeness(
            result,
            cast(tuple[CompletenessReferenceLabel, ...], []),
        )
