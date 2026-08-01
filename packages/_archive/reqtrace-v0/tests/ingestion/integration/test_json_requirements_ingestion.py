from pathlib import Path

import pytest

from reqtrace.ingestion.requirements.adapter import RequirementsAdapter
from reqtrace.ingestion.requirements.json.loader import JsonRequirementsLoader

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "ingestion"
pytestmark = pytest.mark.integration


def test_json_loader_and_adapter_ingest_use_case_collection() -> None:
    path = FIXTURES_DIR / "sample_requirements.json"
    loader = JsonRequirementsLoader()
    parsed = loader.load(path)

    batch = RequirementsAdapter().ingest(parsed)

    assert len(batch.documents) == 1
    assert len(batch.requirements) == 2
    assert batch.requirements[0].external_id == "UC.10"
    assert any(fragment.kind.value == "trigger" for fragment in batch.fragments)
    assert any(flow.name == "Constraints" for flow in batch.flows)
