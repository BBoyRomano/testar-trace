"""Logging configuration for diagnostic CLI output."""

import logging

from rich.logging import RichHandler

from ._runtime import RuntimeOptions, console


def configure_logging(runtime: RuntimeOptions) -> None:
    """Configure deterministic stderr logging for the requested verbosity."""
    level = (
        logging.DEBUG
        if runtime.verbose >= 2
        else logging.INFO
        if runtime.verbose
        else logging.WARNING
    )
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[
            RichHandler(
                console=console(runtime, stderr=True),
                show_path=runtime.verbose >= 2,
                show_time=False,
                rich_tracebacks=runtime.debug,
                markup=False,
            )
        ],
        force=True,
    )
