from pathlib import Path

from reqtrace.presentation.runtime import RunInput, build_request, execute_run, export_result_json, import_result_json
from tests._builders import write_minimal_requirement_markdown, write_minimal_testar_model_file


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
