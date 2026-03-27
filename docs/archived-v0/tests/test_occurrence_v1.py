from pathlib import Path

import pytest

from reqtrace.application.analyze_coverage import (
    AnalyzeCoverageRequest,
    AnalyzeCoverageUseCase,
)
from reqtrace.domain.coverage import RequirementStatus
from tests.test_support import get_tbuis_public_model_path


FIXTURES_DIR = Path("tests/fixtures")


def test_occurrence_v1_builds_occurrences() -> None:
    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path=str(FIXTURES_DIR / "canonical" /
                           "case_001_found" / "state.json"),
            requirements_path=str(
                FIXTURES_DIR / "canonical" / "case_001_found" / "requirements.json"
            ),
            analyzer_name="occurrence_v1",
        )
    )

    assert report.summary.total_requirements == 1
    assert report.results[0].status == RequirementStatus.FOUND
    assert report.results[0].occurrences
    assert len(report.results[0].occurrences) >= 1


def test_occurrence_v1_reports_occurrence_metadata() -> None:
    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path=str(FIXTURES_DIR / "canonical" /
                           "case_001_found" / "state.json"),
            requirements_path=str(
                FIXTURES_DIR / "canonical" / "case_001_found" / "requirements.json"
            ),
            analyzer_name="occurrence_v1",
        )
    )

    occurrence = report.results[0].occurrences[0]
    assert occurrence.status
    assert occurrence.steps
    assert any(step.unit_id for step in occurrence.steps)


def test_occurrence_v1_runs_on_tbuis_public_model() -> None:
    model_path = get_tbuis_public_model_path()
    if model_path is None:
        pytest.skip(
            "TbUIS public TESTAR model is not available in this repository layout.")

    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path=str(model_path),
            requirements_path="suts/tbuis/requirements/use-cases.json",
            analyzer_name="occurrence_v1",
        )
    )

    assert report.summary.total_requirements >= 1
    assert report.metadata["analyzer"] == "occurrence_v1"
