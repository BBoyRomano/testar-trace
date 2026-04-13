from __future__ import annotations

from rich.console import Console

from reqtrace.presentation.cli.rendering import render_result
from reqtrace.presentation.runtime import RunInput, execute_run


def test_render_result_includes_duration_and_external_id_column(
    tmp_path,
    write_minimal_requirement_markdown,
    write_minimal_testar_model_file,
) -> None:
    requirements_path = tmp_path / "requirements.md"
    write_minimal_requirement_markdown(
        requirements_path,
        title=(
            "A very long requirement title intended to exercise CLI truncation behavior and "
            "keep terminal output readable"
        ),
    )
    evidence_path = tmp_path / "testar.json"
    write_minimal_testar_model_file(evidence_path)

    result = execute_run(
        RunInput(
            requirements_paths=[requirements_path],
            requirements_format="markdown",
            evidence_path=evidence_path,
            evidence_format="testar",
            method_name="baseline",
        )
    )

    console = Console(record=True, width=200)
    render_result(console, result)
    output = console.export_text()

    assert "Traceability Summary" in output
    assert "Duration" in output
    assert "Overall Coverage (%)" in output
    assert "Per-requirement Results" in output
    assert "External ID" in output
    assert "Confidence (%)" in output
