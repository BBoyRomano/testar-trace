"""Stable identifier construction for canonical values."""

import re


def identifier(value: str, *, fallback: str = "item") -> str:
    """Convert source text into a stable lowercase identifier."""
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().casefold())
    return normalized.strip("-") or fallback


def artifact_stem(value: str) -> str:
    """Return an identifier derived from an artifact id without its extension."""
    stem = value.rsplit(".", maxsplit=1)[0]
    return identifier(stem, fallback="artifact")


def scoped_id(scope_id: str, kind: str, native_id: str) -> str:
    """Create a globally unique canonical id while preserving the native id."""
    return f"{scope_id}:{kind}:{native_id}"
