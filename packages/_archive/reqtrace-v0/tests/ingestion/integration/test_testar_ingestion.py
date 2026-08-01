import json
from pathlib import Path

import pytest

from reqtrace.ingestion.common.exceptions import SourceParseError
from reqtrace.ingestion.evidence.adapter import EvidenceAdapter
from reqtrace.ingestion.evidence.testar.loader import TestarLoader

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "ingestion"
pytestmark = pytest.mark.integration


def test_testar_loader_and_adapter_ingest_sample_payload() -> None:
    payload = json.loads((FIXTURES_DIR / "sample_testar.json").read_text(encoding="utf-8"))

    loader = TestarLoader()
    parsed = loader.load_payload(payload=payload)

    adapter = EvidenceAdapter()
    batch = adapter.ingest(parsed)

    assert len(batch.runs) == 1
    assert len(batch.states) == 2
    assert len(batch.elements) == 1
    assert len(batch.actions) == 1
    assert len(batch.transitions) == 1
    assert batch.actions[0].target_element_id == "state-checkout:element-pay"


def test_testar_loader_rejects_invalid_json_file(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not-json}", encoding="utf-8")

    loader = TestarLoader()
    with pytest.raises(SourceParseError):
        loader.load(path)
