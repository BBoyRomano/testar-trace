from pathlib import Path

from reqtrace.ingest.common import load_json_file
from reqtrace.ingest.state_models.canonical_json import load_canonical_json_state_graph
from reqtrace.ingest.state_models.testar_json_v1 import load_testar_json_v1_state_graph


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_load_canonical_json_state_graph_directly() -> None:
    data = load_json_file(FIXTURES_DIR / "canonical" /
                          "case_001_found" / "state.json")
    graph = load_canonical_json_state_graph(data)

    assert len(graph.states) == 1
    assert graph.states[0].id == "S1"
    assert graph.metadata == {}


def test_load_testar_json_v1_state_graph_directly() -> None:
    data = load_json_file(FIXTURES_DIR / "state_models" /
                          "testar_v1_minimal.json")
    graph = load_testar_json_v1_state_graph(data)

    assert len(graph.states) == 2
    assert len(graph.transitions) == 1
    assert graph.metadata["source"] == "testar"
    assert graph.metadata["version"] == "json_v1"
