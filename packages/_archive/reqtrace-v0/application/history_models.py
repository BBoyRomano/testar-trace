"""Application models for persisted run history."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from reqtrace.application.result_enums import RunStatus


class RunHistoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: f"run-history-{uuid4().hex}")
    label: str = Field(..., min_length=1)
    status: RunStatus = RunStatus.PENDING
    method_name: str = Field(default="baseline", min_length=1)
    run_id: str | None = None
    result_path: str | None = None
    source_path: str | None = None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_timestamps(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Run history timestamps must be timezone-aware.")
        return value.astimezone(timezone.utc)
