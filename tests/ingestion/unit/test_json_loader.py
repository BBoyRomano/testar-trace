import pytest

from reqtrace.ingestion.common.exceptions import SourceParseError, SourceValidationError
from reqtrace.ingestion.requirements.json.loader import JsonRequirementsLoader


def test_json_loader_parses_use_case_payload(minimal_use_case_json_payload) -> None:
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


def test_json_loader_load_rejects_invalid_json_file(tmp_path) -> None:
    loader = JsonRequirementsLoader()
    path = tmp_path / "broken.json"
    path.write_text("{ not-json }", encoding="utf-8")

    with pytest.raises(SourceParseError, match="Invalid JSON requirements source"):
        loader.load(path)


def test_json_loader_load_rejects_directory_path(tmp_path) -> None:
    loader = JsonRequirementsLoader()

    with pytest.raises(SourceParseError, match="Could not read JSON source"):
        loader.load(tmp_path)


def test_json_loader_parses_list_payload() -> None:
    loader = JsonRequirementsLoader()
    payload = [
        {"id": "REQ-1", "title": "Login", "main_steps": ["Open page"]},
        {"id": "REQ-2", "title": "Logout", "main_steps": ["Click logout"]},
    ]

    parsed = loader.load_payload(payload=payload)

    assert parsed.document_title is None
    assert [item.external_id for item in parsed.requirements] == ["REQ-1", "REQ-2"]


def test_json_loader_rejects_non_object_entry_in_list_payload() -> None:
    loader = JsonRequirementsLoader()
    payload = [
        {"id": "REQ-1", "title": "Login"},
        "not-an-object",
    ]

    with pytest.raises(SourceValidationError, match="entry #2 must be an object"):
        loader.load_payload(payload=payload)


def test_json_loader_rejects_non_object_or_list_payload() -> None:
    loader = JsonRequirementsLoader()

    with pytest.raises(SourceValidationError, match="must be an object or list"):
        loader.load_payload(payload="invalid")  # type: ignore[arg-type]


def test_json_loader_rejects_empty_requirements_payload() -> None:
    loader = JsonRequirementsLoader()

    with pytest.raises(SourceValidationError, match="payload is empty"):
        loader.load_payload(payload={"requirements": []})


def test_json_loader_supports_string_alternative_flows() -> None:
    loader = JsonRequirementsLoader()
    payload = {
        "requirements": [
            {
                "id": "REQ-1",
                "title": "Login",
                "alternative_flows": ["Invalid credentials", "Network timeout"],
            }
        ]
    }

    parsed = loader.load_payload(payload=payload)

    assert len(parsed.requirements[0].alternative_flows) == 1
    assert parsed.requirements[0].alternative_flows[0].title == "Alternative flow"
    assert parsed.requirements[0].alternative_flows[0].steps == [
        "Invalid credentials",
        "Network timeout",
    ]


@pytest.mark.parametrize(
    "alternative_flows",
    [
        "not-a-list",
        [{"title": "Flow"}, "mixed"],
    ],
    ids=["non-list", "contains-non-object"],
)
def test_json_loader_rejects_invalid_alternative_flows(alternative_flows) -> None:
    loader = JsonRequirementsLoader()
    payload = {
        "requirements": [
            {
                "id": "REQ-1",
                "title": "Login",
                "alternative_flows": alternative_flows,
            }
        ]
    }

    with pytest.raises(SourceValidationError):
        loader.load_payload(payload=payload)


def test_json_loader_rejects_non_list_main_steps() -> None:
    loader = JsonRequirementsLoader()
    payload = {
        "requirements": [
            {
                "id": "REQ-1",
                "title": "Login",
                "main_steps": "not-a-list",
            }
        ]
    }

    with pytest.raises(SourceValidationError, match="Expected a list of strings"):
        loader.load_payload(payload=payload)


def test_json_loader_preserves_selected_metadata_fields() -> None:
    loader = JsonRequirementsLoader()
    payload = {
        "requirements": [
            {
                "id": "REQ-1",
                "title": "Login",
                "stakeholders_and_interests": ["User can sign in"],
                "technology_and_data_variations": ["Browser and locale differences"],
                "unrelated_field": "ignored",
            }
        ]
    }

    parsed = loader.load_payload(payload=payload)
    metadata = parsed.requirements[0].metadata

    assert "stakeholders_and_interests" in metadata
    assert "technology_and_data_variations" in metadata
    assert "unrelated_field" not in metadata
