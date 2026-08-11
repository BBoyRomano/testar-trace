"""Serialization helpers for CLI output."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from testar_trace.serialization import to_plain_data as canonical_to_plain_data

__all__ = ["dumps_json", "load_json_file", "to_plain_data", "write_json"]


def to_plain_data(value: object) -> object:
    """Convert canonical values to JSON-compatible plain data."""
    if isinstance(value, Path):
        return str(value)
    return canonical_to_plain_data(value)


def dumps_json(value: object) -> str:
    """Serialize a canonical or plain value as stable readable JSON."""
    return json.dumps(
        to_plain_data(value), ensure_ascii=False, indent=2, sort_keys=True
    )


def write_json(path: Path, data: Any, *, overwrite: bool = False) -> None:
    """Atomically write JSON output without replacing files by default."""
    if path.exists() and not overwrite:
        raise FileExistsError(f"output file already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as file:
            file.write(dumps_json(data) + "\n")
        temporary_path.replace(path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def load_json_file(path: Path) -> Any:
    """Load plain JSON data from a file."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
