from __future__ import annotations

from dataclasses import dataclass, field

from reqtrace.domain.coverage import OccurrenceStatus, RequirementUnitStatus


@dataclass(frozen=True)
class TraceStepMatch:
    requirement_id: str
    unit_id: str
    unit_kind: str
    sequence: int | None
    state_ids: tuple[str, ...] = ()
    transition_ids: tuple[str, ...] = ()
    matched_observations: tuple[str, ...] = ()
    status: RequirementUnitStatus = RequirementUnitStatus.NOT_FOUND
    explanation: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class TraceCandidate:
    requirement_id: str
    step_matches: tuple[TraceStepMatch, ...]
    missing_unit_ids: tuple[str, ...] = ()
    state_ids: tuple[str, ...] = ()
    transition_ids: tuple[str, ...] = ()
    is_connected: bool = False
    is_order_consistent: bool = False
    score: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class TraceOccurrence:
    requirement_id: str
    occurrence_id: str
    status: OccurrenceStatus
    step_matches: tuple[TraceStepMatch, ...]
    missing_unit_ids: tuple[str, ...] = ()
    state_ids: tuple[str, ...] = ()
    transition_ids: tuple[str, ...] = ()
    metadata: dict = field(default_factory=dict)
