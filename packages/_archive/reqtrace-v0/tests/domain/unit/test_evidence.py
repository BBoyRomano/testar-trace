from datetime import datetime, timezone

import pytest

from reqtrace.domain.evidence.enums import (
    ActionKind,
    AttachmentKind,
    EvidenceArtifactKind,
    EvidenceTool,
    ExecutionRunStatus,
    ObservationKind,
    StateModelLayer,
)
from reqtrace.domain.evidence.models import (
    Action,
    ApplicationState,
    Attachment,
    EvidenceArtifact,
    ExecutionRun,
    Observation,
    Transition,
    UIElement,
)


def test_evidence_sequence_can_be_created() -> None:
    run = ExecutionRun(
        id="run-1",
        tool_name="sample-tool",
        tool=EvidenceTool.OTHER,
        status=ExecutionRunStatus.COMPLETED,
        state_model_layers=[StateModelLayer.SEQUENCE],
    )
    state_a = ApplicationState(
        id="state-a",
        title="Sample page",
        url="/sample-page",
    )
    element = UIElement(
        id="el-1",
        state_id=state_a.id,
        text="Continue",
        css_selector="#continue",
    )
    action = Action(
        id="act-1",
        kind=ActionKind.CLICK,
        source_state_id=state_a.id,
        target_element_id=element.id,
    )
    transition = Transition(
        id="tr-1",
        from_state_id=state_a.id,
        action_id=action.id,
        to_state_id="state-b",
        run_id=run.id,
        occurred_at=datetime.now(timezone.utc),
    )
    observation = Observation(
        id="obs-1",
        run_id=run.id,
        kind=ObservationKind.MESSAGE,
        text="The next page is shown",
        transition_id=transition.id,
    )

    assert transition.to_state_id == "state-b"
    assert observation.transition_id == transition.id
    assert action.target_element_id == element.id
    assert run.tool == EvidenceTool.OTHER
    assert run.state_model_layers == [StateModelLayer.SEQUENCE]


def test_execution_run_rejects_end_before_start() -> None:
    with pytest.raises(ValueError):
        ExecutionRun(
            id="run-1",
            tool_name="sample-tool",
            status=ExecutionRunStatus.FAILED,
            started_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
            ended_at=datetime(2026, 1, 1, 11, 59, tzinfo=timezone.utc),
        )


def test_execution_run_rejects_duplicate_state_model_layers() -> None:
    with pytest.raises(ValueError):
        ExecutionRun(
            id="run-1",
            tool_name="TESTAR",
            tool=EvidenceTool.TESTAR,
            status=ExecutionRunStatus.COMPLETED,
            state_model_layers=[StateModelLayer.CONCRETE, StateModelLayer.CONCRETE],
        )


def test_observation_requires_a_state_or_transition_anchor() -> None:
    with pytest.raises(ValueError):
        Observation(
            id="obs-1",
            run_id="run-1",
            kind=ObservationKind.MESSAGE,
            text="Standalone observation",
        )


def test_observation_with_only_state_anchor_is_valid() -> None:
    observation = Observation(
        id="obs-1",
        run_id="run-1",
        kind=ObservationKind.MESSAGE,
        text="State scoped observation",
        state_id="state-1",
    )

    assert observation.state_id == "state-1"


def test_attachment_requires_an_owner_reference() -> None:
    with pytest.raises(ValueError):
        Attachment(
            id="att-1",
            kind=AttachmentKind.SCREENSHOT,
            path_or_uri="artifacts/screenshot.png",
        )


def test_attachment_with_only_observation_owner_is_valid() -> None:
    attachment = Attachment(
        id="att-1",
        kind=AttachmentKind.SCREENSHOT,
        path_or_uri="artifacts/screenshot.png",
        observation_id="obs-1",
    )

    assert attachment.observation_id == "obs-1"


def test_transition_rejects_negative_order_index() -> None:
    with pytest.raises(ValueError):
        Transition(
            id="tr-1",
            from_state_id="state-a",
            action_id="act-1",
            order_index=-1,
        )


def test_execution_run_rejects_blank_tool_name() -> None:
    with pytest.raises(ValueError):
        ExecutionRun(
            id="run-1",
            tool_name="   ",
            status=ExecutionRunStatus.COMPLETED,
        )


def test_attachment_rejects_blank_path_or_uri() -> None:
    with pytest.raises(ValueError):
        Attachment(
            id="att-1",
            kind=AttachmentKind.SCREENSHOT,
            path_or_uri="   ",
            observation_id="obs-1",
        )


def test_evidence_artifact_can_be_created() -> None:
    artifact = EvidenceArtifact(
        id="artifact-1",
        kind=EvidenceArtifactKind.STATE_MODEL_JSON,
        path_or_uri="evidence/runs/run-1/model/model.json",
        run_id="run-1",
        model_layer=StateModelLayer.CONCRETE,
    )

    assert artifact.kind == EvidenceArtifactKind.STATE_MODEL_JSON
    assert artifact.model_layer == StateModelLayer.CONCRETE
