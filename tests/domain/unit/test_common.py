from datetime import datetime, timedelta, timezone

import pytest

from reqtrace.domain.common.enums import SourceType
from reqtrace.domain.common.value_objects import ImportBatchRef, Provenance, SourceRef


def test_provenance_value_objects_can_be_created() -> None:
    source = SourceRef(
        source_type=SourceType.FILE,
        source_name="sample-requirements-source",
        native_id="REQ-1",
        path_or_uri="sample-requirements.md",
    )
    batch = ImportBatchRef(batch_id="batch-1")
    provenance = Provenance(
        source=source,
        import_batch=batch,
        parser_name="sample-parser",
        parser_version="v1",
    )

    assert provenance.source.source_name == "sample-requirements-source"
    assert provenance.import_batch.batch_id == "batch-1"


def test_import_batch_ref_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError):
        ImportBatchRef(batch_id="batch-1", imported_at=datetime(2026, 1, 1, 12, 0, 0))


def test_import_batch_ref_normalizes_datetime_to_utc() -> None:
    plus_two = timezone(timedelta(hours=2))
    batch = ImportBatchRef(
        batch_id="batch-1",
        imported_at=datetime(2026, 1, 1, 12, 0, tzinfo=plus_two),
    )

    assert batch.imported_at == datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)


def test_source_ref_rejects_blank_source_name() -> None:
    with pytest.raises(ValueError):
        SourceRef(source_type=SourceType.FILE, source_name="   ")


def test_frozen_value_objects_are_immutable() -> None:
    source = SourceRef(source_type=SourceType.FILE, source_name="sample")

    with pytest.raises(Exception):
        source.source_name = "changed"


def test_extra_fields_are_forbidden_on_domain_models() -> None:
    with pytest.raises(ValueError):
        SourceRef(source_type=SourceType.FILE, source_name="sample", unexpected="x")
