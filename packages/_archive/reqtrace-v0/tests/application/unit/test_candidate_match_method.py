from __future__ import annotations

from reqtrace.application.results import EvidenceSnapshot, RequirementSnapshot, TraceabilityRequest
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


def test_candidate_match_can_link_simple_login_step_to_evidence() -> None:
    """Candidate matching should produce at least one trace link for an obvious UI step."""

    requirements = RequirementSnapshot.from_mapping(
        {
            "requirements": [
                RequirementArtifact(id="REQ-1", kind=RequirementKind.USE_CASE, title="Login"),
            ],
            "fragments": [
                RequirementFragment(
                    id="REQ-1-frag-1",
                    requirement_id="REQ-1",
                    kind=RequirementFragmentKind.MAIN_STEP,
                    text="The user clicks the Login button.",
                    order_index=0,
                ),
                RequirementFragment(
                    id="REQ-1-frag-2",
                    requirement_id="REQ-1",
                    kind=RequirementFragmentKind.POSTCONDITION,
                    text="The system shows the protected page.",
                    order_index=1,
                ),
            ],
            "flows": [],
            "flow_edges": [],
        }
    )

    evidence = EvidenceSnapshot.from_mapping(
        {
            "states": [
                ApplicationState(id="state-1", title="Login page", url="/login"),
                ApplicationState(id="state-2", title="Protected page", url="/protected"),
            ],
            "elements": [
                UIElement(
                    id="el-login",
                    state_id="state-1",
                    tag_name="button",
                    role="button",
                    text="Login",
                    title="Login",
                ),
            ],
            "actions": [
                Action(
                    id="act-login",
                    kind=ActionKind.CLICK,
                    description="Click Login",
                    source_state_id="state-1",
                    target_element_id="el-login",
                ),
            ],
            "transitions": [
                Transition(
                    id="tr-1",
                    from_state_id="state-1",
                    action_id="act-login",
                    to_state_id="state-2",
                    order_index=0,
                )
            ],
            "runs": [
                ExecutionRun(id="run-1", tool_name="TESTAR", status=ExecutionRunStatus.COMPLETED),
            ],
            "observations": [],
            "attachments": [],
        }
    )

    result = build_default_traceability_service(include_experimental_methods=True).execute(
        TraceabilityRequest(
            method_name="candidate_match", requirements=requirements, evidence=evidence
        )
    )

    assert result.summary.trace_link_count >= 1
    assert result.summary.trace_evidence_count >= 1
    assert result.summary.uncovered_requirement_count < result.summary.requirement_count


def test_candidate_match_prefers_operational_evidence_over_generic_banner_text() -> None:
    """Candidate matching should prefer operational UI evidence over generic banner text."""

    requirements = RequirementSnapshot.from_mapping(
        {
            "requirements": [
                RequirementArtifact(
                    id="REQ-OP-1", kind=RequirementKind.USE_CASE, title="Restore database"
                ),
            ],
            "fragments": [
                RequirementFragment(
                    id="REQ-OP-1-frag-1",
                    requirement_id="REQ-OP-1",
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
                ExecutionRun(id="run-1", tool_name="TESTAR", status=ExecutionRunStatus.COMPLETED)
            ],
            "states": [
                ApplicationState(id="state-home", title="Home", url="/"),
                ApplicationState(id="state-restore", title="Restore DB", url="/restore"),
            ],
            "elements": [
                UIElement(
                    id="el-banner",
                    state_id="state-home",
                    tag_name="h1",
                    text="University information system",
                ),
                UIElement(
                    id="el-restore",
                    state_id="state-home",
                    tag_name="a",
                    role="link",
                    text="Restore DB",
                    href="/restore",
                ),
            ],
            "actions": [
                Action(
                    id="act-restore",
                    kind=ActionKind.NAVIGATE,
                    description="Click Restore DB",
                    source_state_id="state-home",
                    target_element_id="el-restore",
                )
            ],
            "transitions": [
                Transition(
                    id="tr-restore",
                    from_state_id="state-home",
                    action_id="act-restore",
                    to_state_id="state-restore",
                    order_index=0,
                )
            ],
            "observations": [],
            "attachments": [],
        }
    )

    result = build_default_traceability_service(include_experimental_methods=True).execute(
        TraceabilityRequest(
            method_name="candidate_match", requirements=requirements, evidence=evidence
        )
    )

    assert result.summary.trace_link_count >= 1
    assert any(
        link.evidence_target_id in {"el-restore", "act-restore", "tr-restore", "state-restore"}
        for link in result.requirement_results[0].trace_links
    )
    assert not any(
        (ev.text_excerpt or "").lower().startswith("university information system")
        for ev in result.requirement_results[0].trace_evidence
    )


def test_candidate_match_respects_selected_evidence_run_ids() -> None:
    requirements = RequirementSnapshot.from_mapping(
        {
            "requirements": [
                RequirementArtifact(
                    id="REQ-RESTORE-1", kind=RequirementKind.USE_CASE, title="Restore DB"
                ),
            ],
            "fragments": [
                RequirementFragment(
                    id="REQ-RESTORE-1-frag-1",
                    requirement_id="REQ-RESTORE-1",
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
                ExecutionRun(id="run-2", tool_name="TESTAR", status=ExecutionRunStatus.COMPLETED),
            ],
            "states": [
                ApplicationState(id="state-home", title="Home"),
                ApplicationState(id="state-help", title="Help"),
                ApplicationState(id="state-restore", title="Restore Database"),
            ],
            "elements": [
                UIElement(id="el-help", state_id="state-home", text="Help", tag_name="a"),
                UIElement(
                    id="el-restore", state_id="state-home", text="Restore DB", tag_name="button"
                ),
            ],
            "actions": [
                Action(
                    id="act-help",
                    kind=ActionKind.NAVIGATE,
                    description="Open help",
                    source_state_id="state-home",
                    target_element_id="el-help",
                ),
                Action(
                    id="act-restore",
                    kind=ActionKind.CLICK,
                    description="Restore database",
                    source_state_id="state-home",
                    target_element_id="el-restore",
                ),
            ],
            "transitions": [
                Transition(
                    id="tr-help",
                    from_state_id="state-home",
                    action_id="act-help",
                    to_state_id="state-help",
                    run_id="run-1",
                    order_index=0,
                ),
                Transition(
                    id="tr-restore",
                    from_state_id="state-home",
                    action_id="act-restore",
                    to_state_id="state-restore",
                    run_id="run-2",
                    order_index=1,
                ),
            ],
            "observations": [],
            "attachments": [],
        }
    )

    service = build_default_traceability_service(include_experimental_methods=True)
    run1_result = service.execute(
        TraceabilityRequest(
            method_name="candidate_match",
            requirements=requirements,
            evidence=evidence,
            selected_evidence_run_ids=["run-1"],
        )
    )
    run2_result = service.execute(
        TraceabilityRequest(
            method_name="candidate_match",
            requirements=requirements,
            evidence=evidence,
            selected_evidence_run_ids=["run-2"],
        )
    )

    assert run1_result.summary.trace_link_count == 0
    assert run1_result.summary.uncovered_requirement_count == 1
    assert run2_result.summary.trace_link_count >= 1
