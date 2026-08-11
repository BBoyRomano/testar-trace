"""Terminal runtime configuration and progress presentation."""

import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from testar_trace import ProgressEvent, TraceContext


@dataclass(frozen=True, slots=True, kw_only=True)
class RuntimeOptions:
    """Global behavior selected for one CLI invocation."""

    verbose: int = 0
    quiet: bool = False
    no_color: bool | None = None
    progress: bool = True
    debug: bool = False


def get_runtime(context) -> RuntimeOptions:
    """Return the initialized runtime from a Typer context."""
    runtime = context.ensure_object(RuntimeOptions)
    if not isinstance(runtime, RuntimeOptions):
        raise TypeError("CLI context does not contain RuntimeOptions")
    return runtime


def console(runtime: RuntimeOptions, *, stderr: bool = False) -> Console:
    """Create a console that respects global color and output settings."""
    return Console(
        file=sys.stderr if stderr else sys.stdout,
        stderr=stderr,
        no_color=runtime.no_color,
        color_system=None if runtime.no_color else "auto",
        highlight=False,
        soft_wrap=False,
    )


@contextmanager
def analysis_progress(
    runtime: RuntimeOptions,
    *,
    description: str,
) -> Iterator[TraceContext]:
    """Yield a trace context connected to a terminal-aware progress display."""
    error_console = console(runtime, stderr=True)
    interactive = (
        runtime.progress
        and not runtime.quiet
        and error_console.is_terminal
        and os.environ.get("CI") is None
    )
    if not interactive:
        yield TraceContext(progress=_verbose_progress(runtime, error_console))
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        console=error_console,
        transient=True,
    ) as progress:
        task_id = progress.add_task(description, total=None)

        def update(event: ProgressEvent) -> None:
            task_description = event.message or _humanize_phase(event.phase)
            progress.update(
                task_id,
                description=task_description,
                completed=event.completed,
                total=event.total,
            )

        yield TraceContext(progress=update)


def _verbose_progress(runtime: RuntimeOptions, error_console: Console):
    if runtime.verbose < 2 or runtime.quiet:
        return None

    def report(event: ProgressEvent) -> None:
        message = event.message or _humanize_phase(event.phase)
        counts = (
            f" ({event.completed}/{event.total})"
            if event.completed is not None and event.total is not None
            else ""
        )
        error_console.print(f"[dim]{message}{counts}[/dim]")

    return report


def _humanize_phase(phase: str) -> str:
    return phase.replace(".", " ").replace("-", " ").capitalize()
