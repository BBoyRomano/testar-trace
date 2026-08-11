import importlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import pytest
from typer.testing import CliRunner

from testar_trace.domain import (
    AssessabilityStatus,
    AssessmentScopeKind,
    AssessmentViewKind,
    CompletenessStatus,
    CoverageAssessment,
    CoverageStatus,
    PathMaterializationResult,
    Requirement,
    RequirementSet,
    State,
    StateModel,
    StateModelCollection,
    TraceabilityResult,
)
from testar_trace_cli._evaluation import load_reference_labels
from testar_trace_cli._rendering import (
    render_report,
    render_requirements,
    render_to_text,
)
from testar_trace_cli._serialize import to_plain_data
from testar_trace_cli.main import app

runner = CliRunner()
cli_main = importlib.import_module("testar_trace_cli.main")


def test_help_presents_the_complete_command_surface() -> None:
    result = runner.invoke(app, ["--no-color", "--help"])

    assert result.exit_code == 0
    assert "Establish requirements completeness" in result.stdout
    for command in ("analyze", "compare", "validate", "requirements", "report"):
        assert command in result.stdout
    assert "--install-completion" in result.stdout


def test_version_reports_the_installed_cli_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "TESTAR Trace CLI 0.1.0"


def test_console_entrypoint_formats_usage_errors_without_a_traceback(capsys) -> None:
    exit_code = cli_main.main(["--invalid-option"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "No such option" in captured.err
    assert "Traceback" not in captured.err


def test_methods_supports_machine_readable_output() -> None:
    result = runner.invoke(app, ["methods", "--format", "json"])

    assert result.exit_code == 0
    methods = json.loads(result.stdout)
    assert {item["id"] for item in methods} >= {
        "graph-alignment",
        "execution-alignment",
        "automata-conformance",
    }


def test_formats_uses_canonical_state_model_terminology() -> None:
    result = runner.invoke(app, ["--no-color", "formats"])

    assert result.exit_code == 0
    assert "Input adapters" in result.stdout
    assert "Requirements" in result.stdout
    assert "State model" in result.stdout
    assert "testar" in result.stdout


def test_validate_requires_at_least_one_input() -> None:
    result = runner.invoke(app, ["--no-color", "validate"])

    assert result.exit_code == 1
    assert "provide --requirements, --state-models, or both" in result.stderr
    assert "Traceback" not in result.stderr


def test_requirements_command_renders_authored_flows(
    monkeypatch, tmp_path: Path
) -> None:
    source = tmp_path / "requirements.md"
    source.write_text("fixture", encoding="utf-8")
    monkeypatch.setattr(
        cli_main, "load_requirements", lambda *args, **kwargs: requirement_set()
    )

    result = runner.invoke(
        app,
        ["--no-color", "requirements", "--requirements", str(source)],
    )

    assert result.exit_code == 0
    assert "Requirements" in result.stdout
    assert "REQ-1 · Login" in result.stdout


def test_analyze_emits_current_completeness_summary(
    monkeypatch, tmp_path: Path
) -> None:
    requirements_path, state_models_path = input_paths(tmp_path)
    patch_analysis(monkeypatch)

    result = runner.invoke(
        app,
        [
            "--no-color",
            "--no-progress",
            "analyze",
            "--requirements",
            str(requirements_path),
            "--state-models",
            str(state_models_path),
            "--detail",
            "summary",
        ],
    )

    assert result.exit_code == 0
    assert "0 of 1 complete" in result.stdout
    assert "1 incomplete" in result.stdout
    assert "Requirement paths" in result.stdout


@pytest.mark.parametrize(
    ("arguments", "obsolete_option"),
    [
        (["analyze", "--evidence", "model.json"], "--evidence"),
        (["requirements", "--requirements-kind", "use-case"], "--requirements-kind"),
        (["analyze", "--json"], "--json"),
    ],
)
def test_cli_rejects_removed_compatibility_options(
    monkeypatch, tmp_path: Path, arguments: list[str], obsolete_option: str
) -> None:
    _, state_models_path = input_paths(tmp_path)
    patch_analysis(monkeypatch)
    resolved_arguments = [
        str(state_models_path) if value == "model.json" else value
        for value in arguments
    ]
    result = runner.invoke(app, resolved_arguments)

    assert result.exit_code == 2
    assert obsolete_option in result.stderr


@pytest.mark.parametrize("command", ["show-requirements", "show-report"])
def test_cli_rejects_removed_compatibility_commands(command: str) -> None:
    result = runner.invoke(app, [command])

    assert result.exit_code == 2
    assert "No such command" in result.stderr


def test_analyze_can_fail_ci_on_incomplete_requirements(
    monkeypatch, tmp_path: Path
) -> None:
    requirements_path, state_models_path = input_paths(tmp_path)
    patch_analysis(monkeypatch)

    result = runner.invoke(
        app,
        [
            "--no-progress",
            "analyze",
            "--requirements",
            str(requirements_path),
            "--state-models",
            str(state_models_path),
            "--fail-on-incomplete",
            "--detail",
            "summary",
        ],
    )

    assert result.exit_code == 1
    assert "0 of 1 complete" in result.stdout


def test_analyze_refuses_to_replace_output_without_force(
    monkeypatch, tmp_path: Path
) -> None:
    requirements_path, state_models_path = input_paths(tmp_path)
    output = tmp_path / "report.json"
    output.write_text("keep", encoding="utf-8")
    patch_analysis(monkeypatch)

    result = runner.invoke(
        app,
        [
            "--no-color",
            "analyze",
            "--requirements",
            str(requirements_path),
            "--state-models",
            str(state_models_path),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 1
    assert "Use --force" in result.stderr
    assert output.read_text(encoding="utf-8") == "keep"


def test_analyze_writes_a_full_report_atomically(monkeypatch, tmp_path: Path) -> None:
    requirements_path, state_models_path = input_paths(tmp_path)
    output = tmp_path / "report.json"
    patch_analysis(monkeypatch)

    result = runner.invoke(
        app,
        [
            "--quiet",
            "analyze",
            "--requirements",
            str(requirements_path),
            "--state-models",
            str(state_models_path),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert (
        json.loads(output.read_text(encoding="utf-8"))["summary"][
            "incomplete_requirements"
        ]
        == 1
    )


def test_unknown_method_is_a_concise_user_error(monkeypatch, tmp_path: Path) -> None:
    requirements_path, state_models_path = input_paths(tmp_path)
    patch_analysis(monkeypatch)

    result = runner.invoke(
        app,
        [
            "--no-color",
            "analyze",
            "--requirements",
            str(requirements_path),
            "--state-models",
            str(state_models_path),
            "--method",
            "missing",
        ],
    )

    assert result.exit_code == 1
    assert "unknown traceability method" in result.stderr
    assert "Traceback" not in result.stderr


def test_compare_reports_accuracy_macro_f1_and_assessability(
    monkeypatch, tmp_path: Path
) -> None:
    requirements_path, state_models_path = input_paths(tmp_path)
    labels = tmp_path / "labels.json"
    labels.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "labels": [
                    {
                        "scope_kind": "requirement",
                        "scope_id": "REQ-1",
                        "completeness": "not-assessable",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        cli_main, "load_requirements", lambda *args, **kwargs: requirement_set()
    )
    monkeypatch.setattr(
        cli_main, "load_state_models", lambda *args, **kwargs: state_model_collection()
    )

    result = runner.invoke(
        app,
        [
            "compare",
            "--requirements",
            str(requirements_path),
            "--state-models",
            str(state_models_path),
            "--labels",
            str(labels),
            "--method",
            "noop",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    evaluation = data["methods"][0]["evaluation"]
    assert evaluation["accuracy"] == 1
    assert evaluation["assessability_rate"] == 0
    assert "macro_f1" in evaluation


def test_reference_labels_reject_unknown_fields(tmp_path: Path) -> None:
    labels = tmp_path / "labels.json"
    labels.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "labels": [
                    {
                        "scope_kind": "requirement",
                        "scope_id": "REQ-1",
                        "completeness": "complete",
                        "completness": "complete",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="completness"):
        load_reference_labels(labels)


def test_render_report_uses_current_link_and_occurrence_fields() -> None:
    text = render_to_text(
        render_report(
            cast(Mapping[str, object], to_plain_data(traceability_result())),
            detail="full",
        )
    )

    assert "Requirement assessments" in text
    assert "Requirement paths" in text
    assert "Trace links" in text
    assert "Requirement completeness" in text


def test_render_requirements_can_focus_one_requirement() -> None:
    text = render_to_text(
        render_requirements(
            {
                "requirements": [
                    {"id": "REQ-1", "title": "Login"},
                    {"id": "REQ-2", "title": "Logout"},
                ],
                "elements": [],
                "flows": [],
            },
            requirement_id="REQ-1",
        )
    )

    assert "REQ-1 · Login" in text
    assert "REQ-2" not in text


def test_to_plain_data_converts_path() -> None:
    assert to_plain_data(Path("report.json")) == "report.json"


def patch_analysis(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_main, "load_requirements", lambda *args, **kwargs: requirement_set()
    )
    monkeypatch.setattr(
        cli_main, "load_state_models", lambda *args, **kwargs: state_model_collection()
    )
    monkeypatch.setattr(
        cli_main, "analyze_traceability", lambda *args, **kwargs: traceability_result()
    )


def input_paths(tmp_path: Path) -> tuple[Path, Path]:
    requirements = tmp_path / "requirements.md"
    state_models = tmp_path / "model.json"
    requirements.write_text("fixture", encoding="utf-8")
    state_models.write_text("{}", encoding="utf-8")
    return requirements, state_models


def requirement_set() -> RequirementSet:
    return RequirementSet(requirements=(Requirement(id="REQ-1", title="Login"),))


def state_model_collection() -> StateModelCollection:
    return StateModelCollection(
        id="models",
        title="State models",
        models=(
            StateModel(
                id="model-1",
                title="Login model",
                states=(State(id="state-1", state_model_id="model-1"),),
            ),
        ),
    )


def traceability_result() -> TraceabilityResult:
    return TraceabilityResult(
        id="result-1",
        title="Graph alignment result",
        path_materialization=PathMaterializationResult(paths=(), bounded=False),
        assessments=(
            CoverageAssessment(
                id="assessment-1",
                scope_kind=AssessmentScopeKind.REQUIREMENT,
                scope_id="REQ-1",
                requirement_ids=("REQ-1",),
                view_kind=AssessmentViewKind.STATE_MODEL_COLLECTION,
                state_model_collection_id="models",
                state_model_ids=("model-1",),
                status=CoverageStatus.PARTIALLY_COVERED,
                assessability=AssessabilityStatus.FULL,
                completeness=CompletenessStatus.INCOMPLETE,
                coverage_ratio=0.5,
                rationale="Required ordered evidence is incomplete.",
            ),
        ),
        metadata={"method": "graph-alignment"},
    )
