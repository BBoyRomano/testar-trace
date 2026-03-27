from __future__ import annotations

from typing import Any, Optional

from pydantic import Field, model_validator

from reqtrace.domain.common import DomainModel
from reqtrace.domain.traceability.enums import (
    ConfidenceLabel,
    CoverageStatus,
    CoverageSubjectType,
    EvidenceTargetType,
    LinkType,
    TraceEvidenceKind,
)


class TraceLink(DomainModel):
    id: str = Field(..., min_length=1)
    analysis_run_id: str = Field(..., min_length=1)
    requirement_fragment_id: str = Field(..., min_length=1)
    evidence_target_type: EvidenceTargetType
    evidence_target_id: str = Field(..., min_length=1)
    link_type: LinkType
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_label: ConfidenceLabel = ConfidenceLabel.UNKNOWN
    metadata: dict[str, Any] = Field(default_factory=dict)



class TraceEvidence(DomainModel):
    id: str = Field(..., min_length=1)
    trace_link_id: str = Field(..., min_length=1)
    evidence_kind: TraceEvidenceKind
    text_excerpt: Optional[str] = None
    matched_tokens: list[str] = Field(default_factory=list)
    run_id: Optional[str] = None
    state_id: Optional[str] = None
    transition_id: Optional[str] = None
    element_id: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_support_payload(self) -> "TraceEvidence":
        has_context_anchor = any(
            value is not None
            for value in (self.run_id, self.state_id, self.transition_id, self.element_id)
        )
        has_content = bool(self.text_excerpt) or bool(self.matched_tokens)
        if not has_context_anchor and not has_content:
            raise ValueError(
                "TraceEvidence must include textual content, matched tokens, or an evidence anchor."
            )
        return self


class CoverageAssessment(DomainModel):
    id: str = Field(..., min_length=1)
    analysis_run_id: str = Field(..., min_length=1)
    subject_type: CoverageSubjectType
    subject_id: str = Field(..., min_length=1)
    coverage_status: CoverageStatus
    coverage_ratio: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_ratio: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    covered_fragment_count: Optional[int] = Field(default=None, ge=0)
    total_fragment_count: Optional[int] = Field(default=None, ge=0)
    supporting_run_count: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_consistency(self) -> "CoverageAssessment":
        if (
            self.covered_fragment_count is not None
            and self.total_fragment_count is not None
            and self.covered_fragment_count > self.total_fragment_count
        ):
            raise ValueError("covered_fragment_count cannot exceed total_fragment_count.")

        if self.coverage_status == CoverageStatus.COVERED and self.coverage_ratio == 0.0:
            raise ValueError("Covered assessments cannot have a coverage_ratio of 0.0.")
        if self.coverage_status == CoverageStatus.UNCOVERED and self.coverage_ratio == 1.0:
            raise ValueError("Uncovered assessments cannot have a coverage_ratio of 1.0.")
        return self
