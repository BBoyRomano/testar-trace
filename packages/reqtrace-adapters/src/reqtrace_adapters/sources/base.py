"""Source protocol and raw input model."""

from dataclasses import dataclass
from typing import Protocol

__all__ = ["Source", "SourceInput"]


@dataclass(frozen=True, slots=True)
class SourceInput:
    """Raw input loaded from an external source."""

    data: object
    name: str
    format: str
    uri: str | None = None


class Source(Protocol):
    """A source that can load one or more raw inputs."""

    def load(self) -> tuple[SourceInput, ...]:
        """Load raw inputs."""
