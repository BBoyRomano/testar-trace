"""Shared validation helpers for canonical domain models."""

from collections.abc import Collection, Hashable, Iterable
from math import isfinite
from typing import Protocol


class _Identified(Protocol):
    @property
    def id(self) -> str: ...


def require_text(value: object, field_name: str) -> None:
    """Require a nonblank string value."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def require_optional_text(
    value: object | None,
    field_name: str,
) -> None:
    """Require a nonblank string when a value is present."""
    if value is not None:
        require_text(value, field_name)


def require_non_negative_int(
    value: int | None,
    field_name: str,
) -> None:
    """Require a non-negative integer when a value is present."""
    if value is None:
        return

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer or None")

    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def require_unit_interval(
    value: float | None,
    field_name: str,
) -> None:
    """Require a finite numeric value between zero and one."""
    if value is None:
        return

    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{field_name} must be numeric or None")

    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite")

    if not 0 <= value <= 1:
        raise ValueError(f"{field_name} must be between 0 and 1")


def require_ids(
    values: tuple[str, ...],
    field_name: str,
    *,
    allow_empty: bool = False,
    unique: bool = False,
) -> None:
    """Validate a tuple of identifier strings."""
    if not allow_empty and not values:
        raise ValueError(f"{field_name} must not be empty")

    for value in values:
        require_text(value, field_name)

    if unique:
        require_unique_values(values, field_name)


def require_unique_values(
    values: Iterable[Hashable],
    field_name: str,
) -> None:
    """Require every value in an iterable to be unique."""
    seen: set[Hashable] = set()

    for value in values:
        if value in seen:
            raise ValueError(
                f"{field_name} must not contain duplicate values: {value!r}"
            )
        seen.add(value)


def unique_ids(
    items: Iterable[_Identified],
    type_name: str,
) -> set[str]:
    """Validate and return the identifiers of domain objects."""
    identifiers: set[str] = set()

    for item in items:
        require_text(item.id, f"{type_name}.id")

        if item.id in identifiers:
            raise ValueError(f"duplicate {type_name}.id: {item.id}")

        identifiers.add(item.id)

    return identifiers


def require_known(
    values: Iterable[str],
    known: Collection[str],
    field_name: str,
) -> None:
    """Require every identifier to occur in a known collection."""
    for value in values:
        if value not in known:
            raise ValueError(f"{field_name} must reference a known identifier: {value}")
