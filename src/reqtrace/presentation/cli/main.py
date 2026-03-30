from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from reqtrace.application.services.traceability_service import build_default_traceability_service
from reqtrace.presentation.cli.rendering import render_result
from reqtrace.presentation.gui.app import launch_gui
from reqtrace.presentation.runtime import RunInput, default_export_path, execute_run, export_result_json, import_result_json

app = typer.Typer(help="ReqTrace CLI.", no_args_is_help=True)
console = Console()


@app.command("methods")
def list_methods() -> None:
    """List available traceability methods."""
    service = build_default_traceability_service()
    for name in service.available_methods():
        console.print(name)


@app.command("run")
def run_command(
    requirements: list[Path] = typer.Option(..., "--requirements", exists=True, readable=True,
                                            help="Requirement markdown file(s) or directories. Repeat the option to provide multiple paths."),
    evidence: Path = typer.Option(..., "--evidence",
                                  exists=True, readable=True),
    requirements_format: str = typer.Option(
        "markdown", "--requirements-format"),
    evidence_format: str = typer.Option("testar", "--evidence-format"),
    method: str = typer.Option("baseline", "--method"),
    selected_requirement_ids: list[str] = typer.Option([], "--requirement-id"),
    selected_evidence_run_ids: list[str] = typer.Option(
        [], "--evidence-run-id"),
    output: Path | None = typer.Option(None, "--output", "-o"),
) -> None:
    """Execute a traceability run from source files.

    You may pass one or more requirement markdown files, or a directory to load all
    ``*.md`` use-case files from that directory.
    """
    run_input = RunInput(
        requirements_paths=list(requirements),
        evidence_path=evidence,
        requirements_format=requirements_format,
        evidence_format=evidence_format,
        method_name=method,
        selected_requirement_ids=selected_requirement_ids,
        selected_evidence_run_ids=selected_evidence_run_ids,
    )

    result = execute_run(run_input)
    render_result(console, result)

    export_path = output or default_export_path(run_input, result)
    export_result_json(result, export_path)
    console.print(f"Saved result to {export_path}")


@app.command("show-result")
def show_result(result_path: Path = typer.Argument(..., exists=True, readable=True)) -> None:
    """Open and render a previously exported JSON result."""
    result = import_result_json(result_path)
    render_result(console, result)


@app.command("ui")
def ui() -> None:
    """Launch the lightweight desktop UI."""
    raise typer.Exit(code=launch_gui())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
