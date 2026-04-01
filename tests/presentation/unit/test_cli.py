from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from reqtrace.presentation.cli.main import app
from tests._builders import write_minimal_requirement_markdown, write_minimal_testar_model_file

runner = CliRunner()


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    requirements_path = tmp_path / "requirements.md"
    write_minimal_requirement_markdown(requirements_path)
    evidence_path = tmp_path / "testar.json"
    write_minimal_testar_model_file(evidence_path)
    return requirements_path, evidence_path


def test_methods_lists_expected_methods() -> None:
    result = runner.invoke(app, ["methods"])
    assert result.exit_code == 0
    assert "baseline" in result.stdout
    assert "candidate_match" in result.stdout
    assert "flow_match" in result.stdout


def test_run_command_executes_and_exports(tmp_path: Path) -> None:
    requirements_path, evidence_path = _write_inputs(tmp_path)
    output_path = tmp_path / "result.json"

    result = runner.invoke(
        app,
        [
            "run",
            "--requirements",
            str(requirements_path),
            "--evidence",
            str(evidence_path),
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert "Traceability Summary" in result.stdout
    assert output_path.exists()


def test_show_result_renders_exported_json(tmp_path: Path) -> None:
    requirements_path, evidence_path = _write_inputs(tmp_path)
    output_path = tmp_path / "result.json"
    first = runner.invoke(
        app,
        [
            "run",
            "--requirements",
            str(requirements_path),
            "--evidence",
            str(evidence_path),
            "--output",
            str(output_path),
        ],
    )
    assert first.exit_code == 0

    shown = runner.invoke(app, ["show-result", str(output_path)])
    assert shown.exit_code == 0
    assert "Per-requirement Results" in shown.stdout


def test_run_command_autogenerates_output_when_missing(tmp_path: Path) -> None:
    with runner.isolated_filesystem(temp_dir=tmp_path):
        workdir = Path.cwd()
        requirements_path = workdir / "requirements.md"
        evidence_path = workdir / "testar.json"
        write_minimal_requirement_markdown(requirements_path)
        write_minimal_testar_model_file(evidence_path)

        result = runner.invoke(
            app,
            [
                "run",
                "--requirements",
                str(requirements_path),
                "--evidence",
                str(evidence_path),
            ],
        )

        assert result.exit_code == 0
        assert "Saved result to" in result.stdout

        saved_line = [line for line in result.stdout.splitlines(
        ) if line.startswith("Saved result to")][-1]
        saved_path = Path(saved_line.split("Saved result to", 1)[1].strip())
        assert (workdir / saved_path).exists()


def test_run_command_supports_requirements_directory(tmp_path: Path) -> None:
    req_dir = tmp_path / "requirements"
    req_dir.mkdir()
    write_minimal_requirement_markdown(req_dir / "uc-01.md", title="UC 01")
    write_minimal_requirement_markdown(req_dir / "uc-02.md", title="UC 02")
    evidence_path = tmp_path / "testar.json"
    write_minimal_testar_model_file(evidence_path)
    output_path = tmp_path / "result.json"

    result = runner.invoke(
        app,
        [
            "run",
            "--requirements",
            str(req_dir),
            "--evidence",
            str(evidence_path),
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["summary"]["requirement_count"] == 2
