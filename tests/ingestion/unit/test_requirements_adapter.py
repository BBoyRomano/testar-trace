from reqtrace.ingestion.requirements.adapter import RequirementsAdapter
from reqtrace.ingestion.requirements.models import ParsedRequirementsSource


def test_requirements_adapter_normalizes_parsed_requirements_source() -> None:
    parsed = ParsedRequirementsSource(
        title="Sample requirement",
        external_id="REQ-1",
        actor="Sample actor",
        preconditions=["A valid precondition exists"],
        main_steps=["The user performs the main action"],
        alternative_steps=["An alternative outcome is shown"],
        postconditions=["The operation is completed"],
        source_name="markdown",
    )

    adapter = RequirementsAdapter()
    batch = adapter.ingest(parsed)

    assert len(batch.requirements) == 1
    assert batch.requirements[0].id == "req-1"
    assert batch.requirements[0].external_id == "REQ-1"
    assert len(batch.fragments) == 4
    assert len(batch.flows) == 4

    flow_by_name = {flow.name: flow for flow in batch.flows}
    fragment_by_id = {fragment.id: fragment for fragment in batch.fragments}

    assert flow_by_name["Preconditions"].entry_fragment_id is not None
    assert flow_by_name["Main flow"].entry_fragment_id is not None
    assert flow_by_name["Alternative flow"].entry_fragment_id is not None
    assert flow_by_name["Postconditions"].entry_fragment_id is not None

    assert fragment_by_id[flow_by_name["Main flow"].entry_fragment_id].text == "The user performs the main action"
    assert fragment_by_id[flow_by_name["Alternative flow"].entry_fragment_id].branch_id == "alt-1"


def test_requirements_adapter_preserves_linear_flow_edges() -> None:
    parsed = ParsedRequirementsSource(
        title="Checkout",
        main_steps=["Open cart", "Confirm order", "See receipt"],
        source_name="markdown",
    )

    batch = RequirementsAdapter().ingest(parsed)

    main_flow = next(flow for flow in batch.flows if flow.name == "Main flow")
    main_fragments = [fragment for fragment in batch.fragments if fragment.kind.name == "MAIN_STEP"]

    assert main_flow.entry_fragment_id == main_fragments[0].id
    assert [fragment.order_index for fragment in main_fragments] == [1, 2, 3]
    assert [(edge.from_fragment_id, edge.to_fragment_id) for edge in batch.flow_edges] == [
        (main_fragments[0].id, main_fragments[1].id),
        (main_fragments[1].id, main_fragments[2].id),
    ]
