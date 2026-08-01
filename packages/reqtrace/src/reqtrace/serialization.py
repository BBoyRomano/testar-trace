"""Serialization helpers for ReqTrace model objects."""

import dataclasses
import json
from collections.abc import Mapping
from datetime import date, datetime, time
from enum import Enum
from pathlib import Path
from typing import Any

__all__ = ["dumps_json", "to_plain_data"]


def to_plain_data(value: Any) -> Any:
    """Convert supported model objects into JSON-compatible plain data."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if dataclasses.is_dataclass(value):
        return {
            field.name: to_plain_data(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }
    if isinstance(value, Mapping):
        return {str(key): to_plain_data(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set | frozenset):
        return [to_plain_data(item) for item in value]
    if isinstance(value, datetime | date | time):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    return value


def dumps_json(data: Any) -> str:
    """Serialize supported model objects as formatted JSON."""
    return json.dumps(to_plain_data(data), ensure_ascii=False, indent=2)
