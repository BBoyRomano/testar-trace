from reqtrace.domain.coverage import (
    CoverageReport,
    CoverageSummary,
    MatchEvidence,
    OccurrenceStatus,
    RequirementOccurrence,
    RequirementOccurrenceStep,
    RequirementResult,
    RequirementStatus,
    RequirementUnitResult,
    RequirementUnitStatus,
)


def test_requirement_result_supports_occurrences() -> None:
    evidence = MatchEvidence(
        state_ids=("S1",),
        transition_ids=("T1",),
        observations=("Login",),
        explanation="Matched login step.",
        metadata={},
    )

    unit_result = RequirementUnitResult(
        requirement_id="UC.01",
        unit_id="UC.01.main.1",
        status=RequirementUnitStatus.FOUND,
        evidence=(evidence,),
        metadata={},
    )

    occurrence_step = RequirementOccurrenceStep(
        unit_id="UC.01.main.1",
        status=RequirementUnitStatus.FOUND,
        evidence=(evidence,),
        metadata={},
    )

    occurrence = RequirementOccurrence(
        occurrence_id="UC.01#1",
        status=OccurrenceStatus.FOUND,
        state_ids=("S1", "S2"),
        transition_ids=("T1",),
        steps=(occurrence_step,),
        metadata={},
    )

    result = RequirementResult(
        requirement_id="UC.01",
        status=RequirementStatus.FOUND,
        unit_results=(unit_result,),
        occurrences=(occurrence,),
        metadata={},
    )

    assert result.requirement_id == "UC.01"
    assert len(result.occurrences) == 1
    assert result.occurrences[0].occurrence_id == "UC.01#1"
    assert result.occurrences[0].steps[0].unit_id == "UC.01.main.1"


def test_coverage_report_can_hold_occurrence_based_results() -> None:
    result = RequirementResult(
        requirement_id="UC.01",
        status=RequirementStatus.PARTIALLY_FOUND,
        unit_results=(),
        occurrences=(),
        metadata={},
    )

    report = CoverageReport(
        results=(result,),
        summary=CoverageSummary(
            total_requirements=1,
            found=0,
            partially_found=1,
            not_found=0,
        ),
        metadata={"analyzer": "keyword_v1"},
    )

    assert report.summary.total_requirements == 1
    assert report.results[0].status == RequirementStatus.PARTIALLY_FOUND
