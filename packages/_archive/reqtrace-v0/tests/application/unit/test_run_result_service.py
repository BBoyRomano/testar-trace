from __future__ import annotations

from pathlib import Path

import pytest

from reqtrace.application.services.run_result_service import export_result_json, import_result_json
from reqtrace.infrastructure.exceptions import ReportDeserializationError


def test_export_and_import_result_json_roundtrip(tmp_path: Path, build_traceability_result) -> None:
    result = build_traceability_result(tmp_path)
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
