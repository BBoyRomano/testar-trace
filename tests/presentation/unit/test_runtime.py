from pathlib import Path

import pytest
from tests._builders import (
    write_minimal_requirement_markdown,
    write_minimal_testar_model_file,
    write_minimal_use_case_json_file,
)

from reqtrace.presentation.exceptions import RunInputValidationError
from reqtrace.presentation.runtime import (
    RunInput,
    build_request,
    execute_run,
    export_result_json,
    import_result_json,
    infer_requirements_format,
    normalize_evidence_format,
    normalize_requirements_format,
)


def test_build_request_and_execute_roundtrip(tmp_path: Path) -> None:
    requirements_path = tmp_path / "requirements.md"
    write_minimal_requirement_markdown(requirements_path)

    evidence_path = tmp_path / "testar.json"
    write_minimal_testar_model_file(evidence_path)

    run_input = RunInput(requirements_path=requirements_path, evidence_path=evidence_path)
    request = build_request(run_input)
    assert request.method_name == "baseline"
    assert len(request.requirements.requirements) == 1
    assert len(request.evidence.runs) == 1

    result = execute_run(run_input)
    assert result.summary.requirement_count == 1
    assert result.summary.uncovered_requirement_count == 1

    export_path = tmp_path / "result.json"
    export_result_json(result, export_path)
    imported = import_result_json(export_path)
    assert imported.run.id == result.run.id
    assert imported.summary.requirement_count == 1


def test_build_request_supports_requirements_directory(tmp_path: Path) -> None:
    req_dir = tmp_path / "requirements"
    req_dir.mkdir()
    write_minimal_requirement_markdown(req_dir / "uc-01.md", title="UC 01")
    write_minimal_requirement_markdown(req_dir / "uc-02.md", title="UC 02")

    evidence_path = tmp_path / "testar.json"
    write_minimal_testar_model_file(evidence_path)

    request = build_request(RunInput(requirements_paths=[req_dir], evidence_path=evidence_path))
    assert len(request.requirements.requirements) == 2


def test_build_request_supports_json_requirements_directory(tmp_path: Path) -> None:
    req_dir = tmp_path / "requirements-json"
    req_dir.mkdir()
    write_minimal_use_case_json_file(req_dir / "tbuis.json")

    evidence_path = tmp_path / "testar.json"
    write_minimal_testar_model_file(evidence_path)

    request = build_request(
        RunInput(
            requirements_paths=[req_dir],
            requirements_format="json",
            evidence_path=evidence_path,
        )
    )
    assert len(request.requirements.requirements) == 2


def test_normalize_format_helpers_support_aliases_and_reject_unknowns() -> None:
    assert normalize_requirements_format("md") == "markdown"
    assert normalize_requirements_format("JSON") == "json"
    assert normalize_evidence_format("TESTAR") == "testar"

    with pytest.raises(RunInputValidationError):
        normalize_requirements_format("xml")


def test_build_request_requires_evidence_path(tmp_path: Path) -> None:
    requirements_path = tmp_path / "requirements.md"
    write_minimal_requirement_markdown(requirements_path)

    with pytest.raises(RunInputValidationError):
        build_request(RunInput(requirements_path=requirements_path, evidence_path=None))


def test_build_request_rejects_missing_requirements_path(tmp_path: Path) -> None:
    evidence_path = tmp_path / "testar.json"
    write_minimal_testar_model_file(evidence_path)

    with pytest.raises(RunInputValidationError):
        build_request(RunInput(requirements_paths=[], evidence_path=evidence_path))


def test_build_request_rejects_missing_evidence_file(tmp_path: Path) -> None:
    requirements_path = tmp_path / "requirements.md"
    write_minimal_requirement_markdown(requirements_path)

    with pytest.raises(RunInputValidationError):
        build_request(
            RunInput(requirements_path=requirements_path, evidence_path=tmp_path / "missing.json")
        )


def test_build_request_rejects_requirements_directory_without_matching_files(
    tmp_path: Path,
) -> None:
    req_dir = tmp_path / "requirements"
    req_dir.mkdir()
    (req_dir / "ignored.txt").write_text("nothing", encoding="utf-8")
    evidence_path = tmp_path / "testar.json"
    write_minimal_testar_model_file(evidence_path)

    with pytest.raises(RunInputValidationError):
        build_request(RunInput(requirements_paths=[req_dir], evidence_path=evidence_path))


def test_build_request_deduplicates_repeated_requirement_paths(tmp_path: Path) -> None:
    requirements_path = tmp_path / "requirements.md"
    write_minimal_requirement_markdown(requirements_path)
    evidence_path = tmp_path / "testar.json"
    write_minimal_testar_model_file(evidence_path)

    request = build_request(
        RunInput(
            requirements_paths=[requirements_path, requirements_path],
            evidence_path=evidence_path,
        )
    )
    assert len(request.requirements.requirements) == 1


def test_normalize_evidence_format_rejects_unknown_value() -> None:
    with pytest.raises(RunInputValidationError):
        normalize_evidence_format("xml")


def test_infer_requirements_format_from_file_and_directory(tmp_path: Path) -> None:
    markdown_file = tmp_path / "requirements.md"
    markdown_file.write_text("# UC\n## Main flow\n- step", encoding="utf-8")
    assert infer_requirements_format([markdown_file]) == "markdown"

    json_dir = tmp_path / "req-json"
    json_dir.mkdir()
    write_minimal_use_case_json_file(json_dir / "uc.json")
    assert infer_requirements_format([json_dir]) == "json"


def test_infer_requirements_format_rejects_mixed_inputs(tmp_path: Path) -> None:
    markdown_file = tmp_path / "requirements.md"
    markdown_file.write_text("# UC\n## Main flow\n- step", encoding="utf-8")
    json_file = tmp_path / "requirements.json"
    json_file.write_text('{"requirements":[]}', encoding="utf-8")

    with pytest.raises(RunInputValidationError):
        infer_requirements_format([markdown_file, json_file])
