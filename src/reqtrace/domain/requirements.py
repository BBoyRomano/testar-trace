from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class RequirementKind(str, Enum):
    USE_CASE = "use_case"
    USER_STORY = "user_story"
    OTHER = "other"


class RequirementUnitKind(str, Enum):
    PRECONDITION = "precondition"
    TRIGGER = "trigger"
    MAIN_STEP = "main_step"
    POSTCONDITION = "postcondition"
    ALTERNATIVE_FLOW = "alternative_flow"
    CONSTRAINT = "constraint"
    OTHER = "other"


@dataclass(frozen=True)
class RequirementUnit:
    id: str
    kind: RequirementUnitKind
    text: str
    critical: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Requirement:
    id: str
    kind: RequirementKind
    title: str
    summary: str | None = None
    units: tuple[RequirementUnit, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RequirementCatalog:
    requirements: tuple[Requirement, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)
