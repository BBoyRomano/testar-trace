"""Serialization helpers for CLI output."""

import json
from pathlib import Path
from typing import Any

from reqtrace.serialization import dumps_json, to_plain_data

__all__ = ["dumps_json", "load_json_file", "to_plain_data", "write_json"]


def write_json(path: Path, data: Any) -> None:
    """Write JSON output to a path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps_json(data) + "\n", encoding="utf-8")


def load_json_file(path: Path) -> Any:
    """Load plain JSON data from a file."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
