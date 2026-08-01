"""Infrastructure-layer exceptions."""

from __future__ import annotations


class InfrastructureError(Exception):
    """Base exception for infrastructure adapter failures."""


class ReportSerializationError(InfrastructureError):
    """Raised when a traceability report cannot be serialized to disk."""


class ReportDeserializationError(InfrastructureError):
    """Raised when a traceability report cannot be read or parsed from disk."""


class RunHistoryPersistenceError(InfrastructureError):
    """Raised when run history entries cannot be persisted or loaded."""
