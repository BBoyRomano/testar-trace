from pathlib import Path

from reqtrace.ingest.common import load_json_file
from reqtrace.ingest.requirements.registry import detect_requirement_importer
from reqtrace.ingest.state_models.registry import detect_state_model_importer


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_detect_canonical_state_model_importer() -> None:
    data = load_json_file(FIXTURES_DIR / "canonical" /
                          "case_001_found" / "state.json")
    importer = detect_state_model_importer(data)

    assert importer.__name__ == "load_canonical_json_state_graph"


def test_detect_testar_state_model_importer() -> None:
    data = load_json_file(FIXTURES_DIR / "state_models" /
                          "testar_v1_minimal.json")
    importer = detect_state_model_importer(data)

    assert importer.__name__ == "load_testar_json_v1_state_graph"


def test_detect_canonical_requirement_importer() -> None:
    data = load_json_file(FIXTURES_DIR / "canonical" /
                          "case_001_found" / "requirements.json")
    importer = detect_requirement_importer(data)

    assert importer.__name__ == "load_canonical_json_requirement_catalog"
