from __future__ import annotations

from typing import Any, Optional

from pydantic import Field, field_validator, model_validator

from reqtrace.domain.common import DomainModel, Provenance, SourceRef
from reqtrace.domain.requirements.enums import (
    RequirementFlowEdgeKind,
    RequirementFlowKind,
    RequirementFragmentKind,
    RequirementKind,
)


class RequirementArtifact(DomainModel):
    id: str = Field(..., min_length=1)
    kind: RequirementKind
    title: str = Field(..., min_length=1)
    external_id: Optional[str] = None
    summary: Optional[str] = None
    body: Optional[str] = None
    actor: Optional[str] = None
    scope: Optional[str] = None
    level: Optional[str] = None
    source_ref: Optional[SourceRef] = None
    provenance: Optional[Provenance] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RequirementFragment(DomainModel):
    id: str = Field(..., min_length=1)
    requirement_id: str = Field(..., min_length=1)
    kind: RequirementFragmentKind
    text: str = Field(..., min_length=1)
    order_index: Optional[int] = Field(default=None, ge=0)
    branch_id: Optional[str] = None
    parent_fragment_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RequirementFlow(DomainModel):
    id: str = Field(..., min_length=1)
    requirement_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    flow_kind: RequirementFlowKind
    entry_fragment_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name cannot be blank.")
        return value


class RequirementFlowEdge(DomainModel):
    id: str = Field(..., min_length=1)
    requirement_id: str = Field(..., min_length=1)
    from_fragment_id: str = Field(..., min_length=1)
    to_fragment_id: str = Field(..., min_length=1)
    edge_kind: RequirementFlowEdgeKind
    condition_label: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_self_loop_rules(self) -> "RequirementFlowEdge":
        if self.from_fragment_id == self.to_fragment_id and self.edge_kind != RequirementFlowEdgeKind.TERMINATES:
            raise ValueError("Self-loop edges are only allowed for terminates edges.")
        return self
