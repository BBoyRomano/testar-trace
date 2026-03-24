from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RequirementKind(str, Enum):
    USE_CASE = "use_case"
    USER_STORY = "user_story"
    FEATURE = "feature"


class RequirementUnitKind(str, Enum):
    PRECONDITION = "precondition"
    TRIGGER = "trigger"
    STEP = "step"
    POSTCONDITION = "postcondition"


@dataclass(frozen=True)
class RequirementUnit:
    id: str
    kind: RequirementUnitKind
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Requirement:
    id: str
    kind: RequirementKind
    title: str
    summary: str | None = None
    actor: str | None = None
    units: tuple[RequirementUnit, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RequirementCatalog:
    requirements: tuple[Requirement, ...]
    metadata: dict[str, Any] = field(default_factory=dict)
