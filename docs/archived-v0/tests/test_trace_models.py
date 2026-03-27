from reqtrace.analysis.trace_models import (
    TraceCandidate,
    TraceOccurrence,
    TraceStepMatch,
)
from reqtrace.domain.coverage import OccurrenceStatus, RequirementUnitStatus


def test_trace_step_match_defaults_are_stable() -> None:
    match = TraceStepMatch(
        requirement_id="UC.01",
        unit_id="UC.01.step.1",
        unit_kind="step",
        sequence=1,
    )

    assert match.requirement_id == "UC.01"
    assert match.unit_id == "UC.01.step.1"
    assert match.status == RequirementUnitStatus.NOT_FOUND
    assert match.state_ids == ()
    assert match.transition_ids == ()
    assert match.matched_observations == ()


def test_trace_candidate_groups_step_matches() -> None:
    match = TraceStepMatch(
        requirement_id="UC.01",
        unit_id="UC.01.step.1",
        unit_kind="step",
        sequence=1,
        state_ids=("S1",),
        matched_observations=("Login form",),
        status=RequirementUnitStatus.FOUND,
    )

    candidate = TraceCandidate(
        requirement_id="UC.01",
        step_matches=(match,),
        state_ids=("S1",),
        is_connected=True,
        is_order_consistent=True,
        score=1.0,
    )

    assert candidate.requirement_id == "UC.01"
    assert len(candidate.step_matches) == 1
    assert candidate.is_connected is True
    assert candidate.is_order_consistent is True
    assert candidate.score == 1.0


def test_trace_occurrence_wraps_selected_candidate_shape() -> None:
    match = TraceStepMatch(
        requirement_id="UC.01",
        unit_id="UC.01.step.1",
        unit_kind="step",
        sequence=1,
        state_ids=("S1",),
        status=RequirementUnitStatus.FOUND,
    )

    occurrence = TraceOccurrence(
        requirement_id="UC.01",
        occurrence_id="UC.01.occ.1",
        status=OccurrenceStatus.FOUND,
        step_matches=(match,),
        state_ids=("S1",),
    )

    assert occurrence.requirement_id == "UC.01"
    assert occurrence.occurrence_id == "UC.01.occ.1"
    assert occurrence.status == OccurrenceStatus.FOUND
    assert len(occurrence.step_matches) == 1
