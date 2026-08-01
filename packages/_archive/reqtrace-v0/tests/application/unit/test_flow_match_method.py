from __future__ import annotations

from reqtrace.application.results import (
    CoverageVerdict,
    EvidenceSnapshot,
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


def test_flow_match_finds_ordered_main_flow_with_intermediate_noise() -> None:
    requirements = RequirementSnapshot.from_mapping(
        {
            "requirements": [
                RequirementArtifact(id="REQ-LOGIN", kind=RequirementKind.USE_CASE, title="Login"),
            ],
            "fragments": [
                RequirementFragment(
                    id="REQ-LOGIN-frag-1",
                    requirement_id="REQ-LOGIN",
                    kind=RequirementFragmentKind.MAIN_STEP,
                    text="The system shows the home page.",
                    order_index=0,
                ),
                RequirementFragment(
                    id="REQ-LOGIN-frag-2",
                    requirement_id="REQ-LOGIN",
                    kind=RequirementFragmentKind.MAIN_STEP,
                    text="The system shows the dashboard.",
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
                ApplicationState(id="state-login", title="Login"),
                ApplicationState(id="state-help", title="Help"),
                ApplicationState(id="state-dashboard", title="Dashboard"),
            ],
            "elements": [
                UIElement(id="el-login", state_id="state-home", tag_name="button", text="Login"),
                UIElement(id="el-help", state_id="state-login", tag_name="a", text="Help"),
            ],
            "actions": [
                Action(
                    id="act-login",
                    kind=ActionKind.CLICK,
                    description="Click Login",
                    source_state_id="state-home",
                    target_element_id="el-login",
                ),
                Action(
                    id="act-help",
                    kind=ActionKind.NAVIGATE,
                    description="Open Help",
                    source_state_id="state-login",
                    target_element_id="el-help",
                ),
                Action(
                    id="act-back",
                    kind=ActionKind.NAVIGATE,
                    description="Back to Login",
                    source_state_id="state-help",
                    target_element_id="el-login",
                ),
                Action(
                    id="act-submit-login",
                    kind=ActionKind.SUBMIT,
                    description="Submit Login",
                    source_state_id="state-login",
                    target_element_id="el-login",
                ),
            ],
            "transitions": [
                Transition(
                    id="tr-login",
                    from_state_id="state-home",
                    action_id="act-login",
                    to_state_id="state-login",
                    run_id="run-2",
                    order_index=0,
                ),
                Transition(
                    id="tr-help",
                    from_state_id="state-login",
                    action_id="act-help",
                    to_state_id="state-help",
                    run_id="run-2",
                    order_index=1,
                ),
                Transition(
                    id="tr-back",
                    from_state_id="state-help",
                    action_id="act-back",
                    to_state_id="state-login",
                    run_id="run-2",
                    order_index=2,
                ),
                Transition(
                    id="tr-dashboard",
                    from_state_id="state-login",
                    action_id="act-submit-login",
                    to_state_id="state-dashboard",
                    run_id="run-2",
                    order_index=3,
                ),
            ],
            "observations": [],
            "attachments": [],
        }
    )

    result = build_default_traceability_service(include_experimental_methods=True).execute(
        TraceabilityRequest(method_name="flow_match", requirements=requirements, evidence=evidence)
    )

    assert result.summary.trace_link_count >= 1
    assert result.requirement_results
    execution_instances = result.requirement_results[0].execution_instances
    assert execution_instances
    path = execution_instances[0].representative_trace.path
    assert any(item.match_role == "matched" for item in path)
    assert any(item.match_role == "intermediate" for item in path)


def test_flow_match_respects_selected_evidence_run_ids() -> None:
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
            method_name="flow_match",
            requirements=requirements,
            evidence=evidence,
            selected_evidence_run_ids=["run-1"],
        )
    )
    run2_result = service.execute(
        TraceabilityRequest(
            method_name="flow_match",
            requirements=requirements,
            evidence=evidence,
            selected_evidence_run_ids=["run-2"],
        )
    )

    assert run1_result.summary.trace_link_count == 0
    assert run2_result.summary.trace_link_count >= 1


def test_flow_match_alt_only_has_non_zero_artifact_coverage_ratio() -> None:
    requirements = RequirementSnapshot.from_mapping(
        {
            "requirements": [
                RequirementArtifact(id="REQ-ALT", kind=RequirementKind.USE_CASE, title="Alternate"),
            ],
            "fragments": [
                RequirementFragment(
                    id="REQ-ALT-main-1",
                    requirement_id="REQ-ALT",
                    kind=RequirementFragmentKind.MAIN_STEP,
                    text="The system shows the dashboard.",
                    order_index=0,
                ),
                RequirementFragment(
                    id="REQ-ALT-alt-1",
                    requirement_id="REQ-ALT",
                    kind=RequirementFragmentKind.ALTERNATIVE_STEP,
                    text="The system shows the help page.",
                    branch_id="alt-1",
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
                ExecutionRun(id="run-1", tool_name="TESTAR", status=ExecutionRunStatus.COMPLETED),
            ],
            "states": [
                ApplicationState(id="state-home", title="Home"),
                ApplicationState(id="state-help", title="Help"),
            ],
            "elements": [
                UIElement(id="el-help", state_id="state-home", text="Help", tag_name="a"),
            ],
            "actions": [
                Action(
                    id="act-help",
                    kind=ActionKind.NAVIGATE,
                    description="Open help",
                    source_state_id="state-home",
                    target_element_id="el-help",
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
            ],
            "observations": [],
            "attachments": [],
        }
    )

    result = build_default_traceability_service(include_experimental_methods=True).execute(
        TraceabilityRequest(method_name="flow_match", requirements=requirements, evidence=evidence)
    )

    item = result.requirement_results[0]
    assert item.coverage.status == CoverageVerdict.ALT_ONLY
    assert item.artifact_coverage is not None
    assert item.artifact_coverage.coverage_ratio is not None
    assert item.artifact_coverage.coverage_ratio > 0.0
