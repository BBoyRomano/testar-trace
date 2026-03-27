from pathlib import Path

from reqtrace.ingest.state_models import load_state_graph


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "state_models"


def test_load_testar_v1_minimal_fixture() -> None:
    graph = load_state_graph(str(FIXTURES_DIR / "testar_v1_minimal.json"))

    assert len(graph.states) == 2
    assert len(graph.transitions) == 1
    assert graph.metadata["source"] == "testar"
    assert graph.metadata["version"] == "json_v1"
