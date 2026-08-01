"""Application output/result models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from reqtrace.application.result_enums import (
    CoverageVerdict,
    FlowStatus,
    MatchRole,
    RequirementResultStatus,
    RunStatus,
    TraceKind,
    TracePathItemKind,
)
from reqtrace.domain.traceability.models import CoverageAssessment, TraceEvidence, TraceLink


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


class InputSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_count: int = Field(default=0, ge=0)
    fragment_count: int = Field(default=0, ge=0)
    flow_count: int = Field(default=0, ge=0)
    state_count: int = Field(default=0, ge=0)
    element_count: int = Field(default=0, ge=0)
    action_count: int = Field(default=0, ge=0)
    transition_count: int = Field(default=0, ge=0)
    run_count: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CoverageSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: CoverageVerdict = CoverageVerdict.NONE
    main_flow_status: FlowStatus = FlowStatus.NOT_COVERED
    alt_flow_status: FlowStatus = FlowStatus.NONE_DEFINED
    main_flow_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    alt_flow_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)


class FlowCoverageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flow_id: str
    flow_kind: TraceKind
    name: str
    status: FlowStatus
    ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    fragment_ids: list[str] = Field(default_factory=list)
    covered_fragment_ids: list[str] = Field(default_factory=list)
    instance_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FragmentTraceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fragment_id: str
    fragment_kind: str
    fragment_text: str
    status: FlowStatus
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_state_ids: list[str] = Field(default_factory=list)
    matched_transition_ids: list[str] = Field(default_factory=list)
    matched_action_ids: list[str] = Field(default_factory=list)
    matched_element_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TracePathItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: TracePathItemKind
    item_id: str
    state_id: Optional[str] = None
    transition_id: Optional[str] = None
    action_id: Optional[str] = None
    label: str = ""
    matched_fragment_ids: list[str] = Field(default_factory=list)
    match_role: MatchRole = MatchRole.INTERMEDIATE
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(default_factory=lambda: f"trace-{uuid4().hex}")
    trace_kind: TraceKind
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    path: list[TracePathItem] = Field(default_factory=list)
    matched_fragment_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionInstance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instance_id: str = Field(default_factory=lambda: f"instance-{uuid4().hex}")
    flow_id: str
    flow_kind: TraceKind
    covered_fragment_ids: list[str] = Field(default_factory=list)
    representative_trace: ExecutionTrace
    overlapping_trace_count: int = Field(default=1, ge=1)
    omitted_trace_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GlobalCoverageSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_requirements: int = Field(default=0, ge=0)
    fully_covered: int = Field(default=0, ge=0)
    main_only: int = Field(default=0, ge=0)
    alt_only: int = Field(default=0, ge=0)
    partial: int = Field(default=0, ge=0)
    none: int = Field(default=0, ge=0)
    uncertain: int = Field(default=0, ge=0)
    requirements_with_any_trace: int = Field(default=0, ge=0)
    requirements_with_main_trace: int = Field(default=0, ge=0)
    requirements_with_alt_trace: int = Field(default=0, ge=0)
    overall_coverage_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    main_flow_coverage_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    alt_flow_coverage_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    average_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RequirementTraceabilityResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str = Field(..., min_length=1)
    requirement_title: str = Field(..., min_length=1)
    requirement_external_id: Optional[str] = None
    status: RequirementResultStatus
    coverage: CoverageSummary = Field(default_factory=CoverageSummary)
    main_flow_result: Optional[FlowCoverageResult] = None
    alternative_flow_results: list[FlowCoverageResult] = Field(default_factory=list)
    fragment_results: list[FragmentTraceResult] = Field(default_factory=list)
    execution_instances: list[ExecutionInstance] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Backward compatible fields.
    artifact_coverage: Optional[CoverageAssessment] = None
    fragment_coverages: list[CoverageAssessment] = Field(default_factory=list)
    trace_links: list[TraceLink] = Field(default_factory=list)
    trace_evidence: list[TraceEvidence] = Field(default_factory=list)


class TraceabilitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Legacy summary fields.
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

    input_summary: InputSummary = Field(default_factory=InputSummary)
    global_coverage: GlobalCoverageSummary = Field(default_factory=GlobalCoverageSummary)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def total_requirements(self) -> int:
        return self.global_coverage.total_requirements


class TraceabilityResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    run: TraceabilityRun
    requirement_results: list[RequirementTraceabilityResult] = Field(default_factory=list)
    summary: TraceabilitySummary
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
