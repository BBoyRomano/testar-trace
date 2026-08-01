"""Common models shared across ReqTrace."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType

__all__ = [
    "SourceRef",
    "SourceType",
    "freeze_metadata",
]


class SourceType(StrEnum):
    """Kinds of original sources represented in canonical models."""

    FILE = "file"
    API = "api"
    IMPORT = "import"
    GENERATED = "generated"


@dataclass(slots=True, frozen=True)
class SourceRef:
    """Reference to the original source of canonical data."""

    source_type: SourceType
    source_name: str
    native_id: str | None = None
    path_or_uri: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_name.strip():
            raise ValueError("SourceRef.source_name must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


def freeze_metadata(metadata: Mapping[str, object]) -> Mapping[str, object]:
    """Return an immutable shallow copy of metadata."""
    return MappingProxyType(dict(metadata))
