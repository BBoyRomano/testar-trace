from pathlib import Path

from reqtrace.ingest.requirements import load_requirement_catalog
from reqtrace.ingest.state_models import load_state_graph


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "canonical"


def test_load_state_graph() -> None:
    state_graph = load_state_graph(
        str(FIXTURES_DIR / "case_001_found" / "state.json"))

    assert len(state_graph.states) == 1
    assert len(state_graph.transitions) == 0
    assert state_graph.states[0].id == "S1"


def test_load_requirement_catalog() -> None:
    requirement_catalog = load_requirement_catalog(
        str(FIXTURES_DIR / "case_001_found" / "requirements.json")
    )

    assert len(requirement_catalog.requirements) == 1
    assert requirement_catalog.requirements[0].id == "UC.01"
