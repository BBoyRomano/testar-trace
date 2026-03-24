import pytest

from reqtrace.application.analyze_coverage import (
    AnalyzeCoverageRequest,
    AnalyzeCoverageUseCase,
)
from reqtrace.domain.coverage import RequirementStatus
from tests.test_support import get_tbuis_public_model_path


def test_evidence_v1_runs_on_tbuis_public_model() -> None:
    model_path = get_tbuis_public_model_path()
    if model_path is None:
        pytest.skip(
            "TbUIS public TESTAR model is not available in this repository layout.")

    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path=str(model_path),
            requirements_path="suts/tbuis/requirements/use-cases.json",
            analyzer_name="evidence_v1",
        )
    )

    assert report.summary.total_requirements >= 1
    assert report.metadata["analyzer"] == "evidence_v1"
    assert any(
        result.status
        in {
            RequirementStatus.FOUND,
            RequirementStatus.PARTIALLY_FOUND,
            RequirementStatus.NOT_FOUND,
        }
        for result in report.results
    )
