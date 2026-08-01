from pathlib import Path

import pytest
from reqtrace_adapters.sources.directory import DirectorySource
from reqtrace_adapters.sources.file import FileSource


def test_file_source_loads_text(tmp_path: Path) -> None:
    path = tmp_path / "requirement.md"
    path.write_text("# Login\n", encoding="utf-8")

    inputs = FileSource(path).load()

    assert len(inputs) == 1
    assert inputs[0].data == "# Login\n"
    assert inputs[0].name == "requirement.md"
    assert inputs[0].format == "md"
    assert inputs[0].uri == str(path)


def test_file_source_loads_json(tmp_path: Path) -> None:
    path = tmp_path / "story.json"
    path.write_text('{"title": "Login"}', encoding="utf-8")

    inputs = FileSource(path).load()

    assert len(inputs) == 1
    assert inputs[0].data == {"title": "Login"}
    assert inputs[0].name == "story.json"
    assert inputs[0].format == "json"
    assert inputs[0].uri == str(path)


def test_file_source_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(IsADirectoryError):
        FileSource(tmp_path).load()


def test_directory_source_loads_matching_files(tmp_path: Path) -> None:
    first = tmp_path / "a.md"
    second = tmp_path / "b.md"
    ignored = tmp_path / "ignored.txt"

    first.write_text("# A\n", encoding="utf-8")
    second.write_text("# B\n", encoding="utf-8")
    ignored.write_text("ignored", encoding="utf-8")

    inputs = DirectorySource(tmp_path, pattern="*.md").load()

    assert [source.name for source in inputs] == ["a.md", "b.md"]
    assert [source.data for source in inputs] == ["# A\n", "# B\n"]


def test_directory_source_loads_recursively(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()

    root_file = tmp_path / "root.md"
    nested_file = nested / "nested.md"

    root_file.write_text("# Root\n", encoding="utf-8")
    nested_file.write_text("# Nested\n", encoding="utf-8")

    shallow_inputs = DirectorySource(tmp_path, pattern="*.md").load()
    recursive_inputs = DirectorySource(
        tmp_path,
        pattern="*.md",
        recursive=True,
    ).load()

    assert [source.name for source in shallow_inputs] == ["root.md"]
    assert [source.name for source in recursive_inputs] == ["nested.md", "root.md"]


def test_directory_source_rejects_non_directory(tmp_path: Path) -> None:
    path = tmp_path / "file.md"
    path.write_text("# File\n", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        DirectorySource(path).load()
