"""Command application and shared CLI value types."""

from enum import StrEnum
from importlib.metadata import PackageNotFoundError, version

import typer

APP_NAME = "testar-trace"


class OutputFormat(StrEnum):
    """Supported standard-output representations."""

    TEXT = "text"
    JSON = "json"


class DetailLevel(StrEnum):
    """Amount of human-readable report detail to render."""

    SUMMARY = "summary"
    REQUIREMENTS = "requirements"
    FULL = "full"


app = typer.Typer(
    name=APP_NAME,
    help="Establish requirements completeness in TESTAR state models.",
    epilog="Run 'testar-trace COMMAND --help' for command-specific examples.",
    no_args_is_help=True,
    invoke_without_command=True,
    add_completion=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def cli_version() -> str:
    """Return the installed CLI version string."""
    try:
        package_version = version("testar-trace-cli")
    except PackageNotFoundError:
        package_version = "0.0.0"
    return f"TESTAR Trace CLI {package_version}"
