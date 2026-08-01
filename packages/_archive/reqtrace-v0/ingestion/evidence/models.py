from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from reqtrace.domain.common.enums import SourceType
from reqtrace.domain.evidence.enums import (
    ActionKind,
    EvidenceArtifactKind,
    EvidenceTool,
    ExecutionRunStatus,
    ObservationKind,
    StateModelLayer,
)


class ParsedEvidenceRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    tool_name: str = Field(..., min_length=1)
    tool: Optional[EvidenceTool] = None
    status: ExecutionRunStatus
    tool_run_id: Optional[str] = None
    sequence_number: Optional[int] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    state_model_layers: list[StateModelLayer] = Field(default_factory=list)
    native_id: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ParsedEvidenceState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    tool_state_id_abstract: Optional[str] = None
    tool_state_id_concrete: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    dom_signature: Optional[str] = None
    native_id: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ParsedEvidenceElement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    state_id: str = Field(..., min_length=1)
    tool_element_id_abstract: Optional[str] = None
    tool_element_id_concrete: Optional[str] = None
    tag_name: Optional[str] = None
    role: Optional[str] = None
    text: Optional[str] = None
    title: Optional[str] = None
    href: Optional[str] = None
    css_selector: Optional[str] = None
    path: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ParsedEvidenceAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    kind: ActionKind
    description: Optional[str] = None
    tool_action_id_abstract: Optional[str] = None
    tool_action_id_concrete: Optional[str] = None
    source_state_id: Optional[str] = None
    target_element_id: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ParsedEvidenceTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    from_state_id: str = Field(..., min_length=1)
    action_id: str = Field(..., min_length=1)
    to_state_id: Optional[str] = None
    run_id: Optional[str] = None
    order_index: Optional[int] = Field(default=None, ge=0)
    occurred_at: Optional[datetime] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ParsedEvidenceObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    kind: ObservationKind
    text: str = Field(..., min_length=1)
    state_id: Optional[str] = None
    transition_id: Optional[str] = None
    observed_at: Optional[datetime] = None
    severity: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ParsedEvidenceArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    kind: EvidenceArtifactKind
    path_or_uri: str = Field(..., min_length=1)
    run_id: str | None = None
    model_layer: Optional[StateModelLayer] = None
    source_type: SourceType = SourceType.FILE
    native_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedEvidenceSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run: ParsedEvidenceRun
    states: list[ParsedEvidenceState] = Field(default_factory=list)
    elements: list[ParsedEvidenceElement] = Field(default_factory=list)
    actions: list[ParsedEvidenceAction] = Field(default_factory=list)
    transitions: list[ParsedEvidenceTransition] = Field(default_factory=list)
    observations: list[ParsedEvidenceObservation] = Field(default_factory=list)
    artifacts: list[ParsedEvidenceArtifact] = Field(default_factory=list)
    source_type: SourceType = SourceType.FILE
    source_name: str = Field(..., min_length=1)
    path_or_uri: str | None = None
