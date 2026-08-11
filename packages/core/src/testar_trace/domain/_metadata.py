"""Immutable metadata support for canonical domain models."""

from collections.abc import Mapping
from math import isfinite
from types import MappingProxyType
from typing import cast

type MetadataScalar = str | int | float | bool | None
type FrozenData = MetadataScalar | tuple[FrozenData, ...] | Mapping[str, FrozenData]
type FrozenMetadata = Mapping[str, FrozenData]


def freeze_metadata(
    metadata: Mapping[str, object],
) -> FrozenMetadata:
    """Return a deeply immutable copy of JSON-compatible metadata."""
    frozen = freeze_data(metadata)

    if not isinstance(frozen, Mapping):
        raise TypeError("metadata must be a mapping")

    return cast(FrozenMetadata, frozen)


def freeze_data(value: object) -> FrozenData:
    """Freeze JSON-compatible data into immutable containers."""
    if value is None or isinstance(value, str | bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("metadata numbers must be finite")
        return value

    if isinstance(value, Mapping):
        items: list[tuple[str, object]] = []

        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("metadata keys must be strings")
            items.append((key, item))

        frozen_items = {key: freeze_data(item) for key, item in sorted(items)}
        return MappingProxyType(frozen_items)

    if isinstance(value, list | tuple):
        return tuple(freeze_data(item) for item in value)

    raise TypeError(
        "metadata values must be JSON-compatible scalars, mappings, lists, or tuples"
    )
