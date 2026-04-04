import pytest

from reqtrace.ingestion.common.exceptions import SourceValidationError
from reqtrace.ingestion.requirements.markdown.loader import MarkdownRequirementsLoader


def test_markdown_loader_parses_use_case_text() -> None:
    text = """# Sample requirement
ID: REQ-1
Actor: Sample actor

## Preconditions
- A valid precondition exists

## Main Flow
1. The user performs the main action

## Postconditions
- The operation is completed
"""

    loader = MarkdownRequirementsLoader()
    parsed = loader.load_text(text=text)

    assert parsed.document_title == "Sample requirement"
    assert len(parsed.requirements) == 1
    item = parsed.requirements[0]
    assert item.title == "Sample requirement"
    assert item.external_id == "REQ-1"
    assert item.actor == "Sample actor"
    assert item.preconditions == ["A valid precondition exists"]
    assert item.main_steps == ["The user performs the main action"]
    assert item.postconditions == ["The operation is completed"]


def test_markdown_loader_rejects_empty_text() -> None:
    loader = MarkdownRequirementsLoader()
    with pytest.raises(SourceValidationError, match="empty"):
        loader.load_text(text="   ")


def test_markdown_loader_rejects_missing_title() -> None:
    loader = MarkdownRequirementsLoader()

    with pytest.raises(SourceValidationError, match="top-level title"):
        loader.load_text(text="## Main Flow\n1. The user performs the main action\n")


def test_markdown_loader_rejects_missing_supported_sections() -> None:
    loader = MarkdownRequirementsLoader()

    with pytest.raises(SourceValidationError, match="supported requirement sections"):
        loader.load_text(text="# Sample requirement\n\nThis has no supported sections.\n")


def test_markdown_loader_rejects_empty_list_item() -> None:
    loader = MarkdownRequirementsLoader()

    with pytest.raises(SourceValidationError, match="section entry"):
        loader.load_text(text="# Sample requirement\n\n## Main Flow\n1.    \n")
