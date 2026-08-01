"""Local file sources."""

import json
from dataclasses import dataclass
from pathlib import Path

from reqtrace_adapters._utils import normalize_format
from reqtrace_adapters.sources.base import SourceInput

__all__ = ["FileSource"]


@dataclass(frozen=True, slots=True)
class FileSource:
    """A source backed by one local file."""

    path: str | Path

    def load(self) -> tuple[SourceInput, ...]:
        """Load this file as one raw input."""
        path = Path(self.path)
        if path.is_dir():
            raise IsADirectoryError(path)

        input_format = normalize_format(path.suffix)
        data = _load_json(path) if input_format == "json" else _read_text(path)

        return (
            SourceInput(
                data=data,
                name=path.name,
                format=input_format,
                uri=str(path),
            ),
        )


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
