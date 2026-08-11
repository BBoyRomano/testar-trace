"""Command definitions and orchestration for the TESTAR Trace CLI."""

import json
import logging
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, TypeGuard

import typer
from rich.panel import Panel
from rich.text import Text

from testar_trace import analyze_traceability, create_builtin_method_registry
from testar_trace.domain import RequirementSet, StateModelCollection
from testar_trace_adapters import (
    create_builtin_adapter_registry,
    load_requirements,
    load_state_models,
)

from ._args import APP_NAME, DetailLevel, OutputFormat, app, cli_version
from ._evaluation import MethodComparison, compare_method, load_reference_labels
from ._logging import configure_logging
from ._rendering import (
    render_comparisons,
    render_formats,
    render_methods,
    render_report,
    render_requirements,
    render_validation,
)
from ._runtime import RuntimeOptions, analysis_progress, console, get_runtime
from ._serialize import dumps_json, load_json_file, to_plain_data, write_json

logger = logging.getLogger(__name__)

StateModelsPath = Annotated[
    Path,
    typer.Option(
        "--state-models",
        "-s",
        exists=True,
        readable=True,
        resolve_path=True,
        help="TESTAR state-model file or directory.",
        rich_help_panel="Inputs",
    ),
]
RequirementsAdapter = Annotated[
    str | None,
    typer.Option(
        "--requirements-adapter",
        help="Requirement adapter ID. Auto-detected when omitted.",
        rich_help_panel="Input adapters",
    ),
]
StateModelAdapter = Annotated[
    str | None,
    typer.Option(
        "--state-model-adapter",
        help="State-model adapter ID. Auto-detected when omitted.",
        rich_help_panel="Input adapters",
    ),
]


@app.callback()
def cli(
    context: typer.Context,
    verbose: Annotated[
        int,
        typer.Option("--verbose", "-v", count=True, help="Increase diagnostic output."),
    ] = 0,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress terminal rendering for output-file workflows.",
        ),
    ] = False,
    color: Annotated[
        bool | None,
        typer.Option("--color/--no-color", help="Enable or disable ANSI color."),
    ] = None,
    progress: Annotated[
        bool,
        typer.Option(
            "--progress/--no-progress", help="Show interactive analysis progress."
        ),
    ] = True,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Show tracebacks for unexpected failures."),
    ] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version", is_eager=True, help="Show the installed version and exit."
        ),
    ] = False,
) -> None:
    """Establish requirements completeness in TESTAR state models."""
    runtime = RuntimeOptions(
        verbose=verbose,
        quiet=quiet,
        no_color=None if color is None else not color,
        progress=progress,
        debug=debug,
    )
    context.obj = runtime
    context.color = color
    configure_logging(runtime)
    if version:
        console(runtime).print(cli_version())
        raise typer.Exit()


@app.command("methods")
def methods_command(
    context: typer.Context,
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", help="Output format."),
    ] = OutputFormat.TEXT,
) -> None:
    """List available traceability methods and their intended use."""
    runtime = get_runtime(context)
    methods = tuple(create_builtin_method_registry())
    if output_format is OutputFormat.JSON:
        _print_json([{"id": item.id, "name": item.name} for item in methods])
    else:
        console(runtime).print(render_methods(methods))


@app.command("formats")
def formats_command(
    context: typer.Context,
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", help="Output format."),
    ] = OutputFormat.TEXT,
) -> None:
    """List registered requirement and state-model input adapters."""
    runtime = get_runtime(context)
    registry = create_builtin_adapter_registry()
    if output_format is OutputFormat.JSON:
        _print_json(
            {
                "requirements": [
                    {"id": item.id, "name": item.name, "formats": item.formats}
                    for item in registry.requirement_adapters()
                ],
                "state_models": [
                    {"id": item.id, "name": item.name, "formats": item.formats}
                    for item in registry.state_model_adapters()
                ],
            }
        )
    else:
        console(runtime).print(render_formats(registry))


@app.command("requirements")
def requirements_command(
    context: typer.Context,
    requirements: Annotated[
        Path,
        typer.Option(
            "--requirements",
            "-r",
            exists=True,
            readable=True,
            resolve_path=True,
            help="Requirements file or directory.",
        ),
    ],
    requirements_adapter: RequirementsAdapter = None,
    pattern: Annotated[
        str,
        typer.Option(
            "--pattern",
            help="File pattern when loading a directory.",
        ),
    ] = "*",
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive",
            help="Search requirement directories recursively.",
        ),
    ] = False,
    requirement_id: Annotated[
        str | None,
        typer.Option("--requirement", help="Inspect one requirement ID."),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", help="Output format."),
    ] = OutputFormat.TEXT,
) -> None:
    """Inspect requirements after canonical parsing and normalization."""
    with _command(context) as runtime:
        loaded = load_requirements(
            requirements,
            adapter=requirements_adapter,
            pattern=pattern,
            recursive=recursive,
        )
        data = to_plain_data(loaded)
        if not _is_object_dict(data):
            raise TypeError("serialized requirements must be a JSON object")
        filtered = _filter_requirements(data, requirement_id)
        if requirement_id is not None and not _objects(filtered.get("requirements")):
            raise ValueError(f"unknown requirement ID: {requirement_id!r}")
        if output_format is OutputFormat.JSON:
            _print_json(filtered)
        else:
            console(runtime).print(
                render_requirements(data, requirement_id=requirement_id)
            )


@app.command("validate")
def validate_command(
    context: typer.Context,
    requirements: Annotated[
        Path | None,
        typer.Option(
            "--requirements",
            "-r",
            exists=True,
            readable=True,
            resolve_path=True,
            help="Requirements file or directory.",
            rich_help_panel="Inputs",
        ),
    ] = None,
    state_models: Annotated[
        Path | None,
        typer.Option(
            "--state-models",
            "-s",
            exists=True,
            readable=True,
            resolve_path=True,
            help="State-model file or directory.",
            rich_help_panel="Inputs",
        ),
    ] = None,
    requirements_adapter: RequirementsAdapter = None,
    state_model_adapter: StateModelAdapter = None,
    requirements_pattern: Annotated[
        str, typer.Option(help="File pattern for a requirements directory.")
    ] = "*",
    state_model_pattern: Annotated[
        str, typer.Option(help="File pattern for a state-model directory.")
    ] = "*",
    recursive: Annotated[
        bool,
        typer.Option("--recursive", help="Search input directories recursively."),
    ] = False,
    output_format: Annotated[
        OutputFormat, typer.Option("--format", help="Output format.")
    ] = OutputFormat.TEXT,
) -> None:
    """Validate that inputs parse into canonical TESTAR Trace models."""
    with _command(context) as runtime:
        if requirements is None and state_models is None:
            raise ValueError("provide --requirements, --state-models, or both")
        loaded_requirements = (
            load_requirements(
                requirements,
                adapter=requirements_adapter,
                pattern=requirements_pattern,
                recursive=recursive,
            )
            if requirements is not None
            else None
        )
        loaded_models = (
            load_state_models(
                state_models,
                adapter=state_model_adapter,
                pattern=state_model_pattern,
                recursive=recursive,
            )
            if state_models is not None
            else None
        )
        if output_format is OutputFormat.JSON:
            _print_json(
                {
                    "valid": True,
                    "requirements": _requirement_counts(loaded_requirements),
                    "state_models": _state_model_counts(loaded_models),
                }
            )
        else:
            console(runtime).print(
                render_validation(
                    requirements=loaded_requirements,
                    state_models=loaded_models,
                )
            )


@app.command("analyze")
def analyze_command(
    context: typer.Context,
    requirements: Annotated[
        Path,
        typer.Option(
            "--requirements",
            "-r",
            exists=True,
            readable=True,
            resolve_path=True,
            help="Requirements file or directory.",
            rich_help_panel="Inputs",
        ),
    ],
    state_models: StateModelsPath,
    method: Annotated[
        str,
        typer.Option("--method", "-m", help="Traceability method ID."),
    ] = "graph-alignment",
    requirements_adapter: RequirementsAdapter = None,
    state_model_adapter: StateModelAdapter = None,
    requirements_pattern: Annotated[
        str,
        typer.Option(
            "--requirements-pattern",
            help="File pattern for a requirements directory.",
            rich_help_panel="Input adapters",
        ),
    ] = "*",
    state_model_pattern: Annotated[
        str,
        typer.Option(
            "--state-model-pattern",
            help="File pattern for a state-model directory.",
            rich_help_panel="Input adapters",
        ),
    ] = "*",
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive",
            help="Search input directories recursively.",
            rich_help_panel="Input adapters",
        ),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write the full report as JSON."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Replace an existing output file."),
    ] = False,
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", help="Standard-output format."),
    ] = OutputFormat.TEXT,
    detail: Annotated[
        DetailLevel,
        typer.Option("--detail", help="Human-readable report detail."),
    ] = DetailLevel.REQUIREMENTS,
    requirement_id: Annotated[
        str | None,
        typer.Option("--requirement", help="Focus on one requirement ID."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(min=0, help="Maximum rows per full-detail evidence table."),
    ] = 20,
    all_rows: Annotated[
        bool,
        typer.Option("--all", help="Show every full-detail evidence row."),
    ] = False,
    fail_on_incomplete: Annotated[
        bool,
        typer.Option(
            "--fail-on-incomplete",
            help="Exit with status 1 when any requirement is incomplete.",
        ),
    ] = False,
    fail_on_not_assessable: Annotated[
        bool,
        typer.Option(
            "--fail-on-not-assessable",
            help="Exit with status 1 when any requirement is not assessable.",
        ),
    ] = False,
) -> None:
    """Run one traceability method and establish requirements completeness."""
    with _command(context) as runtime:
        requirement_set = load_requirements(
            requirements,
            adapter=requirements_adapter,
            pattern=requirements_pattern,
            recursive=recursive,
        )
        state_model_collection = load_state_models(
            state_models,
            adapter=state_model_adapter,
            pattern=state_model_pattern,
            recursive=recursive,
        )
        selected_method = _method(method)
        with analysis_progress(
            runtime, description=f"Running {selected_method.name}"
        ) as trace_context:
            result = analyze_traceability(
                requirement_set,
                state_model_collection,
                method=selected_method,
                context=trace_context,
            )
        report = to_plain_data(result)
        if not _is_object_dict(report):
            raise TypeError("serialized analysis result must be a JSON object")
        if output is not None:
            write_json(output, report, overwrite=force)
            if not runtime.quiet:
                console(runtime, stderr=True).print(f"[green]Wrote[/green] {output}")

        effective_detail = DetailLevel.FULL if all_rows else detail
        if not runtime.quiet:
            if output_format is OutputFormat.JSON:
                _print_json(_report_json_view(report, effective_detail, requirement_id))
            else:
                console(runtime).print(
                    render_report(
                        report,
                        detail=effective_detail.value,
                        requirement_id=requirement_id,
                        limit=None if all_rows else limit,
                    )
                )
        _enforce_result_policy(
            report,
            fail_on_incomplete=fail_on_incomplete,
            fail_on_not_assessable=fail_on_not_assessable,
        )


@app.command("report")
def report_command(
    context: typer.Context,
    report: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    output_format: Annotated[
        OutputFormat, typer.Option("--format", help="Output format.")
    ] = OutputFormat.TEXT,
    detail: Annotated[
        DetailLevel, typer.Option("--detail", help="Report detail.")
    ] = DetailLevel.REQUIREMENTS,
    requirement_id: Annotated[
        str | None,
        typer.Option("--requirement", help="Focus on one requirement ID."),
    ] = None,
    limit: Annotated[
        int, typer.Option(min=0, help="Maximum rows per evidence table.")
    ] = 20,
    all_rows: Annotated[
        bool, typer.Option("--all", help="Show all evidence rows.")
    ] = False,
) -> None:
    """Inspect a previously exported TESTAR Trace report."""
    with _command(context) as runtime:
        data = load_json_file(report)
        if not _is_object_dict(data):
            raise ValueError("report file must contain a JSON object")
        effective_detail = DetailLevel.FULL if all_rows else detail
        if output_format is OutputFormat.JSON:
            _print_json(_report_json_view(data, effective_detail, requirement_id))
        else:
            console(runtime).print(
                render_report(
                    data,
                    detail=effective_detail.value,
                    requirement_id=requirement_id,
                    limit=None if all_rows else limit,
                )
            )


@app.command("compare")
def compare_command(
    context: typer.Context,
    requirements: Annotated[
        Path,
        typer.Option(
            "--requirements",
            "-r",
            exists=True,
            readable=True,
            resolve_path=True,
            help="Requirements file or directory.",
            rich_help_panel="Inputs",
        ),
    ],
    state_models: StateModelsPath,
    labels: Annotated[
        Path,
        typer.Option(
            "--labels",
            "-l",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help="Independent completeness-reference labels JSON.",
            rich_help_panel="Inputs",
        ),
    ],
    methods: Annotated[
        list[str] | None,
        typer.Option(
            "--method", "-m", help="Method ID; repeat to compare multiple methods."
        ),
    ] = None,
    requirements_adapter: RequirementsAdapter = None,
    state_model_adapter: StateModelAdapter = None,
    requirements_pattern: Annotated[str, typer.Option()] = "*",
    state_model_pattern: Annotated[str, typer.Option()] = "*",
    recursive: Annotated[
        bool,
        typer.Option("--recursive", help="Search input directories recursively."),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write comparison metrics as JSON."),
    ] = None,
    force: Annotated[
        bool, typer.Option("--force", help="Replace an existing output file.")
    ] = False,
    output_format: Annotated[
        OutputFormat, typer.Option("--format", help="Standard-output format.")
    ] = OutputFormat.TEXT,
    fail_under: Annotated[
        float | None,
        typer.Option(
            min=0.0,
            max=1.0,
            help="Fail when any method's macro F1 is below this value.",
        ),
    ] = None,
) -> None:
    """Compare methods against independently curated completeness labels."""
    with _command(context) as runtime:
        selected_ids = methods or ["graph-alignment", "execution-alignment"]
        if len(set(selected_ids)) != len(selected_ids):
            raise ValueError("each comparison method must be specified once")
        selected_methods = tuple(_method(method_id) for method_id in selected_ids)
        requirement_set = load_requirements(
            requirements,
            adapter=requirements_adapter,
            pattern=requirements_pattern,
            recursive=recursive,
        )
        state_model_collection = load_state_models(
            state_models,
            adapter=state_model_adapter,
            pattern=state_model_pattern,
            recursive=recursive,
        )
        reference_labels = load_reference_labels(labels)
        comparisons: list[MethodComparison] = []
        for selected_method in selected_methods:
            with analysis_progress(
                runtime, description=f"Evaluating {selected_method.name}"
            ) as trace_context:
                comparisons.append(
                    compare_method(
                        requirement_set,
                        state_model_collection,
                        selected_method,
                        reference_labels,
                        context=trace_context,
                    )
                )
        data = {
            "schema_version": 1,
            "reference_label_count": len(reference_labels),
            "methods": [to_plain_data(item) for item in comparisons],
        }
        if output is not None:
            write_json(output, data, overwrite=force)
            if not runtime.quiet:
                console(runtime, stderr=True).print(f"[green]Wrote[/green] {output}")
        if not runtime.quiet:
            if output_format is OutputFormat.JSON:
                _print_json(data)
            else:
                console(runtime).print(render_comparisons(comparisons))
        if fail_under is not None and any(
            item.evaluation.macro_f1 < fail_under for item in comparisons
        ):
            raise typer.Exit(code=1)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code for console entry points."""
    try:
        app(args=argv, prog_name=APP_NAME, standalone_mode=True)
    except SystemExit as error:
        return error.code if isinstance(error.code, int) else 1
    return 0


@contextmanager
def _command(context: typer.Context) -> Iterator[RuntimeOptions]:
    runtime = get_runtime(context)
    try:
        yield runtime
    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console(runtime, stderr=True).print("\n[yellow]Analysis cancelled.[/yellow]")
        raise typer.Exit(code=130) from None
    except Exception as error:
        if runtime.debug:
            raise
        logger.debug("CLI command failed", exc_info=True)
        message = _friendly_error(error)
        console(runtime, stderr=True).print(
            Panel(Text(message), title="Command failed", border_style="red")
        )
        raise typer.Exit(code=1) from None


def _method(method_id: str):
    registry = create_builtin_method_registry()
    try:
        selected = registry.get(method_id)
    except ValueError as error:
        raise ValueError(f"invalid traceability method ID: {method_id!r}") from error
    if selected is None:
        available = ", ".join(item.id for item in registry)
        raise ValueError(
            f"unknown traceability method {method_id!r}; choose from: {available}"
        )
    return selected


def _print_json(value: object) -> None:
    sys.stdout.write(dumps_json(value) + "\n")


def _friendly_error(error: Exception) -> str:
    if isinstance(error, json.JSONDecodeError):
        return f"Invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}"
    if isinstance(error, FileExistsError):
        return f"{error}\n\nUse --force to replace the existing file."
    if isinstance(error, OSError):
        return f"Could not access an input or output file: {error}"
    return str(error) or type(error).__name__


def _enforce_result_policy(
    report: Mapping[str, object],
    *,
    fail_on_incomplete: bool,
    fail_on_not_assessable: bool,
) -> None:
    summary = report.get("summary")
    if not _is_object_dict(summary):
        return
    failed = (
        fail_on_incomplete and _count(summary.get("incomplete_requirements")) > 0
    ) or (
        fail_on_not_assessable
        and _count(summary.get("not_assessable_requirements")) > 0
    )
    if failed:
        raise typer.Exit(code=1)


def _report_json_view(
    report: dict[str, object],
    detail: DetailLevel,
    requirement_id: str | None,
) -> object:
    if detail is DetailLevel.SUMMARY:
        return report.get("summary", {})
    return _filter_report(report, requirement_id) if requirement_id else report


def _filter_requirements(
    data: dict[str, object], requirement_id: str | None
) -> dict[str, object]:
    if requirement_id is None:
        return data
    filtered = dict(data)
    for key in ("requirements", "elements", "flows"):
        value = data.get(key)
        if not isinstance(value, list):
            continue
        filtered[key] = [
            item
            for item in value
            if _is_object_dict(item)
            and (
                item.get("id") == requirement_id
                if key == "requirements"
                else item.get("requirement_id") == requirement_id
            )
        ]
    return filtered


def _filter_report(report: dict[str, object], requirement_id: str) -> dict[str, object]:
    filtered = dict(report)
    for key in ("assessments", "links", "occurrences"):
        value = report.get(key)
        if isinstance(value, list):
            filtered[key] = [
                item
                for item in value
                if _is_object_dict(item)
                and _belongs_to_requirement(item, requirement_id)
            ]
    path_materialization = report.get("path_materialization")
    if _is_object_dict(path_materialization):
        filtered_paths = dict(path_materialization)
        paths = path_materialization.get("paths")
        if isinstance(paths, list):
            filtered_paths["paths"] = [
                item
                for item in paths
                if _is_object_dict(item)
                and item.get("requirement_id") == requirement_id
            ]
        filtered["path_materialization"] = filtered_paths
    return filtered


def _belongs_to_requirement(item: dict[str, object], requirement_id: str) -> bool:
    if item.get("requirement_id") == requirement_id:
        return True
    requirement_ids = item.get("requirement_ids")
    return isinstance(requirement_ids, list) and requirement_id in requirement_ids


def _requirement_counts(requirements: RequirementSet | None) -> object:
    if requirements is None:
        return None
    return {
        "requirements": len(requirements.requirements),
        "elements": len(requirements.elements),
        "flows": len(requirements.flows),
    }


def _state_model_counts(state_models: StateModelCollection | None) -> object:
    if state_models is None:
        return None
    return {"models": len(state_models.models)}


def _objects(value: object) -> list[dict[str, object]]:
    return (
        [item for item in value if _is_object_dict(item)]
        if isinstance(value, list)
        else []
    )


def _count(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _is_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)
