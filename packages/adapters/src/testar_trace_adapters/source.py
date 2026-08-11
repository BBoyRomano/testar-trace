"""Raw source artifacts accepted by TESTAR Trace adapters."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from testar_trace.domain.provenance import SourceRef, SourceType

__all__ = [
    "Source",
    "SourceArtifact",
    "SourceValue",
    "read_source_artifacts",
]


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceArtifact:
    """One loaded external artifact and its source identity."""

    id: str
    name: str
    data: object
    format: str
    uri: str | None = None
    source_type: SourceType = SourceType.IMPORT

    def __post_init__(self) -> None:
        for field_name in ("id", "name", "format"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string")
            if not value.strip():
                raise ValueError(f"{field_name} must not be blank")
            if value != value.strip():
                raise ValueError(f"{field_name} must not have surrounding whitespace")

        if self.uri is not None:
            if not isinstance(self.uri, str):
                raise TypeError("uri must be a string or None")
            if not self.uri.strip():
                raise ValueError("uri must not be blank")

        if not isinstance(self.source_type, SourceType):
            raise TypeError("source_type must be a SourceType")

        object.__setattr__(self, "format", _normalize_format(self.format))

    def source_ref(
        self,
        *,
        native_id: str | None = None,
        element_kind: str | None = None,
        container_id: str | None = None,
        location: str | None = None,
    ) -> SourceRef:
        """Create a canonical reference back to this source artifact."""
        return SourceRef(
            source_type=self.source_type,
            source_name=self.name,
            artifact_id=self.id,
            native_id=native_id,
            element_kind=element_kind,
            container_id=container_id,
            location=location,
            path_or_uri=self.uri,
        )


class Source(Protocol):
    """A synchronous provider of one or more source artifacts."""

    def read(self) -> Iterable[SourceArtifact]:
        """Read source artifacts."""


type SourceItem = str | Path | SourceArtifact
type SourceValue = SourceItem | Source | Iterable[SourceItem]


def read_source_artifacts(
    source: SourceValue,
    *,
    pattern: str = "*",
    recursive: bool = False,
) -> tuple[SourceArtifact, ...]:
    """Read paths, in-memory artifacts, or a custom source provider."""
    if isinstance(source, SourceArtifact):
        return (source,)
    if isinstance(source, str | Path):
        return _read_path(Path(source), pattern=pattern, recursive=recursive)

    read = getattr(source, "read", None)
    if callable(read):
        artifacts = tuple(read())
        _require_artifacts(artifacts)
        return artifacts

    if not isinstance(source, Iterable):
        raise TypeError("source must be a path, SourceArtifact, Source, or iterable")

    artifacts: list[SourceArtifact] = []
    for item in source:
        if isinstance(item, SourceArtifact):
            artifacts.append(item)
        elif isinstance(item, str | Path):
            artifacts.extend(
                _read_path(Path(item), pattern=pattern, recursive=recursive)
            )
        else:
            raise TypeError(
                "source iterables may contain only paths or SourceArtifact values"
            )

    result = tuple(artifacts)
    _require_artifacts(result)
    return result


def _read_path(
    path: Path,
    *,
    pattern: str,
    recursive: bool,
) -> tuple[SourceArtifact, ...]:
    if path.is_file():
        return (_read_file(path, artifact_id=path.name),)
    if not path.is_dir():
        raise FileNotFoundError(path)

    paths = path.rglob(pattern) if recursive else path.glob(pattern)
    files = tuple(sorted(item for item in paths if item.is_file()))
    if not files:
        raise ValueError(f"source directory contains no matching files: {path}")
    return tuple(
        _read_file(item, artifact_id=item.relative_to(path).as_posix())
        for item in files
    )


def _read_file(path: Path, *, artifact_id: str) -> SourceArtifact:
    return SourceArtifact(
        id=artifact_id,
        name=path.name,
        data=path.read_text(encoding="utf-8"),
        format=path.suffix.removeprefix("."),
        uri=str(path),
        source_type=SourceType.FILE,
    )


def _require_artifacts(artifacts: tuple[SourceArtifact, ...]) -> None:
    if not artifacts:
        raise ValueError("source must provide at least one artifact")
    if any(not isinstance(artifact, SourceArtifact) for artifact in artifacts):
        raise TypeError("Source.read() must return SourceArtifact values")


def _normalize_format(value: str) -> str:
    normalized = value.strip().casefold().removeprefix(".")
    if not normalized:
        raise ValueError("format must not be blank")
    return normalized
