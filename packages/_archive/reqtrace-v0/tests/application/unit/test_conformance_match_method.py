from __future__ import annotations

from reqtrace.application.results import (
    CoverageVerdict,
    EvidenceSnapshot,
    FlowStatus,
    RequirementSnapshot,
    TraceabilityRequest,
)
from reqtrace.application.services.traceability_service import build_default_traceability_service
from reqtrace.domain.evidence.enums import ActionKind, ExecutionRunStatus
from reqtrace.domain.evidence.models import (
    Action,
    ApplicationState,
    ExecutionRun,
    Transition,
    UIElement,
)
from reqtrace.domain.requirements.enums import RequirementFragmentKind, RequirementKind
from reqtrace.domain.requirements.models import RequirementArtifact, RequirementFragment


def test_conformance_match_requires_operational_evidence_for_main_steps() -> None:
    requirements = RequirementSnapshot.from_mapping(
        {
            "requirements": [
                RequirementArtifact(
                    id="REQ-RESTORE", kind=RequirementKind.USE_CASE, title="Restore database"
                ),
            ],
            "fragments": [
                RequirementFragment(
                    id="REQ-RESTORE-frag-1",
                    requirement_id="REQ-RESTORE",
                    kind=RequirementFragmentKind.MAIN_STEP,
                    text="The user restores the database.",
                    order_index=0,
                ),
            ],
            "flows": [],
            "flow_edges": [],
        }
    )

    evidence = EvidenceSnapshot.from_mapping(
        {
            "runs": [
                ExecutionRun(id="run-1", tool_name="TESTAR", status=ExecutionRunStatus.COMPLETED),
            ],
            "states": [
                ApplicationState(id="state-home", title="Home"),
                ApplicationState(id="state-use-cases", title="Use-cases"),
            ],
            "elements": [
                UIElement(
                    id="el-doc-link",
                    state_id="state-home",
                    tag_name="a",
                    text="Application use-cases",
                ),
                UIElement(
                    id="el-doc-row",
                    state_id="state-use-cases",
                    tag_name="td",
                    text="Restoration of the database",
                ),
            ],
            "actions": [
                Action(
                    id="act-open-docs",
                    kind=ActionKind.NAVIGATE,
                    description="Open use-cases page",
                    source_state_id="state-home",
                    target_element_id="el-doc-link",
                ),
            ],
            "transitions": [
                Transition(
                    id="tr-docs",
                    from_state_id="state-home",
                    action_id="act-open-docs",
                    to_state_id="state-use-cases",
                    run_id="run-1",
                    order_index=0,
                ),
            ],
            "observations": [],
            "attachments": [],
        }
    )

    result = build_default_traceability_service(include_experimental_methods=True).execute(
        TraceabilityRequest(
            method_name="conformance_match",
            requirements=requirements,
            evidence=evidence,
        )
    )

    item = result.requirement_results[0]
    assert item.execution_instances == []
    assert item.fragment_results[0].status == FlowStatus.NOT_COVERED
    assert item.coverage.status == CoverageVerdict.NONE


def test_conformance_match_finds_ordered_operational_sequence() -> None:
    requirements = RequirementSnapshot.from_mapping(
        {
            "requirements": [
                RequirementArtifact(id="REQ-SEQ", kind=RequirementKind.USE_CASE, title="Restore"),
            ],
            "fragments": [
                RequirementFragment(
                    id="REQ-SEQ-frag-1",
                    requirement_id="REQ-SEQ",
                    kind=RequirementFragmentKind.MAIN_STEP,
                    text="Teacher opens the restore page.",
                    order_index=0,
                ),
                RequirementFragment(
                    id="REQ-SEQ-frag-2",
                    requirement_id="REQ-SEQ",
                    kind=RequirementFragmentKind.MAIN_STEP,
                    text="Teacher submits restore database.",
                    order_index=1,
                ),
            ],
            "flows": [],
            "flow_edges": [],
        }
    )

    evidence = EvidenceSnapshot.from_mapping(
        {
            "runs": [
                ExecutionRun(id="run-2", tool_name="TESTAR", status=ExecutionRunStatus.COMPLETED),
            ],
            "states": [
                ApplicationState(id="state-home", title="Home"),
                ApplicationState(id="state-restore", title="Restore DB"),
                ApplicationState(id="state-done", title="Restore Complete"),
            ],
            "elements": [
                UIElement(id="el-open", state_id="state-home", tag_name="a", text="Restore DB"),
                UIElement(
                    id="el-submit", state_id="state-restore", tag_name="button", text="Restore"
                ),
            ],
            "actions": [
                Action(
                    id="act-open",
                    kind=ActionKind.NAVIGATE,
                    description="Open restore page",
                    source_state_id="state-home",
                    target_element_id="el-open",
                ),
                Action(
                    id="act-submit",
                    kind=ActionKind.SUBMIT,
                    description="Submit restore database",
                    source_state_id="state-restore",
                    target_element_id="el-submit",
                ),
            ],
            "transitions": [
                Transition(
                    id="tr-open",
                    from_state_id="state-home",
                    action_id="act-open",
                    to_state_id="state-restore",
                    run_id="run-2",
                    order_index=0,
                ),
                Transition(
                    id="tr-submit",
                    from_state_id="state-restore",
                    action_id="act-submit",
                    to_state_id="state-done",
                    run_id="run-2",
                    order_index=1,
                ),
            ],
            "observations": [],
            "attachments": [],
        }
    )

    result = build_default_traceability_service(include_experimental_methods=True).execute(
        TraceabilityRequest(
            method_name="conformance_match",
            requirements=requirements,
            evidence=evidence,
        )
    )

    item = result.requirement_results[0]
    assert item.execution_instances
    assert item.coverage.status == CoverageVerdict.FULL
    assert item.main_flow_result is not None
    assert item.main_flow_result.status == FlowStatus.COVERED
