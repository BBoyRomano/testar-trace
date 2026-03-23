from __future__ import annotations

import json
from pathlib import Path

import typer

from reqtrace.application.analyze_coverage import (
    AnalyzeCoverageRequest,
    AnalyzeCoverageUseCase,
)
from reqtrace.export.json_report import write_json_report
from reqtrace.presentation.ui.app import ReqTraceApp, UiInput

app = typer.Typer(help="ReqTrace CLI.", no_args_is_help=True)


@app.callback()
def callback() -> None:
    """ReqTrace CLI."""
    return None


@app.command()
def analyze(
    state_path: Path = typer.Argument(..., exists=True, readable=True),
    requirements_path: Path = typer.Argument(..., exists=True, readable=True),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write the full report as JSON.",
    ),
    analyzer: str = typer.Option(
        "keyword_v1",
        "--analyzer",
        help="Analyzer to use.",
    ),
) -> None:
    use_case = AnalyzeCoverageUseCase()
    report = use_case.execute(
        AnalyzeCoverageRequest(
            state_path=str(state_path),
            requirements_path=str(requirements_path),
            analyzer_name=analyzer,
        )
    )

    if output is not None:
        write_json_report(report, output)

    typer.echo(
        json.dumps(
            {
                "summary": {
                    "total_requirements": report.summary.total_requirements,
                    "found": report.summary.found,
                    "partially_found": report.summary.partially_found,
                    "not_found": report.summary.not_found,
                },
                "metadata": dict(report.metadata),
            },
            indent=2,
        )
    )


@app.command()
def ui(
    state_path: Path = typer.Argument(..., exists=True, readable=True),
    requirements_path: Path = typer.Argument(..., exists=True, readable=True),
) -> None:
    app_ui = ReqTraceApp(
        UiInput(
            state_path=str(state_path),
            requirements_path=str(requirements_path),
        )
    )
    app_ui.run()


def main() -> None:
    app()
