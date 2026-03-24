from pathlib import Path

from reqtrace.application.analyze_coverage import (
    AnalyzeCoverageRequest,
    AnalyzeCoverageUseCase,
)
from reqtrace.domain.coverage import OccurrenceStatus, RequirementStatus


FIXTURES_DIR = Path("tests/fixtures")


def test_path_occurrence_v1_builds_occurrences() -> None:
    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path=str(FIXTURES_DIR / "canonical" /
                           "case_001_found" / "state.json"),
            requirements_path=str(
                FIXTURES_DIR / "canonical" / "case_001_found" / "requirements.json"
            ),
            analyzer_name="path_occurrence_v1",
        )
    )

    result = report.results[0]

    assert result.status == RequirementStatus.FOUND
    assert len(result.occurrences) >= 1

    occurrence = result.occurrences[0]
    assert occurrence.occurrence_id
    assert occurrence.status in {
        OccurrenceStatus.FOUND,
        OccurrenceStatus.PARTIALLY_FOUND,
    }
    assert occurrence.state_ids
    assert isinstance(occurrence.steps, tuple)


def test_path_occurrence_v1_occurrences_include_step_details() -> None:
    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path=str(FIXTURES_DIR / "canonical" /
                           "case_001_found" / "state.json"),
            requirements_path=str(
                FIXTURES_DIR / "canonical" / "case_001_found" / "requirements.json"
            ),
            analyzer_name="path_occurrence_v1",
        )
    )

    occurrence = report.results[0].occurrences[0]
    assert occurrence.steps

    first_step = occurrence.steps[0]
    assert first_step.unit_id
    assert first_step.status.value in {"found", "partially_found", "not_found"}


def test_path_occurrence_v1_runs_on_tbuis_public_model() -> None:
    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path="suts/tbuis/testar/runs/2026-03-22-webdriver-tbuis-public/model.json",
            requirements_path="suts/tbuis/requirements/use-cases.json",
            analyzer_name="path_occurrence_v1",
        )
    )

    assert report.summary.total_requirements >= 1
    assert report.metadata["analyzer"] == "path_occurrence_v1"
