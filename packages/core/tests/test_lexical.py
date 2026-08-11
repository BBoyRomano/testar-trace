import pytest

from testar_trace import create_builtin_method_registry
from testar_trace.domain.requirements import (
    Requirement,
    RequirementElement,
    RequirementFlow,
    RequirementFlowBranch,
    RequirementFlowBranchKind,
    RequirementFlowEdge,
    RequirementFlowEdgeKind,
    RequirementFlowNode,
    RequirementPathOutcome,
    RequirementSet,
)
from testar_trace.domain.state_models import (
    Action,
    State,
    StateModel,
    StateModelCollection,
    Transition,
    Widget,
)
from testar_trace.domain.traceability import (
    AssessmentScopeKind,
    AssessmentViewKind,
    CompletenessStatus,
    CoverageStatus,
    TraceTargetKind,
)
from testar_trace.execution import ProgressEvent, TraceContext
from testar_trace.methods.lexical import (
    LexicalConfig,
    LexicalMethod,
    trace_with_lexical,
)


def test_lexical_returns_highlightable_links_and_scoped_coverage() -> None:
    requirements = _requirements()
    state_models = _state_models()

    result = trace_with_lexical(requirements, state_models, TraceContext())

    assert result.occurrences == ()
    assert result.path_materialization.is_exhaustive
    assert result.links
    assert {link.requirement_element_id for link in result.links} == {"cancel"}
    assert all(link.state_model_id == "model-1" for link in result.links)
    assert any(
        link.target_ref.kind is TraceTargetKind.TRANSITION for link in result.links
    )
    assert result.links[0].metadata["matched_tokens"] == (
        "cancel",
        "registration",
    )

    requirement_assessment = _assessment(
        result,
        AssessmentScopeKind.REQUIREMENT,
        "UC-04",
        AssessmentViewKind.STATE_MODEL_COLLECTION,
    )
    assert requirement_assessment.status is CoverageStatus.PARTIALLY_COVERED
    assert requirement_assessment.coverage_ratio == 0.5
    assert requirement_assessment.covered_element_ids == ("cancel",)
    assert requirement_assessment.missing_element_ids == ("confirmation",)
    assert requirement_assessment.completeness is (CompletenessStatus.NOT_ASSESSABLE)

    path = result.path_materialization.paths[0]
    path_assessment = _assessment(
        result,
        AssessmentScopeKind.PATH,
        path.id,
        AssessmentViewKind.STATE_MODEL_COLLECTION,
    )
    assert path_assessment.coverage_ratio == 0.5
    assert result.summary.overall_coverage_ratio == 0.5
    assert result.summary.total_paths == 1
    assert result.summary.not_assessable_paths == 1


def test_lexical_is_deterministic_and_respects_retention_threshold() -> None:
    requirements = _requirements()
    state_models = _state_models()
    config = LexicalConfig(retention_threshold=0.9)

    first = trace_with_lexical(
        requirements,
        state_models,
        TraceContext(),
        config=config,
    )
    second = trace_with_lexical(
        requirements,
        state_models,
        TraceContext(),
        config=config,
    )

    assert len(first.links) == 1
    assert first.links[0].id == second.links[0].id
    assert first.links[0].score == second.links[0].score
    assert first.links[0].score == pytest.approx(0.9428090415820632)


def test_lexical_reports_progress() -> None:
    events: list[ProgressEvent] = []

    trace_with_lexical(
        _requirements(),
        _state_models(),
        TraceContext(progress=events.append),
    )

    assert [event.phase for event in events] == [
        "lexical.started",
        "lexical.matching",
        "lexical.matching",
        "lexical.assessing",
        "lexical.completed",
    ]
    assert all(event.metadata["total_requirements"] == 1 for event in events)
    assert all(event.metadata["total_paths"] == 1 for event in events)


def test_collection_coverage_combines_links_without_cross_model_occurrences() -> None:
    first_model = _state_models().models[0]
    second_model = StateModel(
        id="model-2",
        title="Confirmation model",
        states=(
            State(
                id="state-confirmation",
                state_model_id="model-2",
                title="Confirmation page",
            ),
        ),
        actions=(
            Action(
                id="action-confirmation",
                state_model_id="model-2",
                description="Show success message",
            ),
        ),
    )
    models = StateModelCollection(
        id="models",
        title="State models",
        models=(first_model, second_model),
    )

    result = trace_with_lexical(_requirements(), models, TraceContext())

    collection = _assessment(
        result,
        AssessmentScopeKind.REQUIREMENT,
        "UC-04",
        AssessmentViewKind.STATE_MODEL_COLLECTION,
    )
    per_model = tuple(
        assessment
        for assessment in result.assessments
        if assessment.scope_kind is AssessmentScopeKind.REQUIREMENT
        and assessment.scope_id == "UC-04"
        and assessment.view_kind is AssessmentViewKind.STATE_MODEL
    )
    assert collection.coverage_ratio == 1.0
    assert collection.covered_element_ids == ("cancel", "confirmation")
    assert [assessment.coverage_ratio for assessment in per_model] == [0.5, 0.5]
    assert {link.state_model_id for link in result.links} == {"model-1", "model-2"}
    assert result.occurrences == ()


def test_lexical_is_registered_as_a_builtin() -> None:
    method = create_builtin_method_registry().get("lexical")

    assert method is not None
    assert method.name == "Lexical"


def test_lexical_config_rejects_invalid_retention_threshold() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        LexicalConfig(retention_threshold=1.1)


def test_configured_lexical_method_is_callable() -> None:
    method = LexicalMethod(config=LexicalConfig(retention_threshold=0.9))

    result = method(_requirements(), _state_models(), TraceContext())

    assert len(result.links) == 1


def _assessment(result, scope_kind, scope_id, view_kind):
    return next(
        assessment
        for assessment in result.assessments
        if assessment.scope_kind is scope_kind
        and assessment.scope_id == scope_id
        and assessment.view_kind is view_kind
    )


def _requirements() -> RequirementSet:
    requirement_id = "UC-04"
    flow_id = "UC-04:flow"
    return RequirementSet(
        requirements=(Requirement(id=requirement_id, title="Cancel registration"),),
        elements=(
            RequirementElement(
                id="cancel",
                requirement_id=requirement_id,
                text="Cancel registration",
            ),
            RequirementElement(
                id="confirmation",
                requirement_id=requirement_id,
                text="Show success message",
            ),
        ),
        flows=(
            RequirementFlow(
                id=flow_id,
                requirement_id=requirement_id,
                title="Main flow",
                entry_node_id="node-cancel",
                branches=(
                    RequirementFlowBranch(
                        id="main",
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        title="Main",
                        kind=RequirementFlowBranchKind.MAIN,
                        entry_node_id="node-cancel",
                    ),
                ),
                nodes=(
                    RequirementFlowNode(
                        id="node-cancel",
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        branch_id="main",
                        element_id="cancel",
                    ),
                    RequirementFlowNode(
                        id="node-confirmation",
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        branch_id="main",
                        element_id="confirmation",
                        outcome=RequirementPathOutcome.SUCCESS,
                    ),
                ),
                edges=(
                    RequirementFlowEdge(
                        id="edge-cancel-confirmation",
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        source_node_id="node-cancel",
                        target_node_id="node-confirmation",
                        kind=RequirementFlowEdgeKind.NEXT,
                    ),
                ),
            ),
        ),
    )


def _state_models() -> StateModelCollection:
    model_id = "model-1"
    return StateModelCollection(
        id="models",
        title="State models",
        models=(
            StateModel(
                id=model_id,
                title="Registration model",
                states=(
                    State(
                        id="state-enrollment",
                        state_model_id=model_id,
                        title="Enrollment page",
                    ),
                    State(
                        id="state-dashboard",
                        state_model_id=model_id,
                        title="Dashboard",
                    ),
                ),
                widgets=(
                    Widget(
                        id="widget-cancel",
                        state_model_id=model_id,
                        state_id="state-enrollment",
                        tag_name="button",
                        text="Cancel registration",
                    ),
                ),
                actions=(
                    Action(
                        id="action-cancel",
                        state_model_id=model_id,
                        description="Cancel registration",
                        target_widget_id="widget-cancel",
                    ),
                ),
                transitions=(
                    Transition(
                        id="transition-cancel",
                        state_model_id=model_id,
                        source_state_id="state-enrollment",
                        action_id="action-cancel",
                        target_state_id="state-dashboard",
                    ),
                ),
            ),
        ),
    )
