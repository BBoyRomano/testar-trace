import pytest

from reqtrace.ingestion.common.exceptions import UnsupportedSourceError
from reqtrace.ingestion.common.registry import build_default_registry


def test_default_registry_ingests_requirements_from_markdown_file(tmp_path) -> None:
    registry = build_default_registry()
    path = tmp_path / "sample.md"
    path.write_text(
        "# Sample requirement\n\n## Main Flow\n1. The user performs the main action\n",
        encoding="utf-8",
    )

    batch = registry.ingest_requirements("markdown", path)

    assert len(batch.requirements) == 1
    assert len(batch.fragments) == 1


def test_default_registry_ingests_evidence_from_testar_file(
    tmp_path,
    write_minimal_testar_model_file,
) -> None:
    registry = build_default_registry()
    path = tmp_path / "sample.json"
    write_minimal_testar_model_file(path)

    batch = registry.ingest_evidence("testar", path)

    assert len(batch.runs) == 1
    assert len(batch.states) == 1


def test_default_registry_ingests_requirements_from_json_file(
    tmp_path,
    write_minimal_use_case_json_file,
) -> None:
    registry = build_default_registry()
    path = tmp_path / "sample.json"
    write_minimal_use_case_json_file(path)

    batch = registry.ingest_requirements("json", path)

    assert len(batch.requirements) == 2
    assert len(batch.documents) == 1


def test_default_registry_rejects_unsupported_source() -> None:
    registry = build_default_registry()

    with pytest.raises(UnsupportedSourceError):
        registry.get_requirement_loader("unknown")
