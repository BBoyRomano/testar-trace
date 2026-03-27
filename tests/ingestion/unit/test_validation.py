import pytest

from reqtrace.domain.common.enums import SourceType
from reqtrace.domain.evidence.enums import ActionKind, ExecutionRunStatus, ObservationKind
from reqtrace.domain.requirements.enums import (
    RequirementFlowEdgeKind,
    RequirementFlowKind,
    RequirementFragmentKind,
    RequirementKind,
)
from reqtrace.ingestion.common.exceptions import IngestionValidationError
from reqtrace.ingestion.common.models import (
    NormalizedActionRecord,
    NormalizedEvidenceBatch,
    NormalizedEvidenceElementRecord,
    NormalizedEvidenceStateRecord,
    NormalizedExecutionRunRecord,
    NormalizedObservationRecord,
    NormalizedRequirementBatch,
    NormalizedRequirementFlowEdgeRecord,
    NormalizedRequirementFlowRecord,
    NormalizedRequirementFragmentRecord,
    NormalizedRequirementRecord,
    NormalizedTransitionRecord,
)
from reqtrace.ingestion.common.validation import validate_evidence_batch, validate_requirement_batch


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
            NormalizedEvidenceStateRecord(id="state-a", source_type=SourceType.FILE, source_name="sample"),
            NormalizedEvidenceStateRecord(id="state-a", source_type=SourceType.FILE, source_name="sample"),
        ]
    )

    with pytest.raises(IngestionValidationError, match="Duplicate state ids"):
        validate_evidence_batch(batch)


def test_evidence_batch_validation_rejects_unknown_target_element_id() -> None:
    batch = NormalizedEvidenceBatch(
        states=[
            NormalizedEvidenceStateRecord(id="state-a", source_type=SourceType.FILE, source_name="sample")
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
            NormalizedEvidenceStateRecord(id="state-a", source_type=SourceType.FILE, source_name="sample")
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


def test_evidence_batch_validation_rejects_duplicate_action_transition_and_observation_ids() -> None:
    batch = NormalizedEvidenceBatch(
        states=[
            NormalizedEvidenceStateRecord(id="state-a", source_type=SourceType.FILE, source_name="sample")
        ],
        actions=[
            NormalizedActionRecord(id="action-1", kind=ActionKind.CLICK),
            NormalizedActionRecord(id="action-1", kind=ActionKind.CLICK),
        ],
        transitions=[
            NormalizedTransitionRecord(id="transition-1", from_state_id="state-a", action_id="action-1"),
            NormalizedTransitionRecord(id="transition-1", from_state_id="state-a", action_id="action-1"),
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
