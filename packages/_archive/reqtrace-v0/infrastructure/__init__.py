"""Infrastructure adapters (serialization/persistence, external boundaries)."""

from .exceptions import (
    InfrastructureError,
    ReportDeserializationError,
    ReportSerializationError,
    RunHistoryPersistenceError,
)

__all__ = [
    "InfrastructureError",
    "ReportSerializationError",
    "ReportDeserializationError",
    "RunHistoryPersistenceError",
]
