import pytest

from reqtrace.domain.common.enums import SourceType
from reqtrace.domain.evidence.enums import (
    ActionKind,
    AttachmentKind,
    EvidenceArtifactKind,
    ExecutionRunStatus,
    ObservationKind,
)
from reqtrace.domain.requirements.enums import (
    RequirementFormat,
    RequirementFlowEdgeKind,
    RequirementFlowKind,
    RequirementFragmentKind,
    RequirementKind,
    RequirementNotation,
)
from reqtrace.ingestion.common.exceptions import IngestionValidationError
from reqtrace.ingestion.common.models import (
    NormalizedActionRecord,
    NormalizedAttachmentRecord,
    NormalizedEvidenceBatch,
    NormalizedEvidenceArtifactRecord,
    NormalizedEvidenceElementRecord,
    NormalizedEvidenceStateRecord,
    NormalizedExecutionRunRecord,
    NormalizedRequirementDocumentRecord,
    NormalizedObservationRecord,
    NormalizedRequirementBatch,
    NormalizedRequirementFlowEdgeRecord,
    NormalizedRequirementFlowRecord,
    NormalizedRequirementFragmentRecord,
    NormalizedRequirementRecord,
    NormalizedTransitionRecord,
)
from reqtrace.ingestion.common.validation import validate_evidence_batch, validate_requirement_batch


def _valid_requirement_batch() -> NormalizedRequirementBatch:
    return NormalizedRequirementBatch(
        documents=[
            NormalizedRequirementDocumentRecord(
                id="doc-1",
                title="Requirements",
                notation=RequirementNotation.USE_CASE,
                file_format=RequirementFormat.MARKDOWN,
                source_type=SourceType.FILE,
                source_name="sample",
            )
        ],
        requirements=[
            NormalizedRequirementRecord(
                id="req-1",
                kind=RequirementKind.USE_CASE,
                title="Sample",
                document_id="doc-1",
                source_type=SourceType.FILE,
                source_name="sample",
            )
        ],
        fragments=[
            NormalizedRequirementFragmentRecord(
                id="frag-1",
                requirement_id="req-1",
                kind=RequirementFragmentKind.MAIN_STEP,
                text="Step 1",
                order_index=1,
            )
        ],
        flows=[
            NormalizedRequirementFlowRecord(
                id="flow-1",
                requirement_id="req-1",
                name="Main flow",
                flow_kind=RequirementFlowKind.MAIN,
                entry_fragment_id="frag-1",
            )
        ],
        flow_edges=[
            NormalizedRequirementFlowEdgeRecord(
                id="edge-1",
                requirement_id="req-1",
                from_fragment_id="frag-1",
                to_fragment_id="frag-1",
                edge_kind=RequirementFlowEdgeKind.NEXT,
            )
        ],
    )


def _valid_evidence_batch() -> NormalizedEvidenceBatch:
    return NormalizedEvidenceBatch(
        states=[
            NormalizedEvidenceStateRecord(
                id="state-a",
                source_type=SourceType.FILE,
                source_name="sample",
            )
        ],
        elements=[
            NormalizedEvidenceElementRecord(
                id="el-1",
                state_id="state-a",
            )
        ],
        actions=[
            NormalizedActionRecord(
                id="action-1",
                kind=ActionKind.CLICK,
                source_state_id="state-a",
                target_element_id="el-1",
            )
        ],
        transitions=[
            NormalizedTransitionRecord(
                id="transition-1",
                from_state_id="state-a",
                action_id="action-1",
                to_state_id="state-a",
                run_id="run-1",
            )
        ],
        runs=[
            NormalizedExecutionRunRecord(
                id="run-1",
                tool_name="TESTAR",
                status=ExecutionRunStatus.COMPLETED,
                source_type=SourceType.FILE,
                source_name="sample",
            )
        ],
        observations=[
            NormalizedObservationRecord(
                id="obs-1",
                run_id="run-1",
                kind=ObservationKind.MESSAGE,
                text="Message",
                state_id="state-a",
                transition_id="transition-1",
            )
        ],
        attachments=[
            NormalizedAttachmentRecord(
                id="attachment-1",
                kind=AttachmentKind.SCREENSHOT,
                path_or_uri="/tmp/screenshot.png",
                run_id="run-1",
                state_id="state-a",
                observation_id="obs-1",
            )
        ],
        artifacts=[
            NormalizedEvidenceArtifactRecord(
                id="artifact-1",
                kind=EvidenceArtifactKind.STATE_MODEL_JSON,
                path_or_uri="/tmp/model.json",
                run_id="run-1",
                source_type=SourceType.FILE,
                source_name="sample",
            )
        ],
    )


def test_requirement_batch_validation_accepts_consistent_references() -> None:
    validate_requirement_batch(_valid_requirement_batch())


def test_evidence_batch_validation_accepts_consistent_references() -> None:
    validate_evidence_batch(_valid_evidence_batch())


def test_requirement_batch_validation_rejects_unknown_requirement_reference() -> None:
    batch = NormalizedRequirementBatch(
        requirements=[
            NormalizedRequirementRecord(
                id="req-1",
                kind=RequirementKind.USE_CASE,
                title="Sample",
                source_type=SourceType.FILE,
                source_name="sample",
            )
        ],
        fragments=[
            NormalizedRequirementFragmentRecord(
                id="frag-1",
                requirement_id="missing",
                kind=RequirementFragmentKind.MAIN_STEP,
                text="Do something",
                order_index=1,
            )
        ],
    )

    with pytest.raises(IngestionValidationError, match="Unknown requirement_id"):
        validate_requirement_batch(batch)


def test_requirement_batch_validation_rejects_duplicate_fragment_ids() -> None:
    batch = NormalizedRequirementBatch(
        requirements=[
            NormalizedRequirementRecord(
                id="req-1",
                kind=RequirementKind.USE_CASE,
                title="Sample",
                source_type=SourceType.FILE,
                source_name="sample",
            )
        ],
        fragments=[
            NormalizedRequirementFragmentRecord(
                id="frag-1",
                requirement_id="req-1",
                kind=RequirementFragmentKind.MAIN_STEP,
                text="Do something",
                order_index=1,
            ),
            NormalizedRequirementFragmentRecord(
                id="frag-1",
                requirement_id="req-1",
                kind=RequirementFragmentKind.MAIN_STEP,
                text="Do something else",
                order_index=2,
            ),
        ],
    )

    with pytest.raises(IngestionValidationError, match="Duplicate fragment ids"):
        validate_requirement_batch(batch)


def test_evidence_batch_validation_rejects_duplicate_state_ids() -> None:
    batch = NormalizedEvidenceBatch(
        states=[
            NormalizedEvidenceStateRecord(
                id="state-a", source_type=SourceType.FILE, source_name="sample"
            ),
            NormalizedEvidenceStateRecord(
                id="state-a", source_type=SourceType.FILE, source_name="sample"
            ),
        ]
    )

    with pytest.raises(IngestionValidationError, match="Duplicate state ids"):
        validate_evidence_batch(batch)


def test_evidence_batch_validation_rejects_unknown_target_element_id() -> None:
    batch = NormalizedEvidenceBatch(
        states=[
            NormalizedEvidenceStateRecord(
                id="state-a", source_type=SourceType.FILE, source_name="sample"
            )
        ],
        actions=[
            NormalizedActionRecord(
                id="action-1",
                kind=ActionKind.CLICK,
                source_state_id="state-a",
                target_element_id="missing-element",
            )
        ],
        runs=[
            NormalizedExecutionRunRecord(
                id="run-1",
                tool_name="TESTAR",
                status=ExecutionRunStatus.COMPLETED,
                source_type=SourceType.FILE,
                source_name="sample",
            )
        ],
    )

    with pytest.raises(IngestionValidationError, match="Unknown target_element_id"):
        validate_evidence_batch(batch)


def test_evidence_batch_validation_rejects_unknown_run_id() -> None:
    batch = NormalizedEvidenceBatch(
        states=[
            NormalizedEvidenceStateRecord(
                id="state-a", source_type=SourceType.FILE, source_name="sample"
            )
        ],
        elements=[NormalizedEvidenceElementRecord(id="el-1", state_id="state-a")],
        actions=[
            NormalizedActionRecord(
                id="action-1",
                kind=ActionKind.CLICK,
                source_state_id="state-a",
                target_element_id="el-1",
            )
        ],
        transitions=[
            NormalizedTransitionRecord(
                id="transition-1",
                from_state_id="state-a",
                action_id="action-1",
                run_id="missing-run",
            )
        ],
    )

    with pytest.raises(IngestionValidationError, match="Unknown run_id for transition"):
        validate_evidence_batch(batch)


def test_evidence_batch_validation_rejects_duplicate_action_transition_and_observation_ids() -> (
    None
):
    batch = NormalizedEvidenceBatch(
        states=[
            NormalizedEvidenceStateRecord(
                id="state-a", source_type=SourceType.FILE, source_name="sample"
            )
        ],
        actions=[
            NormalizedActionRecord(id="action-1", kind=ActionKind.CLICK),
            NormalizedActionRecord(id="action-1", kind=ActionKind.CLICK),
        ],
        transitions=[
            NormalizedTransitionRecord(
                id="transition-1", from_state_id="state-a", action_id="action-1"
            ),
            NormalizedTransitionRecord(
                id="transition-1", from_state_id="state-a", action_id="action-1"
            ),
        ],
        runs=[
            NormalizedExecutionRunRecord(
                id="run-1",
                tool_name="TESTAR",
                status=ExecutionRunStatus.COMPLETED,
                source_type=SourceType.FILE,
                source_name="sample",
            )
        ],
        observations=[
            NormalizedObservationRecord(
                id="obs-1",
                run_id="run-1",
                kind=ObservationKind.MESSAGE,
                text="Message",
            ),
            NormalizedObservationRecord(
                id="obs-1",
                run_id="run-1",
                kind=ObservationKind.MESSAGE,
                text="Message",
            ),
        ],
    )

    with pytest.raises(IngestionValidationError, match="Duplicate action ids"):
        validate_evidence_batch(batch)


def test_requirement_batch_validation_rejects_flow_entry_fragment_from_other_requirement() -> None:
    batch = NormalizedRequirementBatch(
        requirements=[
            NormalizedRequirementRecord(
                id="req-1",
                kind=RequirementKind.USE_CASE,
                title="Sample 1",
                source_type=SourceType.FILE,
                source_name="sample",
            ),
            NormalizedRequirementRecord(
                id="req-2",
                kind=RequirementKind.USE_CASE,
                title="Sample 2",
                source_type=SourceType.FILE,
                source_name="sample",
            ),
        ],
        fragments=[
            NormalizedRequirementFragmentRecord(
                id="frag-2",
                requirement_id="req-2",
                kind=RequirementFragmentKind.MAIN_STEP,
                text="Other requirement step",
                order_index=1,
            )
        ],
        flows=[
            NormalizedRequirementFlowRecord(
                id="flow-1",
                requirement_id="req-1",
                name="Main flow",
                flow_kind=RequirementFlowKind.MAIN,
                entry_fragment_id="frag-2",
            )
        ],
    )

    with pytest.raises(IngestionValidationError, match="belongs to a different requirement"):
        validate_requirement_batch(batch)


def test_requirement_batch_validation_rejects_flow_edge_fragment_from_other_requirement() -> None:
    batch = NormalizedRequirementBatch(
        requirements=[
            NormalizedRequirementRecord(
                id="req-1",
                kind=RequirementKind.USE_CASE,
                title="Sample 1",
                source_type=SourceType.FILE,
                source_name="sample",
            ),
            NormalizedRequirementRecord(
                id="req-2",
                kind=RequirementKind.USE_CASE,
                title="Sample 2",
                source_type=SourceType.FILE,
                source_name="sample",
            ),
        ],
        fragments=[
            NormalizedRequirementFragmentRecord(
                id="frag-1",
                requirement_id="req-1",
                kind=RequirementFragmentKind.MAIN_STEP,
                text="Step 1",
                order_index=1,
            ),
            NormalizedRequirementFragmentRecord(
                id="frag-2",
                requirement_id="req-2",
                kind=RequirementFragmentKind.MAIN_STEP,
                text="Step 2",
                order_index=1,
            ),
        ],
        flow_edges=[
            NormalizedRequirementFlowEdgeRecord(
                id="edge-1",
                requirement_id="req-1",
                from_fragment_id="frag-1",
                to_fragment_id="frag-2",
                edge_kind=RequirementFlowEdgeKind.NEXT,
            )
        ],
    )

    with pytest.raises(IngestionValidationError, match="belongs to a different requirement"):
        validate_requirement_batch(batch)


def test_requirement_batch_validation_rejects_flow_edge_from_fragment_from_other_requirement() -> (
    None
):
    batch = NormalizedRequirementBatch(
        requirements=[
            NormalizedRequirementRecord(
                id="req-1",
                kind=RequirementKind.USE_CASE,
                title="Sample 1",
                source_type=SourceType.FILE,
                source_name="sample",
            ),
            NormalizedRequirementRecord(
                id="req-2",
                kind=RequirementKind.USE_CASE,
                title="Sample 2",
                source_type=SourceType.FILE,
                source_name="sample",
            ),
        ],
        fragments=[
            NormalizedRequirementFragmentRecord(
                id="frag-1",
                requirement_id="req-2",
                kind=RequirementFragmentKind.MAIN_STEP,
                text="Step 1",
                order_index=1,
            ),
            NormalizedRequirementFragmentRecord(
                id="frag-2",
                requirement_id="req-1",
                kind=RequirementFragmentKind.MAIN_STEP,
                text="Step 2",
                order_index=1,
            ),
        ],
        flow_edges=[
            NormalizedRequirementFlowEdgeRecord(
                id="edge-1",
                requirement_id="req-1",
                from_fragment_id="frag-1",
                to_fragment_id="frag-2",
                edge_kind=RequirementFlowEdgeKind.NEXT,
            )
        ],
    )

    with pytest.raises(IngestionValidationError, match="belongs to a different requirement"):
        validate_requirement_batch(batch)


@pytest.mark.parametrize(
    ("batch", "error_message"),
    [
        pytest.param(
            _valid_requirement_batch().model_copy(
                update={
                    "requirements": [
                        _valid_requirement_batch().requirements[0].model_copy(
                            update={"document_id": "missing-doc"}
                        )
                    ]
                }
            ),
            "Unknown document_id",
            id="requirement-document-missing",
        ),
        pytest.param(
            _valid_requirement_batch().model_copy(
                update={
                    "flows": [
                        _valid_requirement_batch().flows[0].model_copy(
                            update={"requirement_id": "missing-req"}
                        )
                    ]
                }
            ),
            "Unknown requirement_id for flow",
            id="flow-requirement-missing",
        ),
        pytest.param(
            _valid_requirement_batch().model_copy(
                update={
                    "flows": [
                        _valid_requirement_batch().flows[0].model_copy(
                            update={"entry_fragment_id": "missing-frag"}
                        )
                    ]
                }
            ),
            "Unknown entry_fragment_id",
            id="flow-entry-fragment-missing",
        ),
        pytest.param(
            _valid_requirement_batch().model_copy(
                update={
                    "flow_edges": [
                        _valid_requirement_batch().flow_edges[0].model_copy(
                            update={"requirement_id": "missing-req"}
                        )
                    ]
                }
            ),
            "Unknown requirement_id for flow edge",
            id="edge-requirement-missing",
        ),
        pytest.param(
            _valid_requirement_batch().model_copy(
                update={
                    "flow_edges": [
                        _valid_requirement_batch().flow_edges[0].model_copy(
                            update={"from_fragment_id": "missing-frag"}
                        )
                    ]
                }
            ),
            "Unknown from_fragment_id",
            id="edge-from-fragment-missing",
        ),
        pytest.param(
            _valid_requirement_batch().model_copy(
                update={
                    "flow_edges": [
                        _valid_requirement_batch().flow_edges[0].model_copy(
                            update={"to_fragment_id": "missing-frag"}
                        )
                    ]
                }
            ),
            "Unknown to_fragment_id",
            id="edge-to-fragment-missing",
        ),
    ],
)
def test_requirement_batch_validation_rejects_unknown_references(
    batch: NormalizedRequirementBatch,
    error_message: str,
) -> None:
    with pytest.raises(IngestionValidationError, match=error_message):
        validate_requirement_batch(batch)


@pytest.mark.parametrize(
    ("batch", "error_message"),
    [
        pytest.param(
            _valid_evidence_batch().model_copy(
                update={
                    "elements": [
                        _valid_evidence_batch().elements[0].model_copy(
                            update={"state_id": "missing-state"}
                        )
                    ]
                }
            ),
            "Unknown state_id for element",
            id="element-state-missing",
        ),
        pytest.param(
            _valid_evidence_batch().model_copy(
                update={
                    "actions": [
                        _valid_evidence_batch().actions[0].model_copy(
                            update={"source_state_id": "missing-state"}
                        )
                    ]
                }
            ),
            "Unknown source_state_id",
            id="action-source-state-missing",
        ),
        pytest.param(
            _valid_evidence_batch().model_copy(
                update={
                    "transitions": [
                        _valid_evidence_batch().transitions[0].model_copy(
                            update={"from_state_id": "missing-state"}
                        )
                    ]
                }
            ),
            "Unknown from_state_id",
            id="transition-from-state-missing",
        ),
        pytest.param(
            _valid_evidence_batch().model_copy(
                update={
                    "transitions": [
                        _valid_evidence_batch().transitions[0].model_copy(
                            update={"action_id": "missing-action"}
                        )
                    ]
                }
            ),
            "Unknown action_id",
            id="transition-action-missing",
        ),
        pytest.param(
            _valid_evidence_batch().model_copy(
                update={
                    "transitions": [
                        _valid_evidence_batch().transitions[0].model_copy(
                            update={"to_state_id": "missing-state"}
                        )
                    ]
                }
            ),
            "Unknown to_state_id",
            id="transition-to-state-missing",
        ),
        pytest.param(
            _valid_evidence_batch().model_copy(
                update={
                    "observations": [
                        _valid_evidence_batch().observations[0].model_copy(
                            update={"run_id": "missing-run"}
                        )
                    ]
                }
            ),
            "Unknown run_id for observation",
            id="observation-run-missing",
        ),
        pytest.param(
            _valid_evidence_batch().model_copy(
                update={
                    "observations": [
                        _valid_evidence_batch().observations[0].model_copy(
                            update={"state_id": "missing-state"}
                        )
                    ]
                }
            ),
            "Unknown state_id for observation",
            id="observation-state-missing",
        ),
        pytest.param(
            _valid_evidence_batch().model_copy(
                update={
                    "observations": [
                        _valid_evidence_batch().observations[0].model_copy(
                            update={"transition_id": "missing-transition"}
                        )
                    ]
                }
            ),
            "Unknown transition_id for observation",
            id="observation-transition-missing",
        ),
        pytest.param(
            _valid_evidence_batch().model_copy(
                update={
                    "attachments": [
                        _valid_evidence_batch().attachments[0].model_copy(
                            update={"run_id": "missing-run"}
                        )
                    ]
                }
            ),
            "Unknown run_id for attachment",
            id="attachment-run-missing",
        ),
        pytest.param(
            _valid_evidence_batch().model_copy(
                update={
                    "attachments": [
                        _valid_evidence_batch().attachments[0].model_copy(
                            update={"state_id": "missing-state"}
                        )
                    ]
                }
            ),
            "Unknown state_id for attachment",
            id="attachment-state-missing",
        ),
        pytest.param(
            _valid_evidence_batch().model_copy(
                update={
                    "attachments": [
                        _valid_evidence_batch().attachments[0].model_copy(
                            update={"observation_id": "missing-observation"}
                        )
                    ]
                }
            ),
            "Unknown observation_id for attachment",
            id="attachment-observation-missing",
        ),
        pytest.param(
            _valid_evidence_batch().model_copy(
                update={
                    "artifacts": [
                        _valid_evidence_batch().artifacts[0].model_copy(
                            update={"run_id": "missing-run"}
                        )
                    ]
                }
            ),
            "Unknown run_id for artifact",
            id="artifact-run-missing",
        ),
    ],
)
def test_evidence_batch_validation_rejects_unknown_references(
    batch: NormalizedEvidenceBatch,
    error_message: str,
) -> None:
    with pytest.raises(IngestionValidationError, match=error_message):
        validate_evidence_batch(batch)
