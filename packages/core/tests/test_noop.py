import pytest

from testar_trace.domain.requirements import Requirement, RequirementSet
from testar_trace.domain.state_models import StateModelCollection
from testar_trace.domain.traceability import (
    AssessabilityStatus,
    AssessmentScopeKind,
    CompletenessStatus,
)
from testar_trace.execution import (
    CancellationToken,
    ProgressEvent,
    TraceCancelledError,
    TraceContext,
)
from testar_trace.methods.noop import trace_with_noop


def test_noop_returns_app_facing_assessments(
    requirement_set: RequirementSet,
    state_model_collection: StateModelCollection,
) -> None:
    result = trace_with_noop(requirement_set, state_model_collection, TraceContext())

    assert result.id == "noop"
    assert result.path_materialization.paths == ()
    assert result.links == ()
    assert result.occurrences == ()
    assert [assessment.scope_kind for assessment in result.assessments] == [
        AssessmentScopeKind.REQUIREMENT_SET,
        AssessmentScopeKind.REQUIREMENT,
    ]
    requirement_assessment = result.assessments[1]
    assert requirement_assessment.assessability is AssessabilityStatus.NONE
    assert requirement_assessment.completeness is (CompletenessStatus.NOT_ASSESSABLE)


def test_noop_summary_is_derived_from_requirement_assessments(
    state_model_collection: StateModelCollection,
) -> None:
    requirements = RequirementSet(
        requirements=(
            Requirement(id="req-1", title="Login"),
            Requirement(id="req-2", title="Logout"),
        ),
    )

    result = trace_with_noop(requirements, state_model_collection, TraceContext())

    assert result.summary.total_requirements == 2
    assert result.summary.uncovered_requirements == 2
    assert result.summary.not_assessable_requirements == 2
    assert result.summary.total_paths == 0
    assert result.summary.overall_coverage_ratio is None


def test_noop_reports_progress(
    requirement_set: RequirementSet,
    state_model_collection: StateModelCollection,
) -> None:
    events: list[ProgressEvent] = []

    trace_with_noop(
        requirement_set,
        state_model_collection,
        TraceContext(progress=events.append),
    )

    assert [event.phase for event in events] == [
        "noop.started",
        "noop.assessing",
        "noop.completed",
    ]


def test_noop_honours_cancellation(
    requirement_set: RequirementSet,
    state_model_collection: StateModelCollection,
) -> None:
    token = CancellationToken()
    token.cancel()

    with pytest.raises(TraceCancelledError, match="cancelled"):
        trace_with_noop(
            requirement_set,
            state_model_collection,
            TraceContext(cancellation=token),
        )
