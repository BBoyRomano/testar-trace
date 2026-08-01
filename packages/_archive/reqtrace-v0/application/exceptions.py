"""Application-layer exceptions for traceability execution."""

from __future__ import annotations


class TraceabilityError(Exception):
    """Base exception for application-level traceability failures."""


class InvalidTraceabilityRequestError(TraceabilityError):
    """Raised when a request cannot be executed (missing keys, unknown IDs, etc.)."""


class UnknownTraceabilityMethodError(TraceabilityError):
    """Raised when a requested traceability method is not registered."""


class TraceabilityMethodExecutionError(TraceabilityError):
    """Raised when a method fails unexpectedly."""


class RunCanceledError(TraceabilityError):
    """Raised when a traceability run is canceled by the user."""


class RunHistoryError(TraceabilityError):
    """Base exception for run history management failures."""


class RunHistoryEntryNotFoundError(RunHistoryError):
    """Raised when a run history entry cannot be found."""
