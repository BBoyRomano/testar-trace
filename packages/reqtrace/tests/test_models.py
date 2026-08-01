import pytest
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
    EvidenceRef,
    EvidenceRefKind,
    FragmentMatchKind,
    RequirementFragmentAlignment,
    TraceabilityResult,
    TraceabilitySummary,
)


def test_requirement_set_rejects_fragment_with_unknown_requirement() -> None:
    with pytest.raises(ValueError, match="reference a known requirement"):
        RequirementSet(
            fragments=(
                RequirementFragment(
                    id="fragment-1",
                    requirement_id="missing",
                    text="User logs in",
                ),
            ),
        )


def test_requirement_set_rejects_duplicate_fragment_ids() -> None:
    with pytest.raises(ValueError, match=r"Duplicate RequirementFragment\.id"):
        RequirementSet(
            requirements=(
                RequirementArtifact(
                    id="req-1",
                    title="Login",
                ),
            ),
            fragments=(
                RequirementFragment(
                    id="fragment-1",
                    requirement_id="req-1",
                    text="User enters credentials",
                ),
                RequirementFragment(
                    id="fragment-1",
                    requirement_id="req-1",
                    text="System logs in the user",
                ),
            ),
        )


def test_requirement_set_rejects_scenario_with_unknown_fragment() -> None:
    with pytest.raises(ValueError, match="reference known fragments"):
        RequirementSet(
            requirements=(
                RequirementArtifact(
                    id="req-1",
                    title="Login",
                ),
            ),
            scenarios=(
                RequirementScenario(
                    id="scenario-1",
                    requirement_id="req-1",
                    title="Main",
                    kind="main",
                    fragment_ids=("missing",),
                ),
            ),
        )


def test_requirement_scenario_rejects_blank_title() -> None:
    with pytest.raises(ValueError, match="title must not be blank"):
        RequirementScenario(
            id="scenario-1",
            requirement_id="req-1",
            title=" ",
            kind="main",
            fragment_ids=("fragment-1",),
        )


def test_requirement_scenario_rejects_blank_fragment_id() -> None:
    with pytest.raises(ValueError, match="must not contain blanks"):
        RequirementScenario(
            id="scenario-1",
            requirement_id="req-1",
            title="Main",
            kind="main",
            fragment_ids=(" ",),
        )


def test_evidence_set_rejects_element_with_unknown_state() -> None:
    with pytest.raises(ValueError, match="reference a known state"):
        EvidenceSet(
            id="evidence-1",
            title="Evidence",
            elements=(
                ExecutionElement(
                    id="element-1",
                    state_id="missing",
                ),
            ),
        )


def test_evidence_set_rejects_transition_with_unknown_action() -> None:
    with pytest.raises(ValueError, match="reference a known action"):
        EvidenceSet(
            id="evidence-1",
            title="Evidence",
            states=(
                ExecutionState(
                    id="state-1",
                ),
            ),
            transitions=(
                ExecutionTransition(
                    id="transition-1",
                    from_state_id="state-1",
                    action_id="missing",
                ),
            ),
        )


def test_evidence_set_accepts_valid_transition_references() -> None:
    evidence = EvidenceSet(
        id="evidence-1",
        title="Evidence",
        states=(
            ExecutionState(
                id="state-1",
            ),
            ExecutionState(
                id="state-2",
            ),
        ),
        actions=(
            ExecutionAction(
                id="action-1",
            ),
        ),
        transitions=(
            ExecutionTransition(
                id="transition-1",
                from_state_id="state-1",
                action_id="action-1",
                to_state_id="state-2",
            ),
        ),
    )

    assert len(evidence.transitions) == 1


def test_traceability_summary_rejects_negative_counts() -> None:
    with pytest.raises(ValueError, match="must be non-negative"):
        TraceabilitySummary(
            total_requirements=-1,
            covered_requirements=0,
            partially_covered_requirements=0,
            uncovered_requirements=0,
            total_links=0,
        )


def test_traceability_summary_rejects_inconsistent_counts() -> None:
    with pytest.raises(ValueError, match="must equal total_requirements"):
        TraceabilitySummary(
            total_requirements=1,
            covered_requirements=1,
            partially_covered_requirements=1,
            uncovered_requirements=0,
            total_links=0,
        )


def test_traceability_result_rejects_alignment_with_unknown_occurrence() -> None:
    summary = TraceabilitySummary(
        total_requirements=1,
        covered_requirements=0,
        partially_covered_requirements=0,
        uncovered_requirements=1,
        total_links=0,
    )

    with pytest.raises(ValueError, match="reference a known occurrence"):
        TraceabilityResult(
            id="result-1",
            title="Result",
            summary=summary,
            fragment_alignments=(
                RequirementFragmentAlignment(
                    id="alignment-1",
                    requirement_id="req-1",
                    fragment_id="fragment-1",
                    occurrence_id="missing",
                    evidence_refs=(
                        EvidenceRef(
                            kind=EvidenceRefKind.ARTIFACT,
                            evidence_id="artifact-1",
                        ),
                    ),
                    match_kind=FragmentMatchKind.PARTIAL,
                ),
            ),
        )
