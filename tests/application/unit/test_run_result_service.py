from __future__ import annotations

from pathlib import Path

import pytest
from tests._builders import write_minimal_requirement_markdown, write_minimal_testar_model_file

from reqtrace.application.services.run_result_service import export_result_json, import_result_json
from reqtrace.infrastructure.exceptions import ReportDeserializationError
from reqtrace.presentation.runtime import RunInput, execute_run


def _build_result(tmp_path: Path):
    requirements_path = tmp_path / "requirements.md"
    evidence_path = tmp_path / "testar.json"
    write_minimal_requirement_markdown(requirements_path)
    write_minimal_testar_model_file(evidence_path)
    return execute_run(RunInput(requirements_path=requirements_path, evidence_path=evidence_path))


def test_export_and_import_result_json_roundtrip(tmp_path: Path) -> None:
    result = _build_result(tmp_path)
    output_path = tmp_path / "result.json"

    export_result_json(result, output_path)
    imported = import_result_json(output_path)

    assert imported.run.id == result.run.id
    assert imported.summary.requirement_count == result.summary.requirement_count


def test_import_result_json_raises_on_invalid_json(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{broken json", encoding="utf-8")

    with pytest.raises(ReportDeserializationError):
        import_result_json(broken)
