from reqtrace.application.analyze_coverage import (
    AnalyzeCoverageRequest,
    AnalyzeCoverageUseCase,
)
from reqtrace.analysis.evidence_v1 import EvidenceV1Analyzer
from reqtrace.analysis.registry import get_analyzer


def test_get_evidence_v1_analyzer() -> None:
    analyzer = get_analyzer("evidence_v1")

    assert isinstance(analyzer, EvidenceV1Analyzer)


def test_evidence_v1_runs_on_tbuis_public_model() -> None:
    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path="suts/tbuis/testing/testar/runs/2026-03-22-webdriver-tbuis-public/model.json",
            requirements_path="suts/tbuis/requirements/use-cases.json",
            analyzer_name="evidence_v1",
        )
    )

    assert report.summary.total_requirements == 3
    assert report.metadata["analyzer"] == "evidence_v1"
