from pathlib import Path

import pytest
from reqtrace.models.requirements import RequirementArtifact, RequirementSet
from reqtrace_adapters import (
    load_evidence,
    load_requirements,
    register_parser,
    validate_evidence,
    validate_requirements,
)
from reqtrace_adapters.sources.base import SourceInput


def test_load_requirements_from_file(tmp_path: Path) -> None:
    path = tmp_path / "use-case.md"
    path.write_text(
        "# Login\n\n## Main flow\n- User enters credentials\n- System logs in\n",
        encoding="utf-8",
    )

    result = load_requirements(path, kind="use-case")

    assert len(result.documents) == 1
    assert len(result.requirements) == 1
    assert len(result.fragments) == 2
    assert len(result.scenarios) == 1
    assert result.requirements[0].title == "Login"


def test_load_requirements_can_select_parser_automatically(tmp_path: Path) -> None:
    path = tmp_path / "use-case.md"
    path.write_text(
        "# Login\n\n## Main flow\n- User enters credentials\n- System logs in\n",
        encoding="utf-8",
    )

    result = load_requirements(path, kind="auto")

    assert len(result.requirements) == 1
    assert result.requirements[0].title == "Login"


def test_validate_requirements_accepts_supported_input(tmp_path: Path) -> None:
    path = tmp_path / "use-case.md"
    path.write_text("# Login\n\n## Main flow\n- User logs in\n", encoding="utf-8")

    validate_requirements(path)


def test_load_requirements_rejects_markdown_without_requirements(
    tmp_path: Path,
) -> None:
    path = tmp_path / "notes.md"
    path.write_text("# Notes\n\nThis is not a use case.", encoding="utf-8")

    with pytest.raises(ValueError, match="does not contain"):
        load_requirements(path, kind="auto")


def test_load_requirements_from_directory(tmp_path: Path) -> None:
    first = tmp_path / "login.md"
    second = tmp_path / "logout.md"

    first.write_text("# Login\n\n## Main flow\n- User logs in\n", encoding="utf-8")
    second.write_text("# Logout\n\n## Main flow\n- User logs out\n", encoding="utf-8")

    result = load_requirements(tmp_path, kind="use-case", pattern="*.md")

    assert len(result.documents) == 2
    assert len(result.requirements) == 2
    assert len(result.fragments) == 2
    assert len(result.scenarios) == 2
    assert result.metadata["source_count"] == 2


def test_load_requirements_from_directory_recursively(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()

    root_file = tmp_path / "root.md"
    nested_file = nested / "nested.md"

    root_file.write_text("# Root\n\n## Main flow\n- Root step\n", encoding="utf-8")
    nested_file.write_text(
        "# Nested\n\n## Main flow\n- Nested step\n",
        encoding="utf-8",
    )

    result = load_requirements(
        tmp_path,
        kind="use-case",
        pattern="*.md",
        recursive=True,
    )

    assert len(result.documents) == 2
    assert len(result.requirements) == 2
    assert len(result.fragments) == 2
    assert len(result.scenarios) == 2


def test_load_evidence_from_file(tmp_path: Path) -> None:
    path = tmp_path / "model.json"
    path.write_text(
        (
            "{"
            '"InitialPage": "Login",'
            '"ConcreteState": [{"AbstractID": "s1", "WidgetTree": []}],'
            '"ConcreteAction": [{"AbstractID": "a1", "Desc": "Click login"}],'
            '"ConcreteTransitions": [{"Source": "s1", "Action": "a1", "Target": "s1"}]'
            "}"
        ),
        encoding="utf-8",
    )

    result = load_evidence(path, kind="testar-state-model")

    assert result.id == "model"
    assert result.title == "Login"
    assert len(result.states) == 1
    assert len(result.actions) == 1
    assert len(result.transitions) == 1


def test_load_evidence_rejects_file_without_evidence_items(tmp_path: Path) -> None:
    path = tmp_path / "empty-model.json"
    path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="No evidence items found"):
        load_evidence(path, kind="auto")


def test_validate_evidence_accepts_supported_input(tmp_path: Path) -> None:
    path = tmp_path / "model.json"
    path.write_text(
        (
            "{"
            '"ConcreteState": [{"AbstractID": "s1", "WidgetTree": []}],'
            '"ConcreteAction": [{"AbstractID": "a1"}],'
            '"ConcreteTransitions": [{"Source": "s1", "Action": "a1", "Target": "s1"}]'
            "}"
        ),
        encoding="utf-8",
    )

    validate_evidence(path)


def test_load_evidence_rejects_directory(tmp_path: Path) -> None:
    first = tmp_path / "one.json"
    second = tmp_path / "two.json"

    first.write_text("{}", encoding="utf-8")
    second.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="expects exactly one source input"):
        load_evidence(tmp_path, kind="testar-state-model")


def test_load_unknown_parser_raises_helpful_error(tmp_path: Path) -> None:
    path = tmp_path / "input.unknown"
    path.write_text("content", encoding="utf-8")

    with pytest.raises(ValueError, match="No requirement parser registered"):
        load_requirements(path, kind="missing-kind")


def test_custom_parser_can_be_registered_and_loaded(tmp_path: Path) -> None:
    path = tmp_path / "custom.txt"
    path.write_text("custom requirement", encoding="utf-8")

    def load_custom_requirement(source: SourceInput) -> RequirementSet:
        assert source.data == "custom requirement"
        return RequirementSet(
            requirements=(
                RequirementArtifact(
                    id="custom-1",
                    title="Custom requirement",
                    body=str(source.data),
                ),
            ),
        )

    register_parser(
        "requirements",
        "custom-test",
        "txt",
        load_custom_requirement,
    )

    result = load_requirements(path, kind="custom-test")

    assert result.requirements[0].id == "custom-1"
    assert result.requirements[0].body == "custom requirement"
