import json
from pathlib import Path

from reqtrace.application.analyze_coverage import (
    AnalyzeCoverageRequest,
    AnalyzeCoverageUseCase,
)
from reqtrace.export.json_report import report_to_dict, write_json_report


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "canonical"


def test_report_to_dict_contains_expected_sections() -> None:
    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path=str(FIXTURES_DIR / "case_001_found" / "state.json"),
            requirements_path=str(
                FIXTURES_DIR / "case_001_found" / "requirements.json"),
            analyzer_name="keyword_v1",
        )
    )

    payload = report_to_dict(report)

    assert set(payload.keys()) == {"results", "summary", "metadata"}
    assert payload["summary"]["total_requirements"] == 1
    assert payload["summary"]["found"] == 1
    assert payload["metadata"]["analyzer"] == "keyword_v1"


def test_write_json_report_writes_utf8_json_file(tmp_path: Path) -> None:
    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path=str(FIXTURES_DIR / "case_001_found" / "state.json"),
            requirements_path=str(
                FIXTURES_DIR / "case_001_found" / "requirements.json"),
            analyzer_name="evidence_v1",
        )
    )

    output_path = tmp_path / "report.json"
    write_json_report(report, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert output_path.exists()
    assert payload["metadata"]["analyzer"] == "evidence_v1"
    assert payload["summary"]["total_requirements"] == 1
    assert payload["results"][0]["requirement_id"] == "UC.01"
