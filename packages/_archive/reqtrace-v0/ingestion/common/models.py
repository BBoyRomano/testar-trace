from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from reqtrace.domain.common.enums import SourceType
from reqtrace.domain.evidence.enums import (
    ActionKind,
    AttachmentKind,
    EvidenceArtifactKind,
    EvidenceTool,
    ExecutionRunStatus,
    ObservationKind,
    StateModelLayer,
)
from reqtrace.domain.requirements.enums import (
    RequirementFlowEdgeKind,
    RequirementFlowKind,
    RequirementFormat,
    RequirementFragmentKind,
    RequirementKind,
    RequirementNotation,
)


class NormalizedRequirementRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    kind: RequirementKind
    title: str = Field(..., min_length=1)
    external_id: Optional[str] = None
    summary: Optional[str] = None
    body: Optional[str] = None
    actor: Optional[str] = None
    scope: Optional[str] = None
    level: Optional[str] = None
    notation: Optional[RequirementNotation] = None
    file_format: Optional[RequirementFormat] = None
    document_id: Optional[str] = None
    source_type: SourceType
    source_name: str = Field(..., min_length=1)
    native_id: Optional[str] = None
    path_or_uri: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedRequirementFragmentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    requirement_id: str = Field(..., min_length=1)
    kind: RequirementFragmentKind
    text: str = Field(..., min_length=1)
    order_index: Optional[int] = Field(default=None, ge=0)
    branch_id: Optional[str] = None
    parent_fragment_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedRequirementFlowRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    requirement_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    flow_kind: RequirementFlowKind
    entry_fragment_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedRequirementFlowEdgeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    requirement_id: str = Field(..., min_length=1)
    from_fragment_id: str = Field(..., min_length=1)
    to_fragment_id: str = Field(..., min_length=1)
    edge_kind: RequirementFlowEdgeKind
    condition_label: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedRequirementDocumentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    notation: RequirementNotation
    file_format: RequirementFormat
    source_type: SourceType
    source_name: str = Field(..., min_length=1)
    native_id: Optional[str] = None
    path_or_uri: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedRequirementBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    documents: list[NormalizedRequirementDocumentRecord] = Field(default_factory=list)
    requirements: list[NormalizedRequirementRecord] = Field(default_factory=list)
    fragments: list[NormalizedRequirementFragmentRecord] = Field(default_factory=list)
    flows: list[NormalizedRequirementFlowRecord] = Field(default_factory=list)
    flow_edges: list[NormalizedRequirementFlowEdgeRecord] = Field(default_factory=list)


class NormalizedEvidenceStateRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    tool_state_id_abstract: Optional[str] = None
    tool_state_id_concrete: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    dom_signature: Optional[str] = None
    source_type: SourceType
    source_name: str = Field(..., min_length=1)
    native_id: Optional[str] = None
    path_or_uri: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class NormalizedEvidenceElementRecord(BaseModel):
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


class NormalizedActionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    kind: ActionKind
    description: Optional[str] = None
    tool_action_id_abstract: Optional[str] = None
    tool_action_id_concrete: Optional[str] = None
    source_state_id: Optional[str] = None
    target_element_id: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class NormalizedTransitionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    from_state_id: str = Field(..., min_length=1)
    action_id: str = Field(..., min_length=1)
    to_state_id: Optional[str] = None
    run_id: Optional[str] = None
    order_index: Optional[int] = Field(default=None, ge=0)
    occurred_at: Optional[datetime] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class NormalizedExecutionRunRecord(BaseModel):
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
    source_type: SourceType
    source_name: str = Field(..., min_length=1)
    native_id: Optional[str] = None
    path_or_uri: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class NormalizedObservationRecord(BaseModel):
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


class NormalizedAttachmentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    kind: AttachmentKind
    path_or_uri: str = Field(..., min_length=1)
    run_id: Optional[str] = None
    state_id: Optional[str] = None
    observation_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedEvidenceArtifactRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    kind: EvidenceArtifactKind
    path_or_uri: str = Field(..., min_length=1)
    run_id: Optional[str] = None
    model_layer: Optional[StateModelLayer] = None
    source_type: SourceType
    source_name: str = Field(..., min_length=1)
    native_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedEvidenceBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    states: list[NormalizedEvidenceStateRecord] = Field(default_factory=list)
    elements: list[NormalizedEvidenceElementRecord] = Field(default_factory=list)
    actions: list[NormalizedActionRecord] = Field(default_factory=list)
    transitions: list[NormalizedTransitionRecord] = Field(default_factory=list)
    runs: list[NormalizedExecutionRunRecord] = Field(default_factory=list)
    observations: list[NormalizedObservationRecord] = Field(default_factory=list)
    attachments: list[NormalizedAttachmentRecord] = Field(default_factory=list)
    artifacts: list[NormalizedEvidenceArtifactRecord] = Field(default_factory=list)
