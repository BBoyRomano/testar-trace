from pathlib import Path

from reqtrace.application.analyze_coverage import (
    AnalyzeCoverageRequest,
    AnalyzeCoverageUseCase,
)
from reqtrace.domain.coverage import RequirementStatus


FIXTURES_DIR = Path("tests/fixtures/analysis_sources")


def _analyze(state_path: Path, requirements_path: Path) -> tuple[str, dict]:
    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path=str(state_path),
            requirements_path=str(requirements_path),
            analyzer_name="keyword_v1",
        )
    )

    assert report.summary.total_requirements == 1
    result = report.results[0]
    return result.status.value, {
        "found": report.summary.found,
        "partially_found": report.summary.partially_found,
        "not_found": report.summary.not_found,
    }


def test_keyword_v1_produces_equivalent_outcomes_for_login_across_formats() -> None:
    json_status, json_summary = _analyze(
        FIXTURES_DIR / "use_cases_json" / "state.json",
        FIXTURES_DIR / "use_cases_json" / "requirements.json",
    )
    markdown_status, markdown_summary = _analyze(
        FIXTURES_DIR / "use_cases_markdown" / "state.json",
        FIXTURES_DIR / "use_cases_markdown" / "requirements.md",
    )
    csv_status, csv_summary = _analyze(
        FIXTURES_DIR / "user_stories_csv" / "state.json",
        FIXTURES_DIR / "user_stories_csv" / "requirements.csv",
    )
    gherkin_status, gherkin_summary = _analyze(
        FIXTURES_DIR / "gherkin_feature" / "state.json",
        FIXTURES_DIR / "gherkin_feature" / "requirements.feature",
    )

    assert json_status == markdown_status == csv_status == gherkin_status
    assert json_summary == markdown_summary == csv_summary == gherkin_summary
    assert json_status == RequirementStatus.PARTIALLY_FOUND.value
