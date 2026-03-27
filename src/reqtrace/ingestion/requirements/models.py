from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from reqtrace.domain.common.enums import SourceType


class ParsedRequirementsSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    external_id: str | None = None
    actor: str | None = None
    body: str | None = None
    preconditions: list[str] = Field(default_factory=list)
    main_steps: list[str] = Field(default_factory=list)
    alternative_steps: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    source_type: SourceType = SourceType.FILE
    source_name: str = Field(..., min_length=1)
    path_or_uri: str | None = None
