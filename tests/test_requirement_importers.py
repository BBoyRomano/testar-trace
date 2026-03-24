import json
from pathlib import Path

from reqtrace.domain.requirements import RequirementKind, RequirementUnitKind
from reqtrace.ingest.requirements import load_requirement_catalog
from reqtrace.ingest.requirements.canonical_json import (
    load_canonical_json_requirement_catalog,
)
from reqtrace.ingest.requirements.gherkin_feature import (
    load_gherkin_feature_requirement_catalog,
)
from reqtrace.ingest.requirements.use_cases_json import (
    load_use_cases_json_requirement_catalog,
)
from reqtrace.ingest.requirements.use_cases_markdown import (
    load_use_cases_markdown_requirement_catalog,
)
from reqtrace.ingest.requirements.user_stories_csv import (
    load_user_stories_csv_requirement_catalog,
)


FIXTURES_DIR = Path("tests/fixtures")


def test_load_canonical_json_requirement_catalog() -> None:
    catalog = load_canonical_json_requirement_catalog(
        {
            "metadata": {
                "format": "canonical_requirements_v1",
            },
            "requirements": [
                {
                    "id": "UC.01",
                    "kind": "use_case",
                    "title": "Application login",
                    "summary": "Registered user logs into the application.",
                    "actor": "Unlogged user",
                    "units": [
                        {
                            "id": "UC.01.pre.1",
                            "kind": "precondition",
                            "text": "User is on the UIS homepage.",
                        },
                        {
                            "id": "UC.01.trigger.1",
                            "kind": "trigger",
                            "text": "User selects the Login option.",
                        },
                        {
                            "id": "UC.01.step.1",
                            "kind": "step",
                            "text": "User enters pass in the password field.",
                        },
                        {
                            "id": "UC.01.post.1",
                            "kind": "postcondition",
                            "text": "Overview page appears.",
                        },
                    ],
                }
            ],
        }
    )

    assert catalog.metadata == {"format": "canonical_requirements_v1"}
    assert len(catalog.requirements) == 1

    requirement = catalog.requirements[0]
    assert requirement.id == "UC.01"
    assert requirement.kind == RequirementKind.USE_CASE
    assert requirement.title == "Application login"
    assert requirement.summary == "Registered user logs into the application."
    assert requirement.actor == "Unlogged user"
    assert len(requirement.units) == 4
    assert requirement.units[0].kind == RequirementUnitKind.PRECONDITION
    assert requirement.units[1].kind == RequirementUnitKind.TRIGGER
    assert requirement.units[2].kind == RequirementUnitKind.STEP
    assert requirement.units[3].kind == RequirementUnitKind.POSTCONDITION


def test_load_canonical_json_requirement_catalog_defaults_optional_fields() -> None:
    catalog = load_canonical_json_requirement_catalog(
        {
            "requirements": [
                {
                    "id": "US-001",
                    "kind": "user_story",
                    "title": "Application login",
                    "units": [
                        {
                            "id": "US-001.step.1",
                            "kind": "step",
                            "text": "As a registered user, I want to log into the application.",
                        }
                    ],
                }
            ]
        }
    )

    requirement = catalog.requirements[0]
    unit = requirement.units[0]

    assert requirement.summary is None
    assert requirement.actor is None
    assert requirement.metadata == {}
    assert unit.metadata == {}


def test_load_use_cases_json_requirement_catalog() -> None:
    data = json.loads(
        (
            FIXTURES_DIR
            / "requirements_sources"
            / "use_cases_json"
            / "tbuis_use_cases.json"
        ).read_text(encoding="utf-8")
    )

    catalog = load_use_cases_json_requirement_catalog(data)

    assert catalog.metadata["format"] == "tbuis_use_cases_v1"
    assert len(catalog.requirements) == 1

    requirement = catalog.requirements[0]
    assert requirement.id == "UC.01"
    assert requirement.kind == RequirementKind.USE_CASE
    assert requirement.title == "Application login"
    assert requirement.summary == (
        "Registered user will log into the application and based on the login "
        "name the user will be recognized either as a student or a teacher"
    )
    assert requirement.actor == "Unlogged user"

    unit_kinds = [unit.kind for unit in requirement.units]
    assert RequirementUnitKind.PRECONDITION in unit_kinds
    assert RequirementUnitKind.TRIGGER in unit_kinds
    assert RequirementUnitKind.STEP in unit_kinds
    assert RequirementUnitKind.POSTCONDITION in unit_kinds

    alternative_units = [
        unit
        for unit in requirement.units
        if unit.metadata.get("flow") == "alternative"
    ]
    assert alternative_units


def test_load_use_cases_markdown_requirement_catalog() -> None:
    text = (
        FIXTURES_DIR
        / "requirements_sources"
        / "use_cases_markdown"
        / "tbuis_use_cases.md"
    ).read_text(encoding="utf-8")

    catalog = load_use_cases_markdown_requirement_catalog(
        {
            "format": "tbuis_use_cases_markdown_v1",
            "content": text,
        }
    )

    assert catalog.metadata["format"] == "tbuis_use_cases_markdown_v1"
    assert len(catalog.requirements) == 1

    requirement = catalog.requirements[0]
    assert requirement.id == "UC.01"
    assert requirement.kind == RequirementKind.USE_CASE
    assert requirement.title == "Application login"
    assert requirement.actor == "Unlogged user"

    unit_kinds = [unit.kind for unit in requirement.units]
    assert RequirementUnitKind.PRECONDITION in unit_kinds
    assert RequirementUnitKind.TRIGGER in unit_kinds
    assert RequirementUnitKind.STEP in unit_kinds
    assert RequirementUnitKind.POSTCONDITION in unit_kinds


def test_use_cases_markdown_and_json_normalize_to_equivalent_requirement() -> None:
    json_data = json.loads(
        (
            FIXTURES_DIR
            / "requirements_sources"
            / "use_cases_json"
            / "tbuis_use_cases.json"
        ).read_text(encoding="utf-8")
    )
    markdown_text = (
        FIXTURES_DIR
        / "requirements_sources"
        / "use_cases_markdown"
        / "tbuis_use_cases.md"
    ).read_text(encoding="utf-8")

    json_catalog = load_use_cases_json_requirement_catalog(json_data)
    markdown_catalog = load_use_cases_markdown_requirement_catalog(
        {
            "format": "tbuis_use_cases_markdown_v1",
            "content": markdown_text,
        }
    )

    json_requirement = json_catalog.requirements[0]
    markdown_requirement = markdown_catalog.requirements[0]

    assert markdown_requirement.id == json_requirement.id
    assert markdown_requirement.kind == json_requirement.kind
    assert markdown_requirement.title == json_requirement.title
    assert markdown_requirement.summary == json_requirement.summary
    assert markdown_requirement.actor == json_requirement.actor
    assert [unit.kind for unit in markdown_requirement.units] == [
        unit.kind for unit in json_requirement.units
    ]
    assert [unit.text for unit in markdown_requirement.units] == [
        unit.text for unit in json_requirement.units
    ]


def test_load_user_stories_csv_requirement_catalog() -> None:
    content = (
        FIXTURES_DIR
        / "requirements_sources"
        / "user_stories_csv"
        / "tbuis_user_stories.csv"
    ).read_text(encoding="utf-8")

    catalog = load_user_stories_csv_requirement_catalog(
        {
            "format": "user_stories_csv_v1",
            "content": content,
        }
    )

    assert catalog.metadata["format"] == "user_stories_csv_v1"
    assert len(catalog.requirements) == 2

    requirement = catalog.requirements[0]
    assert requirement.id == "US.01"
    assert requirement.kind == RequirementKind.USER_STORY
    assert requirement.title == "Application login"
    assert requirement.actor == "registered user"

    unit_kinds = [unit.kind for unit in requirement.units]
    assert unit_kinds[0] == RequirementUnitKind.STEP
    assert RequirementUnitKind.POSTCONDITION in unit_kinds


def test_load_gherkin_feature_requirement_catalog() -> None:
    content = (
        FIXTURES_DIR
        / "requirements_sources"
        / "gherkin_feature"
        / "requirements.feature"
    ).read_text(encoding="utf-8")

    catalog = load_gherkin_feature_requirement_catalog(
        {
            "format": "gherkin_feature_v1",
            "content": content,
        }
    )

    assert catalog.metadata["format"] == "gherkin_feature_v1"
    assert len(catalog.requirements) == 2

    requirement = catalog.requirements[0]
    assert requirement.kind == RequirementKind.FEATURE
    assert requirement.title == "Application login"
    assert requirement.summary == "TbUIS authentication and profile management"

    unit_kinds = [unit.kind for unit in requirement.units]
    assert RequirementUnitKind.PRECONDITION in unit_kinds
    assert RequirementUnitKind.STEP in unit_kinds
    assert RequirementUnitKind.POSTCONDITION in unit_kinds


def test_load_requirement_catalog_detects_use_cases_json_importer() -> None:
    path = (
        FIXTURES_DIR
        / "requirements_sources"
        / "use_cases_json"
        / "tbuis_use_cases.json"
    )

    catalog = load_requirement_catalog(str(path))

    assert len(catalog.requirements) == 1
    assert catalog.requirements[0].id == "UC.01"
    assert catalog.requirements[0].kind == RequirementKind.USE_CASE
