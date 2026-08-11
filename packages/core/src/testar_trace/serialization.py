"""Source-agnostic conversion of canonical values to plain JSON data."""

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum

from testar_trace.domain.traceability import TraceabilityResult

__all__ = ["to_plain_data"]


def to_plain_data(value: object) -> object:
    """Convert canonical values to JSON-compatible Python containers.

    Applications remain responsible for choosing a JSON envelope, schema
    version, formatting, and persistence behavior.
    """
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        result = {
            field.name: to_plain_data(getattr(value, field.name))
            for field in fields(value)
        }
        if isinstance(value, TraceabilityResult):
            result["summary"] = to_plain_data(value.summary)
        return result
    if isinstance(value, Mapping):
        return {str(key): to_plain_data(item) for key, item in value.items()}
    if isinstance(value, tuple | list | set | frozenset):
        return [to_plain_data(item) for item in value]
    if value is None or isinstance(value, str | int | float | bool):
        return value
    raise TypeError(f"Cannot serialize {type(value).__name__} to JSON.")
