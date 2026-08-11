from dataclasses import replace

from testar_trace.domain.formal_requirements import (
    FormalConformancePolicy,
    FormalElementBinding,
    FormalizationStatus,
    FormalRequirementSet,
    ObservableField,
    ObservableOperator,
    ObservablePredicate,
    ObservableSelector,
    RequirementObservable,
)
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
)
from testar_trace.domain.traceability import (
    AssessmentScopeKind,
    AssessmentViewKind,
    CompletenessStatus,
    TraceEvidenceBasis,
    TraceOccurrenceStatus,
)
from testar_trace.execution import TraceContext
from testar_trace.methods.automata_conformance import (
    trace_with_automata_conformance,
)


def test_approved_observables_produce_exact_complete_witness() -> None:
    result = trace_with_automata_conformance(
        _requirements(),
        _models(order=("open", "submit")),
        TraceContext(),
    )

    assessment = _requirement_assessment(result)
    occurrence = result.occurrences[0]

    assert assessment.completeness is CompletenessStatus.COMPLETE
    assert assessment.coverage_ratio == 1.0
    assert occurrence.status is TraceOccurrenceStatus.FULL
    assert occurrence.evidence_basis is TraceEvidenceBasis.FORMAL_MODEL_CHECK
    assert [target.target_id for target in occurrence.target_path] == [
        "t-open",
        "t-submit",
    ]
    assert all(link.score == 1.0 for link in result.links)


def test_formal_product_rejects_wrong_event_order() -> None:
    result = trace_with_automata_conformance(
        _requirements(),
        _models(order=("submit", "open")),
        TraceContext(),
    )

    assert _requirement_assessment(result).completeness is CompletenessStatus.INCOMPLETE
    assert result.occurrences[0].status is TraceOccurrenceStatus.PARTIAL


def test_intervening_transition_policy_is_explicit() -> None:
    permissive = trace_with_automata_conformance(
        _requirements(),
        _models(order=("open", "noise", "submit")),
        TraceContext(),
    )
    strict_requirements = _requirements(
        policy=FormalConformancePolicy(
            allow_intervening_transitions=False,
            maximum_intervening_transitions=0,
        )
    )
    strict = trace_with_automata_conformance(
        strict_requirements,
        _models(order=("open", "noise", "submit")),
        TraceContext(),
    )

    assert (
        _requirement_assessment(permissive).completeness is CompletenessStatus.COMPLETE
    )
    assert _requirement_assessment(strict).completeness is CompletenessStatus.INCOMPLETE


def test_missing_draft_or_incomplete_formalization_is_not_assessable() -> None:
    approved = _requirements()
    assert approved.formalization is not None
    values = (
        replace(approved, formalization=None),
        replace(
            approved,
            formalization=replace(
                approved.formalization,
                status=FormalizationStatus.DRAFT,
            ),
        ),
        replace(
            approved,
            formalization=replace(
                approved.formalization,
                bindings=approved.formalization.bindings[:1],
            ),
        ),
    )

    for requirements in values:
        result = trace_with_automata_conformance(
            requirements,
            _models(order=("open", "submit")),
            TraceContext(),
        )
        assert (
            _requirement_assessment(result).completeness
            is CompletenessStatus.NOT_ASSESSABLE
        )
        assert result.occurrences == ()


def _requirements(*, policy: FormalConformancePolicy | None = None) -> RequirementSet:
    requirement_id = "req-login"
    flow_id = "login-flow"
    elements = (
        RequirementElement(
            id="login-open",
            requirement_id=requirement_id,
            text="Open login",
            kind="main_step",
            order_index=0,
        ),
        RequirementElement(
            id="login-submit",
            requirement_id=requirement_id,
            text="Submit login",
            kind="main_step",
            order_index=1,
        ),
    )
    observables = tuple(
        RequirementObservable(
            id=f"observable-{name}",
            requirement_id=requirement_id,
            label=label,
            selectors=(
                ObservableSelector(
                    predicates=(
                        ObservablePredicate(
                            field=ObservableField.ACTION_DESCRIPTION,
                            operator=ObservableOperator.EQUALS,
                            value=label,
                        ),
                    )
                ),
            ),
        )
        for name, label in (("open", "Open login"), ("submit", "Submit login"))
    )
    formalization = FormalRequirementSet(
        status=FormalizationStatus.APPROVED,
        observables=observables,
        bindings=(
            FormalElementBinding(
                id="binding-open",
                requirement_element_id="login-open",
                observable_id="observable-open",
            ),
            FormalElementBinding(
                id="binding-submit",
                requirement_element_id="login-submit",
                observable_id="observable-submit",
            ),
        ),
        policy=policy or FormalConformancePolicy(),
    )
    return RequirementSet(
        requirements=(Requirement(id=requirement_id, title="Login"),),
        elements=elements,
        flows=(
            RequirementFlow(
                id=flow_id,
                requirement_id=requirement_id,
                title="Login",
                entry_node_id="node-open",
                branches=(
                    RequirementFlowBranch(
                        id="main",
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        title="Main",
                        kind=RequirementFlowBranchKind.MAIN,
                        entry_node_id="node-open",
                    ),
                ),
                nodes=(
                    RequirementFlowNode(
                        id="node-open",
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        branch_id="main",
                        element_id="login-open",
                    ),
                    RequirementFlowNode(
                        id="node-submit",
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        branch_id="main",
                        element_id="login-submit",
                        outcome=RequirementPathOutcome.SUCCESS,
                    ),
                ),
                edges=(
                    RequirementFlowEdge(
                        id="edge-submit",
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        source_node_id="node-open",
                        target_node_id="node-submit",
                        kind=RequirementFlowEdgeKind.NEXT,
                    ),
                ),
            ),
        ),
        formalization=formalization,
    )


def _models(*, order: tuple[str, ...]) -> StateModelCollection:
    model_id = "model"
    states = tuple(
        State(id=f"s{index}", state_model_id=model_id, title=f"State {index}")
        for index in range(len(order) + 1)
    )
    actions = tuple(
        Action(
            id=f"a-{name}",
            state_model_id=model_id,
            description={
                "open": "Open login",
                "submit": "Submit login",
                "noise": "Inspect help",
            }[name],
        )
        for name in dict.fromkeys(order)
    )
    transitions = tuple(
        Transition(
            id=f"t-{name}",
            state_model_id=model_id,
            source_state_id=f"s{index}",
            action_id=f"a-{name}",
            target_state_id=f"s{index + 1}",
        )
        for index, name in enumerate(order)
    )
    return StateModelCollection(
        id="models",
        title="Models",
        models=(
            StateModel(
                id=model_id,
                title="Login model",
                initial_state_ids=("s0",),
                states=states,
                actions=actions,
                transitions=transitions,
            ),
        ),
    )


def _requirement_assessment(result):
    return next(
        assessment
        for assessment in result.assessments
        if assessment.scope_kind is AssessmentScopeKind.REQUIREMENT
        and assessment.view_kind is AssessmentViewKind.STATE_MODEL_COLLECTION
    )
