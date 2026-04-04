"""Enums used by application request/result contracts."""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return str(self.value)


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class RequirementResultStatus(StrEnum):
    DONE = "done"
    FAILED = "failed"


class CoverageVerdict(StrEnum):
    FULL = "full"
    MAIN_ONLY = "main_only"
    ALT_ONLY = "alt_only"
    PARTIAL = "partial"
    NONE = "none"
    UNCERTAIN = "uncertain"


class FlowStatus(StrEnum):
    COVERED = "covered"
    PARTIAL = "partial"
    NOT_COVERED = "not_covered"
    NONE_DEFINED = "none_defined"


class TraceKind(StrEnum):
    MAIN = "main"
    ALTERNATIVE = "alternative"
    MIXED = "mixed"
    CANDIDATE = "candidate"


class TracePathItemKind(StrEnum):
    STATE = "state"
    TRANSITION = "transition"


class MatchRole(StrEnum):
    MATCHED = "matched"
    INTERMEDIATE = "intermediate"
