"""Source provenance for canonical domain data."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from testar_trace.domain._metadata import freeze_metadata
from testar_trace.domain._validation import (
    require_optional_text,
    require_text,
)

__all__ = [
    "SourceRef",
    "SourceType",
]


class SourceType(StrEnum):
    """Kind of source from which canonical data originated."""

    FILE = "file"
    API = "api"
    IMPORT = "import"
    GENERATED = "generated"


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceRef:
    """Reference to the original source of canonical data."""

    source_type: SourceType
    source_name: str
    artifact_id: str | None = None
    native_id: str | None = None
    element_kind: str | None = None
    container_id: str | None = None
    location: str | None = None
    path_or_uri: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.source_name, "source_name")
        require_optional_text(self.artifact_id, "artifact_id")
        require_optional_text(self.native_id, "native_id")
        require_optional_text(self.element_kind, "element_kind")
        require_optional_text(self.container_id, "container_id")
        require_optional_text(self.location, "location")
        require_optional_text(self.path_or_uri, "path_or_uri")

        object.__setattr__(
            self,
            "metadata",
            freeze_metadata(self.metadata),
        )
