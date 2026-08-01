"""Trace method registry for ReqTrace."""

from collections.abc import Callable

from reqtrace.models.evidence import EvidenceSet
from reqtrace.models.requirements import RequirementSet
from reqtrace.models.traceability import TraceabilityResult
from reqtrace.progress import TraceContext

__all__ = [
    "TraceMethod",
    "available_trace_methods",
    "get_trace_method",
    "register_trace_method",
]

TraceMethod = Callable[[RequirementSet, EvidenceSet, TraceContext], TraceabilityResult]

_TRACE_METHODS: dict[str, TraceMethod] = {}


def register_trace_method(
    name: str,
    method: TraceMethod,
    *,
    replace: bool = False,
) -> None:
    """Register a traceability method."""
    if not callable(method):
        raise TypeError("method must be callable")

    key = _normalize_method_name(name)
    if not replace and key in _TRACE_METHODS:
        raise ValueError(f"Trace method already registered: {key}")

    _TRACE_METHODS[key] = method


def get_trace_method(name: str) -> TraceMethod | None:
    """Return a registered traceability method, if present."""
    return _TRACE_METHODS.get(_normalize_method_name(name))


def available_trace_methods() -> tuple[str, ...]:
    """Return registered traceability method names."""
    return tuple(sorted(_TRACE_METHODS))


def _normalize_method_name(name: str) -> str:
    return name.strip().lower().replace("_", "-").replace(" ", "-")
