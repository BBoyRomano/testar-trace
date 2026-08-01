"""Progress models for live traceability execution updates."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

RequirementProgressState = Literal["processing", "completed", "failed"]


@dataclass(slots=True, frozen=True)
class RequirementProgress:
    requirement_id: str
    requirement_title: str
    state: RequirementProgressState
    processed_requirement_count: int
    total_requirement_count: int
    phase: str | None = None
    message: str | None = None


ProgressCallback = Callable[[RequirementProgress], None]
CancellationCallback = Callable[[], bool]
