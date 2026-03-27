import pytest

from reqtrace.domain.requirements.enums import (
    RequirementFlowEdgeKind,
    RequirementFlowKind,
    RequirementFragmentKind,
    RequirementKind,
)
from reqtrace.domain.requirements.models import (
    RequirementArtifact,
    RequirementFlow,
    RequirementFlowEdge,
    RequirementFragment,
)


def test_requirement_artifact_can_be_created() -> None:
    artifact = RequirementArtifact(
        id="req-1",
        kind=RequirementKind.USE_CASE,
        title="Sample requirement",
        external_id="REQ-1",
    )

    assert artifact.kind == RequirementKind.USE_CASE
    assert artifact.external_id == "REQ-1"


def test_requirement_structure_can_represent_branching_flow() -> None:
    artifact = RequirementArtifact(
        id="req-1",
        kind=RequirementKind.USE_CASE,
        title="Sample requirement",
    )
    precondition = RequirementFragment(
        id="frag-pre-1",
        requirement_id=artifact.id,
        kind=RequirementFragmentKind.PRECONDITION,
        text="A valid precondition exists",
    )
    main_step = RequirementFragment(
        id="frag-main-1",
        requirement_id=artifact.id,
        kind=RequirementFragmentKind.MAIN_STEP,
        text="The user performs the main action",
        order_index=1,
    )
    alt_step = RequirementFragment(
        id="frag-alt-1",
        requirement_id=artifact.id,
        kind=RequirementFragmentKind.ALTERNATIVE_STEP,
        text="An alternative outcome is shown",
        order_index=2,
        branch_id="alt-a",
    )
    main_flow = RequirementFlow(
        id="flow-main-1",
        requirement_id=artifact.id,
        name="Main flow",
        flow_kind=RequirementFlowKind.MAIN,
        entry_fragment_id=main_step.id,
    )
    branch_edge = RequirementFlowEdge(
        id="edge-1",
        requirement_id=artifact.id,
        from_fragment_id=main_step.id,
        to_fragment_id=alt_step.id,
        edge_kind=RequirementFlowEdgeKind.BRANCH,
        condition_label="alternative condition",
    )

    assert precondition.kind == RequirementFragmentKind.PRECONDITION
    assert main_flow.entry_fragment_id == main_step.id
    assert branch_edge.edge_kind == RequirementFlowEdgeKind.BRANCH


def test_invalid_self_loop_flow_edge_is_rejected() -> None:
    with pytest.raises(ValueError):
        RequirementFlowEdge(
            id="edge-1",
            requirement_id="req-1",
            from_fragment_id="frag-1",
            to_fragment_id="frag-1",
            edge_kind=RequirementFlowEdgeKind.NEXT,
        )


def test_terminates_self_loop_flow_edge_is_allowed() -> None:
    edge = RequirementFlowEdge(
        id="edge-1",
        requirement_id="req-1",
        from_fragment_id="frag-1",
        to_fragment_id="frag-1",
        edge_kind=RequirementFlowEdgeKind.TERMINATES,
    )

    assert edge.edge_kind == RequirementFlowEdgeKind.TERMINATES


def test_requirement_flow_rejects_blank_name() -> None:
    with pytest.raises(ValueError):
        RequirementFlow(
            id="flow-main-1",
            requirement_id="req-1",
            name="   ",
            flow_kind=RequirementFlowKind.MAIN,
        )


def test_requirement_artifact_rejects_blank_title() -> None:
    with pytest.raises(ValueError):
        RequirementArtifact(
            id="req-1",
            kind=RequirementKind.USE_CASE,
            title="   ",
        )
