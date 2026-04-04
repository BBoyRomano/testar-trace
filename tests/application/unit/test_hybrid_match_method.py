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

_RANK = {
    CoverageVerdict.FULL: 5,
    CoverageVerdict.MAIN_ONLY: 4,
    CoverageVerdict.ALT_ONLY: 4,
    CoverageVerdict.PARTIAL: 3,
    CoverageVerdict.UNCERTAIN: 2,
    CoverageVerdict.NONE: 1,
}


def _build_request() -> TraceabilityRequest:
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
                    text="The system shows the home page.",
                    order_index=0,
                ),
                RequirementFragment(
                    id="REQ-1-frag-2",
                    requirement_id="REQ-1",
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
                ExecutionRun(id="run-1", tool_name="TESTAR", status=ExecutionRunStatus.COMPLETED),
            ],
            "states": [
                ApplicationState(id="state-home", title="Home"),
                ApplicationState(id="state-login", title="Login"),
                ApplicationState(id="state-dashboard", title="Dashboard"),
            ],
            "elements": [
                UIElement(id="el-login", state_id="state-home", tag_name="button", text="Login"),
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
                    id="act-submit",
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
                    run_id="run-1",
                    order_index=0,
                ),
                Transition(
                    id="tr-dashboard",
                    from_state_id="state-login",
                    action_id="act-submit",
                    to_state_id="state-dashboard",
                    run_id="run-1",
                    order_index=1,
                ),
            ],
            "observations": [],
            "attachments": [],
        }
    )

    return TraceabilityRequest(
        method_name="hybrid_match",
        requirements=requirements,
        evidence=evidence,
    )


def test_hybrid_match_is_available_and_executable() -> None:
    request = _build_request()
    result = build_default_traceability_service().execute(request)

    assert result.run.method_name == "hybrid_match"
    assert result.summary.requirement_count == 1


def test_hybrid_match_per_requirement_verdict_not_weaker_than_component_methods() -> None:
    service = build_default_traceability_service()
    base_request = _build_request()
    flow_result = service.execute(base_request.model_copy(update={"method_name": "flow_match"}))
    candidate_result = service.execute(
        base_request.model_copy(update={"method_name": "candidate_match"})
    )
    hybrid_result = service.execute(base_request)

    flow_verdict = flow_result.requirement_results[0].coverage.status
    candidate_verdict = candidate_result.requirement_results[0].coverage.status
    hybrid_verdict = hybrid_result.requirement_results[0].coverage.status

    assert _RANK[hybrid_verdict] >= max(_RANK[flow_verdict], _RANK[candidate_verdict])
