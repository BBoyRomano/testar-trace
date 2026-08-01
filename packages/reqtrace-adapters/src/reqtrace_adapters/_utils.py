"""Small shared helpers for ReqTrace adapters."""

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING

from reqtrace.models.common import SourceRef, SourceType

if TYPE_CHECKING:
    from reqtrace_adapters.sources.base import SourceInput

__all__ = [
    "freeze_metadata",
    "normalize_format",
    "normalize_key",
    "slugify",
    "source_ref_from_source",
]


def freeze_metadata(metadata: Mapping[str, object]) -> Mapping[str, object]:
    """Return an immutable shallow copy of metadata."""
    return MappingProxyType(dict(metadata))


def normalize_key(value: str) -> str:
    """Normalize an artifact, kind, or source key."""
    return value.strip().lower().replace("_", "-").replace(" ", "-")


def normalize_format(value: str) -> str:
    """Normalize a raw input format key."""
    return normalize_key(value).removeprefix(".")


def slugify(value: str, *, fallback: str = "item") -> str:
    """Return a stable lowercase identifier fragment."""
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-{2,}", "-", lowered).strip("-")
    return lowered or fallback


def source_ref_from_source(source: "SourceInput") -> SourceRef:
    """Create a canonical source reference from raw source input."""
    return SourceRef(
        source_type=_source_type(source),
        source_name=source.name,
        path_or_uri=source.uri,
    )


def _source_type(source: "SourceInput") -> SourceType:
    if source.uri is None:
        return SourceType.IMPORT
    if _looks_like_api_uri(source.uri):
        return SourceType.API
    return SourceType.FILE


def _looks_like_api_uri(uri: str) -> bool:
    return "://" in uri or uri.startswith(
        ("jira:",),
    )
