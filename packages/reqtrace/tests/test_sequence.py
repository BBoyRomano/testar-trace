from reqtrace import analyze_traceability
from reqtrace.methods.sequence import trace_with_sequence
from reqtrace.models.evidence import (
    EvidenceSet,
    ExecutionAction,
    ExecutionElement,
    ExecutionState,
    ExecutionTransition,
)
from reqtrace.models.requirements import (
    RequirementArtifact,
    RequirementFragment,
    RequirementScenario,
    RequirementSet,
)
from reqtrace.models.traceability import (
    CoverageStatus,
    TraceOccurrenceStatus,
)
from reqtrace.progress import TraceContext
from reqtrace.registry import available_trace_methods


def test_sequence_method_is_registered() -> None:
    assert "sequence" in available_trace_methods()


def test_sequence_method_finds_full_main_flow() -> None:
    requirements = RequirementSet(
        requirements=(RequirementArtifact(id="req-login", title="Account access"),),
        fragments=(
            RequirementFragment(
                id="req-login-pre",
                requirement_id="req-login",
                kind="precondition",
                order_index=0,
                text="Login page is open",
            ),
            RequirementFragment(
                id="req-login-main-1",
                requirement_id="req-login",
                kind="main_step",
                order_index=1,
                text="Enter valid credentials",
            ),
            RequirementFragment(
                id="req-login-main-2",
                requirement_id="req-login",
                kind="main_step",
                order_index=2,
                text="Submit login form",
            ),
            RequirementFragment(
                id="req-login-post",
                requirement_id="req-login",
                kind="postcondition",
                order_index=3,
                text="Dashboard is shown",
            ),
        ),
    )
    evidence = _login_evidence()

    result = analyze_traceability(
        requirements,
        evidence,
        method="sequence",
        options={"min_score": 0.1},
    )

    assert result.summary.covered_requirements == 1
    assert result.summary.uncovered_requirements == 0
    assert result.coverage[0].status is CoverageStatus.COVERED
    assert result.occurrences[0].status is TraceOccurrenceStatus.FULL
    assert len(result.occurrences[0].alignment_ids) == 4
    assert len(result.fragment_alignments) >= 4
    assert {alignment.fragment_id for alignment in result.fragment_alignments[:4]} == {
        "req-login-pre",
        "req-login-main-1",
        "req-login-main-2",
        "req-login-post",
    }


def test_sequence_method_returns_partial_sequences() -> None:
    requirements = RequirementSet(
        requirements=(RequirementArtifact(id="req-search", title="Catalog search"),),
        fragments=(
            RequirementFragment(
                id="req-search-1",
                requirement_id="req-search",
                kind="main_step",
                order_index=0,
                text="Open catalog page",
            ),
            RequirementFragment(
                id="req-search-2",
                requirement_id="req-search",
                kind="main_step",
                order_index=1,
                text="Filter products by price",
            ),
        ),
    )
    evidence = EvidenceSet(
        id="evidence-catalog",
        title="Catalog evidence",
        states=(ExecutionState(id="state-catalog", title="Catalog page"),),
        actions=(ExecutionAction(id="action-open", description="Open catalog page"),),
        transitions=(
            ExecutionTransition(
                id="transition-open",
                from_state_id="state-catalog",
                action_id="action-open",
                order_index=0,
            ),
        ),
    )

    result = trace_with_sequence(requirements, evidence, TraceContext())

    assert result.summary.partially_covered_requirements == 1
    assert result.coverage[0].status is CoverageStatus.PARTIALLY_COVERED
    assert result.occurrences[0].status is TraceOccurrenceStatus.PARTIAL
    assert result.occurrences[0].metadata["matched_fragment_count"] == 1
    assert result.occurrences[0].metadata["total_fragment_count"] == 2


def test_sequence_method_deduplicates_sequences_from_multiple_anchors() -> None:
    requirements = RequirementSet(
        requirements=(RequirementArtifact(id="req-order", title="Checkout"),),
        fragments=(
            RequirementFragment(
                id="req-order-1",
                requirement_id="req-order",
                kind="main_step",
                order_index=0,
                text="Open checkout page",
            ),
            RequirementFragment(
                id="req-order-2",
                requirement_id="req-order",
                kind="main_step",
                order_index=1,
                text="Confirm checkout order",
            ),
        ),
    )
    evidence = EvidenceSet(
        id="evidence-order",
        title="Checkout evidence",
        states=(
            ExecutionState(id="state-cart", title="Cart"),
            ExecutionState(id="state-checkout", title="Checkout page"),
            ExecutionState(id="state-confirm", title="Order confirmation"),
        ),
        actions=(
            ExecutionAction(id="action-open", description="Open checkout page"),
            ExecutionAction(id="action-confirm", description="Confirm checkout order"),
        ),
        transitions=(
            ExecutionTransition(
                id="transition-open",
                from_state_id="state-cart",
                action_id="action-open",
                to_state_id="state-checkout",
                order_index=0,
            ),
            ExecutionTransition(
                id="transition-confirm",
                from_state_id="state-checkout",
                action_id="action-confirm",
                to_state_id="state-confirm",
                order_index=1,
            ),
        ),
    )

    result = trace_with_sequence(requirements, evidence, TraceContext())

    signatures = [occurrence.metadata["signature"] for occurrence in result.occurrences]
    assert len(signatures) == len(set(signatures))
    assert ("main", "main", "", "transition-open", "transition-confirm") in signatures


def test_sequence_method_finds_alternative_flow_with_conditions() -> None:
    requirements = RequirementSet(
        requirements=(RequirementArtifact(id="req-login", title="Account access"),),
        fragments=(
            RequirementFragment(
                id="req-login-pre",
                requirement_id="req-login",
                kind="precondition",
                order_index=0,
                text="Login page is open",
            ),
            RequirementFragment(
                id="req-login-alt",
                requirement_id="req-login",
                kind="alternative_step",
                branch_id="invalid-password",
                order_index=1,
                text="Submit invalid password",
            ),
            RequirementFragment(
                id="req-login-post",
                requirement_id="req-login",
                kind="postcondition",
                order_index=2,
                text="Error message is shown",
            ),
        ),
    )
    evidence = EvidenceSet(
        id="evidence-login-alt",
        title="Login invalid password evidence",
        states=(
            ExecutionState(id="state-login", title="Login page"),
            ExecutionState(id="state-error", title="Error message shown"),
        ),
        elements=(
            ExecutionElement(
                id="element-error",
                state_id="state-error",
                text="Invalid password error message",
            ),
        ),
        actions=(
            ExecutionAction(
                id="action-invalid",
                description="Submit invalid password",
            ),
        ),
        transitions=(
            ExecutionTransition(
                id="transition-invalid",
                from_state_id="state-login",
                action_id="action-invalid",
                to_state_id="state-error",
                order_index=0,
            ),
        ),
    )

    result = trace_with_sequence(requirements, evidence, TraceContext())

    assert result.summary.covered_requirements == 1
    assert result.occurrences[0].metadata["variant"] == "alternative"
    assert result.occurrences[0].metadata["branch_id"] == "invalid-password"
    assert result.occurrences[0].status is TraceOccurrenceStatus.FULL


def test_sequence_coverage_reports_each_scenario() -> None:
    requirements = RequirementSet(
        requirements=(RequirementArtifact(id="req-login", title="Account access"),),
        fragments=(
            RequirementFragment(
                id="req-login-main",
                requirement_id="req-login",
                kind="main_step",
                order_index=0,
                text="Submit login form",
            ),
            RequirementFragment(
                id="req-login-alt",
                requirement_id="req-login",
                kind="alternative_step",
                branch_id="invalid-password",
                order_index=1,
                text="Approve wire transfer",
            ),
        ),
        scenarios=(
            RequirementScenario(
                id="req-login:scenario:main",
                requirement_id="req-login",
                title="Main flow",
                kind="main",
                fragment_ids=("req-login-main",),
                order_index=0,
            ),
            RequirementScenario(
                id="req-login:scenario:alt",
                requirement_id="req-login",
                title="Alternative flow",
                kind="alternative",
                fragment_ids=("req-login-alt",),
                order_index=1,
                metadata={"branch_id": "invalid-password"},
            ),
        ),
    )
    evidence = EvidenceSet(
        id="evidence-login",
        title="Login evidence",
        states=(ExecutionState(id="state-login", title="Login page"),),
        actions=(ExecutionAction(id="action-submit", description="Submit login form"),),
        transitions=(
            ExecutionTransition(
                id="transition-submit",
                from_state_id="state-login",
                action_id="action-submit",
                order_index=0,
            ),
        ),
    )

    result = trace_with_sequence(
        requirements,
        evidence,
        TraceContext(options={"min_score": 0.1}),
    )

    assert result.coverage[0].status is CoverageStatus.PARTIALLY_COVERED
    assert result.coverage[0].coverage_ratio == 0.5
    assert result.coverage[0].metadata["requirement_title"] == "Account access"
    assert result.summary.metadata["requirements_coverage_ratio"] == 0.5
    assert result.coverage[0].rationale == (
        "1/2 scenarios fully covered; 0 partially covered; 1 not covered."
    )
    scenario_coverage = result.coverage[0].metadata["scenario_coverage"]
    assert scenario_coverage == (
        {
            "scenario_id": "req-login:scenario:main",
            "kind": "main",
            "branch_id": None,
            "status": "covered",
            "coverage_ratio": 1.0,
            "best_score": 0.4042,
            "best_occurrence_id": "req-login:sequence:1",
            "matched_fragment_count": 1,
            "total_fragment_count": 1,
            "sequence_count": 1,
        },
        {
            "scenario_id": "req-login:scenario:alt",
            "kind": "alternative",
            "branch_id": "invalid-password",
            "status": "not-covered",
            "coverage_ratio": 0.0,
            "best_score": None,
            "best_occurrence_id": None,
            "matched_fragment_count": 0,
            "total_fragment_count": 1,
            "sequence_count": 0,
        },
    )


def _login_evidence() -> EvidenceSet:
    return EvidenceSet(
        id="evidence-login",
        title="Login evidence",
        states=(
            ExecutionState(id="state-login", title="Login page"),
            ExecutionState(id="state-credentials", title="Credentials entered"),
            ExecutionState(id="state-dashboard", title="Dashboard shown"),
        ),
        elements=(
            ExecutionElement(
                id="element-username",
                state_id="state-login",
                text="Username",
            ),
            ExecutionElement(
                id="element-password",
                state_id="state-login",
                text="Password",
            ),
        ),
        actions=(
            ExecutionAction(
                id="action-enter-credentials",
                description="Enter valid credentials",
            ),
            ExecutionAction(
                id="action-submit-login",
                description="Submit login form",
            ),
        ),
        transitions=(
            ExecutionTransition(
                id="transition-enter-credentials",
                from_state_id="state-login",
                action_id="action-enter-credentials",
                to_state_id="state-credentials",
                order_index=0,
            ),
            ExecutionTransition(
                id="transition-submit-login",
                from_state_id="state-credentials",
                action_id="action-submit-login",
                to_state_id="state-dashboard",
                order_index=1,
            ),
        ),
    )
