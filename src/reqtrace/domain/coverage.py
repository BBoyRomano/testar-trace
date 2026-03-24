from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class RequirementStatus(str, Enum):
    FOUND = "found"
    PARTIALLY_FOUND = "partially_found"
    NOT_FOUND = "not_found"


class RequirementUnitStatus(str, Enum):
    FOUND = "found"
    PARTIALLY_FOUND = "partially_found"
    NOT_FOUND = "not_found"


class OccurrenceStatus(str, Enum):
    FOUND = "found"
    PARTIALLY_FOUND = "partially_found"
    NOT_FOUND = "not_found"


@dataclass(frozen=True)
class MatchEvidence:
    state_ids: tuple[str, ...]
    transition_ids: tuple[str, ...]
    observations: tuple[str, ...]
    explanation: str
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class RequirementUnitResult:
    requirement_id: str
    unit_id: str
    status: RequirementUnitStatus
    evidence: tuple[MatchEvidence, ...]
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class RequirementOccurrenceStep:
    unit_id: str
    status: RequirementUnitStatus
    evidence: tuple[MatchEvidence, ...]
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class RequirementOccurrence:
    occurrence_id: str
    status: OccurrenceStatus
    state_ids: tuple[str, ...]
    transition_ids: tuple[str, ...]
    steps: tuple[RequirementOccurrenceStep, ...]
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class RequirementResult:
    requirement_id: str
    status: RequirementStatus
    unit_results: tuple[RequirementUnitResult, ...]
    occurrences: tuple[RequirementOccurrence, ...] = ()
    metadata: Mapping[str, object] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


@dataclass(frozen=True)
class CoverageSummary:
    total_requirements: int
    found: int
    partially_found: int
    not_found: int


@dataclass(frozen=True)
class CoverageReport:
    results: tuple[RequirementResult, ...]
    summary: CoverageSummary
    metadata: Mapping[str, object]
