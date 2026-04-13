from pathlib import Path

import pytest

from reqtrace.ingestion.requirements.adapter import RequirementsAdapter
from reqtrace.ingestion.requirements.markdown.loader import MarkdownRequirementsLoader

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "ingestion"
pytestmark = pytest.mark.integration


def test_markdown_loader_and_adapter_ingest_use_case_text() -> None:
    text = """# Sample requirement
ID: REQ-1
Actor: Sample actor

## Preconditions
- A valid precondition exists

## Main Flow
1. The user performs the main action
2. The system shows the next state

## Alternative Flow
1. An alternative outcome is shown

## Postconditions
- The operation is completed
"""

    loader = MarkdownRequirementsLoader()
    parsed = loader.load_text(text=text)

    adapter = RequirementsAdapter()
    batch = adapter.ingest(parsed)

    assert len(batch.requirements) == 1
    requirement = batch.requirements[0]
    assert requirement.id == "req-1"
    assert requirement.external_id == "REQ-1"

    flow_by_name = {flow.name: flow for flow in batch.flows}
    assert flow_by_name["Main flow"].flow_kind.value == "main"
    assert flow_by_name["Alternative flow"].flow_kind.value == "alternative"

    fragment_by_id = {fragment.id: fragment for fragment in batch.fragments}
    main_entry_id = flow_by_name["Main flow"].entry_fragment_id
    assert main_entry_id is not None
    assert fragment_by_id[main_entry_id].text == "The user performs the main action"
    assert fragment_by_id[main_entry_id].kind.value == "main_step"

    alternative_fragments = [
        fragment for fragment in batch.fragments if fragment.kind.value == "alternative_step"
    ]
    assert len(alternative_fragments) == 1
    assert alternative_fragments[0].branch_id == "alt-1"

    main_edges = [
        edge
        for edge in batch.flow_edges
        if edge.id.startswith(f"{flow_by_name['Main flow'].id}-edge")
    ]
    assert len(main_edges) == 1
    assert (
        fragment_by_id[main_edges[0].from_fragment_id].text == "The user performs the main action"
    )
    assert fragment_by_id[main_edges[0].to_fragment_id].text == "The system shows the next state"


def test_markdown_loader_file_entrypoint_ingests_realistic_fixture() -> None:
    path = FIXTURES_DIR / "sample_requirements.md"

    loader = MarkdownRequirementsLoader()
    parsed = loader.load(path)

    adapter = RequirementsAdapter()
    batch = adapter.ingest(parsed)

    assert batch.requirements[0].id == "uc-checkout-1"
    assert batch.requirements[0].actor == "Shopper"
    assert [flow.name for flow in batch.flows] == [
        "Preconditions",
        "Main flow",
        "Alternative flow",
        "Postconditions",
    ]
    assert batch.flows[1].entry_fragment_id == batch.fragments[1].id
    assert batch.fragments[1].text == "The shopper enters a valid card number"
    assert batch.fragments[4].kind.value == "alternative_step"
