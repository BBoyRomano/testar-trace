from reqtrace.domain.evidence.enums import (
    ActionKind,
    EvidenceArtifactKind,
    EvidenceTool,
    ExecutionRunStatus,
    ObservationKind,
    StateModelLayer,
)
from reqtrace.ingestion.evidence.adapter import EvidenceAdapter
from reqtrace.ingestion.evidence.models import (
    ParsedEvidenceAction,
    ParsedEvidenceElement,
    ParsedEvidenceObservation,
    ParsedEvidenceRun,
    ParsedEvidenceSource,
    ParsedEvidenceState,
    ParsedEvidenceTransition,
)


def test_evidence_adapter_normalizes_parsed_evidence_source() -> None:
    parsed = ParsedEvidenceSource(
        run=ParsedEvidenceRun(
            id="run-1",
            tool_name="TESTAR",
            status=ExecutionRunStatus.COMPLETED,
            native_id="native-run-1",
        ),
        states=[
            ParsedEvidenceState(id="state-a", title="Sample page", native_id="native-state-a"),
            ParsedEvidenceState(id="state-b", title="Next page"),
        ],
        elements=[ParsedEvidenceElement(id="el-1", state_id="state-a", text="Continue")],
        actions=[
            ParsedEvidenceAction(
                id="act-1",
                kind=ActionKind.CLICK,
                source_state_id="state-a",
                target_element_id="el-1",
            )
        ],
        transitions=[
            ParsedEvidenceTransition(
                id="tr-1",
                from_state_id="state-a",
                action_id="act-1",
                to_state_id="state-b",
                run_id="run-1",
            )
        ],
        observations=[
            ParsedEvidenceObservation(
                id="obs-1",
                run_id="run-1",
                kind=ObservationKind.MESSAGE,
                text="The next page is shown",
                state_id="state-b",
                transition_id="tr-1",
            )
        ],
        source_name="testar",
        path_or_uri="suts/tbuis/evidence/runs/demo/model/model.json",
    )

    adapter = EvidenceAdapter()
    batch = adapter.ingest(parsed)

    assert len(batch.states) == 2
    assert len(batch.elements) == 1
    assert len(batch.actions) == 1
    assert len(batch.transitions) == 1
    assert len(batch.runs) == 1
    assert len(batch.observations) == 1
    assert batch.runs[0].native_id == "native-run-1"
    assert batch.states[0].native_id == "native-state-a"
    assert batch.actions[0].source_state_id == "state-a"
    assert batch.actions[0].target_element_id == "el-1"
    assert batch.transitions[0].action_id == "act-1"
    assert batch.transitions[0].to_state_id == "state-b"
    assert batch.observations[0].state_id == "state-b"
    assert batch.observations[0].transition_id == "tr-1"
    assert batch.runs[0].tool == EvidenceTool.TESTAR
    assert StateModelLayer.CONCRETE in batch.runs[0].state_model_layers
    assert len(batch.artifacts) == 1
    assert batch.artifacts[0].kind == EvidenceArtifactKind.STATE_MODEL_JSON
