import pytest
from tests._builders import minimal_use_case_json_payload

from reqtrace.ingestion.common.exceptions import SourceValidationError
from reqtrace.ingestion.requirements.json.loader import JsonRequirementsLoader


def test_json_loader_parses_use_case_payload() -> None:
    loader = JsonRequirementsLoader()
    parsed = loader.load_payload(payload=minimal_use_case_json_payload())

    assert parsed.document_title == "tbuis_use_cases_v1"
    assert len(parsed.requirements) == 2
    assert parsed.requirements[0].external_id == "UC.01"
    assert parsed.requirements[0].trigger == "User clicks Login"
    assert parsed.requirements[0].main_steps == ["Enter credentials", "Submit form"]
    assert parsed.requirements[0].alternative_steps == []
    assert len(parsed.requirements[0].alternative_flows) == 1
    assert parsed.requirements[0].alternative_flows[0].title == "Invalid credentials"


def test_json_loader_rejects_missing_title() -> None:
    loader = JsonRequirementsLoader()
    payload = {"requirements": [{"id": "REQ-1", "main_steps": ["Do x"]}]}

    with pytest.raises(SourceValidationError, match="missing a non-empty title"):
        loader.load_payload(payload=payload)
