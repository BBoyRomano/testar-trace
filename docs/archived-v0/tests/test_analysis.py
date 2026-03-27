from pathlib import Path

from reqtrace.application.analyze_coverage import (
    AnalyzeCoverageRequest,
    AnalyzeCoverageUseCase,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "canonical"


def test_case_001_found() -> None:
    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path=str(FIXTURES_DIR / "case_001_found" / "state.json"),
            requirements_path=str(
                FIXTURES_DIR / "case_001_found" / "requirements.json"),
        )
    )

    assert report.summary.total_requirements == 1
    assert report.summary.found == 1
    assert report.summary.partially_found == 0
    assert report.summary.not_found == 0


def test_case_002_partially_found() -> None:
    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path=str(
                FIXTURES_DIR / "case_002_partially_found" / "state.json"),
            requirements_path=str(
                FIXTURES_DIR / "case_002_partially_found" / "requirements.json"
            ),
        )
    )

    assert report.summary.total_requirements == 1
    assert report.summary.found == 0
    assert report.summary.partially_found == 1
    assert report.summary.not_found == 0


def test_case_003_not_found() -> None:
    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path=str(FIXTURES_DIR / "case_003_not_found" / "state.json"),
            requirements_path=str(
                FIXTURES_DIR / "case_003_not_found" / "requirements.json"),
        )
    )

    assert report.summary.total_requirements == 1
    assert report.summary.found == 0
    assert report.summary.partially_found == 0
    assert report.summary.not_found == 1
