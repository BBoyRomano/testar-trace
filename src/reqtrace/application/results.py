"""Stable application-level traceability models.

These models are intended to be consumed by the CLI/UI and by export/reporting.
Keep them stable and boring.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from reqtrace.application.exceptions import InvalidTraceabilityRequestError
from reqtrace.domain.evidence.models import (
    Action,
    ApplicationState,
    Attachment,
    ExecutionRun,
    Observation,
    Transition,
    UIElement,
)
from reqtrace.domain.requirements.models import (
    RequirementArtifact,
    RequirementFlow,
    RequirementFlowEdge,
    RequirementFragment,
)
from reqtrace.domain.traceability.models import CoverageAssessment, TraceEvidence, TraceLink


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


class RequirementSnapshot(BaseModel):
    """In-memory requirement snapshot ready for analysis."""

    model_config = ConfigDict(extra="forbid")

    requirements: list[RequirementArtifact] = Field(default_factory=list)
    fragments: list[RequirementFragment] = Field(default_factory=list)
    flows: list[RequirementFlow] = Field(default_factory=list)
    flow_edges: list[RequirementFlowEdge] = Field(default_factory=list)

    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> "RequirementSnapshot":
        required_keys = {"requirements", "fragments", "flows", "flow_edges"}
        missing_keys = sorted(required_keys.difference(mapping))
        if missing_keys:
            raise InvalidTraceabilityRequestError(
                f"Requirement mapping is missing required keys: {', '.join(missing_keys)}"
            )
        return cls(
            requirements=list(mapping["requirements"]),
            fragments=list(mapping["fragments"]),
            flows=list(mapping["flows"]),
            flow_edges=list(mapping["flow_edges"]),
        )

    def iter_requirements(self, selected_ids: list[str] | None = None) -> list[RequirementArtifact]:
        if not selected_ids:
            return list(self.requirements)
        selected_set = set(selected_ids)
        return [req for req in self.requirements if req.id in selected_set]

    def fragments_for(self, requirement_id: str) -> list[RequirementFragment]:
        return [fragment for fragment in self.fragments if fragment.requirement_id == requirement_id]


class EvidenceSnapshot(BaseModel):
    """In-memory evidence snapshot ready for analysis."""

    model_config = ConfigDict(extra="forbid")

    states: list[ApplicationState] = Field(default_factory=list)
    elements: list[UIElement] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)
    transitions: list[Transition] = Field(default_factory=list)
    runs: list[ExecutionRun] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)

    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> "EvidenceSnapshot":
        required_keys = {
            "states",
            "elements",
            "actions",
            "transitions",
            "runs",
            "observations",
            "attachments",
        }
        missing_keys = sorted(required_keys.difference(mapping))
        if missing_keys:
            raise InvalidTraceabilityRequestError(
                f"Evidence mapping is missing required keys: {', '.join(missing_keys)}"
            )
        return cls(
            states=list(mapping["states"]),
            elements=list(mapping["elements"]),
            actions=list(mapping["actions"]),
            transitions=list(mapping["transitions"]),
            runs=list(mapping["runs"]),
            observations=list(mapping["observations"]),
            attachments=list(mapping["attachments"]),
        )


class TraceabilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method_name: str = Field(default="baseline", min_length=1)
    requirements: RequirementSnapshot
    evidence: EvidenceSnapshot
    selected_requirement_ids: list[str] = Field(default_factory=list)
    selected_evidence_run_ids: list[str] = Field(default_factory=list)
    options: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_selected_ids(self) -> "TraceabilityRequest":
        if self.selected_requirement_ids:
            known = {req.id for req in self.requirements.requirements}
            unknown = sorted(set(self.selected_requirement_ids).difference(known))
            if unknown:
                raise InvalidTraceabilityRequestError(
                    "Unknown selected requirement ids: " + ", ".join(unknown)
                )

        if self.selected_evidence_run_ids:
            known = {run.id for run in self.evidence.runs}
            unknown = sorted(set(self.selected_evidence_run_ids).difference(known))
            if unknown:
                raise InvalidTraceabilityRequestError(
                    "Unknown selected evidence run ids: " + ", ".join(unknown)
                )
        return self


class TraceabilityRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: f"trace-run-{uuid4().hex}")
    method_name: str = Field(..., min_length=1)
    status: RunStatus = RunStatus.PENDING
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    total_requirement_count: int = Field(default=0, ge=0)
    processed_requirement_count: int = Field(default=0, ge=0)
    failed_requirement_count: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("started_at", "ended_at")
    @classmethod
    def validate_timestamps(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return value
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Traceability run timestamps must be timezone-aware.")
        return value.astimezone(timezone.utc)


class RequirementTraceabilityResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str = Field(..., min_length=1)
    requirement_title: str = Field(..., min_length=1)
    status: RequirementResultStatus
    artifact_coverage: Optional[CoverageAssessment] = None
    fragment_coverages: list[CoverageAssessment] = Field(default_factory=list)
    trace_links: list[TraceLink] = Field(default_factory=list)
    trace_evidence: list[TraceEvidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceabilitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_count: int = Field(default=0, ge=0)
    analyzed_requirement_count: int = Field(default=0, ge=0)
    failed_requirement_count: int = Field(default=0, ge=0)
    covered_requirement_count: int = Field(default=0, ge=0)
    partially_covered_requirement_count: int = Field(default=0, ge=0)
    uncovered_requirement_count: int = Field(default=0, ge=0)
    uncertain_requirement_count: int = Field(default=0, ge=0)
    requirement_fragment_count: int = Field(default=0, ge=0)
    covered_fragment_count: int = Field(default=0, ge=0)
    trace_link_count: int = Field(default=0, ge=0)
    trace_evidence_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceabilityResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run: TraceabilityRun
    requirement_results: list[RequirementTraceabilityResult] = Field(default_factory=list)
    summary: TraceabilitySummary
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
