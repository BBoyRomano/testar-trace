"""Presentation-layer boundary exceptions."""

from __future__ import annotations


class PresentationError(Exception):
    """Base exception for presentation/runtime failures."""


class RunInputValidationError(PresentationError):
    """Raised when run input from CLI/GUI cannot be validated."""
