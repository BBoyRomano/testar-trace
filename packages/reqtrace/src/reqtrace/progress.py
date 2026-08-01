"""Progress and cancellation helpers for traceability analysis."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

__all__ = [
    "CancellationToken",
    "ProgressEvent",
    "ProgressReporter",
    "TraceContext",
]

ProgressReporter = Callable[["ProgressEvent"], None]


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    """A structured progress event emitted during analysis."""

    phase: str
    message: str | None = None
    completed: int | None = None
    total: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.phase.strip():
            raise ValueError("ProgressEvent.phase must not be blank.")
        if self.completed is not None and self.completed < 0:
            raise ValueError("ProgressEvent.completed must be non-negative.")
        if self.total is not None and self.total < 0:
            raise ValueError("ProgressEvent.total must be non-negative.")
        if (
            self.completed is not None
            and self.total is not None
            and self.completed > self.total
        ):
            raise ValueError("ProgressEvent.completed must not be greater than total.")

        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(slots=True)
class CancellationToken:
    """Shared cancellation state for traceability analysis."""

    cancelled: bool = False

    def cancel(self) -> None:
        """Request cancellation."""
        self.cancelled = True

    def raise_if_cancelled(self) -> None:
        """Raise if cancellation has been requested."""
        if self.cancelled:
            raise InterruptedError("Traceability analysis was cancelled.")


@dataclass(frozen=True, slots=True)
class TraceContext:
    """Runtime context passed to trace methods."""

    progress: ProgressReporter | None = None
    cancellation: CancellationToken | None = None
    options: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "options", _freeze_mapping(self.options))

    def report(
        self,
        phase: str,
        *,
        message: str | None = None,
        completed: int | None = None,
        total: int | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        """Report progress if a reporter is configured."""
        if self.progress is None:
            return

        self.progress(
            ProgressEvent(
                phase=phase,
                message=message,
                completed=completed,
                total=total,
                metadata=metadata or {},
            ),
        )

    def raise_if_cancelled(self) -> None:
        """Raise if cancellation has been requested."""
        if self.cancellation is not None:
            self.cancellation.raise_if_cancelled()


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))
