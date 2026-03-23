from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class RequirementUnitStatus(str, Enum):
    FOUND = "found"
    PARTIALLY_FOUND = "partially_found"
    NOT_FOUND = "not_found"


class RequirementStatus(str, Enum):
    FOUND = "found"
    PARTIALLY_FOUND = "partially_found"
    NOT_FOUND = "not_found"


@dataclass(frozen=True)
class MatchEvidence:
    state_ids: tuple[str, ...] = ()
    transition_ids: tuple[str, ...] = ()
    observations: tuple[str, ...] = ()
    explanation: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RequirementUnitResult:
    requirement_id: str
    unit_id: str
    status: RequirementUnitStatus
    evidence: tuple[MatchEvidence, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RequirementResult:
    requirement_id: str
    status: RequirementStatus
    unit_results: tuple[RequirementUnitResult, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


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
    metadata: Mapping[str, object] = field(default_factory=dict)
