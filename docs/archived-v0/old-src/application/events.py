from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisStarted:
    requirement_count: int


@dataclass(frozen=True)
class RequirementAnalysisStarted:
    requirement_id: str


@dataclass(frozen=True)
class RequirementAnalysisCompleted:
    requirement_id: str
    status: str


@dataclass(frozen=True)
class AnalysisCompleted:
    requirement_count: int
