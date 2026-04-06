from __future__ import annotations

import json
from pathlib import Path

from tests._builders import (
    write_minimal_requirement_markdown,
    write_minimal_testar_model_file,
    write_minimal_use_case_json_file,
)
from typer.testing import CliRunner

import reqtrace.presentation.cli.main as cli_main
from reqtrace.presentation.cli.main import app

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
    assert "conformance_match" in result.stdout
    assert "flow_match" in result.stdout
    assert "hybrid_match" in result.stdout


def test_formats_lists_supported_values() -> None:
    result = runner.invoke(app, ["formats"])
    assert result.exit_code == 0
    assert "requirements: markdown, json" in result.stdout
    assert "evidence: testar" in result.stdout


def test_methods_accepts_valid_log_level_option() -> None:
    result = runner.invoke(app, ["--log-level", "debug", "methods"])
    assert result.exit_code == 0
    assert "baseline" in result.stdout


def test_methods_accepts_verbose_short_option() -> None:
    result = runner.invoke(app, ["-v", "methods"])
    assert result.exit_code == 0
    assert "baseline" in result.stdout


def test_methods_accepts_quiet_short_option() -> None:
    result = runner.invoke(app, ["-q", "methods"])
    assert result.exit_code == 0
    assert "baseline" in result.stdout


def test_methods_accepts_log_file_option(tmp_path: Path) -> None:
    log_path = tmp_path / "reqtrace.log"
    result = runner.invoke(app, ["--log-file", str(log_path), "methods"])
    assert result.exit_code == 0
    assert log_path.exists()


def test_invalid_log_level_returns_non_zero() -> None:
    result = runner.invoke(app, ["--log-level", "verbose", "methods"])
    assert result.exit_code == 2
    assert "Unsupported log level" in result.stderr


def test_ui_command_uses_cli_logging_options(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, str | None] = {}

    def fake_launch_gui(*, log_level: str | None = None, log_file: Path | None = None) -> int:
        captured["log_level"] = log_level
        captured["log_file"] = str(log_file) if log_file else None
        return 0

    monkeypatch.setattr(cli_main, "launch_gui", fake_launch_gui)
    log_path = tmp_path / "gui.log"

    result = runner.invoke(
        app,
        ["--log-level", "debug", "--log-file", str(log_path), "ui"],
    )

    assert result.exit_code == 0
    assert captured["log_level"] == "DEBUG"
    assert captured["log_file"] == str(log_path)


def test_ui_command_verbosity_ladder_from_default_warning(monkeypatch) -> None:
    captured_levels: list[str | None] = []

    def fake_launch_gui(*, log_level: str | None = None, log_file: Path | None = None) -> int:
        captured_levels.append(log_level)
        return 0

    monkeypatch.setattr(cli_main, "launch_gui", fake_launch_gui)

    default_result = runner.invoke(app, ["ui"])
    verbose_result = runner.invoke(app, ["-v", "ui"])
    very_verbose_result = runner.invoke(app, ["-vv", "ui"])

    assert default_result.exit_code == 0
    assert verbose_result.exit_code == 0
    assert very_verbose_result.exit_code == 0
    assert captured_levels == ["WARNING", "INFO", "DEBUG"]


def test_ui_command_applies_quiet_and_verbose_adjustments(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, str | None] = {}

    def fake_launch_gui(*, log_level: str | None = None, log_file: Path | None = None) -> int:
        captured["log_level"] = log_level
        captured["log_file"] = str(log_file) if log_file else None
        return 0

    monkeypatch.setattr(cli_main, "launch_gui", fake_launch_gui)
    log_path = tmp_path / "gui.log"

    result = runner.invoke(
        app,
        ["--log-level", "warning", "-v", "-q", "-q", "--log-file", str(log_path), "ui"],
    )

    assert result.exit_code == 0
    assert captured["log_level"] == "ERROR"
    assert captured["log_file"] == str(log_path)


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


def test_run_command_does_not_export_when_missing_output(tmp_path: Path) -> None:
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
        assert "Saved result to" not in result.stdout
        assert not (workdir / "result.json").exists()


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


def test_run_command_supports_json_requirements_file(tmp_path: Path) -> None:
    requirements_path = tmp_path / "requirements.json"
    write_minimal_use_case_json_file(requirements_path)
    evidence_path = tmp_path / "testar.json"
    write_minimal_testar_model_file(evidence_path)

    result = runner.invoke(
        app,
        [
            "run",
            "--requirements",
            str(requirements_path),
            "--requirements-format",
            "json",
            "--evidence",
            str(evidence_path),
        ],
    )

    assert result.exit_code == 0
    assert "Traceability Summary" in result.stdout


def test_run_command_returns_non_zero_for_invalid_requirements_format(tmp_path: Path) -> None:
    requirements_path, evidence_path = _write_inputs(tmp_path)
    result = runner.invoke(
        app,
        [
            "run",
            "--requirements",
            str(requirements_path),
            "--requirements-format",
            "yaml",
            "--evidence",
            str(evidence_path),
        ],
    )
    assert result.exit_code == 2
    assert "Unsupported requirements format" in result.stderr
