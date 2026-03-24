from reqtrace.analysis.trace_builders import build_trace_step_matches
from reqtrace.domain.coverage import (
    MatchEvidence,
    RequirementUnitResult,
    RequirementUnitStatus,
)


def test_build_trace_step_matches_from_unit_results() -> None:
    unit_results = (
        RequirementUnitResult(
            requirement_id="UC.01",
            unit_id="UC.01.step.1",
            status=RequirementUnitStatus.FOUND,
            evidence=(
                MatchEvidence(
                    state_ids=("S1",),
                    transition_ids=("T1",),
                    observations=("Login button",),
                    explanation="Matched Login button.",
                    metadata={},
                ),
            ),
            metadata={"unit_kind": "step"},
        ),
    )

    matches = build_trace_step_matches(unit_results)

    assert len(matches) == 1

    match = matches[0]
    assert match.requirement_id == "UC.01"
    assert match.unit_id == "UC.01.step.1"
    assert match.unit_kind == "step"
    assert match.sequence == 1
    assert match.state_ids == ("S1",)
    assert match.transition_ids == ("T1",)
    assert match.matched_observations == ("Login button",)
    assert match.status == RequirementUnitStatus.FOUND
    assert match.explanation == "Matched Login button."


def test_build_trace_step_matches_extracts_multiple_matches() -> None:
    unit_results = (
        RequirementUnitResult(
            requirement_id="UC.01",
            unit_id="UC.01.post.2",
            status=RequirementUnitStatus.PARTIALLY_FOUND,
            evidence=(
                MatchEvidence(
                    state_ids=("S1",),
                    transition_ids=(),
                    observations=("Overview page",),
                    explanation="Matched Overview page.",
                    metadata={},
                ),
                MatchEvidence(
                    state_ids=("S2",),
                    transition_ids=(),
                    observations=("Logout option",),
                    explanation="Matched Logout option.",
                    metadata={},
                ),
            ),
            metadata={"unit_kind": "postcondition"},
        ),
    )

    matches = build_trace_step_matches(unit_results)

    assert len(matches) == 2
    assert all(match.sequence == 2 for match in matches)
    assert all(match.unit_kind == "postcondition" for match in matches)


def test_build_trace_step_matches_defaults_unknown_unit_kind() -> None:
    unit_results = (
        RequirementUnitResult(
            requirement_id="UC.99",
            unit_id="UC.99.trigger.1",
            status=RequirementUnitStatus.FOUND,
            evidence=(
                MatchEvidence(
                    state_ids=("S1",),
                    transition_ids=(),
                    observations=("Login option",),
                    explanation="Matched Login option.",
                    metadata={},
                ),
            ),
            metadata={},
        ),
    )

    matches = build_trace_step_matches(unit_results)

    assert len(matches) == 1
    assert matches[0].unit_kind == "unknown"
