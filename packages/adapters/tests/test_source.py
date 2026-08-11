from pathlib import Path

import pytest

from testar_trace.domain.provenance import SourceType
from testar_trace_adapters import SourceArtifact, read_source_artifacts


def test_source_artifact_builds_canonical_source_reference() -> None:
    artifact = SourceArtifact(
        id="requirements/login.md",
        name="login.md",
        data="# Login",
        format=".MD",
        uri="memory:login",
    )

    reference = artifact.source_ref(
        native_id="UC-01",
        element_kind="requirement",
    )

    assert artifact.format == "md"
    assert reference.artifact_id == "requirements/login.md"
    assert reference.native_id == "UC-01"


def test_read_source_artifacts_reads_one_file(tmp_path: Path) -> None:
    path = tmp_path / "requirement.md"
    path.write_text("# Login\n", encoding="utf-8")

    artifacts = read_source_artifacts(path)

    assert artifacts[0].id == "requirement.md"
    assert artifacts[0].data == "# Login\n"
    assert artifacts[0].source_type is SourceType.FILE


def test_read_source_artifacts_reads_directory_deterministically(
    tmp_path: Path,
) -> None:
    (tmp_path / "b.json").write_text("{}", encoding="utf-8")
    (tmp_path / "a.json").write_text("{}", encoding="utf-8")

    artifacts = read_source_artifacts(tmp_path, pattern="*.json")

    assert [artifact.id for artifact in artifacts] == ["a.json", "b.json"]


def test_read_source_artifacts_rejects_empty_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no matching files"):
        read_source_artifacts(tmp_path, pattern="*.json")
