from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from reqtrace.domain.common.enums import SourceType
from reqtrace.domain.common.value_objects import ImportBatchRef, Provenance, SourceRef


def build_provenance(
    *,
    source_type: SourceType,
    source_name: str,
    batch_id: str | None = None,
    native_id: str | None = None,
    path_or_uri: str | Path | None = None,
    parser_name: str | None = None,
    parser_version: str | None = None,
) -> Provenance:
    resolved_batch_id = batch_id or f"batch-{int(datetime.now(timezone.utc).timestamp())}"
    source_ref = SourceRef(
        source_type=source_type,
        source_name=source_name,
        native_id=native_id,
        path_or_uri=str(path_or_uri) if path_or_uri is not None else None,
    )
    return Provenance(
        source=source_ref,
        import_batch=ImportBatchRef(batch_id=resolved_batch_id),
        parser_name=parser_name,
        parser_version=parser_version,
    )
