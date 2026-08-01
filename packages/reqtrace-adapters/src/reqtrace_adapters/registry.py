"""Parser callable registry for ReqTrace adapters."""

# ruff: noqa: A002

from collections.abc import Callable

from reqtrace_adapters._utils import normalize_format, normalize_key
from reqtrace_adapters.sources.base import SourceInput

__all__ = [
    "ParserFunction",
    "available_parsers",
    "get_parser",
    "register_builtin_parser",
    "register_parser",
]

ParserFunction = Callable[[SourceInput], object]

_PARSERS: dict[tuple[str, str, str], ParserFunction] = {}


def register_builtin_parser(
    artifact: str,
    kind: str,
    format: str,
    parser: ParserFunction,
    *,
    replace: bool = False,
) -> None:
    """Register a built-in parser callable."""
    register_parser(artifact, kind, format, parser, replace=replace)


def register_parser(
    artifact: str,
    kind: str,
    format: str,
    parser: ParserFunction,
    *,
    replace: bool = False,
) -> None:
    """Register a parser callable."""
    if not callable(parser):
        raise TypeError("parser must be callable")

    key = _parser_key(artifact, kind, format)

    if not replace and key in _PARSERS:
        raise ValueError(f"Parser already registered for {'/'.join(key)}.")

    _PARSERS[key] = parser


def get_parser(artifact: str, kind: str, format: str) -> ParserFunction | None:
    """Return a registered parser callable, if present."""
    return _PARSERS.get(_parser_key(artifact, kind, format))


def available_parsers() -> tuple[tuple[str, str, str], ...]:
    """Return registered parser keys."""
    return tuple(sorted(_PARSERS))


def _parser_key(artifact: str, kind: str, format: str) -> tuple[str, str, str]:
    return (
        normalize_key(artifact),
        normalize_key(kind),
        normalize_format(format),
    )
