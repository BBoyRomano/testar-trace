"""Execution context, progress reporting, and cancellation for tracing."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from threading import Event
from types import MappingProxyType

__all__ = [
    "CancellationToken",
    "ProgressCallback",
    "ProgressEvent",
    "TraceCancelledError",
    "TraceContext",
]


class TraceCancelledError(RuntimeError):
    """Raised when trace execution is cancelled."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ProgressEvent:
    """A structured progress event emitted during trace execution."""

    phase: str
    message: str | None = None
    completed: int | None = None
    total: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.phase, str):
            raise TypeError("phase must be a string")

        if not self.phase:
            raise ValueError("phase must not be empty")

        if self.phase != self.phase.strip():
            raise ValueError("phase must not start or end with whitespace")

        if self.message is not None and not isinstance(self.message, str):
            raise TypeError("message must be a string or None")

        _validate_progress_value("completed", self.completed)
        _validate_progress_value("total", self.total)

        if (
            self.completed is not None
            and self.total is not None
            and self.completed > self.total
        ):
            raise ValueError("completed must not be greater than total")

        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata),
        )


type ProgressCallback = Callable[[ProgressEvent], None]


class CancellationToken:
    """Cooperative cancellation state shared with trace execution."""

    __slots__ = ("_event",)

    def __init__(self) -> None:
        self._event = Event()

    @property
    def cancelled(self) -> bool:
        """Whether cancellation has been requested."""
        return self._event.is_set()

    def cancel(self) -> None:
        """Request cancellation."""
        self._event.set()

    def raise_if_cancelled(self) -> None:
        """Raise when cancellation has been requested."""
        if self.cancelled:
            raise TraceCancelledError("trace execution was cancelled")


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class TraceContext:
    """Runtime context passed to trace methods."""

    progress: ProgressCallback | None = None
    cancellation: CancellationToken = field(default_factory=CancellationToken)

    def __post_init__(self) -> None:
        if self.progress is not None and not callable(self.progress):
            raise TypeError("progress must be callable or None")

    def report(
        self,
        phase: str,
        *,
        message: str | None = None,
        completed: int | None = None,
        total: int | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        """Emit a progress event when a callback is configured."""
        if self.progress is None:
            return

        self.progress(
            ProgressEvent(
                phase=phase,
                message=message,
                completed=completed,
                total=total,
                metadata={} if metadata is None else metadata,
            )
        )

    def raise_if_cancelled(self) -> None:
        """Raise when cancellation has been requested."""
        self.cancellation.raise_if_cancelled()


def _validate_progress_value(
    field_name: str,
    value: int | None,
) -> None:
    if value is None:
        return

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer or None")

    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _freeze_mapping(
    value: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError("metadata must be a mapping")

    return MappingProxyType(dict(value))
