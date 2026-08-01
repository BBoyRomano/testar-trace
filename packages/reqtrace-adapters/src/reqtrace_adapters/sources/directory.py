"""Local directory sources."""

from dataclasses import dataclass
from pathlib import Path

from reqtrace_adapters.sources.base import SourceInput
from reqtrace_adapters.sources.file import FileSource

__all__ = ["DirectorySource"]


@dataclass(frozen=True, slots=True)
class DirectorySource:
    """A source backed by multiple local files."""

    path: str | Path
    pattern: str = "*"
    recursive: bool = False

    def load(self) -> tuple[SourceInput, ...]:
        """Load all matching files as raw inputs."""
        directory = Path(self.path)
        if not directory.is_dir():
            raise NotADirectoryError(directory)

        paths = (
            directory.rglob(self.pattern)
            if self.recursive
            else directory.glob(self.pattern)
        )

        inputs: list[SourceInput] = []
        for file_path in sorted(paths):
            if file_path.is_file():
                inputs.extend(FileSource(file_path).load())

        return tuple(inputs)
