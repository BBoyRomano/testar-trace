from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.console import Console

from reqtrace.application.services.run_result_service import (
    export_result_json,
    import_result_json,
)
from reqtrace.application.services.traceability_service import build_default_traceability_service
from reqtrace.logging_config import configure_logging
from reqtrace.presentation.cli.rendering import render_result
from reqtrace.presentation.gui.app import launch_gui
from reqtrace.presentation.runtime import (
    SUPPORTED_EVIDENCE_FORMATS,
    SUPPORTED_REQUIREMENTS_FORMATS,
    RunInput,
    execute_run,
)

app = typer.Typer(help="ReqTrace CLI.", no_args_is_help=True)
console = Console()
logger = logging.getLogger(__name__)
_cli_log_level = "WARNING"
_cli_log_file: Path | None = None
_LOG_LEVEL_ORDER = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def _resolve_log_level(base_level: str, *, verbose: int, quiet: int) -> str:
    normalized = base_level.strip().upper()
    try:
        index = _LOG_LEVEL_ORDER.index(normalized)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported log level: {base_level!r}. "
            "Supported values: DEBUG, INFO, WARNING, ERROR, CRITICAL."
        ) from exc
    adjusted_index = index - verbose + quiet
    adjusted_index = max(0, min(len(_LOG_LEVEL_ORDER) - 1, adjusted_index))
    return _LOG_LEVEL_ORDER[adjusted_index]


@app.callback()
def app_callback(
    log_level: str = typer.Option(
        "WARNING",
        "--log-level",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    ),
    verbose: int = typer.Option(
        0,
        "-v",
        "--verbose",
        count=True,
        help="Increase verbosity (repeat for more detail, e.g. -vv).",
    ),
    quiet: int = typer.Option(
        0,
        "-q",
        "--quiet",
        count=True,
        help="Decrease verbosity (repeat for less detail, e.g. -qq).",
    ),
    log_file: Path | None = typer.Option(
        None,
        "--log-file",
        help="Optional path for rotating log file output.",
    ),
) -> None:
    global _cli_log_file, _cli_log_level
    try:
        effective_level = _resolve_log_level(log_level, verbose=verbose, quiet=quiet)
        resolved = configure_logging(effective_level, log_file=log_file)
    except (OSError, ValueError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    logger.debug(
        "CLI logging configured.",
        extra={
            "log_level": resolved,
            "base_log_level": log_level.strip().upper(),
            "verbose": verbose,
            "quiet": quiet,
            "log_file": str(log_file) if log_file else None,
        },
    )
    _cli_log_level = effective_level
    _cli_log_file = log_file


@app.command("methods")
def list_methods() -> None:
    service = build_default_traceability_service()
    logger.info("Listing available traceability methods.")
    for name in service.available_methods():
        console.print(name)


@app.command("formats")
def list_formats() -> None:
    logger.info("Listing supported ingestion formats.")
    console.print("requirements: " + ", ".join(SUPPORTED_REQUIREMENTS_FORMATS))
    console.print("evidence: " + ", ".join(SUPPORTED_EVIDENCE_FORMATS))


@app.command("run")
def run_command(
    requirements: list[Path] = typer.Option(
        ...,
        "--requirements",
        exists=True,
        readable=True,
        help="Requirement source file(s) or directories.",
    ),
    evidence: Path = typer.Option(..., "--evidence", exists=True, readable=True),
    requirements_format: str = typer.Option(
        "markdown",
        "--requirements-format",
        help=f"Requirements format ({', '.join(SUPPORTED_REQUIREMENTS_FORMATS)}).",
    ),
    evidence_format: str = typer.Option(
        "testar",
        "--evidence-format",
        help=f"Evidence format ({', '.join(SUPPORTED_EVIDENCE_FORMATS)}).",
    ),
    method: str = typer.Option("baseline", "--method"),
    selected_requirement_ids: list[str] = typer.Option([], "--requirement-id"),
    selected_evidence_run_ids: list[str] = typer.Option([], "--evidence-run-id"),
    output: Path | None = typer.Option(None, "--output", "-o"),
) -> None:
    run_input = RunInput(
        requirements_paths=list(requirements),
        evidence_path=evidence,
        requirements_format=requirements_format,
        evidence_format=evidence_format,
        method_name=method,
        selected_requirement_ids=selected_requirement_ids,
        selected_evidence_run_ids=selected_evidence_run_ids,
    )
    try:
        result = execute_run(run_input)
    except Exception as exc:
        logger.error(
            "CLI run failed.",
            exc_info=exc,
            extra={"method_name": method, "requirements_count": len(requirements)},
        )
        typer.secho(f"Run failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    logger.debug(
        "CLI run completed.",
        extra={"run_id": result.run.id, "method_name": result.run.method_name},
    )
    render_result(console, result)
    if output is not None:
        export_result_json(result, output)
        logger.info(
            "CLI run result exported.",
            extra={"run_id": result.run.id, "output_path": str(output)},
        )
        console.print(f"Saved result to {output}")


@app.command("show-result")
def show_result(result_path: Path = typer.Argument(..., exists=True, readable=True)) -> None:
    logger.info("Rendering saved result.", extra={"result_path": str(result_path)})
    render_result(console, import_result_json(result_path))


@app.command("ui")
def ui() -> None:
    logger.info("Launching GUI from CLI.")
    raise typer.Exit(code=launch_gui(log_level=_cli_log_level, log_file=_cli_log_file))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
