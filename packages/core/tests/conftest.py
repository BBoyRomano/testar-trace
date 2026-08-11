from collections.abc import Callable

import pytest

from testar_trace.domain.requirement_paths import PathMaterializationResult
from testar_trace.domain.requirements import Requirement, RequirementSet
from testar_trace.domain.state_models import State, StateModel, StateModelCollection
from testar_trace.domain.traceability import (
    AssessabilityStatus,
    AssessmentScopeKind,
    AssessmentViewKind,
    CompletenessStatus,
    CoverageAssessment,
    CoverageStatus,
    TraceabilityResult,
)
from testar_trace.execution import TraceContext


@pytest.fixture
def requirement_set() -> RequirementSet:
    return RequirementSet(
        requirements=(Requirement(id="req-1", title="Login"),),
    )


@pytest.fixture
def state_model_collection() -> StateModelCollection:
    return StateModelCollection(
        id="models-1",
        title="State models",
        models=(
            StateModel(
                id="model-1",
                title="Login state model",
                states=(State(id="state-1", state_model_id="model-1"),),
            ),
        ),
    )


@pytest.fixture
def empty_trace_result() -> TraceabilityResult:
    return TraceabilityResult(
        id="test-result",
        title="Test result",
        path_materialization=PathMaterializationResult(paths=(), bounded=False),
        assessments=(
            CoverageAssessment(
                id="assessment-1",
                scope_kind=AssessmentScopeKind.REQUIREMENT,
                scope_id="req-1",
                requirement_ids=("req-1",),
                view_kind=AssessmentViewKind.STATE_MODEL_COLLECTION,
                state_model_collection_id="models-1",
                state_model_ids=("model-1",),
                status=CoverageStatus.NOT_COVERED,
                assessability=AssessabilityStatus.NONE,
                completeness=CompletenessStatus.NOT_ASSESSABLE,
            ),
        ),
    )


@pytest.fixture
def dummy_trace_method(
    empty_trace_result: TraceabilityResult,
) -> Callable[[RequirementSet, StateModelCollection, TraceContext], TraceabilityResult]:
    def trace_method(
        requirements: RequirementSet,
        state_models: StateModelCollection,
        context: TraceContext,
    ) -> TraceabilityResult:
        del requirements, state_models
        context.raise_if_cancelled()
        return empty_trace_result

    return trace_method
