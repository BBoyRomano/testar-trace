from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import Field, model_validator

from reqtrace.domain.common import DomainModel, Provenance, SourceRef
from reqtrace.domain.evidence.enums import (
    ActionKind,
    AttachmentKind,
    ExecutionRunStatus,
    ObservationKind,
)


class ApplicationState(DomainModel):
    id: str = Field(..., min_length=1)
    tool_state_id_abstract: Optional[str] = None
    tool_state_id_concrete: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    dom_signature: Optional[str] = None
    source_ref: Optional[SourceRef] = None
    provenance: Optional[Provenance] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class UIElement(DomainModel):
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


class Action(DomainModel):
    id: str = Field(..., min_length=1)
    kind: ActionKind
    description: Optional[str] = None
    tool_action_id_abstract: Optional[str] = None
    tool_action_id_concrete: Optional[str] = None
    source_state_id: Optional[str] = None
    target_element_id: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class Transition(DomainModel):
    id: str = Field(..., min_length=1)
    from_state_id: str = Field(..., min_length=1)
    action_id: str = Field(..., min_length=1)
    to_state_id: Optional[str] = None
    run_id: Optional[str] = None
    order_index: Optional[int] = Field(default=None, ge=0)
    occurred_at: Optional[datetime] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ExecutionRun(DomainModel):
    id: str = Field(..., min_length=1)
    tool_name: str = Field(..., min_length=1)
    status: ExecutionRunStatus
    tool_run_id: Optional[str] = None
    sequence_number: Optional[int] = Field(default=None, ge=0)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    source_ref: Optional[SourceRef] = None
    provenance: Optional[Provenance] = None
    attributes: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_time_range(self) -> "ExecutionRun":
        if (
            self.started_at is not None
            and self.ended_at is not None
            and self.ended_at < self.started_at
        ):
            raise ValueError("ended_at cannot be earlier than started_at.")
        return self


class Observation(DomainModel):
    id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    kind: ObservationKind
    text: str = Field(..., min_length=1)
    state_id: Optional[str] = None
    transition_id: Optional[str] = None
    observed_at: Optional[datetime] = None
    severity: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_anchor(self) -> "Observation":
        if self.state_id is None and self.transition_id is None:
            raise ValueError("Observation must reference at least a state_id or transition_id.")
        return self


class Attachment(DomainModel):
    id: str = Field(..., min_length=1)
    kind: AttachmentKind
    path_or_uri: str = Field(..., min_length=1)
    run_id: Optional[str] = None
    state_id: Optional[str] = None
    observation_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_owner_reference(self) -> "Attachment":
        if self.run_id is None and self.state_id is None and self.observation_id is None:
            raise ValueError("Attachment must reference at least one owner entity.")
        return self
