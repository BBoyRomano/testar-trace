from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from reqtrace.domain.common.enums import SourceType
from reqtrace.domain.requirements.enums import RequirementFormat, RequirementNotation


class ParsedAlternativeFlow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_id: str | None = None
    title: str | None = None
    steps: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedRequirementRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    external_id: str | None = None
    actor: str | None = None
    body: str | None = None
    scope: str | None = None
    level: str | None = None
    trigger: str | None = None
    preconditions: list[str] = Field(default_factory=list)
    main_steps: list[str] = Field(default_factory=list)
    alternative_steps: list[str] = Field(default_factory=list)
    alternative_flows: list[ParsedAlternativeFlow] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    related_information: list[str] = Field(default_factory=list)
    notation: RequirementNotation = RequirementNotation.USE_CASE
    file_format: RequirementFormat = RequirementFormat.MARKDOWN
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedRequirementsSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_title: str | None = None
    requirements: list[ParsedRequirementRecord] = Field(default_factory=list)
    source_type: SourceType = SourceType.FILE
    source_name: str = Field(..., min_length=1)
    path_or_uri: str | None = None

    @model_validator(mode="after")
    def validate_non_empty_requirements(self) -> "ParsedRequirementsSource":
        if not self.requirements:
            raise ValueError("Parsed requirements source must contain at least one requirement.")
        return self
