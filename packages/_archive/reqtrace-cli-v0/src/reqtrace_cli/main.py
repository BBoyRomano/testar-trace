from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import typer
from rich.console import Console

from reqtrace._api_types import (
    parse_evidence_format_input,
    parse_requirements_format_input,
    parse_trace_method_name,
)
from reqtrace.application.execution.orchestrator import (
    build_default_orchestrator,
)
from reqtrace import (
    TraceRequest,
    analyze,
    load_result,
    save_result,
)
from reqtrace.formats import (
    SUPPORTED_EVIDENCE_FORMATS,
    SUPPORTED_REQUIREMENTS_FORMATS,
)
from reqtrace_cli.rendering import render_result

app = typer.Typer(help="ReqTrace CLI.", no_args_is_help=True)
console = Console()
logger = logging.getLogger(__name__)
_LOG_LEVEL_ORDER = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
_DEFAULT_LOG_MAX_BYTES = 5 * 1024 * 1024
_DEFAULT_LOG_BACKUP_COUNT = 3


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


def _configure_app_logging(
    *,
    level_name: str,
    log_file: Path | None,
) -> int:
    resolved_level = getattr(logging, level_name)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                filename=log_file,
                maxBytes=_DEFAULT_LOG_MAX_BYTES,
                backupCount=_DEFAULT_LOG_BACKUP_COUNT,
                encoding="utf-8",
            )
        )
    logging.basicConfig(
        level=resolved_level,
        handlers=handlers,
        force=True,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return resolved_level


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
    try:
        effective_level = _resolve_log_level(log_level, verbose=verbose, quiet=quiet)
        resolved = _configure_app_logging(
            level_name=effective_level,
            log_file=log_file,
        )
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


@app.command("methods")
def list_methods() -> None:
    service = build_default_orchestrator()
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
    evidence: Path = typer.Option(
        ...,
        "--evidence",
        exists=True,
        readable=True,
    ),
    requirements_format: str = typer.Option(
        "auto",
        "--requirements-format",
        help=(
            "Requirements format "
            f"({', '.join(SUPPORTED_REQUIREMENTS_FORMATS)} or auto)."
        ),
    ),
    evidence_format: str = typer.Option(
        "auto",
        "--evidence-format",
        help=f"Evidence format ({', '.join(SUPPORTED_EVIDENCE_FORMATS)} or auto).",
    ),
    method: str = typer.Option("baseline", "--method"),
    selected_requirement_ids: list[str] = typer.Option([], "--requirement-id"),
    selected_evidence_run_ids: list[str] = typer.Option(
        [],
        "--evidence-run-id",
    ),
    output: Path | None = typer.Option(None, "--output", "-o"),
) -> None:
    try:
        trace_request = TraceRequest(
            requirements_paths=list(requirements),
            evidence_path=evidence,
            requirements_format=parse_requirements_format_input(
                requirements_format
            ),
            evidence_format=parse_evidence_format_input(
                evidence_format
            ),
            method_name=parse_trace_method_name(method),
            selected_requirement_ids=selected_requirement_ids,
            selected_evidence_run_ids=selected_evidence_run_ids,
        )
        result = analyze(trace_request)
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
        save_result(result, output)
        logger.info(
            "CLI run result exported.",
            extra={"run_id": result.run.id, "output_path": str(output)},
        )
        console.print(f"Saved result to {output}")


@app.command("show-result")
def show_result(
    result_path: Path = typer.Argument(..., exists=True, readable=True),
) -> None:
    logger.info("Rendering saved result.", extra={"result_path": str(result_path)})
    render_result(console, load_result(result_path))


def main() -> None:
    app()


if __name__ == "__main__":
    main()



