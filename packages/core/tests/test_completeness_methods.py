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
    ExecutionSequence,
    ExecutionStep,
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
    TraceTargetKind,
    TraceTargetRef,
)
from testar_trace.execution import TraceContext
from testar_trace.methods.execution_alignment import trace_with_execution_alignment
from testar_trace.methods.graph_alignment import trace_with_graph_alignment


def test_builtins_replace_sequence_with_completeness_alignment_methods() -> None:
    method_ids = tuple(method.id for method in create_builtin_method_registry())

    assert "sequence" not in method_ids
    assert "graph-alignment" in method_ids
    assert "execution-alignment" in method_ids


def test_graph_alignment_requires_one_connected_route() -> None:
    result = trace_with_graph_alignment(
        _requirements(),
        _state_models(connected=True),
        TraceContext(),
    )

    assessment = _requirement_assessment(result, "graph-alignment")
    assert assessment.completeness is CompletenessStatus.COMPLETE
    assert assessment.coverage_ratio == 1.0
    assert len(result.occurrences) == 1
    assert result.occurrences[0].status is TraceOccurrenceStatus.FULL
    assert result.occurrences[0].evidence_basis is TraceEvidenceBasis.STATE_MODEL_GRAPH
    assert {link.requirement_element_id for link in result.links} == {
        "req-login:open",
        "req-login:enter",
        "req-login:submit",
    }
    assert {link.target_ref.kind for link in result.links} == {TraceTargetKind.ACTION}
    assert {target.kind for target in result.occurrences[0].target_path} == {
        TraceTargetKind.ACTION,
        TraceTargetKind.TRANSITION,
    }


def test_graph_alignment_preserves_a_direct_state_target_on_the_transition_route() -> (
    None
):
    result = trace_with_graph_alignment(
        _single_element_requirements("Dashboard ready"),
        _single_transition_model(target_title="Dashboard ready"),
        TraceContext(),
    )

    assert result.links[0].target_ref.kind is TraceTargetKind.STATE
    assert result.links[0].target_ref.target_id == "target"
    assert len(result.occurrences[0].target_path) == 2
    assert result.occurrences[0].target_path[0].kind is TraceTargetKind.TRANSITION
    assert result.occurrences[0].target_path[0].target_id == "single-transition"
    assert result.occurrences[0].target_path[1] == result.links[0].target_ref


def test_graph_alignment_uses_source_state_evidence_for_preconditions() -> None:
    result = trace_with_graph_alignment(
        _requirements_for_elements((("precondition", "Start"),)),
        _single_transition_model(target_title="Dashboard ready"),
        TraceContext(),
    )

    assert result.links[0].target_ref == TraceTargetRef(
        kind=TraceTargetKind.STATE,
        target_id="source",
    )
    assert result.links[0].metadata["facet"] == "source-state"


def test_graph_alignment_uses_target_state_evidence_for_postconditions() -> None:
    result = trace_with_graph_alignment(
        _requirements_for_elements((("postcondition", "Dashboard ready"),)),
        _single_transition_model(target_title="Dashboard ready"),
        TraceContext(),
    )

    assert result.links[0].target_ref == TraceTargetRef(
        kind=TraceTargetKind.STATE,
        target_id="target",
    )
    assert result.links[0].metadata["facet"] == "target-state"


def test_graph_alignment_allows_action_and_outcome_on_one_transition() -> None:
    result = trace_with_graph_alignment(
        _requirements_for_elements(
            (("main_step", "Continue"), ("main_step", "Dashboard ready"))
        ),
        _single_transition_model(target_title="Dashboard ready"),
        TraceContext(),
    )

    assert result.occurrences[0].status is TraceOccurrenceStatus.FULL
    assert [link.target_ref.kind for link in result.links] == [
        TraceTargetKind.ACTION,
        TraceTargetKind.STATE,
    ]
    assert [target.kind for target in result.occurrences[0].target_path] == [
        TraceTargetKind.TRANSITION,
        TraceTargetKind.ACTION,
        TraceTargetKind.STATE,
    ]


def test_graph_alignment_does_not_reuse_one_action_for_two_steps() -> None:
    result = trace_with_graph_alignment(
        _requirements_for_elements(
            (("main_step", "Continue"), ("main_step", "Continue"))
        ),
        _single_transition_model(target_title="Dashboard ready"),
        TraceContext(),
    )

    assert result.occurrences[0].status is TraceOccurrenceStatus.PARTIAL
    assert len(result.links) == 1


def test_graph_alignment_allows_trigger_and_first_step_to_share_an_action() -> None:
    result = trace_with_graph_alignment(
        _requirements_for_elements(
            (("trigger", "Continue"), ("main_step", "Continue"))
        ),
        _single_transition_model(target_title="Dashboard ready"),
        TraceContext(),
    )

    assert result.occurrences[0].status is TraceOccurrenceStatus.FULL
    assert len(result.links) == 2
    assert {link.target_ref.kind for link in result.links} == {TraceTargetKind.ACTION}
    assert all(
        link.metadata["route_transition_id"] == "single-transition"
        for link in result.links
    )


def test_graph_alignment_rejects_disconnected_semantic_matches() -> None:
    result = trace_with_graph_alignment(
        _requirements(),
        _state_models(connected=False),
        TraceContext(),
    )

    assessment = _requirement_assessment(result, "graph-alignment")
    assert assessment.completeness is CompletenessStatus.INCOMPLETE
    assert assessment.coverage_ratio < 1.0
    assert result.occurrences[0].status is TraceOccurrenceStatus.PARTIAL


def test_collection_coverage_never_stitches_a_path_across_models() -> None:
    result = trace_with_graph_alignment(
        _requirements(),
        _split_state_models(),
        TraceContext(),
    )

    assessment = _requirement_assessment(result, "graph-alignment")

    assert assessment.coverage_ratio == 1.0
    assert assessment.completeness is CompletenessStatus.INCOMPLETE
    assert all(
        occurrence.status is TraceOccurrenceStatus.PARTIAL
        for occurrence in result.occurrences
    )


def test_execution_alignment_is_not_assessable_without_recorded_sequences() -> None:
    result = trace_with_execution_alignment(
        _requirements(),
        _state_models(connected=True),
        TraceContext(),
    )

    assessment = _requirement_assessment(result, "execution-alignment")
    assert assessment.completeness is CompletenessStatus.NOT_ASSESSABLE
    assert assessment.coverage_ratio is None
    assert result.occurrences == ()


def test_execution_alignment_requires_chronological_order() -> None:
    complete = trace_with_execution_alignment(
        _requirements(),
        _state_models(connected=True, sequence_order=("t1", "t2", "t3")),
        TraceContext(),
    )
    incomplete = trace_with_execution_alignment(
        _requirements(),
        _state_models(connected=True, sequence_order=("t1", "t3", "t2")),
        TraceContext(),
    )

    assert (
        _requirement_assessment(complete, "execution-alignment").completeness
        is CompletenessStatus.COMPLETE
    )
    assert (
        _requirement_assessment(incomplete, "execution-alignment").completeness
        is CompletenessStatus.INCOMPLETE
    )
    assert complete.occurrences[0].execution_sequence_id == "run-1"


def _requirement_assessment(result, method_id: str):
    return next(
        assessment
        for assessment in result.assessments
        if assessment.id.startswith(f"{method_id}:assessment:requirement:")
        and assessment.scope_kind is AssessmentScopeKind.REQUIREMENT
        and assessment.view_kind is AssessmentViewKind.STATE_MODEL_COLLECTION
    )


def _requirements() -> RequirementSet:
    requirement_id = "req-login"
    flow_id = "req-login:flow"
    elements = (
        RequirementElement(
            id="req-login:open",
            requirement_id=requirement_id,
            kind="main_step",
            text="Open login",
            order_index=0,
        ),
        RequirementElement(
            id="req-login:enter",
            requirement_id=requirement_id,
            kind="main_step",
            text="Enter username",
            order_index=1,
        ),
        RequirementElement(
            id="req-login:submit",
            requirement_id=requirement_id,
            kind="main_step",
            text="Submit login",
            order_index=2,
        ),
    )

    nodes = tuple(
        RequirementFlowNode(
            id=f"node-{index}",
            requirement_id=requirement_id,
            flow_id=flow_id,
            branch_id="main",
            element_id=element.id,
            outcome=(
                RequirementPathOutcome.SUCCESS if index == len(elements) else None
            ),
        )
        for index, element in enumerate(elements, start=1)
    )
    return RequirementSet(
        requirements=(Requirement(id=requirement_id, title="Login"),),
        elements=elements,
        flows=(
            RequirementFlow(
                id=flow_id,
                requirement_id=requirement_id,
                title="Login",
                entry_node_id="node-1",
                branches=(
                    RequirementFlowBranch(
                        id="main",
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        title="Main flow",
                        kind=RequirementFlowBranchKind.MAIN,
                        entry_node_id="node-1",
                    ),
                ),
                nodes=nodes,
                edges=(
                    RequirementFlowEdge(
                        id="edge-1",
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        source_node_id="node-1",
                        target_node_id="node-2",
                        kind=RequirementFlowEdgeKind.NEXT,
                    ),
                    RequirementFlowEdge(
                        id="edge-2",
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        source_node_id="node-2",
                        target_node_id="node-3",
                        kind=RequirementFlowEdgeKind.NEXT,
                    ),
                ),
            ),
        ),
    )


def _single_element_requirements(text: str) -> RequirementSet:
    requirement_id = "req-single"
    flow_id = "req-single:flow"
    element = RequirementElement(
        id="req-single:element",
        requirement_id=requirement_id,
        kind="main_step",
        text=text,
        order_index=0,
    )
    node = RequirementFlowNode(
        id="req-single:node",
        requirement_id=requirement_id,
        flow_id=flow_id,
        branch_id="main",
        element_id=element.id,
        outcome=RequirementPathOutcome.SUCCESS,
    )
    return RequirementSet(
        requirements=(Requirement(id=requirement_id, title="Single requirement"),),
        elements=(element,),
        flows=(
            RequirementFlow(
                id=flow_id,
                requirement_id=requirement_id,
                title="Single flow",
                entry_node_id=node.id,
                branches=(
                    RequirementFlowBranch(
                        id="main",
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        title="Main flow",
                        kind=RequirementFlowBranchKind.MAIN,
                        entry_node_id=node.id,
                    ),
                ),
                nodes=(node,),
            ),
        ),
    )


def _requirements_for_elements(
    values: tuple[tuple[str, str], ...],
) -> RequirementSet:
    requirement_id = "req-elements"
    flow_id = "req-elements:flow"
    elements = tuple(
        RequirementElement(
            id=f"req-elements:element:{index}",
            requirement_id=requirement_id,
            kind=kind,
            text=text,
            order_index=index,
        )
        for index, (kind, text) in enumerate(values)
    )
    nodes = tuple(
        RequirementFlowNode(
            id=f"req-elements:node:{index}",
            requirement_id=requirement_id,
            flow_id=flow_id,
            branch_id="main",
            element_id=element.id,
            outcome=(
                RequirementPathOutcome.SUCCESS if index == len(elements) - 1 else None
            ),
        )
        for index, element in enumerate(elements)
    )
    edges = tuple(
        RequirementFlowEdge(
            id=f"req-elements:edge:{index}",
            requirement_id=requirement_id,
            flow_id=flow_id,
            source_node_id=nodes[index].id,
            target_node_id=nodes[index + 1].id,
            kind=RequirementFlowEdgeKind.NEXT,
        )
        for index in range(len(nodes) - 1)
    )
    return RequirementSet(
        requirements=(Requirement(id=requirement_id, title="Elements"),),
        elements=elements,
        flows=(
            RequirementFlow(
                id=flow_id,
                requirement_id=requirement_id,
                title="Elements",
                entry_node_id=nodes[0].id,
                branches=(
                    RequirementFlowBranch(
                        id="main",
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        title="Main flow",
                        kind=RequirementFlowBranchKind.MAIN,
                        entry_node_id=nodes[0].id,
                    ),
                ),
                nodes=nodes,
                edges=edges,
            ),
        ),
    )


def _single_transition_model(*, target_title: str) -> StateModelCollection:
    model = StateModel(
        id="single-model",
        title="Single model",
        initial_state_ids=("source",),
        states=(
            State(id="source", state_model_id="single-model", title="Start"),
            State(id="target", state_model_id="single-model", title=target_title),
        ),
        actions=(
            Action(
                id="continue",
                state_model_id="single-model",
                description="Continue",
            ),
        ),
        transitions=(
            Transition(
                id="single-transition",
                state_model_id="single-model",
                source_state_id="source",
                action_id="continue",
                target_state_id="target",
            ),
        ),
    )
    return StateModelCollection(id="single-models", title="Models", models=(model,))


def _state_models(
    *,
    connected: bool,
    sequence_order: tuple[str, ...] | None = None,
) -> StateModelCollection:
    model_id = "model-1"
    states = tuple(
        State(id=f"s{index}", state_model_id=model_id, title=f"State {index}")
        for index in range(6)
    )
    actions = (
        Action(id="a1", state_model_id=model_id, description="Click Login"),
        Action(id="a2", state_model_id=model_id, description="Type username"),
        Action(id="a3", state_model_id=model_id, description="Submit login"),
    )
    transitions = (
        Transition(
            id="t1",
            state_model_id=model_id,
            source_state_id="s0",
            action_id="a1",
            target_state_id="s1",
        ),
        Transition(
            id="t2",
            state_model_id=model_id,
            source_state_id="s1" if connected else "s2",
            action_id="a2",
            target_state_id="s2" if connected else "s3",
        ),
        Transition(
            id="t3",
            state_model_id=model_id,
            source_state_id="s2" if connected else "s4",
            action_id="a3",
            target_state_id="s3" if connected else "s5",
        ),
    )
    sequences: tuple[ExecutionSequence, ...] = ()
    if sequence_order is not None:
        transitions_by_id = {transition.id: transition for transition in transitions}
        steps = tuple(
            ExecutionStep(
                id=f"step-{index}",
                state_model_id=model_id,
                sequence_id="run-1",
                order_index=index,
                transition_id=transition_id,
                state_id=transitions_by_id[transition_id].source_state_id,
                action_id=transitions_by_id[transition_id].action_id,
            )
            for index, transition_id in enumerate(sequence_order)
        )
        sequences = (
            ExecutionSequence(
                id="run-1",
                state_model_id=model_id,
                title="Recorded login",
                steps=steps,
            ),
        )
    model = StateModel(
        id=model_id,
        title="Login model",
        initial_state_ids=("s0",),
        states=states,
        actions=actions,
        transitions=transitions,
        sequences=sequences,
    )
    return StateModelCollection(id="models", title="Models", models=(model,))


def _split_state_models() -> StateModelCollection:
    first = StateModel(
        id="model-open",
        title="Open login only",
        initial_state_ids=("open-s0",),
        states=(
            State(id="open-s0", state_model_id="model-open", title="Start"),
            State(id="open-s1", state_model_id="model-open", title="Login"),
        ),
        actions=(
            Action(
                id="open-a1",
                state_model_id="model-open",
                description="Open login",
            ),
        ),
        transitions=(
            Transition(
                id="open-t1",
                state_model_id="model-open",
                source_state_id="open-s0",
                action_id="open-a1",
                target_state_id="open-s1",
            ),
        ),
    )
    second = StateModel(
        id="model-submit",
        title="Enter and submit only",
        initial_state_ids=("submit-s0",),
        states=tuple(
            State(
                id=f"submit-s{index}",
                state_model_id="model-submit",
                title=f"State {index}",
            )
            for index in range(3)
        ),
        actions=(
            Action(
                id="submit-a1",
                state_model_id="model-submit",
                description="Enter username",
            ),
            Action(
                id="submit-a2",
                state_model_id="model-submit",
                description="Submit login",
            ),
        ),
        transitions=(
            Transition(
                id="submit-t1",
                state_model_id="model-submit",
                source_state_id="submit-s0",
                action_id="submit-a1",
                target_state_id="submit-s1",
            ),
            Transition(
                id="submit-t2",
                state_model_id="model-submit",
                source_state_id="submit-s1",
                action_id="submit-a2",
                target_state_id="submit-s2",
            ),
        ),
    )
    return StateModelCollection(
        id="models",
        title="Split models",
        models=(first, second),
    )
