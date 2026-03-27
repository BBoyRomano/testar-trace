from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import Field, field_validator

from reqtrace.domain.common.base import FrozenDomainModel
from reqtrace.domain.common.enums import SourceType


class ImportBatchRef(FrozenDomainModel):
    batch_id: str = Field(..., min_length=1)
    imported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("batch_id")
    @classmethod
    def validate_batch_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("batch_id cannot be blank.")
        return value

    @field_validator("imported_at")
    @classmethod
    def validate_imported_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("imported_at must be timezone-aware.")
        return value.astimezone(timezone.utc)


class SourceRef(FrozenDomainModel):
    source_type: SourceType
    source_name: str = Field(..., min_length=1)
    native_id: Optional[str] = None
    path_or_uri: Optional[str] = None

    @field_validator("source_name")
    @classmethod
    def validate_source_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source_name cannot be blank.")
        return value


class Provenance(FrozenDomainModel):
    source: SourceRef
    import_batch: ImportBatchRef
    parser_name: Optional[str] = None
    parser_version: Optional[str] = None
