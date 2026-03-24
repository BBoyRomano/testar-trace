from pathlib import Path

from reqtrace.domain.requirements import Requirement, RequirementUnitKind
from reqtrace.ingest.requirements import load_requirement_catalog


FIXTURES_DIR = Path("tests/fixtures/requirements_sources")


def _find_requirement_by_title(
    requirements: tuple[Requirement, ...],
    title: str,
) -> Requirement:
    for requirement in requirements:
        if requirement.title == title:
            return requirement
    raise AssertionError(f"Requirement with title {title!r} not found")


def _unit_texts(requirement: Requirement, kind: RequirementUnitKind) -> list[str]:
    return [unit.text for unit in requirement.units if unit.kind == kind]


def test_application_login_is_preserved_across_all_supported_formats() -> None:
    use_cases_json = load_requirement_catalog(
        str(FIXTURES_DIR / "use_cases_json" / "tbuis_use_cases.json")
    )
    use_cases_markdown = load_requirement_catalog(
        str(FIXTURES_DIR / "use_cases_markdown" / "tbuis_use_cases.md")
    )
    user_stories_csv = load_requirement_catalog(
        str(FIXTURES_DIR / "user_stories_csv" / "tbuis_user_stories.csv")
    )
    gherkin_feature = load_requirement_catalog(
        str(FIXTURES_DIR / "gherkin_feature" / "requirements.feature")
    )

    use_case_json_requirement = _find_requirement_by_title(
        use_cases_json.requirements,
        "Application login",
    )
    use_case_markdown_requirement = _find_requirement_by_title(
        use_cases_markdown.requirements,
        "Application login",
    )
    user_story_requirement = _find_requirement_by_title(
        user_stories_csv.requirements,
        "Application login",
    )
    gherkin_requirement = _find_requirement_by_title(
        gherkin_feature.requirements,
        "Application login",
    )

    assert use_case_json_requirement.actor == "Unlogged user"
    assert use_case_markdown_requirement.actor == "Unlogged user"
    assert user_story_requirement.actor == "registered user"

    assert "application" in use_case_json_requirement.title.lower()
    assert "application" in use_case_markdown_requirement.title.lower()
    assert "application" in user_story_requirement.title.lower()
    assert "application" in gherkin_requirement.title.lower()

    assert any(
        "login option" in text.lower()
        for text in _unit_texts(use_case_json_requirement, RequirementUnitKind.TRIGGER)
    )
    assert any(
        "login option" in text.lower()
        for text in _unit_texts(use_case_markdown_requirement, RequirementUnitKind.TRIGGER)
    )

    assert any(
        "log into the application" in text.lower()
        for text in _unit_texts(user_story_requirement, RequirementUnitKind.STEP)
    )

    assert any(
        "login option" in text.lower()
        for text in _unit_texts(gherkin_requirement, RequirementUnitKind.STEP)
    )

    assert any(
        "overview page" in text.lower()
        for text in _unit_texts(use_case_json_requirement, RequirementUnitKind.POSTCONDITION)
    )
    assert any(
        "overview page" in text.lower()
        for text in _unit_texts(use_case_markdown_requirement, RequirementUnitKind.POSTCONDITION)
    )
    assert any(
        "overview page" in text.lower()
        for text in _unit_texts(user_story_requirement, RequirementUnitKind.POSTCONDITION)
    )
    assert any(
        "overview page" in text.lower()
        for text in _unit_texts(gherkin_requirement, RequirementUnitKind.POSTCONDITION)
    )


def test_profile_update_intent_is_preserved_across_csv_and_gherkin() -> None:
    user_stories_csv = load_requirement_catalog(
        str(FIXTURES_DIR / "user_stories_csv" / "tbuis_user_stories.csv")
    )
    gherkin_feature = load_requirement_catalog(
        str(FIXTURES_DIR / "gherkin_feature" / "requirements.feature")
    )

    user_story_requirement = _find_requirement_by_title(
        user_stories_csv.requirements,
        "Change of user's personal data",
    )
    gherkin_requirement = _find_requirement_by_title(
        gherkin_feature.requirements,
        "Change of user's personal data",
    )

    assert user_story_requirement.actor == "logged in user"

    assert any(
        "change my personal data" in text.lower()
        for text in _unit_texts(user_story_requirement, RequirementUnitKind.STEP)
    )
    assert any(
        "first name entry" in text.lower()
        for text in _unit_texts(gherkin_requirement, RequirementUnitKind.STEP)
    )

    assert any(
        "overview page" in text.lower()
        for text in _unit_texts(user_story_requirement, RequirementUnitKind.POSTCONDITION)
    )
    assert any(
        "overview page" in text.lower()
        for text in _unit_texts(gherkin_requirement, RequirementUnitKind.POSTCONDITION)
    )
