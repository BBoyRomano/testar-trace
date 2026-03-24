from reqtrace.domain.requirements import RequirementKind, RequirementUnitKind
from reqtrace.ingest.requirements.canonical_json import (
    load_canonical_json_requirement_catalog,
)


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
