from __future__ import annotations

from pathlib import Path

import pytest
from tests._builders import write_minimal_requirement_markdown, write_minimal_testar_model_file

from reqtrace.infrastructure.exceptions import ReportDeserializationError, ReportSerializationError
from reqtrace.infrastructure.serialization.traceability_report_json import load_report, save_report
from reqtrace.presentation.runtime import RunInput, execute_run


def _build_result(tmp_path: Path):
    requirements_path = tmp_path / "requirements.md"
    evidence_path = tmp_path / "testar.json"
    write_minimal_requirement_markdown(requirements_path)
    write_minimal_testar_model_file(evidence_path)
    return execute_run(RunInput(requirements_path=requirements_path, evidence_path=evidence_path))


def test_save_and_load_report_roundtrip(tmp_path: Path) -> None:
    result = _build_result(tmp_path)
    output_path = tmp_path / "nested" / "result.json"

    save_report(result, output_path)
    loaded = load_report(output_path)

    assert loaded.run.id == result.run.id
    assert loaded.summary.requirement_count == result.summary.requirement_count


def test_save_report_raises_serialization_error_for_unwritable_parent(tmp_path: Path) -> None:
    result = _build_result(tmp_path)
    blocking_file = tmp_path / "not-a-directory"
    blocking_file.write_text("x", encoding="utf-8")
    output_path = blocking_file / "result.json"

    with pytest.raises(ReportSerializationError):
        save_report(result, output_path)


def test_load_report_raises_deserialization_error_for_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{ not: json }", encoding="utf-8")

    with pytest.raises(ReportDeserializationError):
        load_report(path)

